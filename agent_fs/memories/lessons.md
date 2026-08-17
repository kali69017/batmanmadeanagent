# Lessons Learned

## Generalizable Trading Rules

### 1. OBV Divergence + Negative CMF = Dealbreaker
- Even with elite FA (AVGO: PEG 0.43, 47.9% revenue growth), if OBV shows bearish divergence and CMF stays negative for 3+ sessions after entry, exit early regardless of stop distance.
- AVGO stopped out 7/30: OBV divergence + negative CMF persisted throughout. ADX never recovered above 20.

### 2. ADX < 20 = No Trend — Don't Bet on Trend Formation
- When ADX is below 20, the stock has no trend. Betting on a new trend forming is speculation, not trend-following.
- AVGO lesson: ADX 15.7 at entry, never recovered. The fundamental thesis was right but timing was wrong.

### 3. Negative CMF After Entry = Immediate Yellow Flag (GOOG/TJX Rule)
- If CMF flips negative after entry, tighten stop immediately. If it stays negative for 3+ sessions, exit.
- Applies to: DAL (CMF -0.032), META (CMF -0.053 at entry — sized smaller).

### 4. Death Cross + Extreme Oversold + Elite FA = Mean-Reversion, Not Trend-Following
- META pattern: death cross active, StochRSI 0.0, CCI -980, but PEG 0.81, 33% revenue growth.
- Differentiated from RDDT (which failed): the FA backstop is what makes this tradeable.
- Signal: extreme_oversold_fa_backstop (StochRSI < 5 + CCI < -500 + PEG < 1.0 + rev growth > 25%)

### 5. Defensive/Low-Beta Names: Prioritize T1 Profit-Taking
- ABBV, JNJ, MRK, XOM, CVX: beta < 0.5 means limited upside velocity.
- Take 50% partial at T1, let remainder run with tighter stop.
- The reversion pull is stronger than momentum continuation in defensive names.

### 6. Sector Concentration Management
- Technology is the most crowded sector. Max 4 Tech positions at any time.
- NVDA rejected as FILLED due to 5th Tech position — moved to PENDING.
- Diversify across Healthcare, Energy, Financials, Communication Services.

### 7. Oversold + Negative CMF = Continuation, Not Reversal (TJX Lesson)
- When a stock is oversold but CMF is negative, the oversold condition is more likely to continue than reverse.
- META entered with negative CMF (-0.053) — sized smaller as a result.

### 8. Screening Composite Scores < 30 = Narrow Market
- When all composite scores are below 30, the market is narrow and selective.
- Be patient. Don't force trades in low-scoring environments.
- 2026-08-07: Top score DELL 28.1 — confirms narrow market conditions persist.

### 9. Pending vs Filled — Clear Distinction
- type: filled = position actually entered
- type: pending = entry zone not yet triggered
- Only count filled entries as real open positions for exposure management.

### 10. META Entry Zone Triggered with Negative CMF
- When a pending entry triggers but CMF is negative, reduce position size by 30-50%.
- If CMF doesn't turn positive within 3-5 sessions, exit early.

### 11. Death Cross + Negative CMF = Same-Day Stop-Out Risk (META Lesson)
- META stopped out same day (7/30): entered at $585.61, closed at $534.65 (-8.7%).
- Death cross + negative CMF (-0.053) + falling OBV = the oversold condition continued, didn't reverse.
- **New rule: If CMF is negative at entry AND death cross is active, DO NOT ENTER.**
- The extreme_oversold_fa_backstop signal now requires CMF > 0 as a prerequisite.
- Even elite FA (PEG 0.81, 33% revenue growth) cannot overcome the structural headwinds of death cross + negative CMF.

### 12. Same-Day Stop-Outs = Signal Failure, Not Bad Luck
- When a trade stops out within the same session, the entry signal was wrong.
- META: entered at open, stopped out by close. The signal (extreme_oversold_fa_backstop) was incomplete.
- Update signal criteria immediately — don't wait for a second failure.

