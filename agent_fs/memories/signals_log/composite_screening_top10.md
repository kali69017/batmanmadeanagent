---
signal: composite_screening_top10
description: Top 10 by composite score using fundamental_quality*0.35 + momentum_12_1*0.35 + rsi_neutrality*0.15 + sharpe_ratio*0.15
triggered_correctly: 3
triggered_falsely: 2
notes: >
  Used to surface candidates from watchlist. Has correctly identified winners
  (CRM, AAPL, V, ABBV) but also surfaces momentum traps (RIOT, HUT, RKLB)
  when momentum dominates composite. Requires FA deep-dive cross-check.
  Most useful when composite scores >30 and candidates are from diverse sectors.
  When all scores <30, signals market narrowness — be patient.

  Recent hits: CRM (T1 hit +7.8%, running to T2), AAPL (T1 hit +4.3%, running to T2),
  V (T1 hit +4.0%, running to T2), SNOW (T1 hit +6.5%, running to T2).

  Recent misses: RKLB (rank #5, rejected — TA 35, FA 5, unprofitable, extreme distribution).
  META (rank #4, stopped out same day -8.7% — death cross + negative CMF).
  Lesson: high composite score driven by momentum alone is a trap if FA is poor.
  Lesson: death cross + negative CMF candidates should be excluded from screening.

  2026-07-31 update: RKLB correctly identified as momentum trap (momentum_12_1 +84%
  but below all SMAs, CMF -0.33). ABBV correctly surfaced as quality candidate
  (rank #2) but needs pullback entry. APH surfaced (rank #10) with elite FA but
  ADX 15.6 — correctly held back per Lesson #2. Screening continues to work as
  a first-pass filter when cross-checked with TA/FA deep-dives.
---