"""Deterministic analysis of TurboCell CSV exports.

Numbers in the report must be exact, so all statistics and event detection
happen here in code. The LLM only writes prose from this module's output.
"""
from __future__ import annotations

import pandas as pd

# Column-name hints -> canonical parameter. Real exports vary, so matching is fuzzy
# and anything unmatched is reported back for the engineer to map.
HINTS = {
    "speed": ["speed", "tnh", "rpm"],
    "load": ["load", "mw", "dwatt"],
    "exhaust_avg": ["exh_temp", "ttxm", "exhaust"],
    "exhaust_spread": ["spread", "ttxsp"],
    "vibration": ["vib", "bb", "ips", "mils"],
    "wheelspace": ["wheel", "ttws"],
}


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    ts = next((c for c in df.columns if "time" in c.lower() or "date" in c.lower()), None)
    if ts is None:
        raise ValueError("No timestamp column found; map it manually.")
    df[ts] = pd.to_datetime(df[ts])
    return df.set_index(ts).sort_index()


def classify(columns) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"unmapped": []}
    for col in columns:
        low = col.lower()
        # Check spread before exhaust so "Exh_Spread" isn't classed as exhaust_avg.
        for key in ["exhaust_spread", *[k for k in HINTS if k != "exhaust_spread"]]:
            if any(h in low for h in HINTS[key]):
                out.setdefault(key, []).append(col)
                break
        else:
            out["unmapped"].append(col)
    return out


def stats(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.select_dtypes("number").columns:
        s = df[col]
        rows.append({"parameter": col, "min": s.min(), "max": s.max(), "mean": round(s.mean(), 3),
                     "time_of_max": s.idxmax().strftime("%H:%M:%S")})
    return pd.DataFrame(rows)


def first_time(mask: pd.Series):
    hits = mask[mask]
    return hits.index[0].strftime("%H:%M:%S") if len(hits) else None


def events(df: pd.DataFrame, cols: dict[str, list[str]]) -> list[dict]:
    ev = []
    if cols.get("speed"):
        sp = df[cols["speed"][0]]
        if (t := first_time(sp > 25)):
            ev.append({"time": t, "event": "Ignition / acceleration (speed > 25%)"})
        if (t := first_time(sp > 99)):
            ev.append({"time": t, "event": "Full speed no load (speed > 99%)"})
    if cols.get("load"):
        ld = df[cols["load"][0]]
        if (t := first_time(ld > 2)):
            ev.append({"time": t, "event": "Breaker closed / load pickup (load > 2 MW)"})
        peak = ld.max()
        if (t := first_time(ld > 0.98 * peak)):
            ev.append({"time": t, "event": f"Reached ~base load ({peak:.1f} MW peak)"})
    return sorted(ev, key=lambda e: e["time"])


def limit_exceedances(df: pd.DataFrame, limits: dict[str, float]) -> list[dict]:
    out = []
    for col, lim in limits.items():
        if col in df:
            over = df[col] > lim
            if over.any():
                out.append({"parameter": col, "limit": lim, "first": first_time(over),
                            "seconds_over": int(over.sum() * df.index.to_series().diff().median().total_seconds())})
    return out


def analyze(path: str, limits: dict[str, float] | None = None) -> dict:
    df = load(path)
    cols = classify(df.columns)
    return {"file": path, "rows": len(df), "start": str(df.index[0]), "end": str(df.index[-1]),
            "column_map": cols, "stats": stats(df).to_dict("records"),
            "events": events(df, cols), "exceedances": limit_exceedances(df, limits or {})}


if __name__ == "__main__":
    import json, sys
    print(json.dumps(analyze(sys.argv[1]), indent=2, default=str))