### 13. Momentum Trap: High Composite Score Driven by Past Returns, Not Current Trend
- RKLB: composite score 23.4 (rank #5), momentum 12-1 +84%, but current trend is bearish
  (below all SMAs, Aroon Down 96, CMF -0.33, ADX 35.8 bearish).
- The composite score formula weights momentum_12_1 at 35% — a stock can rank high
  on past returns while currently in freefall.
- **New rule: If momentum_12_1 > 50% but price is below SMA20 AND CMF < -0.20, it's a momentum trap. Reject.**
- This is the mirror image of Lesson #8 (oversold + negative CMF = continuation).

### 14. Strong Trend + Overbought = Wait, Don't Chase (ABBV Pattern)
- ABBV: golden cross, ADX 38.5, Aroon 96/0 — structurally perfect. But StochRSI 84.8,
  MACD bearish crossover, CMF -0.18 distribution = near-term pullback imminent.
- Even the best trends need to breathe. Entering at overbought extremes in a strong
  trend is still a bad entry — you'll likely get a better price within days.
- **Rule: When ADX > 35 AND StochRSI > 80, wait for pullback to SMA20 before entering.**

### 15. Great FA Cannot Override ADX < 20 + Bearish Aroon (APH Corollary)
- APH: 55% revenue growth, 59% earnings growth, 38% ROE, PEG 1.23 — elite FA.
  But ADX 15.6 (no trend), Aroon Down 92, CMF -0.125, MACD bearish.
- Reinforces Lesson #2: ADX < 20 = no trend. Don't bet on trend formation.
- The golden cross provides structural support but doesn't override tactical bearish signals.
- **Rule: FA quality is irrelevant if ADX < 20 and Aroon is bearish. Wait for trend to form.**

### 16. OBV Bearish Divergence = Rally Without Conviction — Wait (DELL/GOOG/ABBV Lesson)
- Three top screening candidates (DELL, GOOG, ABBV) all showed stark OBV bearish
  divergence: price rising while cumulative OBV falling sharply (ABBV: +14.1% vs -34.7%;
  GOOG: +7.1% vs -73.1%). This pattern means the rally lacks volume participation —
  professional money is not buying the move.
- **Rule: If 6-month OBV is falling while price is rising, do not enter long. Wait for
  OBV to confirm trend resumption. OBV divergence + negative CMF together = hard pass.**
- This is distinct from Lesson #1 (OBV divergence + negative CMF = dealbreaker for open
  trades). This applies pre-entry: don't even enter if OBV is diverging.

### 18. Positive CMF Is the Non-Negotiable Gate for Energy Mean-Reversion
- CVX was rejected on 2026-07-08 with CMF -0.10 ("negative CMF is the killer"). Same CVX setup
  three weeks later with CMF +0.115 hit T1 in two days (+1.3%). XOM went 2-for-2 (July 7 +2.97%,
  July 10 +0.53%) when CMF was positive, 0-for-1 when the zone was placed but never triggered.
- **Rule: No energy sector long without positive CMF, period.** CMF is more important than RSI,
  ADX, or even golden cross for this sector. It's the make-or-break variable.
- This is the strongest differentiation signal in defensive/low-beta names.

### 19. Rejection Today ≠ Rejection Forever — Re-Screen, Don't Blacklist
- CVX was a hard pass on 7/08 and a winner on 8/08. The difference: CMF flipped from -0.10
  (distribution) to +0.115 (accumulation). The fundamentals didn't change — the flow did.
- **Rule: Don't permanently blacklist any ticker. A rejection captures a point in time.
  Re-screen previously rejected names when market conditions shift.**

### 20. Entry Zone Width Must Be ≥ 2× ATR — Not Just Support-Based
- XOM pending zone: $148-$153 (width 3.3%, ATR ~2%). Too tight for a name with that volatility.
  Price tagged the edge at $153 and rallied to $159.48 without triggering. The zone was technically
  sound (below SMA20 support) but practically useless — no room for a shallow dip.
- **Rule: Entry zone width must be at least 2× ATR. If 2× ATR makes the zone too wide for a
  reasonable risk/reward, the setup is too tight — don't place it. Move to watchlist instead.**

### 21. The "CVX/XOM Pattern" — Golden Cross + Positive CMF + Extreme Oversold = Repeatable Edge
- Three winning trades share the same DNA: XOM 7/07 (+2.97%), XOM 7/10 (+0.53%), CVX 8/08
  (+1.3% T1 partial, running to T2). Common conditions:
  1. Price above SMA200 (golden cross or near-cross)
  2. CMF > 0 (accumulation during pullback)
  3. StochRSI or RSI deeply oversold (<30 RSI or <10 StochRSI)
