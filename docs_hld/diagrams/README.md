# Advanced Flow Diagrams – Agentic Self-Healing QA System

All diagrams are written in **Mermaid** (`.mmd` files) for maximum clarity, version control, and high-quality rendering.

## Diagram Index

| #  | File                              | Description                                                                 |
|----|-----------------------------------|-----------------------------------------------------------------------------|
| 01 | `01_Overall_Architecture.mmd`     | Complete system architecture (all components + data flow)                   |
| 02 | `02_Self_Healing_Levels.mmd`      | Safety state machine – 6 explicit levels of autonomy                        |
| 03 | `03_RCA_Reasoning_Structure.mmd`  | Mandatory separation: Fact → Observation → Inference → Hypothesis → Recommendation |
| 04 | `04_End_to_End_Sequence.mmd`      | Full sequence diagram of an investigation lifecycle                         |
| 05 | `05_Failure_Router.mmd`           | Structured failure classification decision tree                             |
| 06 | `06_Evaluator_Decision.mmd`       | Post-recovery evaluation logic (Success / Failed / Uncertain / Escalate)    |

## Additional Embedded Diagrams

Many more diagrams (Orchestrator parallelization, Human-in-the-Loop, etc.) are embedded inside:

`docs/05_Core_Workflows_and_Diagrams.md`

## How to Render These Diagrams

| Method                    | How                                                                 |
|---------------------------|---------------------------------------------------------------------|
| **Mermaid Live Editor**   | https://mermaid.live → paste the content of any `.mmd` file         |
| **VS Code**               | Install extension: “Markdown Preview Mermaid Support”               |
| **GitHub / GitLab**       | Automatic rendering when viewing Markdown                           |
| **CLI (mermaid-cli)**     | `mmdc -i diagram.mmd -o diagram.svg` or `.png`                      |
| **Obsidian / Notion**     | Native or community plugin support                                  |

These diagrams are designed to be **presentation-ready** and suitable for both technical reviews and stakeholder discussions.
