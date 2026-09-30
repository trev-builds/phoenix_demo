# Garmin running agent: do computed tools beat LLM math?

**Question:** Does moving computation (date logic + arithmetic) into tools improve numeric accuracy for an agent answering questions about personal running data?

**Model:** Claude Haiku 4.5 for both designs, set in `config.py`. Override with `AGENT_MODEL` in `.env`.

Same model, same system prompt, same 22 questions, same underlying data. Both designs start with only the question plus a system prompt giving today's date, the Monday–Sunday week rule, and the "average pace = total time / total distance" definition. The only difference is the tools (defined in `tools.py`):

### Design A (`A_raw`): 1 tool, the LLM does the math
| Tool | Input | Returns |
|---|---|---|
| `get_runs` | `start_date`, `end_date` (YYYY-MM-DD, inclusive) | One text line per run: date, miles, time (hh:mm:ss), avg pace (m:ss /mi), avg HR, ascent (ft) |

The model must turn phrases like "last week" into dates itself, and do all counting, summing, averaging, filtering and comparing from the raw rows.

### Design B (`B_computed`): 4 tools, code does the math
| Tool | Input | Returns |
|---|---|---|
| `resolve_date_range` | a phrase: `this week`, `last week`, `this month`, `last month`, `this year`, `last N days` | JSON `start_date` / `end_date` (anything else returns an error) |
| `summarize_period` | `start_date`, `end_date` | JSON: `num_runs`, `total_miles`, `avg_run_miles`, `longest_run_miles`, `avg_pace_min_per_mi` (distance-weighted, decimal), `fastest_run_pace_min_per_mi`, `avg_hr`, `total_ascent_ft` |
| `compare_periods` | start/end for period A and period B | JSON with both periods' summaries plus `b_minus_a` differences |
| `count_runs_over` | `min_miles` (strictly greater), `start_date`, `end_date` | JSON `count` |

Design B never sees individual runs; the model only picks tools, passes dates, and reads off (or converts) the computed numbers.

Ground truth is computed independently in pandas (`ground_truth.py`).

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # fill in ANTHROPIC_API_KEY, PHOENIX_API_KEY, PHOENIX_COLLECTOR_ENDPOINT
```

## Data
- Real: put your Garmin Connect CSV at `data/activities.csv`. Delete `AGENT_TODAY` from `.env` so "today" is real.
- Synthetic fallback: `python make_synthetic_data.py` (keep `AGENT_TODAY=2026-09-28` in `.env`).

## Run
```bash
python ground_truth.py          # sanity-check the expected answers against the CSV
python agent.py B_computed      # one question, one traced run: look at it in Phoenix
python run_experiments.py       # uploads dataset + runs both designs as Phoenix experiments
```
Then open Phoenix, compare the `A_raw` and `B_computed` experiments, and read the traces of every wrong answer.

## Files
config.py, data.py (cleaning), tools.py (both designs), ground_truth.py, agent.py, evals.py, run_experiments.py, notebook.ipynb
