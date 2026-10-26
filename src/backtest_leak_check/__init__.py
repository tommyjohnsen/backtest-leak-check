# PROVENANCE (mirror of .provenance/ledger.jsonl; ledger wins)
# written-by: unknown (pre-provenance) | 2026-10-13 | e10f0e8
# modified-by: codex/gpt-5.6-sol | 2026-10-26 | f566a55 | provenance block added
# reviewed-by: claude-code/claude-opus-5-5 | 2026-10-26 | APPROVE
# END PROVENANCE
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
