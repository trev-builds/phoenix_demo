import os
from datetime import date
from dotenv import load_dotenv
load_dotenv()

TODAY = date.fromisoformat(os.getenv("AGENT_TODAY", date.today().isoformat()))
MODEL = os.getenv("AGENT_MODEL", "claude-haiku-4-5-20251001")
DISTANCE_UNIT = os.getenv("DISTANCE_UNIT", "mi")  # "mi" or "km"
CSV_PATH = os.getenv("CSV_PATH", "data/activities.csv")
