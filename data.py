import pandas as pd
from config import CSV_PATH, DISTANCE_UNIT

KM_PER_MI, FT_PER_M = 1.609344, 3.28084

def _to_seconds(x):
    try:
        s = 0.0
        for p in str(x).split(":"):
            s = s * 60 + float(p)
        return s
    except ValueError:
        return float("nan")

def load_runs(path: str = CSV_PATH) -> pd.DataFrame:
    """Load a Garmin Connect CSV export and return cleaned RUNNING activities only.
    Columns: date, distance_mi, duration_s, pace_min_per_mi, avg_hr, ascent_ft"""
    raw = pd.read_csv(path)
    raw = raw[raw["Activity Type"].str.contains("Running", case=False, na=False)].copy()
    dist = pd.to_numeric(raw["Distance"].astype(str).str.replace(",", ""), errors="coerce")
    ascent = pd.to_numeric(raw["Total Ascent"].astype(str).str.replace(",", ""), errors="coerce")
    if DISTANCE_UNIT == "km":
        dist = dist / KM_PER_MI
        ascent = ascent * FT_PER_M          # metric accounts report ascent in meters
    out = pd.DataFrame({
        "date": pd.to_datetime(raw["Date"]),
        "distance_mi": dist,
        "duration_s": raw["Time"].map(_to_seconds),
        "avg_hr": pd.to_numeric(raw["Avg HR"], errors="coerce"),
        "ascent_ft": ascent,
    })
    out = out.dropna(subset=["distance_mi", "duration_s"])
    out = out[out.distance_mi > 0].sort_values("date").reset_index(drop=True)
    out["pace_min_per_mi"] = out.duration_s / 60 / out.distance_mi
    return out
