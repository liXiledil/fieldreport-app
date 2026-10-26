import json
from pathlib import Path

from fieldreport import receipts, report

ROOT = Path(__file__).parents[1] / "sample-data"
JOB = next(ROOT.glob("JOB-*"))
SMAP = json.loads((ROOT / "template_section_map.json").read_text())


class FakeProvider:
    """Records calls and returns canned, schema-shaped answers."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []

    def complete_json(self, system, content, schema):
        self.calls.append({"system": system, "content": content, "schema": schema})
        return self.answers.pop(0)


def test_report_schema_and_prompt():
    tpl = SMAP["templates"][0]
    fields = [s["field"] for s in tpl["sections"]]
    fake = FakeProvider([{"sections": {f: "x" for f in fields}, "open_items": []}])
    result = report.draft(JOB, tpl, fake, run_analyses=[{"events": []}], style_rules=SMAP["style_rules"])
    call = fake.calls[0]
    assert call["schema"]["properties"]["sections"]["required"] == fields
    prompt = call["content"][0]["text"]
    assert "liner 4 has thermal barrier coating loss" in prompt
    assert "Run data analysis" in prompt and "[CONFIRM" in call["system"]
    assert set(result["sections"]) == set(fields)


def test_receipts_one_call_per_image_and_sheet(tmp_path):
    truth = json.loads((JOB / "receipts" / "_ground_truth.json").read_text())
    answers = [{"receipt": {"date": t["date"], "vendor": t["vendor"], "category": t["category"],
                            "amount": t["amount"], "currency": "USD", "notes": t["notes"], "flags": []}}
               for t in truth]
    fake = FakeProvider(answers)
    rows = receipts.extract(JOB / "receipts", fake, ["Meals", "Lodging"], "WO-DEMO-0001")
    assert len(rows) == len(truth) == len(fake.calls)
    assert fake.calls[0]["content"][0]["type"] == "image"
    assert rows[1]["suggested_name"] == "2026-11-02_QuickFuel22_48.37.jpg"
    out = tmp_path / "sheet.csv"
    receipts.write_entry_sheet(rows, out)
    assert out.read_text().splitlines()[0].startswith("file,date,vendor")


def test_fields_txt_format(tmp_path):
    from fieldreport import export
    out = tmp_path / "r.fields.txt"
    export.write_fields_txt({"sections": {"summary": "Line 1\nLine 2", "scope": "CI"},
                             "open_items": ["Confirm liner serial"]}, out)
    text = out.read_text()
    assert text.startswith("===FIELD:summary===\nLine 1\nLine 2\n===FIELD:scope===\nCI\n")
    assert "===FIELD:open_items===\n- Confirm liner serial" in text


def test_save_outputs(tmp_path):
    from fieldreport import save
    job = tmp_path / "job"
    job.mkdir()
    txt = save.save_report(job, "Field Service Report", {"sections": {"summary": "ok"}, "open_items": []})
    assert txt.name == "field_service_report.fields.txt" and txt.read_text().startswith("===FIELD:summary===")
    sheet = save.save_receipts(job, [{"file": "r.jpg", "date": "2026-11-02", "vendor": "Main St Diner",
                                      "category": "Meals", "amount": 18.42, "currency": "USD",
                                      "notes": "Dinner", "flags": ["alcohol"]}])
    assert "2026-11-02_MainStDiner_18.42.jpg" in sheet.read_text() and "alcohol" in sheet.read_text()
