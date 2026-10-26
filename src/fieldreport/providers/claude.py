from __future__ import annotations

import json
import os
from typing import Any

import anthropic


class RefusalError(RuntimeError):
    pass


class ClaudeProvider:
    def __init__(self, model: str | None = None, effort: str = "medium"):
        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("FIELDREPORT_MODEL", "claude-opus-5-5")
        self.effort = effort

    def complete_json(self, system: str, content: list[dict[str, Any]], schema: dict) -> dict:
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": content}],
            output_config={"effort": self.effort,
                           "format": {"type": "json_schema", "schema": schema}},
            # Server-side refusal fallback, routed by category.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            raise RefusalError(getattr(response.stop_details, "explanation", None) or "Request declined")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Output truncated at max_tokens")
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)
