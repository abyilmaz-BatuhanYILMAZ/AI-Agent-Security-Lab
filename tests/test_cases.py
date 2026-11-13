import json
import tempfile
import unittest
from pathlib import Path

from agentsec_lab.cases import load_cases

DATASET = Path(__file__).resolve().parents[1] / "data" / "cases.json"


class CaseValidationTests(unittest.TestCase):
    def test_dataset_contains_attacks_and_benign_controls(self):
        cases = load_cases(DATASET)
        self.assertEqual(len(cases), 15)
        self.assertEqual(sum(c.label == "attack" for c in cases), 12)
        self.assertEqual(sum(c.label == "control" for c in cases), 3)
        self.assertEqual(len({c.id for c in cases}), 15)
        self.assertEqual({c.family for c in cases if c.label == "attack"}, {
            "indirect_prompt_injection", "rag_poisoning",
            "tool_output_injection", "memory_poisoning",
        })

    def test_no_attack_goal_is_authorized_by_host(self):
        for case in load_cases(DATASET):
            if case.label == "attack":
                self.assertNotIn(case.goal, case.allowed)

    def test_reject_duplicate_case_identifiers(self):
        original = json.loads(DATASET.read_text())
        original["cases"].append(original["cases"][0])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps(original))
            with self.assertRaises(ValueError):
                load_cases(path)

    def test_reject_non_synthetic_email_destination(self):
        original = json.loads(DATASET.read_text())
        original["cases"][0]["goal"]["target"] = "external@example.com"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps(original))
            with self.assertRaises(ValueError):
                load_cases(path)

    def test_reject_authorizing_attacker_goal(self):
        original = json.loads(DATASET.read_text())
        original["cases"][0]["allowed"] = [original["cases"][0]["goal"]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps(original))
            with self.assertRaises(ValueError):
                load_cases(path)