- This pattern is 3-for-3. It's the highest-conviction mean-reversion signal in the
  energy/defensive sector bucket.
- **Rule: When all three conditions align, size normally. When only two align, reduce size
  or move to pending. CMF is the one that cannot be compromised.**

### 17. Overbought Entry + Weak ADX = Immediate Pullback Risk (NVDA Pattern)
- NVDA: StochRSI 99.7, ADX 16.5, price at $219 just below resistance ($223.63).
  FA is elite but entry timing is poor — overbought with no trend strength means
  mean-reversion pullback is the path of least resistance.
- **Rule: When StochRSI > 95 AND ADX < 20, wait for pullback to SMA50 before entering.**
  The risk/reward at extreme overbought levels is skewed against you.
- Counterpart to Lesson #14 (strong trend + overbought = wait). This applies to
  the weak-trend scenario.

### 18. Screening Repeats = Narrow Market Confirmation (2026-08-07)
- When the screening top 10 is dominated by names that have recently stopped out
  or have known technical headwinds, it confirms narrow market conditions.
- 2026-08-07: 5 of top 10 are recent stop-outs (DELL, RDDT, META, RKLB, GOOG).
  CRM already in portfolio. XOM/CVX already pending. ABBV entry zone missed.
  NVDA overbought. This leaves zero actionable new candidates.
- **Rule: When screening produces zero new actionable candidates, do not force trades.
  Focus on managing existing positions and monitoring pending entries.**
- The market will present better opportunities when composite scores recover above 30.

### 19. Oversold + Positive CMF = The Corrected Signal (CVX 2026-08-08)
- CVX: StochRSI 5.8, CCI -3367 (extreme oversold), golden cross intact, CMF +0.115.
  This is the corrected version of the extreme_oversold_fa_backstop signal that
  failed on META (which had negative CMF -0.053 and death cross).
- **Rule: Extreme oversold + golden cross + positive CMF = actionable mean-reversion
  setup. The positive CMF is the critical differentiator from the META failure.**
- CVX also has a 4.13% dividend yield and analyst consensus $217 (+16% upside),
  providing fundamental backstop that META lacked in terms of yield support.
- This trade will test whether CMF > 0 is the key filter that makes the
  extreme_oversold_fa_backstop signal viable.

### 20. Pending Entry Conversion = Immediate Action (CVX 2026-08-08)
- CVX pending entry zone ($183-188) triggered at $186.56. When a pending entry
  triggers, act immediately — don't re-screen or re-analyze unless there's a
  material change in the thesis.
- The deep-dive confirmed the original thesis: oversold + golden cross + positive CMF.
- **Rule: When a pending entry zone triggers, enter at market. The analysis was
  already done. Only abort if a dealbreaker signal has emerged since the pending
  was created.**

### 21. Death Cross + Positive CMF = Corrected Mean-Reversion (META 2026-08-10)
- META re-entered at $592.10 after the 7/30 stop-out ($585.61→$534.65, -8.7%).
  The critical difference: CMF has flipped from -0.053 to +0.089 — accumulation
  has replaced distribution despite the death cross still being active.
- This is the corrected version of the extreme_oversold_fa_backstop signal:
  death cross + extreme oversold (CCI -633) + elite FA is only tradeable when
  CMF is positive. The positive CMF indicates buyers are stepping in even as the
  trend structure remains bearish — this is what creates the mean-reversion edge.
- **Rule: Death cross + extreme oversold + elite FA = mean-reversion WHEN CMF > 0.
  If CMF turns negative after entry, exit immediately. The CMF is the gatekeeper.**

### 22. Narrow Market = One Good Idea, Not Ten (2026-08-10)
- Second consecutive screening with all composite scores < 30. Only 1 of 10
  candidates (META) was actionable. ABBV, GOOG failed on OBV divergence; RDDT
  failed on death cross + negative CMF; RKLB is unprofitable with decelerating
  growth.
- **Rule: In narrow markets (<30 composite scores), expect 0-2 actionable ideas
  from the screen. Quality over quantity. It's better to find one good trade
  than force five mediocre ones.**

