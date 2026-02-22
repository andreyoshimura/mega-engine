"""
Mega Engine — Strategy Versioning Module

Responsável por:

✔ Registrar versões de estratégia
✔ Evitar duplicação de registro
✔ Manter histórico append-only
✔ Ser resiliente a arquivos corrompidos
✔ Preparar base para rollback futuro
✔ Integrar com GitHub Actions (commit SHA)

Arquivo de saída:
data/model_history.jsonl
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Histórico append-only
MODEL_HISTORY_PATH = Path("data/model_history.jsonl")


# ============================================================
# HASH DA CONFIGURAÇÃO
# ============================================================

def _config_hash(config: dict) -> str:
    """
    Gera hash determinístico da configuração.
    Ordena chaves para garantir consistência.
    """
    serialized = json.dumps(config, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


# ============================================================
# ÚLTIMO HASH REGISTRADO (RESILIENTE)
# ============================================================

def _last_hash() -> str | None:
    """
    Retorna o último config_hash válido do histórico.
    Ignora:
    - linhas vazias
    - JSON inválido
    - linhas parcialmente escritas
    """

    if not MODEL_HISTORY_PATH.exists():
        return None

    try:
        with MODEL_HISTORY_PATH.open("r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        # Se falhar leitura, não bloqueia execução
        return None

    # Percorre de trás para frente
    for line in reversed(lines):
        line = line.strip()

        if not line:
            continue

        try:
            entry = json.loads(line)
            return entry.get("config_hash")
        except json.JSONDecodeError:
            # Ignora linha corrompida
            continue

    return None


# ============================================================
# REGISTRO DE ESTRATÉGIA
# ============================================================

def register_strategy(config: dict, execution_type: str = "production"):
    """
    Registra estratégia no histórico.

    execution_type:
        - production
        - backtest
        - manual
        - experiment
    """

    MODEL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    config_hash = _config_hash(config)

    # Evita registrar duplicado
    last_hash = _last_hash()
    if config_hash == last_hash:
        print("ℹ Estratégia já registrada. Nenhuma alteração detectada.")
        return

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "execution_type": execution_type,
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "parameters": config.get("parameters", {}),
        "notes": config.get("notes", ""),
        "config_hash": config_hash,
        "commit_sha": os.environ.get("GITHUB_SHA", "local")
    }

    try:
        with MODEL_HISTORY_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print("✅ Nova estratégia registrada.")

    except Exception as e:
        # Nunca derruba pipeline por falha de log
        print(f"⚠ Falha ao registrar estratégia: {e}")
