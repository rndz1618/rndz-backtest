# Rndz — 30-Day Research Agenda (Quant Research Analyst Onboarding)

**Author:** Quant Research Analyst (agent 036a4949)
**Date:** 2026-08-21
**Status:** Draft for CEO review
**Document key:** roadmap (issue RND-7)

---

## Executive Summary

This agenda proposes a 30-day research program grounded in **honest, reproducible backtesting** against the live data we have, with explicit acknowledgment of data limitations. No profit promises. No cherry-picked windows. Every hypothesis is testable and will be evaluated on the test partition only after parameter selection on the train partition.

---

## 1. Infrastructure Verification (Complete ✅)

| Component | Status | Notes |
|-----------|--------|-------|
| **Data DB** (`/root/rndz-market-data/data/market.db`) | ✅ Verified | 90 daily bars BTCUSDT/ETHUSDT (Binance), 60 daily bars AAPL/MSFT/NVDA (Nasdaq), snapshots for 11 symbols, fundamentals for 5 stocks, clean fetch logs (21 ok, 0 error) |
| **Backtest harness** (`/root/rndz-backtest/`) | ✅ Verified | 18/18 unit tests pass; stdlib-only; train/test timewise split; grid search on train Sharpe only; test evaluated once |
| **Risk gate** (`/root/rndz-market-data/risk/`) | ✅ Verified | 18/18 checks pass on sample report; risk register has 2 entries (RND-REG-001, 002) |
| **Delivery pipeline** (`/root/rndz-delivery/`) | ✅ Verified | Weekly report generates from CoinGecko; watchdog + delivery scripts functional |

---

## 2. Demo Strategy Results — Honest Read

| Strategy | Symbol | Test Return | Buy & Hold (Test) | Verdict |
|----------|--------|-------------|-------------------|---------|
| SMA Crossover (fast=3, slow=10, short_on_down=True) | BTCUSDT | **+5.41%** | +12.85% | **Underperforms** |
| SMA Crossover (fast=3, slow=10, short_on_down=True) | ETHUSDT | **+15.89%** | +24.71% | **Underperforms** |
| Bollinger Mean Reversion (window=20, n_std=1.5, short_upper=True) | BTCUSDT | **–4.49%** | +12.85% | **Fails** |

**Interpretation:** Both demo strategies underperform simple buy & hold on the out-of-sample test window (28 bars ≈ 1 month). The Bollinger mean reversion strategy loses money on test despite strong train Sharpe (3.99) — classic overfit signal on small sample. This is the correct output of a harness that does not sell edges.

---

## 3. Data Coverage Gaps (Blocking for Many Strategies)

| Gap | Impact | Mitigation Path |
|-----|--------|-----------------|
| **Only daily bars** | No intraday mean-reversion, no execution modeling, no 1h/4h regime detection | Add Binance `interval: "1h"` or `"5m"` to ingestion config; Nasdaq is daily-only |
| **Only 90 bars (≈3 months) per crypto** | Train=62, test=28 → statistically thin; cannot do walk-forward or multiple OOS windows | Let ingestion run longer; backfill not allowed (honesty contract); consider external CSV for historical deepening (must be disclosed) |
| **Only 2 crypto assets with full history** | No cross-asset correlation, no sector/portfolio construction | Add more Binance symbols to `config.json` (SOL, BNB, XRP, ADA, DOGE, ARB, LINK, NEAR, AVAX, DOT already in snapshots) |
| **Only 3 stocks with daily bars** | No equity portfolio, no cross-asset crypto/equity | Add MSFT already there; add GOOGL, TSLA, META, AMZN via Nasdaq config |
| **No futures/perpetuals** | Leverage strategies per risk framework (2× cap for top-20 liquid majors) not testable | Binance futures klines endpoint available; add to ingestion when ready |
| **No on-chain / fundamental / sentiment data** | Cannot test on-chain regime filters, valuation models | Future: separate ingest module; not in scope for 30 days |
| **No slippage / fee model beyond fixed cost** | Real execution will be worse | Add dynamic cost model later; current 0.1% per trade is conservative for liquid spot |

---

## 4. Research Hypotheses (Testable, No Profit Promises)

Each hypothesis will be implemented as a strategy function in `strategies/__init__.py`, registered, and backtested with the same train/test discipline. **Success = passes risk gate + honest framing in report.** Not "makes money."

### Week 1: Extend Coverage & Baseline Expansion

