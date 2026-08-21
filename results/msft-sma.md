# Backtest: sma_crossover on MSFT

- Source data: nasdaq/MSFT 1d (60 bars, 2026-05-26 → 2026-08-19)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `c93aa6d350c61459fa50d19dd11c9fa9e639f987` (dirty) · seed 42
- Strategy code hash: `7eb0c841bbda6f62`

## Train/test discipline

- Split: timewise, train 70% (42 bars, 2026-05-26 → 2026-07-24)
- Test: 18 bars (2026-07-27 → 2026-08-19)
- Parameters chosen by grid search on **train Sharpe only**: `{'fast': 3, 'slow': 10, 'short_on_down': True}` (grid: 8 combos; train Sharpe 1.479494)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | -0.75% | 23.18% |
| CAGR | -15.01% | 8695.29% |
| Ann. volatility | 15.83% | 78.69% |
| Sharpe | -0.95 | 6.07 |
| Sortino | -1.34 | 25.52 |
| Calmar | -5.57 | 1711.53 |
| Max drawdown | 2.69% | 5.08% |
| Win rate | 33.33% | 64.71% |
| End equity (10k start) | 9,924.56 | 12,306.08 |

- Trades on test: 2 (42.94 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 1.48, max DD 9.64%, total return 5.46%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
