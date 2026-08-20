#!/usr/bin/env python3
"""Unit tests for rndz-backtest. Run with: python3 -m unittest -v"""

from __future__ import annotations

import math
import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtest.engine import EngineConfig, run_backtest  # noqa: E402
from backtest.loader import available_symbols, load_candles  # noqa: E402
from backtest.metrics import (  # noqa: E402
    cagr,
    daily_returns,
    max_drawdown,
    sharpe_ratio,
    summarize_equity,
    total_return,
)
from backtest.splits import split_n_last, split_timewise  # noqa: E402
from strategies import buy_and_hold, get_strategy  # noqa: E402


def make_rows(closes: list[float], opens: list[float] | None = None) -> list[dict]:
    opens = opens or closes
    return [
        {
            "open_time": 1700000000 + i * 86400,
            "open": opens[i],
            "high": max(opens[i], c) * 1.001,
            "low": min(opens[i], c) * 0.999,
            "close": c,
            "volume": 1000.0,
        }
        for i, c in enumerate(closes)
    ]


class TestMetrics(unittest.TestCase):
    def test_total_return(self):
        eq = [100, 110, 121]
        self.assertAlmostEqual(total_return(eq), 0.21)

    def test_cagr_daily(self):
        # 21% total return over 2 daily bars -> annualized over 365 bars/yr
        eq = [100, 110, 121]
        self.assertAlmostEqual(cagr(eq, 365.0), (1.21) ** (365.0 / 2) - 1.0, places=6)

    def test_daily_returns(self):
        eq = [100, 110, 99]
        rets = daily_returns(eq)
        self.assertEqual(len(rets), 2)
        self.assertAlmostEqual(rets[0], 0.10)
        self.assertAlmostEqual(rets[1], -0.10, places=10)

    def test_max_drawdown(self):
        eq = [100, 120, 90, 95, 80]
        self.assertAlmostEqual(max_drawdown(eq), (120 - 80) / 120)

    def test_sharpe_zero_variance(self):
        self.assertEqual(sharpe_ratio([0.0, 0.0, 0.0]), 0.0)

    def test_summarize_equity_fields(self):
        s = summarize_equity([100, 110, 99, 105])
        for key in (
            "total_return",
            "cagr",
            "annualized_vol",
            "sharpe",
            "sortino",
            "calmar",
            "max_drawdown",
            "win_rate",
            "profit_factor",
            "end_equity",
        ):
            self.assertIn(key, s)


class TestSplits(unittest.TestCase):
    def test_timewise_split(self):
        rows = make_rows([float(i) for i in range(100)])
        s = split_timewise(rows, 0.7)
        self.assertEqual(len(s.train) + len(s.test), 100)
        self.assertEqual(s.train[0]["open_time"], rows[0]["open_time"])
        self.assertEqual(s.test[-1]["open_time"], rows[-1]["open_time"])
        # no overlap
        train_times = {r["open_time"] for r in s.train}
        test_times = {r["open_time"] for r in s.test}
        self.assertEqual(train_times & test_times, set())

    def test_split_n_last(self):
        rows = make_rows([float(i) for i in range(50)])
        s = split_n_last(rows, 10)
        self.assertEqual(len(s.test), 10)
        self.assertEqual(len(s.train), 40)

    def test_unsorted_raises(self):
        rows = make_rows([1.0, 2.0, 3.0, 4.0])
        rows[1], rows[2] = rows[2], rows[1]
        with self.assertRaises(ValueError):
            split_timewise(rows)