| Hypothesis | Description | Test Assets | Timeframe | Success Criteria |
|------------|-------------|-------------|-----------|------------------|
| **H1: More symbols, same strategies** | Run SMA crossover & Bollinger on all available crypto (BTC, ETH, SOL, BNB, XRP, ADA, DOGE, ARB, LINK, NEAR, AVAX, DOT) and stocks (AAPL, MSFT, NVDA, plus newly added) | All 12 crypto + 5 stocks | Daily (existing) | Strategy code hash recorded; test metrics published for every asset; honest comparison vs buy & hold |
| **H2: Parameter stability across assets** | Do the *same* params (fast=3, slow=10) chosen on BTC train generalize to ETH/SOL/etc without re-fitting? | BTC (train) → ETH, SOL, BNB (test) | Daily | Out-of-sample test without re-optimization; report parameter decay |
| **H3: Volatility-scaled position sizing** | Scale position by inverse realized vol (risk framework §2.1); compare fixed-fractional vs vol-scaled equity curves | BTC, ETH | Daily | Risk-adjusted metrics (Sharpe, Calmar) improve without increasing max DD beyond 20% strategy stop |

### Week 2: New Strategy Families (Pure Functions, No Look-Ahead)

| Hypothesis | Description | Rationale | Test Assets | Success Criteria |
|------------|-------------|-----------|-------------|------------------|
| **H4: Donchian channel breakout** | Long on 20-day high, short on 20-day low (optional), flat otherwise. Classic trend-following. | Different logic from SMA (price-level vs moving avg) | BTC, ETH, AAPL, NVDA | Train/test discipline; compare vs SMA & buy & hold |
| **H5: RSI mean reversion (2-period)** | Long when RSI(2) < 10, exit when RSI(2) > 90; short symmetric (optional). Short-term mean reversion. | Tests if very short-term reversion survives costs | BTC, ETH | Must beat buy & hold on test *after costs*; otherwise documented as failure |
| **H6: Dual-momentum (absolute + relative)** | Hold asset only if 12M momentum > 0 AND asset beats cash (or BTC for crypto); else flat. | Gary Antonacci dual momentum; regime filter | BTC vs ETH (crypto), AAPL vs MSFT (equity) | Test on available lookback (only 3M data → truncated; must disclose) |

### Week 3: Risk Framework Integration & Portfolio Construction

| Hypothesis | Description | Rationale | Test Assets | Success Criteria |
|------------|-------------|-----------|-------------|------------------|
| **H7: Risk-budgeted multi-asset portfolio** | Combine 3–5 uncorrelated strategies × assets; size each by fixed-fractional risk budget (2% per position, 20% portfolio max per §2.1). Rebalance monthly. | Tests portfolio-level risk framework in backtest | BTC, ETH, AAPL, MSFT, NVDA | Portfolio passes gate checks A1–A6; max DD < 15%; concentration limits respected |
| **H8: Correlation-aware concentration guardrail** | Implement §2.4 correlated basket guardrail (BTC+ETH+ETH-eco ≤ 50%) in backtest engine; measure portfolio vol vs 30% cap (§2.2) | Validates risk framework programmatically | Same as H7 | Gate script `risk_gate.py` can ingest backtest output and PASS |
| **H9: Walk-forward validation (expanding window)** | Re-optimize params every N bars on expanding train window; test on next M bars. Compare to single split. | Addresses overfitting concern on small sample | BTC, ETH | Document parameter drift; report if walk-forward degrades vs single split |

### Week 4: Reporting, Delivery & Handoff

| Hypothesis | Description | Deliverable |
|------------|-------------|-------------|
| **H10: Upgrade weekly report with research content** | Replace CoinGecko-only price table with: (a) backtest metric summary for current strategies, (b) risk gate status, (c) data freshness audit, (d) open research questions | `rndz_report.py` extended; weekly Discord delivery includes real research |
| **H11: Automated risk gate on every backtest run** | CI-style: `run_backtest.py` output JSON → feed to `risk_gate.py` (extend gate to read backtest JSON) → block delivery if FAIL | Gate integrated in delivery pipeline |
| **H12: Research log / decision register** | Append every tested hypothesis + result (PASS/FAIL/INCONCLUSIVE) to `risk/gate-run-log.md` or new `research-log.md` | Auditable trail; CEO can review |

---

## 5. Proposed 30-Day Sprint Plan

