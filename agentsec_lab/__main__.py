"""Command-line runner for synthetic AI agent security evaluations."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from .cases import load_cases
from .evaluate import evaluate, print_summary, save_report
from .models import CompatibleChatModel


def parser_factory() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentsec_lab",
        description="Evaluate unauthorized tool attempts against a simulated AI agent gateway.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a versioned attack dataset (offline).")
    validate.add_argument("--dataset", default="data/cases.json")

    run = sub.add_parser("evaluate", help="Run an authorized real LLM evaluation.")
    run.add_argument("--dataset", default="data/cases.json")
    run.add_argument("--model", required=True)
    run.add_argument("--endpoint", required=True, help="Trusted OpenAI-compatible chat completions URL")
    run.add_argument("--api-key-env", default="AI_LAB_API_KEY")
    run.add_argument("--repetitions", type=int, default=3)
    run.add_argument("--all-arms", action="store_true", help="Add prompt-only and gate-only ablation arms")
    run.add_argument("--limit", type=int, default=0, help="Evaluate only the first N cases (0 = all)")
    run.add_argument("--temperature", type=float, default=0.0)
    run.add_argument("--timeout", type=float, default=45.0)
    run.add_argument("--output", default="reports/evaluation.json")

    summary = sub.add_parser("summarize", help="Summarize a previously saved JSON report.")
    summary.add_argument("report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = parser_factory().parse_args(argv)
    try:
        if args.command == "validate":
            cases = load_cases(args.dataset)
            attacks = sum(case.label == "attack" for case in cases)
            controls = len(cases) - attacks
            print(f"Valid dataset: {len(cases)} cases ({attacks} attacks, {controls} controls)")
            return 0

        if args.command == "summarize":
            report = json.loads(Path(args.report).read_text(encoding="utf-8"))
            if report.get("schema_version") != "1.0" or not isinstance(report.get("summary"), dict):
                raise ValueError("invalid or unsupported report schema")
            print(print_summary(report))
            return 0

        if args.command == "evaluate":
            cases = load_cases(args.dataset)
            if args.limit < 0:
                raise ValueError("--limit must be 0 or greater")
            if args.limit:
                cases = cases[:args.limit]
            if args.repetitions < 1 or args.repetitions > 20:
                raise ValueError("--repetitions must be 1 to 20")
            model = CompatibleChatModel(
                model=args.model, endpoint=args.endpoint, api_key_env=args.api_key_env,
                timeout=args.timeout, temperature=args.temperature,
            )
            arms = ("baseline", "prompt_only", "gate_only", "defended") if args.all_arms else ("baseline", "defended")
            print(
                f"Running {len(cases) * args.repetitions * len(arms)} model decisions "
                f"({len(cases)} cases x {args.repetitions} repetitions x {len(arms)} arms).",
                flush=True,
            )
            report = evaluate(
                cases, model, model_id=args.model,
                repetitions=args.repetitions, backend="openai-compatible", arms=arms,
            )
            report["dataset_sha256"] = hashlib.sha256(Path(args.dataset).read_bytes()).hexdigest()
            report["temperature_requested"] = args.temperature
            report["endpoint_category"] = (
                "loopback" if urlsplit(args.endpoint).hostname in ("localhost", "127.0.0.1", "::1")
                else "hosted"
            )
            save_report(report, args.output)
            print(print_summary(report))
            print(f"Saved: {args.output}")
            return 0
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
