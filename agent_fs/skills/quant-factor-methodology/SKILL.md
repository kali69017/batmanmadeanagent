---
name: quant-factor-methodology
description: Use when the user asks about the quant/composite score, "alpha score", short-squeeze setups, or any request to invent, name, or combine metrics that don't exist as real tools. Explains what get_quant_factors actually measures and how to handle requests for metrics that don't exist.
---

# Quant Factor Methodology

## get_quant_factors
`get_quant_factors` computes a real, documented 0-100 composite score from:
- **Value**: PEG ratio, Price/FCF
- **Momentum**: 12-1 month momentum, volume-confirmed breakout
- **Quality**: revenue growth inflection, debt/equity

This is a simple heuristic score, **NOT a backtested model**. Always:
- Show the factor breakdown alongside the score, never just the number.
- Explicitly state it should inform judgment rather than be treated as a
  standalone buy/sell signal.

## Short-squeeze data
Short % of float and short ratio are frequently unavailable or stale
(Yahoo reports it ~2 weeks delayed).
- If present: flag the staleness explicitly.
- If absent: say so plainly. Do NOT treat missing short-interest data as
  "no squeeze risk" — absence of data is not evidence of absence of risk.

## Requests for metrics that don't exist
If a requested metric doesn't exist as a tool or field (e.g. a user-invented
name like "alpha_score"):
1. State plainly that no such metric exists in your toolset.
2. Offer the closest real metrics you DO have (Sharpe, Sortino, excess
   return, the quant factor score, etc.) as separate reported values.
3. If you construct any informal combined ranking from those, describe it
   honestly as a qualitative judgment call across multiple metrics — never
   as a named statistical procedure you didn't actually execute (e.g. do
   not claim "z-score normalization" when you just eyeballed and ranked
   raw numbers).
