# Backtest: bollinger_mean_reversion on ETHUSDT

- Source data: binance/ETHUSDT 1d (90 bars, 2026-05-23 → 2026-08-20)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `c93aa6d350c61459fa50d19dd11c9fa9e639f987` (dirty) · seed 42
- Strategy code hash: `e7af9fdcfedb4a5a`

## Train/test discipline

- Split: timewise, train 70% (62 bars, 2026-05-23 → 2026-07-23)
- Test: 28 bars (2026-07-24 → 2026-08-20)
- Parameters chosen by grid search on **train Sharpe only**: `{'window': 30, 'n_std': 2.0, 'short_upper': True}` (grid: 18 combos; train Sharpe 2.351358)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | 0.00% | 24.71% |
| CAGR | 0.00% | 1878.51% |
| Ann. volatility | 0.00% | 70.55% |
| Sharpe | 0.00 | 4.56 |
| Sortino | 0.00 | 17.24 |
| Calmar | 0.00 | 334.48 |
| Max drawdown | 0.00% | 5.62% |
| Win rate | 0.00% | 59.26% |
| End equity (10k start) | 10,000.00 | 12,458.30 |

- Trades on test: 0 (0.0 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 2.35, max DD 0.10%, total return 2.57%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
