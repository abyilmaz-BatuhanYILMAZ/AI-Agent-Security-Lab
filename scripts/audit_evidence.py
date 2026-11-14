"""Validate provenance, paired replay invariants and published metrics.

Offline stdlib-only. Does not infer general model safety from a synthetic run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED_ARMS = ("baseline", "prompt_only", "gate_only", "defended")
REQUIRED_COUNTS = (
    "total_trials", "attack_trials", "control_trials", "valid_attack_trials",
    "attack_attempts", "executed_attacks", "blocked_attack_attempts",
    "legitimate_controls_executed", "errors",
)


class EvidenceError(ValueError):
    """A required experiment invariant was not satisfied."""


def _assert(value: bool, explanation: str) -> None:
    if not value:
        raise EvidenceError(explanation)


def audit(report: dict, dataset: bytes) -> dict:
    _assert(isinstance(report, dict), "Report must be a JSON object")
    _assert(report.get("evidence_kind") == "real_model", "Not a real-model report")
    _assert(report.get("paired_replay") is True, "Paired replay evidence required")
    _assert(tuple(report.get("modes", [])) == REQUIRED_ARMS, "Four arms must be ordered consistently")
    _assert(report.get("experiment_protocol") == "v2-paired-replay-strict-json-160", "Protocol mismatch")
    _assert(report.get("max_new_tokens") == 160, "Generation limit mismatch")
    _assert(report.get("dataset_sha256") == hashlib.sha256(dataset).hexdigest(), "Dataset SHA-256 differs")
    _assert(isinstance(report.get("model_revision"), str) and bool(report["model_revision"]), "Model revision missing")
    _assert(isinstance(report.get("code_commit"), str) and bool(report["code_commit"]), "Code revision missing")

    trials = report.get("trials")
    n = report.get("case_count")
    repetitions = report.get("repetitions")
    _assert(isinstance(trials, list) and isinstance(n, int) and n > 0 and
            isinstance(repetitions, int) and repetitions >= 1, "Missing trials or run dimensions")
    _assert(len(trials) == n * repetitions * 4, "Missing/duplicate agent trial")
    _assert(report.get("agent_trials") == len(trials), "Incorrect reported agent-trial count")
    _assert(report.get("model_calls_actual") == n * repetitions * 2, "Incorrect actual model-call count")
    _assert(report.get("model_calls_completed") == report.get("model_calls_actual"),
            "Incomplete model generation calls")
    cases: dict[tuple[str, int], dict[str, dict]] = defaultdict(dict)
    for t in trials:
        _assert(isinstance(t, dict) and t.get("mode") in REQUIRED_ARMS and
                isinstance(t.get("case_id"), str) and
                t.get("label") in ("attack", "control"), "Malformed trial")
        key = (t["case_id"], t["repetition"])
        _assert(t["mode"] not in cases[key], "Duplicated case/repetition/arm")
        cases[key][t["mode"]] = t
        _assert(not t.get("attack_executed") or
                (t.get("attack_attempt") and t.get("executed")),
                "Attack counted as executed without goal-matching execution")
        _assert(t.get("error") is None or
                (not t.get("executed") and not t.get("attack_executed")),
                "Parsing error counted as executed action")
    _assert(len(cases) == n * repetitions, "Unique case/repetition count mismatch")
    for group in cases.values():
        _assert(set(group) == set(REQUIRED_ARMS), "One case is missing an arm")
        for first, second in (("baseline", "gate_only"), ("prompt_only", "defended")):
            a, b = group[first], group[second]
            for field in ("decision", "error", "raw_model_text"):
                _assert(a.get(field) == b.get(field),
                        f"Paired replay changed {field} between {first} and {second}")
            _assert(a.get("model_decision_reused") is False and
                    b.get("model_decision_reused") is True, "Incorrect model-call reuse flags")

    summary: dict = {}
    for arm in REQUIRED_ARMS:
        items = [t for t in trials if t["mode"] == arm]
        attacks = [t for t in items if t["label"] == "attack"]
        controls = [t for t in items if t["label"] == "control"]
        recomputed = {
            "total_trials": len(items),
            "attack_trials": len(attacks),
            "control_trials": len(controls),
            "valid_attack_trials": sum(t["error"] is None for t in attacks),
            "attack_attempts": sum(bool(t.get("attack_attempt")) for t in attacks),
            "executed_attacks": sum(bool(t.get("attack_executed")) for t in attacks),
            "blocked_attack_attempts": sum(bool(t.get("blocked_attack_attempt")) for t in attacks),
            "legitimate_controls_executed": sum(bool(t.get("control_pass")) for t in controls),
            "errors": sum(t["error"] is not None for t in items),
        }
        stored = report["summary"][arm]
        for key in REQUIRED_COUNTS:
            _assert(recomputed[key] == stored.get(key), f"Inconsistent {arm}.{key}")
        summary[arm] = recomputed

    return {
        "model": report["model_id"],
        "model_revision": report["model_revision"],
        "dataset_sha256": report["dataset_sha256"],
        "protocol": report["experiment_protocol"],
        "actual_model_calls": report["model_calls_actual"],
        "agent_trials": len(trials),
        "summary": summary,
        "quality": {
            "provenance_and_denominators": "verified",
            "paired_replay_invariance": "verified",
            "output_validity_is_separately_counted": True,
            "generalizable_security_benchmark": False,
            "real_production_environment_evaluated": False,
        },
    }


def compare(results: list[dict]) -> dict:
    _assert(len(results) >= 2, "At least two reports are needed for comparison")
    for r in results[1:]:
        _assert(r["dataset_sha256"] == results[0]["dataset_sha256"] and
                r["protocol"] == results[0]["protocol"], "Comparison protocol/data mismatch")
        for arm in REQUIRED_ARMS:
            a, b = results[0]["summary"][arm], r["summary"][arm]
            _assert(a["attack_trials"] == b["attack_trials"] and
                    a["control_trials"] == b["control_trials"], "Unequal trial denominators")
    return {
        "assessment": "matched_exploratory_runs_not_model_rankings",
        "models": results,
        "interpretation": (
            "Invalid outputs count toward primary denominators and are not refusals. "
            "Small unblinded synthetic cases cannot rank model robustness. "
            "A host gate that denies observed unauthorized tool calls does not "
            "demonstrate production security or answer-quality preservation."
        ),
    }


def render_markdown(result: dict) -> str:
    lines = [
        "# Matched real-model evidence audit",
        "",
        "**Status:** Metadata and replay invariants verified from checked-in records. "
        "**Not** an independent model-reproduction run.",
        "",
        "| Model | Arm | Attempts | Executed | Controls passed | Errors | Valid attack outputs |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for report in result["models"]:
        for mode in REQUIRED_ARMS:
            m = report["summary"][mode]
            lines.append(
                f"| {report['model']} | {mode} | {m['attack_attempts']}/{m['attack_trials']} | "
                f"{m['executed_attacks']}/{m['attack_trials']} | "
                f"{m['legitimate_controls_executed']}/{m['control_trials']} | "
                f"{m['errors']}/{m['total_trials']} | {m['valid_attack_trials']}/{m['attack_trials']} |"
            )
    lines.extend(["", "## Interpretation", result["interpretation"], "",
        "This tool checks provenance, totals, and paired decisions; it cannot validate "
        "the underlying model weights, re-run inference, or establish statistical generalization.", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check historical real-model evidence integrity")
    parser.add_argument("--dataset", type=Path, default=Path("data/cases.json"))
    parser.add_argument("--reports", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="New local report path; refuses to overwrite")
    args = parser.parse_args(argv)
    try:
        dataset = args.dataset.read_bytes()
        results = [audit(json.loads(path.read_text(encoding="utf-8")), dataset)
                   for path in args.reports]
        result = compare(results)
        md = render_markdown(result)
        if args.output:
            with args.output.open("x", encoding="utf-8") as f:
                f.write(md)
            print(f"Verified evidence audit: {args.output}")
        else:
            print(md)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Evidence audit FAILED: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
