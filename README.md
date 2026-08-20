# Agentic Self-Healing QA System

**Production-oriented AI platform for autonomous test failure investigation, root-cause analysis, and bounded self-healing.**

> Detect → Investigate → Reason → Decide → Safely Act → Validate → Explain → Escalate when necessary

This is **not** a chatbot that explains failures.  
It is a complete investigation engine with:

- Structured failure classification
- Parallel specialized evidence collection
- Evidence-grounded RCA (Fact / Observation / Inference / Hypothesis / Recommendation)
- Risk-aware action selection
- Bounded safe recovery
- Evaluator that validates whether recovery actually worked
- Full audit trail and human-in-the-loop gates

---

## Quick Start (Offline Demo – No API Keys Required)

```bash
# 1. Create virtualenv & install
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .

# 2. Run three realistic scenarios
python -m src.cli demo

# 3. Investigate a custom failure
python -m src.cli investigate -m "locator 'button[data-testid=login-button]' not found"

# 4. Start the API
uvicorn src.api.main:app --reload --port 8000
# Then POST to http://localhost:8000/api/v1/investigate
```

The system ships with a high-quality **deterministic MOCK LLM** so the entire pipeline runs offline and still produces realistic, structured RCA and recovery decisions.

---

## Architecture Highlights

| Component              | Role                                                                 |
|------------------------|----------------------------------------------------------------------|
| Failure Router         | Structured classification with confidence                            |
| Orchestrator + Agents  | Parallel evidence collection (screenshot, DOM, logs, deploy, history)|
| RCA Agent              | Strict Fact → Observation → Inference → Hypothesis separation        |
| Action Selector        | Risk + healing-level gated decisions                                 |
| Safe Recovery          | Only Level 0–2 by default (retry, wait-and-retry, session refresh)   |
| Evaluator              | Confirms original failure disappeared and no new failures introduced |
| Bounds                 | Hard limits on investigation depth, retries, recovery attempts       |
| HITL                   | Automatic escalation when confidence low or risk high                |

See the companion **High-Level Design** document for full architecture, diagrams, and design rationale.

---

## Project Layout

```
src/
├── models/schemas.py      # All Pydantic models (Classification, RCA, Action…)
├── state.py               # LangGraph InvestigationState
├── config.py              # Central settings + safety bounds
├── services/llm.py        # Provider abstraction + high-quality mock
├── tools/                 # Investigation tools (screenshot, DOM, logs…)
├── graph/
│   ├── nodes.py           # All graph nodes
│   └── workflow.py        # LangGraph definition + conditional edges
├── api/main.py            # FastAPI surface
└── cli.py                 # Rich CLI
```

---

## Safety Design

- **6 explicit healing levels** (Diagnosis-only → Restricted autonomous)
- **Hard counters** prevent infinite loops
- **Least-privilege tools** – agents only see what they need
- **No production-modifying tools** exposed by default
- **Structured outputs only** for routing and RCA
- **Human approval required** for Level 3+

---

## Next Steps / Roadmap

1. Real Playwright integration for live DOM & screenshots
2. Persistent checkpointer (Postgres / Redis)
3. Vector historical memory (pgvector)
4. Full OpenTelemetry instrumentation
5. Dashboard (Next.js) for approval & evidence review
6. Evaluation harness with labeled failure datasets

---

## License

MIT – designed as a serious portfolio / enterprise foundation.


---
## ScreenShots
<img width="716" height="634" alt="image" src="https://github.com/user-attachments/assets/d1e311ae-af95-4d96-9957-e664de56fdf0" />

<img width="712" height="635" alt="image" src="https://github.com/user-attachments/assets/22852104-bf54-4dc8-a3e3-7169f300067b" />

<img width="717" height="668" alt="image" src="https://github.com/user-attachments/assets/b4b6487a-7622-468c-a815-7c1407e88ee8" />

<img width="718" height="641" alt="image" src="https://github.com/user-attachments/assets/1b3b8aff-06e0-4087-89ef-a06c0f94242d" />

<img width="721" height="642" alt="image" src="https://github.com/user-attachments/assets/dbdb9181-de37-409a-8f7e-00e038c5b3c5" />
