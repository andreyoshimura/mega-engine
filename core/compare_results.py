from __future__ import annotations

import csv
import json
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import (
    GAME_NAME,
    LAST_RESULT_PATH,
    MAX_NUMBER,
    MIN_NUMBER,
    OUT_GAMES_PATH,
    OUT_HISTORY_DIR,
    PERFORMANCE_LOG_PATH,
    RESULTS_PATH,
)

OUT_JOGOS = OUT_GAMES_PATH
OUT_HISTORY = OUT_HISTORY_DIR
PERF_LOG = PERFORMANCE_LOG_PATH
LAST_RESULT = LAST_RESULT_PATH
RESULTS_CSV = RESULTS_PATH
MIN_N = MIN_NUMBER
MAX_N = MAX_NUMBER
DEFAULT_DRAW_SIZE = 6
DEFAULT_TICKET_SIZE = 9


@dataclass(frozen=True)
class LatestDraw:
    concurso: int
    data: str
    dezenas: tuple[int, ...]


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _draw_date_to_timestamp_utc(draw_date: str) -> str:
    parsed = datetime.strptime(str(draw_date), "%d/%m/%Y")
    return parsed.replace(tzinfo=timezone.utc).isoformat()


def _parse_int_list(x: Any) -> list[int]:
    if not isinstance(x, list):
        return []
    out = []
    for v in x:
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            continue
    return out


def _validate_numbers(nums: list[int], *, expected_len: int) -> list[int]:
    cleaned = [n for n in nums if isinstance(n, int) and MIN_N <= n <= MAX_N]
    uniq = sorted(set(cleaned))
    if len(uniq) == expected_len:
        return uniq
    raise ValueError(f"Numeros invalidos: esperado {expected_len} distintos. Obtido={uniq}")


def load_latest_draw_from_file() -> LatestDraw:
    if not LAST_RESULT.exists():
        raise FileNotFoundError("data/last_result.json nao encontrado.")

    data = _load_json(LAST_RESULT)
    dezenas = _validate_numbers(_parse_int_list(data.get("dezenas")), expected_len=DEFAULT_DRAW_SIZE)
    return LatestDraw(concurso=int(data["concurso"]), data=str(data["data"]), dezenas=tuple(dezenas))


def load_pending_draws(latest_draw: LatestDraw) -> list[LatestDraw]:
    if not RESULTS_CSV.exists():
        return [latest_draw]

    draws: list[LatestDraw] = []
    with RESULTS_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                concurso = int(row["concurso"])
            except (KeyError, TypeError, ValueError):
                continue
            if concurso > latest_draw.concurso:
                continue
            try:
                dezenas = _validate_numbers(
                    [int(row[f"d{i}"]) for i in range(1, DEFAULT_DRAW_SIZE + 1)],
                    expected_len=DEFAULT_DRAW_SIZE,
                )
            except (KeyError, TypeError, ValueError):
                continue
            draws.append(LatestDraw(concurso=concurso, data=str(row["data"]), dezenas=tuple(dezenas)))

    draws.sort(key=lambda draw: draw.concurso)
    if not draws or draws[-1].concurso != latest_draw.concurso:
        draws.append(latest_draw)
    return draws


def _payload_to_runtime(payload: dict[str, Any]) -> tuple[dict[str, Any], list[tuple[str, list[int]]]]:
    if str(payload.get("game", "")).lower() != GAME_NAME:
        raise ValueError("out/jogos_gerados.json invalido")

    games = payload.get("games")
    if not isinstance(games, list) or not games:
        raise ValueError("Lista games invalida ou vazia")

    ticket_size = int(payload.get("ticket_size", DEFAULT_TICKET_SIZE))
    out: list[tuple[str, list[int]]] = []
    for game in games:
        gid = str(game.get("id", "")).strip() or "J??"
        nums = _validate_numbers(_parse_int_list(game.get("numbers")), expected_len=ticket_size)
        out.append((gid, nums))

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    info = {
        "ticket_size": ticket_size,
        "draw_size": int(payload.get("draw_size", DEFAULT_DRAW_SIZE)),
        "n_games": len(out),
        "objective": payload.get("objective"),
        "metadata": metadata,
    }
    return info, out


def load_generated_games(concurso: int) -> tuple[dict[str, Any], list[tuple[str, list[int]]]]:
    history_path = OUT_HISTORY / f"jogos_concurso_{int(concurso)}.json"
    if history_path.exists():
        payload = _load_json(history_path)
        return _payload_to_runtime(payload)

    payload = _load_json(OUT_JOGOS)
    info, games = _payload_to_runtime(payload)
    target_concurso = info["metadata"].get("target_concurso")
    if target_concurso is not None and int(target_concurso) != int(concurso):
        raise ValueError(
            f"Jogos atuais apontam para o concurso {target_concurso}, mas o resultado publicado eh do concurso {concurso}."
        )
    return info, games


def already_logged(concurso: int) -> bool:
    if not PERF_LOG.exists():
        return False

    with PERF_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if int(event.get("concurso", -1)) == concurso:
                return True
    return False


