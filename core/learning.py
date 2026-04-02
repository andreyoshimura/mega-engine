from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from core.config import (
    LEARNING_DECISION_PATH,
    LEARNING_LOG_PATH,
    MONITOR_REPORT_PATH,
    NEXT_STRATEGY_CONFIG_PATH,
    PROMOTION_DECISION_PATH,
    RECOMMENDED_CONFIG_PATH,
    get_learning,
    load_config,
)
from core.time_utils import utc_now_pair
from core.versioning import _config_hash, register_strategy


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _blend_value(current: float, target: float, ratio: float) -> float:
    return current + ((target - current) * ratio)


def build_incremental_config(
    current_config: dict[str, Any],
    recommended_config: dict[str, Any],
    learning: dict[str, Any],
) -> dict[str, Any]:
    promoted = deepcopy(current_config)
    current_params = promoted.setdefault("parameters", {})
    target_params = recommended_config.get("parameters", {})

    current_weights = dict(current_params.get("feature_weights", {}))
    target_weights = dict(target_params.get("feature_weights", current_weights))
    weight_ratio = float(learning["feature_weight_step_ratio"])
    for key in sorted(set(current_weights) | set(target_weights)):
        current_value = float(current_weights.get(key, 0.0))
        target_value = float(target_weights.get(key, current_value))
        current_weights[key] = round(_blend_value(current_value, target_value, weight_ratio), 6)
    current_params["feature_weights"] = current_weights

    current_bayes = dict(current_params.get("bayesian", {}))
    target_bayes = dict(target_params.get("bayesian", current_bayes))
    bayes_ratio = float(learning["bayesian_step_ratio"])
    for key in sorted(set(current_bayes) | set(target_bayes)):
        current_value = float(current_bayes.get(key, 0.0))
        target_value = float(target_bayes.get(key, current_value))
        current_bayes[key] = round(_blend_value(current_value, target_value, bayes_ratio), 6)
    current_params["bayesian"] = current_bayes

    if bool(learning.get("allow_parameter_promotion", True)):
        for key in ("window", "num_games", "max_intersection", "backtest_n_sim"):
            if key in target_params:
                current_params[key] = target_params[key]

    promoted["notes"] = "incremental_learning_promotion"
    return promoted


def build_learning_decision(
    current_config: dict[str, Any],
    recommended_config: dict[str, Any] | None,
    promotion_decision: dict[str, Any] | None,
    monitor_report: dict[str, Any] | None,
) -> dict[str, Any]:
    learning = get_learning(current_config)
    should_recalibrate = bool((monitor_report or {}).get("decision", {}).get("should_recalibrate", False))
    should_promote = bool((promotion_decision or {}).get("decision", {}).get("should_promote", False))
    require_signal = bool(learning.get("require_recalibration_signal", True))
    current_hash = _config_hash(current_config)
    recommended_hash = _config_hash(recommended_config) if recommended_config is not None else None

    reasons: list[str] = []
    next_config = deepcopy(current_config)
    action = "hold_current"

    if recommended_config is None or promotion_decision is None:
        reasons.append("missing_recommendation_artifacts")
    elif recommended_hash == current_hash:
        reasons.append("no_effective_change")
    elif require_signal and not should_recalibrate:
        reasons.append("waiting_recalibration_signal")
    elif should_promote:
        next_config = build_incremental_config(current_config, recommended_config, learning)
        action = "promote_incremental"
        reasons.append("promotion_guard_passed")
        if should_recalibrate:
            reasons.append("recalibration_signal_active")
    else:
        action = "rollback_hold"
        reasons.extend((promotion_decision.get("decision", {}) or {}).get("reasons", []) or ["promotion_blocked"])
        if should_recalibrate:
            reasons.append("recalibration_signal_active")

    return {
        **utc_now_pair("timestamp"),
        "action": action,
        "reasons": reasons,
        "should_recalibrate": should_recalibrate,
        "should_promote": should_promote,
        "current_config_hash": current_hash,
        "next_config_hash": _config_hash(next_config),
        "current_config": current_config,
        "next_config": next_config,
        "recommended_config_hash": recommended_hash,
        "monitor_status": (monitor_report or {}).get("status"),
        "promotion_summary": (promotion_decision or {}).get("decision"),
    }


def write_learning_artifacts(
    decision: dict[str, Any],
    *,
    decision_path: Path = LEARNING_DECISION_PATH,
    next_config_path: Path = NEXT_STRATEGY_CONFIG_PATH,
    log_path: Path = LEARNING_LOG_PATH,
) -> None:
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(json.dumps(decision, indent=2, ensure_ascii=False), encoding="utf-8")

    next_config_path.parent.mkdir(parents=True, exist_ok=True)
    next_config_path.write_text(json.dumps(decision["next_config"], indent=2, ensure_ascii=False), encoding="utf-8")

    _append_jsonl(log_path, decision)


def main() -> None:
    current_config = load_config()
    recommended_config = _load_optional_json(RECOMMENDED_CONFIG_PATH)
    promotion_decision = _load_optional_json(PROMOTION_DECISION_PATH)
    monitor_report = _load_optional_json(MONITOR_REPORT_PATH)

    decision = build_learning_decision(
        current_config=current_config,
        recommended_config=recommended_config,
        promotion_decision=promotion_decision,
        monitor_report=monitor_report,
    )
    write_learning_artifacts(decision)

    if decision["action"] == "promote_incremental":
        register_strategy(decision["next_config"], execution_type="recalibration_candidate")

    print(
        "[LEARNING] OK:",
        f"action={decision['action']}",
        f"should_recalibrate={decision['should_recalibrate']}",
        f"should_promote={decision['should_promote']}",
    )


if __name__ == "__main__":
    main()
