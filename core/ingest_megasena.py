from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
import requests

from core.config import LAST_RESULT_PATH as LAST_JSON, RESULTS_PATH as CSV_PATH

API_CAIXA = "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena"
API_HISTORICO = "https://loteriascaixa-api.herokuapp.com/api/megasena"
REQUEST_TIMEOUT = 20
DRAW_COLUMNS = [f"d{i}" for i in range(1, 7)]
CSV_COLUMNS = ["concurso", "data", *DRAW_COLUMNS]


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "mega-engine/1.1"})
    return session


def _request_json(session: requests.Session, url: str):
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _normalize_result(concurso: int, data: str, dezenas: list[int]) -> dict:
    dezenas_ordenadas = sorted(int(d) for d in dezenas)
    if len(dezenas_ordenadas) != 6 or len(set(dezenas_ordenadas)) != 6:
        raise ValueError(f"Resultado invalido para concurso {concurso}: {dezenas}")
    return {
        "concurso": int(concurso),
        "data": str(data),
        "dezenas": dezenas_ordenadas,
    }


def read_existing() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame(columns=CSV_COLUMNS)

    df = pd.read_csv(CSV_PATH)
    if list(df.columns) != CSV_COLUMNS:
        df = df[CSV_COLUMNS]
    df = df.dropna(subset=["concurso"])
    df["concurso"] = df["concurso"].astype(int)
    for col in DRAW_COLUMNS:
        df[col] = df[col].astype(int)
    return df.sort_values("concurso").drop_duplicates(subset=["concurso"], keep="last")


def fetch_latest_caixa(session: requests.Session) -> dict:
    print("[INGEST] Consultando API oficial da Caixa...")
    data = _request_json(session, API_CAIXA)
    return _normalize_result(
        concurso=int(data["numero"]),
        data=data["dataApuracao"],
        dezenas=[int(d) for d in data["listaDezenas"]],
    )


def fetch_history(session: requests.Session) -> list[dict]:
    print("[INGEST] Consultando API historica (fallback)...")
    data = _request_json(session, API_HISTORICO)
    history = []
    for item in data:
        history.append(
            _normalize_result(
                concurso=int(item["concurso"]),
                data=item["data"],
                dezenas=[int(d) for d in item["dezenas"]],
            )
        )
    history.sort(key=lambda item: item["concurso"])
    return history


def merge_results(existing_df: pd.DataFrame, new_results: list[dict]) -> pd.DataFrame:
    if not new_results:
        return existing_df.copy()

    new_df = pd.DataFrame(
        [
            {
                "concurso": item["concurso"],
                "data": item["data"],
                "d1": item["dezenas"][0],
                "d2": item["dezenas"][1],
                "d3": item["dezenas"][2],
                "d4": item["dezenas"][3],
                "d5": item["dezenas"][4],
                "d6": item["dezenas"][5],
            }
            for item in new_results
        ]
    )
    merged = pd.concat([existing_df, new_df], ignore_index=True)
    merged = merged.sort_values("concurso").drop_duplicates(subset=["concurso"], keep="last")
    return merged[CSV_COLUMNS]


def save_results(df: pd.DataFrame) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)


def save_last(result: dict) -> None:
    payload = dict(result)
    payload["fetched_at_utc"] = datetime.now(timezone.utc).isoformat()
    LAST_JSON.parent.mkdir(parents=True, exist_ok=True)
    with LAST_JSON.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def main() -> None:
    existing_df = read_existing()
    last_saved = int(existing_df["concurso"].max()) if not existing_df.empty else 0
    print(f"[INGEST] Ultimo concurso salvo: {last_saved}")

    session = _session()
    latest = fetch_latest_caixa(session)
    latest_concurso = latest["concurso"]
    print(f"[INGEST] Ultimo concurso na Caixa: {latest_concurso}")

    if latest_concurso <= last_saved:
        print("[INGEST] Nenhum concurso novo.")
        if latest_concurso == last_saved:
            save_last(latest)
        return

    if latest_concurso == last_saved + 1:
        new_results = [latest]
    else:
        history = fetch_history(session)
        new_results = [item for item in history if item["concurso"] > last_saved]

    if not new_results:
        print("[INGEST] Nenhum concurso novo apos conciliacao.")
        return

    merged = merge_results(existing_df, new_results)
    save_results(merged)
    save_last(new_results[-1])
    print(f"[INGEST] Concursos inseridos/atualizados: {len(new_results)}")


if __name__ == "__main__":
    main()
