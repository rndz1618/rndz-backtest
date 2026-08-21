"""RSI Mean Reversion Strategy for rndz-backtest.

Long when RSI < oversold threshold, flat when RSI > overbought threshold (or optional short).
Uses rolling window ending at current bar — no look-ahead.

Params (optimized on train partition only):
    window      RSI lookback period (default 14)
    oversold    RSI level to enter long (default 30)
    overbought  RSI level to exit/short (default 70)
    short_overbought  if True, short when RSI > overbought (default False)
"""
from __future__ import annotations
from typing import Any


def rsi_mean_reversion(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[int]:
    """RSI mean reversion. Positions: +1 long, -1 short, 0 flat.

    RSI computed on rolling window ending at current bar (no look-ahead).
    """
    window = int(params.get("window", 14))
    oversold = float(params.get("oversold", 30.0))
    overbought = float(params.get("overbought", 70.0))
    short_overbought = bool(params.get("short_overbought", False))

    if window < 2:
        raise ValueError("RSI window must be >= 2")

    positions: list[int] = []
    closes = [r["close"] for r in rows]

    # Precompute gains/losses for rolling RSI
    for i in range(len(closes)):
        if i < window:
            positions.append(0)
            continue

        # Rolling window ending at current bar i (inclusive)
        win = closes[i - window + 1 : i + 1]

        # Compute RSI on this window
        gains = []
        losses = []
        for j in range(1, len(win)):
            diff = win[j] - win[j - 1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(-diff)

        if not gains:
            positions.append(0)
            continue

        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        if rsi < oversold:
            positions.append(1)
        elif short_overbought and rsi > overbought:
            positions.append(-1)
        else:
            positions.append(0)

    return positions
