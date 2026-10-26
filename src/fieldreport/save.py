"""Save outputs drafted interactively (e.g. by Claude Code) in the same formats the API pipeline writes.

  python -m fieldreport.save report   <job_dir> "<Template Name>" <draft.json>
  python -m fieldreport.save receipts <job_dir> <receipts.json>

draft.json: {"sections": {field: text}, "open_items": [...]}
receipts.json: [{"file", "date", "vendor", "category", "amount", "currency", "notes", "flags"}]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import export, receipts


def save_report(job_dir: Path, template_name: str, draft: dict) -> Path:
    out = job_dir / "output"
    out.mkdir(exist_ok=True)
    name = template_name.lower().replace(" ", "_")
    (out / f"{name}.fields.json").write_text(json.dumps(draft, indent=2))
    export.write_fields_txt(draft, out / f"{name}.fields.txt")
    return out / f"{name}.fields.txt"


def save_receipts(job_dir: Path, rows: list[dict]) -> Path:
    out = job_dir / "output"
    out.mkdir(exist_ok=True)
    for r in rows:
        r["suggested_name"] = receipts.suggested_name(r, Path(r["file"]).suffix)
    path = out / "expense_entry_sheet.csv"
    receipts.write_entry_sheet(rows, path)
    return path


def main(argv: list[str]) -> None:
    if len(argv) < 3:
        raise SystemExit(__doc__)
    kind, job = argv[0], Path(argv[1])
    if kind == "report" and len(argv) == 4:
        print(save_report(job, argv[2], json.loads(Path(argv[3]).read_text())))
    elif kind == "receipts":
        print(save_receipts(job, json.loads(Path(argv[2]).read_text())))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
