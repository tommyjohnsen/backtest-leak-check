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
