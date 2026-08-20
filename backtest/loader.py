"""SQLite loader for the rndz-market-data ingestion pipeline.

Reads OHLCV candles from the `candles` table. The schema is defined in
rndz-market-data/ingest.py:

    candles(
        source TEXT, symbol TEXT, open_time INTEGER, interval TEXT,
        open REAL, high REAL, low REAL, close REAL, volume REAL,
        quote_volume REAL, raw TEXT,
        PRIMARY KEY (source, symbol, interval, open_time)
    )

Returns a list of dicts with string keys:
    open_time, open, high, low, close, volume
sorted ascending by open_time.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def load_candles(
    db_path: str | Path,
    symbol: str,
    source: str = "binance",
    interval: str = "1d",
    max_rows: int | None = None,
) -> list[dict[str, Any]]:
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"market DB not found: {db_path}")

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            """
            SELECT open_time, open, high, low, close, volume
            FROM candles
            WHERE source = ? AND symbol = ? AND interval = ?
            ORDER BY open_time ASC
            """,
            (source, symbol, interval),
        ).fetchall()
    finally:
        con.close()

    if max_rows is not None and max_rows > 0:
        rows = rows[-max_rows:]

    return [
        {
            "open_time": r[0],
            "open": r[1],
            "high": r[2],
            "low": r[3],
            "close": r[4],
            "volume": r[5],
        }
        for r in rows
    ]


def available_symbols(db_path: str | Path) -> list[tuple[str, str, str, int]]:
    """List (source, symbol, interval, count) present in the DB."""
    db_path = Path(db_path)
    if not db_path.exists():
        return []
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            """
            SELECT source, symbol, interval, COUNT(*)
            FROM candles
            GROUP BY source, symbol, interval
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()
    finally:
        con.close()
    return [(r[0], r[1], r[2], r[3]) for r in rows]
