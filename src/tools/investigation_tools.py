"""
Investigation tools used by specialized agents.
In a real deployment these would call Playwright, log APIs, health endpoints, etc.
Here they return high-fidelity simulated evidence so the full pipeline is demonstrable offline.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta
from typing import Any

from src.tools.base import BaseTool, ToolResult, ToolRisk


class ScreenshotTool(BaseTool):
    name = "take_screenshot"
    description = "Capture the current browser viewport"
    risk = ToolRisk.LOW

    async def run(self, test_id: str = "", **kwargs: Any) -> ToolResult:
        await asyncio.sleep(0.05)
        return ToolResult(
            success=True,
            data={
                "screenshot_path": f"/artifacts/screenshots/{test_id or 'unknown'}.png",
                "viewport": "1280x720",
                "page_title": "Login – Demo App",
                "visible_text_sample": "Welcome back. Please sign in to continue.",
            },
            summary="Screenshot captured. Page appears fully rendered.",
            duration_ms=50,
        )


class DOMInspectionTool(BaseTool):
    name = "inspect_dom"
    description = "Extract relevant DOM structure and candidate locators"
    risk = ToolRisk.LOW

    async def run(self, failure_message: str = "", **kwargs: Any) -> ToolResult:
        await asyncio.sleep(0.08)
        # Simulate locator change when the failure looks like a locator issue
        if any(k in failure_message.lower() for k in ["not found", "locator", "selector", "no such element"]):
            return ToolResult(
                success=True,
                data={
                    "expected_locator": "button[data-testid='login-button']",
                    "found_candidates": [
                        {"selector": "[data-testid='login-btn-v2']", "tag": "button", "text": "Sign In"},
                        {"selector": "button.primary-cta", "tag": "button", "text": "Sign In"},
                        {"selector": "button:has-text('Sign In')", "tag": "button", "text": "Sign In"},
                    ],
                    "missing_expected": True,
                    "dom_hash": "a1b2c3d4",
                },
                summary="Expected locator missing. Three candidate locators found in current DOM.",
                duration_ms=80,
            )
        return ToolResult(
            success=True,
            data={
                "expected_locator": "button[data-testid='login-button']",
                "found_candidates": [],
                "missing_expected": False,
                "dom_hash": "stable123",
            },
            summary="Expected locator present in DOM.",
            duration_ms=60,
        )


class LogAnalysisTool(BaseTool):
    name = "query_logs"
    description = "Search application and test logs around the failure timestamp"
    risk = ToolRisk.LOW

    async def run(self, failure_message: str = "", **kwargs: Any) -> ToolResult:
        await asyncio.sleep(0.1)
        if "503" in failure_message or "service unavailable" in failure_message.lower():
            return ToolResult(
                success=True,
                data={
                    "error_signatures": ["Upstream service returned 503", "circuit_breaker_open"],
                    "last_error_timestamp": (datetime.utcnow() - timedelta(seconds=12)).isoformat(),
                    "severity_ids": ["corr-9f3a"],
                    "log_level_counts": {"ERROR": 3, "WARN": 7, "INFO": 42},
                },
                summary="Multiple 503 / circuit-breaker entries found in application logs.",
                duration_ms=100,
            )
        return ToolResult(
            success=True,
            data={
                "error_signatures": [],
                "last_error_timestamp": None,
                "correlation_ids": [],
                "log_level_counts": {"ERROR": 0, "WARN": 1, "INFO": 28},
            },
            summary="No significant application errors in the relevant time window.",
            duration_ms=90,
        )


class EnvironmentHealthTool(BaseTool):
    name = "check_service_health"
    description = "Probe health endpoints and basic resource metrics"
    risk = ToolRisk.LOW

    async def run(self, **kwargs: Any) -> ToolResult:
        await asyncio.sleep(0.07)
        return ToolResult(
            success=True,
            data={
                "services": {
                    "frontend": "healthy",
                    "auth-service": "healthy",
                    "payment-service": "healthy",
                    "database": "healthy",
                },
                "cpu_percent": 34,
                "memory_percent": 61,
            },
            summary="All critical services report healthy. Resource pressure normal.",
            duration_ms=70,
        )


class DeploymentHistoryTool(BaseTool):
    name = "get_deployment_history"
    description = "Retrieve recent deployments for the application under test"
    risk = ToolRisk.LOW

    async def run(self, **kwargs: Any) -> ToolResult:
        await asyncio.sleep(0.06)
        now = datetime.utcnow()
        return ToolResult(
            success=True,
            data={
                "recent_deployments": [
                    {
                        "version": "2.8.17",
                        "component": "frontend",
                        "deployed_at": (now - timedelta(minutes=22)).isoformat(),
                        "deployed_by": "ci-bot",
                        "changelog_summary": "Updated login button styling and data-testid",
                    },
                    {
                        "version": "2.8.16",
                        "component": "backend",
                        "deployed_at": (now - timedelta(hours=6)).isoformat(),
                        "deployed_by": "ci-bot",
                        "changelog_summary": "Payment timeout tuning",
                    },
                ]
            },
            summary="Frontend v2.8.17 deployed 22 minutes ago (login button changes).",
            duration_ms=60,
        )


class HistoricalFailureTool(BaseTool):
    name = "query_historical_failures"
    description = "Retrieve similar past failures and their resolutions"
    risk = ToolRisk.LOW

    async def run(self, failure_message: str = "", failure_type: str = "", **kwargs: Any) -> ToolResult:
        await asyncio.sleep(0.09)
        if "locator" in failure_message.lower() or failure_type == "LOCATOR_FAILURE":
            return ToolResult(
                success=True,
                data={
                    "similar_cases": [
                        {
                            "failure_id": "hist-441",
                            "root_cause": "Locator changed after frontend deploy",
                            "resolution": "Updated data-testid to login-btn-v2",
                            "resolved_at": "2026-08-12T14:22:00Z",
                            "similarity": 0.89,
                        },
                        {
                            "failure_id": "hist-398",
                            "root_cause": "Locator changed after frontend deploy",
                            "resolution": "Switched to role-based locator",
                            "resolved_at": "2026-07-28T09:11:00Z",
                            "similarity": 0.84,
                        },
                    ]
                },
                summary="Two highly similar historical locator failures found after frontend releases.",
                duration_ms=90,
            )
        return ToolResult(
            success=True,
            data={"similar_cases": []},
            summary="No highly similar historical failures found.",
            duration_ms=70,
        )


class TestRetryTool(BaseTool):
    name = "retry_test"
    description = "Re-execute the failed test (bounded)"
    risk = ToolRisk.LOW

    async def run(self, test_id: str = "", simulate_pass: bool = False, **kwargs: Any) -> ToolResult:
        await asyncio.sleep(0.3)
        # For demo purposes we can force a pass on second attempt for certain scenarios
        passed = simulate_pass or random.random() > 0.35
        return ToolResult(
            success=True,
            data={
                "test_id": test_id,
                "passed": passed,
                "duration_ms": 1240 if passed else 3100,
                "new_failure_message": None if passed else "Still failing (simulated)",
            },
            summary=f"Test re-executed. Result: {'PASSED' if passed else 'FAILED'}",
            duration_ms=300,
        )


# Registry for easy injection
TOOL_REGISTRY: dict[str, BaseTool] = {
    "take_screenshot": ScreenshotTool(),
    "inspect_dom": DOMInspectionTool(),
    "query_logs": LogAnalysisTool(),
    "check_service_health": EnvironmentHealthTool(),
    "get_deployment_history": DeploymentHistoryTool(),
    "query_historical_failures": HistoricalFailureTool(),
    "retry_test": TestRetryTool(),
}
