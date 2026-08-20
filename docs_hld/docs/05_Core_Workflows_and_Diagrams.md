# 5. Core Workflows & Advanced Flow Diagrams

## 5.1 End-to-End Investigation Flow (Primary Sequence)

```mermaid
sequenceDiagram
    autonumber
    participant TR as Test Runner
    participant FI as Failure Ingestion
    participant FR as Failure Router
    participant OR as Orchestrator
    participant Agents as Specialized Agents
    participant AGG as Evidence Aggregator
    participant RCA as RCA Agent
    participant ACT as Action Selector
    participant REC as Safe Recovery
    participant EVAL as Evaluator
    participant HITL as Human Approval
    participant MEM as Historical Memory
    participant OUT as Final Diagnosis

    TR->>FI: Test Failure Event
    FI->>FR: Normalized Failure
    FR->>FR: Classify (Structured Output)
    FR->>OR: Failure Type + Confidence

    OR->>OR: Plan Investigation Tasks
    par Parallel Evidence Collection
        OR->>Agents: Log Analysis
        OR->>Agents: UI / DOM / Screenshot
        OR->>Agents: API Inspection
        OR->>Agents: Test Data Check
        OR->>Agents: Environment Health
        OR->>Agents: Deployment History
        OR->>Agents: Locator History
        OR->>Agents: Historical Similar Failures
    end

    Agents->>AGG: Evidence Packets
    AGG->>RCA: Aggregated Evidence
    RCA->>MEM: Query similar past cases
    MEM-->>RCA: Historical Context
    RCA->>RCA: Reason (Fact / Obs / Inf / Hyp / Rec)
    RCA->>ACT: RCA Result + Confidence

    alt Confidence High & Risk Low
        ACT->>REC: Execute Safe Action
        REC->>EVAL: Action Result
        EVAL->>EVAL: Validate Outcome
        alt Recovery Success
            EVAL->>OUT: Resolved + Diagnosis
        else Recovery Failed / Uncertain
            EVAL->>OR: Increment counters & replan (if limits allow)
        end
    else Confidence Low or Risk High
        ACT->>HITL: Request Approval
        HITL-->>ACT: Approve / Reject
        alt Approved
            ACT->>REC: Execute
        else Rejected
            ACT->>OUT: Escalate with full evidence
        end
    end

    OUT->>MEM: Store Outcome for future learning
```

## 5.2 Failure Router Decision Flow

```mermaid
flowchart TD
    Start([Test Failure Event]) --> Extract[Extract Failure Message<br/>Stack Trace<br/>Test Metadata<br/>Screenshot/DOM if available]
    Extract --> Classify[LLM Structured Classification]
    
    Classify --> Type{Failure Type}
    
    Type -->|UI / Locator / Timeout| UI[UI_FAILURE<br/>LOCATOR_FAILURE<br/>TIMEOUT_FAILURE]
    Type -->|HTTP / Contract| API[API_FAILURE]
    Type -->|Data Integrity| DATA[DATA_FAILURE]
    Type -->|Service Down / Health| ENV[ENVIRONMENT_FAILURE]
    Type -->|Auth / Session| AUTH[AUTH_FAILURE]
    Type -->|Recent Deploy Correlation| DEP[DEPLOYMENT_FAILURE]
    Type -->|Infra| INFRA[INFRASTRUCTURE_FAILURE]
    Type -->|Assertion| ASSERT[ASSERTION_FAILURE]
    Type -->|Intermittent Pattern| FLAKY[FLAKY_FAILURE]
    Type -->|Cannot Determine| UNK[UNKNOWN_FAILURE]
    
    UI --> Conf{Confidence ≥ Threshold?}
    API --> Conf
    DATA --> Conf
    ENV --> Conf
    AUTH --> Conf
    DEP --> Conf
    INFRA --> Conf
    ASSERT --> Conf
    FLAKY --> Conf
    UNK --> Escalate[Force Escalation Path]
    
    Conf -->|Yes| Route[Route to Orchestrator<br/>with Type + Confidence]
    Conf -->|No| Escalate
    
    Route --> End([Continue Investigation])
    Escalate --> Human([Human Review Required])
```

## 5.3 Self-Healing Levels (Safety State Machine)

```mermaid
stateDiagram-v2
    [*] --> Level0: Diagnosis Only
    
    Level0 --> Level1: Policy allows retry
    Level1 --> Level2: Non-destructive recovery permitted
    Level2 --> Level3: Propose test modification
    Level3 --> Level4: Human-approved modification
    Level4 --> Level5: Explicitly approved low-risk autonomous change
    
    Level0 --> Escalate: Low confidence or policy
    Level1 --> Escalate: Max retries reached
    Level2 --> Escalate: Validation failed
    Level3 --> HumanApproval
    Level4 --> HumanApproval
    Level5 --> HumanApproval: Only for pre-approved scenarios
    
    HumanApproval --> Level3: Approved
    HumanApproval --> Escalate: Rejected
    
    Level1 --> Success: Retry passed + validated
    Level2 --> Success: Recovery validated
    Level5 --> Success: Change validated
    
    Success --> [*]
    Escalate --> [*]
```

