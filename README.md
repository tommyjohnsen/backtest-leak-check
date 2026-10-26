<!--
PROVENANCE (mirror of .provenance/ledger.jsonl; ledger wins)
written-by: unknown (pre-provenance) | 2026-10-13 | e10f0e8
modified-by: codex/gpt-5.6-sol | 2026-10-26 | f566a55 | provenance block added
END PROVENANCE
-->
# backtest-leak-check

`backtest-leak-check` is a small Python library and CLI for detecting future-bar leakage in event-driven backtests. It is strategy-agnostic and has no network or data-provider dependency.

This software is not financial advice.

## What it checks

- Static availability: every bar recorded as an input to a decision must exist and must be fully closed at that decision time.
- Bar-open timestamps: an exchange kline timestamp is treated as its opening time. A `4h` bar opened at 08:00 is first available at 12:00.
- Higher timeframes: an unfinished higher-timeframe bar is never readable merely because its opening time is in the past.
- Truncation invariance: a callable can be run with full data and with future bars physically removed. Different outputs reveal future-data access.

## Install and run

```console
python -m pip install .
backtest-leak-check --bars bars.csv --uses uses.csv
```

The bars CSV columns are:

```text
symbol,timeframe,open_time,open,high,low,close,volume
```

The uses CSV columns are:

```text
decision_id,decision_time,symbol,timeframe,bar_open_time
```

Timestamps must be ISO 8601 values with an offset. Timeframes are fixed durations such as `30s`, `15m`, `1h`, `4h`, or `1d`. The command exits `0` when all uses are safe, `1` when it finds a temporal leak, and `2` for invalid input.

## Library example

```python
from datetime import datetime, timezone
from backtest_leak_check import Bar, BarUse, check_availability

utc = timezone.utc
opened = datetime(2024, 1, 2, 8, tzinfo=utc)
decided = datetime(2024, 1, 2, 12, tzinfo=utc)
bars = [Bar("XYZ", "4h", opened, 10, 12, 9, 11, 5)]
uses = [BarUse("decision-1", decided, "XYZ", "4h", opened)]
assert check_availability(bars, uses).ok
```

For dynamic checking, `run_truncation_test(runner, bars, cutoffs)` compares a run over the entire dataset with one where bars that had not closed are physically removed. When those outputs match despite unavailable bars being present, it also replaces future OHLCV values with canaries. This catches leaks masked by coincidentally equal values. A causal runner returns equivalent results.

## Limits

The static check can assess only the bar-use records supplied to it; it cannot detect an input that was consumed but never recorded. The dynamic check detects future access only when that access changes the normalized output under truncation or canary probing, so it does not prove that a backtest is leak-free. Timeframes are fixed durations and do not model calendar-based bars, exchange sessions, publication delays, or later data revisions.

## Development

```console
python -m pytest
```

All tests use generated, synthetic fixtures.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
