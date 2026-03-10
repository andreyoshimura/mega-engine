"""
Mega-Engine — Ingest Mega-Sena (API Oficial)

Responsável por:
1. Consultar o último resultado da Mega-Sena na API oficial da Caixa
2. Atualizar data/last_result.json
3. Atualizar o histórico data/results/megasena.csv
4. Evitar duplicação de concursos

Este script é executado pelo GitHub Actions diariamente.

Fluxo:
API Caixa → ingest_megasena.py → last_result.json + megasena.csv
"""

import json
import csv
import requests
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# PATHS DO REPOSITÓRIO
# ============================================================

# Detecta automaticamente a raiz do repositório
REPO_ROOT = Path(__file__).resolve().parents[1]

# Arquivo que guarda apenas o último resultado
LAST_RESULT_PATH = REPO_ROOT / "data" / "last_result.json"

# Arquivo histórico com todos os concursos
CSV_HISTORY_PATH = REPO_ROOT / "data" / "results" / "megasena.csv"


# ============================================================
# API OFICIAL DA CAIXA
# ============================================================

CAIXA_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"

HEADERS = {
    "User-Agent": "mega-engine/1.0",
    "Accept": "application/json",
}


# ============================================================
# FUNÇÃO: CONSULTAR API OFICIAL
# ============================================================

def fetch_caixa():
    """
    Consulta a API oficial da Caixa e retorna
    o último resultado disponível.
    """

    response = requests.get(
        CAIXA_API,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return {
        "concurso": int(data["numero"]),
        "data": data["dataApuracao"],
        "dezenas": sorted(int(d) for d in data["listaDezenas"]),
    }


# ============================================================
# FUNÇÃO: LER ÚLTIMO CONCURSO REGISTRADO
# ============================================================

def load_last_concurso():
    """
    Lê o arquivo last_result.json
    para descobrir qual foi o último concurso salvo.
    """

    if not LAST_RESULT_PATH.exists():
        return 0

    with LAST_RESULT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
        return int(data.get("concurso", 0))


# ============================================================
# FUNÇÃO: SALVAR RESULTADO MAIS RECENTE
# ============================================================

def save_last_result(result):
    """
    Salva o último resultado em last_result.json.
    Esse arquivo é usado por outros módulos do sistema.
    """

    result["fetched_at_utc"] = datetime.now(timezone.utc).isoformat()

    LAST_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with LAST_RESULT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# FUNÇÃO: LER ÚLTIMO CONCURSO DO CSV
# ============================================================

def load_last_csv_concurso():
    """
    Verifica qual o último concurso registrado
    no arquivo histórico CSV.
    """

    if not CSV_HISTORY_PATH.exists():
        return 0

    with CSV_HISTORY_PATH.open("r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if len(rows) == 0:
        return 0

    last_row = rows[-1]

    try:
        return int(last_row[0])
    except Exception:
        return 0


# ============================================================
# FUNÇÃO: ADICIONAR RESULTADO AO CSV
# ============================================================

def append_csv(result):
    """
    Adiciona um novo concurso ao histórico CSV.
    """

    CSV_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

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

    with CSV_HISTORY_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # Último concurso salvo no JSON
    last_concurso_json = load_last_concurso()

    # Último concurso salvo no CSV
    last_concurso_csv = load_last_csv_concurso()

    # Usa o maior para evitar inconsistência
    last_concurso = max(last_concurso_json, last_concurso_csv)

    try:
        latest = fetch_caixa()
    except Exception as e:
        print(f"❌ Falha ao consultar API oficial da Caixa: {e}")
        raise SystemExit(1)

    # ========================================================
    # SE EXISTIR CONCURSO NOVO
    # ========================================================

    if latest["concurso"] > last_concurso:

        print(f"✅ Novo concurso encontrado: {latest['concurso']}")

        # Atualiza JSON com último resultado
        save_last_result(latest)

        # Atualiza histórico CSV
        append_csv(latest)

        print("📄 last_result.json atualizado")
        print("📊 megasena.csv atualizado")

    else:

        print("ℹ️ Nenhum concurso novo encontrado.")
