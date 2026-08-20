"""Base tool interface with permission, risk and failure-mode metadata."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolResult(BaseModel):
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    summary: str
    error: str | None = None
    duration_ms: int | None = None


class BaseTool(ABC):
    name: str
    description: str
    risk: ToolRisk = ToolRisk.LOW
    required_permission: str = "read"

    @abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult:
        ...
