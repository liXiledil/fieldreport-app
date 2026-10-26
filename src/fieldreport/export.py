"""Write drafted sections in a format the Word import macro can read without a JSON parser."""
from __future__ import annotations

from pathlib import Path

MARK = "===FIELD:{}==="


def write_fields_txt(result: dict, out: Path) -> None:
    parts = [f"{MARK.format(name)}\n{text.strip()}" for name, text in result["sections"].items()]
    if result.get("open_items"):
        parts.append(MARK.format("open_items") + "\n" + "\n".join(f"- {i}" for i in result["open_items"]))
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")
