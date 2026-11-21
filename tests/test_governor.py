import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from goal_runner.governor import JobRequest, VercelUsage, choose_executor

NOW = datetime(2026, 11, 21, 20, 0, tzinfo=timezone.utc)

def usage():
    return VercelUsage(
        observed_at=NOW,
        cpu_hours_remaining=4.0,
        memory_gb_hours_remaining=400,
        transfer_gb_remaining=10,
        creations_remaining=2000,
        snapshot_gb_remaining=10,
        next_reset=None,
        hard_no_overage_verified=True,
    )

class GovernorTests(unittest.TestCase):
    def test_public_actions_is_preferred(self):
        result = choose_executor(JobRequest(kind="frontend_test", public_repo=True), now=NOW)
        self.assertTrue(result.permitted)
        self.assertEqual(result.provider, "github_actions")

    def test_private_not_published(self):
        self.assertFalse(choose_executor(JobRequest(kind="ci", public_repo=False), now=NOW).permitted)

    def test_retry_cap(self):
        self.assertFalse(choose_executor(JobRequest(kind="ci", public_repo=True,
                                                    attempts_for_step=2), now=NOW).permitted)

    def test_daily_limit(self):
        self.assertFalse(choose_executor(JobRequest(kind="ci", public_repo=True,
                                                    total_job_minutes_today=115), now=NOW).permitted)

    def test_vercel_quota_unknown(self):
        self.assertFalse(choose_executor(JobRequest(kind="interactive", public_repo=True),
                                         now=NOW).permitted)

    def test_vercel_usage_stale(self):
        self.assertFalse(choose_executor(JobRequest(kind="interactive", public_repo=True),
                                         now=NOW, vercel=replace(usage(), observed_at=NOW-timedelta(hours=1))).permitted)

    def test_vercel_under_budget(self):
        result = choose_executor(JobRequest(kind="interactive", public_repo=True),
                                 now=NOW, vercel=usage())
        self.assertTrue(result.permitted)
        self.assertEqual(result.provider, "vercel_sandbox")

    def test_no_billing_guard(self):
        self.assertFalse(choose_executor(JobRequest(kind="interactive", public_repo=True),
                                         now=NOW, vercel=replace(usage(), hard_no_overage_verified=False)).permitted)

    def test_vercel_low_cpu(self):
        self.assertFalse(choose_executor(JobRequest(kind="interactive", public_repo=True),
                                         now=NOW, vercel=replace(usage(), cpu_hours_remaining=0.01)).permitted)

    def test_vercel_low_transfer(self):
        self.assertFalse(choose_executor(JobRequest(kind="interactive", public_repo=True),
                                         now=NOW, vercel=replace(usage(), transfer_gb_remaining=0.01)).permitted)

    def test_oversize_rejected(self):
        self.assertFalse(choose_executor(JobRequest(kind="interactive", public_repo=True,
                                         estimated_wall_minutes=50), now=NOW, vercel=usage()).permitted)

    def test_future_quota_timestamp_rejected(self):
        self.assertFalse(choose_executor(JobRequest(kind="interactive", public_repo=True),
                                         now=NOW, vercel=replace(usage(), observed_at=NOW+timedelta(minutes=2))).permitted)

    def test_negative_egress_rejected(self):
        self.assertFalse(choose_executor(JobRequest(kind="interactive", public_repo=True,
                                         estimated_egress_gb=-1), now=NOW, vercel=usage()).permitted)

if __name__ == "__main__":
    unittest.main()
