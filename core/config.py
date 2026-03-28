from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = REPO_ROOT / "configs" / "strategy_config.json"
RESULTS_PATH = REPO_ROOT / "data" / "results" / "megasena.csv"
FEATURES_PATH = REPO_ROOT / "data" / "features" / "dezenas.csv"
LAST_RESULT_PATH = REPO_ROOT / "data" / "last_result.json"
MODEL_HISTORY_PATH = REPO_ROOT / "data" / "model_history.jsonl"
CONFIG_PROMOTION_LOG_PATH = REPO_ROOT / "data" / "config_promotion_log.jsonl"
LEARNING_LOG_PATH = REPO_ROOT / "data" / "learning_log.jsonl"
PERFORMANCE_LOG_PATH = REPO_ROOT / "data" / "performance_log.jsonl"
OUT_GAMES_PATH = REPO_ROOT / "out" / "jogos_gerados.json"
OUT_HISTORY_DIR = REPO_ROOT / "out" / "history"
BACKTEST_REPORT_PATH = REPO_ROOT / "out" / "backtest_report.json"
OPTIMIZATION_REPORT_PATH = REPO_ROOT / "out" / "optimization_report.json"
RECOMMENDED_CONFIG_PATH = REPO_ROOT / "out" / "recommended_strategy_config.json"
PROMOTION_DECISION_PATH = REPO_ROOT / "out" / "config_promotion_decision.json"
LEARNING_DECISION_PATH = REPO_ROOT / "out" / "learning_decision.json"
NEXT_STRATEGY_CONFIG_PATH = REPO_ROOT / "out" / "next_strategy_config.json"
MONITOR_REPORT_PATH = REPO_ROOT / "out" / "performance_monitor.json"
RECALIBRATION_SIGNAL_PATH = REPO_ROOT / "out" / "recalibration_signal.json"
IMAGE_OUTPUT_DIR = REPO_ROOT / "out" / "images"

GAME_NAME = "megasena"
MIN_NUMBER = 1
MAX_NUMBER = 60
DEFAULT_DRAW_SIZE = 6
DEFAULT_TICKET_SIZE = 9
DEFAULT_NUM_GAMES = 5
DEFAULT_WINDOW = 100
DEFAULT_N_SIM = 5000
DEFAULT_MAX_INTERSECTION = 4
DEFAULT_MIN_HISTORY = 100
DEFAULT_BACKTEST_N_SIM = 20
DEFAULT_BAYESIAN = {
    "alpha_prior": 1.0,
    "beta_prior": 9.0,
}
DEFAULT_FEATURE_WEIGHTS = {
    "freq_100": 1.0,
    "bayes_mean": 1.0,
    "bayes_score": 0.0,
}
DEFAULT_PROMOTION_GUARD = {
    "min_improvement_score": 0.0,
    "min_improvement_ge4": 0.0,
    "max_score_drop_ratio": 0.95,
    "max_ge4_drop_ratio": 0.95,
    "max_hits_drop_ratio": 0.98,
}
DEFAULT_LEARNING = {
    "feature_weight_step_ratio": 0.25,
    "bayesian_step_ratio": 0.2,
    "allow_parameter_promotion": True,
    "require_recalibration_signal": True,
}

DEFAULT_MONITORING = {
    "recent_window": 5,
    "baseline_window": 20,
    "min_draws_required": 12,
    "score_drop_ratio": 0.5,
    "max_hits_drop_ratio": 0.85,
    "ge4_drop_ratio": 0.5,
}

DEFAULT_OPTIMIZATION_GRID = {
    "window": [50, 100, 150],
    "num_games": [4, 5, 6],
    "max_intersection": [3, 4, 5],
}


def load_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_parameters(config: dict[str, Any]) -> dict[str, Any]:
    return dict(config.get("parameters", {}))


def get_ticket_size(config: dict[str, Any]) -> int:
    return int(get_parameters(config).get("ticket_size", DEFAULT_TICKET_SIZE))


def get_num_games(config: dict[str, Any]) -> int:
    return int(get_parameters(config).get("num_games", DEFAULT_NUM_GAMES))


def get_draw_size(config: dict[str, Any]) -> int:
    return int(get_parameters(config).get("draw_size", DEFAULT_DRAW_SIZE))


def get_window(config: dict[str, Any]) -> int:
    return int(get_parameters(config).get("window", DEFAULT_WINDOW))


def get_max_intersection(config: dict[str, Any]) -> int:
    return int(get_parameters(config).get("max_intersection", DEFAULT_MAX_INTERSECTION))


def get_monitoring(config: dict[str, Any]) -> dict[str, Any]:
    monitoring = dict(DEFAULT_MONITORING)
    monitoring.update(get_parameters(config).get("monitoring", {}))
    return monitoring


def get_bayesian(config: dict[str, Any]) -> dict[str, Any]:
    bayesian = dict(DEFAULT_BAYESIAN)
    bayesian.update(get_parameters(config).get("bayesian", {}))
    return bayesian


def get_feature_weights(config: dict[str, Any]) -> dict[str, Any]:
    weights = dict(DEFAULT_FEATURE_WEIGHTS)
    weights.update(get_parameters(config).get("feature_weights", {}))
    return weights


def get_promotion_guard(config: dict[str, Any]) -> dict[str, Any]:
    guard = dict(DEFAULT_PROMOTION_GUARD)
    guard.update(get_parameters(config).get("promotion_guard", {}))
    return guard


def get_learning(config: dict[str, Any]) -> dict[str, Any]:
    learning = dict(DEFAULT_LEARNING)
    learning.update(get_parameters(config).get("learning", {}))
    return learning


def get_optimization_grid(config: dict[str, Any]) -> dict[str, Any]:
    grid = dict(DEFAULT_OPTIMIZATION_GRID)
    grid.update(get_parameters(config).get("optimization_grid", {}))
    return grid
