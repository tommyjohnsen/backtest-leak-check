from datetime import datetime, timezone

import pytest

from backtest_leak_check import (
    Bar,
    BarUse,
    available_bars,
    check_availability,
    parse_timeframe,
    run_truncation_test,
)

UTC = timezone.utc


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 2, hour, minute, tzinfo=UTC)


def bar(hour: int, timeframe: str = "1h") -> Bar:
    return Bar("XYZ", timeframe, at(hour), 10, 12, 9, 11, 5)


@pytest.mark.parametrize(("value", "seconds"), [("30s", 30), ("15m", 900), ("4h", 14400), ("1d", 86400)])
def test_parse_timeframe(value, seconds):
    assert parse_timeframe(value).total_seconds() == seconds


@pytest.mark.parametrize("value", ["0h", "H1", "hour", "1w", "-1h"])
def test_rejects_unsupported_timeframe(value):
    with pytest.raises(ValueError):
        parse_timeframe(value)


def test_open_timestamp_becomes_available_at_close():
    item = bar(8, "4h")
    assert item.close_time == at(12)
    assert not available_bars([item], at(11, 59))
    assert available_bars([item], at(12)) == (item,)


def test_static_check_accepts_completed_bar():
    item = bar(8, "4h")
    report = check_availability([item], [BarUse("d1", at(12), "xyz", "4h", at(8))])
    assert report.ok
    assert report.checked_uses == 1


def test_static_check_rejects_unfinished_higher_timeframe_bar():
    item = bar(8, "4h")
    report = check_availability([item], [BarUse("d1", at(10), "XYZ", "4h", at(8))])
    assert not report.ok
    assert "closes at" in report.errors[0].message


def test_static_check_rejects_unknown_bar():
    report = check_availability([], [BarUse("d1", at(10), "XYZ", "1h", at(8))])
    assert not report.ok
    assert "does not exist" in report.errors[0].message


def test_conflicting_duplicate_bar_is_rejected():
    first = bar(8)
    second = Bar("XYZ", "1h", at(8), 10, 13, 9, 12, 5)
    with pytest.raises(ValueError, match="conflicting duplicate"):
        check_availability([first, second], [])


def test_naive_timestamps_are_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        Bar("XYZ", "1h", datetime(2024, 1, 2), 1, 2, 0, 1)


def test_inconsistent_ohlc_is_rejected():
    with pytest.raises(ValueError, match="high"):
        Bar("XYZ", "1h", at(1), 10, 9, 8, 10)


def test_truncation_test_accepts_causal_runner():
    bars = [bar(8), bar(9), bar(10)]

    def causal(items, cutoff):
        return [item.close for item in items if item.close_time <= cutoff]

    assert run_truncation_test(causal, bars, [at(9), at(10)]) == ()


def test_truncation_test_detects_future_read():
    bars = [bar(8), bar(9), bar(10)]

    def leaking(items, _cutoff):
        return items[-1].close

    failures = run_truncation_test(leaking, bars, [at(10)])
    assert len(failures) == 1
    assert failures[0].cutoff == at(10)


def test_truncation_test_can_normalize_metadata():
    bars = [bar(8), bar(9)]
    calls = iter(["first", "second"])

    def runner(items, cutoff):
        return {"values": [x.close for x in items if x.close_time <= cutoff], "run": next(calls)}

    assert run_truncation_test(runner, bars, [at(10)], normalize=lambda value: value["values"]) == ()
