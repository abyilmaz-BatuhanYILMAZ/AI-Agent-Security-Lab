import unittest

from agentsec_lab.cases import Grant
from agentsec_lab.gateway import Decision, SimulatedGateway


class GatewayTests(unittest.TestCase):
    def test_baseline_executes_synthetic_outbox_action(self):
        gateway = SimulatedGateway(defended=False)
        result = gateway.execute(Decision("send_email", "collector@outside.invalid", "synthetic"), ())
        self.assertTrue(result.executed)
        self.assertEqual(gateway.email_outbox, [("collector@outside.invalid", "synthetic")])

    def test_defended_gateway_blocks_unauthorized_email(self):
        gateway = SimulatedGateway(defended=True)
        result = gateway.execute(Decision("send_email", "collector@outside.invalid", "synthetic"), ())
        self.assertTrue(result.blocked)
        self.assertFalse(result.executed)
        self.assertEqual(gateway.email_outbox, [])

    def test_exact_recipient_capability_required(self):
        gateway = SimulatedGateway(defended=True)
        grants = (Grant("send_email", "teammate@team.invalid"),)
        self.assertFalse(gateway.execute(Decision("send_email", "attacker@outside.invalid"), grants).executed)
        self.assertTrue(gateway.execute(Decision("send_email", "teammate@team.invalid"), grants).executed)

    def test_real_email_is_never_delivered_even_in_baseline(self):
        gateway = SimulatedGateway(defended=False)
        self.assertTrue(gateway.execute(Decision("send_email", "person@example.org"), ()).blocked)
        self.assertEqual(gateway.email_outbox, [])

    def test_synthetic_secret_access_is_blocked_under_defense(self):
        decision = Decision("read_secret", "synthetic_canary")
        self.assertTrue(SimulatedGateway(defended=False).execute(decision, ()).executed)
        self.assertTrue(SimulatedGateway(defended=True).execute(decision, ()).blocked)

    def test_write_note_has_no_filesystem_side_effect(self):
        gateway = SimulatedGateway(defended=True)
        grants = (Grant("write_note", "sprint-plan"),)
        self.assertTrue(gateway.execute(Decision("write_note", "sprint-plan", "approved"), grants).executed)
        self.assertEqual(gateway.notes["sprint-plan"], "approved")
        self.assertTrue(gateway.execute(Decision("write_note", "admin-plan", "wrong"), grants).blocked)

    def test_structured_decision_rejects_unknown_actions(self):
        with self.assertRaises(ValueError):
            Decision.from_raw({"action": "shell", "target": "x", "content": "x"})

    def test_structured_decision_requires_all_fields(self):
        with self.assertRaises(ValueError):
            Decision.from_raw({"action": "answer", "content": "hi"})

    def test_empty_answer_is_not_a_successful_execution(self):
        self.assertFalse(SimulatedGateway(defended=True).execute(Decision("answer", "", ""), ()).executed)
