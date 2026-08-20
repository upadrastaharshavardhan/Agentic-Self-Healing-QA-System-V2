# 6. Specialized Agents & Tool Ecosystem

## 6.1 Agent Design Principles

- Each agent has a **narrow responsibility**.
- Each agent receives **only the tools it needs** (least privilege).
- All agent outputs are **structured** (Pydantic / JSON Schema).
- Every agent returns a **confidence score**.
- Agents never perform recovery actions themselves — they only investigate and report.
- Agents handle their own tool failures gracefully and report partial evidence.

## 6.2 Specialized Investigation Agents

| Agent                        | Responsibility                                      | Allowed Tools                                      | Output Schema Highlights                  |
|-----------------------------|-----------------------------------------------------|----------------------------------------------------|-------------------------------------------|
| Log Analysis Agent          | Extract relevant errors, timestamps, correlation IDs | Application logs, test logs, infrastructure logs   | error_signatures, timestamps, severity    |
| UI / Browser Agent          | Analyze visual and DOM state                        | Screenshot, DOM snapshot, browser trace, console   | missing_elements, locator_candidates, visual_diff |
| API Investigation Agent     | Inspect request/response and contract violations    | API traffic capture, response validation           | status_codes, payload_diffs, latency      |
| Test Data Agent             | Validate and optionally refresh test data           | Data store queries, data generation helpers        | data_integrity, missing_records           |
| Environment Agent           | Assess infrastructure and service health            | Health endpoints, Prometheus, K8s status           | service_status, resource_pressure         |
| Deployment Agent            | Correlate failures with recent changes              | Deployment history, version diffs, changelogs      | recent_deploys, changed_components        |
| Locator Analysis Agent      | Detect and propose locator updates                  | DOM, locator history, previous successful locators | candidate_locators, stability_score       |
| Historical Failure Agent    | Retrieve similar past failures and resolutions      | Vector search + relational history                 | similar_cases, past_rca, past_resolution  |

## 6.3 RCA Agent (Core Reasoning Engine)

**Input:** Aggregated evidence packets + historical context  
**Output (Structured):**

```json
{
  "facts": [],
  "observations": [],
  "inferences": [],
  "hypotheses": [
    {
      "root_cause": "...",
      "confidence": 0.0-1.0,
      "supporting_evidence_ids": [],
      "contradicting_evidence_ids": []
    }
  ],
  "selected_root_cause": "...",
  "overall_confidence": 0.0-1.0,
  "recommendation": {
    "action": "...",
    "risk_level": "LOW|MEDIUM|HIGH",
    "rationale": "..."
  }
}
```

The RCA Agent is strictly prohibited from inventing evidence.

## 6.4 Tool Catalog (Summary)

| Tool Name                  | Purpose                              | Risk Level | Permission Required      | Failure Mode                     |
|---------------------------|--------------------------------------|------------|--------------------------|----------------------------------|
| take_screenshot           | Capture current UI state             | Low        | Browser context          | Return empty + error flag        |
| get_dom_snapshot          | Full or filtered DOM                 | Low        | Browser context          | Partial DOM or timeout           |
| query_logs                | Search application/test logs         | Low        | Log read access          | Empty result set                 |
| inspect_api_traffic       | Retrieve recent API calls            | Low        | Network capture access   | No traffic found                 |
| check_service_health      | Call health endpoints                | Low        | Network                  | Timeout / unreachable            |
| get_deployment_history    | List recent deployments              | Low        | CI/CD read access        | Empty history                    |
| validate_test_data        | Check data preconditions             | Low        | Data read                | Data missing                     |
| refresh_test_data         | Re-seed non-production data          | Medium     | Data write (scoped)      | Partial refresh                  |
| retry_test                | Re-execute the failed test           | Low        | Test runner              | Same failure or new failure      |
| propose_locator_update    | Generate new locator candidates      | Medium     | DOM + history            | No stable candidate              |
| query_historical_failures | Semantic + structured search         | Low        | Memory read              | No similar cases                 |

**Critical Rule:** No tool that can modify production application code, production data, or infrastructure is exposed to any agent by default.

## 6.5 Tool Calling Pattern

All tools are invoked through a controlled ToolNode / tool-calling interface with:

- Input validation
- Permission checks
- Timeout enforcement
- Output sanitization (PII / secrets masking)
- Full tracing of input → output → latency → cost
