from __future__ import annotations

import json

from core.config import (
    MONITOR_REPORT_PATH,
    PERFORMANCE_LOG_PATH,
    RECALIBRATION_SIGNAL_PATH,
    get_monitoring,
    load_config,
)


def load_events() -> list[dict]:
    if not PERFORMANCE_LOG_PATH.exists():
        return []

    events = []
    with PERFORMANCE_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if is_canonical_event(event):
                events.append(event)

    events.sort(key=lambda event: int(event.get("concurso", 0)))
    return events


def is_canonical_event(event: dict) -> bool:
    if int(event.get("n_games", 0)) <= 0:
        return False

    meta = event.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}

    if bool(meta.get("manual_patch")):
        return False

    if str(meta.get("snapshot_source", "")).strip() == "manual_patch_noncanonical":
        return False

    return True


def summarize_window(events: list[dict]) -> dict:
    draws = len(events)
    if draws == 0:
        return {
            "draws": 0,
            "avg_score": 0.0,
            "avg_max_hits": 0.0,
            "rate_ge4": 0.0,
            "rate_ge5": 0.0,
        }

    avg_score = sum(float(e.get("score", 0)) for e in events) / draws
    avg_max_hits = sum(float(e.get("max_hits", 0)) for e in events) / draws
    rate_ge4 = sum(1 for e in events if int(e.get("count_ge4", 0)) > 0) / draws
    rate_ge5 = sum(1 for e in events if int(e.get("count_ge5", 0)) > 0) / draws

    return {
        "draws": draws,
        "avg_score": round(avg_score, 4),
        "avg_max_hits": round(avg_max_hits, 4),
        "rate_ge4": round(rate_ge4, 4),
        "rate_ge5": round(rate_ge5, 4),
    }


def evaluate_recalibration(recent: dict, baseline: dict, monitoring: dict) -> dict:
    reasons = []

    baseline_score = float(baseline["avg_score"])
    baseline_max_hits = float(baseline["avg_max_hits"])
    baseline_rate_ge4 = float(baseline["rate_ge4"])

    recent_score = float(recent["avg_score"])
    recent_max_hits = float(recent["avg_max_hits"])
    recent_rate_ge4 = float(recent["rate_ge4"])

    score_ratio = None
    max_hits_ratio = None
    ge4_ratio = None

    if baseline_score > 0:
        score_ratio = recent_score / baseline_score
        if score_ratio < float(monitoring["score_drop_ratio"]):
            reasons.append("score_drop")

    if baseline_max_hits > 0:
        max_hits_ratio = recent_max_hits / baseline_max_hits
        if max_hits_ratio < float(monitoring["max_hits_drop_ratio"]):
            reasons.append("max_hits_drop")

    if baseline_rate_ge4 > 0:
        ge4_ratio = recent_rate_ge4 / baseline_rate_ge4
        if ge4_ratio < float(monitoring["ge4_drop_ratio"]):
            reasons.append("ge4_drop")

    return {
        "should_recalibrate": bool(reasons),
        "reasons": reasons,
        "ratios": {
            "score_ratio": round(score_ratio, 4) if score_ratio is not None else None,
            "max_hits_ratio": round(max_hits_ratio, 4) if max_hits_ratio is not None else None,
            "ge4_ratio": round(ge4_ratio, 4) if ge4_ratio is not None else None,
        },
    }


def build_monitor_report(config: dict, events: list[dict]) -> dict:
    monitoring = get_monitoring(config)
    total_events = len(events)
    min_draws_required = int(monitoring["min_draws_required"])
    recent_window = int(monitoring["recent_window"])
    baseline_window = int(monitoring["baseline_window"])

    if total_events < min_draws_required:
        return {
            "status": "insufficient_history",
            "strategy_name": config.get("strategy_name"),
            "model_version": config.get("model_version"),
            "total_events": total_events,
            "latest_concurso": events[-1].get("concurso") if events else None,
            "monitoring": monitoring,
            "decision": {
                "should_recalibrate": False,
                "reasons": ["insufficient_history"],
                "ratios": {
                    "score_ratio": None,
                    "max_hits_ratio": None,
                    "ge4_ratio": None,
                },
            },
        }

    recent_events = events[-recent_window:]
    baseline_events = events[-(baseline_window + recent_window):-recent_window]
    if not baseline_events:
        baseline_events = events[:-recent_window]

    recent_summary = summarize_window(recent_events)
    baseline_summary = summarize_window(baseline_events)
    decision = evaluate_recalibration(recent_summary, baseline_summary, monitoring)

    latest = events[-1]
    return {
        "status": "ok",
        "strategy_name": config.get("strategy_name"),
        "model_version": config.get("model_version"),
        "total_events": total_events,
        "latest_concurso": latest.get("concurso"),
        "monitoring": monitoring,
        "recent_window": recent_summary,
        "baseline_window": baseline_summary,
        "decision": decision,
    }


def main() -> None:
    config = load_config()
    events = load_events()
    report = build_monitor_report(config, events)

    MONITOR_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MONITOR_REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    signal = {
        "should_recalibrate": report["decision"]["should_recalibrate"],
        "reasons": report["decision"]["reasons"],
        "latest_concurso": report.get("latest_concurso"),
        "strategy_name": report.get("strategy_name"),
        "model_version": report.get("model_version"),
    }

    with RECALIBRATION_SIGNAL_PATH.open("w", encoding="utf-8") as f:
        json.dump(signal, f, indent=2, ensure_ascii=False)

    status = report["status"]
    should_recalibrate = signal["should_recalibrate"]
    reasons = signal["reasons"]
    print("[MONITOR] OK:", f"status={status}", f"should_recalibrate={should_recalibrate}", f"reasons={reasons}")


if __name__ == "__main__":
    main()
