import json
import os
from datetime import datetime
from pathlib import Path

MODEL_HISTORY_PATH = Path("data/model_history.jsonl")


def register_strategy(strategy_name: str,
                      model_version: str,
                      parameters: dict,
                      notes: str = ""):

    MODEL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "strategy_name": strategy_name,
        "model_version": model_version,
        "parameters": parameters,
        "commit_sha": os.environ.get("GITHUB_SHA", "local"),
        "notes": notes
    }

    with open(MODEL_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
