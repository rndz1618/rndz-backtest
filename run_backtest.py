#!/usr/bin/env python3
"""rndz-backtest CLI — run a strategy against stored historical data.

Usage:
  python3 run_backtest.py --db /root/rndz-market-data/data/market.db \
      --symbol BTCUSDT --source binance --strategy bollinger_mean_reversion \
      --train-frac 0.7 --out results/btc-demo.json

  python3 run_backtest.py --list                    # list strategies
  python3 run_backtest.py --symbols --db <path>     # list data available in DB

Train/test discipline (the honest part):
  - rows are split timewise; TRAIN is used to select strategy parameters
    (grid search by Sharpe on the train partition only).
  - TEST is evaluated once with those parameters. The test partition is
    NEVER used during fitting.
  - buy_and_hold on the same partition is reported as the benchmark.

Reproducibility:
  - every run records: seed, git revision, strategy code hash, DB path,
    SQL data contract, param grid searched, chosen params.
  - deterministic PRNG seeding for anything stochastic.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import random
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backtest.engine import EngineConfig, run_backtest  # noqa: E402
from backtest.loader import available_symbols, load_candles  # noqa: E402
from backtest.metrics import summarize_equity  # noqa: E402
from backtest.splits import split_timewise  # noqa: E402
from strategies import STRATEGIES, get_strategy  # noqa: E402

# Byte-stable timestamps: the report must reproduce EXACTLY on reruns,
# so we embed the data's own last bar time instead of wall-clock now().
def report_timestamp(rows: list[dict]) -> str:
    return datetime.datetime.fromtimestamp(
        rows[-1]["open_time"], datetime.timezone.utc
    ).isoformat()


def git_revision() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT
        )
        return out.stdout.strip() or "dirty"
    except Exception:
        return "unknown"


def git_dirty() -> bool:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT
        )
        return bool(out.stdout.strip())
    except Exception:
        return True


def grid_search_train(
    strategy_name: str,
    train_rows: list[dict],
    grid: list[dict],
    cost_per_trade: float = 0.001,
) -> dict:
    """Pick the param set with best TRAIN Sharpe. Test data untouched."""
    strategy = get_strategy(strategy_name)
    cfg = EngineConfig(cost_per_trade=cost_per_trade)
    best: dict | None = None
    for params in grid:
        try:
            res = run_backtest(train_rows, strategy, params, cfg)
            metrics = summarize_equity(res.equity, periods_per_year=365.0)
            score = metrics["sharpe"]
        except Exception:
            continue
        if best is None or score > best["score"]:
            best = {"params": params, "score": score, "metrics": metrics}
    if best is None:
        raise RuntimeError("grid search produced no valid result on train split")
    return best


def main() -> int:
    ap = argparse.ArgumentParser(description="rndz-backtest harness")
    ap.add_argument("--db", default=str(ROOT / "data" / "market.db"), help="path to market SQLite DB")
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--source", default="binance")
    ap.add_argument("--interval", default="1d")
    ap.add_argument("--strategy", default="bollinger_mean_reversion")
    ap.add_argument("--train-frac", type=float, default=0.7)
    ap.add_argument("--cost", type=float, default=0.001)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(ROOT / "results" / "backtest.json"))
    ap.add_argument("--md", default=None, help="markdown summary output path")
    ap.add_argument("--list", action="store_true", help="list strategies and exit")
    ap.add_argument("--symbols", action="store_true", help="list available symbols and exit")
    args = ap.parse_args()

    if args.list:
        print("Strategies:")
        for name in sorted(STRATEGIES):
            fn = STRATEGIES[name]
            print(f"  {name:<28} {fn.__doc__.splitlines()[0] if fn.__doc__ else ''}")
        return 0

    if args.symbols:
        for src, sym, iv, n in available_symbols(args.db):
            print(f"  {src:8s} {sym:10s} {iv:4s} n={n}")
        return 0

    random.seed(args.seed)
    strategy = get_strategy(args.strategy)

    rows = load_candles(args.db, args.symbol, args.source, args.interval)
    if len(rows) < 30:
        print(f"ERROR: only {len(rows)} rows for {args.symbol} — need >= 30 for a meaningful split", file=sys.stderr)
        return 2

    split = split_timewise(rows, args.train_frac)
    train_rows, test_rows = split.train, split.test
    cfg = EngineConfig(cost_per_trade=args.cost)

    # ---- TRAIN: grid search by Sharpe on train partition only ----
    grid = []
    if args.strategy == "bollinger_mean_reversion":
        for window in (10, 20, 30):
            for n_std in (1.5, 2.0, 2.5):
                for short_upper in (False, True):
                    grid.append({"window": window, "n_std": n_std, "short_upper": short_upper})
    elif args.strategy == "sma_crossover":
        for fast, slow in ((3, 10), (5, 20), (10, 30), (5, 15)):
            for short_on_down in (False, True):
                grid.append({"fast": fast, "slow": slow, "short_on_down": short_on_down})
    elif args.strategy == "rsi_mean_reversion":
        for window in (10, 14, 20):
            for oversold in (25, 30, 35):
                for overbought in (65, 70, 75):
                    for short_overbought in (False, True):
                        grid.append({"window": window, "oversold": oversold, "overbought": overbought, "short_overbought": short_overbought})
    elif args.strategy == "ema_atr_trend":
        for fast, slow in ((12, 26), (8, 21), (5, 13), (10, 20)):
            for atr_w in (10, 14, 20):
                for vol_thresh in (0.6, 0.7, 0.8):
                    for vol_tgt in (0.25, 0.30, 0.40):
                        grid.append({"fast_ema": fast, "slow_ema": slow, "atr_window": atr_w, "vol_threshold": vol_thresh, "vol_target": vol_tgt})
    else:
        grid = [{}]
    train_sel = grid_search_train(args.strategy, train_rows, grid, args.cost)

    # ---- TEST: one evaluation with the chosen params ----
    test_res = run_backtest(test_rows, strategy, train_sel["params"], cfg)
    test_metrics = summarize_equity(test_res.equity, periods_per_year=365.0)

    # ---- TRAIN metrics with same params (diagnostic only) ----
    train_res = run_backtest(train_rows, strategy, train_sel["params"], cfg)
    train_metrics = summarize_equity(train_res.equity, periods_per_year=365.0)

    # ---- Benchmark: buy & hold on the test partition ----
    bh_res = run_backtest(test_rows, get_strategy("buy_and_hold"), {}, cfg)
    bh_metrics = summarize_equity(bh_res.equity, periods_per_year=365.0)

    # ---- Buy & hold benchmark on the full series (context) ----
    full_bh = run_backtest(rows, get_strategy("buy_and_hold"), {}, cfg)
    full_bh_metrics = summarize_equity(full_bh.equity, periods_per_year=365.0)

    n_trades = len(test_res.trades)
    trades_per_year = n_trades / (max(len(test_rows) - 1, 1) / 365.0) if n_trades else 0.0

    report = {
        "harness_version": "0.1.0",
        "generated_at": report_timestamp(rows),
        "reproducibility": {
            "seed": args.seed,
            "git_revision": git_revision(),
            "git_dirty": git_dirty(),
            "strategy_code_hash": test_res.strategy_code_hash,
            "python": sys.version.split()[0],
            "platform": os.uname().machine,
        },
        "data": {
            "db_path": str(args.db),
            "source": args.source,
            "symbol": args.symbol,
            "interval": args.interval,
            "n_rows": len(rows),
            "start": rows[0]["open_time"],
            "end": rows[-1]["open_time"],
            "start_iso": datetime.datetime.fromtimestamp(rows[0]["open_time"], datetime.timezone.utc).isoformat(),
            "end_iso": datetime.datetime.fromtimestamp(rows[-1]["open_time"], datetime.timezone.utc).isoformat(),
            "contract": "candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite",
        },
        "split": {
            "method": "timewise",
            "train_frac": args.train_frac,
            "n_train": len(train_rows),
            "n_test": len(test_rows),
            "train_start_iso": datetime.datetime.fromtimestamp(train_rows[0]["open_time"], datetime.timezone.utc).isoformat(),
            "train_end_iso": datetime.datetime.fromtimestamp(train_rows[-1]["open_time"], datetime.timezone.utc).isoformat(),
            "test_start_iso": datetime.datetime.fromtimestamp(test_rows[0]["open_time"], datetime.timezone.utc).isoformat(),
            "test_end_iso": datetime.datetime.fromtimestamp(test_rows[-1]["open_time"], datetime.timezone.utc).isoformat(),
        },
        "strategy": {
            "name": args.strategy,
            "params_grid_searched": grid,
            "params_chosen_on_train": train_sel["params"],
            "train_sharpe_of_chosen": round(train_sel["score"], 6),
        },
        "engine": {"initial_capital": cfg.initial_capital, "cost_per_trade": cfg.cost_per_trade},
        "results": {
            "train": train_metrics,
            "test": test_metrics,
            "test_n_trades": n_trades,
            "test_trades_per_year": round(trades_per_year, 2),
            "benchmark_buy_and_hold_test": bh_metrics,
            "benchmark_buy_and_hold_full": full_bh_metrics,
        },
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")

    # ---- Markdown summary ----
    md = build_markdown(report)
    md_path = Path(args.md) if args.md else out.with_suffix(".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md)

    print(json.dumps(report["results"], indent=2))
    print(f"\nJSON report : {out}")
    print(f"Markdown    : {md_path}")
    return 0


def build_markdown(report: dict) -> str:
    r = report
    data = r["data"]
    split = r["split"]
    st = r["strategy"]
    res = r["results"]
    t = res["test"]
    tr = res["train"]
    bh = res["benchmark_buy_and_hold_test"]

    def iso(ts: str) -> str:
        return ts[:10]

    lines = [
        f"# Backtest: {st['name']} on {data['symbol']}",
        "",
        f"- Source data: {data['source']}/{data['symbol']} {data['interval']} "
        f"({data['n_rows']} bars, {iso(data['start_iso'])} → {iso(data['end_iso'])})",
        f"- Contract: `{data['contract']}`",
        f"- Harness: v{r['harness_version']} · git `{r['reproducibility']['git_revision']}`"
        f"{' (dirty)' if r['reproducibility']['git_dirty'] else ''} · seed {r['reproducibility']['seed']}",
        f"- Strategy code hash: `{r['reproducibility']['strategy_code_hash']}`",
        "",
        "## Train/test discipline",
        "",
        f"- Split: {split['method']}, train {split['train_frac']:.0%} "
        f"({split['n_train']} bars, {iso(split['train_start_iso'])} → {iso(split['train_end_iso'])})",
        f"- Test: {split['n_test']} bars ({iso(split['test_start_iso'])} → {iso(split['test_end_iso'])})",
        f"- Parameters chosen by grid search on **train Sharpe only**: `{st['params_chosen_on_train']}` "
        f"(grid: {len(st['params_grid_searched'])} combos; train Sharpe {st['train_sharpe_of_chosen']})",
        f"- Test partition evaluated exactly once with those parameters.",
        "",
        "## Test metrics (strategy vs buy & hold)",
        "",
        "| Metric | Strategy | Buy & hold |",
        "|---|---|---|",
        f"| Total return | {t['total_return']:.2%} | {bh['total_return']:.2%} |",
        f"| CAGR | {t['cagr']:.2%} | {bh['cagr']:.2%} |",
        f"| Ann. volatility | {t['annualized_vol']:.2%} | {bh['annualized_vol']:.2%} |",
        f"| Sharpe | {t['sharpe']:.2f} | {bh['sharpe']:.2f} |",
        f"| Sortino | {t['sortino']:.2f} | {bh['sortino']:.2f} |",
        f"| Calmar | {t['calmar']:.2f} | {bh['calmar']:.2f} |",
        f"| Max drawdown | {t['max_drawdown']:.2%} | {bh['max_drawdown']:.2%} |",
        f"| Win rate | {t['win_rate']:.2%} | {bh['win_rate']:.2%} |",
        f"| End equity (10k start) | {t['end_equity']:,.2f} | {bh['end_equity']:,.2f} |",
        "",
        f"- Trades on test: {res['test_n_trades']} ({res['test_trades_per_year']} / year) · "
        f"cost {r['engine']['cost_per_trade']:.1%} per change",
        f"- Train (same params, diagnostic): Sharpe {tr['sharpe']:.2f}, "
        f"max DD {tr['max_drawdown']:.2%}, total return {tr['total_return']:.2%}",
        "",
        "## Caveats",
        "",
        "- Daily bars only, one asset; no slippage model beyond per-trade cost.",
        "- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.",
        "- Strategy signals use rolling windows ending at the current bar (no look-ahead); "
        "the engine executes at the next bar's open.",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
