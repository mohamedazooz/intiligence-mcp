"""Human/operator escalation contract; no automatic challenge bypass."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Escalation:
    status: str
    reason: str
    requires_operator: bool = True


def escalate_challenge(category: str) -> Escalation:
    return Escalation("requires_human_review", f"Access challenge detected: {category}")