def load_logged_concursos() -> set[int]:
    if not PERF_LOG.exists():
        return set()

    concursos: set[int] = set()
    with PERF_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                concursos.add(int(event.get("concurso", -1)))
            except (TypeError, ValueError):
                continue
    return concursos


def summarize_recent_events(window: int = 20) -> dict[str, Any] | None:
    if not PERF_LOG.exists():
        return None

    events: list[dict[str, Any]] = []
    with PERF_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not events:
        return None

    sample = events[-window:]
    draws = len(sample)
    return {
        "avg_max_hits": round(sum(float(e.get("max_hits", 0)) for e in sample) / draws, 4),
        "avg_score": round(sum(float(e.get("score", 0)) for e in sample) / draws, 4),
        "rate_ge4": round(sum(1 for e in sample if int(e.get("count_ge4", 0)) > 0) / draws, 4),
        "window": draws,
    }


def compute_hits(draw_set: set[int], games: list[tuple[str, list[int]]]) -> dict[str, Any]:
    per_game = []
    covered_numbers: set[int] = set()
    for gid, nums in games:
        hits = sum(1 for n in nums if n in draw_set)
        per_game.append({"id": gid, "numbers": nums, "hits": hits})
        covered_numbers.update(nums)

    max_hits = max((item["hits"] for item in per_game), default=0)
    ge4 = sum(1 for item in per_game if item["hits"] >= 4)
    ge5 = sum(1 for item in per_game if item["hits"] >= 5)
    eq6 = sum(1 for item in per_game if item["hits"] == 6)
    score = (ge4 * 1) + (ge5 * 5) + (eq6 * 50)
    hit_counter = Counter(item["hits"] for item in per_game)
    hist_hits_count = {str(i): int(hit_counter.get(i, 0)) for i in range(10)}
    neglected_draw_numbers = sorted(int(n) for n in draw_set if n not in covered_numbers)
    covered_draw_numbers = sorted(int(n) for n in draw_set if n in covered_numbers)
    coverage_count = len(covered_draw_numbers)
    draw_size = len(draw_set)

    return {
        "per_game": per_game,
        "summary": {
            "max_hits": max_hits,
            "count_ge4": ge4,
            "count_ge5": ge5,
            "count_eq6": eq6,
            "score": score,
            "hist_hits_count": hist_hits_count,
            "coverage_count": coverage_count,
            "coverage_rate": round(coverage_count / draw_size, 4) if draw_size else 0.0,
            "covered_draw_numbers": covered_draw_numbers,
            "neglected_draw_numbers": neglected_draw_numbers,
        },
    }


def main() -> None:
    try:
        latest = load_latest_draw_from_file()
    except FileNotFoundError as exc:
        print(f"[COMPARE] Skip: {exc}")
        return

    logged_concursos = load_logged_concursos()
    latest_logged_concurso = max(logged_concursos, default=0)
    pending_draws = [
        draw
        for draw in load_pending_draws(latest)
        if draw.concurso > latest_logged_concurso and draw.concurso not in logged_concursos
    ]
    if not pending_draws:
        print(f"[COMPARE] Concurso {latest.concurso} ja logado.")
        return

    logged_count = 0
    for draw in pending_draws:
        try:
            generated_meta, games = load_generated_games(draw.concurso)
        except (FileNotFoundError, ValueError) as exc:
            print(f"[COMPARE] Skip concurso={draw.concurso}: {exc}")
            continue

        draw_set = set(draw.dezenas)
        result = compute_hits(draw_set, games)
        rolling_20 = summarize_recent_events(window=20)
        logged_at_utc = datetime.now(timezone.utc).isoformat()
        event = {
            "timestamp_utc": _draw_date_to_timestamp_utc(draw.data),
            "game": GAME_NAME,
            "concurso": draw.concurso,
            "data_sorteio": draw.data,
            "dezenas_sorteadas": list(draw.dezenas),
            "ticket_size": generated_meta["ticket_size"],
            "n_games": generated_meta["n_games"],
            "meta": {
                "git_sha": os.getenv("GITHUB_SHA", "").strip() or None,
                "strategy": generated_meta["metadata"].get("strategy_name")
                or os.getenv("STRATEGY_NAME", "").strip()
                or "megasena_v1",
                "model_version": generated_meta["metadata"].get("model_version"),
                "generated_at_utc": generated_meta["metadata"].get("generated_at_utc"),
                "target_concurso": generated_meta["metadata"].get("target_concurso"),
                "logged_at_utc": logged_at_utc,
            },
            **result["summary"],
            "games": result["per_game"],
        }
        if rolling_20 is not None:
            event["rolling_20"] = rolling_20

        _append_jsonl(PERF_LOG, event)
        logged_count += 1
        print(
            "[COMPARE] OK:",
            f"concurso={draw.concurso}",
            f"n_games={generated_meta['n_games']}",
            f"max_hits={event['max_hits']}",
            f"score={event['score']}",
        )

    if logged_count == 0:
        print("[COMPARE] Nenhum concurso pendente com snapshot canonico disponivel.")


if __name__ == "__main__":
    main()
