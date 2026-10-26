---
name: fieldreport
description: Build a field service report package (report sections per template, expense entry sheet, TurboCell run summary) from a job folder. Use when asked to build, draft, or close out a job report, process receipts, or summarize TurboCell data.
---

# Build a field report package

Runs the FieldReport pipeline interactively, with you (Claude) doing the reading and drafting instead of the API. Exact numbers always come from code.

## Inputs

- A job folder shaped like `sample-data/JOB-0001_*`: `job.json` (work order, site, unit, scope, dates), `notes/*.txt`, `turbocell/*.csv`, `receipts/*.jpg|png`, and optionally `photos/`.
- A section map JSON (default `sample-data/template_section_map.json`). It lists each report template's fields, headings, and guidance, plus style rules.

If the user doesn't name a job folder, ask which one.

## Steps

1. **Run data (code, not judgment).** For each CSV in `turbocell/`, run
   `python -m fieldreport.turbocell <csv>`
   and save the combined output to `<job>/output/run_analysis.json`. Quote values from it exactly; never re-read numbers off the CSV yourself. If `column_map.unmapped` is non-empty, list those columns as open items.

2. **Draft each template.** Read `job.json`, every note in `notes/`, the run analysis, and the section map. For each template, write a JSON draft `{"sections": {field: text, ...}, "open_items": [...]}` with every field in that template filled in. Then save it with
   `python -m fieldreport.save report <job> "<Template Name>" <draft.json>`
   Rules:
   - Use the engineer's technical wording. Keep it factual, with no filler.
   - Put units on every value, and readings in simple tables (pipe-separated lines are fine).
   - Never invent readings, part numbers, serial numbers, or findings. If something is missing or uncertain, write `[CONFIRM: what is needed]` and add it to `open_items`.
   - Follow the section map's style rules.

3. **Receipts.** Look at each image in `receipts/`, skipping files that start with `_`. For each, record:
   - date (YYYY-MM-DD)
   - vendor
   - category, from the user's expense categories (default: Lodging, Meals, Fuel, Car Rental, Parking, Airfare, Tools/Supplies, Other)
   - amount and currency
   - short notes
   - flags: alcohol, unreadable fields, missing itemization, likely out of policy

   If a field is unreadable, use null plus a flag; never guess. Save with
   `python -m fieldreport.save receipts <job> <receipts.json>`
   If `receipts/_ground_truth.json` exists (sample data), compare your rows to it and report any mismatches.

4. **Verify before reporting back.** Re-read each draft against the notes and the run analysis. Every number must trace back to one of them, every `[CONFIRM]` must appear in the open items, and no section may be empty.

5. **Report back briefly:** the files written to `<job>/output/`, the open items, receipt totals by category, and anything flagged.

## Never

- Upload or send job data anywhere outside this machine.
- Use real customer or company data unless the user confirms their employer allows it.
- Edit macro-enabled Word templates directly. Output goes into `.fields.txt` for `vba/ImportFields.bas`.
