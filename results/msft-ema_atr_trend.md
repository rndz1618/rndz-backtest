# Backtest: ema_atr_trend on MSFT

- Source data: nasdaq/MSFT 1d (60 bars, 2026-05-26 → 2026-08-19)
- Contract: `candles(source,symbol,interval,open_time,open,high,low,close,volume) from rndz-market-data SQLite`
- Harness: v0.1.0 · git `58366be2366bc9f569be3c7f4d54c40727167d50` (dirty) · seed 42
- Strategy code hash: `2d2de74cd57caad2`

## Train/test discipline

- Split: timewise, train 70% (42 bars, 2026-05-26 → 2026-07-24)
- Test: 18 bars (2026-07-27 → 2026-08-19)
- Parameters chosen by grid search on **train Sharpe only**: `{'fast_ema': 5, 'slow_ema': 13, 'atr_window': 10, 'vol_threshold': 0.7, 'vol_target': 0.3}` (grid: 108 combos; train Sharpe 1.104918)
- Test partition evaluated exactly once with those parameters.

## Test metrics (strategy vs buy & hold)

| Metric | Strategy | Buy & hold |
|---|---|---|
| Total return | -1.91% | 23.18% |
| CAGR | -33.96% | 8695.29% |
| Ann. volatility | 15.13% | 78.69% |
| Sharpe | -2.67 | 6.07 |
| Sortino | -2.85 | 25.52 |
| Calmar | -10.21 | 1711.53 |
| Max drawdown | 3.33% | 5.08% |
| Win rate | 50.00% | 64.71% |
| End equity (10k start) | 9,808.64 | 12,306.08 |

- Trades on test: 1 (21.47 / year) · cost 0.1% per change
- Train (same params, diagnostic): Sharpe 1.10, max DD 4.70%, total return 2.19%

## Caveats

- Daily bars only, one asset; no slippage model beyond per-trade cost.
- 90 bars is a small sample; results are a demo of the harness, not a tradable edge.
- Strategy signals use rolling windows ending at the current bar (no look-ahead); the engine executes at the next bar's open.
