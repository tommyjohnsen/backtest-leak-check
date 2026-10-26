# PROVENANCE (mirror of .provenance/ledger.jsonl; ledger wins)
# written-by: unknown (pre-provenance) | 2026-10-13 | e10f0e8
# modified-by: codex/gpt-5.6-sol | 2026-10-26 | f566a55 | provenance block added
# reviewed-by: claude-code/claude-opus-5-5 | 2026-10-26 | APPROVE
# END PROVENANCE
"""CLI for static bar-availability checks."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from .checks import check_availability
from .csvio import read_bars, read_uses


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="backtest-leak-check")
    parser.add_argument("--bars", required=True, help="CSV containing OHLCV bars")
    parser.add_argument("--uses", required=True, help="CSV recording bars consumed by decisions")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)
    try:
        report = check_availability(read_bars(args.bars), read_uses(args.uses))
    except (OSError, KeyError, ValueError, TypeError) as error:
        parser.exit(2, f"input error: {error}\n")
    payload = {
        "status": "PASS" if report.ok else "FAIL",
        "checked_uses": report.checked_uses,
        "errors": [{"decision_id": item.decision_id, "message": item.message} for item in report.errors],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"{payload['status']}: checked {report.checked_uses} bar uses")
        for item in report.errors:
            print(f"- {item.decision_id}: {item.message}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
