# Backtest: rsi_mean_reversion on AAPL

- Source data: nasdaq/AAPL 1d (60 bars, 2026-05-26 → 2026-08-19)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `c93aa6d350c61459fa50d19dd11c9fa9e639f987` (dirty) · seed 42
- Strategy code hash: `9df4476a9986dfa4`

## Train/test discipline

- Split: timewise, train 70% (42 bars, 2026-05-26 → 2026-07-24)
- Test: 18 bars (2026-07-27 → 2026-08-19)
- Parameters chosen by grid search on **train Sharpe only**: `{'window': 10, 'oversold': 35, 'overbought': 65, 'short_overbought': False}` (grid: 54 combos; train Sharpe 4.904154)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | -1.01% | -6.82% |
| CAGR | -19.54% | -78.07% |
| Ann. volatility | 7.34% | 41.05% |
| Sharpe | -2.92 | -3.49 |
| Sortino | -3.64 | -3.86 |
| Calmar | -10.36 | -7.02 |
| Max drawdown | 1.89% | 11.12% |
| Win rate | 25.00% | 52.94% |
| End equity (10k start) | 9,899.26 | 9,308.39 |

- Trades on test: 2 (42.94 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 4.90, max DD 1.52%, total return 8.40%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
