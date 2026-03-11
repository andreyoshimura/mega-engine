import json
from pathlib import Path

import pandas as pd

from core.compare_results import compute_hits
from core.generator import (
    DRAW_SIZE,
    MAX_INTERSECTION,
    N_GAMES,
    N_SIM,
    TICKET_SIZE,
    build_probabilities_from_history,
    generate_games_from_probs,
)
from core.versioning import _config_hash


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = REPO_ROOT / "data" / "results" / "megasena.csv"
CONFIG_PATH = REPO_ROOT / "configs" / "strategy_config.json"
OUT_PATH = REPO_ROOT / "out" / "backtest_report.json"

DEFAULT_WINDOW = 100
DEFAULT_MIN_HISTORY = 100
DEFAULT_BACKTEST_N_SIM = 20


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_backtest(
    results_df: pd.DataFrame,
    *,
    window: int = DEFAULT_WINDOW,
    min_history: int = DEFAULT_MIN_HISTORY,
    n_games: int = N_GAMES,
    ticket_size: int = TICKET_SIZE,
    n_sim: int = N_SIM,
    max_intersection: int = MAX_INTERSECTION,
    seed_base: int = 10_000,
) -> dict:
    if len(results_df) <= min_history:
        raise ValueError("Histórico insuficiente para backtest.")

    per_draw = []

    for idx in range(min_history, len(results_df)):
        history = results_df.iloc[:idx].copy()
        target = results_df.iloc[idx]

        probs = build_probabilities_from_history(history, window=window)
        games = generate_games_from_probs(
            probs,
            seed=seed_base + idx,
            n_games=n_games,
            ticket_size=ticket_size,
            n_sim=n_sim,
            max_intersection=max_intersection,
        )

        draw_numbers = [int(target[f"d{i}"]) for i in range(1, DRAW_SIZE + 1)]
        compare_input = [
            (f"J{str(i + 1).zfill(2)}", game)
            for i, game in enumerate(games)
        ]
        result = compute_hits(set(draw_numbers), compare_input)

        per_draw.append(
            {
                "concurso": int(target["concurso"]),
                "data": str(target["data"]),
                "dezenas_sorteadas": draw_numbers,
                **result["summary"],
                "games": result["per_game"],
            }
        )

    total_draws = len(per_draw)
    avg_max_hits = sum(item["max_hits"] for item in per_draw) / total_draws
    avg_score = sum(item["score"] for item in per_draw) / total_draws
    rate_ge4 = sum(1 for item in per_draw if item["count_ge4"] > 0) / total_draws
    rate_ge5 = sum(1 for item in per_draw if item["count_ge5"] > 0) / total_draws
    total_eq6 = sum(item["count_eq6"] for item in per_draw)

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
        },
        "per_draw": per_draw,
    }


def main() -> None:
    config = load_config()
    params = config.get("parameters", {})

    results_df = pd.read_csv(RESULTS_PATH)
    window = int(params.get("window", DEFAULT_WINDOW))
    min_history = max(int(params.get("min_history", DEFAULT_MIN_HISTORY)), window)
    n_games = int(params.get("num_games", N_GAMES))
    ticket_size = int(params.get("ticket_size", TICKET_SIZE))
    n_sim = int(params.get("backtest_n_sim", min(params.get("n_sim", N_SIM), DEFAULT_BACKTEST_N_SIM)))
    max_intersection = int(params.get("max_intersection", MAX_INTERSECTION))

    report = run_backtest(
        results_df,
        window=window,
        min_history=min_history,
        n_games=n_games,
        ticket_size=ticket_size,
        n_sim=n_sim,
        max_intersection=max_intersection,
    )

    report["strategy"] = {
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "config_hash": _config_hash(config),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(
        "[BACKTEST] OK:",
        f"draws={report['summary']['draws_evaluated']}",
        f"avg_max_hits={report['summary']['avg_max_hits']}",
        f"rate_ge4={report['summary']['rate_ge4']}",
    )


if __name__ == "__main__":
    main()
