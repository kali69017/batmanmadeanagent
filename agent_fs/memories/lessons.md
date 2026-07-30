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
- Today's top score: CRM 26.5 — confirms narrow market conditions.

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