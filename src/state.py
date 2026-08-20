"""
LangGraph State definition.
This is the single source of truth that travels through the entire graph.
Designed to be minimal, typed, traceable, and safely updatable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Optional, Sequence
from typing_extensions import TypedDict
from operator import add

from src.models.schemas import (
    ActionProposal,
    ActionResult,
    AgentFinding,
    ClassificationResult,
    EvaluationOutcome,
    EvidenceItem,
    FailureEvent,
    FailureType,
    FinalDiagnosis,
    InvestigationStatus,
    RCAResult,
    Recommendation,
)


def merge_evidence(existing: list[EvidenceItem], new: list[EvidenceItem]) -> list[EvidenceItem]:
    """Reducer that appends new evidence while preventing exact duplicates by evidence_id."""
    seen = {e.evidence_id for e in existing}
    merged = list(existing)
    for item in new:
        if item.evidence_id not in seen:
            merged.append(item)
            seen.add(item.evidence_id)
    return merged


def merge_findings(existing: list[AgentFinding], new: list[AgentFinding]) -> list[AgentFinding]:
    return list(existing) + list(new)


class InvestigationState(TypedDict, total=False):
    # ── Identity ──────────────────────────────────────────────────────────
    run_id: str
    failure_id: str
    test_id: str

    # ── Original Failure ──────────────────────────────────────────────────
    failure_event: FailureEvent
    failure_type: Optional[FailureType]
    classification: Optional[ClassificationResult]

    # ── Control Counters (hard bounds) ────────────────────────────────────
    investigation_count: int
    retry_count: int
    recovery_attempt_count: int
    max_investigation: int
    max_retries: int
    max_recovery_attempts: int

    # ── Evidence & Reasoning ──────────────────────────────────────────────
    evidence: Annotated[list[EvidenceItem], merge_evidence]
    agent_findings: Annotated[list[AgentFinding], merge_findings]
    rca_result: Optional[RCAResult]
    selected_rca: Optional[str]
    confidence: float

    # ── Action & Outcome ──────────────────────────────────────────────────
    recommended_action: Optional[ActionProposal]
    executed_actions: Annotated[list[ActionResult], add]
    last_action_result: Optional[ActionResult]
    evaluation: Optional[EvaluationOutcome]

    # ── Human Control ─────────────────────────────────────────────────────
    approval_required: bool
    approval_status: Optional[str]  # PENDING | APPROVED | REJECTED
    human_notes: Optional[str]

    # ── Final ─────────────────────────────────────────────────────────────
    status: InvestigationStatus
    final_diagnosis: Optional[FinalDiagnosis]
    error_messages: Annotated[list[str], add]

    # ── Metadata ──────────────────────────────────────────────────────────
    started_at: datetime
    updated_at: datetime
    messages: Annotated[list[dict[str, Any]], add]  # optional chat-style history
