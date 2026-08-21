# Backtest: ema_atr_trend on ETHUSDT

- Source data: binance/ETHUSDT 1d (90 bars, 2026-05-23 → 2026-08-20)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `58366be2366bc9f569be3c7f4d54c40727167d50` (dirty) · seed 42
- Strategy code hash: `2d2de74cd57caad2`

## Train/test discipline

- Split: timewise, train 70% (62 bars, 2026-05-23 → 2026-07-23)
- Test: 28 bars (2026-07-24 → 2026-08-20)
- Parameters chosen by grid search on **train Sharpe only**: `{'fast_ema': 12, 'slow_ema': 26, 'atr_window': 10, 'vol_threshold': 0.6, 'vol_target': 0.4}` (grid: 108 combos; train Sharpe 2.378134)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | 17.23% | 24.71% |
| CAGR | 757.64% | 1878.51% |
| Ann. volatility | 63.80% | 70.55% |
| Sharpe | 3.65 | 4.56 |
| Sortino | 634.14 | 17.24 |
| Calmar | 7576.39 | 334.48 |
| Max drawdown | 0.10% | 5.62% |
| Win rate | 50.00% | 59.26% |
| End equity (10k start) | 11,723.01 | 12,458.30 |

- Trades on test: 2 (27.04 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 2.38, max DD 2.89%, total return 7.74%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
