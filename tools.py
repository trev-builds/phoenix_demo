"""Two tool designs over the same data.
Design A ("raw"):      one tool returns raw rows; the LLM must do date logic + math itself.
Design B ("computed"): tools do date resolution and math in code; the LLM picks tools and phrases results."""
import json
from datetime import date, timedelta
import pandas as pd
from config import TODAY
from data import load_runs

_df = None
def runs() -> pd.DataFrame:
    """Load the cleaned runs once and cache them.
    Input: none. Output: DataFrame with date, distance_mi, duration_s, avg_hr, ascent_ft, pace_min_per_mi."""
    global _df
    if _df is None:
        _df = load_runs()
    return _df

def _slice(start: str, end: str) -> pd.DataFrame:
    """Filter runs to a date range.
    Input: start, end as 'YYYY-MM-DD' strings (both inclusive). Output: DataFrame of runs on those dates."""
    df = runs()
    d = df.date.dt.date
    return df[(d >= date.fromisoformat(start)) & (d <= date.fromisoformat(end))]

def _fmt_pace(p):
    """Format a pace for display.
    Input: pace in decimal minutes per mile (e.g. 8.5). Output: 'm:ss' string (e.g. '8:30')."""
    m, s = divmod(round(p * 60), 60)
    return f"{m}:{s:02d}"

# -------------------- DESIGN A --------------------
def get_runs(start_date: str, end_date: str) -> str:
    """Design A's only tool: return raw run rows so the LLM does all the math itself.
    Input: start_date, end_date as 'YYYY-MM-DD' (inclusive).
    Output: text, one line per run (date | miles | time | avg pace | avg HR | ascent), or 'No runs in this date range.'"""
    sub = _slice(start_date, end_date)
    if sub.empty:
        return "No runs in this date range."
    h = lambda s: f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d}"
    lines = [f"{r.date.date()} | {r.distance_mi:.2f} mi | time {h(r.duration_s)} | avg pace {_fmt_pace(r.pace_min_per_mi)} /mi | "
             f"avg HR {'' if pd.isna(r.avg_hr) else int(r.avg_hr)} | ascent {'' if pd.isna(r.ascent_ft) else int(r.ascent_ft)} ft"
             for r in sub.itertuples()]
    return "\n".join(lines)

# -------------------- DESIGN B --------------------
def resolve_date_range(phrase: str) -> str:
    """Turn a relative date phrase into exact dates, relative to TODAY. Weeks run Monday-Sunday.
    Input: phrase, one of 'this week', 'last week', 'this month', 'last month', 'this year', 'last N days'.
    Output: JSON {"start_date", "end_date"}, or {"error": ...} for any other phrase."""
    p = phrase.lower().strip()
    mon = TODAY - timedelta(days=TODAY.weekday())
    if p == "this week":   s, e = mon, mon + timedelta(days=6)
    elif p == "last week": s, e = mon - timedelta(days=7), mon - timedelta(days=1)
    elif p == "this month": s, e = TODAY.replace(day=1), TODAY
    elif p == "last month":
        e = TODAY.replace(day=1) - timedelta(days=1); s = e.replace(day=1)
    elif p == "this year": s, e = date(TODAY.year, 1, 1), TODAY
    elif p.startswith("last ") and p.endswith(" days"):
        n = int(p.split()[1]); s, e = TODAY - timedelta(days=n - 1), TODAY
    else:
        return json.dumps({"error": "unsupported phrase; use 'this week','last week','this month','last month','this year','last N days' or explicit dates"})
    return json.dumps({"start_date": str(s), "end_date": str(e)})



