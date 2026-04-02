from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.compare_results import compute_hits
from core.config import OUT_HISTORY_DIR, OUT_GAMES_PATH, PERFORMANCE_LOG_PATH, REPO_ROOT

AUDIT_REPORT_PATH = REPO_ROOT / "out" / "performance_audit.json"
LEGACY_INFERRED_SHA = {
    2974: "2c6c1a9ced68d91abf3037666c36590ad0f07df5",
}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_git_sha(value: Any) -> str | None:
    sha = str(value).strip().lower() if value is not None else ""
    if len(sha) < 7 or len(sha) > 40:
        return None
    if any(ch not in "0123456789abcdef" for ch in sha):
        return None
    return sha


def _git_show_json(sha: str, rel_path: str) -> dict[str, Any]:
    raw = subprocess.check_output(["git", "show", f"{sha}:{rel_path}"], cwd=REPO_ROOT, text=True)
    return json.loads(raw)


def _event_games_to_compare_input(event: dict[str, Any]) -> list[tuple[str, list[int]]]:
    return [(g["id"], [int(n) for n in g["numbers"]]) for g in event.get("games", [])]


def _payload_games(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"id": g["id"], "numbers": [int(n) for n in g["numbers"]]} for g in payload.get("games", [])]


def _build_snapshot_payload(event: dict[str, Any], payload: dict[str, Any], sha: str | None) -> dict[str, Any]:
    out = dict(payload)
    metadata = dict(out.get("metadata", {}) if isinstance(out.get("metadata"), dict) else {})
    meta = dict(event.get("meta", {}) if isinstance(event.get("meta"), dict) else {})
    metadata.setdefault("strategy_name", meta.get("strategy") or "megasena_v1")
    metadata.setdefault("model_version", meta.get("model_version"))
    metadata.setdefault("generated_at_utc", meta.get("generated_at_utc"))
    metadata["target_concurso"] = int(event["concurso"])
    metadata["source_commit_sha"] = sha
    metadata["reconstructed_at_utc"] = datetime.now(timezone.utc).isoformat()
    out["metadata"] = metadata
    return out


def _draw_date_to_timestamp_utc(draw_date: str | None) -> str | None:
    if not draw_date:
        return None
    parsed = datetime.strptime(str(draw_date), "%d/%m/%Y")
    return parsed.replace(tzinfo=timezone.utc).isoformat()


def audit_and_repair() -> dict[str, Any]:
    entries = [json.loads(line) for line in PERFORMANCE_LOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    repaired_entries = []
    audit_rows = []
    OUT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    for event in entries:
        concurso = int(event["concurso"])
        meta = dict(event.get("meta", {}) if isinstance(event.get("meta"), dict) else {})
        sha = _normalize_git_sha(meta.get("git_sha")) or LEGACY_INFERRED_SHA.get(concurso)
        source = "log_only"
        payload = None

        if sha:
            try:
                payload = _git_show_json(sha, "out/jogos_gerados.json")
                source = "git_show"
            except subprocess.CalledProcessError:
                payload = None

        if payload is None:
            payload = {
                "game": event.get("game", "megasena"),
                "ticket_size": event.get("ticket_size", 9),
                "draw_size": 6,
                "n_games": event.get("n_games", len(event.get("games", []))),
                "objective": "maximize_hit_rate_ge4",
                "games": _payload_games({"games": event.get("games", [])}),
                "metadata": {},
            }
            source = "performance_log"

        snapshot_payload = _build_snapshot_payload(event, payload, sha)
        snapshot_path = OUT_HISTORY_DIR / f"jogos_concurso_{concurso}.json"
        snapshot_path.write_text(json.dumps(snapshot_payload, indent=2, ensure_ascii=False), encoding="utf-8")

        compare_input = [(g["id"], [int(n) for n in g["numbers"]]) for g in snapshot_payload["games"]]
        draw_set = {int(n) for n in event["dezenas_sorteadas"]}
        recomputed = compute_hits(draw_set, compare_input)
        summary = recomputed["summary"]

        existing_games = _payload_games({"games": event.get("games", [])})
        snapshot_games = snapshot_payload["games"]
        games_match_snapshot = existing_games == snapshot_games

        repaired = dict(event)
        repaired_timestamp = _draw_date_to_timestamp_utc(event.get("data_sorteio"))
        if repaired_timestamp:
            repaired["timestamp_utc"] = repaired_timestamp
        repaired["ticket_size"] = int(snapshot_payload.get("ticket_size", event.get("ticket_size", 9)))
        repaired["n_games"] = len(snapshot_games)
        repaired["games"] = recomputed["per_game"]
        repaired.update(summary)

        repaired_meta = dict(meta)
        if sha:
            repaired_meta["git_sha"] = sha
        else:
            repaired_meta["git_sha"] = None
        repaired_meta.setdefault("strategy", snapshot_payload["metadata"].get("strategy_name") or "megasena_v1")
        repaired_meta["model_version"] = snapshot_payload["metadata"].get("model_version")
        repaired_meta["generated_at_utc"] = snapshot_payload["metadata"].get("generated_at_utc")
        repaired_meta["target_concurso"] = snapshot_payload["metadata"].get("target_concurso")
        repaired_meta["snapshot_source"] = source
        repaired_meta["snapshot_path"] = str(snapshot_path.relative_to(REPO_ROOT))
        repaired_meta.setdefault("logged_at_utc", event.get("meta", {}).get("logged_at_utc") if isinstance(event.get("meta"), dict) else None)
        if repaired_meta.get("logged_at_utc") is None:
            repaired_meta["logged_at_utc"] = event.get("timestamp_utc")
        repaired["meta"] = repaired_meta

        repaired_entries.append(repaired)
        audit_rows.append(
            {
                "concurso": concurso,
                "data_sorteio": event.get("data_sorteio"),
                "git_sha": sha,
                "snapshot_source": source,
                "games_match_snapshot": games_match_snapshot,
                "max_hits": repaired["max_hits"],
                "score": repaired["score"],
                "snapshot_path": str(snapshot_path.relative_to(REPO_ROOT)),
            }
        )

    PERFORMANCE_LOG_PATH.write_text(
        "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in repaired_entries),
        encoding="utf-8",
    )

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "entries_audited": len(audit_rows),
        "all_entries_match_snapshots": all(row["games_match_snapshot"] for row in audit_rows),
        "rows": audit_rows,
    }
    AUDIT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    report = audit_and_repair()
    print("[AUDIT] OK:", f"entries={report['entries_audited']}", f"all_match={report['all_entries_match_snapshots']}")
