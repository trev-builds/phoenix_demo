"""Re-score experiments that already ran, without calling Claude again.
Phoenix stores task outputs separately from evaluations, so an improved eval can be applied to old runs.
Usage: python reevaluate.py <experiment_id> [<experiment_id> ...]"""
import sys
from dotenv import load_dotenv
load_dotenv()
from phoenix.client import Client
from evals import answer_correct

def answer_correct_explained(output, expected) -> dict:
    """Same check as answer_correct, under a new name so it shows as its own column next to the original score-only eval."""
    return answer_correct(output, expected)

if __name__ == "__main__":
    client = Client()
    for experiment_id in sys.argv[1:]:
        experiment = client.experiments.get_experiment(experiment_id=experiment_id)
        client.experiments.evaluate_experiment(experiment=experiment, evaluators=[answer_correct_explained])