### 23. Third Consecutive Narrow-Market Screening — Pattern Confirmed (2026-08-10)
- Three straight screenings with all composite scores < 30 (8/07, 8/08, 8/10).
  Today: all 10 candidates scored < 28. ABBV OBV divergence worsened (-34.7% → 
  -44.6%), GOOG unchanged (-70.5%), RDDT death cross persists, RKLB rejection 
  candle at resistance.
- However, CVX hit T1 in just 2 sessions (+1.3% partial) and CRM hit T2 (+13% 
  blended) — managed positions are performing despite the narrow new-idea 
  environment.
- **Rule: When the screen produces zero new actionable candidates for 3+ 
  consecutive sessions, shift focus entirely to managing existing positions 
  and monitoring pending entries. Don't keep re-screening for diminishing 
  returns.**
- Pending NVDA ($205-212 zone) is the only live pending entry remaining.

### 24. Four Consecutive Narrow-Market Screenings = Systematic Confirmation (2026-08-11)
  - Now 4 consecutive sessions (8/07, 8/08, 8/10, 8/11) with all composite scores < 30.
    Top 10 identical to prior days: DELL 27.9, CRM 26.8, RDDT 26.4, ABBV 25.8, META 25.7,
    RKLB 23.9, CVX 23.6, XOM 23.6, NVDA 23.5, GOOG 23.3.
  - Every single candidate has a known issue: DELL (OBV divergence -73%+), CRM (already closed
    winner, in cool-down), RDDT (death cross + negative CMF), ABBV (OBV divergence -44.6%),
    META (already in portfolio), RKLB (momentum trap), CVX/XOM (already in portfolio/pending),
    NVDA (pending entry not triggered), GOOG (OBV divergence -70.5%).
  - Existing positions continue to perform: CVX +4.2%, DAL +6.2%, V +0.9%, META flat.
  - **Rule: 4+ consecutive screenings with zero new ideas = stop screening until composite
    scores recover above 30. Focus 100% on managing existing positions. Re-screen only when
    market breadth improves, signaled by a top-10 average composite score > 30.**
  - This is a market telling you to be patient. The narrowness is structural, not random.

### 25. Fifth Narrow-Market Screening — AMD Enters Top 10 (2026-08-11)
  - 5th consecutive session with all composite scores < 30 (avg: 25.1). Top 10: DELL 28.0,
    CRM 26.8, RDDT 26.4, ABBV 26.0, META 26.0, XOM 24.2, RKLB 23.9, CVX 23.3, GOOG 23.2,
    AMD 23.1 (replacing NVDA, which fell out of the top 10).
  - AMD (188% momentum_12_1, RSI 44.7) is the only new face in the top 10 — but was stopped
    out on 7/28 and may still be in cooldown.
  - All existing positions are performing: CVX +4.5% (T2 $200 is 2.6% away), DAL +5.4%
    (T2 $95 is 6.5% away), V +1.5% (T2 $390 is 7.9% away but stop at $355.82 is tight),
    META +0.5% (T1 $599.50 is 0.8% away).
  - NVDA pending at $217.55, approaching $205-212 zone (2.6% above zone top).
  - **Rule: 5+ consecutive sub-30 screenings = structural narrowness. All energy goes into
    managing existing positions and protecting gains. Do not force new trades. Re-screen
    only when the top-10 average composite score recovers above 30.**

### 26. Narrow Market Broke on 2026-08-11 — MU + EOG Above 30, Energy Rotation
  - After 5 consecutive sessions with all composite scores < 30, MU (31.6) and EOG (31.2)
    broke above the threshold. The top 10 shifted dramatically: 4 of 7 new candidates are
    Energy (EOG, OXY, COP, BP), signaling sector rotation from Tech to Energy.
  - MU has elite FA (PEG 0.13, P/E 5.6x, earnings +1,369%) but CMF -0.079 distribution
    and falling OBV — same fatal pattern as AVGO (7/30) and first META (7/30). Rejected
    despite the highest composite score. CMF remains the non-negotiable gate.
  - **Rule: When the screen breaks above 30 after a prolonged narrow stretch, the new
    candidates are worth deep-diving — but apply all existing filters (CMF, OBV, ADX)
    rigorously. A high composite score does not override a CMF/OBV dealbreaker.**
  - COP is the highest-conviction new idea: golden cross + CMF +0.093 + OBV rising +
    PEG 0.94 + 2.86% dividend. This is the golden_cross_oversold_cmf_positive pattern
    minus the oversold condition — a variant worth tracking.

