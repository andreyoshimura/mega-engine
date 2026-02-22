import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

MODEL_HISTORY_PATH = Path("data/model_history.jsonl")


def _config_hash(config: dict) -> str:
    serialized = json.dumps(config, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _last_hash() -> str | None:
    if not MODEL_HISTORY_PATH.exists():
        return None

    with open(MODEL_HISTORY_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return None
        last_entry = json.loads(lines[-1])
        return last_entry.get("config_hash")


def register_strategy(config: dict, execution_type: str = "production"):
    MODEL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    config_hash = _config_hash(config)

    # Evita registrar duplicado
    if config_hash == _last_hash():
        print("ℹ Estratégia já registrada. Nenhuma alteração detectada.")
        return

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "execution_type": execution_type,
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "parameters": config.get("parameters", {}),
        "config_hash": config_hash,
        "commit_sha": os.environ.get("GITHUB_SHA", "local")
    }

    with open(MODEL_HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    print("✅ Nova estratégia registrada.")
