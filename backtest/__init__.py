"""rndz-backtest — lightweight, honest backtesting harness for Rndz.

Design goals (mirrors rndz-market-data constraints):
  - Python 3 stdlib ONLY (sqlite3, json, statistics). No pandas/numpy.
  - Runs on a 2GB ARM64 SBC or a tiny cloud runner without OOM.
  - Consumes OHLCV candles stored by the ingestion pipeline
    (rndz-market-data SQLite: table `candles`, columns
    source, symbol, interval, open_time, open, high, low, close, volume).
  - Honest train/test discipline: the strategy trains ONLY on the train
    partition; the test partition is never touched during fitting.
  - Reproducible: every run is seeded, versioned (git), and writes a
    JSON report + markdown summary with the exact SQL data contract,
    strategy code hash, and metric definitions.

Modules
-------
  backtest/engine.py     — event-loop backtest engine + P&L accounting
  backtest/metrics.py    — returns, drawdown, Sharpe-style statistics
  backtest/splits.py     — train/test split helpers (walk-forward aware)
  backtest/loader.py     — SQLite reader for the rndz-market-data DB
  strategies/            — strategy registry (each is a pure function)
  run_backtest.py        — CLI entry point
"""

__version__ = "0.1.0"
