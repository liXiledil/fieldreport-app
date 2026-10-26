"""Generate a fully synthetic field-service job for FieldReport development."""
import json, os, sys
import numpy as np, pandas as pd
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
job = os.path.join(OUT, "JOB-0001_DemoSite_Unit2_CombustionInspection")
for d in ["notes", "receipts", "turbocell", "photos", "output"]:
    os.makedirs(os.path.join(job, d), exist_ok=True)
rng = np.random.default_rng(42)

meta = {
    "work_order": "WO-DEMO-0001", "customer": "Demo Power Cooperative (fictional)",
    "site": "Riverbend Station (fictional)", "unit": "Unit 2 - heavy-duty gas turbine",
    "scope": "Combustion inspection and return-to-service testing",
    "start": "2026-11-02", "end": "2026-11-08", "engineer": "Sample Engineer",
    "note": "ALL DATA IN THIS FOLDER IS SYNTHETIC. No real customer, unit, or OEM data.",
}
json.dump(meta, open(os.path.join(job, "job.json"), "w"), indent=2)

notes = {
"2026-11-02.txt": """Arrived site 0700. Safety orientation and permit review with site lead. LOTO walkdown completed 0930, verified zero energy on fuel and starting systems. Customer wants unit back by Saturday for a weekend dispatch. Unpacked tooling, staged combustion hardware in laydown area. Noted a minor oil leak at the number 2 bearing drain flange, customer aware, not in scope but will mention in report.""",
"2026-11-03.txt": """Removed combustion liners and transition pieces cans 1 through 6. As found: liner 4 has thermal barrier coating loss approx 2 inches near the crossfire tube, other liners normal wear. Transition piece 3 aft frame shows light cracking, length about 0.5 inch, photographed. Fuel nozzles removed for flow check offsite. Borescope of first stage nozzle shows typical coating erosion, no burn-through. Need to confirm crack length measurement with the dye pen results tomorrow.""",
"2026-11-04.txt": """Dye penetrant on TP 3 confirmed crack indication 0.6 inch, within limits per customer's repair criteria, customer approved to reinstall and monitor. Liner 4 replaced with customer spare, serial to be recorded from tag (CONFIRM). Fuel nozzles returned, flow within tolerance. Crossfire tubes and seals replaced on all cans.""",
"2026-11-05.txt": """Reassembly of combustion hardware complete. Torque values recorded on the reassembly sheet. Flame detectors cleaned and checked. Spark plugs inspected and replaced on cans 1 and 2.""",
"2026-11-06.txt": """Return to service. Crank and purge good. Ignition 1012, flame established all cans. Full speed no load 1031. Breaker closed 1046. Load steps to base load by 1215. Exhaust spread looked normal after warmup, peaked during load ramp. Vibration on bearing 2 slightly higher than baseline but steady, below alarm. Ran at base load 2 hours for heat soak. Customer witnessed. Export run data from TurboCell for the report.""",
"2026-11-07.txt": """Demob. Cleaned laydown area, returned tooling. Debrief with plant manager: recommend replacing TP 3 at next hot gas path, monitor bearing 2 vibration trend, fix bearing 2 drain flange leak at next outage. Customer asked for report by next Friday.""",
}
for f, t in notes.items():
    open(os.path.join(job, "notes", f), "w").write(t + "\n")

# TurboCell-style return-to-service run export (generic column names, 1 s sampling)
t = pd.date_range("2026-11-06 10:00:00", "2026-11-06 14:30:00", freq="5s")
n = len(t); sec = (t - t[0]).total_seconds().values
def ramp(x, x0, x1, y0, y1):
    return np.clip((x - x0) / (x1 - x0), 0, 1) * (y1 - y0) + y0
ign, fsnl, brk, base = 12*60, 31*60, 46*60, 135*60
speed = np.where(sec < ign, ramp(sec, 0, ign, 0, 20), ramp(sec, ign, fsnl, 20, 100)) + rng.normal(0, .05, n)
load = np.where(sec < brk, 0, ramp(sec, brk, base, 5, 168)) + rng.normal(0, .3, n) * (sec > brk)
exh = np.where(sec < ign, 80, 450 + ramp(sec, brk, base, 0, 120)) + rng.normal(0, 2, n)
spread = np.where(sec < ign, 0, 18 + 22*np.exp(-((sec - 90*60)/(12*60))**2) + rng.normal(0, 1.5, n))
vib1 = np.where(sec < ign, 0.05, 0.18 + 0.12*speed/100) + rng.normal(0, .01, n)
vib2 = np.where(sec < ign, 0.05, 0.22 + 0.20*speed/100 + 0.04*load/168) + rng.normal(0, .012, n)
wheel = np.where(sec < ign, 90, 300 + ramp(sec, ign, base+20*60, 0, 420)) + rng.normal(0, 3, n)
df = pd.DataFrame({"Timestamp": t, "Speed_pct": speed.round(2), "Load_MW": load.clip(0).round(1),
    "Exh_Temp_Avg_F": exh.round(1), "Exh_Spread_F": spread.clip(0).round(1),
    "Brg1_Vib_ips": vib1.round(3), "Brg2_Vib_ips": vib2.round(3), "Wheelspace_1FO_F": wheel.round(1)})
