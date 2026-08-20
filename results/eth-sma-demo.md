# Backtest: sma_crossover on ETHUSDT

- Source data: binance/ETHUSDT 1d (90 bars, 2026-05-23 → 2026-08-20)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `f469543053bb3d35eb90b00d8aa9f82f1cd630aa` (dirty) · seed 42
- Strategy code hash: `7eb0c841bbda6f62`

## Train/test discipline

- Split: timewise, train 70% (62 bars, 2026-05-23 → 2026-07-23)
- Test: 28 bars (2026-07-24 → 2026-08-20)
- Parameters chosen by grid search on **train Sharpe only**: `{'fast': 3, 'slow': 10, 'short_on_down': True}` (grid: 8 combos; train Sharpe 3.552001)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | 15.89% | 24.71% |
| CAGR | 634.42% | 1878.51% |
| Ann. volatility | 67.07% | 70.55% |
| Sharpe | 3.27 | 4.56 |
| Sortino | 16.23 | 17.24 |
| Calmar | 113.01 | 334.48 |
| Max drawdown | 5.61% | 5.62% |
| Win rate | 57.89% | 59.26% |
| End equity (10k start) | 11,589.28 | 12,458.30 |

- Trades on test: 4 (54.07 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 3.55, max DD 8.46%, total return 34.07%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
