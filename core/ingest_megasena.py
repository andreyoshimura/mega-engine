"""
Mega-Engine
Ingest Mega-Sena com fallback inteligente

Fluxo:

1) consulta API oficial da Caixa
2) verifica último concurso salvo no CSV
3) se houver concursos faltando:
      usa API histórica alternativa
4) atualiza:
      data/results/megasena.csv
      data/last_result.json

Isso evita:
- pular concursos
- depender de API instável
"""

import requests
import csv
import json
from pathlib import Path
from datetime import datetime, timezone


# --------------------------------------------------
# PATHS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = ROOT / "data" / "results" / "megasena.csv"
LAST_JSON = ROOT / "data" / "last_result.json"


# --------------------------------------------------
# APIS
# --------------------------------------------------

API_CAIXA = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"

API_HISTORICO = "https://loteriascaixa-api.herokuapp.com/api/megasena"


# --------------------------------------------------
# LER CSV
# --------------------------------------------------

def read_existing():

    concursos = []

    if not CSV_PATH.exists():
        return concursos

    with open(CSV_PATH) as f:

        reader = csv.reader(f)

        for row in reader:

            try:
                concursos.append(int(row[0]))
            except:
                pass

    return concursos


# --------------------------------------------------
# CONSULTAR API CAIXA
# --------------------------------------------------

def fetch_latest_caixa():

    print("Consultando API oficial da Caixa...")

    r = requests.get(API_CAIXA)

    r.raise_for_status()

    data = r.json()

    dezenas = sorted(int(d) for d in data["listaDezenas"])

    return {
        "concurso": int(data["numero"]),
        "data": data["dataApuracao"],
        "dezenas": dezenas
    }


# --------------------------------------------------
# CONSULTAR HISTÓRICO COMPLETO
# --------------------------------------------------

def fetch_history():

    print("Consultando API histórica (fallback)...")

    r = requests.get(API_HISTORICO)

    r.raise_for_status()

    data = r.json()

    history = []

    for item in data:

        dezenas = sorted(int(d) for d in item["dezenas"])

        history.append({
            "concurso": int(item["concurso"]),
            "data": item["data"],
            "dezenas": dezenas
        })

    return history


# --------------------------------------------------
# SALVAR CSV
# --------------------------------------------------

def append_csv(result):

    row = [
        result["concurso"],
        result["data"],
        result["dezenas"][0],
        result["dezenas"][1],
        result["dezenas"][2],
        result["dezenas"][3],
        result["dezenas"][4],
        result["dezenas"][5],
    ]

    with open(CSV_PATH, "a", newline="") as f:

        writer = csv.writer(f)

        writer.writerow(row)


# --------------------------------------------------
# SALVAR LAST_RESULT
# --------------------------------------------------

def save_last(result):

    result["fetched_at_utc"] = datetime.now(timezone.utc).isoformat()

    with open(LAST_JSON, "w") as f:

        json.dump(result, f, indent=2)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    existing = read_existing()

    if existing:
        last_saved = max(existing)
    else:
        last_saved = 0

    print("Último concurso salvo:", last_saved)

    latest = fetch_latest_caixa()

    latest_concurso = latest["concurso"]

    print("Último concurso na Caixa:", latest_concurso)

    # --------------------------------------------------
    # CASO NORMAL
    # --------------------------------------------------

    if latest_concurso == last_saved:

        print("Nenhum concurso novo.")
        return

    # --------------------------------------------------
    # SE FOR APENAS UM CONCURSO NOVO
    # --------------------------------------------------

    if latest_concurso == last_saved + 1:

        print("Novo concurso encontrado:", latest_concurso)

        append_csv(latest)

        save_last(latest)

        return

    # --------------------------------------------------
    # SE HOUVER CONCURSOS FALTANDO
    # --------------------------------------------------

    print("Detectado gap de concursos — buscando histórico")

    history = fetch_history()

    inserted = 0

    for r in history:

        if r["concurso"] > last_saved:

            append_csv(r)

            save_last(r)

            inserted += 1

            print("Adicionado concurso:", r["concurso"])

    print("Total inserido:", inserted)


# --------------------------------------------------

if __name__ == "__main__":

    main()
