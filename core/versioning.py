"""Strategy versioning module."""

from __future__ import annotations

import hashlib
import json
import os

from core.config import MODEL_HISTORY_PATH
from core.time_utils import utc_now_pair


def _config_hash(config: dict) -> str:
    serialized = json.dumps(config, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()



def _last_hash() -> str | None:
    if not MODEL_HISTORY_PATH.exists():
        return None

    try:
        with MODEL_HISTORY_PATH.open("r", encoding="utf-8") as f:
            for line in reversed(f.readlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                return entry.get("config_hash")
    except OSError:
        return None

    return None



def register_strategy(config: dict, execution_type: str = "production") -> None:
    MODEL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    config_hash = _config_hash(config)
    if config_hash == _last_hash():
        print("[VERSIONING] Estrategia ja registrada. Nenhuma alteracao detectada.")
        return

    entry = {
        **utc_now_pair("timestamp"),
        "execution_type": execution_type,
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "parameters": config.get("parameters", {}),
        "notes": config.get("notes", ""),
        "config_hash": config_hash,
        "commit_sha": os.environ.get("GITHUB_SHA", "local"),
    }

    try:
        with MODEL_HISTORY_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print("[VERSIONING] Nova estrategia registrada.")
    except OSError as exc:
        print(f"[VERSIONING] Falha ao registrar estrategia: {exc}")
