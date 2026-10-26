"""Run the whole pipeline on one job folder: python -m fieldreport.cli <job_dir> <section_map.json>"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import receipts, report, turbocell
from .providers import default_provider

DEFAULT_CATEGORIES = ["Lodging", "Meals", "Fuel", "Car Rental", "Parking", "Airfare", "Tools/Supplies", "Other"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("job_dir", type=Path)
    ap.add_argument("section_map", type=Path)
    ap.add_argument("--categories", nargs="*", default=DEFAULT_CATEGORIES)
    args = ap.parse_args()

    out = args.job_dir / "output"
    out.mkdir(exist_ok=True)
    provider = default_provider()
    smap = json.loads(args.section_map.read_text())
    meta = json.loads((args.job_dir / "job.json").read_text())

    runs = [turbocell.analyze(str(p)) for p in sorted((args.job_dir / "turbocell").glob("*.csv"))]
    (out / "run_analysis.json").write_text(json.dumps(runs, indent=2, default=str))

    for tpl in smap["templates"]:
        result = report.draft(args.job_dir, tpl, provider, runs, smap.get("style_rules"))
        name = tpl["name"].lower().replace(" ", "_")
        (out / f"{name}.fields.json").write_text(json.dumps(result, indent=2))

    rows = receipts.extract(args.job_dir / "receipts", provider, args.categories, meta["work_order"])
    receipts.write_entry_sheet(rows, out / "expense_entry_sheet.csv")
    print(f"Wrote outputs to {out}")


if __name__ == "__main__":
    main()
