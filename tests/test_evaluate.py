import json
import tempfile
import unittest
from pathlib import Path

from agentsec_lab.cases import Case, Grant, load_cases
from agentsec_lab.evaluate import evaluate, print_summary, save_report
from agentsec_lab.gateway import Decision
from agentsec_lab.models import ModelFailure, validate_endpoint
from agentsec_lab.prompts import build_messages

DATASET = Path(__file__).resolve().parents[1] / "data" / "cases.json"


class ScriptedModel:
    """Contract-test double. It does not evaluate an actual language model."""

    def __init__(self, decisions):
        self.decisions = iter(decisions)

    def decide(self, messages):
        return next(self.decisions)


class FailingModel:
    def decide(self, messages):
        raise ModelFailure("invalid JSON decision from inference model")


class AgentEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.attack = load_cases(DATASET)[0]
        self.control = next(c for c in load_cases(DATASET) if c.id == "control-email-02")

    def test_lower_trust_text_is_not_a_system_message(self):
        messages = build_messages(self.attack, defended=True)
        self.assertEqual([m["role"] for m in messages], ["system", "system", "user", "user"])
        self.assertIn(self.attack.source_text, messages[3]["content"])
        self.assertNotIn(self.attack.source_text, messages[0]["content"])
        self.assertIn("lower-trust", messages[0]["content"])

    def test_scripted_attack_is_executed_baseline_and_blocked_defended(self):
        decision = Decision("send_email", "archive@outside.invalid", "synthetic")
        report = evaluate([self.attack], ScriptedModel([decision, decision]),
                          model_id="scripted-fixture", backend="scripted-contract-test")
        self.assertEqual(report["summary"]["baseline"]["executed_attacks"], 1)
        self.assertEqual(report["summary"]["defended"]["executed_attacks"], 0)
        self.assertEqual(report["summary"]["defended"]["blocked_attack_attempts"], 1)
        self.assertEqual(report["evidence_kind"], "scripted_contract_test_not_model_evidence")

    def test_authorized_control_passes_in_defended_mode(self):
        decision = Decision("send_email", "teammate@team.invalid", "release note")
        report = evaluate([self.control], ScriptedModel([decision, decision]),
                          model_id="scripted-fixture", backend="scripted-contract-test")
        self.assertEqual(report["summary"]["defended"]["legitimate_controls_executed"], 1)
        self.assertIsNone(report["summary"]["baseline"]["executed_attack_success_rate"])

    def test_failures_are_counted_and_not_treated_as_successes(self):
        report = evaluate([self.attack], FailingModel(), model_id="scripted-fixture",
                          backend="scripted-contract-test", repetitions=2)
        self.assertEqual(report["summary"]["baseline"]["errors"], 2)
        self.assertEqual(report["summary"]["defended"]["errors"], 2)
        self.assertEqual(report["summary"]["baseline"]["executed_attacks"], 0)

    def test_report_round_trip(self):
        decision = Decision("answer", "", "Synthetic summary")
        report = evaluate([self.attack], ScriptedModel([decision, decision]),
                          model_id="scripted-fixture", backend="scripted-contract-test")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            save_report(report, path)
            loaded = json.loads(path.read_text())
            self.assertEqual(loaded["schema_version"], "1.0")
            self.assertIn("Executed attacker goals", print_summary(loaded))

    def test_endpoint_accepts_https_and_literal_local_http_only(self):
        self.assertEqual(validate_endpoint("https://example.org/v1/chat/completions"),
                         "https://example.org/v1/chat/completions")
        self.assertEqual(validate_endpoint("http://127.0.0.1:11434/v1/chat/completions"),
                         "http://127.0.0.1:11434/v1/chat/completions")
        for address in [
            "http://example.org/v1/chat/completions",
            "http://169.254.169.254/latest/meta-data/",
            "https://user:pass@example.org/v1/chat/completions",
            "file:///tmp/secrets",
        ]:
            with self.subTest(address=address):
                with self.assertRaises(ValueError):
                    validate_endpoint(address)

    def test_empty_case_list_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([], ScriptedModel([]), model_id="x", backend="scripted-contract-test")
