# rndz-backtest

Lightweight, honest backtesting harness for **Rndz** — runs strategies against
historical OHLCV data stored by the ingestion pipeline
([rndz-market-data](https://github.com/rndz1618/rndz-market-data)).

Optimized for the same constraints as the rest of the stack: **Python stdlib
only, SQLite input, ~no memory footprint** — runs fine on a 2GB ARM64 SBC or a
tiny cloud runner. No pandas, no numpy, no backtrader.

## What it does

```
market.db (candles table)
      │
      ▼
run_backtest.py ──train/test split──▶ grid search params on TRAIN only
      │                                (best Sharpe on train partition)
      ▼
      └──────────────▶ run strategy once on TEST partition (never touched
                       during fitting) → returns, drawdown, Sharpe, Sortino,
                       Calmar, win rate, profit factor
      │
      ▼
results/<run>.json  (full reproducible report)
results/<run>.md    (human-readable summary)
```

## Quick start

```bash
git clone https://github.com/rndz1618/rndz-backtest.git
cd rndz-backtest

python3 -m unittest discover -s tests   # run the test suite

# Demo backtest: BTCUSDT daily bars from the market-data DB
python3 run_backtest.py \
    --db /root/rndz-market-data/data/market.db \
    --symbol BTCUSDT --source binance --strategy sma_crossover \
    --train-frac 0.7 --cost 0.001 --seed 42 \
    --out results/btc-sma-demo.json --md results/btc-sma-demo.md

python3 run_backtest.py --list                  # strategies
python3 run_backtest.py --symbols --db <path>   # what data is in the DB
```

## Honesty contract (train/test discipline)

- Rows are split **timewise** (no shuffling): the first 70% is train, the last
  30% is test.
- Strategy parameters are chosen by grid search on the **train partition
  only** (best Sharpe). The test partition is evaluated **exactly once** with
  those parameters.
- Every strategy is a pure function `(rows, params) -> positions`. Rolling
  windows end at the current bar, so signals never use future data.
- The engine executes at the **next bar's open** after a signal change — no
  look-ahead, no claiming overnight gaps. P&L: open→close on the first day of a
  position, close→close afterwards. Shorts mirror the move.
- Costs: `--cost 0.001` = 0.1% per position change (entry and exit).
- Every run records: seed, git revision, strategy code hash, DB path, the exact
  SQL data contract, and the full param grid searched — so any result can be
  regenerated.

## Strategies

| Strategy | Idea | Params |
|---|---|---|
| `sma_crossover` | fast/slow SMA trend following (long on uptrend, optional short) | `fast`, `slow`, `short_on_down` |
| `bollinger_mean_reversion` | buy dips below lower band, optional short on upper band | `window`, `n_std`, `short_upper` |
| `buy_and_hold` | benchmark every strategy must be compared against | — |

To add one: write a pure function in `strategies/__init__.py`, register it in
`STRATEGIES`, and add its param grid in `run_backtest.py`.

## Published demo results

| Run | Symbol | Test return | Test Sharpe | Test max DD | Buy & hold (test) |
|---|---|---|---|---|---|
| [BTC SMA crossover](results/btc-sma-demo.md) | BTCUSDT | +4.75% | 2.06 | 5.74% | +12.14% |
| [ETH SMA crossover](results/eth-sma-demo.md) | ETHUSDT | +14.37% | 3.02 | 2.50% | +23.07% |

Honest read: on this 90-bar sample both strategies **underperform buy & hold**
in the test window. That is the correct output of a harness that is not trying
to sell you an edge — it is reporting what happened. The demo is meant to
validate the pipeline, not to suggest these strategies are profitable.

Caveats: daily bars only, one asset per run, no slippage model beyond per-trade
cost, small sample (90 bars ≈ 3 months). Not investment advice.

## Layout

```
backtest/engine.py    event-loop engine, P&L, cost model
backtest/metrics.py   returns/drawdown/Sharpe/Sortino/Calmar/win rate
backtest/splits.py    timewise train/test splits
backtest/loader.py    SQLite reader for rndz-market-data
strategies/           strategy registry
tests/                unit tests (metrics math, splits, engine P&L, no-look-ahead)
results/              generated demo reports
run_backtest.py       CLI
```

## License

MIT
