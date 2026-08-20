# 4. High-Level Architecture

## 4.1 Conceptual Architecture

```mermaid
flowchart TB
    subgraph External["External Systems"]
        TR[Test Runner<br/>Playwright / pytest / Selenium]
        APP[Application Under Test]
        LOGS[Log Aggregators<br/>ELK / CloudWatch / Loki]
        DEP[Deployment Systems<br/>CI/CD / Argo / K8s]
        ENV[Environment Health<br/>Prometheus / Health APIs]
    end

    subgraph Core["Agentic Self-Healing QA Core"]
        FI[Failure Ingestion Service]
        FR[Failure Router<br/>Structured Classification]
        ORCH[Orchestrator<br/>Task Planner]
        
        subgraph Parallel["Parallel Evidence Collection"]
            LA[Log Analysis Agent]
            UA[UI / Browser Agent]
            AA[API Investigation Agent]
            DA[Test Data Agent]
            EA[Environment Agent]
            DepA[Deployment Agent]
            LocA[Locator Analysis Agent]
            HA[Historical Failure Agent]
        end

        AGG[Evidence Aggregator]
        RCA[RCA Agent<br/>Root Cause Reasoner]
        ACT[Action Selector]
        REC[Safe Recovery Executor]
        EVAL[Evaluator]
        MEM[Historical Memory<br/>Vector + Relational]
        STATE[Persistent State Store]
        OBS[Observability Layer<br/>OpenTelemetry]
        HITL[Human Approval Gateway]
    end

    subgraph Output["Outputs"]
        DIAG[Final Diagnosis Report]
        AUDIT[Full Audit Trail]
        DASH[Investigation Dashboard]
    end

    TR -->|Failure Event| FI
    FI --> FR
    FR --> ORCH
    ORCH --> Parallel
    Parallel --> AGG
    AGG --> RCA
    RCA --> ACT
    ACT -->|Low Risk| REC
    ACT -->|High Risk / Low Conf| HITL
    HITL -->|Approved| REC
    HITL -->|Rejected| DIAG
    REC --> EVAL
    EVAL -->|Success| DIAG
    EVAL -->|Failure / Uncertain| ORCH
    EVAL -->|Max Retries| HITL
    RCA --> MEM
    EVAL --> MEM
    STATE -.->|Read/Write| Core
    OBS -.->|Trace Everything| Core
    DIAG --> DASH
    AUDIT --> DASH
```

## 4.2 Layered View

| Layer                  | Responsibility                                                                 | Key Technologies                  |
|------------------------|--------------------------------------------------------------------------------|-----------------------------------|
| Ingestion              | Receive and normalize test failure events                                      | FastAPI, Event schemas            |
| Classification         | Structured failure typing with confidence                                      | LLM + Structured Output           |
| Orchestration          | Decide which investigation tasks are needed                                    | LangGraph Orchestrator            |
| Investigation          | Parallel specialized evidence collection                                       | Specialized Agents + Tools        |
| Reasoning              | Multi-evidence RCA with Fact/Observation/Inference separation                  | RCA Agent                         |
| Decision               | Select recovery action based on risk, confidence, and policy                   | Action Selector                   |
| Execution              | Perform only permitted recovery actions                                        | Safe Recovery Executor            |
| Validation             | Determine if recovery succeeded and original failure is resolved               | Evaluator                         |
| Knowledge              | Store and retrieve historical failures & resolutions                           | PostgreSQL + pgvector             |
| Control                | Human approval, bounds enforcement, escalation                                 | HITL Gateway + Policy Engine      |
| Observability          | Full tracing, metrics, cost, confidence tracking                               | OpenTelemetry                     |

## 4.3 Key Architectural Decisions

1. **LangGraph as the orchestration backbone** — provides explicit graph structure, persistent state, checkpointing, and human-in-the-loop interrupts.
2. **Specialized agents with least-privilege tools** — no single agent has access to all tools.
3. **Structured outputs everywhere critical** — routing, RCA, action proposals never rely on free-form text alone.
4. **Evidence-first design** — RCA is forbidden from making unsupported claims.
5. **Bounded loops by construction** — investigation depth, retries, and recovery attempts are hard limits in state.
6. **Separation of Diagnosis and Action** — the system can always stop at diagnosis if recovery risk is unacceptable.
