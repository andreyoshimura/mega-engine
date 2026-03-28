"""
Mega-Engine - Generator (Mega-Sena)

Gera jogos estatisticos preservando o contrato JSON usado pela automacao.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from itertools import combinations

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
    RESULTS_PATH,
    get_bayesian,
    get_draw_size,
    get_feature_weights,
    get_parameters,
    get_structural_rules,
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


def pair_key(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a <= b else (b, a)


def build_weak_pair_set(results_df: pd.DataFrame, bottom_pairs: int) -> set[tuple[int, int]]:
    if bottom_pairs <= 0 or results_df.empty:
        return set()

    counts: dict[tuple[int, int], int] = {}
    for _, row in results_df.iterrows():
        nums = sorted(int(row[f"d{i}"]) for i in range(1, DRAW_SIZE + 1))
        for a, b in combinations(nums, 2):
            key = pair_key(a, b)
            counts[key] = counts.get(key, 0) + 1

    ranked = sorted(((pair, count) for pair, count in counts.items() if count > 0), key=lambda item: (item[1], item[0]))
    return {pair for pair, _count in ranked[:bottom_pairs]}


def count_weak_pairs_in_game(game: list[int], weak_pairs: set[tuple[int, int]]) -> int:
    count = 0
    for a, b in combinations(game, 2):
        if pair_key(a, b) in weak_pairs:
            count += 1
    return count


def check_max_consecutive(game: list[int], max_seq: int) -> bool:
    if max_seq <= 0:
        return True

    ordered = sorted(game)
    run = 1
    for idx in range(1, len(ordered)):
        if ordered[idx] == ordered[idx - 1] + 1:
            run += 1
            if run > max_seq:
                return False
        else:
            run = 1
    return True


def diff_count(game_a: list[int], game_b: list[int]) -> int:
    inter = len(set(game_a).intersection(game_b))
    return len(game_a) - inter


def score_game(
    game: list[int],
    probs: np.ndarray,
    *,
    weak_pairs: set[tuple[int, int]] | None = None,
    penalty_weak_pair: float = 0.0,
) -> float:
    base_score = float(sum(probs[n - 1] for n in game if MIN_N <= n <= MAX_N))
    weak_pair_penalty = count_weak_pairs_in_game(game, weak_pairs or set()) * penalty_weak_pair
    return base_score - weak_pair_penalty


def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    scores = np.where(np.isfinite(scores), scores, 0.0)
    scores = np.maximum(scores, 0.0) + 1e-9

    total = float(scores.sum())
    if total <= 0:
        return np.ones(MAX_N) / MAX_N
    return scores / total


def load_probs(features_path: Path = FEATURES_PATH, config: dict[str, Any] | None = None) -> np.ndarray:
    if not features_path.exists():
        return np.ones(MAX_N) / MAX_N

    df = pd.read_csv(features_path)
    return scores_from_features(df, config=config)


def scores_from_features(features_df: pd.DataFrame, config: dict[str, Any] | None = None) -> np.ndarray:
    if "freq_100" not in features_df.columns and "bayes_score" not in features_df.columns:
        return np.ones(MAX_N) / MAX_N

    config = config or load_config()
    weights = get_feature_weights(config)

    scores = np.zeros(len(features_df), dtype=float)
    if "freq_20" in features_df.columns:
        scores += float(weights.get("freq_20", 0.0)) * features_df["freq_20"].astype(float).values
    if "freq_50" in features_df.columns:
        scores += float(weights.get("freq_50", 0.0)) * features_df["freq_50"].astype(float).values
    if "freq_100" in features_df.columns:
        scores += float(weights.get("freq_100", 0.0)) * features_df["freq_100"].astype(float).values
    if "atraso_score" in features_df.columns:
        scores += float(weights.get("atraso_score", 0.0)) * features_df["atraso_score"].astype(float).values
    if "bayes_mean" in features_df.columns:
        scores += float(weights.get("bayes_mean", 0.0)) * features_df["bayes_mean"].astype(float).values
    if "bayes_score" in features_df.columns:
        scores += float(weights.get("bayes_score", 0.0)) * features_df["bayes_score"].astype(float).values

    score_alpha = max(float(weights.get("score_alpha", 1.0)), 1e-6)
    if score_alpha != 1.0:
        scores = np.power(np.maximum(scores, 0.0), score_alpha)

    if "dezena" in features_df.columns:
        ordered_scores = np.zeros(MAX_N)
        for d, s in zip(features_df["dezena"].astype(int), scores):
            if MIN_N <= d <= MAX_N:
                ordered_scores[d - 1] = float(s)
        scores = ordered_scores

    return _normalize_scores(scores)


def build_probabilities_from_history(
    results_df: pd.DataFrame,
    window: int = 100,
    *,
    config: dict[str, Any] | None = None,
) -> np.ndarray:
    config = config or load_config()
    bayesian = get_bayesian(config)
    features_df = build_features(
        results_df,
        window=window,
        alpha_prior=float(bayesian["alpha_prior"]),
        beta_prior=float(bayesian["beta_prior"]),
    )
    return scores_from_features(features_df, config=config)


def generate_games_from_probs(
    probs: np.ndarray,
    *,
    seed: int | None = None,
    n_games: int = N_GAMES,
    ticket_size: int = TICKET_SIZE,
    n_sim: int = N_SIM,
    max_intersection: int = MAX_INTERSECTION,
    weak_pairs: set[tuple[int, int]] | None = None,
    max_seq: int = 0,
    min_diff: int = 0,
    penalty_weak_pair: float = 0.0,
) -> list[list[int]]:
    if n_games <= 0:
        raise ValueError("n_games deve ser maior que zero")
    if ticket_size <= 0 or ticket_size > MAX_N:
        raise ValueError("ticket_size invalido")
    if n_sim <= 0:
        raise ValueError("n_sim deve ser maior que zero")

    rng = np.random.default_rng(seed)
    candidates = [weighted_sample(probs, ticket_size, rng) for _ in range(n_sim)]
    seen_candidates: set[tuple[int, ...]] = set()
    ranked_candidates: list[tuple[float, list[int]]] = []
    for game in candidates:
        key = tuple(game)
        if key in seen_candidates:
            continue
        seen_candidates.add(key)
        if not check_max_consecutive(game, max_seq):
            continue
        ranked_candidates.append(
            (
                score_game(
                    game,
                    probs,
                    weak_pairs=weak_pairs,
                    penalty_weak_pair=penalty_weak_pair,
                ),
                game,
            )
        )

    ranked_candidates.sort(key=lambda item: item[0], reverse=True)

    selected: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()

    for _score, game in ranked_candidates:
        if len(selected) >= n_games:
            break
        if all(
            len(set(game).intersection(existing)) <= max_intersection and diff_count(game, existing) >= min_diff
            for existing in selected
        ):
            selected.append(game)
            seen.add(tuple(game))

    if len(selected) < n_games:
        for _score, game in ranked_candidates:
            key = tuple(game)
            if key not in seen:
                selected.append(game)
                seen.add(key)
                if len(selected) >= n_games:
                    break

    while len(selected) < n_games:
        game = tuple(int(x) for x in sorted(rng.choice(np.arange(MIN_N, MAX_N + 1), size=ticket_size, replace=False)))
        if game not in seen and check_max_consecutive(list(game), max_seq):
            selected.append(list(game))
            seen.add(game)

    for game in selected:
        validate_game(game, ticket_size=ticket_size)

    return selected[:n_games]


def generate_games(seed: int | None = None, config: dict[str, Any] | None = None) -> list[list[int]]:
    config = config or load_config()
    params = get_parameters(config)
    structural_rules = get_structural_rules(config)
    probs = load_probs(config=config)
    results_df = pd.read_csv(RESULTS_PATH)
    weak_pairs = build_weak_pair_set(results_df, int(structural_rules["bottom_pairs"]))
    return generate_games_from_probs(
        probs,
        seed=seed,
        n_games=int(params.get("num_games", N_GAMES)),
        ticket_size=int(params.get("ticket_size", TICKET_SIZE)),
        n_sim=int(params.get("n_sim", N_SIM)),
        max_intersection=int(params.get("max_intersection", MAX_INTERSECTION)),
        weak_pairs=weak_pairs,
        max_seq=int(structural_rules["max_seq"]),
        min_diff=int(structural_rules["min_diff"]),
        penalty_weak_pair=float(structural_rules["penalty_weak_pair"]),
    )


def _load_last_result() -> dict[str, Any] | None:
    if not LAST_RESULT_PATH.exists():
        return None
    with LAST_RESULT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def derive_generation_seed(config: dict[str, Any], last_result: dict[str, Any] | None = None) -> int:
    params = get_parameters(config)
    last_result = last_result if last_result is not None else _load_last_result()

    latest_concurso = None
    target_concurso = None
    if isinstance(last_result, dict) and "concurso" in last_result:
        latest_concurso = int(last_result["concurso"])
        target_concurso = latest_concurso + 1

    seed_payload = {
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "parameters": params,
        "latest_concurso": latest_concurso,
        "target_concurso": target_concurso,
    }
    digest = hashlib.sha256(json.dumps(seed_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def build_output_payload(games: list[list[int]], config: dict[str, Any]) -> dict[str, Any]:
    params = get_parameters(config)
    ticket_size = int(params.get("ticket_size", TICKET_SIZE))
    draw_size = int(params.get("draw_size", get_draw_size(config)))
    last_result = _load_last_result()
    latest_concurso = None
    next_concurso = None
    generation_seed = derive_generation_seed(config, last_result)
    bayesian = get_bayesian(config)
    feature_weights = get_feature_weights(config)
    structural_rules = get_structural_rules(config)

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
            "generation_seed": generation_seed,
            "bayesian": bayesian,
            "feature_weights": feature_weights,
            "structural_rules": structural_rules,
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
    games = generate_games(seed=derive_generation_seed(config), config=config)
    export_json(games, config=config)
    register_strategy(config, execution_type="production")
