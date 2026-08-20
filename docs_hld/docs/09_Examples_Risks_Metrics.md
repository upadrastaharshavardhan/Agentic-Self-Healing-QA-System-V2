# 9. End-to-End Examples, Risks, Anti-Patterns & Success Metrics

## 9.1 Example Scenarios (Summary)

### Example 1: UI Locator Changed after Frontend Deployment
- **Failure:** “Login button not found”
- **Classification:** LOCATOR_FAILURE (confidence 0.93)
- **Evidence:** Screenshot shows page loaded, DOM missing expected selector, deployment of frontend 18 min ago, historical similar locator failures after previous deploys
- **RCA:** Frontend locator changed in recent deployment (confidence 0.91)
- **Action:** Level 2 – propose new locator candidate + safe retry after update (requires approval in MVP)
- **Validation:** After locator update and retry → test passes
- **Outcome:** Resolved with full evidence trail

### Example 2: API Service Temporarily Unavailable
- **Failure:** Payment service returned 503
- **Classification:** API_FAILURE / ENVIRONMENT_FAILURE
- **Evidence:** API logs show 503, service health endpoint unhealthy, no recent code deploy, historical transient 503s
- **RCA:** Transient service unavailability
- **Action:** Level 1 – wait + retry
- **Validation:** Second attempt passes
- **Outcome:** Resolved as transient

### Example 3: Invalid / Stale Test Data
- **Failure:** Assertion on user balance failed
- **Classification:** DATA_FAILURE
- **Evidence:** Test data record missing expected field, data last refreshed 3 days ago
- **RCA:** Stale test data
- **Action:** Level 2 – refresh non-production test data + retry
- **Validation:** Passes after refresh
- **Outcome:** Resolved

### Example 4: Environment Instability (Resource Pressure)
- **Failure:** Timeout waiting for element
- **Classification:** TIMEOUT_FAILURE / ENVIRONMENT_FAILURE
- **Evidence:** High CPU on test environment, multiple concurrent tests, no locator change
- **RCA:** Environment resource contention
- **Action:** Escalate (cannot safely fix environment from QA system)
- **Outcome:** Escalated with clear evidence

### Example 5: Classic Flaky Timeout
- **Failure:** Intermittent timeout on the same step
- **Classification:** FLAKY_FAILURE / TIMEOUT_FAILURE
- **Evidence:** Same test passed 4/5 times in last hour, no deployment, stable locators
- **RCA:** Timing / synchronization flake
- **Action:** Level 1 – retry with slightly increased timeout (bounded)
- **Validation:** Passes on retry
- **Outcome:** Marked as flaky with recommendation for long-term hardening

## 9.2 Major Risks & Mitigations

| Risk                              | Impact                  | Mitigation                                      |
|-----------------------------------|-------------------------|-------------------------------------------------|
| Hallucinated RCA                  | Wrong diagnosis         | Mandatory evidence grounding + structured output|
| Unbounded retries                 | Cost / infinite loops   | Hard counters in state                          |
| Tool failure cascade              | Incomplete investigation| Graceful degradation + partial evidence         |
| Secret leakage to LLM             | Security incident       | Strict masking + secret isolation               |
| False recovery (test passes once) | False confidence        | Evaluator checks consistency + side effects     |
| Over-autonomy                     | Production impact       | Strict level system + HITL gates                |
| Stale historical knowledge        | Wrong recommendations   | Confidence decay + recency weighting            |

## 9.3 Anti-Patterns Explicitly Avoided

1. One giant agent that does everything
2. Agent for every trivial task
3. Unlimited retries or investigation depth
4. Unlimited tool access
5. Free-form text for critical routing decisions
6. Autonomous production modifications
7. Ignoring failure and edge-case paths
8. No observability / audit trail
9. Untyped or mutable free-form state
10. No human escalation path
11. Assuming every failure is automatically fixable
12. Treating raw LLM confidence as absolute truth

## 9.4 Success Metrics (Targets)

| Metric                              | MVP Target                  | Measurement Method                     |
|-------------------------------------|-----------------------------|----------------------------------------|
| Classification accuracy             | ≥ 90% on supported types    | Evaluation dataset                     |
| Evidence collection completeness    | ≥ 95% of expected sources   | Automated checks                       |
| RCA has supporting evidence         | 100%                        | Schema validation                      |
| False recovery rate                 | < 5%                        | Evaluator + human review sample        |
| Escalation rate (supported failures)| Tracked (not optimized yet) | System metrics                         |
| Mean investigation latency          | < 3 minutes (MVP)           | OpenTelemetry                          |
| Zero unsafe autonomous actions      | 100%                        | Audit log review                       |
| Full decision traceability          | 100%                        | Trace completeness                     |

## 9.5 Business Case (Illustrative Assumptions)

**Assumptions (clearly labeled):**
- 10,000 test executions / month
- 5% failure rate → 500 failures / month
- Average manual investigation time = 20 minutes
- Total manual effort = 500 × 20 = 10,000 minutes ≈ 167 engineering hours / month

**Potential with system (illustrative):**
- 60–70% of supported failures reach diagnosis automatically
- 20–30% of recoverable failures auto-resolved within bounds
- Remaining cases still benefit from pre-collected evidence and structured RCA

**Even partial automation of evidence collection and first-pass RCA can save substantial engineering time and improve consistency.** Actual savings must be measured after deployment.
