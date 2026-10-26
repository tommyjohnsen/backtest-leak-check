# PROVENANCE (mirror of .provenance/ledger.jsonl; ledger wins)
# written-by: unknown (pre-provenance) | 2026-10-13 | e10f0e8
# modified-by: codex/gpt-5.6-sol | 2026-10-26 | f566a55 | provenance block added
# END PROVENANCE
"""Temporal availability and truncation checks for OHLCV backtests."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from typing import Generic, TypeVar

UTC = timezone.utc
Output = TypeVar("Output")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC)


def parse_timeframe(value: str) -> timedelta:
    """Parse a fixed-duration timeframe such as 30s, 15m, 4h, or 1d."""
    match = re.fullmatch(r"([1-9][0-9]*)([smhd])", value.strip().lower())
    if match is None:
        raise ValueError(f"unsupported timeframe: {value!r}")
    count = int(match.group(1))
    unit = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}[match.group(2)]
    return timedelta(**{unit: count})


@dataclass(frozen=True, slots=True)
class Bar:
    """A fixed-duration bar identified by its opening timestamp.

    Exchange kline timestamps commonly identify when the bar opened, not when
    its final OHLCV values became knowable. ``close_time`` accounts for that.
    """

    symbol: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", self.symbol.upper())
        object.__setattr__(self, "timeframe", self.timeframe.lower())
        object.__setattr__(self, "open_time", _utc(self.open_time))
        parse_timeframe(self.timeframe)
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("bar high is inconsistent with OHLC values")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("bar low is inconsistent with OHLC values")

    @property
    def close_time(self) -> datetime:
        return self.open_time + parse_timeframe(self.timeframe)

    @property
    def key(self) -> tuple[str, str, datetime]:
        return self.symbol, self.timeframe, self.open_time


@dataclass(frozen=True, slots=True)
class BarUse:
    """A claim that a decision consumed a particular bar."""

    decision_id: str
    decision_time: datetime
    symbol: str
    timeframe: str
    bar_open_time: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_time", _utc(self.decision_time))
        object.__setattr__(self, "bar_open_time", _utc(self.bar_open_time))
        object.__setattr__(self, "symbol", self.symbol.upper())
        object.__setattr__(self, "timeframe", self.timeframe.lower())
        parse_timeframe(self.timeframe)


@dataclass(frozen=True, slots=True)
class AvailabilityError:
    decision_id: str
    message: str


@dataclass(frozen=True, slots=True)
class LeakReport:
    checked_uses: int
    errors: tuple[AvailabilityError, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _bar_index(bars: Iterable[Bar]) -> dict[tuple[str, str, datetime], Bar]:
    result: dict[tuple[str, str, datetime], Bar] = {}
    for bar in bars:
        previous = result.get(bar.key)
        if previous is not None and previous != bar:
            raise ValueError(f"conflicting duplicate bar: {bar.key!r}")
        result[bar.key] = bar
    return result


def check_availability(bars: Iterable[Bar], uses: Iterable[BarUse]) -> LeakReport:
    """Statically verify that every referenced bar existed and had closed.

    This applies identically to every timeframe. In particular, a partially
    formed higher-timeframe bar is unavailable even if its opening timestamp is
    earlier than the decision timestamp.
    """
    index = _bar_index(bars)
    errors: list[AvailabilityError] = []
    count = 0
    for use in uses:
        count += 1
        key = (use.symbol, use.timeframe, use.bar_open_time)
        bar = index.get(key)
        if bar is None:
            errors.append(AvailabilityError(use.decision_id, f"referenced bar does not exist: {key!r}"))
        elif bar.close_time > use.decision_time:
            errors.append(AvailabilityError(
                use.decision_id,
                f"bar closes at {bar.close_time.isoformat()} after decision at {use.decision_time.isoformat()}",
            ))
    return LeakReport(count, tuple(errors))


def available_bars(bars: Iterable[Bar], as_of: datetime) -> tuple[Bar, ...]:
    """Return only bars whose full interval had completed by ``as_of``."""
    cutoff = _utc(as_of)
    return tuple(sorted((bar for bar in bars if bar.close_time <= cutoff), key=lambda bar: bar.key))


def _probe_future_values(bars: Sequence[Bar], cutoff: datetime) -> tuple[Bar, ...]:
    """Replace unavailable values with conspicuous, internally valid canaries."""
    probed: list[Bar] = []
    for index, bar in enumerate(bars):
        if bar.close_time <= cutoff:
            probed.append(bar)
            continue
        delta = float(1_000_003 * (index + 1))
        probed.append(Bar(
            bar.symbol,
            bar.timeframe,
            bar.open_time,
            bar.open + delta,
            bar.high + delta,
            bar.low + delta,
            bar.close + delta,
            bar.volume + delta,
        ))
    return tuple(probed)


@dataclass(frozen=True, slots=True)
class TruncationFailure(Generic[Output]):
    cutoff: datetime
    baseline: Output
    truncated: Output


def run_truncation_test(
    runner: Callable[[Sequence[Bar], datetime], Output],
    bars: Iterable[Bar],
    cutoffs: Iterable[datetime],
    *,
    normalize: Callable[[Output], object] | None = None,
) -> tuple[TruncationFailure[Output], ...]:
    """Detect a runner whose result changes when future bars are removed.

    For each cutoff, ``runner`` is called with the complete dataset and with
    only bars completed by that cutoff. If those outputs happen to be equal,
    unavailable OHLCV values are replaced with canaries for one additional
    call. This catches future reads even when future and available bars contain
    coincidentally equal values. ``normalize`` can discard nondeterministic
    metadata before comparison.
    """
    complete = tuple(bars)
    compare = normalize or (lambda value: value)
    failures: list[TruncationFailure[Output]] = []
    for raw_cutoff in cutoffs:
        cutoff = _utc(raw_cutoff)
        baseline = runner(complete, cutoff)
        available = available_bars(complete, cutoff)
        truncated = runner(available, cutoff)
        if compare(baseline) != compare(truncated):
            failures.append(TruncationFailure(cutoff, baseline, truncated))
        elif len(available) != len(complete):
            probed = runner(_probe_future_values(complete, cutoff), cutoff)
            if compare(probed) != compare(truncated):
                failures.append(TruncationFailure(cutoff, probed, truncated))
    return tuple(failures)
