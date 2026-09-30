"""Uploads the question set to Phoenix and runs one experiment per tool design.
NOTE: Phoenix's Python client API evolves. If a call below errors, check the current
'Datasets & Experiments' quickstart in the Phoenix docs and adjust the 3 marked lines."""
import os, sys
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from phoenix.otel import register

tracer_provider = register(project_name="garmin-run-agent", auto_instrument=True)   # traces every Claude call

from phoenix.client import Client                        # <-- was px.Client + phoenix.experiments (deprecated)
from agent import run_agent
from evals import answer_correct, tool_calls_used
from ground_truth import build_questions

DATASET_NAME = "garmin-run-questions-v1"

def main(designs=("A_raw", "B_computed")):
    qs = build_questions()
    df = pd.DataFrame(qs)
    client = Client()                                     # <-- reads PHOENIX_API_KEY + PHOENIX_COLLECTOR_ENDPOINT
    try:
        dataset = client.datasets.get_dataset(dataset=DATASET_NAME)   # reuse if already uploaded
    except Exception:
        dataset = client.datasets.create_dataset(name=DATASET_NAME, dataframe=df, input_keys=["question"],
                                                 output_keys=["expected", "tolerance", "kind"])   # <-- flat keys
    for design in designs:
        def task(input, design=design):
            return run_agent(input["question"], design)
        client.experiments.run_experiment(dataset=dataset, task=task, evaluators=[answer_correct, tool_calls_used],
                                          experiment_name=f"{design}", experiment_description=f"Tool design {design}")

if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or ("A_raw", "B_computed"))
