"""Public API for checking temporal integrity in bar-based backtests."""

from .checks import (
    AvailabilityError,
    Bar,
    BarUse,
    LeakReport,
    TruncationFailure,
    available_bars,
    check_availability,
    parse_timeframe,
    run_truncation_test,
)

__all__ = [
    "AvailabilityError",
    "Bar",
    "BarUse",
    "LeakReport",
    "TruncationFailure",
    "available_bars",
    "check_availability",
    "parse_timeframe",
    "run_truncation_test",
]
