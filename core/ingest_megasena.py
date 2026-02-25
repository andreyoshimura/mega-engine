"""
Mega-Engine — Ingest Mega-Sena (API Oficial)

Fonte única da verdade:
API oficial da Caixa.

Remove completamente dependência da API heroku atrasada.
"""

import json
import requests
from pathlib import Path
from datetime import datetime, timezone

# ============================================================
# PATHS
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
LAST_RESULT_PATH = REPO_ROOT / "data" / "last_result.json"

# ============================================================
# API OFICIAL DA CAIXA
# ============================================================

CAIXA_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"

HEADERS = {
    "User-Agent": "mega-engine/1.0",
    "Accept": "application/json",
}

# ============================================================
# FUNÇÕES
# ============================================================

def fetch_caixa():
    """
    Busca o último concurso na API oficial da Caixa.
    """
    r = requests.get(CAIXA_API, headers=HEADERS, timeout=30)
    r.raise_for_status()

    data = r.json()

    return {
        "concurso": int(data["numero"]),
        "data": data["dataApuracao"],
        "dezenas": sorted(int(d) for d in data["listaDezenas"]),
    }


def load_last_concurso():
    if not LAST_RESULT_PATH.exists():
        return 0

    with LAST_RESULT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
        return int(data.get("concurso", 0))


def save_result(result):
    result["fetched_at_utc"] = datetime.now(timezone.utc).isoformat()

    LAST_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with LAST_RESULT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    last_concurso = load_last_concurso()

    try:
        latest = fetch_caixa()
    except Exception as e:
        print(f"❌ Falha ao consultar API oficial da Caixa: {e}")
        raise SystemExit(1)

    if latest["concurso"] > last_concurso:
        save_result(latest)
        print(f"✅ Novo concurso registrado: {latest['concurso']}")
    else:
        print("ℹ️ Nenhum concurso novo encontrado.")
