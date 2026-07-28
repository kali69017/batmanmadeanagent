# Trading lessons (cumulative, principle-level only)

- Oversold + negative CMF (distribution) tends to mean continuation, not
  reversal, even when RSI and golden-cross structure look textbook mean-reversion.
  (Seen in: TJX, stopped out -2.02% — CMF was -0.093 at entry, worsened to -0.179.)

- An 'RSI crosses 50 + MACD turns positive' exit condition fires very early in
  a mean-reversion move, often capturing <20% of the distance to the stated
  target. Consider it a signal to tighten the stop and reassess, not automatic
  full-close. (Seen in: XOM, closed +0.53% against a 5.4-8.4% target.)

- Entering a momentum/trend-continuation name after a >20% one-month run
  means buying near the top of a vertical move — expect a near-term give-back
  even if the underlying thesis is fine. (Seen in: DELL, entered after +21.65%
  monthly return, immediately pulled back -1.33%.)

- An unbounded 'RSI > 55' filter for a 'market leaders' screen tends to
  surface late-stage-momentum names (RSI 65-75+) that are 'hold if already in,
  don't chase' — not actionable fresh entries. Needs an upper bound or a
  distance-from-high filter. (Seen in: JNJ RSI 74.2, AAPL RSI 61.7.)

- ADX > 35 with deeply negative CMF makes oversold signals continuation
  patterns, not reversal patterns. (Seen in: PFE rejected twice, fell -6.26%.)

- Sidecar/summary RSI data can be stale by 30+ points (ADBE showed 19.2 in
  sidecar but 62.8 live). Always verify with force_refresh=True before acting.
  (Seen in: ADBE, AAPL stale rejections.)

- When ADX collapses from strong-trend territory (>30) to no-trend (<20)
  within days, the original trend-following thesis is invalidated regardless
  of what other indicators show. Take full profits, don't leave a runner.
  (Seen in: NVDA, ADX 33.3→15.5 in 5 days, remaining half stopped at breakeven.)

- On defensive/low-beta stocks (beta < 0.5), a +10%+ 1-month run vs SPY is
  an unusually large move — take partial or full profit at T1 rather than
  holding for T2, even if the technical structure still looks constructive.
  The low beta means the stock isn't built for sustained momentum runs; the
  reversion pull is stronger. (Seen in: ABBV, +12% 1mo vs SPY, hit T1 +3.66%
  in 1 week, would have given back if held for T2.)

- When a death cross is intact and price breaks below SMA20 with momentum,
  even strong accumulation (CMF +0.138) and heavily washed-out Stoch RSI
  won't save a mean-reversion trade. The structural trend (death cross)
  overrides the tactical signal (oversold + accumulation). Wait for price
  to reclaim SMA20 AND SMA50 before trusting accumulation in death cross
  names. (Seen in: RDDT, stopped out -7.5% and -8.4% across two separate entries.)

- OBV bearish divergence (price up >10% while OBV falls >10% over 6mo) is a
  near-universal rejection signal regardless of bullish price structure. Even
  with golden cross, price above all SMAs, and positive CMF, OBV divergence
  weakens conviction to the point of unreliability. (Seen in: PLD rejected
  7/23, AVGO rejected 7/22, JNJ rejected 7/22.)

- When a scan surfaces 3+ strong candidates all in the same sector (e.g.,
  Technology), sector concentration risk alone can justify passing on the
  2nd and 3rd best names. The incremental benefit of a 3rd tech position
  is lower than the risk of correlated drawdown. (Seen in: 7/23 scan —
  AVGO, AAPL, AMD all Tech; CRM, SNOW already open in Tech.)

- When CMF flips negative on an oversold mean-reversion trade, exit immediately
  rather than waiting for a tightened stop to trigger. The gap risk on a
  deteriorating name is real — price can blow through the stop before you
  can react. The TJX lesson (oversold + negative CMF = continuation) is
  the governing principle. (Seen in: GOOG, CMF flipped from +0.022 to -0.004
  to -0.12, price gapped from $347 to $318 through the $340 tightened stop.)

- When the composite screening score is dominated by 12-1mo momentum (e.g.,
  RIOT +74%, HUT +450%), the resulting top-10 list will be heavy on
  momentum-driven names with toxic fundamentals. The screen is useful for
  surfacing candidates but the composite score alone should never be the
  basis for entry — always cross-reference with the FA deep-dive. A high
  composite score driven by momentum in an unprofitable company is a
  momentum trap, not a buy signal. (Seen in: 7/25 scan — RIOT #1 with 30.9
  composite but -133% margins; HUT #6 with 23.8 but -110% margins.)

- When 6+ of the top 10 screening candidates are in the same sector
  (Technology/Crypto), the screen is telling you the market is narrow, not
  that you should load up on that sector. Use the screen as a starting
  point, then deliberately seek non-correlated candidates from outside
  the top 10. (Seen in: 7/25 scan — 6 of top 10 were Tech/Crypto; had to
  manually pull ABT, PG, UBER to find non-Tech candidates.)

- When ADX is below 20 and MACD is bearish, even strong accumulation
  (CMF +0.165) and a golden cross won't prevent a pullback from turning
  into a stop-out. No trend means no floor — wait for ADX > 20 AND MACD
  bullish before entering trend-following trades, regardless of how good
  the fundamentals look. (Seen in: AMD, stopped out -6.5% — CMF stayed
  positive through the decline but ADX 16.3 + bearish MACD overrode it.)
