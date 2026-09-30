"""Independent pandas ground truth (does NOT use tools.py). Each question states its answer units so the FINAL line is checkable."""
from datetime import date, timedelta
import pandas as pd
from config import TODAY
from data import load_runs

def build_questions() -> list[dict]:
    df = load_runs(); d = df.date.dt.date
    def sl(s, e): return df[(d >= s) & (d <= e)]
    def pace(x): return x.duration_s.sum() / 60 / x.distance_mi.sum()
    mon = TODAY - timedelta(days=TODAY.weekday())
    lw_s, lw_e = mon - timedelta(days=7), mon - timedelta(days=1)
    yr = sl(date(TODAY.year, 1, 1), TODAY)
    aug = sl(date(TODAY.year, 8, 1), date(TODAY.year, 8, 31))
    sep = sl(date(TODAY.year, 9, 1), date(TODAY.year, 9, 30))
    jul = sl(date(TODAY.year, 7, 1), date(TODAY.year, 7, 31))
    l30 = sl(TODAY - timedelta(days=29), TODAY)
    l8w = sl(mon - timedelta(days=56), mon - timedelta(days=1))
    wk = sl(date(TODAY.year, 9, 14), date(TODAY.year, 9, 20))
    lw = sl(lw_s, lw_e)
    Y = TODAY.year
    q = [
     ("How many miles did I run last week? (answer in miles)", round(lw.distance_mi.sum(), 2), "num"),
     ("How many runs did I do last week? (answer as a count)", len(lw), "num"),
     ("What was my longest run this year? (answer in miles)", round(yr.distance_mi.max(), 2), "num"),
     ("How many total miles did I run in August? (answer in miles)", round(aug.distance_mi.sum(), 2), "num"),
     ("What was my average pace in August? Use total time divided by total distance. (answer in decimal minutes per mile)", round(pace(aug), 2), "num"),
     ("What was my average pace in September so far? Use total time divided by total distance. (answer in decimal minutes per mile)", round(pace(sep), 2), "num"),
     ("Was my average pace faster in September than in August? Use total time divided by total distance. (answer yes or no)", "yes" if pace(sep) < pace(aug) else "no", "yesno"),
     ("How many runs longer than 8 miles did I do this year? (answer as a count)", int((yr.distance_mi > 8).sum()), "num"),
     ("How many miles did I run in the last 30 days, counting today as day 1? (answer in miles)", round(l30.distance_mi.sum(), 2), "num"),
     (f"How many miles did I run in the week of Monday {Y}-09-14 through Sunday {Y}-09-20? (answer in miles)", round(wk.distance_mi.sum(), 2), "num"),
     ("What was my fastest single-run average pace this year? (answer in decimal minutes per mile)", round(yr.pace_min_per_mi.min(), 2), "num"),
     ("How many feet of elevation did I climb on runs in August? Ignore runs with no ascent data. (answer in feet)", round(aug.ascent_ft.sum(), 0), "num"),
     ("What was my average run distance in September? (answer in miles)", round(sep.distance_mi.mean(), 2), "num"),
     ("How many runs did I do in July? (answer as a count)", len(jul), "num"),
     ("How many more or fewer miles did I run in September than August? Give September minus August. (answer in miles)", round(sep.distance_mi.sum() - aug.distance_mi.sum(), 2), "num"),
     ("What was my longest run in August? (answer in miles)", round(aug.distance_mi.max(), 2), "num"),
     ("What was my average heart rate across my September runs? Average the per-run averages. (answer in bpm)", round(sep.avg_hr.mean(), 1), "num"),
     ("On average, how many runs per week did I do over the last 8 full weeks (Mon-Sun, not counting this week)? (answer as a decimal)", round(len(l8w) / 8, 2), "num"),
     ("How many total miles have I run this year so far? (answer in miles)", round(yr.distance_mi.sum(), 2), "num"),
     ("How many miles did I run in January 2020? (answer in miles)", 0.0, "num"),   # no data: tests hallucination
     ("How many runs did I do in the first week of February this year, Feb 1 through Feb 7? (answer as a count)", len(sl(date(Y, 2, 1), date(Y, 2, 7))), "num"),
     ("Did I run more total miles in June or in July? (answer june or july)", "june" if sl(date(Y,6,1),date(Y,6,30)).distance_mi.sum() > jul.distance_mi.sum() else "july", "yesno"),
    ]
    return [{"question": t, "expected": e, "kind": k, "tolerance": 0.06 if k == "num" else 0} for t, e, k in q]

EFF_DEF = ("Aerobic efficiency definition: per-run efficiency = (average speed in mph) / (average HR in bpm) x 100, "
           "where average speed in mph = distance in miles / (duration in hours). Only include runs of at least 1.0 mile "
           "that have heart-rate data. Period efficiency = the mean of per-run efficiency across those runs. "
           "Higher efficiency means improvement.")

def build_efficiency_questions() -> list[dict]:
    """v2 additions. Plain pandas, independent of tools.py."""
    df = load_runs(); df = df[(df.distance_mi >= 1.0) & df.avg_hr.notna()]; d = df.date.dt.date
    def eff(s, e):
        x = df[(d >= s) & (d <= e)]
        return (x.distance_mi / (x.duration_s / 3600) / x.avg_hr * 100).mean()
    Y = TODAY.year
    mon = TODAY - timedelta(days=TODAY.weekday())
    apr, may = eff(date(Y, 4, 1), date(Y, 4, 30)), eff(date(Y, 5, 1), date(Y, 5, 31))
    aug = eff(date(Y, 8, 1), date(Y, 8, 31))
    sep = eff(date(Y, 9, 1), TODAY)
    recent = eff(mon - timedelta(days=56), mon - timedelta(days=1))
    earlier = eff(mon - timedelta(days=112), mon - timedelta(days=57))
    num = "(answer as a decimal rounded to 2 places)"
    q = [
     (f"What was my aerobic efficiency in August? {EFF_DEF} {num}", round(aug, 2), "num"),
     (f"What was my aerobic efficiency in September so far? {EFF_DEF} {num}", round(sep, 2), "num"),
     (f"How much did my aerobic efficiency change from April to August? Give August minus April. {EFF_DEF} {num}", round(aug - apr, 2), "num"),
     (f"Did my aerobic efficiency improve from April to August? {EFF_DEF} (answer yes or no)", "yes" if aug > apr else "no", "yesno"),
     (f"Did my aerobic efficiency improve from May to September? {EFF_DEF} (answer yes or no)", "yes" if sep > may else "no", "yesno"),
     (f"How much did my aerobic efficiency change between the last 8 full weeks (Mon-Sun, not counting this week) and the 8 full weeks "
      f"before that? Give the recent 8 weeks minus the earlier 8 weeks. {EFF_DEF} {num}", round(recent - earlier, 2), "num"),
    ]
    return [{"question": t, "expected": e, "kind": k, "tolerance": 0.02 if k == "num" else 0} for t, e, k in q]

if __name__ == "__main__":
    for x in build_questions() + build_efficiency_questions():
        print(x["expected"], "<-", x["question"][:80])
