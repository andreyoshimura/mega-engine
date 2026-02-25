import json
import requests
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parents[1]
LAST_RESULT_PATH = REPO_ROOT / "data" / "last_result.json"

HEROKU_API = "https://loteriascaixa-api.herokuapp.com/api/megasena/latest"
CAIXA_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"


def fetch_heroku():
    try:
        r = requests.get(HEROKU_API, timeout=10)
        r.raise_for_status()
        data = r.json()

        return {
            "concurso": int(data["concurso"]),
            "data": data["data"],
            "dezenas": [int(d) for d in data["dezenas"]],
        }

    except Exception:
        return None


def fetch_caixa():
    try:
        r = requests.get(CAIXA_API, timeout=10)
        r.raise_for_status()
        data = r.json()

        return {
            "concurso": int(data["numero"]),
            "data": data["dataApuracao"],
            "dezenas": [int(d) for d in data["listaDezenas"]],
        }

    except Exception:
        return None


def load_last_concurso():
    if not LAST_RESULT_PATH.exists():
        return 0

    with LAST_RESULT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
        return int(data.get("concurso", 0))


def save_result(result):
    result["fetched_at_utc"] = datetime.utcnow().isoformat()

    LAST_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LAST_RESULT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    last_concurso = load_last_concurso()

    heroku_data = fetch_heroku()
    caixa_data = fetch_caixa()

    candidates = [d for d in [heroku_data, caixa_data] if d]

    if not candidates:
        print("❌ Nenhuma API respondeu.")
        exit(1)

    # escolhe maior concurso disponível
    latest = max(candidates, key=lambda x: x["concurso"])

    if latest["concurso"] > last_concurso:
        save_result(latest)
        print(f"✅ Novo concurso registrado: {latest['concurso']}")
    else:
        print("ℹ️ Nenhum concurso novo encontrado.")
