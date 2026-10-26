# PROVENANCE (mirror of .provenance/ledger.jsonl; ledger wins)
# written-by: unknown (pre-provenance) | 2026-10-13 | e10f0e8
# modified-by: codex/gpt-5.6-sol | 2026-10-26 | f566a55 | provenance block added
# reviewed-by: claude-code/claude-opus-5-5 | 2026-10-26 | APPROVE
# reviewed-by: grok-build/grok-4.7 | 2026-10-26 | APPROVE
# END PROVENANCE
"""CSV adapters for the command-line interface."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from .checks import Bar, BarUse


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def read_bars(path: str | Path) -> list[Bar]:
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return [Bar(
            row["symbol"], row["timeframe"], parse_timestamp(row["open_time"]),
            float(row["open"]), float(row["high"]), float(row["low"]),
            float(row["close"]), float(row.get("volume") or 0),
        ) for row in csv.DictReader(stream)]


def read_uses(path: str | Path) -> list[BarUse]:
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return [BarUse(
            row["decision_id"], parse_timestamp(row["decision_time"]),
            row["symbol"], row["timeframe"], parse_timestamp(row["bar_open_time"]),
        ) for row in csv.DictReader(stream)]
