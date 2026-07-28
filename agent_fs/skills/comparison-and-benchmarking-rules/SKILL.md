---
name: comparison-and-benchmarking-rules
description: Use when comparing two or more watchlist symbols, ranking symbols, asking "which is the better investment", checking analyst price targets, or asking whether a stock's move is broad-market-driven vs stock-specific. Explains which comparison tool and metric to use and a known upside/downside calculation bug to avoid.
---

# Comparison & Benchmarking Rules

## Risk-adjusted vs. raw return
When the user is asking "which is the better investment" (as opposed to
"which went up the most"), prefer risk-adjusted metrics — Sharpe, Sortino,
Calmar via `get_risk_adjusted_returns`, or `compare_symbols` with those
metrics — over raw return % alone. Raw return ranks by magnitude only;
risk-adjusted ranking accounts for how much pain (volatility, drawdown) was
required to get there.

## Market-relative performance
Use `get_relative_strength` to distinguish genuine stock-specific
outperformance from a broad market rally before crediting a rally to
company-specific strength.

- Valid benchmarks for `get_relative_strength`: `SPY`, `QQQ`, `DIA`, `IWM`
  only.
- Do NOT call `get_price_data`, `get_technicals`, or other per-symbol tools
  on a benchmark ticker — `get_relative_strength` already returns
  `benchmark_return_pct` directly in its output.

## `compare_symbols` valid metrics
`period_return_pct`, `annualized_volatility_pct`, `trailingPE`,
`forwardPE`, `dividendYield`, `revenueGrowth`, `rsi_14`,
`macd_histogram`, `sharpe_ratio`, `sortino_ratio`, `max_drawdown_pct`,
`calmar_ratio`, `excess_return_pct`, `composite_score`.

## Analyst price targets — known bug, do not repeat it
Always use the pre-computed `upside_to_mean_target_pct` /
`upside_to_high_target_pct` / `upside_to_low_target_pct` fields from
`get_fundamentals` output directly.

**Never recompute upside/downside from raw target and price values
yourself.** This previously caused a direction-of-division error —
reporting a -4% downside as +4% upside for CAT. Trust the pre-computed
field, don't re-derive it.

## Time window honesty
If a requested time window exceeds the actual available history for a
symbol (e.g. asking for 5-year metrics on a stock that IPO'd 2-3 years
ago), explicitly state the actual available window you used instead of
silently reporting numbers as if the requested window was satisfied — e.g.
"ARM has ~3.3 years of trading history; metrics below cover that full
period, not literally 5 years." Check the `actual_years_used` field in
`get_risk_adjusted_returns` output for the exact number.
