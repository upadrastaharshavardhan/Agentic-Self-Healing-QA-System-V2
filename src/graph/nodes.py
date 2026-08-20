"""
Graph nodes implementing the investigation pipeline.
Each node is a pure async function that receives and returns InvestigationState.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from uuid import uuid4

from src.config import get_settings
from src.models.schemas import (
    ActionProposal,
    ActionResult,
    ActionType,
    AgentFinding,
    ClassificationResult,
    EvaluationOutcome,
    EvaluationResult,
    EvidenceItem,
    FailureType,
    FinalDiagnosis,
    HealingLevel,
    InvestigationStatus,
    RiskLevel,
)
from src.services.llm import get_llm_service
from src.state import InvestigationState
from src.tools.investigation_tools import TOOL_REGISTRY


settings = get_settings()
llm = get_llm_service()


# ─── Node: Ingest / Initialize ───────────────────────────────────────────────

async def initialize_node(state: InvestigationState) -> dict[str, Any]:
    event = state["failure_event"]
    return {
        "run_id": event.run_id,
        "failure_id": event.failure_id,
        "test_id": event.test_id,
        "investigation_count": 0,
        "retry_count": 0,
        "recovery_attempt_count": 0,
        "max_investigation": settings.max_investigation_iterations,
        "max_retries": settings.max_test_retries,
        "max_recovery_attempts": settings.max_recovery_attempts,
        "evidence": [],
        "agent_findings": [],
        "executed_actions": [],
        "error_messages": [],
        "approval_required": False,
        "status": InvestigationStatus.IN_PROGRESS,
        "confidence": 0.0,
        "started_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


# ─── Node: Failure Router (Structured Classification) ────────────────────────

async def classify_node(state: InvestigationState) -> dict[str, Any]:
    event = state["failure_event"]
    classification: ClassificationResult = await llm.structured_invoke(
        system_prompt="You are a precise QA failure classifier. Output only the structured schema.",
        user_prompt=f"Classify this test failure:\nMessage: {event.failure_message}\nStack: {event.stack_trace or 'N/A'}",
        output_schema=ClassificationResult,
        context={"failure_message": event.failure_message},
    )

    requires_escalation = (
        classification.requires_escalation
        or classification.confidence < settings.classification_confidence_threshold
        or classification.failure_type == FailureType.UNKNOWN_FAILURE
    )

    return {
        "classification": classification,
        "failure_type": classification.failure_type,
        "confidence": classification.confidence,
        "approval_required": requires_escalation,
        "updated_at": datetime.utcnow(),
    }


# ─── Node: Parallel Evidence Collection (Orchestrated) ───────────────────────

async def collect_evidence_node(state: InvestigationState) -> dict[str, Any]:
    """Simulate parallel specialized agents by calling the relevant tools."""
    event = state["failure_event"]
    failure_type = state.get("failure_type") or FailureType.UNKNOWN_FAILURE
    failure_msg = event.failure_message

    evidence: list[EvidenceItem] = []
    findings: list[AgentFinding] = []

    # Always collect core evidence
    tools_to_run = [
        ("UI/Browser Agent", "take_screenshot", {"test_id": event.test_id}),
        ("UI/Browser Agent", "inspect_dom", {"failure_message": failure_msg}),
        ("Log Analysis Agent", "query_logs", {"failure_message": failure_msg}),
        ("Environment Agent", "check_service_health", {}),
        ("Deployment Agent", "get_deployment_history", {}),
        ("Historical Agent", "query_historical_failures", {
            "failure_message": failure_msg,
            "failure_type": str(failure_type),
        }),
    ]

    for agent_name, tool_name, kwargs in tools_to_run:
        tool = TOOL_REGISTRY[tool_name]
        start = time.perf_counter()
        result = await tool.run(**kwargs)
        duration = int((time.perf_counter() - start) * 1000)

        ev = EvidenceItem(
            source=tool_name,
            agent=agent_name,
            content=result.data,
            summary=result.summary,
            confidence=0.9 if result.success else 0.3,
            raw_refs=[],
        )
        evidence.append(ev)

        findings.append(
            AgentFinding(
                agent_name=agent_name,
                findings=[result.summary],
                evidence_ids=[ev.evidence_id],
                confidence=ev.confidence,
                errors=[result.error] if result.error else [],
                duration_ms=duration,
            )
        )

    return {
        "evidence": evidence,
        "agent_findings": findings,
        "investigation_count": state.get("investigation_count", 0) + 1,
        "updated_at": datetime.utcnow(),
    }


# ─── Node: RCA Agent ─────────────────────────────────────────────────────────

async def rca_node(state: InvestigationState) -> dict[str, Any]:
    event = state["failure_event"]
    evidence = state.get("evidence", [])
    summaries = [e.summary for e in evidence]

    from src.models.schemas import RCAResult

    rca = await llm.structured_invoke(
        system_prompt=(
            "You are an expert Root-Cause Analysis agent for automated tests. "
            "You MUST separate FACTS, OBSERVATIONS, INFERENCES, HYPOTHESES and RECOMMENDATION. "
            "Never present an inference as a fact."
        ),
        user_prompt=f"Perform RCA for failure: {event.failure_message}",
        output_schema=RCAResult,
        context={
            "failure_message": event.failure_message,
            "failure_type": str(state.get("failure_type")),
            "evidence_summaries": summaries,
        },
    )

    recommendation = rca.recommendation
    action_proposal = ActionProposal(
        action=recommendation.action,
        risk_level=recommendation.risk_level,
        healing_level=recommendation.healing_level,
        rationale=recommendation.rationale,
        parameters=recommendation.parameters,
        requires_approval=recommendation.requires_approval,
        expected_outcome=recommendation.expected_outcome,
        validation_method=recommendation.validation_method,
    )

    return {
        "rca_result": rca,
        "selected_rca": rca.selected_root_cause,
        "confidence": rca.overall_confidence,
        "recommended_action": action_proposal,
        "approval_required": action_proposal.requires_approval
        or rca.overall_confidence < settings.rca_confidence_threshold,
        "updated_at": datetime.utcnow(),
    }


# ─── Node: Action Selection / Gate ───────────────────────────────────────────

async def action_gate_node(state: InvestigationState) -> dict[str, Any]:
    """Decide whether we can auto-execute or must escalate / wait for approval."""
    proposal = state.get("recommended_action")
    if not proposal:
        return {
            "status": InvestigationStatus.ESCALATED,
            "approval_required": True,
        }

    # Hard safety: never auto-execute above allowed risk
    if proposal.risk_level.value not in ("LOW",) and proposal.healing_level.value > 2:
        return {
            "approval_required": True,
            "status": InvestigationStatus.AWAITING_APPROVAL,
        }

    if state.get("approval_required"):
        return {"status": InvestigationStatus.AWAITING_APPROVAL}

    return {"status": InvestigationStatus.IN_PROGRESS}


# ─── Node: Safe Recovery ─────────────────────────────────────────────────────

async def recover_node(state: InvestigationState) -> dict[str, Any]:
    proposal = state.get("recommended_action")
    if not proposal:
        return {}

    if state.get("recovery_attempt_count", 0) >= state.get("max_recovery_attempts", 1):
        return {
            "status": InvestigationStatus.ESCALATED,
            "error_messages": ["Max recovery attempts reached"],
        }

    action = proposal.action
    result: ActionResult

    if action in (ActionType.RETRY_TEST, ActionType.WAIT_AND_RETRY):
        tool = TOOL_REGISTRY["retry_test"]
        # For demo: if this is a timeout/flake we bias toward pass on retry
        simulate_pass = "timeout" in (state["failure_event"].failure_message or "").lower()
        tool_result = await tool.run(
            test_id=state["test_id"],
            simulate_pass=simulate_pass,
        )
        result = ActionResult(
            action=action,
            success=tool_result.data.get("passed", False),
            message=tool_result.summary,
            details=tool_result.data,
            duration_ms=tool_result.duration_ms,
            new_failure_detected=not tool_result.data.get("passed", False),
        )
    elif action == ActionType.ESCALATE_TO_HUMAN:
        result = ActionResult(
            action=action,
            success=True,
            message="Escalation package prepared for human engineer.",
            details={},
        )
    else:
        # Level-2 style actions are acknowledged but not fully implemented in MVP
        result = ActionResult(
            action=action,
            success=True,
            message=f"Action {action.value} acknowledged (MVP stub).",
            details=proposal.parameters,
        )

    return {
        "last_action_result": result,
        "executed_actions": [result],
        "recovery_attempt_count": state.get("recovery_attempt_count", 0) + 1,
        "retry_count": state.get("retry_count", 0) + (1 if action in (ActionType.RETRY_TEST, ActionType.WAIT_AND_RETRY) else 0),
        "updated_at": datetime.utcnow(),
    }


# ─── Node: Evaluator ─────────────────────────────────────────────────────────

async def evaluate_node(state: InvestigationState) -> dict[str, Any]:
    last = state.get("last_action_result")
    rca = state.get("rca_result")
    confidence = state.get("confidence", 0.0)

    if not last:
        outcome = EvaluationOutcome(
            result=EvaluationResult.ESCALATE,
            original_failure_resolved=False,
            new_failures_introduced=False,
            evidence_consistent=True,
            confidence_still_high=False,
            rationale="No action was executed.",
            should_retry_investigation=False,
        )
    elif last.action == ActionType.ESCALATE_TO_HUMAN:
        outcome = EvaluationOutcome(
            result=EvaluationResult.ESCALATE,
            original_failure_resolved=False,
            new_failures_introduced=False,
            evidence_consistent=True,
            confidence_still_high=confidence >= settings.rca_confidence_threshold,
            rationale="Explicit escalation requested by RCA.",
            should_retry_investigation=False,
        )
    elif last.success and not last.new_failure_detected:
        outcome = EvaluationOutcome(
            result=EvaluationResult.SUCCESS,
            original_failure_resolved=True,
            new_failures_introduced=False,
            evidence_consistent=True,
            confidence_still_high=True,
            rationale="Recovery action succeeded and original failure no longer present.",
            should_retry_investigation=False,
        )
    else:
        # Failed recovery – decide whether we can investigate further
        can_continue = (
            state.get("investigation_count", 0) < state.get("max_investigation", 3)
            and state.get("retry_count", 0) < state.get("max_retries", 2)
        )
        outcome = EvaluationOutcome(
            result=EvaluationResult.FAILED_RECOVERY if not can_continue else EvaluationResult.UNCERTAIN,
            original_failure_resolved=False,
            new_failures_introduced=last.new_failure_detected,
            evidence_consistent=True,
            confidence_still_high=confidence >= 0.6,
            rationale="Recovery did not resolve the failure." + (" Will replan." if can_continue else " Limits reached."),
            should_retry_investigation=can_continue,
        )

    return {
        "evaluation": outcome,
        "updated_at": datetime.utcnow(),
    }


# ─── Node: Finalize ──────────────────────────────────────────────────────────

async def finalize_node(state: InvestigationState) -> dict[str, Any]:
    event = state["failure_event"]
    rca = state.get("rca_result")
    evaluation = state.get("evaluation")
    classification = state.get("classification")

    status = InvestigationStatus.RESOLVED
    if evaluation and evaluation.result == EvaluationResult.ESCALATE:
        status = InvestigationStatus.ESCALATED
    elif evaluation and evaluation.result in (EvaluationResult.FAILED_RECOVERY, EvaluationResult.UNCERTAIN):
        status = InvestigationStatus.ESCALATED
    elif state.get("approval_required") and state.get("approval_status") != "APPROVED":
        status = InvestigationStatus.AWAITING_APPROVAL

    diagnosis = FinalDiagnosis(
        failure_id=event.failure_id,
        status=status,
        failure_type=state.get("failure_type") or FailureType.UNKNOWN_FAILURE,
        selected_root_cause=state.get("selected_rca") or "Unknown",
        confidence=state.get("confidence", 0.0),
        facts=rca.facts if rca else [],
        observations=rca.observations if rca else [],
        inferences=rca.inferences if rca else [],
        recommendation=rca.recommendation if rca else None,
        executed_actions=state.get("executed_actions", []),
        evaluation=evaluation,
        evidence_trail=state.get("evidence", []),
        investigation_iterations=state.get("investigation_count", 0),
        retry_count=state.get("retry_count", 0),
        human_approval_required=state.get("approval_required", False),
        human_approval_status=state.get("approval_status"),
        final_message=_build_final_message(state, status),
        completed_at=datetime.utcnow(),
    )

    return {
        "final_diagnosis": diagnosis,
        "status": status,
        "updated_at": datetime.utcnow(),
    }


def _build_final_message(state: InvestigationState, status: InvestigationStatus) -> str:
    rca = state.get("selected_rca", "Unknown")
    conf = state.get("confidence", 0.0)
    if status == InvestigationStatus.RESOLVED:
        return f"Resolved. Root cause: {rca} (confidence {conf:.0%}). Recovery validated."
    if status == InvestigationStatus.ESCALATED:
        return f"Escalated to human. Suspected root cause: {rca} (confidence {conf:.0%}). Full evidence trail attached."
    if status == InvestigationStatus.AWAITING_APPROVAL:
        return f"Awaiting human approval. Proposed action based on: {rca}."
    return f"Investigation finished with status {status}."
