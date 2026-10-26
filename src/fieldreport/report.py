"""Job notes + run-data summary -> section content for a report template."""
from __future__ import annotations

import json
from pathlib import Path

from .content import text_block
from .providers import ModelProvider

SYSTEM = (
    "You draft field service report content for a gas turbine field engineer. "
    "Use the engineer's technical wording and keep it factual. Put units on every value. "
    "Never invent readings, part numbers, serial numbers, or findings: where information is "
    "missing or uncertain, write [CONFIRM: what is needed]. Run-data values come from the "
    "provided analysis and must be quoted exactly."
)


def schema_for(template: dict) -> dict:
    fields = [s["field"] for s in template["sections"]]
    return {
        "type": "object",
        "properties": {
            "sections": {"type": "object", "properties": {f: {"type": "string"} for f in fields},
                         "required": fields, "additionalProperties": False},
            "open_items": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["sections", "open_items"],
        "additionalProperties": False,
    }


def draft(job_dir: Path, template: dict, provider: ModelProvider, run_analyses: list[dict] | None = None,
          style_rules: list[str] | None = None) -> dict:
    meta = json.loads((job_dir / "job.json").read_text())
    notes = "\n\n".join(f"## {p.stem}\n{p.read_text().strip()}" for p in sorted((job_dir / "notes").glob("*.txt")))
    guide = "\n".join(f"- {s['field']} ({s['heading']}): {s['guide']}" for s in template["sections"])
    parts = [
        f"Template: {template['name']}\nSections:\n{guide}",
        f"Job metadata:\n{json.dumps(meta, indent=1)}",
        f"Daily notes:\n{notes}",
    ]
    if run_analyses:
        parts.append("Run data analysis (exact values):\n" + json.dumps(run_analyses, indent=1, default=str))
    if style_rules:
        parts.append("Style rules:\n" + "\n".join(f"- {r}" for r in style_rules))
    return provider.complete_json(SYSTEM, [text_block("\n\n".join(parts))], schema_for(template))