| Week | Focus | Outputs |
|------|-------|---------|
| **Week 1 (Aug 21–27)** | Data expansion + baseline | `config.json` updated with 10+ crypto symbols; ingestion cron running; H1–H3 backtests complete; results in `results/` |
| **Week 2 (Aug 28–Sep 3)** | New strategy families | H4–H6 implemented, registered, backtested; honest markdown reports for each |
| **Week 3 (Sep 4–10)** | Portfolio + risk integration | H7–H9 backtests; `risk_gate.py` extended to consume backtest JSON; portfolio reports |
| **Week 4 (Sep 11–17)** | Delivery upgrade + documentation | H10–H12 live; weekly report includes research; research agenda v2 proposed |

**Buffer (Sep 18–20):** CEO review, adjustments, finalize v2 agenda.

---

## 6. Resource Constraints & Guardrails

- **Compute:** 2GB ARM64 SBC — backtests are fast (<2s per run), but no pandas/numpy. All strategies must stay stdlib.
- **Heavy compute OFF-device:** Any ML, large grid searches, or multi-year walk-forwards go to cloud runner (Hugging Face Space pattern used elsewhere in company).
- **No backfilling ever:** Data gaps are documented, not filled.
- **Risk gate is fail-closed:** Any recommendation that fails mandatory checks (A1–A6, B1–B5, C1–C5, D1–D3) does not ship.
- **Honest framing mandatory:** Every report carries uncertainty labels (🟢/🟡/🟠), data source disclosure, and "not financial advice."

---

## 7. Open Questions for CEO / Founding Engineer

1. **Historical depth:** Should we acquire 1–2 years of daily OHLCV from a reputable vendor (disclosed) to enable walk-forward? Current 90 bars is a demo sample only.
2. **Intraday data:** Enable Binance 1h/5m ingestion? Increases DB size ~24× but enables execution research.
3. **Futures/perp data:** Add Binance USDⓈ-M perpetual klines for leverage strategy research (per risk framework §2.3)?
4. **Stock universe expansion:** Add GOOGL, TSLA, META, AMZN, AVGO to Nasdaq config for equity diversification?
5. **Report audience:** Weekly report currently goes to Discord. Should we also publish to a static site (GitHub Pages) or Notion for client access?
6. **Success metric for this role:** Is "number of strategies tested with honest results" the right KPI, or should we track "strategies passing risk gate"?

---

## 8. Acceptance Criteria for This Agenda

- [ ] CEO reviews and approves / adjusts hypothesis list
- [ ] Founding Engineer confirms data expansion plan (config.json changes, ingestion cron)
- [ ] First backtest of H1 (expanded symbols) runs and produces reproducible JSON + MD
- [ ] Risk gate extended to consume backtest JSON (Founding Engineer + Quant collaboration)
- [ ] Weekly report updated to include research section (delivery pipeline)

---

## Appendix A: Current Data Inventory (for reference)

```
Candles (daily OHLCV):
  binance  BTCUSDT  1d  n=90  (2026-05-23 → 2026-08-20)
  binance  ETHUSDT  1d  n=90  (2026-05-23 → 2026-08-20)
  nasdaq   AAPL      1d  n=60  (2026-05-26 → 2026-08-19)
  nasdaq   MSFT      1d  n=60  (2026-05-26 → 2026-08-19)
  nasdaq   NVDA      1d  n=60  (2026-05-26 → 2026-08-19)

Snapshots (latest price/volume):
  binance: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, ADAUSDT
  nasdaq:  AAPL, MSFT, NVDA, META, AMZN, TSLA

Fundamentals (sector, cap, yield, 52wk):
  AAPL, MSFT, NVDA, META, AMZN

Sources health: binance ✅, nasdaq ✅ (0 failures)
```

---

## Appendix B: Risk Framework Quick Reference (from RISK_FRAMEWORK.md)

- **Position risk budget:** 2% per position, 20% portfolio max
- **Vol adjustment:** × (40% / realized_vol) when 20d vol > 40% p.a.
- **Max DD stops:** 15% portfolio / 20% strategy
- **Portfolio vol ceiling:** 30% p.a.
- **Leverage caps:** Spot 1×, Perp 2× (top-20 liquid), Equity margin 1.5×
- **Concentration:** 25% single asset, 40% sector/narrative, 50% correlated basket (BTC+ETH+eco)
- **Gate:** 18 mandatory checks (A1–A6, B1–B5, C1–C5, D1–D3); fail-closed

---

*End of Research Agenda v1.0 — Ready for CEO review.*