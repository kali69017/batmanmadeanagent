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

### 17. (Reserved — numbering gap from earlier session, intentionally skipped)

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

### 42. Full Scan Returned Only 5 Tickers = Extreme Narrow Breadth (2026-08-17)
  - The full scan (mode='full') returned only 5 tickers with all composite scores < 30
    (NVDA 29.2, META 25.3, GOOG 23.2, AAPL 19.3, MSFT 15.2). This is the narrowest
    breadth yet observed — earlier sessions produced 10+ candidates, and even the
    "narrow market" stretch (8/07-8/11) produced a full top-10 list.
  - **Rule: When a full scan returns a shrunken candidate list AND all scores < 30,
    the market is structurally selective. Do not force fills — the correct move is
    watchlist/pending placement with hard gates, not entries.**

### 43. NVDA: Elite FA Cannot Override Overbought + Slight Distribution (2026-08-17)
  - NVDA's FA is the best on the board (PEG 0.62, 215% EPS growth, 114% ROE, quant 72),
    but StochRSI 93.6 (overbought) + CMF -0.03 (slight distribution) violate the
    non-negotiable CMF gate and Lesson #14 (strong trend + overbought = wait). This is
    a repeat of Lesson #17 (overbought + weak ADX = pullback risk) — same NVDA, same
    overbought entry-timing problem.
  - **Rule: A pullback entry zone is only actionable if BOTH gates clear at trigger time:
    CMF > 0 AND StochRSI cooled below ~80. Do not chase overbought strength regardless of
    FA quality.**

