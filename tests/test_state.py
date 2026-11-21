import unittest
from goal_runner.state import GoalState, StateConflict

class GoalStateTests(unittest.TestCase):
    def test_happy_path(self):
        s = GoalState("pilot")
        for i, target in enumerate(("PLANNING", "EXECUTING", "AWAITING_CI", "VERIFYING")):
            s = s.transition(expected_revision=i, event_id=f"e{i}", target=target)
        s = s.transition(
            expected_revision=4, event_id="e4", target="COMPLETED",
            evidence_ref="commit:abc:ci:green", verified_checks=("build", "e2e"),
        )
        self.assertEqual(s.status, "COMPLETED")
        self.assertEqual(s.revision, 5)
        self.assertEqual(GoalState.from_dict(s.to_dict()), s)

    def test_exact_duplicate_noop(self):
        s = GoalState("pilot").transition(expected_revision=0, event_id="e1", target="PLANNING")
        self.assertIs(s.transition(expected_revision=0, event_id="e1", target="PLANNING"), s)

    def test_conflicting_duplicate(self):
        s = GoalState("pilot").transition(expected_revision=0, event_id="e1", target="PLANNING")
        with self.assertRaises(StateConflict):
            s.transition(expected_revision=1, event_id="e1", target="EXECUTING")

    def test_stale_revision(self):
        s = GoalState("pilot").transition(expected_revision=0, event_id="e1", target="PLANNING")
        with self.assertRaises(StateConflict):
            s.transition(expected_revision=0, event_id="e2", target="EXECUTING")

    def test_completion_needs_evidence(self):
        s = GoalState("pilot", status="VERIFYING")
        with self.assertRaises(StateConflict):
            s.transition(expected_revision=0, event_id="e3", target="COMPLETED")

    def test_completed_terminal(self):
        s = GoalState("pilot", status="COMPLETED")
        with self.assertRaises(StateConflict):
            s.transition(expected_revision=0, event_id="e4", target="EXECUTING")

    def test_recovery_from_block(self):
        s = GoalState("pilot", status="EXECUTING").transition(
            expected_revision=0, event_id="e1", target="BLOCKED")
        self.assertEqual(
            s.transition(expected_revision=1, event_id="e2", target="EXECUTING").status,
            "EXECUTING",
        )

if __name__ == "__main__":
    unittest.main()
