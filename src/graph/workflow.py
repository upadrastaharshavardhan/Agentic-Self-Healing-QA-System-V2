"""
LangGraph workflow definition – the executable investigation pipeline.

Design principles applied:
- Deterministic edges where the path is known
- Conditional edges only for real decision points
- Hard bounds enforced via state counters
- Clear separation of nodes with single responsibility
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph

from src.graph.nodes import (
    action_gate_node,
    classify_node,
    collect_evidence_node,
    evaluate_node,
    finalize_node,
    initialize_node,
    rca_node,
    recover_node,
)
from src.models.schemas import EvaluationResult, InvestigationStatus
from src.state import InvestigationState


def _should_collect_evidence(state: InvestigationState) -> Literal["collect", "escalate"]:
    if state.get("approval_required") and state.get("classification") and state["classification"].requires_escalation:
        return "escalate"
    return "collect"


def _after_action_gate(state: InvestigationState) -> Literal["recover", "await_approval", "finalize"]:
    status = state.get("status")
    if status == InvestigationStatus.AWAITING_APPROVAL:
        return "await_approval"
    if status == InvestigationStatus.ESCALATED:
        return "finalize"
    return "recover"


def _after_evaluate(state: InvestigationState) -> Literal["reinvestigate", "finalize"]:
    evaluation = state.get("evaluation")
    if evaluation and evaluation.should_retry_investigation:
        # Bound check already done inside evaluate_node
        if state.get("investigation_count", 0) < state.get("max_investigation", 3):
            return "reinvestigate"
    return "finalize"


def build_investigation_graph() -> StateGraph:
    graph = StateGraph(InvestigationState)

    # Register nodes
    graph.add_node("initialize", initialize_node)
    graph.add_node("classify", classify_node)
    graph.add_node("collect_evidence", collect_evidence_node)
    graph.add_node("rca", rca_node)
    graph.add_node("action_gate", action_gate_node)
    graph.add_node("recover", recover_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("finalize", finalize_node)

    # Entry
    graph.set_entry_point("initialize")

    # Linear happy path with conditional branches
    graph.add_edge("initialize", "classify")

    graph.add_conditional_edges(
        "classify",
        _should_collect_evidence,
        {
            "collect": "collect_evidence",
            "escalate": "finalize",  # early escalation for UNKNOWN / low conf
        },
    )

    graph.add_edge("collect_evidence", "rca")
    graph.add_edge("rca", "action_gate")

    graph.add_conditional_edges(
        "action_gate",
        _after_action_gate,
        {
            "recover": "recover",
            "await_approval": "finalize",  # MVP: treat approval wait as terminal for now
            "finalize": "finalize",
        },
    )

    graph.add_edge("recover", "evaluate")

    graph.add_conditional_edges(
        "evaluate",
        _after_evaluate,
        {
            "reinvestigate": "collect_evidence",  # bounded loop back
            "finalize": "finalize",
        },
    )

    graph.add_edge("finalize", END)

    return graph


def compile_graph(checkpointer=None):
    """Compile the graph, optionally with a checkpointer for persistence."""
    builder = build_investigation_graph()
    return builder.compile(checkpointer=checkpointer)
