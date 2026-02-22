import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

MODEL_HISTORY_PATH = Path("data/model_history.jsonl")


def _config_hash(config: dict) -> str:
    serialized = json.dumps(config, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def register_strategy(config: dict, execution_type: str = "production"):
    MODEL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "execution_type": execution_type,
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "parameters": config.get("parameters", {}),
        "config_hash": _config_hash(config),
        "commit_sha": os.environ.get("GITHUB_SHA", "local")
    }

    with open(MODEL_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
