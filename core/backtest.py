from __future__ import annotations

import json
from typing import Any

import pandas as pd

from core.compare_results import compute_hits
from core.config import (
    BACKTEST_REPORT_PATH as OUT_PATH,
    DEFAULT_BACKTEST_N_SIM,
    DEFAULT_MAX_INTERSECTION,
    DEFAULT_MIN_HISTORY,
    DEFAULT_N_SIM,
    DEFAULT_NUM_GAMES,
    DEFAULT_TICKET_SIZE,
    DEFAULT_WINDOW,
    RESULTS_PATH,
    get_parameters,
    load_config,
)
from core.generator import build_probabilities_from_history, generate_games_from_probs
from core.versioning import _config_hash

DRAW_SIZE = 6


def build_probability_cache(
    results_df: pd.DataFrame,
    *,
    windows: list[int],
    min_history: int,
    config: dict[str, Any] | None = None,
) -> dict[int, dict[int, Any]]:
    caches: dict[int, dict[int, Any]] = {}
    unique_windows = sorted({int(window) for window in windows})

    for window in unique_windows:
        start_idx = max(int(min_history), window)
        window_cache: dict[int, Any] = {}
        for idx in range(start_idx, len(results_df)):
            history = results_df.iloc[:idx].copy()
            window_cache[idx] = build_probabilities_from_history(history, window=window, config=config)
        caches[window] = window_cache

    return caches


def run_backtest(
    results_df: pd.DataFrame,
    *,
    window: int = DEFAULT_WINDOW,
    min_history: int = DEFAULT_MIN_HISTORY,
    n_games: int = DEFAULT_NUM_GAMES,
    ticket_size: int = DEFAULT_TICKET_SIZE,
    n_sim: int = DEFAULT_N_SIM,
    max_intersection: int = DEFAULT_MAX_INTERSECTION,
    seed_base: int = 10_000,
    config: dict | None = None,
    probability_cache: dict[int, Any] | None = None,
    include_per_draw: bool = True,
) -> dict:
    if len(results_df) <= min_history:
        raise ValueError("Historico insuficiente para backtest.")

    per_draw = []
    total_draws = 0
    sum_max_hits = 0.0
    sum_score = 0.0
    sum_coverage_rate = 0.0
    sum_neglected = 0.0
    count_ge4_draws = 0
    count_ge5_draws = 0
    total_eq6 = 0
    for idx in range(min_history, len(results_df)):
        target = results_df.iloc[idx]

        if probability_cache is not None and idx in probability_cache:
            probs = probability_cache[idx]
        else:
            history = results_df.iloc[:idx].copy()
            probs = build_probabilities_from_history(history, window=window, config=config)
        games = generate_games_from_probs(
            probs,
            seed=seed_base + idx,
            n_games=n_games,
            ticket_size=ticket_size,
            n_sim=n_sim,
            max_intersection=max_intersection,
        )

        draw_numbers = [int(target[f"d{i}"]) for i in range(1, DRAW_SIZE + 1)]
        compare_input = [(f"J{str(i + 1).zfill(2)}", game) for i, game in enumerate(games)]
        result = compute_hits(set(draw_numbers), compare_input)
        summary = result["summary"]
        total_draws += 1
        sum_max_hits += float(summary["max_hits"])
        sum_score += float(summary["score"])
        sum_coverage_rate += float(summary.get("coverage_rate", 0.0))
        sum_neglected += float(len(summary.get("neglected_draw_numbers", [])))
        count_ge4_draws += int(summary["count_ge4"] > 0)
        count_ge5_draws += int(summary["count_ge5"] > 0)
        total_eq6 += int(summary["count_eq6"])

        if include_per_draw:
            per_draw.append(
                {
                    "concurso": int(target["concurso"]),
                    "data": str(target["data"]),
                    "dezenas_sorteadas": draw_numbers,
                    **summary,
                    "games": result["per_game"],
                }
            )

    avg_max_hits = sum_max_hits / total_draws
    avg_score = sum_score / total_draws
    rate_ge4 = count_ge4_draws / total_draws
    rate_ge5 = count_ge5_draws / total_draws
    avg_coverage_rate = sum_coverage_rate / total_draws
    avg_neglected = sum_neglected / total_draws

    return {
        "summary": {
            "draws_evaluated": total_draws,
            "window": window,
            "min_history": min_history,
            "n_games": n_games,
            "ticket_size": ticket_size,
            "n_sim": n_sim,
            "max_intersection": max_intersection,
            "avg_max_hits": round(avg_max_hits, 4),
            "avg_score": round(avg_score, 4),
            "rate_ge4": round(rate_ge4, 4),
            "rate_ge5": round(rate_ge5, 4),
            "total_eq6": total_eq6,
            "avg_coverage_rate": round(avg_coverage_rate, 4),
            "avg_neglected_draw_numbers": round(avg_neglected, 4),
        },
        "per_draw": per_draw if include_per_draw else [],
    }


def main() -> None:
    config = load_config()
    params = get_parameters(config)

    results_df = pd.read_csv(RESULTS_PATH)
    window = int(params.get("window", DEFAULT_WINDOW))
    min_history = max(int(params.get("min_history", DEFAULT_MIN_HISTORY)), window)
    n_games = int(params.get("num_games", DEFAULT_NUM_GAMES))
    ticket_size = int(params.get("ticket_size", DEFAULT_TICKET_SIZE))
    n_sim = int(params.get("backtest_n_sim", min(int(params.get("n_sim", DEFAULT_N_SIM)), DEFAULT_BACKTEST_N_SIM)))
    max_intersection = int(params.get("max_intersection", DEFAULT_MAX_INTERSECTION))

    report = run_backtest(
        results_df,
        window=window,
        min_history=min_history,
        n_games=n_games,
        ticket_size=ticket_size,
        n_sim=n_sim,
        max_intersection=max_intersection,
        config=config,
    )
    report["strategy"] = {
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "config_hash": _config_hash(config),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    summary = report["summary"]
    draws = summary["draws_evaluated"]
    avg_max_hits = summary["avg_max_hits"]
    rate_ge4 = summary["rate_ge4"]
    print("[BACKTEST] OK:", f"draws={draws}", f"avg_max_hits={avg_max_hits}", f"rate_ge4={rate_ge4}")


if __name__ == "__main__":
    main()
