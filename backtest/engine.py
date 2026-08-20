"""Event-loop backtest engine.

Design
------
- A strategy is a pure function:

      def strategy(rows: list[dict], params: dict) -> list[int]:
          '''Return the desired POSITION for each row:
              +1 long, -1 short, 0 flat.
             len(return) == len(rows).'''

  The strategy may only use information available AT or BEFORE row i
  (no look-ahead). The engine holds the strategy to this contract by
  evaluating `position[i]` with data only from rows[:i+1].

- The engine trades at the NEXT bar's open after a signal change
  (standard practice to avoid look-ahead bias): the position decided
  using data up to close of bar i-1 is executed at bar i's open.

- P&L accounting:
    - On the first day of a position: open->close move (we never claim
      the overnight gap between signal and execution).
    - Subsequent days: close->close move.
    - Short mirrors: ret = -(move).
    - Costs: `cost_per_trade` fraction of current equity, charged per
      position change (both entry and exit), before the day's P&L.

- Equity is compounded: equity[i] = equity[i-1] * (1 + ret[i]).
- Default params: initial_capital=10_000, cost_per_trade=0.001 (0.1%).

Reproducibility: the engine is deterministic; strategy PRNGs are
seeded by the caller (run_backtest.py) from a run seed.
"""

from __future__ import annotations

import hashlib
import inspect
from dataclasses import dataclass
from typing import Any, Callable

Strategy = Callable[[list[dict[str, Any]], dict[str, Any]], list[int]]


@dataclass
class EngineConfig:
    initial_capital: float = 10_000.0
    cost_per_trade: float = 0.001  # fraction of notional, per position change


@dataclass
class RunResult:
    rows: list[dict[str, Any]]
    positions: list[int]
    equity: list[float]
    trades: list[dict[str, Any]]
    returns: list[float]
    params: dict[str, Any]
    config: EngineConfig
    strategy_code_hash: str
    train_rows: int = 0
    test_rows: int = 0


def _hash_strategy(strategy: Strategy) -> str:
    return hashlib.sha256(inspect.getsource(strategy).encode("utf-8")).hexdigest()[:16]


def run_backtest(
    rows: list[dict[str, Any]],
    strategy: Strategy,
    params: dict[str, Any],
    config: EngineConfig | None = None,
) -> RunResult:
    """Run a strategy over rows (sorted ascending by open_time)."""
    cfg = config or EngineConfig()
    if len(rows) < 2:
        raise ValueError("need at least 2 rows to backtest")

    positions = strategy(rows, params)
    if len(positions) != len(rows):
        raise ValueError(f"strategy returned {len(positions)} positions for {len(rows)} rows")

    equity = [float(cfg.initial_capital)]
    returns: list[float] = []
    trades: list[dict[str, Any]] = []
    cur_pos = 0
    entry_idx: int | None = None  # bar index at which the current position opened

    for i in range(1, len(rows)):
        close_prev = rows[i - 1]["close"]
        open_cur = rows[i]["open"]
        close_cur = rows[i]["close"]
        target = int(max(-1, min(1, positions[i - 1])))  # decided at close of bar i-1

        if target != cur_pos:
            cost = cfg.cost_per_trade * abs(target - cur_pos) * equity[-1]
            if cost > 0:
                trades.append(
                    {
                        "ts": rows[i]["open_time"],
                        "side": (
                            "open_long"
                            if target > cur_pos and target > 0
                            else "open_short" if target < cur_pos and target < 0 else "close_or_flip"
                        ),
                        "price": round(open_cur, 6),
                        "cost": round(cost, 6),
                    }
                )
            equity[-1] -= cost
            cur_pos = target
            entry_idx = i if target != 0 else None

        if cur_pos == 0:
            ret = 0.0
        elif cur_pos == 1:
            if entry_idx == i:  # first day of the position: open->close
                ret = close_cur / open_cur - 1.0 if open_cur else 0.0
            else:
                ret = close_cur / close_prev - 1.0 if close_prev else 0.0
        else:  # short
            if entry_idx == i:
                ret = -(close_cur / open_cur - 1.0) if open_cur else 0.0
            else:
                ret = -(close_cur / close_prev - 1.0) if close_prev else 0.0

        returns.append(ret)
        equity.append(equity[-1] * (1.0 + ret))

    return RunResult(
        rows=rows,
        positions=positions,
        equity=equity,
        trades=trades,
        returns=returns,
        params=params,
        config=cfg,
        strategy_code_hash=_hash_strategy(strategy),
        train_rows=0,
        test_rows=len(rows),
    )
