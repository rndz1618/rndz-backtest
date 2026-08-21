# Backtest: ema_atr_trend on NVDA

- Source data: nasdaq/NVDA 1d (60 bars, 2026-05-26 → 2026-08-19)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `58366be2366bc9f569be3c7f4d54c40727167d50` (dirty) · seed 42
- Strategy code hash: `2d2de74cd57caad2`

## Train/test discipline

- Split: timewise, train 70% (42 bars, 2026-05-26 → 2026-07-24)
- Test: 18 bars (2026-07-27 → 2026-08-19)
- Parameters chosen by grid search on **train Sharpe only**: `{'fast_ema': 5, 'slow_ema': 13, 'atr_window': 10, 'vol_threshold': 0.6, 'vol_target': 0.4}` (grid: 108 combos; train Sharpe 3.826894)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | -3.43% | 11.57% |
| CAGR | -52.70% | 949.08% |
| Ann. volatility | 11.50% | 42.17% |
| Sharpe | -6.45 | 5.79 |
| Sortino | -6.28 | 10.08 |
| Calmar | -15.34 | 267.11 |
| Max drawdown | 3.44% | 3.55% |
| Win rate | 16.67% | 52.94% |
| End equity (10k start) | 9,657.30 | 11,145.77 |

- Trades on test: 1 (21.47 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 3.83, max DD 0.39%, total return 6.76%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
