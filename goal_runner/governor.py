"""Deterministic execution admission, not a billing guarantee."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

@dataclass(frozen=True)
class VercelUsage:
    observed_at: datetime
    cpu_hours_remaining: float | None
    memory_gb_hours_remaining: float | None
    transfer_gb_remaining: float | None
    creations_remaining: int | None
    snapshot_gb_remaining: float | None
    next_reset: datetime | None
    hard_no_overage_verified: bool = False

@dataclass(frozen=True)
class JobRequest:
    kind: Literal["ci", "frontend_test", "interactive", "other"]
    public_repo: bool
    standard_runner: bool = True
    estimated_wall_minutes: float = 15.0
    vcpus: int = 1
    estimated_egress_gb: float = 0.05
    snapshot_gb: float = 0.0
    attempts_for_step: int = 0
    total_job_minutes_today: float = 0.0

@dataclass(frozen=True)
class Decision:
    permitted: bool
    provider: str | None
    reason: str
    billable_exposure: str = "none approved"

def choose_executor(
    request: JobRequest, *, now: datetime,
    vercel: VercelUsage | None = None, reserve_fraction: float = 0.20,
    max_ci_minutes_per_day: float = 120.0, max_attempts_per_step: int = 2,
    max_vercel_minutes: float = 20.0,
) -> Decision:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if not 0 <= reserve_fraction < 1:
        raise ValueError("invalid reserve")
    if request.attempts_for_step >= max_attempts_per_step:
        return Decision(False, None, "Retry cap reached")
    if request.estimated_wall_minutes <= 0 or request.vcpus < 1:
        return Decision(False, None, "Invalid resource estimate")
    if request.estimated_egress_gb < 0 or request.snapshot_gb < 0:
        return Decision(False, None, "Invalid resource estimate")

    if request.kind in {"ci", "frontend_test"} and request.public_repo and request.standard_runner:
        if request.total_job_minutes_today + request.estimated_wall_minutes > max_ci_minutes_per_day:
            return Decision(False, None, "Daily CI cap reached")
        if request.estimated_wall_minutes > 60:
            return Decision(False, None, "Single-job CI cap exceeded")
        return Decision(True, "github_actions", "Approved public standard runner")

    if request.kind != "interactive":
        return Decision(False, None, "No approved no-cost executor")

    if request.estimated_wall_minutes > max_vercel_minutes or request.vcpus > 4:
        return Decision(False, None, "Hobby sandbox safety limits exceeded")
    if vercel is None or vercel.observed_at.tzinfo is None:
        return Decision(False, None, "No trustworthy Vercel quota")
    if now - vercel.observed_at > timedelta(minutes=15):
        return Decision(False, None, "Vercel usage stale")
    if vercel.observed_at > now + timedelta(minutes=1):
        return Decision(False, None, "Vercel usage timestamp invalid")
    if not vercel.hard_no_overage_verified:
        return Decision(False, None, "Hard billing boundary not confirmed")
    remaining = (
        vercel.cpu_hours_remaining, vercel.memory_gb_hours_remaining,
        vercel.transfer_gb_remaining, vercel.creations_remaining,
        vercel.snapshot_gb_remaining,
    )
    if any(value is None or value < 0 for value in remaining):
        return Decision(False, None, "Missing Vercel quota")

    needs = (
        request.vcpus * request.estimated_wall_minutes / 60,
        (2 * request.vcpus) * request.estimated_wall_minutes / 60,
        request.estimated_egress_gb, 1, request.snapshot_gb,
    )
    if any(need > available * (1 - reserve_fraction)
           for need, available in zip(needs, remaining)):
        return Decision(False, None, "Resource reserve would be exceeded")
    return Decision(
        True, "vercel_sandbox",
        "Bounded session with verified quota; stop and check actual usage",
        "Hobby billing exposure depends on verified provider controls",
    )
