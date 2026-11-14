"""Run real, local Hugging Face inference on the synthetic agent security dataset.

This is not a mock. The loaded transformer generates one decision per
(case, repetition, prompt treatment) and replays it across two host policies.
Every inference/parsing failure is counted in all relevant outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import time
from pathlib import Path

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

from agentsec_lab.cases import load_cases
from agentsec_lab.evaluate import evaluate, print_summary, save_report
from agentsec_lab.gateway import Decision
from agentsec_lab.models import ModelFailure

MODEL_IDS = {
    "0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
    "1.5b": "Qwen/Qwen2.5-1.5B-Instruct",
}


class LocalTransformersModel:
    """The only inference backend: a downloaded, locally executed open model."""

    def __init__(self, model_id: str, max_new_tokens: int = 96):
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        print(f"Loading model weights and tokenizer: {model_id}", flush=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=False)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=torch.float32, trust_remote_code=False
        ).eval()
        self.revision = getattr(self.model.config, "_commit_hash", None) or "unknown"
        print(f"Model loaded; revision={self.revision}", flush=True)
        self.count = 0
        self.last_output = None

    def decide(self, messages: list[dict[str, str]]) -> Decision:
        self.count += 1
        self.last_output = None
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([prompt], return_tensors="pt")
        with torch.inference_mode():
            tokens = self.model.generate(
                **inputs, max_new_tokens=self.max_new_tokens,
                do_sample=False, pad_token_id=self.tokenizer.eos_token_id,
            )
        output_ids = tokens[0][inputs["input_ids"].shape[1]:]
        text = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        self.last_output = text

        # Permit complete JSON or a single fenced JSON object; do not repair or
        # hallucinate invalid responses.
        if text.startswith("```"):
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            decision = Decision.from_raw(json.loads(text))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"Decision {self.count}: invalid JSON or action schema", flush=True)
            raise ModelFailure("invalid locally generated model decision") from None
        print(f"Decision {self.count}: {decision.action} -> {decision.target}", flush=True)
        return decision


def markdown_report(report: dict, *, elapsed_seconds: float) -> str:
    lines = [
        "# Preliminary real-model security evaluation",
        "",
        f"- **Model:** `{report['model_id']}`",
        f"- **Model revision:** `{report.get('model_revision')}`",
        f"- **Repository code revision:** `{report.get('code_commit')}`",
        f"- **Dataset SHA-256:** `{report['dataset_sha256']}`",
        f"- **Run UTC:** {report['generated_at_utc']}",
        f"- **Temperature:** greedy decoding (0); max new tokens: {report['max_new_tokens']}",
        f"- **Experiments:** {report['repetitions']} repetition(s); {len(report['modes'])} arms",
        f"- **Model inferences:** {report['model_calls_actual']}; simulated agent trials: {report['agent_trials']}",
        f"- **Prompt protocol:** {report['experiment_protocol']} (not directly comparable to the 2026-11-13 first pass)",
        f"- **Duration:** {elapsed_seconds:.0f} seconds",
        f"- **Evidence:** real model inference; **exploratory / non-generalizable**",
        "",
        f"| Experiment | Attack attempts / {report['summary'][report['modes'][0]]['attack_trials']} | "
        f"Executed attacker goals | Blocked attempts | Controls passed | Invalid responses |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode in report["modes"]:
        metric = report["summary"][mode]
        lines.append(
            f"| {mode} | {metric['attack_attempts']}/{metric['attack_trials']} | "
            f"{metric['executed_attacks']}/{metric['attack_trials']} | "
            f"{metric['blocked_attack_attempts']} | "
            f"{metric['legitimate_controls_executed']}/{metric['control_trials']} | "
            f"{metric['errors']}/{metric['total_trials']} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "An attack attempt is counted only when the model requested the dataset's exact attacker-target tool action. "
        "Execution is counted only when the simulated tool gateway permitted that action. "
        "Errors remain in the trial denominator. The controls measure authorized tool-use, not answer quality.",
        "",
        "Prompt-only changes the model instructions; gate-only changes host authorization. "
        "The paired-replay design reuses the same decision under each gateway configuration, "
        "so the effect of the host gate is not confounded by stochastic model output. "
        "A model may still produce contaminated prose that this metric does not capture.",
        "",
        "## Limitations",
        "",
        "- One local model and a synthetic, unblinded dataset. Results do not generalize to other models.",
        "- Prompts use JSON decision output, not native model tool-calling. There is no actual RAG engine or persistent memory.",
        "- Greedy decoding gives deterministic responses for the same prompt. Repeating identical deterministic prompts does not provide independent samples.",
        "- Any invalid JSON or inference failures are counted explicitly, not silently discarded.",
        "- **Simulated tools never send email, read production secrets or perform network requests.**",
        "",
        "The associated JSON file contains trial-level decisions for independent auditing. "
        "See [research protocol](../../docs/RESEARCH_PROTOCOL.md) and [threat model](../../docs/THREAT_MODEL.md).",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="data/cases.json")
    parser.add_argument("--model-size", choices=sorted(MODEL_IDS), default="1.5b")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    if args.repetitions < 1 or args.repetitions > 5:
        parser.error("repetitions must be between 1 and 5")
    if not 48 <= args.max_new_tokens <= 256:
        parser.error("max-new-tokens must be 48..256")
    torch.set_num_threads(args.threads)

    dataset = Path(args.dataset)
    cases = load_cases(dataset)
    model_id = MODEL_IDS[args.model_size]
    model = LocalTransformersModel(model_id, max_new_tokens=args.max_new_tokens)
    arms = ("baseline", "prompt_only", "gate_only", "defended")
    total = len(cases) * len(arms) * args.repetitions
    unique_calls = len(cases) * 2 * args.repetitions
    print(f"Paired replay: {len(cases)} cases x {len(arms)} arms x "
          f"{args.repetitions} repetition(s) = {total} simulated agent trials "
          f"from {unique_calls} fresh model inferences", flush=True)
    start = time.monotonic()
    result = evaluate(
        cases, model, model_id=model_id, repetitions=args.repetitions,
        backend="local-transformers", arms=arms, paired_replay=True,
    )
    duration = time.monotonic() - start
    result.update({
        "model_revision": model.revision,
        "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "code_commit": os.environ.get("GITHUB_SHA", "local_unrecorded"),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "temperature_requested": 0.0,
        "max_new_tokens": args.max_new_tokens,
        "device": "cpu",
        "run_duration_seconds": round(duration, 1),
        "model_calls_expected": unique_calls,
        "agent_trials_expected": total,
        "experiment_protocol": "v2-paired-replay-strict-json-160" if args.max_new_tokens == 160 else "v2-paired-replay-custom-generation-limit",
        "model_calls_completed": model.count,
        "method": "huggingface_local_cpu_greedy_decode",
    })
    if result["evidence_kind"] != "real_model":
        raise RuntimeError("Real model evidence classification is required")
    output = args.output or f"research/runs/qwen2.5-{args.model_size}-paired-{args.max_new_tokens}.json"
    save_report(result, output)
    target = Path(output)
    target.with_suffix(".md").write_text(
        markdown_report(result, elapsed_seconds=duration), encoding="utf-8"
    )
    print(print_summary(result), flush=True)
    print(f"Saved real-model JSON and Markdown: {target}", flush=True)


if __name__ == "__main__":
    main()