df.to_csv(os.path.join(job, "turbocell", "RTS_run_2026-11-06.csv"), index=False)

# Receipt images
receipts = [
 ("2026-11-02", "Riverbend Inn (fictional)", "Lodging", 6*129.00, "6 nights x $129.00"),
 ("2026-11-02", "QuickFuel #22", "Fuel", 48.37, "Rental car fuel"),
 ("2026-11-02", "Main St Diner", "Meals", 18.42, "Dinner"),
 ("2026-11-03", "Hardware Hut", "Tools/Supplies", 36.99, "Inspection mirror, markers"),
 ("2026-11-03", "Main St Diner", "Meals", 21.10, "Dinner"),
 ("2026-11-04", "Taco Barn", "Meals", 14.85, "Dinner"),
 ("2026-11-05", "Riverbend Grill", "Meals", 64.20, "Dinner incl. 2 beers"),
 ("2026-11-07", "Airport Parking Lot C", "Parking", 72.00, "6 days"),
 ("2026-11-07", "SkyRental Cars", "Car Rental", 412.66, "6 days compact"),
]
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 22)
except OSError:
    font = ImageFont.load_default()
truth = []
for i, (d, v, cat, amt, desc) in enumerate(receipts, 1):
    img = Image.new("RGB", (520, 640), (250, 248, 240)); dr = ImageDraw.Draw(img)
    lines = [v.upper(), "123 Sample Rd, Riverbend", "-"*30, f"Date: {d}", "", desc, "",
             f"Subtotal: ${amt/1.07:,.2f}", f"Tax:      ${amt - amt/1.07:,.2f}", f"TOTAL:    ${amt:,.2f}",
             "", "VISA ****0000", "THANK YOU", "", "SAMPLE - NOT A REAL RECEIPT"]
    y = 30
    for ln in lines:
        dr.text((30, y), ln, fill=(20, 20, 20), font=font); y += 36
    img = img.rotate(rng.uniform(-3, 3), expand=True, fillcolor=(200, 200, 200))
    img.save(os.path.join(job, "receipts", f"receipt_{i:02d}.jpg"), quality=85)
    truth.append({"file": f"receipt_{i:02d}.jpg", "date": d, "vendor": v, "category": cat,
                  "amount": round(amt, 2), "currency": "USD", "notes": desc})
json.dump(truth, open(os.path.join(job, "receipts", "_ground_truth.json"), "w"), indent=2)

# Generic report template section map (not any company's template)
section_map = {"templates": [
 {"name": "Field Service Report", "sections": [
   {"field": "summary", "heading": "Executive Summary", "guide": "3-5 sentences: scope, outcome, key findings, unit status"},
   {"field": "scope", "heading": "Scope of Work", "guide": "What was contracted"},
   {"field": "timeline", "heading": "Daily Log", "guide": "Dated bullets of work performed"},
   {"field": "findings", "heading": "As-Found Condition and Findings", "guide": "Per component; measurements in tables"},
   {"field": "work_performed", "heading": "Work Performed / Parts Replaced", "guide": "Including parts and serials"},
   {"field": "testing", "heading": "Return-to-Service Testing", "guide": "Sequence of events and key values from run data"},
   {"field": "recommendations", "heading": "Recommendations", "guide": "Numbered, actionable"},
   {"field": "as_left", "heading": "As-Left Condition", "guide": "Unit status at demob"}]},
 {"name": "Inspection Data Sheet", "sections": [
   {"field": "component_table", "heading": "Component Inspection Table", "guide": "Component | Location | Finding | Measurement | Disposition"}]}],
 "style_rules": ["Use the engineer's technical wording", "Units on every value", "Never invent readings, serials, or part numbers; use [CONFIRM: ...]", "No customer personal names"],
}
json.dump(section_map, open(os.path.join(OUT, "template_section_map.json"), "w"), indent=2)
open(os.path.join(OUT, "README.md"), "w").write(
"# FieldReport sample data\n\nEverything here is synthetic, generated by `make_sample.py` (fixed seed). "
"It mimics a combustion inspection job: daily voice-note transcripts, a TurboCell-style CSV export of the "
"return-to-service run, 9 receipt images with `_ground_truth.json` for accuracy testing, and a generic "
"report template section map. Deliberate test cases: a [CONFIRM] serial number, a policy flag (alcohol on "
"receipt 7), and a vibration and exhaust-spread peak during the load ramp.\n")
print("done", len(df), "rows")
