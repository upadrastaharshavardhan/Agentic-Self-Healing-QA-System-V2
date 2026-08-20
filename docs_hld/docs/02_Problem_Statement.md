# 2. Problem Statement & Motivation

## 2.1 The Fundamental QA Problem

Traditional automated QA systems follow a linear, passive model:

```
Test Execution → Pass / Fail → Report
```

When a test fails, the system stops. A human engineer is then forced to perform a multi-step forensic investigation that typically includes:

- Inspecting test logs and stack traces
- Examining screenshots and browser traces (Playwright / Selenium)
- Analyzing DOM structure and locators
- Checking API request/response payloads and status codes
- Validating test data integrity
- Reviewing application and infrastructure logs
- Comparing recent deployments and configuration changes
- Checking environment health and service status
- Determining whether the failure is real, transient (flaky), or environmental
- Identifying whether the root cause lies in the test, application, data, or infrastructure
- Deciding on a remediation action
- Retrying the test
- Documenting the findings

This process is **manual, repetitive, time-consuming, and poorly reusable**.

## 2.2 Why the Problem Matters

| Impact Area                    | Consequence                                              |
|--------------------------------|----------------------------------------------------------|
| Engineering Productivity       | High percentage of QA/SDET time spent on triage          |
| Feedback Latency               | Developers wait hours/days for actionable failure insight|
| Trust in Automation            | Flaky tests erode confidence in the suite                |
| Knowledge Loss                 | Same failures are re-investigated repeatedly             |
| Release Velocity               | Investigation bottlenecks delay releases                 |
| Cost                           | Manual effort scales poorly with test volume             |
| Observability                  | Root causes remain opaque and undocumented               |

## 2.3 Who Experiences the Pain

- **Senior QA Automation Engineers / SDETs** (Primary) — spend significant daily time on failure triage
- Automation Engineers
- Developers receiving late or incomplete failure information
- DevOps / Platform Engineers dealing with environment-related noise
- QA Leads and Engineering Managers tracking investigation cost and flaky rates
- Release Managers facing delayed go/no-go decisions

## 2.4 Why Existing Approaches Are Insufficient

| Approach                          | Limitation                                              |
|-----------------------------------|---------------------------------------------------------|
| Basic test reports                | Only show symptoms, not root cause                      |
| Screenshot + video capture        | Still requires human interpretation                     |
| Simple retry mechanisms           | Do not distinguish transient from real failures         |
| Static failure classification     | Cannot handle novel or multi-cause failures             |
| Traditional monitoring dashboards | Lack test-context awareness and RCA reasoning           |
| Generic LLM chatbots              | No structured evidence collection, no safety bounds, no audit trail |

## 2.5 What This System Automates

1. Failure detection and structured classification
2. Parallel multi-source evidence collection
3. Evidence-grounded root-cause reasoning
4. Bounded, safe recovery actions
5. Outcome validation
6. Transparent diagnosis generation
7. Historical pattern recognition and knowledge reuse

## 2.6 What Remains Under Human Control

- Approval of any Level 3+ actions (test modification, production data changes, infrastructure changes)
- Final acceptance of RCA when confidence is medium/low
- Policy decisions on risk levels and recovery permissions
- Review of novel or conflicting evidence cases
- Continuous improvement of the knowledge base and evaluation datasets
