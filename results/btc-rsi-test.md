# Backtest: rsi_mean_reversion on BTCUSDT

- Source data: binance/BTCUSDT 1d (90 bars, 2026-05-23 → 2026-08-20)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `c93aa6d350c61459fa50d19dd11c9fa9e639f987` (dirty) · seed 42
- Strategy code hash: `9df4476a9986dfa4`

## Train/test discipline

- Split: timewise, train 70% (62 bars, 2026-05-23 → 2026-07-23)
- Test: 28 bars (2026-07-24 → 2026-08-20)
- Parameters chosen by grid search on **train Sharpe only**: `{'window': 20, 'oversold': 30, 'overbought': 65, 'short_overbought': False}` (grid: 54 combos; train Sharpe 4.443977)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | 0.00% | 12.85% |
| CAGR | 0.00% | 412.44% |
| Ann. volatility | 0.00% | 36.96% |
| Sharpe | 0.00 | 4.60 |
| Sortino | 0.00 | 10.86 |
| Calmar | 0.00 | 104.70 |
| Max drawdown | 0.00% | 3.94% |
| Win rate | 0.00% | 59.26% |
| End equity (10k start) | 10,000.00 | 11,273.52 |

- Trades on test: 0 (0.0 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 4.44, max DD 0.10%, total return 4.87%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