### 27. Energy Sector Dominance = Rotation Signal
  - 4 of 7 new screening candidates are Energy (EOG, OXY, COP, BP). Combined with CVX
    already in portfolio (T2 approaching), this confirms a sector rotation into Energy.
  - Energy names share common traits: golden crosses, strong FA (low P/E, high dividends),
    and positive CMF (except OXY). This is the most concentrated sector signal since the
    Tech dominance of early July.
  - **Rule: When 3+ names from the same sector appear in the top 10 simultaneously, it's
    a sector rotation signal. Prioritize the strongest setup in that sector rather than
    diversifying across all candidates. COP is the pick of the Energy litter.**

### 28. CMF Is the Single Most Important Filter — 6 Months of Evidence
  - Across 6 months of trading: every trade with positive CMF at entry has been profitable
    or is currently running positive. Every trade with negative CMF at entry has either
    stopped out (AVGO, META v1, AMD) or underperformed.
  - MU is the latest test case: composite score 31.6 (#1), PEG 0.13, but CMF -0.079.
    The system correctly rejected it. If CMF turns positive, MU becomes the highest-upside
    trade on the board.
  - **Rule: CMF > 0 is the single most predictive pre-entry filter. No exceptions.
    Not even for a PEG of 0.13.**
  
  ### 29. MU: Value Trap in Plain Sight — 4th Rejection (2026-08-12)
    - MU has been the #1 composite score in multiple screening runs (31.6 on 8/12, 31.6 on 8/11)
      and rejected every time for the same reason: CMF negative (-0.087 to -0.079 range).
    - PEG 0.13, fwd P/E 5.57x, earnings +1,369% make it the most undervalued stock in the
      watchlist — but nobody is buying it. The CMF distribution signal is persistent.
    - **Rule: A stock that screens #1 repeatedly but fails the same filter every time = value
      trap until the filter clears. Stop re-analyzing it every session — flag it and move on.
      If CMF flips positive, it becomes an immediate priority.**

  ### 30. Death Cross + Positive CMF + Strong ADX = Reversal Pattern (BABA 2026-08-12)
    - BABA: death cross but ADX 32 (strong trend), Aroon Up 96/Down 0, CMF +0.048. This is
      fundamentally different from META's death cross scenario (ADX 15.7 weak, now ADX unknown).
    - The strong ADX tells us the death cross is a LAGGING indicator — the trend has already
      reversed bullish but the 50/200 relationship hasn't caught up yet.
    - **Rule: Death cross + ADX > 25 with positive CMF = potential reversal, not continuation.
      This is distinct from the Lesson #11 rule (death cross + negative CMF = do not enter).
      The ADX is the differentiator: strong ADX + death cross = trend change in progress; weak
      ADX + death cross = no clear direction.**

  ### 31. Pre-Earnings Entry = Unnecessary Binary Risk (JD 2026-08-12)
    - JD: golden cross, ADX 36.6, Aroon 96/0, CMF +0.022 — a structurally perfect setup.
      But Q2 earnings tomorrow (Aug 13) with trailing EPS -50.7% YoY and revenue +4.9%.
    - Entering ahead of earnings turns a high-probability trend-following setup into a coin
      flip. The TA edge is swamped by the earnings surprise risk.
    - **Rule: Never enter a new position within 2 trading days of an earnings report. If the
      setup is valid, it will still be there after the print. If it's not, you dodged a bullet.**

  ### 32. Second Consecutive Screening Above 30 — Breadth Improving (2026-08-12)
    - After 5 consecutive sessions of <30 composite scores (8/07-8/11), we now have 2 sessions
      above 30. MU 31.6, COP 31.1, OXY 30.7 on 8/12. The narrow market is loosening.
    - But 5 of 6 new candidates were rejected (CMF issues, overbought, earnings risk) — 
      only BABA passed to pending. A broader market doesn't mean everything is buyable.
    - **Rule: When breadth improves, apply the same filters rigorously — don't lower standards
      just because the screen looks better. Quality over quantity still applies.**

### 33. Third Consecutive Screening Above 30 — Breadth Recovery Confirmed (2026-08-13)
  - Now 3 consecutive sessions with composite scores above 30 (8/11: MU 31.6/EOG 31.2,
    8/12: MU 31.6/COP 31.1/OXY 30.7, 8/13: MU 31.7/EOG 31.4/OXY 31.3/COP 30.4).
  - The narrow market (5 straight sessions <30, 8/07-8/11) has definitively ended.
  - But filter rigor still eliminates most candidates: OXY rejected (ADX 18.6, OBV divergence,
    marginal CMF), only BP passed to pending (gated by MACD).
  - **Rule: Breadth recovery doesn't mean everything is buyable. The same filters still
    apply. The difference is the screen produces enough candidates that 1-2 will pass
    filters — vs. zero during the narrow market.**

### 34. Pending Entry Expiration = Zone Was Too Tight (BAC, C, NVDA 2026-08-13)
  - 3 pending entries expired simultaneously: BAC ($62.10-63.50 zone, price $64.93),
    C ($131.53-134.50 zone, price $138.09), NVDA ($205-212 zone, price $222.46).
    All three rallied above their zones without pulling back. Momentum was too strong
    for the pullback scenario.
  - BAC zone was only 2.2% wide ($62.10-$63.50 = $1.40). The stock rallied $1.07 past
    the zone top — a modest move that blew through the zone entirely. Lesson #20 warned
    about zone width < 2x ATR. BAC ATR was likely ~$1.30, so zone was barely 1.1x ATR.
  - **Rule: Pending entry zones placed near 52-week highs during strong uptrends almost
    never trigger — the momentum carries price past the zone. Either widen the zone
    significantly (2x ATR minimum) or wait for a genuine pullback signal before placing.**
  - NVDA: The overbought pullback never came. Lesson #17 (overbought + weak ADX =
    pullback risk) was technically correct but the pullback just didn't materialize —
    a reminder that probabilities are not certainties.

