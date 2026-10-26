# PROVENANCE (mirror of .provenance/ledger.jsonl; ledger wins)
# written-by: unknown (pre-provenance) | 2026-10-13 | e10f0e8
# modified-by: codex/gpt-5.6-sol | 2026-10-26 | f566a55 | provenance block added
# reviewed-by: claude-code/claude-opus-5-5 | 2026-10-26 | APPROVE
# END PROVENANCE
import csv

from backtest_leak_check.cli import main


def write(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        writer.writerows(rows)


def fixtures(tmp_path, decision_time="2024-01-02T12:00:00Z"):
    bars = tmp_path / "bars.csv"
    uses = tmp_path / "uses.csv"
    write(bars, ("symbol", "timeframe", "open_time", "open", "high", "low", "close", "volume"),
          (("XYZ", "4h", "2024-01-02T08:00:00Z", 10, 12, 9, 11, 5),))
    write(uses, ("decision_id", "decision_time", "symbol", "timeframe", "bar_open_time"),
          (("sample", decision_time, "XYZ", "4h", "2024-01-02T08:00:00Z"),))
    return bars, uses


def test_cli_pass(tmp_path, capsys):
    bars, uses = fixtures(tmp_path)
    assert main(["--bars", str(bars), "--uses", str(uses)]) == 0
    assert "PASS" in capsys.readouterr().out


def test_cli_fail_json(tmp_path, capsys):
    bars, uses = fixtures(tmp_path, "2024-01-02T10:00:00Z")
    assert main(["--bars", str(bars), "--uses", str(uses), "--json"]) == 1
    assert '"status": "FAIL"' in capsys.readouterr().out
