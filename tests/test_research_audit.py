import copy
import json
from pathlib import Path
import unittest

from agentsec_lab.cases import load_cases
from scripts.audit_evidence import audit, compare, EvidenceError, render_markdown


ROOT = Path(__file__).resolve().parents[1]
DATASET = (ROOT / "data/cases.json").read_bytes()
FILES = [
    ROOT / "research/runs/qwen2.5-0.5b-paired-160.json",
    ROOT / "research/runs/qwen2.5-1.5b-paired-160.json",
]


def reports():
    return [json.loads(f.read_text(encoding="utf-8")) for f in FILES]


class EvidenceIntegrityTests(unittest.TestCase):
    def test_historical_matched_evidence_audits(self):
        results = [audit(r, DATASET) for r in reports()]
        comparison = compare(results)
        self.assertEqual(comparison["assessment"],
                         "matched_exploratory_runs_not_model_rankings")
        self.assertEqual([r["actual_model_calls"] for r in results], [30, 30])
        self.assertEqual([r["agent_trials"] for r in results], [60, 60])
        self.assertIn("Invalid outputs count", comparison["interpretation"])
        self.assertIn("0.5B-Instruct", render_markdown(comparison))

    def test_report_rejects_tampered_counts(self):
        r = copy.deepcopy(reports()[1])
        r["summary"]["baseline"]["attack_attempts"] += 1
        with self.assertRaisesRegex(EvidenceError, "Inconsistent"):
            audit(r, DATASET)

    def test_report_rejects_tampered_paired_decision(self):
        r = copy.deepcopy(reports()[1])
        replayed = next(t for t in r["trials"] if t["mode"] == "gate_only")
        replayed["error"] = "different output"
        with self.assertRaises(EvidenceError):
            audit(r, DATASET)

    def test_rejects_nonmatching_dataset_hash(self):
        with self.assertRaisesRegex(EvidenceError, "Dataset SHA"):
            audit(reports()[0], DATASET + b"modified")

    def test_exploratory_v2_dataset_is_balanced_and_separate(self):
        cases = load_cases(ROOT / "data/cases-exploratory-v2.json")
        self.assertEqual(len(cases), 24)
        self.assertEqual(sum(c.label == "attack" for c in cases), 12)
        self.assertEqual(sum(c.label == "control" for c in cases), 12)
        original = load_cases(ROOT / "data/cases.json")
        self.assertFalse({c.id for c in original} & {c.id for c in cases})
        self.assertEqual(
            {c.family for c in cases if c.label == "attack"},
            {"rag_poisoning", "tool_output_injection",
             "indirect_prompt_injection", "memory_poisoning"},
        )
        self.assertEqual(
            sum(c.goal.action == "answer" for c in cases if c.label == "control"), 4
        )
        self.assertEqual(
            sum(c.goal.action == "send_email" for c in cases if c.label == "control"), 4
        )
        self.assertEqual(
            sum(c.goal.action == "write_note" for c in cases if c.label == "control"), 4
        )


if __name__ == "__main__":
    unittest.main()
