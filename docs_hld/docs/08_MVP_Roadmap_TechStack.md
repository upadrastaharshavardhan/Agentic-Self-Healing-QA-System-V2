# 8. MVP Scope, Phased Roadmap & Technology Stack

## 8.1 MVP Definition (Phases 1–6)

**Goal of MVP:** Demonstrate a complete, safe, explainable investigation + bounded recovery loop for the three most common UI-related failure classes.

**Supported Failure Types in MVP:**
- UI_FAILURE
- LOCATOR_FAILURE
- TIMEOUT_FAILURE

**MVP Capabilities:**
1. Ingest pytest / Playwright failure events
2. Structured failure classification with confidence
3. Parallel collection of: screenshot, DOM snapshot, application logs, test logs
4. Historical similarity lookup (basic)
5. Evidence-grounded RCA with Fact/Observation/Inference separation
6. Safe recovery actions: retry, wait-and-retry, session refresh
7. Evaluator that confirms whether the original failure disappeared
8. Hard bounds on investigation depth and retries
9. Complete audit trail and final diagnosis report
10. Human escalation path

**Explicitly Out of Scope for MVP:**
- Autonomous test code modification
- API / Data / Environment advanced recovery
- Multi-framework support beyond Playwright + pytest
- Level 3+ actions

## 8.2 Phased Roadmap

| Phase | Name                          | Key Deliverables                                      | Success Criteria                              |
|-------|-------------------------------|-------------------------------------------------------|-----------------------------------------------|
| 1     | Failure Ingestion             | Event schema, ingestion API, basic state              | Reliable event capture                        |
| 2     | Failure Classification        | Structured router with confidence                     | ≥90% accuracy on supported types              |
| 3     | Evidence Collection           | Screenshot, DOM, Logs agents working in parallel      | Evidence available for RCA                    |
| 4     | RCA Engine                    | Full Fact/Obs/Inf/Hyp/Rec structure                   | Every RCA has supporting evidence             |
| 5     | Safe Recovery                 | Retry + session refresh with bounds                   | No unbounded loops                            |
| 6     | Evaluator + HITL              | Success/Failed/Uncertain/Escalate + approval UI       | Clean escalation works                        |
| 7     | Historical Memory             | Vector + relational store, similarity search          | Relevant past cases retrieved                 |
| 8     | Advanced Agentic Recovery     | Locator proposal, Level 2–3 actions                   | Controlled increase in autonomy               |
| 9     | Production Observability      | Full OTel, cost tracking, dashboards                  | Complete auditability                         |
| 10    | Enterprise Scale              | Multi-tenant, multi-framework, advanced policies      | Production readiness at scale                 |

## 8.3 Recommended Technology Stack

| Concern                    | Choice                          | Why                                      | Alternative                  | When to Replace                  |
|---------------------------|---------------------------------|------------------------------------------|------------------------------|----------------------------------|
| Language                  | Python 3.11+                    | Rich testing + AI ecosystem              | Go / TypeScript              | Extreme performance needs        |
| Orchestration             | LangGraph                       | Explicit graphs, persistence, HITL       | Custom state machine         | If LangGraph limitations appear  |
| LLM Abstraction           | Provider-agnostic interface     | Model portability                        | Direct OpenAI/Anthropic      | Never (keep abstraction)         |
| Test Framework Integration| Playwright + pytest             | Industry standard for modern UI          | Selenium, Cypress            | Customer requirement             |
| API Layer                 | FastAPI                         | Fast, typed, async                       | Flask / Django               | Heavier enterprise needs         |
| Primary Database          | PostgreSQL                      | Reliability + JSON + pgvector             | CockroachDB                  | Global distribution              |
| Vector Memory             | pgvector                        | Simplicity, single store                 | Pinecone / Weaviate          | Very large scale                 |
| Observability             | OpenTelemetry                   | Vendor-neutral standard                  | Proprietary APM              | Never preferred                  |
| Frontend Dashboard        | Next.js + React                 | Modern, fast developer experience        | Vue / Svelte                 | Team preference                  |
| Containerization          | Docker + Docker Compose         | Reproducibility                          | Podman                       | Security policy                  |
| CI/CD                     | GitHub Actions                  | Native for most repos                    | Jenkins / GitLab CI          | Enterprise standard              |

## 8.4 Key Architectural Patterns Used

| Pattern                  | Where Used                              | Why Needed                                      | Risk if Not Used                          |
|--------------------------|-----------------------------------------|-------------------------------------------------|-------------------------------------------|
| Prompt Chaining          | Classification → RCA → Action           | Controlled information flow                     | Context pollution, hallucination          |
| Parallelization          | Evidence collection agents              | Reduce investigation latency                    | Sequential bottlenecks                    |
| Routing                  | Failure Router                          | Different investigation strategies per type     | One-size-fits-all investigation           |
| Orchestrator-Worker      | Orchestrator + specialized agents       | Clear separation of planning vs execution       | Monolithic agent                          |
| Evaluator-Optimizer      | Evaluator after recovery                | Validate that recovery actually worked          | False sense of success                    |
| Agent (limited)          | RCA and complex investigation steps     | Dynamic reasoning when path is unknown          | Over-rigid system that cannot handle novelty |
| Tool Calling             | All external interactions               | Controlled, auditable side effects              | Uncontrolled LLM actions                  |
