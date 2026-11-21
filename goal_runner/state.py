"""Fail-closed goal transitions; a durable external store must enforce CAS."""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json

VALID_STATES = frozenset({
    "DRAFT", "PLANNING", "EXECUTING", "AWAITING_CI", "VERIFYING",
    "BLOCKED", "PAUSED", "COMPLETED",
})
TRANSITIONS = {
    "DRAFT": {"PLANNING", "PAUSED"},
    "PLANNING": {"EXECUTING", "BLOCKED", "PAUSED"},
    "EXECUTING": {"AWAITING_CI", "VERIFYING", "BLOCKED", "PAUSED"},
    "AWAITING_CI": {"VERIFYING", "BLOCKED", "PAUSED"},
    "VERIFYING": {"EXECUTING", "COMPLETED", "BLOCKED", "PAUSED"},
    "BLOCKED": {"PLANNING", "EXECUTING", "PAUSED"},
    "PAUSED": {"PLANNING", "EXECUTING", "BLOCKED"},
    "COMPLETED": set(),
}

class StateConflict(ValueError):
    """Invalid transition, stale revision or conflicting duplicate event."""

def digest_event(target: str, evidence_ref: str | None, checks: tuple[str, ...]) -> str:
    blob = json.dumps({
        "target": target, "evidence_ref": evidence_ref, "checks": sorted(checks),
    }, sort_keys=True, separators=(",", ":"))
    return sha256(blob.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class GoalState:
    goal_id: str
    status: str = "DRAFT"
    revision: int = 0
    last_evidence_ref: str | None = None
    events: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.goal_id or self.status not in VALID_STATES or self.revision < 0:
            raise ValueError("Invalid goal state")

    def transition(
        self, *, expected_revision: int, event_id: str, target: str,
        evidence_ref: str | None = None, verified_checks: tuple[str, ...] = (),
    ) -> "GoalState":
        if not event_id or target not in VALID_STATES:
            raise StateConflict("Invalid event or target")
        fingerprint = digest_event(target, evidence_ref, verified_checks)
        previous = dict(self.events)
        if event_id in previous:
            if previous[event_id] != fingerprint:
                raise StateConflict("Event ID reused with different payload")
            return self
        if self.revision != expected_revision:
            raise StateConflict("Stale revision: reread canonical state")
        if target not in TRANSITIONS[self.status]:
            raise StateConflict(f"Transition {self.status} -> {target} not allowed")
        if target == "COMPLETED" and (not evidence_ref or not verified_checks):
            raise StateConflict("Completion requires evidence and verified checks")
        return replace(
            self, status=target, revision=self.revision + 1,
            last_evidence_ref=evidence_ref or self.last_evidence_ref,
            events=(*self.events, (event_id, fingerprint)),
        )

    def to_dict(self) -> dict:
        return {
            "goal_id": self.goal_id, "status": self.status, "revision": self.revision,
            "last_evidence_ref": self.last_evidence_ref,
            "events": [{"id": event_id, "hash": digest} for event_id, digest in self.events],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GoalState":
        return cls(
            goal_id=data["goal_id"], status=data.get("status", "DRAFT"),
            revision=data.get("revision", 0),
            last_evidence_ref=data.get("last_evidence_ref"),
            events=tuple((event["id"], event["hash"]) for event in data.get("events", [])),
        )
