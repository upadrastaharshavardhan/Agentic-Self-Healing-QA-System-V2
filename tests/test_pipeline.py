"""
End-to-end tests for the investigation pipeline (runs fully offline with mock LLM).
"""

import pytest
from src.graph.workflow import compile_graph
from src.models.schemas import (
    FailureEvent,
    FailureType,
    InvestigationStatus,
    TestMetadata,
)
from src.state import InvestigationState


@pytest.fixture
def graph():
    return compile_graph()


@pytest.mark.asyncio
async def test_locator_failure_path(graph):
    event = FailureEvent(
        test_id="test-login",
        failure_message="Error: locator 'button[data-testid=\"login-button\"]' not found",
        test_metadata=TestMetadata(test_name="test_login_button"),
    )
    initial: InvestigationState = {"failure_event": event}
    final = await graph.ainvoke(initial)

    diagnosis = final["final_diagnosis"]
    assert diagnosis is not None
    assert diagnosis.failure_type in (FailureType.LOCATOR_FAILURE, FailureType.UI_FAILURE)
    assert diagnosis.confidence >= 0.7
    assert len(diagnosis.facts) > 0
    assert len(diagnosis.evidence_trail) >= 4
    assert diagnosis.status in (
        InvestigationStatus.RESOLVED,
        InvestigationStatus.ESCALATED,
        InvestigationStatus.AWAITING_APPROVAL,
    )


@pytest.mark.asyncio
async def test_timeout_flake_path(graph):
    event = FailureEvent(
        test_id="test-checkout",
        failure_message="Timeout 30000ms exceeded while waiting for element to be visible",
        test_metadata=TestMetadata(test_name="test_checkout_flow"),
    )
    initial: InvestigationState = {"failure_event": event}
    final = await graph.ainvoke(initial)

    diagnosis = final["final_diagnosis"]
    assert diagnosis is not None
    assert diagnosis.failure_type in (FailureType.TIMEOUT_FAILURE, FailureType.FLAKY_FAILURE)
    assert "flake" in diagnosis.selected_root_cause.lower() or "timing" in diagnosis.selected_root_cause.lower()


@pytest.mark.asyncio
async def test_unknown_forces_escalation(graph):
    event = FailureEvent(
        test_id="test-weird",
        failure_message="Completely novel and unrecognizable failure xyz-987",
        test_metadata=TestMetadata(test_name="test_weird"),
    )
    initial: InvestigationState = {"failure_event": event}
    final = await graph.ainvoke(initial)

    diagnosis = final["final_diagnosis"]
    assert diagnosis is not None
    # Low confidence or unknown should escalate or produce low-confidence diagnosis
    assert diagnosis.confidence < 0.7 or diagnosis.status == InvestigationStatus.ESCALATED
