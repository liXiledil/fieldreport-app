"""Model providers. Pipeline code depends only on the ModelProvider protocol,
so a company can swap in its approved endpoint without touching the pipeline."""
from __future__ import annotations

import os
from typing import Any, Protocol


class ModelProvider(Protocol):
    def complete_json(self, system: str, content: list[dict[str, Any]], schema: dict) -> dict:
        """Return a JSON object that validates against `schema`."""
        ...


def default_provider() -> ModelProvider:
    name = os.environ.get("FIELDREPORT_PROVIDER", "claude")
    if name == "claude":
        from .claude import ClaudeProvider
        return ClaudeProvider()
    raise ValueError(f"Unknown provider: {name}")
