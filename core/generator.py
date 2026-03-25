"""
Mega-Engine - Generator (Mega-Sena)

Gera jogos estatisticos preservando o contrato JSON usado pela automacao.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from core.config import (
    CONFIG_PATH,
    DEFAULT_MAX_INTERSECTION,
    DEFAULT_N_SIM,
    DEFAULT_NUM_GAMES,
    DEFAULT_TICKET_SIZE,
    FEATURES_PATH,
    GAME_NAME,
    LAST_RESULT_PATH,
    MAX_NUMBER,
    MIN_NUMBER,
    OUT_GAMES_PATH,
    OUT_HISTORY_DIR,
    REPO_ROOT,
    get_draw_size,
    get_parameters,
    load_config,
)
from core.features_megasena import build_features
from core.versioning import register_strategy

OUT_PATH = OUT_GAMES_PATH

N_GAMES = DEFAULT_NUM_GAMES
TICKET_SIZE = DEFAULT_TICKET_SIZE
DRAW_SIZE = 6
N_SIM = DEFAULT_N_SIM
MIN_N = MIN_NUMBER
MAX_N = MAX_NUMBER
MAX_INTERSECTION = DEFAULT_MAX_INTERSECTION


def weighted_sample(probs: np.ndarray, k: int, rng: np.random.Generator) -> list[int]:
    """Amostragem ponderada sem reposicao (Efraimidis-Spirakis)."""
    if len(probs) != MAX_N:
        raise ValueError(f"Probabilidades invalidas: esperado vetor com {MAX_N} posicoes.")
    if k <= 0 or k > len(probs):
        raise ValueError(f"ticket_size invalido: {k}")

    safe_probs = np.where(np.isfinite(probs), probs, 0.0)
    safe_probs = np.maximum(safe_probs, 0.0)

    if float(safe_probs.sum()) <= 0:
        safe_probs = np.ones(len(probs), dtype=float) / len(probs)
    else:
        safe_probs = safe_probs / safe_probs.sum()

    u = np.clip(rng.random(len(safe_probs)), 1e-12, 1.0)
    keys = -np.log(u) / np.maximum(safe_probs, 1e-12)
    idx = np.argsort(keys)[:k] + 1
    return sorted(int(x) for x in idx)


def validate_game(game: list[int], *, ticket_size: int = TICKET_SIZE) -> None:
    if len(game) != ticket_size:
        raise ValueError(f"Jogo invalido: esperado {ticket_size}, obtido {len(game)}")
    if any((n < MIN_N or n > MAX_N) for n in game):
        raise ValueError(f"Jogo invalido: dezenas fora de [{MIN_N}..{MAX_N}]")
    if len(set(game)) != ticket_size:
        raise ValueError("Jogo invalido: dezenas repetidas")


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    scores = np.where(np.isfinite(scores), scores, 0.0)
    scores = np.maximum(scores, 0.0) + 1e-9

    total = float(scores.sum())
    if total <= 0:
        return np.ones(MAX_N) / MAX_N
    return scores / total


def load_probs(features_path: Path = FEATURES_PATH) -> np.ndarray:
    if not features_path.exists():
        return np.ones(MAX_N) / MAX_N

    df = pd.read_csv(features_path)
    if "freq_100" not in df.columns:
        return np.ones(MAX_N) / MAX_N

    scores = df["freq_100"].astype(float).values
    if "dezena" in df.columns:
        probs = np.zeros(MAX_N)
        for d, s in zip(df["dezena"].astype(int), scores):
            if MIN_N <= d <= MAX_N:
                probs[d - 1] = float(s)
        scores = probs

    return _normalize_scores(scores)


def scores_from_features(features_df: pd.DataFrame) -> np.ndarray:
    if "freq_100" not in features_df.columns:
        return np.ones(MAX_N) / MAX_N

    scores = features_df["freq_100"].astype(float).values
    if "dezena" in features_df.columns:
        ordered_scores = np.zeros(MAX_N)
        for d, s in zip(features_df["dezena"].astype(int), scores):
            if MIN_N <= d <= MAX_N:
                ordered_scores[d - 1] = float(s)
        scores = ordered_scores

    return _normalize_scores(scores)


def build_probabilities_from_history(results_df: pd.DataFrame, window: int = 100) -> np.ndarray:
    features_df = build_features(results_df, window=window)
    return scores_from_features(features_df)


def generate_games_from_probs(
    probs: np.ndarray,
    *,
    seed: int | None = None,
    n_games: int = N_GAMES,
    ticket_size: int = TICKET_SIZE,
    n_sim: int = N_SIM,
    max_intersection: int = MAX_INTERSECTION,
) -> list[list[int]]:
    if n_games <= 0:
        raise ValueError("n_games deve ser maior que zero")
    if ticket_size <= 0 or ticket_size > MAX_N:
        raise ValueError("ticket_size invalido")
    if n_sim <= 0:
        raise ValueError("n_sim deve ser maior que zero")

    rng = np.random.default_rng(seed)
    candidates = [weighted_sample(probs, ticket_size, rng) for _ in range(n_sim)]

    selected: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()

    for game in candidates:
        if len(selected) >= n_games:
            break
        if all(len(set(game).intersection(existing)) <= max_intersection for existing in selected):
            selected.append(game)
            seen.add(tuple(game))

    if len(selected) < n_games:
        for game in candidates:
            key = tuple(game)
            if key not in seen:
                selected.append(game)
                seen.add(key)
                if len(selected) >= n_games:
                    break

    while len(selected) < n_games:
        game = tuple(int(x) for x in sorted(rng.choice(np.arange(MIN_N, MAX_N + 1), size=ticket_size, replace=False)))
        if game not in seen:
            selected.append(list(game))
            seen.add(game)

    for game in selected:
        validate_game(game, ticket_size=ticket_size)

    return selected[:n_games]


def generate_games(seed: int | None = None, config: dict[str, Any] | None = None) -> list[list[int]]:
    config = config or load_config()
    params = get_parameters(config)
    probs = load_probs()
    return generate_games_from_probs(
        probs,
        seed=seed,
        n_games=int(params.get("num_games", N_GAMES)),
        ticket_size=int(params.get("ticket_size", TICKET_SIZE)),
        n_sim=int(params.get("n_sim", N_SIM)),
        max_intersection=int(params.get("max_intersection", MAX_INTERSECTION)),
    )


def _load_last_result() -> dict[str, Any] | None:
    if not LAST_RESULT_PATH.exists():
        return None
    with LAST_RESULT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_output_payload(games: list[list[int]], config: dict[str, Any]) -> dict[str, Any]:
    params = get_parameters(config)
    ticket_size = int(params.get("ticket_size", TICKET_SIZE))
    draw_size = int(params.get("draw_size", get_draw_size(config)))
    last_result = _load_last_result()
    latest_concurso = None
    next_concurso = None

    if isinstance(last_result, dict) and "concurso" in last_result:
        latest_concurso = int(last_result["concurso"])
        next_concurso = latest_concurso + 1

    return {
        "game": GAME_NAME,
        "ticket_size": ticket_size,
        "draw_size": draw_size,
        "n_games": len(games),
        "objective": "maximize_hit_rate_ge4",
        "games": [
            {"id": f"J{str(i + 1).zfill(2)}", "numbers": [int(n) for n in game]}
            for i, game in enumerate(games)
        ],
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "strategy_name": config.get("strategy_name"),
            "model_version": config.get("model_version"),
            "source_features": str(FEATURES_PATH.relative_to(REPO_ROOT)),
            "latest_known_concurso": latest_concurso,
            "target_concurso": next_concurso,
            "config_path": str(CONFIG_PATH.relative_to(REPO_ROOT)),
        },
    }


def export_json(games: list[list[int]], config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    output = build_output_payload(games, config)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    target_concurso = output.get("metadata", {}).get("target_concurso")
    if target_concurso is not None:
        OUT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        history_path = OUT_HISTORY_DIR / f"jogos_concurso_{int(target_concurso)}.json"
        with history_path.open("w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    return output


if __name__ == "__main__":
    config = load_config()
    games = generate_games(config=config)
    export_json(games, config=config)
    register_strategy(config, execution_type="production")
