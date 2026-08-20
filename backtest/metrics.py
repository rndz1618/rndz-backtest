"""Metrics for honest strategy evaluation.

All functions accept plain lists of floats. No external dependencies.
Annualization uses `periods_per_year` (default 365 for daily bars).

Definitions (documented so results are reproducible):
  - total_return:      (end_equity / start_equity) - 1
  - cagr:              annualized compound growth rate
  - vol (annualized):  std(daily_returns) * sqrt(periods_per_year)
  - sharpe:            mean(daily_returns) / std(daily_returns) * sqrt(periods_per_year)
                       using the sample standard deviation (ddof=1)
  - max_drawdown:      max peak-to-trough decline of the equity curve
  - sortino:           like sharpe but downside deviation only
  - calmar:            cagr / abs(max_drawdown)
  - win_rate:          fraction of non-flat daily returns that are positive
"""

from __future__ import annotations

import math
import statistics


def daily_returns(equity: list[float]) -> list[float]:
    """Period returns from an equity curve: (e[t] - e[t-1]) / e[t-1]."""
    out: list[float] = []
    for i in range(1, len(equity)):
        prev = equity[i - 1]
        if prev == 0:
            continue
        out.append((equity[i] - prev) / prev)
    return out


def total_return(equity: list[float]) -> float:
    if len(equity) < 2 or equity[0] == 0:
        return 0.0
    return equity[-1] / equity[0] - 1.0


def cagr(equity: list[float], periods_per_year: float = 365.0) -> float:
    """Compound annual growth rate over the equity curve span.

    NOTE: for backtest purposes the "year count" is the number of
    periods (bars), not calendar days, so CAGR stays consistent when
    bars are daily or weekly. `periods_per_year` is the bar-frequency
    annualization factor (365 for daily bars)."""
    n = max(len(equity) - 1, 1)
    tr = total_return(equity)
    if tr <= -1.0:
        return -1.0
    return (1.0 + tr) ** (periods_per_year / n) - 1.0


def annualized_vol(returns: list[float], periods_per_year: float = 365.0) -> float:
    if len(returns) < 2:
        return 0.0
    return statistics.stdev(returns) * math.sqrt(periods_per_year)


def sharpe_ratio(returns: list[float], periods_per_year: float = 365.0, rf: float = 0.0) -> float:
    """Sharpe-style statistic. Sample std (ddof=1); rf subtracted from mean."""
    if len(returns) < 2:
        return 0.0
    sd = statistics.stdev(returns)
    if sd == 0:
        return 0.0
    return (statistics.mean(returns) - rf / periods_per_year) / sd * math.sqrt(periods_per_year)


def downside_deviation(returns: list[float], periods_per_year: float = 365.0) -> float:
    """Target (0) downside deviation — only negative returns count."""
    neg = [r for r in returns if r < 0]
    if not neg:
        return 0.0
    return math.sqrt(sum(r * r for r in neg) / len(returns))


def sortino_ratio(returns: list[float], periods_per_year: float = 365.0, rf: float = 0.0) -> float:
    dd = downside_deviation(returns, periods_per_year)
    if dd == 0:
        return 0.0
    return (statistics.mean(returns) - rf / periods_per_year) / dd * math.sqrt(periods_per_year)


def max_drawdown(equity: list[float]) -> float:
    """Maximum peak-to-trough decline, as a positive fraction (0.42 == -42%)."""
    peak = -math.inf
    mdd = 0.0
    for v in equity:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (peak - v) / peak
            if dd > mdd:
                mdd = dd
    return mdd


def calmar_ratio(equity: list[float], periods_per_year: float = 365.0) -> float:
    mdd = max_drawdown(equity)
    if mdd <= 0:
        return 0.0
    return cagr(equity, periods_per_year) / mdd


def win_rate(returns: list[float]) -> float:
    """Fraction of non-zero daily returns that are positive."""
    nonzero = [r for r in returns if r != 0]
    if not nonzero:
        return 0.0
    return sum(1 for r in nonzero if r > 0) / len(nonzero)


def profit_factor(returns: list[float]) -> float:
    """Gross profit / gross loss on daily returns."""
    gross_win = sum(r for r in returns if r > 0)
    gross_loss = abs(sum(r for r in returns if r < 0))
    if gross_loss == 0:
        return float("inf") if gross_win > 0 else 0.0
    return gross_win / gross_loss


def summarize_equity(equity: list[float], periods_per_year: float = 365.0) -> dict:
    """Full metric block for one equity curve (used for train and test)."""
    rets = daily_returns(equity)
    return {
        "n_periods": max(len(equity) - 1, 0),
        "total_return": round(total_return(equity), 6),
        "cagr": round(cagr(equity, periods_per_year), 6),
        "annualized_vol": round(annualized_vol(rets, periods_per_year), 6),
        "sharpe": round(sharpe_ratio(rets, periods_per_year), 6),
        "sortino": round(sortino_ratio(rets, periods_per_year), 6),
        "calmar": round(calmar_ratio(equity, periods_per_year), 6),
        "max_drawdown": round(max_drawdown(equity), 6),
        "win_rate": round(win_rate(rets), 6),
        "profit_factor": round(profit_factor(rets), 6) if profit_factor(rets) != float("inf") else None,
        "end_equity": round(equity[-1], 6) if equity else None,
    }
