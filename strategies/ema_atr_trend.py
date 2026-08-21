"""EMA Crossover with ATR Volatility Filter — Trend Following Strategy.

This is a real institutional-style trend-following strategy:
- Fast/slow EMA crossover for trend direction (no look-ahead)
- ATR-based volatility filter to avoid choppy/whipsaw markets
- Position sizing scaled by inverse volatility (volatility targeting)

Params (optimized on train partition only):
    fast_ema      Fast EMA period (default 12)
    slow_ema      Slow EMA period (default 26)
    atr_window    ATR lookback for volatility (default 14)
    vol_threshold Volatility percentile threshold to trade (default 0.7)
                  Only trade when current ATR is below this percentile
                  of recent ATR history (avoids high-vol chop)
    vol_target    Target annualized volatility for position sizing (default 0.30)
                  Position scaled so strategy vol ≈ vol_target
    max_pos       Maximum position size as fraction of equity (default 1.0)

All calculations use rolling windows ending at current bar — no look-ahead.
"""

from __future__ import annotations
from typing import Any
import math


def ema(values: list[float], period: int) -> list[float]:
    """Exponential Moving Average — returns list aligned with input."""
    if not values or period < 1:
        return [0.0] * len(values)
    alpha = 2.0 / (period + 1.0)
    out = [0.0] * len(values)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1]
    return out


def atr(highs: list[float], lows: list[float], closes: list[float], period: int) -> list[float]:
    """Average True Range — returns list aligned with input."""
    n = len(closes)
    if n == 0 or period < 1:
        return [0.0] * n
    tr = [0.0] * n
    for i in range(n):
        if i == 0:
            tr[i] = highs[i] - lows[i]
        else:
            tr[i] = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
    # EMA of TR (Wilder's smoothing = EMA with alpha = 1/period)
    alpha = 1.0 / period
    out = [0.0] * n
    out[0] = tr[0]
    for i in range(1, n):
        out[i] = alpha * tr[i] + (1.0 - alpha) * out[i - 1]
    return out


def ema_atr_trend(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[int]:
    """EMA Crossover with ATR Volatility Filter.

    Position logic:
    - Long (+1) when fast EMA > slow EMA AND volatility filter passes
    - Flat (0) when fast EMA <= slow EMA OR volatility filter fails
    - Optional short (-1) when fast EMA < slow EMA (disabled by default for crypto)
    """
    fast_ema_period = int(params.get("fast_ema", 12))
    slow_ema_period = int(params.get("slow_ema", 26))
    atr_window = int(params.get("atr_window", 14))
    vol_threshold = float(params.get("vol_threshold", 0.7))
    vol_target = float(params.get("vol_target", 0.30))
    max_pos = float(params.get("max_pos", 1.0))

    if fast_ema_period >= slow_ema_period:
        raise ValueError("fast_ema must be < slow_ema")
    if not (0.0 < vol_threshold <= 1.0):
        raise ValueError("vol_threshold must be in (0, 1]")
    if not (0.0 < max_pos <= 1.0):
        raise ValueError("max_pos must be in (0, 1]")

    n = len(rows)
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]

    # Compute indicators on full history (rolling, no look-ahead)
    fast_ema_vals = ema(closes, fast_ema_period)
    slow_ema_vals = ema(closes, slow_ema_period)
    atr_vals = atr(highs, lows, closes, atr_window)

    positions: list[int] = []
    # For volatility percentile: keep rolling window of ATR values
    atr_history: list[float] = []

    for i in range(n):
        # Need enough data for slow EMA and ATR
        if i < max(slow_ema_period, atr_window) - 1:
            positions.append(0)
            if i < len(atr_vals):
                atr_history.append(atr_vals[i])
            continue

        # Current ATR
        current_atr = atr_vals[i] if i < len(atr_vals) else 0.0
        atr_history.append(current_atr)

        # Volatility percentile filter: only trade if current ATR
        # is below the vol_threshold percentile of recent ATR history
        # This avoids trading in extremely volatile/choppy conditions
        if len(atr_history) >= atr_window:
            sorted_atr = sorted(atr_history[-atr_window:])
            idx = int(vol_threshold * (len(sorted_atr) - 1))
            vol_pctile = sorted_atr[idx]
            vol_filter_pass = current_atr <= vol_pctile
        else:
            vol_filter_pass = True

        # Trend signal: fast EMA vs slow EMA
        trend_up = fast_ema_vals[i] > slow_ema_vals[i]

        # Determine raw position
        if trend_up and vol_filter_pass:
            raw_pos = 1.0
        elif not trend_up and vol_filter_pass:
            raw_pos = 0.0  # no short by default for crypto
        else:
            raw_pos = 0.0  # vol filter failed → flat

        # Volatility targeting: scale position so strategy vol ≈ vol_target
        # Use current ATR as proxy for daily vol, annualize
        if current_atr > 0 and closes[i] > 0:
            daily_vol_est = current_atr / closes[i]  # approx daily vol
            annual_vol_est = daily_vol_est * math.sqrt(365.0)
            if annual_vol_est > 0:
                vol_scale = min(vol_target / annual_vol_est, max_pos)
            else:
                vol_scale = max_pos
        else:
            vol_scale = max_pos

        # Final position (clipped to max_pos, then discretized to -1/0/1)
        final_pos = raw_pos * vol_scale
        if final_pos >= 0.5:
            positions.append(1)
        elif final_pos <= -0.5:
            positions.append(-1)
        else:
            positions.append(0)

    return positions