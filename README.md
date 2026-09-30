# Garmin running agent

**Question:** Does moving computation (date logic + arithmetic) into tools improve numeric accuracy for an agent answering questions about personal running data?

**Model:** Claude Haiku 4.5 for both designs, set in `config.py`. Override with `AGENT_MODEL` in `.env`.

Same model, system prompt, 22 questions, and underlying data. Both designs start with only the question plus a system prompt giving today's date, the Monday–Sunday week rule, and the "average pace = total time / total distance" definition. The only difference is the tools (defined in `tools.py`)

### Design A (`A_raw`): 1 tool, the LLM does the math
| Tool | Input | Returns |
|---|---|---|
| `get_runs` | `start_date`, `end_date` (YYYY-MM-DD, inclusive) | One text line per run: date, miles, time (hh:mm:ss), avg pace (m:ss /mi), avg HR, ascent (ft) |

The model must do all counting, summing, averaging, filtering and comparing from the raw rows.

### Design B (`B_computed`): 4 tools, code does the math
| Tool | Input | Returns |
|---|---|---|
| `resolve_date_range` | a phrase: `this week`, `last week`, `this month`, `last month`, `this year`, `last N days` | `start_date` / `end_date` |
| `summarize_period` | `start_date`, `end_date` | `num_runs`, `total_miles`, `avg_run_miles`, `longest_run_miles`, `avg_pace_min_per_mi`, `fastest_run_pace_min_per_mi`, `avg_hr`, `total_ascent_ft` |
| `compare_periods` | start/end for period A and period B | both periods summaries plus `b_minus_a` differences |
| `count_runs_over` | `min_miles` (strictly greater), `start_date`, `end_date` |  `count` |

Ground truth is computed independently in pandas (`ground_truth.py`).

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # fill in ANTHROPIC_API_KEY, PHOENIX_API_KEY, PHOENIX_COLLECTOR_ENDPOINT
```

## Data
- My own Garmin Connect CSV at `data/activities.csv`.
- Synthetic fallback `python make_synthetic_data.py` *(not used)

## Run
```bash
python ground_truth.py          # sanity-check the expected answers against the CSV
python agent.py B_computed      # one question, one traced run: look at it in Phoenix
python run_experiments.py       # uploads dataset + runs both designs as Phoenix experiments
```
Then open Phoenix, compare the `A_raw` and `B_computed` experiments, and read the traces of every wrong answer.

## Files
config.py, data.py, tools.py, ground_truth.py, agent.py, evals.py, run_experiments.py, notebook.ipynb

## Phoenix
I used Arize Phoenix to trace every Claude call and tool call, uploaded the 22 questions as a dataset, ran each design as its own experiment scored by code evaluators (`answer_correct`, `tool_calls_used`), compared the two side by side.