class TestEngine(unittest.TestCase):
    def test_buy_and_hold_equity(self):
        opens = [100.0, 100.5, 102.0, 101.5]
        closes = [100.0, 101.0, 102.5, 101.0]
        rows = make_rows(closes, opens)
        res = run_backtest(rows, buy_and_hold, {}, EngineConfig(cost_per_trade=0.0))
        self.assertEqual(len(res.equity), len(rows))
        # no costs; entry at bar1 open (100.5) with open->close day 1, then close-to-close
        expected = 10000 * (101.0 / 100.5) * (102.5 / 101.0) * (101.0 / 102.5)
        self.assertAlmostEqual(res.equity[-1], expected, places=6)

    def test_flat_strategy_no_change(self):
        rows = make_rows([100.0, 110.0, 90.0])

        def flat(rows, params):
            return [0] * len(rows)

        res = run_backtest(rows, flat, {})
        self.assertEqual(res.equity, [10000.0] * 3)
        self.assertEqual(sum(res.returns), 0.0)

    def test_long_then_flat_costs_money(self):
        rows = make_rows([100.0, 100.0, 100.0, 100.0])

        def enter_exit(rows, params):
            return [1, 1, 0, 0]

        res = run_backtest(rows, enter_exit, {}, EngineConfig(cost_per_trade=0.001))
        # two changes: entry cost 0.1% of 10k, exit cost 0.1% of remaining
        self.assertLess(res.equity[-1], 10000.0)
        expected = 10000 * (1 - 0.001) * (1 - 0.001)
        self.assertAlmostEqual(res.equity[-1], expected, places=4)

    def test_position_length_mismatch_raises(self):
        rows = make_rows([100.0, 101.0, 102.0])

        def bad(rows, params):
            return [1, 0]

        with self.assertRaises(ValueError):
            run_backtest(rows, bad, {})

    def test_no_lookahead_execution_at_next_open(self):
        # If the engine executed at the same bar's open as the signal,
        # a strategy that "predicts" tomorrow's direction would look
        # perfect. Here signal goes long at bar 0 using close 100; the
        # engine should execute at bar 1's open (which we set to a gap
        # DOWN to 90). The long position then loses the gap, i.e. the
        # first-day return uses open->close, NOT close[0]->close[1].
        rows = make_rows(closes=[100.0, 80.0, 120.0], opens=[100.0, 90.0, 80.0])

        def go_long(rows, params):
            return [1, 1, 1]

        res = run_backtest(rows, go_long, {}, EngineConfig(cost_per_trade=0.0))
        # bar1: entry at open 90, close 80 -> ret = -10/90
        self.assertAlmostEqual(res.returns[0], 80.0 / 90.0 - 1.0, places=10)
        # bar2: close-to-close 120/80 - 1
        self.assertAlmostEqual(res.returns[1], 120.0 / 80.0 - 1.0, places=10)


class TestStrategies(unittest.TestCase):
    def test_buy_and_hold_all_long(self):
        rows = make_rows([100.0, 101.0, 102.0])
        self.assertEqual(buy_and_hold(rows, {}), [1, 1, 1])

    def test_bollinger_no_lookahead_warmup(self):
        # Below lower band -> long; warmup rows (window) are flat.
        closes = [100.0 + 10 * math.sin(i / 3.0) for i in range(40)]
        rows = make_rows(closes)
        pos = get_strategy("bollinger_mean_reversion")(
            rows, {"window": 20, "n_std": 2.0, "short_upper": False}
        )
        self.assertEqual(len(pos), len(rows))
        self.assertTrue(all(p == 0 for p in pos[:20]))
        self.assertTrue(all(p in (-1, 0, 1) for p in pos))

    def test_deterministic(self):
        closes = [float(100 + (i % 7) * 2 - (i % 3)) for i in range(60)]
        rows = make_rows(closes)
        a = run_backtest(rows, get_strategy("bollinger_mean_reversion"), {"window": 20, "n_std": 2.0}, EngineConfig())
        b = run_backtest(rows, get_strategy("bollinger_mean_reversion"), {"window": 20, "n_std": 2.0}, EngineConfig())
        self.assertEqual(a.equity, b.equity)


class TestLoader(unittest.TestCase):
    def test_loader_roundtrip_synthetic(self):
        import sqlite3
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "market.db"
            con = sqlite3.connect(db)
            con.executescript(
                """
                CREATE TABLE candles (
                    source TEXT NOT NULL, symbol TEXT NOT NULL,
                    open_time INTEGER NOT NULL, interval TEXT NOT NULL,
                    open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL,
                    close REAL NOT NULL, volume REAL, quote_volume REAL, raw TEXT,
                    PRIMARY KEY (source, symbol, interval, open_time)
                );
                """
            )
            for i in range(10):
                con.execute(
                    "INSERT INTO candles VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    ("binance", "TEST", 1700000000 + i * 86400, "1d",
                     100 + i, 101 + i, 99 + i, 100.5 + i, 1000, None, None),
                )
            con.commit()
            con.close()
            rows = load_candles(db, "TEST", "binance", "1d")
            self.assertEqual(len(rows), 10)
            self.assertEqual(rows[0]["open_time"], 1700000000)
            self.assertEqual(rows[-1]["close"], 109.5)
            syms = available_symbols(db)
            self.assertEqual(syms, [("binance", "TEST", "1d", 10)])


if __name__ == "__main__":
    unittest.main()
