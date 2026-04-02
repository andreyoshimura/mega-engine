from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config import CONFIG_PROMOTION_LOG_PATH, PROMOTION_DECISION_PATH
from core.time_utils import utc_now_pair
from core.versioning import _config_hash


def evaluate_promotion_guard(
    current_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    guard: dict[str, Any],
) -> dict[str, Any]:
    current_score = float(current_summary.get("avg_score", 0.0))
    candidate_score = float(candidate_summary.get("avg_score", 0.0))
    current_ge4 = float(current_summary.get("rate_ge4", 0.0))
    candidate_ge4 = float(candidate_summary.get("rate_ge4", 0.0))
    current_max_hits = float(current_summary.get("avg_max_hits", 0.0))
    candidate_max_hits = float(candidate_summary.get("avg_max_hits", 0.0))

    score_ratio = candidate_score / current_score if current_score > 0 else None
    ge4_ratio = candidate_ge4 / current_ge4 if current_ge4 > 0 else None
    max_hits_ratio = candidate_max_hits / current_max_hits if current_max_hits > 0 else None

    reasons: list[str] = []
    promote = True

    if score_ratio is not None and score_ratio < float(guard["max_score_drop_ratio"]):
        promote = False
        reasons.append("score_regression_guard")
    if ge4_ratio is not None and ge4_ratio < float(guard["max_ge4_drop_ratio"]):
        promote = False
        reasons.append("ge4_regression_guard")
    if max_hits_ratio is not None and max_hits_ratio < float(guard["max_hits_drop_ratio"]):
        promote = False
        reasons.append("max_hits_regression_guard")

    score_improvement = candidate_score - current_score
    ge4_improvement = candidate_ge4 - current_ge4

    if score_improvement < float(guard["min_improvement_score"]) and ge4_improvement < float(guard["min_improvement_ge4"]):
        promote = False
        reasons.append("insufficient_improvement")

    decision = {
        "should_promote": promote,
        "reasons": reasons if reasons else ["promotion_guard_passed"],
        "current_summary": current_summary,
        "candidate_summary": candidate_summary,
        "ratios": {
            "score_ratio": round(score_ratio, 4) if score_ratio is not None else None,
            "ge4_ratio": round(ge4_ratio, 4) if ge4_ratio is not None else None,
            "max_hits_ratio": round(max_hits_ratio, 4) if max_hits_ratio is not None else None,
        },
        "improvements": {
            "avg_score": round(score_improvement, 4),
            "rate_ge4": round(ge4_improvement, 4),
            "avg_max_hits": round(candidate_max_hits - current_max_hits, 4),
        },
        "guard": guard,
    }
    return decision


def write_promotion_artifacts(
    *,
    base_config: dict[str, Any],
    recommended_config: dict[str, Any],
    decision: dict[str, Any],
    report_path: Path = PROMOTION_DECISION_PATH,
    log_path: Path = CONFIG_PROMOTION_LOG_PATH,
) -> None:
    payload = {
        **utc_now_pair("timestamp"),
        "base_config_hash": _config_hash(base_config),
        "recommended_config_hash": _config_hash(recommended_config),
        "strategy_name": base_config.get("strategy_name"),
        "model_version": base_config.get("model_version"),
        "decision": decision,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