### 44. META/GOOG: Oversold CCI + OBV Divergence Is a Trap Without Positive CMF (2026-08-17)
  - META (CCI -2152, bullish OBV divergence, but CMF -0.05 + death cross) and GOOG
    (CCI -1664.7, but CMF -0.152 + OBV divergence -80.6%) both flashed "oversold bounce"
    setups that the expert subagents rated "long." Both are REJECTED: the CMF distribution
    + death-cross/OBV-divergence combination is the exact same fatal pattern as META 7/30
    (-8.7% same-day stop-out).
  - **Rule: Oversold oscillators (CCI < -1000, StochRSI < 10) are NOT a standalone buy
    signal. Without CMF > 0 (and no death cross), they signal continuation, not reversal.
    The expert subagent will sometimes rate these "long" — the CMF/death-cross filter
    overrides the expert's verdict. Trust the filter, not the narrative.**

  ### 45. Breadth Recovery With All-Energy Top-10 = Rotation, But Entries Still Gated (2026-08-17)
    - Full scan (132 tickers) returned 10 candidates (vs only 5 on 8/16) with 5 scores above
      30 — breadth clearly recovered. But the top-10 is dominated by Energy (EOG, CVX, COP,
      OXY, BP = 5 of 10), confirming the ongoing Energy rotation (Lesson #27).
    - Every single Energy candidate is either overbought (CVX StochRSI 85.3, COP Stoch %K 91.1)
      or trend-less (EOG ADX 14.6 + Aroon bearish, OXY ADX 18.9, BP ADX 16.1 + MACD bearish).
    - The rotation signal is real, but the entry timing is not ripe — the sector has already
      run (CVX completed a full T1+T2 winner on 8/14) and now needs to consolidate/pull back.
    - **Rule: When a rotated sector's names all arrive in the top-10 ALREADY overbought or
      trend-less, the rotation has largely played out for the near term. Place pullback/pending
      entries (not market orders) and watchlist the trend-less names with ADX > 20 as the
      re-entry trigger. Do not chase the sector at extended levels.**
    - This extends Lesson #37: breadth recovery + all-Energy top-10 ≠ everything is buyable.
      The sector leader (CVX) already paid; the followers (COP, EOG, OXY, BP) are either
      extended or trend-less. Patience: the sector will offer better entries on a pullback.

  ### 46. Pending Entry Degradation — CMF Can Flip While You Wait (COP 2026-08-18)
    - COP was placed as pending on 8/17 with CMF +0.121 (strong accumulation). By 8/18, the
      CMF had flipped to distribution (-35.8 volume oscillator). StochRSI also worsened from
      77.5 to 81.0 (overbought). The bullish structure (golden cross, SMA stack) remains
      intact but the flow has turned — the pending entry zone is now gated by a condition
      that didn't exist when it was placed.
    - **Rule: Pending entries are not static. Re-check all gates every session. A CMF flip
      from positive to negative is a material degradation — add a new gate or widen the
      entry zone downward. If the degradation persists for 3+ sessions, expire the pending
      and wait for a fresh signal.**

  ### 47. Death-Cross Reversal Pattern Validated — BABA Entry (2026-08-18)
    - BABA entered at $128.08: death cross aging (SMA50 $113.72 rising toward SMA200 $137.68),
      ADX 29.8 (strong trend), CMF +0.153 (strong accumulation), Aroon 80/4 (bullish),
      StochRSI 17.2 (oversold coiled-spring). This is the first dedicated trigger of the
      death_cross_strong_adx_cmf_positive signal.
    - **Rule: The death-cross reversal signal is now live with its own signal log. Entry
      requirements: (1) death cross active but SMA50 rising, (2) ADX > 25, (3) CMF > 0,
      (4) StochRSI not overbought. Size at half for non-US-listed ADRs with geopolitical
      risk.**

  ### 48. NVDA Inside Zone But Both Gates Fail — The System Holds (2026-08-18)
    - NVDA at $221.00 is inside the pending entry zone ($211.48-222) for the first time.
      Elite FA (PEG 0.62, 215% EPS growth, 63% margins, 114% ROE). But both gates fail:
      CMF 0.002 (< 0.05) and StochRSI 88.9 (> 80). The doji candle reinforces indecision.
    - **Rule: When a ticker is inside the entry zone but both CMF and StochRSI gates fail,
      do not enter. FA quality is not a gate override. The gates exist to prevent entering
      at the wrong moment. This is the strongest test yet of the CMF gate (Lesson #28).**

### 49. Parabolic Momentum (>200% 12-1) + Negative CMF = Distribution Into Strength (MU 2026-08-19)
  - MU screens #1 yet again (composite 31.6) on momentum_12_1 of 500.91% — a parabolic
    12-month run (52wk range $113.28-$1254.81, 6mo +125%). But CMF -0.073, ADX 13.4,
    OBV bearish divergence (price +123.5% vs OBV +29%). The 500% momentum is itself a
    red flag: gains that parabolic are being distributed, not accumulated.
  - Rule: When momentum_12_1 exceeds ~200%, discount the momentum component of the
    composite score entirely — a parabolic past is not a bullish signal. Reject unless
    CMF > 0 AND ADX > 20, the same two gates every candidate must pass.
  - Also: EOG reached a fresh 52-week high ($150.55) with CMF +0.158 (strong accumulation)
    but ADX 16.1 + StochRSI 80.3. Positive CMF alone does not justify chasing a 52-week-high
    breakout with no trend and overbought oscillators (extends Lesson #45: rotated-sector
    names arriving already extended = wait for pullback, not market order).

### 50. Golden Cross + Oversold + Positive CMF Works in Financials Too (BAC 2026-08-20)
  - BAC triggered the golden_cross_oversold_cmf_positive signal: golden cross (SMA50 > SMA200),
    CMF +0.098 (strong accumulation), StochRSI 8.7 (deeply oversold). Prior validation was
    100% energy/defensive (XOM 2x, CVX 1x). BAC at $62.89 is the first Financials test of
    this 3-for-3 signal.
  - **Rule: The golden cross + positive CMF + oversold StochRSI pattern is NOT sector-specific.
    It's a structural mean-reversion pattern that works wherever all three conditions align.
    Size normally outside energy/defensive but monitor for any sector-specific behavior
    divergence.**
  - Also: DELL was rejected for the 8th+ time on CMF -0.063 + ADX 11.9 (Lesson #1/#2),
    C watchlisted on CMF -0.041 + ADX 15.2 (same pattern), DAL rejected on CMF -0.277 +
    StochRSI 0.0 (Lesson #7 continuation trap confirmed). The BAC entry stands out because
    it's the only candidate where ALL gates cleared simultaneously.

### 51. COP Pending Zone Blown Through — Pending Entries Have a Shelf Life (2026-08-20)
  - COP pending zone ($123.63-125) was placed 8/17 when price was $128.57. Three sessions
    later price is $134.65 (+7.7% above zone top) at a fresh 52-week high. The pullback
    entry was fundamentally sound but the market didn't offer the pullback — momentum
    continued without pausing.
  - **Rule: When a pending entry zone is >5% above the zone top with no pullback after
    3 sessions, the zone is no longer realistic. Either expire it or widen it downward
    to a new support level. Don't let stale pending entries accumulate indefinitely —
    they clog the portfolio with non-actionable noise.**
  - This extends Lesson #20 (zone width must be ≥ 2× ATR) and Lesson #34 (pending entries
    placed near 52-week highs during strong uptrends almost never trigger).

  ### 52. Expert Subagent Can Recommend LONG on Fatal Patterns — Trust the System Filters (2026-08-21)
    - Three candidates (C, DAL, AVGO) received LONG recommendations from the financial-expert
      subagent. All three were REJECTED by system filters: C (CMF -0.072 + ADX 16.1), DAL
      (CMF -0.335 + D/E 97x), AVGO (OBV divergence + CMF -0.123 + ADX 19.2 — same fatal
      pattern as its 7/30 stop-out). The expert subagent sees oversold oscillators + strong
      FA and recommends entry, but the system's accumulated lessons correctly identify these
      as continuation traps (Lesson #7), no-trend setups (Lesson #2), and OBV-divergence
      dealbreakers (Lesson #1/#16).
    - **Rule: The financial-expert subagent is an advisor, not the decision-maker. When the
      expert recommends LONG but CMF is negative AND ADX < 20, the system filter overrides.
      The expert's job is to synthesize TA+FA — the system's job is to apply the hard-won
      filters that the expert doesn't always weigh heavily enough. Trust the filters.**
    - This is the mirror image of Lesson #44 (expert rated META/GOOG long but CMF/death-cross
      filter overrode). The pattern is now confirmed across multiple sessions and tickers.

  ### 53. NVDA Gate Dynamics: One Gate Improving While Another Deteriorates (2026-08-21)
    - NVDA: StochRSI collapsed from 88.9 to 13.4 (gate now PASSES — oversold is better than
      overbought for entry timing). But CMF flipped from +0.002 to -0.142 (gate now FAILS
      harder — distribution intensified). The net effect: the entry is still blocked, just
      by a different gate. Price is inside the zone at $217.57.
    - **Rule: When one gate improves but another deteriorates, the entry is still blocked.
      Both gates must pass simultaneously. A gate improvement is encouraging but doesn't
      compensate for a gate deterioration — they are independent conditions.**
    - This is a new dynamic not previously observed: gate rotation rather than gate clearance.

  ### 54. AVGO: Same Fatal Pattern 22 Days After Stop-Out — Patterns Persist (2026-08-21)
    - AVGO stopped out 7/30 on OBV divergence + negative CMF + ADX 15.7. On 8/21, the
      pattern is nearly identical: OBV divergence (price +12.8% vs OBV -21.7%), CMF -0.123,
      ADX 19.2. The only difference: StochRSI is now deeply oversold (8.0 vs prior levels)
      and price is at SMA200 support instead of below it. But the core dealbreakers haven't
      changed — the stock is still being distributed.
    - **Rule: A stop-out pattern that persists 3+ weeks later is structural, not temporary.
      Don't re-enter until ALL dealbreaker conditions have cleared, not just some of them.
      Oversold at support is not a reason to override OBV divergence + negative CMF.**

  ### 55. Death-Cross Reversals Bleed Faster Than Golden-Cross Setups — Tighter Stops Needed (BABA 2026-08-21)
    - BABA entered at $128.08 with all gates green: ADX 29.8, CMF +0.153, StochRSI 17.2,
      Aroon 80/4 — a textbook death_cross_strong_adx_cmf_positive trigger. In just 3
      sessions, the cushion collapsed: $4.40 (3.6%) → $3.71 (3.0%) → $0.83 (0.7%). The
      stop distance (7.5% from entry) was too generous — the death-cross structural
      headwind means these setups either work quickly or the death cross reasserts.
    - **Rule: Death-cross reversals need tighter stops than golden-cross setups. Max stop
      distance: 5% from entry (not 7-8%). Exit faster if the bounce doesn't materialize
      within 3-5 sessions. The structural headwind is real even when all gates pass.**
    - This extends Lesson #35 (take 75% at T1 for death-cross plays) with a stop-sizing
      corollary: tighter stops, faster exits. The death cross is not a neutral backdrop.

  ### 56. Golden Cross + Oversold + CMF Pattern Extends to Financials But Works Slower (BAC 2026-08-21)
    - BAC is the first Financials test of the golden_cross_oversold_cmf_positive signal
      (3-for-3 in Energy: XOM 2x, CVX 1x). After 1 session: -1.9%, cushion narrowed from
      3.0% to 1.9%. The Energy winners popped in 1-2 days; BAC is grinding. Lower
      volatility (21.5% vs Energy's 26%) and the 2% dividend yield mean the mean-reversion
      bounce may need 3-5 sessions, not 1-2.
    - **Rule: The golden cross + oversold + positive CMF pattern is sector-transferable,
      but timing expectations differ. Energy names (high beta, commodity-driven) mean-revert
      sharply. Financials (lower vol, yield-supported) grind. Allow 3-5 sessions before
      judging the setup as failing. The signal isn't broken — the clock is different.**

  ### 57. StochRSI Collapse + Simultaneous CMF Deterioration = Distribution, Not Entry (NVDA 2026-08-21)
    - NVDA's StochRSI collapsed from 88.9 → 13.4 (massive cooldown — looks like a buy
      signal), but CMF simultaneously flipped from +0.002 → -0.142 (distribution intensified).
      The StochRSI cooldown in the presence of accelerating negative CMF means sellers are
      in control — the oversold condition signals continuation, not reversal (extends
      Lesson #7: oversold + negative CMF = continuation).
    - This is a new variant: **gate rotation** — one gate improving while another deteriorates.
      It's not net-neutral; the CMF deterioration outweighs the StochRSI improvement because
      CMF is the higher-signal filter (Lesson #28).
    - **Rule: When StochRSI improves but CMF simultaneously deteriorates, the entry remains
      blocked. CMF is the dominant gate. Improving oscillator + worsening flow = distribution
      confirmation, not an entry signal. The oscillator is telling you it's "safe" while
      CMF is screaming that sellers are in control. Trust CMF.**

  ### 58. Death Cross + Positive CMF + Strong ADX Failed on China ADR — Geopolitical Risk Premium (BABA 2026-08-24)
    - BABA entered 8/18 at $128.08 with all gates green: ADX 29.8, CMF +0.153, StochRSI 17.2,
      Aroon 80/4 — a textbook death_cross_strong_adx_cmf_positive trigger. Stopped out 8/24
      at $118.28 (-7.65%). The death cross headwind + China ADR geopolitical risk overwhelmed
      the positive CMF and strong ADX. The signal is now 1-for-2 (50%).
    - **Rule: For China ADRs and other geopolitically-sensitive names, require a golden cross
      (not just an aging death cross) before entering, regardless of ADX/CMF strength. The
      death cross structural headwind combined with geopolitical risk creates a compounding
      effect that positive CMF alone cannot overcome.**
    - This extends Lesson #36 (death cross + strong ADX + positive CMF = valid reversal entry)
      with a critical jurisdiction carve-out: the pattern is valid for US-listed domestic names
      but NOT for ADRs from geopolitically-sensitive jurisdictions (China, Russia, etc.).
    - Also confirms Lesson #55: death-cross reversals need tighter stops (5% max, not 7.5%).
      The 7.5% stop distance on BABA was too generous — a 5% stop at $121.68 would have saved
      2.5% of capital.

  ### 59. OXY: Both Prior Rejection Reasons Fixed — CMF and ADX Now Pass (2026-08-24)
    - OXY was rejected multiple times for marginal CMF (+0.02 range) and ADX < 20. On 8/24,
      both conditions cleared: CMF +0.063 (meaningful accumulation) and ADX 23.9 (trend
      confirmed). Golden cross intact, OBV rising, MACD bullish. FA: PEG 0.87, 53% revenue
      growth, D/E 0.35x pristine.
    - **Rule: When a repeatedly-rejected ticker clears ALL prior rejection filters, it
      graduates from watchlist to pending. Don't hold old rejections against a name when
      the data has changed. Re-screen, don't blacklist (extends Lesson #19).**
    - However, StochRSI 94.8 is deeply overbought — entry requires a pullback. This is a
      "golden cross + positive CMF + pullback to support" setup, not the oversold variant.

  ### 60. NVDA: Price Fell Through Entry Zone — Zone Must Be Reset (2026-08-24)
    - NVDA's prior pending zone ($213.50-217.50) was placed when price was above it. Price
      has now sliced through the zone with conviction, closing at $211.35 — below the zone
      bottom. The zone is invalidated. A new zone anchored to SMA50 support ($207.68) is
      warranted, but CMF remains negative (-0.127) — the non-negotiable gate still fails.
    - **Rule: When price falls through a pending entry zone from above, the zone is
      invalidated. Reset the zone to the next support level below. Do not enter just
      because price is "cheaper" — the fact that it sliced through support means the
      original thesis was wrong. Re-anchor, re-gate, and wait.**
    - StochRSI at 1.0 is extreme oversold — historically a bounce setup — but CMF -0.127
      means the oversold condition signals continuation, not reversal (Lesson #7/#57).

    ### 61. OXY: Overbought StochRSI + Doji at Resistance = Violent Pullback (2026-08-25)
      - OXY pending entry zone ($60.49-61.43) was set at SMA20 support. StochRSI was 94.8
        (extreme overbought) with a doji at $61.43 resistance. Price fell through the entire
        zone and below the stop ($59.80) to $59.06 in a single session — no fill, no loss.
      - **Rule: When StochRSI > 90 and a doji prints at resistance, the subsequent pullback
        can be violent. For Energy names with StochRSI > 90, wait for the pullback to fully
        play out before setting a zone, or anchor the zone to SMA50 (not SMA20).**
      - The correct read was "wait for pullback" — but the zone was too optimistic. The
        overbought condition correctly predicted the pullback; the zone just wasn't wide enough.

    ### 62. MU: ADX < 20 + CMF Negative = No Entry Despite Elite FA (2026-08-25)
      - MU ranked #1 in full scan (composite 31.7) with PEG 0.14, forward P/E 6.0x, 346%
        revenue growth, 1369% earnings growth — arguably the best FA in the entire watchlist.
        But ADX 11.6 (no trend) and CMF -0.06 (mild distribution). Per Lesson #2 and #15:
        FA quality is irrelevant if ADX < 20 and CMF is negative.
      - **Rule: The #1 screening candidate can still be a pending/reject. Composite score
        measures past performance and valuation — it does not measure current trend health.
        Always gate with ADX > 20 and CMF > 0 before entering any screening top-10 name.**
      - This reinforces Lesson #13 (momentum trap) and Lesson #15 (great FA cannot override
        ADX < 20).

    ### 63. Narrow Market Persists — Composite Scores Still Sub-35 (2026-08-25)
      - Top composite score: MU 31.7. Range: 27.6-31.7. All top-10 scores below 35.
      - Per Lesson #8: when all composite scores are below 30-35, the market is narrow and
        selective. Be patient. Don't force trades.
      - Of 6 new screening candidates, 3 were rejected outright (DAL, CVS, ON) and 3 were
        placed as pending with gates (MU, COP, C). Zero immediate fills — the market is not
        offering clean entries right now. This is consistent with a narrow, selective tape.

    ### 64. Asset-Manager + Energy "Screen-topper" Rotation = Broad-Based But Still Gated (2026-08-26)
      - Full scan (384 tickers) surfaced a NEW cluster: two asset managers (BEN, IVZ) and an
        oil-services name (NOV) entered the top-10 alongside the usual Energy/Memory leaders.
        This is a broadening, not a fresh rotation — breadth is improving but entries remain
        gated (BEN/IVZ overbought near resistance, NOV ADX < 20 + weak FA).
      - **Rule: When entirely new sectors (asset managers, oil services) appear in the top-10,
        it confirms the narrow market is loosening — but the same gates (CMF > +0.05, ADX > 20,
        not overbought, no OBV divergence) still eliminate most. Breadth ≠ buyability.**

    ### 65. WDC: Second Parabolic Momentum Trap in the Memory Complex (2026-08-26)
      - WDC momentum_12_1 +289.8%, CMF -0.066, ADX 16.8, OBV bearish divergence (price +59%
        vs OBV +32.8%, falling on 5d/20d/60d), Aroon Down 44 > Up 28, -42.2% off 52wk high.
        This is the SAME distribution-into-strength signature as MU (Lesson #49/#62), just in
        a different memory name.
      - **Rule: The memory sector (MU, WDC) is in a cyclical distribution phase. Both #1-ranked
        candidates in consecutive sessions are memory names with parabolic momentum + negative
        CMF + ADX < 20. Do not buy the memory complex until CMF turns positive across the group.
        A cheap PEG (0.14 MU, 0.87 WDC) is not a reason to catch a falling knife.**

    ### 66. CVX Pending Converted on "Trend-Continuation" Not the Oversold Variant (2026-08-26)
      - CVX pending ($195-200) triggered at $199.88 with CMF +0.124, ADX 28.1, StochRSI 53.1
        (cooled, not oversold). This is a golden-cross trend-continuation re-entry on a prior
        winner, NOT the golden_cross_oversold_cmf_positive pattern (which needs StochRSI < 10).
        Distinct signal class: re-entering a completed winner on a pullback with CMF intact.
      - **Rule: A completed T1+T2 winner can be re-entered on a pullback when (1) golden cross
        intact, (2) CMF > +0.05, (3) StochRSI cooled below ~80. This is trend-continuation,
        not mean-reversion — log it under composite_screening_top10, not the oversold signal.**

    ### 67. APA: The "Clean" Energy Setup — Trend + Accumulation, No Overbought (2026-08-26)
      - APA is the first Energy candidate in weeks with ALL structural boxes ticked AND no
        overbought condition: full SMA stack + golden cross, ADX 25.9, CMF +0.15, OBV confirms
        (+223% vs price +50%, no divergence), StochRSI 28.5 (cool), MACD bullish. FA: fwd P/E
        9.8x, PEG 0.82, 27% ROE. Only blemish: 5-day OBV cooling near $42.05 resistance.
      - **Rule: The rare "clean" Energy setup (trend + accumulation + not overbought) is worth
        a pending entry anchored to SMA20, because Energy names usually arrive in the top-10
        ALREADY overbought (Lesson #45). When one arrives cooled-down, it's a differentiated
        opportunity. Still avoid chasing at market if price is at resistance.**

  ### 68. New-Sector Breadth Expansion Confirms Narrow Market Ending, But CMF Gate Still Dominates (2026-08-28)
    - Full scan (696 tickers) produced an entirely NEW top-10 cluster: ARCB (trucking),
      MFC (insurance), ADM (agribusiness), KNX (trucking), NOV (oil services), ALB (lithium),
      BEN (asset mgmt), CF (ag inputs) — plus MU/APA already covered. This is the broadest
      sector diversification seen all month, confirming the narrow market (Lessons #8, #63)
      has ended.
    - Yet 5 of 8 new names failed the CMF filter (ARCB -0.124, MFC -0.316, ADM -0.067,
      KNX -0.12, BEN negative). The CMF gate (Lesson #28) remains the single most
      predictive pre-entry filter even as breadth expands. Only ALB (CMF positive) and CF
      (golden cross, but ADX 16.2) passed to pending — and both still gated (ADX, overbought).
    - **Rule: Breadth expansion != buyability. The same filters (CMF > +0.05, ADX > 20, not
      overbought, no OBV divergence) still eliminate ~75% of candidates even when the market
      widens. Do not lower standards just because new sectors appear.**
    - Also: ALB is a US-listed death-cross reversal (ADX 24.5 + positive CMF) — the first
      valid non-China application of the death_cross_strong_adx_cmf_positive signal since
      the BABA stop-out. Its outcome will test Lesson #58 (the China-ADR carve-out).

  ### 69. Expired Pending Entries Are Not Failures — They Confirm Momentum (NVDA, APA 2026-08-28)
    - Two pending entries expired simultaneously with no fill and no loss: NVDA (rallied
      8.4% above zone top) and APA (rallied 4.7% above zone top). Both were pullback entries
      placed near resistance; momentum continued without pausing, blowing through the zones.
    - This reinforces Lesson #34/#51: pullback entries placed during strong uptrends almost
      never trigger. The correct read was "wait for pullback" but the market didn't offer one.
    - **Rule: A pending entry expiring with no fill is a WIN in risk terms (no loss) but a
      MISS in opportunity terms. Move stale entries (price >5% above zone top, 3+ sessions)
      to closed_trades/ with return 0% rather than letting them clog pending_entries/.**

  ### 71. Writing a Lesson ≠ Applying It — Scan Open Positions Immediately (BABA Meta-Failure 2026-08-28)
      - Lesson #55 (death-cross stops max 5%) was written on 8/21 while BABA was still alive
        at $122.21. The stop was at $118.50 (7.5% from entry). The lesson was correct — but
        it was filed, not applied. Three days later, BABA stopped out at $118.28 (-7.65%).
        If the stop had been tightened to $121.68 (5%) the day Lesson #55 was written, the
        loss would have been -5.0% instead of -7.65% — a 2.65% capital savings.
      - **Rule: When a new lesson changes a rule, immediately scan every open position for
        that rule. If any position violates the new rule, fix the position — tighten the stop,
        adjust size, or exit. Do not wait for the next session. A lesson in a file that
        doesn't change behavior on a live position is just note-taking.**
      - This is a process-level lesson, not a signal-level one. The framework caught the
        problem (Lesson #55 was correct). The execution lagged behind the framework.

  ### 70. BP Pending on Life Support — Pullback Overshot the Zone (2026-08-28)
    - BP pending ($43-44.50 zone, stop $41.90) has fallen to $42.06 — only $0.16 (0.4%)
      above stop. The pullback that was correctly anticipated (overbought stochastics)
      overshot the zone entirely, similar to OXY (Lesson #61). Price is below SMA20.
    - **Rule: When an overbought stock's pullback overshoots the entry zone and price sits
      within ~0.5% of the stop, do NOT enter. The thesis is under pressure. If it closes
      below $41.90, expire the pending with no fill. The golden cross + positive CMF thesis
      may remain valid, but entry timing was wrong — wait for the pullback to fully resolve
      before setting a new zone (extending Lesson #61).**
      - UPDATE 2026-09-01: BP expired. CMF flipped from +0.066 to -0.104 (distribution) —
        the single most important gate deteriorated. ADX 14.9, MACD bearish, OBV falling.
        Per Lesson #18: no energy sector long without positive CMF. No fill, no loss.

    ### 72. CMF Can Deteriorate Rapidly — Always Re-Check Live at Trigger Time (BP 2026-09-01)
      - BP's CMF was +0.066 when the pending was created on 8/24. By 9/01, it had flipped
        to -0.104 — a complete reversal from accumulation to distribution. The price recovered
        into the zone ($43.73) but the flow had already turned against the thesis.
      - This is the mirror of Lesson #19 (rejection today ≠ rejection forever): a valid setup
        today can become invalid tomorrow if CMF flips. The CMF gate must be checked LIVE at
        trigger time, not assumed from the original analysis.
      - **Rule: For every pending entry, re-check CMF live before triggering. If CMF has
        flipped negative since the pending was created, expire the pending immediately —
        regardless of price action. A price inside the zone with negative CMF is a trap, not
        a trigger. (Extends Lesson #28.)**

    ### 73. CVX T1 Hit — Risk-Free on Remaining Half (2026-09-01)
      - CVX v2 (re-entry at $199.88 on 8/26) hit T1 at $208.91 (+4.1% on T1 portion) in
        just 4 sessions. Per Lesson #5 (defensive/low-beta names: prioritize T1 profit-taking),
        50% taken at T1. Stop raised to $200.00 (breakeven on remaining half). T2 $215 (+7.6%
        from entry) remains active.
      - This is the 4th winning trade from the golden_cross_oversold_cmf_positive signal
        (XOM x2, CVX x2). The signal is now 4-for-4 with zero false triggers.
      - **Rule: When a defensive/low-beta name hits T1, take 50% partial and raise stop to
        breakeven. The remaining half is a risk-free ride to T2. This is the CVX playbook.**

    ### 74. 7 of 10 Screening Candidates Fail CMF — The Filter Remains Dominant (2026-09-01)
      - Full scan (977 tickers) produced top 10: ALB, ARCB, BEN, ADM, ARW, APA, ALGN, BIDU,
        C, APPS. 7 of 10 fail CMF: ARCB (-0.018), BEN (-0.197), ADM (-0.05), BIDU (-0.077),
        C (-0.068), APPS (-0.024), ALB (-0.004). Only ARW (+0.12) and ALGN (+0.076) pass.
      - This is the 4th consecutive screening where CMF eliminates 70%+ of candidates. The
        CMF gate (Lesson #28) is not a temporary filter — it's a structural market feature.
      - **Rule: Expect CMF to eliminate ~70% of screening candidates in any market environment.
        This is not a narrow-market phenomenon — it's the normal operating baseline. The 2-3
        candidates that pass CMF are the only ones worth deep-diving.**

    ### 75. ARW: The CVX/XOM Pattern in a New Sector (Technology Distribution) (2026-09-01)
      - ARW has the exact CVX/XOM DNA (Lesson #21): golden cross + CMF +0.12 (strong
        accumulation) + StochRSI 24.4 (oversold). FA: PEG 0.95, fwd P/E 8.4x, 47% earnings
        growth. But ADX 14.5 (<20) — the trend hasn't formed yet.
      - This is the first time the golden_cross_oversold_cmf_positive pattern has appeared
        in a Technology distribution name (electronics/components). Prior triggers were all
        Energy (XOM, CVX) or Financials (BAC).
      - **Rule: When the CVX/XOM pattern appears in a new sector, treat it as a pending entry
        gated by ADX > 20. The pattern is 4-for-4 but all in defensive/cyclical sectors.
        Technology distribution may behave differently — size cautiously on first trigger.**

    ### 76. ALGN: The Corrected META Pattern — Death Cross + Extreme Oversold + Positive CMF (2026-09-01)
      - ALGN: StochRSI 8.8, CCI -1554.8 (extreme oversold), CMF +0.076 (accumulation),
        PEG 0.75, fwd P/E 12.7x, 31% analyst upside. Death cross active, Aroon Down 96.
        This is the META v2 pattern (Lesson #21/#35): death cross + extreme oversold +
        positive CMF + elite FA = mean-reversion trade.
      - The positive CMF is the critical differentiator from the META v1 failure (CMF -0.053).
        ADX 17.5 is approaching 20 — trend exhaustion is near.
      - **Rule: Death cross + extreme oversold (StochRSI < 10, CCI < -1000) + CMF > +0.05 +
        PEG < 1.0 = actionable mean-reversion setup. This is the corrected
        extreme_oversold_fa_backstop signal. Per Lesson #35: take 75% at T1 on death-cross
        reversals. Gated by ADX > 20 for entry.**

