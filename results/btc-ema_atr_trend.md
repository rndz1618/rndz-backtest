# Backtest: ema_atr_trend on BTCUSDT

- Source data: binance/BTCUSDT 1d (90 bars, 2026-05-23 → 2026-08-20)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `58366be2366bc9f569be3c7f4d54c40727167d50` (dirty) · seed 42
- Strategy code hash: `2d2de74cd57caad2`

## Train/test discipline

- Split: timewise, train 70% (62 bars, 2026-05-23 → 2026-07-23)
- Test: 28 bars (2026-07-24 → 2026-08-20)
- Parameters chosen by grid search on **train Sharpe only**: `{'fast_ema': 5, 'slow_ema': 13, 'atr_window': 10, 'vol_threshold': 0.6, 'vol_target': 0.4}` (grid: 108 combos; train Sharpe 1.143314)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | 4.94% | 12.85% |
| CAGR | 91.81% | 412.44% |
| Ann. volatility | 27.01% | 36.96% |
| Sharpe | 2.54 | 4.60 |
| Sortino | 11.09 | 10.86 |
| Calmar | 40.03 | 104.70 |
| Max drawdown | 2.29% | 3.94% |
| Win rate | 33.33% | 59.26% |
| End equity (10k start) | 10,493.60 | 11,273.52 |

- Trades on test: 4 (54.07 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 1.14, max DD 2.85%, total return 2.99%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
