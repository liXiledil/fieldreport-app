from pathlib import Path

from fieldreport import turbocell

CSV = next(Path(__file__).parents[1].glob("sample-data/JOB-*/turbocell/*.csv"))


def test_column_classification():
    cols = turbocell.classify(turbocell.load(CSV).columns)
    assert cols["exhaust_spread"] == ["Exh_Spread_F"]
    assert cols["exhaust_avg"] == ["Exh_Temp_Avg_F"]
    assert cols["vibration"] == ["Brg1_Vib_ips", "Brg2_Vib_ips"]
    assert cols["unmapped"] == []


def test_events_match_field_notes():
    times = {e["event"].split(" (")[0]: e["time"] for e in turbocell.analyze(CSV)["events"]}
    assert times["Full speed no load"].startswith("10:3")
    assert times["Breaker closed / load pickup"].startswith("10:4")


def test_limit_exceedance():
    exc = turbocell.analyze(CSV, {"Exh_Spread_F": 40})["exceedances"]
    assert exc and exc[0]["parameter"] == "Exh_Spread_F"
