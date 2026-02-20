
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

# ===== Config =====
REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_JOGOS = REPO_ROOT / "out" / "jogos_gerados.json"

DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PERF_LOG = DATA_DIR / "performance_log.jsonl"  # append-only
LAST_RESULT = DATA_DIR / "last_result.json"    # último resultado oficial cacheado

API_LATEST = "https://loteriascaixa-api.herokuapp.com/api/megasena/latest"

MIN_N = 1
MAX_N = 60
DRAW_SIZE = 6
TICKET_SIZE = 9
N_GAMES = 5


@dataclass(frozen=True)
class LatestDraw:
    concurso: int
    data: str  # string vinda da API
    dezenas: Tuple[int, ...]


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _parse_int_list(x: Any) -> List[int]:
    if isinstance(x, list):
        out = []
        for v in x:
            try:
                out.append(int(v))
            except Exception:
                pass
        return out
    return []


def _validate_numbers(nums: List[int], *, expected_len: int, min_n: int, max_n: int) -> List[int]:
    nums2 = [int(n) for n in nums if isinstance(n, (int, float, str))]
    nums3 = []
    for n in nums2:
        if min_n <= n <= max_n:
            nums3.append(n)
    nums_unique = sorted(set(nums3))
    if len(nums_unique) != expected_len:
        raise ValueError(f"Números inválidos: esperado {expected_len} distintos em [{min_n}..{max_n}]. Obtido={nums_unique}")
    return nums_unique


def fetch_latest_draw() -> LatestDraw:
    r = requests.get(API_LATEST, timeout=30)
    r.raise_for_status()
    data = r.json()

    concurso = int(data.get("concurso"))
    data_sorteio = str(data.get("data", "")).strip()

    dezenas_raw = data.get("dezenas") or data.get("listaDezenas") or data.get("numeros") or []
    dezenas = _validate_numbers(_parse_int_list(dezenas_raw), expected_len=DRAW_SIZE, min_n=MIN_N, max_n=MAX_N)

    return LatestDraw(concurso=concurso, data=data_sorteio, dezenas=tuple(dezenas))


def load_generated_games() -> List[Tuple[str, List[int]]]:
    j = _load_json(OUT_JOGOS)

    # valida cabeçalho mínimo
    if str(j.get("game", "")).lower() != "megasena":
        raise ValueError("out/jogos_gerados.json não é game=megasena")

    if int(j.get("ticket_size")) != TICKET_SIZE:
        raise ValueError(f"ticket_size esperado={TICKET_SIZE}")

    if int(j.get("draw_size")) != DRAW_SIZE:
        raise ValueError(f"draw_size esperado={DRAW_SIZE}")

    if int(j.get("n_games")) != N_GAMES:
        raise ValueError(f"n_games esperado={N_GAMES}")

    games = j.get("games")
    if not isinstance(games, list) or len(games) != N_GAMES:
        raise ValueError("Lista games inválida ou tamanho diferente de 15")

    out: List[Tuple[str, List[int]]] = []
    for g in games:
        gid = str(g.get("id", "")).strip() or "J??"
        nums_raw = g.get("numbers")
        nums = _validate_numbers(_parse_int_list(nums_raw), expected_len=TICKET_SIZE, min_n=MIN_N, max_n=MAX_N)
        out.append((gid, nums))
    return out


def already_logged(concurso: int) -> bool:
    if not PERF_LOG.exists():
        return False
    # checagem simples e barata (append-only): procura "concurso": <n>
    needle = f'"concurso": {concurso}'
    with PERF_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if needle in line:
                return True
    return False


def compute_hits(draw_set: Set[int], games: List[Tuple[str, List[int]]]) -> Dict[str, Any]:
    per_game = []
    hits_count = {k: 0 for k in range(0, TICKET_SIZE + 1)}

    for gid, nums in games:
        hits = sum(1 for n in nums if n in draw_set)
        hits_count[hits] = hits_count.get(hits, 0) + 1
        per_game.append({"id": gid, "numbers": nums, "hits": hits})

    max_hits = max(x["hits"] for x in per_game) if per_game else 0
    ge4 = sum(1 for x in per_game if x["hits"] >= 4)
    ge5 = sum(1 for x in per_game if x["hits"] >= 5)
    eq6 = sum(1 for x in per_game if x["hits"] == 6)

    # score simples e auditável
    score = (ge4 * 1) + (ge5 * 5) + (eq6 * 50)

    return {
        "per_game": per_game,
        "summary": {
            "max_hits": max_hits,
            "count_ge4": ge4,
            "count_ge5": ge5,
            "count_eq6": eq6,
            "score": score,
            "hist_hits_count": hits_count,
        }
    }


def main() -> None:
    if not OUT_JOGOS.exists():
        raise FileNotFoundError("Não encontrei out/jogos_gerados.json")

    latest = fetch_latest_draw()
    _write_json(LAST_RESULT, {
        "concurso": latest.concurso,
        "data": latest.data,
        "dezenas": list(latest.dezenas),
        "fetched_at_utc": datetime.now(timezone.utc).isoformat()
    })

    if already_logged(latest.concurso):
        print(f"[COMPARE] Concurso {latest.concurso} já logado. Nenhuma ação.")
        return

    games = load_generated_games()
    draw_set = set(latest.dezenas)

    result = compute_hits(draw_set, games)

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "game": "megasena",
        "concurso": latest.concurso,
        "data_sorteio": latest.data,
        "dezenas_sorteadas": list(latest.dezenas),
        "ticket_size": TICKET_SIZE,
        "n_games": N_GAMES,
        **result["summary"],
        "games": result["per_game"],  # se quiser mais leve, depois removemos e deixamos só resumo
    }

    _append_jsonl(PERF_LOG, event)
    print(f"[COMPARE] OK: concurso={latest.concurso} max_hits={event['max_hits']} ge4={event['count_ge4']} score={event['score']}")


if __name__ == "__main__":
    main()
