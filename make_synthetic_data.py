"""Generates a Garmin-Connect-style activities.csv so you are never blocked on the export."""
import numpy as np, pandas as pd
from datetime import date, timedelta
rng = np.random.default_rng(7)
rows = []
d = date(2026, 1, 1)
end = date(2026, 9, 27)
while d <= end:
    p = 0.55 if d.weekday() not in (2, 6) else 0.25
    if d.weekday() == 5: p = 0.8
    if rng.random() < p:
        dist = float(np.clip(rng.gamma(6, 0.9), 2, 14)) if d.weekday() == 5 else float(np.clip(rng.gamma(5, 0.9), 2, 9))
        pace = rng.normal(8.6, 0.5) - (0.3 if d.month >= 8 else 0)   # min/mile, faster later in year
        secs = dist * pace * 60
        h, r = divmod(int(secs), 3600); m, s = divmod(r, 60)
        pm, ps = divmod(int(pace * 60), 60)
        typ = rng.choice(["Running", "Running", "Running", "Treadmill Running", "Trail Running"])
        rows.append({"Activity Type": typ, "Date": f"{d} 0{rng.integers(6,9)}:{rng.integers(10,59)}:00",
            "Title": "Morning Run", "Distance": round(dist, 2), "Calories": int(dist*105),
            "Time": f"{h:02d}:{m:02d}:{s:02d}", "Avg HR": int(rng.normal(152, 6)),
            "Max HR": int(rng.normal(172, 5)), "Avg Pace": f"{pm}:{ps:02d}",
            "Total Ascent": int(rng.gamma(3, 60)) if typ != "Treadmill Running" else "--"})
    elif rng.random() < 0.08:   # a few non-running activities that must be filtered out
        rows.append({"Activity Type": rng.choice(["Cycling", "Walking", "Strength Training"]),
            "Date": f"{d} 17:30:00", "Title": "Other", "Distance": round(float(rng.uniform(3, 15)), 2),
            "Calories": 300, "Time": "00:45:00", "Avg HR": 120, "Max HR": 150, "Avg Pace": "--", "Total Ascent": "--"})
    d += timedelta(days=1)
pd.DataFrame(rows).iloc[::-1].to_csv("data/activities.csv", index=False)  # Garmin lists newest first
print(f"wrote {len(rows)} rows to data/activities.csv")
