"""Train/test split helpers with honest discipline.

The whole point of the harness is that the strategy's parameters can be
tuned on the TRAIN partition only; the TEST partition is held out until
the final evaluation. These helpers make that boundary explicit.

split_timewise(rows, train_frac)  — contiguous timewise split (default)
    Rows must be sorted ascending by time. First `train_frac` of the
    series is train, the rest is test. No shuffling, no leakage.

split_n_last(rows, n)             — keep the last `n` rows as test
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Split:
    train: list[dict[str, Any]]
    test: list[dict[str, Any]]
    boundary_index: int  # first index of test in the original row order


def _require_sorted(rows: list[dict[str, Any]], time_key: str) -> None:
    times = [r[time_key] for r in rows]
    if times != sorted(times):
        raise ValueError("rows must be sorted ascending by time before splitting")


def split_timewise(rows: list[dict[str, Any]], train_frac: float = 0.7, time_key: str = "open_time") -> Split:
    if not rows:
        return Split([], [], 0)
    if not 0.0 < train_frac < 1.0:
        raise ValueError("train_frac must be in (0, 1)")
    _require_sorted(rows, time_key)
    n = len(rows)
    idx = max(1, int(n * train_frac))
    if idx >= n:
        idx = n - 1
    return Split(train=rows[:idx], test=rows[idx:], boundary_index=idx)


def split_n_last(rows: list[dict[str, Any]], n_test: int = 30, time_key: str = "open_time") -> Split:
    if not rows:
        return Split([], [], 0)
    if n_test <= 0:
        raise ValueError("n_test must be positive")
    _require_sorted(rows, time_key)
    n = len(rows)
    idx = max(1, n - n_test)
    return Split(train=rows[:idx], test=rows[idx:], boundary_index=idx)
