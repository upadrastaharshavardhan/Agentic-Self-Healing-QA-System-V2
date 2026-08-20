"""
Strongly-typed Pydantic models used throughout the system.
All critical LLM outputs are constrained by these schemas.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class FailureType(str, Enum):
    UI_FAILURE = "UI_FAILURE"
    LOCATOR_FAILURE = "LOCATOR_FAILURE"
    TIMEOUT_FAILURE = "TIMEOUT_FAILURE"
    API_FAILURE = "API_FAILURE"
    DATA_FAILURE = "DATA_FAILURE"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
    AUTH_FAILURE = "AUTH_FAILURE"
    DEPLOYMENT_FAILURE = "DEPLOYMENT_FAILURE"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    FLAKY_FAILURE = "FLAKY_FAILURE"
    ASSERTION_FAILURE = "ASSERTION_FAILURE"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionType(str, Enum):
    RETRY_TEST = "RETRY_TEST"
    WAIT_AND_RETRY = "WAIT_AND_RETRY"
    REFRESH_SESSION = "REFRESH_SESSION"
    REFETCH_TEST_DATA = "REFETCH_TEST_DATA"
    PROPOSE_LOCATOR_UPDATE = "PROPOSE_LOCATOR_UPDATE"
    COLLECT_MORE_EVIDENCE = "COLLECT_MORE_EVIDENCE"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    NO_ACTION = "NO_ACTION"


class EvaluationResult(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED_RECOVERY = "FAILED_RECOVERY"
    UNCERTAIN = "UNCERTAIN"
    ESCALATE = "ESCALATE"


class InvestigationStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    ABORTED = "ABORTED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"


class HealingLevel(int, Enum):
    LEVEL_0_DIAGNOSIS_ONLY = 0
    LEVEL_1_SAFE_RETRY = 1
    LEVEL_2_NON_DESTRUCTIVE = 2
    LEVEL_3_PROPOSE_MODIFICATION = 3
    LEVEL_4_HUMAN_APPROVED = 4
    LEVEL_5_RESTRICTED_AUTONOMOUS = 5


# ─────────────────────────────────────────────────────────────────────────────
# Core Input / Failure Event
# ─────────────────────────────────────────────────────────────────────────────

class TestMetadata(BaseModel):
    test_name: str
    test_file: Optional[str] = None
    suite: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    timeout_ms: Optional[int] = None
    browser: Optional[str] = "chromium"
    framework: Literal["playwright", "pytest", "selenium", "cypress"] = "playwright"


class FailureEvent(BaseModel):
    """Normalized failure event ingested from the test runner."""
    failure_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    test_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    failure_message: str
    stack_trace: Optional[str] = None
    test_metadata: TestMetadata
    environment: str = "qa"
    application_version: Optional[str] = None
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    browser_trace_path: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Classification (Router Output)
# ─────────────────────────────────────────────────────────────────────────────

class ClassificationResult(BaseModel):
    failure_type: FailureType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    secondary_types: list[FailureType] = Field(default_factory=list)
    requires_escalation: bool = False

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


# ─────────────────────────────────────────────────────────────────────────────
# Evidence
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str  # e.g. "screenshot", "dom", "application_logs", "historical"
    agent: str
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    content: dict[str, Any]
    summary: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    raw_refs: list[str] = Field(default_factory=list)  # file paths, log URLs etc.


class AgentFinding(BaseModel):
    agent_name: str
    findings: list[str]
    evidence_ids: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    errors: list[str] = Field(default_factory=list)
    duration_ms: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────────────
# RCA (Strict separation of Fact / Observation / Inference / Hypothesis)
# ─────────────────────────────────────────────────────────────────────────────

class Hypothesis(BaseModel):
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    rationale: str


class Recommendation(BaseModel):
    action: ActionType
    risk_level: RiskLevel
    healing_level: HealingLevel
    rationale: str
    expected_outcome: str
    validation_method: str
    requires_approval: bool = False
    parameters: dict[str, Any] = Field(default_factory=dict)


class RCAResult(BaseModel):
    """
    The heart of the system.
    The model is forced to separate FACT from INFERENCE.
    """
    facts: list[str] = Field(
        description="Directly observed data from tools. No interpretation."
    )
    observations: list[str] = Field(
        description="Derived measurements and tool conclusions."
    )
    inferences: list[str] = Field(
        description="Logical conclusions drawn from facts + observations."
    )
    hypotheses: list[Hypothesis]
    selected_root_cause: str
    overall_confidence: float = Field(ge=0.0, le=1.0)
    recommendation: Recommendation
    evidence_summary: str
    conflicting_evidence: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Action & Evaluation
# ─────────────────────────────────────────────────────────────────────────────

class ActionProposal(BaseModel):
    action: ActionType
    risk_level: RiskLevel
    healing_level: HealingLevel
    rationale: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    expected_outcome: str
    validation_method: str
    rollback_strategy: str = "None – non-destructive"


class ActionResult(BaseModel):
    action: ActionType
    success: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[int] = None
    new_failure_detected: bool = False


class EvaluationOutcome(BaseModel):
    result: EvaluationResult
    original_failure_resolved: bool
    new_failures_introduced: bool
    evidence_consistent: bool
    confidence_still_high: bool
    rationale: str
    should_retry_investigation: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Final Diagnosis
# ─────────────────────────────────────────────────────────────────────────────

class FinalDiagnosis(BaseModel):
    failure_id: str
    status: InvestigationStatus
    failure_type: FailureType
    selected_root_cause: str
    confidence: float
    facts: list[str]
    observations: list[str]
    inferences: list[str]
    recommendation: Optional[Recommendation] = None
    executed_actions: list[ActionResult] = Field(default_factory=list)
    evaluation: Optional[EvaluationOutcome] = None
    evidence_trail: list[EvidenceItem] = Field(default_factory=list)
    investigation_iterations: int
    retry_count: int
    human_approval_required: bool = False
    human_approval_status: Optional[str] = None
    final_message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
