"""
FastAPI surface for the Agentic Self-Healing QA System.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import get_settings
from src.graph.workflow import compile_graph
from src.models.schemas import FailureEvent, FinalDiagnosis, TestMetadata
from src.state import InvestigationState

settings = get_settings()

app = FastAPI(
    title="Agentic Self-Healing QA System",
    description="Production-oriented autonomous test failure investigation & bounded recovery",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvestigateRequest(BaseModel):
    failure_message: str
    test_name: str = "api_triggered_test"
    test_id: str | None = None
    environment: str = "qa"
    stack_trace: str | None = None
    application_version: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agentic-self-healing-qa"}


@app.post("/api/v1/investigate", response_model=FinalDiagnosis)
async def investigate(req: InvestigateRequest):
    event = FailureEvent(
        test_id=req.test_id or f"test-{req.test_name}",
        failure_message=req.failure_message,
        stack_trace=req.stack_trace,
        test_metadata=TestMetadata(test_name=req.test_name),
        environment=req.environment,
        application_version=req.application_version,
    )

    initial: InvestigationState = {"failure_event": event}
    graph = compile_graph()

    try:
        final_state = await graph.ainvoke(initial)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    diagnosis = final_state.get("final_diagnosis")
    if not diagnosis:
        raise HTTPException(status_code=500, detail="No diagnosis produced")
    return diagnosis


@app.get("/")
async def root():
    return {
        "service": "Agentic Self-Healing QA System",
        "docs": "/docs",
        "investigate": "POST /api/v1/investigate",
    }
