# Agentic Self-Healing QA System
## Complete High-Level Design Document

**Version:** 1.0  
**Date:** 20 August 2026  
**Status:** Complete & Ready for Implementation Review  

---

### Quick Start

| Item | Path |
|------|------|
| **Single consolidated document** | `COMPLETE_HLD.md` |
| **Modular documentation** | `docs/` |
| **Advanced Mermaid diagrams** | `diagrams/` |

---

### Document Structure

| #  | Document | Description |
|----|----------|-------------|
| 01 | [Executive Summary](docs/01_Executive_Summary.md) | Vision, value proposition, design principles |
| 02 | [Problem Statement](docs/02_Problem_Statement.md) | Current pain & why existing tools fall short |
| 03 | [Vision and Goals](docs/03_Vision_and_Goals.md) | Project vision and explicit non-goals |
| 04 | [High-Level Architecture](docs/04_High_Level_Architecture.md) | System architecture + layered view |
| 05 | [Core Workflows & Diagrams](docs/05_Core_Workflows_and_Diagrams.md) | **Rich Mermaid flow diagrams** |
| 06 | [Agent & Tool Design](docs/06_Agent_and_Tool_Design.md) | Specialized agents, tools, RCA structure |
| 07 | [State, Data, Security, Observability](docs/07_State_Data_Security_Observability.md) | State model, security, OpenTelemetry |
| 08 | [MVP, Roadmap & Tech Stack](docs/08_MVP_Roadmap_TechStack.md) | Phased delivery and technology decisions |
| 09 | [Examples, Risks & Metrics](docs/09_Examples_Risks_Metrics.md) | End-to-end scenarios, anti-patterns, KPIs |

---

### Advanced Flow Diagrams (Standalone)

Located in `diagrams/`:

1. **Overall Architecture** – Full system view
2. **Self-Healing Levels** – 6-level safety state machine
3. **RCA Reasoning Structure** – Fact → Observation → Inference → Hypothesis → Recommendation
4. **End-to-End Sequence** – Complete investigation lifecycle
5. **Failure Router** – Structured classification decision tree
6. **Evaluator Decision** – Success / Failed / Uncertain / Escalate logic

**How to view diagrams:**  
- https://mermaid.live (paste content)  
- VS Code + “Markdown Preview Mermaid Support”  
- GitHub (automatic rendering)

---

### Design Highlights

- **Bounded Autonomy** with 6 explicit self-healing levels
- **Evidence-first RCA** with strict Fact / Observation / Inference separation
- **Parallel specialized investigation agents** with least-privilege tools
- **Hard limits** on investigation depth, retries, and recovery attempts
- **Full OpenTelemetry observability** – every decision is auditable
- **Human-in-the-loop** for any medium/high risk action
- **Production-safe failure handling** for every edge case

---

### Next Step

This High-Level Design is **complete**.

Upon approval, the next deliverable will be the **Detailed Design + MVP implementation skeleton** (LangGraph graph definition, state model, structured schemas, and first investigation pipeline).

---

*Designed as a serious, portfolio-grade and enterprise-ready Agentic AI QA platform.*
