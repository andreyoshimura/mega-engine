from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


def utc_now_pair(prefix: str) -> dict[str, str]:
    now = datetime.now(BRAZIL_TZ).astimezone(ZoneInfo("UTC"))
    return {
        f"{prefix}_utc": now.isoformat(),
        f"{prefix}_brt": now.astimezone(BRAZIL_TZ).strftime("%d/%m/%Y %H:%M:%S"),
    }


def iso_utc_to_brt_text(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(BRAZIL_TZ).strftime("%d/%m/%Y %H:%M:%S")
