# 7. State Model, Data, Security & Observability

## 7.1 Core State Object (LangGraph State)

The system maintains a single, typed, versioned state object that travels through the graph:

```python
class InvestigationState(TypedDict):
    # Identity
    run_id: str
    test_id: str
    failure_id: str
    timestamp: datetime

    # Failure Context
    failure_type: str                    # from Router
    failure_message: str
    stack_trace: Optional[str]
    test_metadata: dict
    environment: str
    application_version: str
    test_data_context: dict

    # Execution Control
    investigation_count: int
    retry_count: int
    recovery_attempt_count: int
    max_investigation: int               # hard limit
    max_retries: int
    max_recovery_attempts: int

    # Evidence & Reasoning
    evidence: list[EvidenceItem]
    agent_findings: list[AgentFinding]
    rca_result: Optional[RCAResult]
    selected_rca: Optional[str]
    confidence: float

    # Action & Outcome
    recommended_action: Optional[ActionProposal]
    executed_action: Optional[str]
    action_result: Optional[dict]
    evaluation_result: Optional[str]     # SUCCESS | FAILED_RECOVERY | UNCERTAIN | ESCALATE

    # Human Control
    approval_required: bool
    approval_status: Optional[str]       # PENDING | APPROVED | REJECTED
    human_notes: Optional[str]

    # Final
    final_diagnosis: Optional[str]
    status: str                          # IN_PROGRESS | RESOLVED | ESCALATED | ABORTED
```

State is checkpointed after every major node so that partial progress is never lost and concurrent executions are safe.

## 7.2 Data Model (Persistence)

**Relational (PostgreSQL)**
- `failure_events`
- `investigations`
- `evidence_items`
- `rca_results`
- `actions_executed`
- `audit_log`
- `historical_resolutions`

**Vector (pgvector or dedicated store)**
- Embeddings of failure messages + RCA summaries for similarity search

**What is stored:**
- Structured failure signatures
- Evidence summaries (not raw secrets)
- Final RCA + confidence
- Successful recovery actions
- Human approval decisions

**What is never stored in clear text:**
- Credentials
- Full production data dumps
- Unmasked PII

## 7.3 Security Model

| Control                      | Implementation                                      |
|-----------------------------|-----------------------------------------------------|
| Least Privilege             | Agents receive only required tools                  |
| Secret Isolation            | Secrets never enter LLM context                     |
| Data Masking                | PII and tokens redacted before any model call       |
| Approval Gates              | Level 3+ actions require human approval             |
| Audit Logging               | Every tool call, decision, and state change logged  |
| Destructive Action Ban      | No tools that delete production data or change infra|
| Network Isolation           | Agents run in restricted network contexts           |
| Model Output Validation     | Structured output parsing + schema enforcement      |

## 7.4 Observability Model

Every investigation produces a complete OpenTelemetry trace containing:

- Graph node execution order and latency
- Every tool call (input summary, output summary, duration)
- Token usage and estimated cost per agent
- Confidence scores at each decision point
- Final RCA and evaluation result
- Human approval events

**Key Questions the system must be able to answer from the audit trail:**

1. Why was this failure classified as X?
2. Which evidence was collected and which was missing?
3. What facts vs inferences led to the root cause conclusion?
4. Why was this particular recovery action chosen?
5. Did the recovery actually resolve the original failure?
6. Where did the system spend the most time / tokens?

## 7.5 Failure Handling Matrix

| Failure Scenario              | System Behavior                                      |
|------------------------------|------------------------------------------------------|
| Invalid model output         | Retry with stricter schema or escalate               |
| Tool timeout / failure       | Record partial evidence and continue if possible     |
| Missing screenshot / logs    | Proceed with available evidence + lower confidence   |
| Conflicting evidence         | Surface conflict explicitly in RCA → escalate        |
| Low confidence               | Force human escalation                               |
| Max retries / investigations | Escalate with full current diagnosis                 |
| Concurrent same test failure | Deduplicate via run_id / test_id locking             |
| Corrupted state              | Abort safely and create incident                     |
