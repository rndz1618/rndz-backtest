"""Strategy registry for rndz-backtest.

Every strategy is a pure function (rows, params) -> list[int] positions.
Positions are +1 long, -1 short, 0 flat.

Honesty rule (enforced by the harness): a strategy must only use
information available at or before the current row. Rolling-window
indicators naturally satisfy this; anything that references future rows
is a bug the trainer/analyst owns.

To add a strategy:
  1. write the pure function below (or in a new module under strategies/),
  2. register it in STRATEGIES,
  3. run `python3 run_backtest.py --list`.
"""

from __future__ import annotations

import statistics
from typing import Any

# Import custom strategies
from strategies.ema_atr_trend import ema_atr_trend

# ---------------------------------------------------------------------------
# Demo strategy: Bollinger mean reversion (trained on train partition only)
# ---------------------------------------------------------------------------


def bollinger_mean_reversion(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[int]:
    """Long when close < lower band, flat otherwise (optional short on upper band).

    Bands computed on a rolling window ENDING at the current bar, so no
    look-ahead. Params (from the train split):
        window      rolling window length (default 20)
        n_std       number of std devs (default 2.0)
        short_upper if True, short when close > upper band (default False)
    """
    window = int(params.get("window", 20))
    n_std = float(params.get("n_std", 2.0))
    short_upper = bool(params.get("short_upper", False))

    positions: list[int] = []
    closes = [r["close"] for r in rows]

    for i, close in enumerate(closes):
        if i < window:
            positions.append(0)
            continue
        win = closes[i - window + 1 : i + 1]  # rolling window ends at current bar
        mid = statistics.mean(win)
        sd = statistics.stdev(win)
        if sd == 0:
            positions.append(0)
            continue
        lower = mid - n_std * sd
        upper = mid + n_std * sd
        if close < lower:
            positions.append(1)
        elif short_upper and close > upper:
            positions.append(-1)
        else:
            positions.append(0)
    return positions


# ---------------------------------------------------------------------------
# Baseline: buy & hold (always long) — the honest benchmark every strategy
# must be compared against.
# ---------------------------------------------------------------------------


def buy_and_hold(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[int]:
    return [1] * len(rows)


# ---------------------------------------------------------------------------
# Trend-following demo strategy: SMA crossover (classic momentum).
# Long when fast SMA > slow SMA, short when fast < slow (optional), flat in
# the neutral zone. Rolling windows end at the current bar — no look-ahead.
# ---------------------------------------------------------------------------


def sma_crossover(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[int]:
    """Fast/slow SMA crossover. Params: fast, slow, short_on_down.

    fast > slow -> long (+1); fast < slow -> -1 if short_on_down else 0.
    """
    fast = int(params.get("fast", 5))
    slow = int(params.get("slow", 20))
    short_on_down = bool(params.get("short_on_down", False))
    if fast >= slow:
        raise ValueError("fast SMA window must be < slow SMA window")

    closes = [r["close"] for r in rows]
    positions: list[int] = []
    for i in range(len(closes)):
        if i < slow - 1:
            positions.append(0)
            continue
        fast_avg = sum(closes[i - fast + 1 : i + 1]) / fast
        slow_avg = sum(closes[i - slow + 1 : i + 1]) / slow
        if fast_avg > slow_avg:
            positions.append(1)
        elif fast_avg < slow_avg and short_on_down:
            positions.append(-1)
        else:
            positions.append(0)
    return positions


# ---------------------------------------------------------------------------
# RSI Mean Reversion — new strategy for Phase 2
# Hypothesis: in crypto markets, extreme RSI readings often revert short-term.
# Long when RSI < oversold threshold; optional short when RSI > overbought.
# ---------------------------------------------------------------------------

from .rsi_mean_reversion import rsi_mean_reversion  # noqa: E402


STRATEGIES: dict[str, Any] = {
    "bollinger_mean_reversion": bollinger_mean_reversion,
    "sma_crossover": sma_crossover,
    "buy_and_hold": buy_and_hold,
    "rsi_mean_reversion": rsi_mean_reversion,
    "ema_atr_trend": ema_atr_trend,
}


def get_strategy(name: str):
    if name not in STRATEGIES:
        raise KeyError(
            f"unknown strategy '{name}'; available: {sorted(STRATEGIES)}"
        )
    return STRATEGIES[name]
