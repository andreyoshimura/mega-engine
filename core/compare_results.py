from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# ============================================================
# CONFIG
# ============================================================

REPO_ROOT = Path(__file__).resolve().parents[1]

OUT_JOGOS = REPO_ROOT / "out" / "jogos_gerados.json"

DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PERF_LOG = DATA_DIR / "performance_log.jsonl"  # append-only
LAST_RESULT = DATA_DIR / "last_result.json"

MIN_N = 1
MAX_N = 60
DRAW_SIZE = 6
TICKET_SIZE = 9


# ============================================================
# MODELO DE DADOS
# ============================================================

@dataclass(frozen=True)
class LatestDraw:
    concurso: int
    data: str
    dezenas: Tuple[int, ...]


# ============================================================
# UTIL
# ============================================================

def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def _validate_numbers(nums: List[int], *, expected_len: int) -> List[int]:
    cleaned = []
    for n in nums:
        if isinstance(n, int) and MIN_N <= n <= MAX_N:
            cleaned.append(n)

    uniq = sorted(set(cleaned))

    if len(uniq) != expected_len:
        raise ValueError(
            f"Números inválidos: esperado {expected_len} distintos. Obtido={uniq}"
        )

    return uniq


# ============================================================
# 🔥 AGORA LÊ SOMENTE DO ARQUIVO LOCAL
# ============================================================

def load_latest_draw_from_file() -> LatestDraw:
    """
    Fonte única da verdade.
    Compare NÃO consulta API.
    Apenas lê data/last_result.json
    """
    if not LAST_RESULT.exists():
        raise FileNotFoundError("data/last_result.json não encontrado.")

    data = _load_json(LAST_RESULT)

    dezenas = _validate_numbers(
        _parse_int_list(data.get("dezenas")),
        expected_len=DRAW_SIZE,
    )

    return LatestDraw(
        concurso=int(data["concurso"]),
        data=str(data["data"]),
        dezenas=tuple(dezenas),
    )


# ============================================================
# JOGOS GERADOS
# ============================================================

def load_generated_games() -> Tuple[int, List[Tuple[str, List[int]]]]:
    j = _load_json(OUT_JOGOS)

    if str(j.get("game", "")).lower() != "megasena":
        raise ValueError("out/jogos_gerados.json inválido")

    games = j.get("games")
    if not isinstance(games, list) or len(games) == 0:
        raise ValueError("Lista games inválida ou vazia")

    out: List[Tuple[str, List[int]]] = []

    for g in games:
        gid = str(g.get("id", "")).strip() or "J??"
        nums = _validate_numbers(
            _parse_int_list(g.get("numbers")),
            expected_len=TICKET_SIZE,
        )
        out.append((gid, nums))

    return len(out), out


# ============================================================
# LOG CHECK
# ============================================================

def already_logged(concurso: int) -> bool:
    if not PERF_LOG.exists():
        return False

    needle = f'"concurso": {concurso}'

    with PERF_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if needle in line:
                return True

    return False


# ============================================================
# COMPUTAÇÃO
# ============================================================

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

    return {
        "per_game": per_game,
        "summary": {
            "max_hits": max_hits,
            "count_ge4": ge4,
            "count_ge5": ge5,
            "count_eq6": eq6,
            "score": score,
        },
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    if not OUT_JOGOS.exists():
        raise FileNotFoundError("Não encontrei out/jogos_gerados.json")

    # 🔥 Agora NÃO consulta API
    latest = load_latest_draw_from_file()

    if already_logged(latest.concurso):
        print(f"[COMPARE] Concurso {latest.concurso} já logado.")
        return

    git_sha = os.getenv("GITHUB_SHA", "").strip() or "unknown"
    strategy = os.getenv("STRATEGY_NAME", "").strip() or "megasena_v1"

    n_games_runtime, games = load_generated_games()
    draw_set = set(latest.dezenas)

    result = compute_hits(draw_set, games)

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "game": "megasena",
        "concurso": latest.concurso,
        "data_sorteio": latest.data,
        "dezenas_sorteadas": list(latest.dezenas),
        "ticket_size": TICKET_SIZE,
        "n_games": n_games_runtime,
        "meta": {
            "git_sha": git_sha,
            "strategy": strategy,
        },
        **result["summary"],
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
