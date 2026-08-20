# Backtest: sma_crossover on BTCUSDT

- Source data: binance/BTCUSDT 1d (90 bars, 2026-05-23 → 2026-08-20)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `f469543053bb3d35eb90b00d8aa9f82f1cd630aa` · seed 42
- Strategy code hash: `7eb0c841bbda6f62`

## Train/test discipline

- Split: timewise, train 70% (62 bars, 2026-05-23 → 2026-07-23)
- Test: 28 bars (2026-07-24 → 2026-08-20)
- Parameters chosen by grid search on **train Sharpe only**: `{'fast': 3, 'slow': 10, 'short_on_down': True}` (grid: 8 combos; train Sharpe 1.103333)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | 5.41% | 12.85% |
| CAGR | 103.73% | 412.44% |
| Ann. volatility | 33.98% | 36.96% |
| Sharpe | 2.25 | 4.60 |
| Sortino | 6.03 | 10.86 |
| Calmar | 18.06 | 104.70 |
| Max drawdown | 5.74% | 3.94% |
| Win rate | 42.11% | 59.26% |
| End equity (10k start) | 10,540.51 | 11,273.52 |

- Trades on test: 4 (54.07 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 1.10, max DD 13.07%, total return 5.83%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