**Level Definitions**

| Level | Name                          | Autonomy                          | Typical Actions                              | Risk     |
|-------|-------------------------------|-----------------------------------|----------------------------------------------|----------|
| 0     | Diagnosis Only                | None                              | Produce RCA + evidence report                | None     |
| 1     | Safe Retry                    | Fully autonomous                  | Retry test, wait-and-retry                   | Very Low |
| 2     | Non-destructive Recovery      | Fully autonomous (bounded)        | Refresh session, re-fetch test data, clear cache | Low  |
| 3     | Propose Test Modification     | Proposal only                     | Suggest new locator / assertion change       | Medium   |
| 4     | Human-Approved Modification   | Requires explicit approval        | Apply locator update, data fix               | Medium-High |
| 5     | Fully Autonomous (Restricted) | Only pre-approved low-risk cases  | Explicitly allowed auto-fixes                | Controlled |

## 5.4 Orchestrator Parallel Task Planning

```mermaid
flowchart LR
    subgraph Orchestrator
        Plan[Analyze Failure Type<br/>+ Available Evidence]
        Plan --> Decide[Decide Required Investigations]
    end

    Decide --> T1[Task: Screenshot + DOM]
    Decide --> T2[Task: Application Logs]
    Decide --> T3[Task: API Traffic]
    Decide --> T4[Task: Test Data Validation]
    Decide --> T5[Task: Environment Health]
    Decide --> T6[Task: Deployment Diff]
    Decide --> T7[Task: Locator History]
    Decide --> T8[Task: Similar Historical Failures]

    T1 & T2 & T3 & T4 & T5 & T6 & T7 & T8 --> Aggregate[Evidence Aggregator]
```

## 5.5 RCA Reasoning Structure (Mandatory Separation)

```mermaid
flowchart TD
    Evidence[Aggregated Evidence] --> Facts[FACTS<br/>Directly observed data]
    Evidence --> Observations[OBSERVATIONS<br/>Derived from tools]
    Facts --> Inferences[INFERENCES<br/>Logical conclusions]
    Observations --> Inferences
    Inferences --> Hypotheses[HYPOTHESES<br/>Possible root causes ranked]
    Hypotheses --> Recommendation[RECOMMENDATION<br/>Best next action + risk]
    
    style Facts fill:#d4edda
    style Observations fill:#cce5ff
    style Inferences fill:#fff3cd
    style Hypotheses fill:#f8d7da
    style Recommendation fill:#e2e3e5
```

The RCA Agent is **forbidden** from presenting an Inference or Hypothesis as a Fact.

## 5.6 Evaluator Decision Flow

```mermaid
flowchart TD
    ActionResult[Recovery Action Completed] --> CheckPass{Did the original test now pass?}
    
    CheckPass -->|No| Failed[FAILED_RECOVERY]
    CheckPass -->|Yes| CheckSide{New failures introduced?}
    
    CheckSide -->|Yes| Failed
    CheckSide -->|No| CheckConsistency{Evidence consistent with RCA?}
    
    CheckConsistency -->|No| Uncertain[UNCERTAIN]
    CheckConsistency -->|Yes| CheckConf{Confidence still high?}
    
    CheckConf -->|No| Uncertain
    CheckConf -->|Yes| Success[SUCCESS]
    
    Failed --> Limits{Retry / Investigation limits reached?}
    Uncertain --> Limits
    
    Limits -->|No| Replan[Return to Orchestrator]
    Limits -->|Yes| Escalate[ESCALATE TO HUMAN]
    
    Success --> Report[Final Diagnosis: Resolved]
    Escalate --> Report2[Final Diagnosis: Escalated]
```

## 5.7 Human-in-the-Loop Approval Flow

```mermaid
sequenceDiagram
    participant System
    participant HITL as Approval Gateway
    participant Engineer as Human Engineer
    participant Audit as Audit Log

    System->>HITL: Action Proposal<br/>(RCA + Evidence + Risk + Confidence)
    HITL->>Engineer: Present structured approval card
    Engineer->>HITL: Approve / Reject / Request more evidence
    HITL->>Audit: Record decision + rationale
    alt Approved
        HITL->>System: Proceed with action
    else Rejected
        HITL->>System: Escalate / Abort with diagnosis
    else More Evidence
        HITL->>System: Trigger additional investigation
    end
```
