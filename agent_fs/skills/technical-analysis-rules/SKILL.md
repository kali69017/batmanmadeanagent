---
name: technical-analysis-rules
description: Use when the user asks about momentum, trend, support/resistance, volatility, volume confirmation, or RSI/MACD/Bollinger/Stochastic-type signals for a symbol on the watchlist. Explains which technical indicator tools to use and how to interpret them correctly.
---

# Technical Analysis Rules

## Available toolkit
`get_technical_analysis` returns ALL of the following in one call — use
it instead of calling individual technical tools separately:

- **Price data**: latest close, period return, 52-week high/low, avg volume
- **Trend**: SMA20/50/200, EMA12/26, MACD line/signal/histogram, ADX(14),
  Parabolic SAR, Aroon(25)
- **Momentum**: RSI(14), Stochastic %K/%D, CCI(20), Williams %R(14),
  ROC(12), Momentum(10), Stoch RSI(14)
- **Volatility**: Bollinger Bands(20,2), ATR(14), Keltner Channel(20,2),
  Donchian Channel(20), rolling stddev(20)
- **Volume**: OBV + multi-window trend + price divergence flag, VWAP(20),
  MFI(14), CMF(20), A/D Line, Volume Oscillator(5,20)
- **Pivot points**: Classic floor pivots (Pivot, R1-R3, S1-S3)

Do NOT call `get_price_data` separately for technical analysis — it's already included in `get_technical_analysis`.

## Rules
- Always state the specific indicator values behind your conclusions and
  the time horizon they apply to.
- Flag when multiple indicators disagree with each other rather than
  cherry-picking the one that supports a narrative.
- When asked whether a price move is volume-confirmed, check the
  `obv_price_divergence` field directly from the tool output — do not
  eyeball the raw OBV trend windows yourself.
- When asked about risk-adjusted return, use `get_risk_adjusted_returns`
  (see the `comparison-and-benchmarking-rules` skill).
- When asked whether a stock is genuinely outperforming the market, use
  `get_relative_strength` (see the `comparison-and-benchmarking-rules`
  skill) rather than judging from raw price action alone.
