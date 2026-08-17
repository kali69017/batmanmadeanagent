"""
Build a precomputed metrics summary across the entire watchlist from the
local yf_data/ cache. Run this after fetch_yfinance_data.py (or on a
schedule) to keep watchlist_summary.json fresh.

Usage:
    python build_watchlist_summary.py
"""

import json
import time
from datetime import datetime, timezone

import config
from tools import (
    get_price_data,
    get_fundamentals,
    get_technicals,
    get_risk_adjusted_returns,
    get_relative_strength,
    get_quant_factors,
)


def build_summary() -> dict:
    rows = {}
    for sym in config.WATCHLIST:
        entry = {"symbol": sym}
        try:
            price = json.loads(get_price_data(sym, period="6mo"))
            entry["period_return_pct"] = price.get("period_return_pct")
            entry["annualized_volatility_pct"] = price.get("annualized_volatility_pct")
            entry["pct_off_52wk_high"] = price.get("pct_off_52wk_high")
            entry["latest_close"] = price.get("latest_close")
        except Exception as e:
            entry["price_error"] = str(e)

        try:
            fund = json.loads(get_fundamentals(sym))
            for f in (
                "trailingPE",
                "forwardPE",
                "pegRatio",
                "priceToBook",
                "dividendYield",
                "revenueGrowth",
                "earningsGrowth",
                "marketCap",
                "sector",
                "industry",
                "recommendationKey",
            ):
                entry[f] = fund.get(f)
        except Exception as e:
            entry["fundamentals_error"] = str(e)

        try:
            tech = json.loads(get_technicals(sym))
            entry["rsi_14"] = tech.get("rsi_14")
            entry["macd_histogram"] = tech.get("macd_histogram")
            entry["technical_signals"] = tech.get("technical_signals")
        except Exception as e:
            entry["technicals_error"] = str(e)

        try:
            risk_adj = json.loads(get_risk_adjusted_returns(sym, period="1y"))
            for f in (
                "sharpe_ratio",
                "sortino_ratio",
                "max_drawdown_pct",
                "calmar_ratio",
            ):
                entry[f] = risk_adj.get(f)
        except Exception as e:
            entry["risk_adjusted_error"] = str(e)

        try:
            rel_strength = json.loads(
                get_relative_strength(sym, benchmark="SPY", period="6mo")
            )
            entry["excess_return_pct"] = rel_strength.get("excess_return_pct")
            entry["outperforming_spy"] = rel_strength.get("outperforming")
        except Exception as e:
            entry["relative_strength_error"] = str(e)

        try:
            qf = json.loads(get_quant_factors(sym))
            entry["composite_score"] = qf.get("composite_score")
            entry["momentum_12_1_pct"] = qf.get("momentum_12_1_pct")
        except Exception as e:
            entry["quant_factors_error"] = str(e)

        rows[sym] = entry
        time.sleep(0.15)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "watchlist": rows,
    }


if __name__ == "__main__":
    summary = build_summary()
    out_path = config.CACHE_DIR / "watchlist_summary.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    n_ok = sum(1 for r in summary["watchlist"].values() if "price_error" not in r)
    print(f"Wrote {out_path} — {n_ok}/{len(config.WATCHLIST)} symbols fully populated.")
    from tools import _save_intraday_cache

    _save_intraday_cache()
