# Garmin running agent: do computed tools beat LLM math?

**Question:** Does moving computation (date logic + arithmetic) into tools improve numeric accuracy for an agent answering questions about personal running data?

- Design A (`A_raw`): one `get_runs` tool returns raw rows; the LLM does the math.
- Design B (`B_computed`): tools resolve dates and return pre-computed stats.
- Same model, same system prompt, same 22 questions. Ground truth is computed independently in pandas (`ground_truth.py`).

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # fill in ANTHROPIC_API_KEY, PHOENIX_API_KEY, PHOENIX_COLLECTOR_ENDPOINT
```

## Data
- Real: put your Garmin Connect CSV at `data/activities.csv`. Delete `AGENT_TODAY` from `.env` so "today" is real. Set `DISTANCE_UNIT=km` if your account is metric.
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