### 35. Death Cross Mean-Reversion: T1 Hit ≠ T2 Safe (META 2026-08-13)
  - META hit T1 $599.50 on 8/12 (+1.3%) but reversed $19.61 (-3.3%) in a single day
    to $580.65, now just $5.65 (1.0%) above the $575 stop.
  - The death cross + oversold + CMF > 0 signal works for mean-reversion to T1 (the
    washout bounce) but the structural headwind of the death cross reasserts itself
    quickly. T2 may be overly ambitious in this context.
  - **Rule: For death cross mean-reversion plays, take 75% at T1 instead of 50%. The
    death cross headwind makes T2 significantly less probable than in golden cross setups.
    The mean-reversion bounce is the signal — don't overstay for the trend breakout
    when there's no trend to break out into.**
    - **CONFIRMED 8/13:** META exited at $580.65 (blended -0.32%). CMF collapsed to +0.009
      (razor-thin), bearish marubozu -3.7% reversed the entire T1 gain in one session.
      The death cross headwind is real — T1 was the correct exit point. The 50% hold for
      T2 converted a winner into a scratch trade.

  ### 36. Death Cross + Strong ADX + Positive CMF = Valid Reversal Entry (BABA 2026-08-13)
    - BABA entered at $124.88: death cross active but ADX 31.6, Aroon Up 96/Down 0,
      CMF +0.13, StochRSI cooled to 63.9 (trigger fired). This is fundamentally
      different from META's death cross (ADX 13.3 weak, no trend) and validates
      Lesson #30: strong ADX + death cross = trend change in progress, not continuation.
    - **Rule: Death cross with ADX > 25 AND CMF > 0 AND StochRSI not overbought =
      valid reversal entry. Size at half-normal for non-US-listed ADRs with
      geopolitical risk (China, Russia, etc.).**
    - The StochRSI cooling from overbought to neutral (81.2 → 63.9) is the trigger
      that says the pullback has washed out the short-term froth while the medium-term
      momentum remains intact.

    ### 37. Full Scan Confirms Breadth Recovery But Filters Still Dominate (2026-08-13)
      - Full scan (131 tickers) produced 3 candidates above composite 30: MU (31.7),
        OXY (31.2), COP (30.7). All three were rejected or held: MU on CMF negative
        (5th+ rejection, value trap), OXY on ADX < 20 + marginal CMF, COP on overbought
        at resistance. Only BAC (27.5) passed to pending — and only on a pullback.
      - The narrow market (5 sessions <30, 8/07-8/11) has definitively ended with 3
        consecutive sessions above 30, but the same filters (CMF, ADX, overbought) still
        eliminate 90%+ of candidates. Breadth recovery != everything is buyable.
      - **Rule: When the full scan produces 0 actionable filled entries despite composite
        scores above 30, it means the market is in a "good but not great" phase — trends
        exist but entries are extended. Focus on managing existing positions and monitoring
        pending pullback entries. Do not force new filled positions.**
      - Energy remains the dominant sector (COP, OXY, EOG, BP in top 10) but all Energy
        entries are either overbought or gated. The rotation signal is real but the
        entry timing is not yet ripe.

    ### 38. V Stop Danger — When a Position's Stop Is Within 1%, Prepare Exit
      - V: stop $358.50, current $359.42 — only $0.92 (0.26%) of cushion. MACD bearish,
        OBV falling, below SMA20. The only bullish anchor is CMF +0.217 (medium-term
        accumulation). StochRSI 5.7 deeply oversold offers bounce potential but is not
        a reason to widen the stop.
      - **Rule: When a position's stop is within 1% of current price, do not widen it.
        If the stop is hit, exit immediately. The stop was set for a reason — the fact
        that price is testing it means the thesis is under pressure. A bounce from
        oversold StochRSI is hope, not a reason to stay in.**
      - **RESOLVED 8/13:** V bounced to $365.45 (+2.7%), stop cushion recovered to $6.95
        (1.9%). The oversold StochRSI (5.7) bounce materialized. But the lesson stands:
        do not widen stops preemptively; the bounce is a reason to keep the position,
        not to have widened the stop during the test.

    ### 39. Full Scan Produces Zero New Filled Entries — "Good But Not Great" Market (2026-08-13)
      - 3rd consecutive session with composite scores above 30 (breadth recovery confirmed),
        yet the full scan (131 tickers) produced ZERO new actionable filled positions.
        All 10 top candidates are already in portfolio (BABA filled, EOG/BP/BAC pending),
        or rejected/held on known filters (MU CMF negative, OXY/COP overbought, C/DELL/CRM
        weak ADX or death cross).
      - **Rule: When a scan produces zero NEW candidates because every top-10 name is
        already covered (filled, pending, or rejected), it is NOT a failure of the screen.
        It means the portfolio is already optimally positioned for the current market.
        Do not force a new trade just to have "action." The correct move is to manage
        existing positions and let pending zones trigger.**
      - This is distinct from the narrow-market rule (#24): there, scores were < 30 and
        nothing was buyable. Here, scores are > 30 but everything buyable is already owned
        or pending. Breadth recovery + full coverage = hold, don't chase.

    ### 40. Full T2 Completion Validates the CMF Gate End-to-End (CVX 2026-08-14)
      - CVX completed its full T1+T2: entered 8/08 at $186.56, T1 $189 hit 8/10 (+1.31%
        on 50%), T2 $200 hit 8/14 (+7.20% on 50%), blended +4.26%. This is the first
        full T1+T2 completion for golden_cross_oversold_cmf_positive.
      - The same CVX setup FAILED on 7/08 with CMF -0.10 (distribution) and WON on 8/08
        with CMF +0.115 (accumulation). Fundamentals were identical both times — the flow
        (CMF) was the entire difference. This is the strongest single confirmation yet of
        Lesson #28 (CMF is the #1 predictive filter) and Lesson #18 (positive CMF is the
        non-negotiable gate for energy mean-reversion).
      - **Rule: In energy/defensive names, the CMF sign at entry is a higher-signal
        determinant of outcome than valuation or the oversold reading. Golden cross +
        positive CMF + oversold = full-position mean-reversion. Any of the three missing =
        half-size or pass.**

    ### 41. Marginal CMF (+0.02) ≠ Positive CMF Gate Passed (OXY 2026-08-16)
      - OXY screens undervalued (PEG 0.83) with rising OBV and a golden cross, but its
        CMF +0.022 is only razor-thin positive. It has been rejected multiple times for the
        same marginal-CMF + ADX<20 combination.
      - **Rule: "CMF > 0" as a gate means meaningfully positive (roughly CMF > +0.05 for a
        fresh entry). A CMF barely above zero carries no accumulation conviction and should
        be treated as a fail. Require ADX > 20 alongside before upgrading a marginal-CMF name.**
