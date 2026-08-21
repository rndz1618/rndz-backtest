# Backtest: sma_crossover on NVDA

- Source data: nasdaq/NVDA 1d (60 bars, 2026-05-26 → 2026-08-19)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `c93aa6d350c61459fa50d19dd11c9fa9e639f987` (dirty) · seed 42
- Strategy code hash: `7eb0c841bbda6f62`

## Train/test discipline

- Split: timewise, train 70% (42 bars, 2026-05-26 → 2026-07-24)
- Test: 18 bars (2026-07-27 → 2026-08-19)
- Parameters chosen by grid search on **train Sharpe only**: `{'fast': 10, 'slow': 30, 'short_on_down': False}` (grid: 8 combos; train Sharpe 0.345899)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | 0.00% | 11.57% |
| CAGR | 0.00% | 949.08% |
| Ann. volatility | 0.00% | 42.17% |
| Sharpe | 0.00 | 5.79 |
| Sortino | 0.00 | 10.08 |
| Calmar | 0.00 | 267.11 |
| Max drawdown | 0.00% | 3.55% |
| Win rate | 0.00% | 52.94% |
| End equity (10k start) | 10,000.00 | 11,145.77 |

- Trades on test: 0 (0.0 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 0.35, max DD 2.46%, total return 0.37%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
