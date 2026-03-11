import json
from itertools import product
from pathlib import Path

import pandas as pd

from core.backtest import (
    DEFAULT_BACKTEST_N_SIM,
    DEFAULT_MIN_HISTORY,
    RESULTS_PATH,
    run_backtest,
)
from core.generator import TICKET_SIZE
from core.versioning import _config_hash


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "strategy_config.json"
OUT_PATH = REPO_ROOT / "out" / "optimization_report.json"
RECOMMENDED_CONFIG_PATH = REPO_ROOT / "out" / "recommended_strategy_config.json"

DEFAULT_GRID = {
    "window": [50, 100, 150],
    "num_games": [4, 5, 6],
    "max_intersection": [3, 4, 5],
}


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_grid(params: dict) -> list[dict]:
    grid = params.get("optimization_grid", {})
    windows = grid.get("window", DEFAULT_GRID["window"])
    num_games_options = grid.get("num_games", DEFAULT_GRID["num_games"])
    max_intersections = grid.get(
        "max_intersection",
        DEFAULT_GRID["max_intersection"],
    )

    combinations = []
    for window, num_games, max_intersection in product(
        windows,
        num_games_options,
        max_intersections,
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
    params = config.get("parameters", {})
    ticket_size = int(params.get("ticket_size", TICKET_SIZE))
    min_history = int(params.get("min_history", DEFAULT_MIN_HISTORY))
    backtest_n_sim = int(params.get("backtest_n_sim", DEFAULT_BACKTEST_N_SIM))

    candidates = []

    for combination in build_grid(params):
        window = int(combination["window"])
        summary_report = run_backtest(
            results_df,
            window=window,
            min_history=max(min_history, window),
            n_games=int(combination["num_games"]),
            ticket_size=ticket_size,
            n_sim=backtest_n_sim,
            max_intersection=int(combination["max_intersection"]),
        )

        summary = summary_report["summary"]
        candidates.append(
            {
                "parameters": {
                    "window": window,
                    "num_games": int(combination["num_games"]),
                    "ticket_size": ticket_size,
                    "max_intersection": int(combination["max_intersection"]),
                    "backtest_n_sim": backtest_n_sim,
                },
                "summary": summary,
            }
        )

    candidates.sort(key=rank_key, reverse=True)

    best = candidates[0]
    recommended_parameters = dict(params)
    recommended_parameters.update(best["parameters"])

    recommended_config = {
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "parameters": recommended_parameters,
    }

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

    best = report["best"]
    print(
        "[OPTIMIZE] OK:",
        f"tested={report['search']['candidates_tested']}",
        f"best_avg_score={best['summary']['avg_score']}",
        f"best_rate_ge4={best['summary']['rate_ge4']}",
        f"params={best['parameters']}",
        f"recommended_config={RECOMMENDED_CONFIG_PATH}",
    )


if __name__ == "__main__":
    main()
