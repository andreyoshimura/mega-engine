from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import requests

# ===== Config =====
REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_JOGOS = REPO_ROOT / "out" / "jogos_gerados.json"

DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PERF_LOG = DATA_DIR / "performance_log.jsonl"  # append-only
LAST_RESULT = DATA_DIR / "last_result.json"

API_LATEST = "https://loteriascaixa-api.herokuapp.com/api/megasena/latest"

MIN_N = 1
MAX_N = 60
DRAW_SIZE = 6
TICKET_SIZE = 9


@dataclass(frozen=True)
class LatestDraw:
    concurso: int
    data: str
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
    if not isinstance(x, list):
        return []
    out = []
    for v in x:
        try:
            out.append(int(v))
        except Exception:
            pass
    return out


def _validate_numbers(nums: List[int], *, expected_len: int, min_n: int, max_n: int) -> List[int]:
    cleaned = []
    for n in nums:
        if isinstance(n, int) and min_n <= n <= max_n:
            cleaned.append(n)
    uniq = sorted(set(cleaned))
    if len(uniq) != expected_len:
        raise ValueError(
            f"Números inválidos: esperado {expected_len} distintos em [{min_n}..{max_n}]. Obtido={uniq}"
        )
    return uniq


def fetch_latest_draw() -> LatestDraw:
    r = requests.get(API_LATEST, timeout=30)
    r.raise_for_status()
    data = r.json()

    concurso = int(data.get("concurso"))
    data_sorteio = str(data.get("data", "")).strip()

    dezenas_raw = data.get("dezenas") or data.get("listaDezenas") or data.get("numeros") or []
    dezenas = _validate_numbers(
        _parse_int_list(dezenas_raw),
        expected_len=DRAW_SIZE,
        min_n=MIN_N,
        max_n=MAX_N
    )

    return LatestDraw(concurso=concurso, data=data_sorteio, dezenas=tuple(dezenas))


def load_generated_games() -> Tuple[int, List[Tuple[str, List[int]]]]:
    j = _load_json(OUT_JOGOS)

    if str(j.get("game", "")).lower() != "megasena":
        raise ValueError("out/jogos_gerados.json não é game=megasena")

    if int(j.get("ticket_size")) != TICKET_SIZE:
        raise ValueError(f"ticket_size esperado={TICKET_SIZE}")

    if int(j.get("draw_size")) != DRAW_SIZE:
        raise ValueError(f"draw_size esperado={DRAW_SIZE}")

    games = j.get("games")
    if not isinstance(games, list) or len(games) == 0:
        raise ValueError("Lista games inválida ou vazia")

    n_games_runtime = len(games)

    declared = j.get("n_games")
    if declared is not None:
        try:
            if int(declared) != n_games_runtime:
                print(
                    f"[WARN] n_games no JSON={declared}, "
                    f"mas lista tem {n_games_runtime}. Usando lista real."
                )
        except Exception:
            print(f"[WARN] n_games inválido no JSON: {declared}")

    out: List[Tuple[str, List[int]]] = []
    for g in games:
        gid = str(g.get("id", "")).strip() or "J??"
        nums = _validate_numbers(
            _parse_int_list(g.get("numbers")),
            expected_len=TICKET_SIZE,
            min_n=MIN_N,
            max_n=MAX_N
        )
        out.append((gid, nums))

    return n_games_runtime, out


def already_logged(concurso: int) -> bool:
    if not PERF_LOG.exists():
        return False
    needle = f'"concurso": {concurso}'
    with PERF_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if needle in line:
                return True
    return False


def compute_hits(draw_set: Set[int], games: List[Tuple[str, List[int]]]) -> Dict[str, Any]:
    per_game = []

    for gid, nums in games:
        hits = sum(1 for n in nums if n in draw_set)
        per_game.append({"id": gid, "numbers": nums, "hits": hits})

    max_hits = max((x["hits"] for x in per_game), default=0)
    ge4 = sum(1 for x in per_game if x["hits"] >= 4)
    ge5 = sum(1 for x in per_game if x["hits"] >= 5)
    eq6 = sum(1 for x in per_game if x["hits"] == 6)

    score = (ge4 * 1) + (ge5 * 5) + (eq6 * 50)

    hist: Dict[int, int] = {}
    for x in per_game:
        h = x["hits"]
        hist[h] = hist.get(h, 0) + 1

    return {
        "per_game": per_game,
        "summary": {
            "max_hits": max_hits,
            "count_ge4": ge4,
            "count_ge5": ge5,
            "count_eq6": eq6,
            "score": score,
            "hist_hits_count": hist,
        }
    }


def compute_rolling_metrics(last_n: int = 20) -> Dict[str, Any]:
    if not PERF_LOG.exists():
        return {}

    lines = PERF_LOG.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return {}

    recent = lines[-last_n:]

    max_hits_list = []
    score_list = []
    ge4_total = 0
    total_games = 0

    for line in recent:
        try:
            obj = json.loads(line)
            max_hits_list.append(obj.get("max_hits", 0))
            score_list.append(obj.get("score", 0))
            ge4_total += obj.get("count_ge4", 0)
            total_games += obj.get("n_games", 0)
        except Exception:
            continue

    if not max_hits_list or total_games == 0:
        return {}

    avg_max_hits = sum(max_hits_list) / len(max_hits_list)
    avg_score = sum(score_list) / len(score_list)
    rate_ge4 = ge4_total / total_games

    return {
        "avg_max_hits": round(avg_max_hits, 4),
        "avg_score": round(avg_score, 4),
        "rate_ge4": round(rate_ge4, 4),
        "window": len(recent),
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
        print(f"[COMPARE] Concurso {latest.concurso} já logado.")
        return

    n_games_runtime, games = load_generated_games()
    draw_set = set(latest.dezenas)

    result = compute_hits(draw_set, games)
    rolling = compute_rolling_metrics(20)

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "game": "megasena",
        "concurso": latest.concurso,
        "data_sorteio": latest.data,
        "dezenas_sorteadas": list(latest.dezenas),
        "ticket_size": TICKET_SIZE,
        "n_games": n_games_runtime,
        **result["summary"],
        "rolling_20": rolling,
        "games": result["per_game"],
    }

    _append_jsonl(PERF_LOG, event)

    print(
        f"[COMPARE] OK: concurso={latest.concurso} "
        f"n_games={n_games_runtime} "
        f"max_hits={event['max_hits']} "
        f"score={event['score']}"
    )


if __name__ == "__main__":
    main()
