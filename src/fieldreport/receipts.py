"""Receipt photos -> rows for manual expense-portal entry (e.g. Stars)."""
from __future__ import annotations

import csv
from pathlib import Path

from .content import MEDIA, image_block, text_block
from .providers import ModelProvider

SYSTEM = (
    "You extract expense receipts for a field service engineer. Read only what is printed. "
    "If a field is unreadable or absent, use null and add a flag; never guess amounts or dates."
)

ROW = {
    "type": "object",
    "properties": {
        "date": {"type": ["string", "null"], "description": "YYYY-MM-DD"},
        "vendor": {"type": ["string", "null"]},
        "category": {"type": ["string", "null"]},
        "amount": {"type": ["number", "null"]},
        "currency": {"type": ["string", "null"]},
        "notes": {"type": "string"},
        "flags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["date", "vendor", "category", "amount", "currency", "notes", "flags"],
    "additionalProperties": False,
}
SCHEMA = {"type": "object", "properties": {"receipt": ROW}, "required": ["receipt"], "additionalProperties": False}

FIELDS = ["file", "date", "vendor", "category", "amount", "currency", "notes", "flags", "suggested_name"]


def suggested_name(row: dict, suffix: str) -> str:
    vendor = "".join(c for c in (row.get("vendor") or "unknown") if c.isalnum())[:20]
    amount = f"{row['amount']:.2f}" if row.get("amount") is not None else "unknown"
    return f"{row.get('date') or 'nodate'}_{vendor}_{amount}{suffix}"


def extract(folder: Path, provider: ModelProvider, categories: list[str], work_order: str) -> list[dict]:
    prompt = (f"Work order {work_order}. Allowed categories: {', '.join(categories)}. "
              "Flag alcohol, missing itemization, or anything likely outside a typical per-diem policy.")
    rows = []
    for path in sorted(p for p in folder.iterdir() if p.suffix.lower() in MEDIA):
        result = provider.complete_json(SYSTEM, [image_block(path), text_block(prompt)], SCHEMA)["receipt"]
        rows.append({"file": path.name, **result, "suggested_name": suggested_name(result, path.suffix)})
    return rows


def write_entry_sheet(rows: list[dict], out: Path) -> None:
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({**r, "flags": "; ".join(r["flags"])})
