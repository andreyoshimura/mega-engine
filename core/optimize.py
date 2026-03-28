from __future__ import annotations

import json
from itertools import product

import pandas as pd

from core.backtest import build_probability_cache, build_weak_pair_cache, run_backtest
from core.config import (
    DEFAULT_BACKTEST_N_SIM,
    DEFAULT_MIN_HISTORY,
    DEFAULT_NUM_GAMES,
    DEFAULT_OPTIMIZATION_GRID,
    DEFAULT_TICKET_SIZE,
    OPTIMIZATION_REPORT_PATH as OUT_PATH,
    RECOMMENDED_CONFIG_PATH,
    RESULTS_PATH,
    get_structural_rules,
    get_promotion_guard,
    get_optimization_grid,
    get_parameters,
    load_config,
)
from core.promotion import evaluate_promotion_guard, write_promotion_artifacts
from core.versioning import _config_hash


def build_grid(config: dict) -> list[dict]:
    grid = get_optimization_grid(config)
    combinations = []
    for window, num_games, max_intersection in product(
        grid.get("window", DEFAULT_OPTIMIZATION_GRID["window"]),
        grid.get("num_games", DEFAULT_OPTIMIZATION_GRID["num_games"]),
        grid.get("max_intersection", DEFAULT_OPTIMIZATION_GRID["max_intersection"]),
    ):
        combinations.append(
            {
                "window": int(window),
                "num_games": int(num_games),
                "max_intersection": int(max_intersection),
            }
        )
    return combinations


def rank_key(candidate: dict) -> tuple[float, float, float, float]:
    summary = candidate["summary"]
    return (
        float(summary["avg_score"]),
        float(summary["rate_ge4"]),
        float(summary["avg_max_hits"]),
        -float(summary["max_intersection"]),
    )


def run_optimization(results_df: pd.DataFrame, config: dict) -> dict:
    params = get_parameters(config)
    ticket_size = int(params.get("ticket_size", DEFAULT_TICKET_SIZE))
    min_history = int(params.get("min_history", DEFAULT_MIN_HISTORY))
    backtest_n_sim = int(params.get("backtest_n_sim", DEFAULT_BACKTEST_N_SIM))
    current_window = int(params.get("window", min_history))
    current_num_games = int(params.get("num_games", DEFAULT_NUM_GAMES))
    current_max_intersection = int(params.get("max_intersection", 3))

    combinations = build_grid(config)
    probability_cache = build_probability_cache(
        results_df,
        windows=[int(item["window"]) for item in combinations] + [current_window],
        min_history=min_history,
        config=config,
    )
    structural_rules = get_structural_rules(config)
    weak_pair_cache = build_weak_pair_cache(
        results_df,
        min_history=min_history,
        bottom_pairs=int(structural_rules["bottom_pairs"]),
    )

    candidates = []
    current_summary = None
    for combination in combinations:
        window = int(combination["window"])
        summary_report = run_backtest(
            results_df,
            window=window,
            min_history=max(min_history, window),
            n_games=int(combination.get("num_games", DEFAULT_NUM_GAMES)),
            ticket_size=ticket_size,
            n_sim=backtest_n_sim,
            max_intersection=int(combination["max_intersection"]),
            config=config,
            probability_cache=probability_cache.get(window),
            include_per_draw=False,
            weak_pair_cache=weak_pair_cache,
        )
        summary = summary_report["summary"]
        candidate = {
            "parameters": {
                "window": window,
                "num_games": int(combination["num_games"]),
                "ticket_size": ticket_size,
                "max_intersection": int(combination["max_intersection"]),
                "backtest_n_sim": backtest_n_sim,
            },
            "summary": summary,
        }
        candidates.append(candidate)

        if (
            window == current_window
            and int(combination["num_games"]) == current_num_games
            and int(combination["max_intersection"]) == current_max_intersection
        ):
            current_summary = summary

    candidates.sort(key=rank_key, reverse=True)
    best = candidates[0]

    recommended_parameters = dict(params)
    recommended_parameters.update(best["parameters"])
    recommended_config = {
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "parameters": recommended_parameters,
    }
    if current_summary is None:
        current_report = run_backtest(
            results_df,
            window=current_window,
            min_history=max(min_history, current_window),
            n_games=current_num_games,
            ticket_size=ticket_size,
            n_sim=backtest_n_sim,
            max_intersection=current_max_intersection,
            config=config,
            probability_cache=probability_cache.get(current_window),
            include_per_draw=False,
            weak_pair_cache=weak_pair_cache,
        )
        current_summary = current_report["summary"]
    promotion_decision = evaluate_promotion_guard(
        current_summary,
        best["summary"],
        get_promotion_guard(config),
    )

    return {
        "strategy": {
            "strategy_name": config.get("strategy_name"),
            "model_version": config.get("model_version"),
            "base_config_hash": _config_hash(config),
        },
        "search": {
            "candidates_tested": len(candidates),
            "ranking_metric": [
                "avg_score",
                "rate_ge4",
                "avg_max_hits",
                "lower_max_intersection",
            ],
        },
        "best": {
            "parameters": best["parameters"],
            "summary": best["summary"],
            "recommended_config_hash": _config_hash(recommended_config),
        },
        "current": {
            "parameters": {
                "window": current_window,
                "num_games": current_num_games,
                "ticket_size": ticket_size,
                "max_intersection": current_max_intersection,
                "backtest_n_sim": backtest_n_sim,
            },
            "summary": current_summary,
        },
        "promotion_decision": promotion_decision,
        "recommended_config": recommended_config,
        "ranking": candidates,
    }


def main() -> None:
    config = load_config()
    results_df = pd.read_csv(RESULTS_PATH)
    report = run_optimization(results_df, config)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    with RECOMMENDED_CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(report["recommended_config"], f, indent=2, ensure_ascii=False)

    write_promotion_artifacts(
        base_config=config,
        recommended_config=report["recommended_config"],
        decision=report["promotion_decision"],
    )

    best = report["best"]
    tested = report["search"]["candidates_tested"]
    best_avg_score = best["summary"]["avg_score"]
    best_rate_ge4 = best["summary"]["rate_ge4"]
    print(
        "[OPTIMIZE] OK:",
        f"tested={tested}",
        f"best_avg_score={best_avg_score}",
        f"best_rate_ge4={best_rate_ge4}",
        f"should_promote={report['promotion_decision']['should_promote']}",
        f"recommended_config={RECOMMENDED_CONFIG_PATH}",
    )


if __name__ == "__main__":
    main()