# -------------------- START OF TOOL FUNCTIONS --------------------
def _summ(sub: pd.DataFrame) -> dict:
    """Compute summary stats for a set of runs (shared by the Design B tools).
    Input: DataFrame of runs. Output: dict with num_runs, total_miles, avg_run_miles, longest_run_miles,
    avg_pace_min_per_mi (total time / total distance), fastest_run_pace_min_per_mi, avg_hr (mean of per-run HR),
    total_ascent_ft. Only num_runs and total_miles when there are no runs."""
    if sub.empty:
        return {"num_runs": 0, "total_miles": 0.0}
    return {
        "num_runs": int(len(sub)),
        "total_miles": round(sub.distance_mi.sum(), 2),
        "avg_run_miles": round(sub.distance_mi.mean(), 2),
        "longest_run_miles": round(sub.distance_mi.max(), 2),
        "avg_pace_min_per_mi": round(sub.duration_s.sum() / 60 / sub.distance_mi.sum(), 3),
        "fastest_run_pace_min_per_mi": round(sub.pace_min_per_mi.min(), 3),
        "avg_hr": None if sub.avg_hr.isna().all() else round(sub.avg_hr.mean(), 1),
        "total_ascent_ft": round(sub.ascent_ft.sum(), 0),
    }

def summarize_period(start_date: str, end_date: str) -> str:
    """Design B tool: pre-computed stats for one date range.
    Input: start_date, end_date as 'YYYY-MM-DD' (inclusive). Output: JSON of the _summ stats."""
    return json.dumps(_summ(_slice(start_date, end_date)))

def compare_periods(a_start: str, a_end: str, b_start: str, b_end: str) -> str:
    """Design B tool: stats for two date ranges and their difference.
    Input: start/end dates ('YYYY-MM-DD') for period A and period B.
    Output: JSON {"period_a": stats, "period_b": stats, "b_minus_a": numeric differences}."""
    a, b = _summ(_slice(a_start, a_end)), _summ(_slice(b_start, b_end))
    diff = {k: round(b[k] - a[k], 3) for k in a if isinstance(a[k], (int, float)) and isinstance(b.get(k), (int, float))}
    return json.dumps({"period_a": a, "period_b": b, "b_minus_a": diff})

def count_runs_over(min_miles: float, start_date: str, end_date: str) -> str:
    """Design B tool: count runs longer than a distance.
    Input: min_miles (strictly greater than), start_date, end_date as 'YYYY-MM-DD' (inclusive).
    Output: JSON {"count": n}."""
    sub = _slice(start_date, end_date)
    return json.dumps({"count": int((sub.distance_mi > min_miles).sum())})

_D = {"type": "string", "description": "YYYY-MM-DD"}
DESIGN_A = {
    "tools": [{"name": "get_runs", "description": "Get the user's individual running activities between two dates (inclusive).",
               "input_schema": {"type": "object", "properties": {"start_date": _D, "end_date": _D}, "required": ["start_date", "end_date"]}}],
    "impl": {"get_runs": get_runs},
}
DESIGN_B = {
    "tools": [
        {"name": "resolve_date_range", "description": "Convert a phrase like 'last week', 'this month', 'last 30 days' into exact start/end dates. Weeks run Monday-Sunday.",
         "input_schema": {"type": "object", "properties": {"phrase": {"type": "string"}}, "required": ["phrase"]}},
        {"name": "summarize_period", "description": "Pre-computed running stats (run count, total miles, avg/longest run, distance-weighted avg pace in decimal min/mi, avg HR, ascent) for a date range.",
         "input_schema": {"type": "object", "properties": {"start_date": _D, "end_date": _D}, "required": ["start_date", "end_date"]}},
        {"name": "compare_periods", "description": "Summaries of two date ranges plus their differences (B minus A).",
         "input_schema": {"type": "object", "properties": {"a_start": _D, "a_end": _D, "b_start": _D, "b_end": _D}, "required": ["a_start", "a_end", "b_start", "b_end"]}},
        {"name": "count_runs_over", "description": "Count runs longer than a distance in miles within a date range.",
         "input_schema": {"type": "object", "properties": {"min_miles": {"type": "number"}, "start_date": _D, "end_date": _D}, "required": ["min_miles", "start_date", "end_date"]}},
    ],
    "impl": {"resolve_date_range": resolve_date_range, "summarize_period": summarize_period,
             "compare_periods": compare_periods, "count_runs_over": count_runs_over},
}
DESIGNS = {"A_raw": DESIGN_A, "B_computed": DESIGN_B}
