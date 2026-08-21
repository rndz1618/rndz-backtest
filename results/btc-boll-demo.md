# Backtest: bollinger_mean_reversion on BTCUSDT

- Source data: binance/BTCUSDT 1d (90 bars, 2026-05-23 → 2026-08-20)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `c93aa6d350c61459fa50d19dd11c9fa9e639f987` (dirty) · seed 42
- Strategy code hash: `e7af9fdcfedb4a5a`

## Train/test discipline

- Split: timewise, train 70% (62 bars, 2026-05-23 → 2026-07-23)
- Test: 28 bars (2026-07-24 → 2026-08-20)
- Parameters chosen by grid search on **train Sharpe only**: `{'window': 20, 'n_std': 1.5, 'short_upper': True}` (grid: 18 combos; train Sharpe 3.986134)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | -4.49% | 12.85% |
| CAGR | -46.25% | 412.44% |
| Ann. volatility | 16.14% | 36.96% |
| Sharpe | -3.76 | 4.60 |
| Sortino | -3.76 | 10.86 |
| Calmar | -10.30 | 104.70 |
| Max drawdown | 4.49% | 3.94% |
| Win rate | 0.00% | 59.26% |
| End equity (10k start) | 9,551.13 | 11,273.52 |

- Trades on test: 1 (13.52 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 3.99, max DD 0.87%, total return 5.19%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
