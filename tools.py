import contextlib
import concurrent.futures
import functools
import io
import json
import os
import pickle
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

import config

_combined_history_df: pd.DataFrame | None = None
_intraday_cache: dict = {}
_intraday_ohlcv_cache: dict = {}


def _with_timeout(fn, seconds: float = 30.0, default=None):
    """Run `fn` in a worker thread and return its result, or `default` if it
    exceeds `seconds`.

    yfinance's `.history()` / `.info` / `.news` calls have no built-in timeout
    and block indefinitely under Yahoo rate-limiting — this is what hung whole
    scheduled scans for 12+ hours. On timeout the stuck thread is abandoned
    (shutdown wait=False) so the caller keeps moving.
    """
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    fut = ex.submit(fn)
    try:
        return fut.result(timeout=seconds)
    except concurrent.futures.TimeoutError:
        return default
    finally:
        ex.shutdown(wait=False)


# ---------------------------------------------------------------------------
# Intraday cache persistence
# ---------------------------------------------------------------------------
def _load_intraday_cache():
    global _intraday_cache, _intraday_ohlcv_cache
    try:
        if not config.INTRADAY_CACHE_FILE.exists():
            return
        age_min = (
            datetime.now().timestamp() - config.INTRADAY_CACHE_FILE.stat().st_mtime
        ) / 60
        if age_min > config.INTRADAY_CACHE_MINUTES:
            config.INTRADAY_CACHE_FILE.unlink(missing_ok=True)
            return
        with open(config.INTRADAY_CACHE_FILE, "rb") as f:
            saved = pickle.load(f)
        _intraday_cache = saved.get("tool_cache", {})
        for k, v in saved.get("ohlcv_cache", {}).items():
            df_dict = v.pop("df", {})
            _intraday_ohlcv_cache[k] = {**v, "df": pd.DataFrame.from_dict(df_dict)}
    except Exception:
        _intraday_cache = {}
        _intraday_ohlcv_cache = {}


def _save_intraday_cache():
    try:
        with open(config.INTRADAY_CACHE_FILE, "wb") as f:
            pickle.dump(
                {
                    "tool_cache": _intraday_cache,
                    "ohlcv_cache": {
                        k: {
                            "fetched_at": v["fetched_at"],
                            "df": (
                                v["df"].to_dict() if hasattr(v["df"], "to_dict") else {}
                            ),
                        }
                        for k, v in _intraday_ohlcv_cache.items()
                    },
                },
                f,
            )
    except Exception:
        pass


_load_intraday_cache()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _check_symbol(symbol: str) -> str:
    sym = symbol.strip().upper()
    if sym not in config.WATCHLIST:
        raise ValueError(
            f"'{symbol}' is not in the approved watchlist ({len(config.WATCHLIST)} tickers)."
        )
    return sym


def _check_benchmark(benchmark: str) -> str:
    bench = benchmark.strip().upper()
    if bench not in config.ALLOWED_BENCHMARKS:
        raise ValueError(
            f"'{benchmark}' is not an approved benchmark. "
            f"Allowed benchmarks: {', '.join(config.ALLOWED_BENCHMARKS)}"
        )
    return bench


def _tool_guard(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            return json.dumps({"error": f"Unexpected error in {fn.__name__}: {e}"})

    return wrapper


# ---------------------------------------------------------------------------
# Cache low-level
# ---------------------------------------------------------------------------
def _cache_file_path(symbol: str) -> Path:
    return config.CACHE_DIR / f"{symbol}.json"


def _cache_is_stale(
    path: Path, max_age_hours: float = config.CACHE_MAX_AGE_HOURS
) -> bool:
    if not path.exists():
        return True
    age_hours = (datetime.now().timestamp() - path.stat().st_mtime) / 3600
    return age_hours > max_age_hours


def _load_cached_symbol_json(symbol: str) -> dict | None:
    path = _cache_file_path(symbol)
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _intraday_get(symbol: str, tool_name: str) -> dict | None:
    if config.INTRADAY_CACHE_MINUTES <= 0:
        return None
    key = f"{symbol}:{tool_name}"
    entry = _intraday_cache.get(key)
    if entry is None:
        return None
    age_minutes = (datetime.now().timestamp() - entry["fetched_at"]) / 60
    if age_minutes > config.INTRADAY_CACHE_MINUTES:
        return None
    return entry["data"]


def _intraday_set(symbol: str, tool_name: str, data: dict) -> None:
    _intraday_cache[f"{symbol}:{tool_name}"] = {
        "data": data,
        "fetched_at": datetime.now().timestamp(),
    }


def _load_combined_history() -> pd.DataFrame | None:
    global _combined_history_df
    if not config.COMBINED_HISTORY_PATH.exists():
        _combined_history_df = None
        return None
    if _cache_is_stale(
        config.COMBINED_HISTORY_PATH, max_age_hours=config.HISTORY_CSV_MAX_AGE_HOURS
    ):
        _combined_history_df = None
        return None
    if _combined_history_df is not None:
        return _combined_history_df
    try:
        df = pd.read_csv(config.COMBINED_HISTORY_PATH)
        df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_localize(None)
        _combined_history_df = df
        return df
    except (OSError, pd.errors.ParserError, ValueError, KeyError):
        return None


def _history_from_cache(symbol: str, period: str) -> pd.DataFrame | None:
    df = _load_combined_history()
    if df is None:
        return None
    sym_df = df[df["Symbol"] == symbol].sort_values("Date")
    if sym_df.empty:
        return None
    period_days = {
        "1mo": 30,
        "3mo": 91,
        "6mo": 182,
        "1y": 365,
        "2y": 730,
        "5y": 1825,
    }
    if period == "max":
        return sym_df.set_index("Date")
    days = period_days.get(period)
    if days is None:
        return None
    cutoff = sym_df["Date"].max() - pd.Timedelta(days=days)
    windowed = sym_df[sym_df["Date"] >= cutoff]
    return windowed.set_index("Date")


def _intraday_ohlcv_get(symbol: str, period: str) -> pd.DataFrame | None:
    if config.INTRADAY_CACHE_MINUTES <= 0:
        return None
    key = f"{symbol}:{period}"
    entry = _intraday_ohlcv_cache.get(key)
    if entry is None:
        return None
    age_minutes = (datetime.now().timestamp() - entry["fetched_at"]) / 60
    if age_minutes > config.INTRADAY_CACHE_MINUTES:
        return None
    return entry["df"]


def _intraday_ohlcv_set(symbol: str, period: str, df: pd.DataFrame) -> None:
    _intraday_ohlcv_cache[f"{symbol}:{period}"] = {
        "df": df,
        "fetched_at": datetime.now().timestamp(),
    }


def _get_ohlcv(
    symbol: str, period: str = "1y", force_refresh: bool = False
) -> pd.DataFrame | None:
    cached_ohlcv = _intraday_ohlcv_get(symbol, period)
    if cached_ohlcv is not None:
        return cached_ohlcv
    hist = None
    if not force_refresh:
        hist = _history_from_cache(symbol, period)
    if hist is None or hist.empty:
        hist = _with_timeout(
            lambda: yf.Ticker(symbol).history(
                period=period, interval="1d", auto_adjust=True
            ),
            30.0,
            None,
        )
    if hist is not None and not hist.empty:
        _intraday_ohlcv_set(symbol, period, hist)
    if hist is None or hist.empty:
        return None
    hist = hist.dropna(subset=["Close"])
    required_cols = {"Open", "High", "Low", "Close", "Volume"}
    if not required_cols.issubset(hist.columns):
        return None
    return hist


def _get_benchmark_ohlcv(benchmark: str, period: str = "1y") -> pd.DataFrame | None:
    try:
        hist = yf.Ticker(benchmark).history(
            period=period, interval="1d", auto_adjust=True
        )
    except Exception:
        return None
    if hist is None or hist.empty:
        return None
    hist = hist.dropna(subset=["Close"])
    return hist


# ---------------------------------------------------------------------------
# Tool: Price data
# ---------------------------------------------------------------------------
@_tool_guard
def get_price_data(
    symbol: str, period: str = "6mo", force_refresh: bool = False
) -> str:
    """Get OHLCV price history and return statistics for a single symbol."""
    sym = _check_symbol(symbol)
    source = "live"
    cache_key = f"price_data_{period}"
    if not force_refresh:
        cached_intraday = _intraday_get(sym, cache_key)
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    if not force_refresh:
        cached_hist = _history_from_cache(sym, period)
        if cached_hist is not None and not cached_hist.empty:
            hist = cached_hist
            yr_hist = _history_from_cache(sym, "1y")
            if yr_hist is None or yr_hist.empty:
                yr_hist = yf.Ticker(sym).history(
                    period="1y", interval="1d", auto_adjust=True
                )
            else:
                yr_hist = yr_hist
            source = "cache"
        else:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period=period, interval="1d", auto_adjust=True)
            yr_hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
    else:
        ticker = yf.Ticker(sym)
        hist = ticker.history(period=period, interval="1d", auto_adjust=True)
        yr_hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
    if hist.empty:
        return json.dumps(
            {"symbol": sym, "error": "No price data returned.", "source": source}
        )
    close = hist["Close"].dropna()
    if close.empty:
        return json.dumps(
            {"symbol": sym, "error": "No valid close prices.", "source": source}
        )
    daily_returns = close.pct_change().dropna()
    period_return_pct = (close.iloc[-1] / close.iloc[0] - 1) * 100
    annualized_vol_pct = daily_returns.std() * np.sqrt(252) * 100
    fifty_two_wk_high = float(yr_hist["High"].max()) if not yr_hist.empty else None
    fifty_two_wk_low = float(yr_hist["Low"].min()) if not yr_hist.empty else None
    result = {
        "symbol": sym,
        "period": period,
        "latest_close": round(float(close.iloc[-1]), 2),
        "period_return_pct": round(float(period_return_pct), 2),
        "annualized_volatility_pct": round(float(annualized_vol_pct), 2),
        "52wk_high": round(fifty_two_wk_high, 2) if fifty_two_wk_high else None,
        "52wk_low": round(fifty_two_wk_low, 2) if fifty_two_wk_low else None,
        "pct_off_52wk_high": (
            round((close.iloc[-1] / fifty_two_wk_high - 1) * 100, 2)
            if fifty_two_wk_high
            else None
        ),
        "avg_volume_20d": (
            int(hist["Volume"].tail(20).mean()) if len(hist) >= 20 else None
        ),
        "as_of": str(close.index[-1].date()),
        "source": source,
    }
    _intraday_set(sym, cache_key, result)
    return json.dumps(result)


def _add_upside_fields(result: dict, info: dict) -> dict:
    current_price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
    )
    for target_key, upside_key in [
        ("targetMeanPrice", "upside_to_mean_target_pct"),
        ("targetHighPrice", "upside_to_high_target_pct"),
        ("targetLowPrice", "upside_to_low_target_pct"),
    ]:
        target_val = result.get(target_key)
        if target_val and current_price and current_price > 0:
            pct = (target_val / current_price - 1) * 100
            result[upside_key] = round(pct, 1)
            tag = "upside" if pct >= 0 else "downside"
            label_target = (
                "mean"
                if "Mean" in target_key
                else "high" if "High" in target_key else "low"
            )
            result[f"{upside_key}_label"] = (
                f"{tag} of {abs(round(pct, 1))}% " f"to analyst {label_target} target"
            )
        else:
            result[upside_key] = None
            result[f"{upside_key}_label"] = "unavailable"
    result["current_price_used_for_upside"] = current_price
    return result


# ---------------------------------------------------------------------------
# Tool: Fundamentals
# ---------------------------------------------------------------------------
@_tool_guard
def get_fundamentals(symbol: str, force_refresh: bool = False) -> str:
    """Get key fundamental/valuation metrics for a symbol from yfinance."""
    sym = _check_symbol(symbol)
    if not force_refresh:
        cached = _load_cached_symbol_json(sym)
        if cached and cached.get("info"):
            info = cached["info"]
            result = {"symbol": sym, "source": "cache"}
            for f in config.FUNDAMENTALS_FIELDS:
                result[f] = info.get(f)
            _add_upside_fields(result, info)
            return json.dumps(result)
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "fundamentals")
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    info = _with_timeout(lambda: yf.Ticker(sym).info, 30.0, {}) or {}
    result = {"symbol": sym, "source": "live"}
    for f in config.FUNDAMENTALS_FIELDS:
        result[f] = info.get(f)
    _add_upside_fields(result, info)
    _intraday_set(sym, "fundamentals", result)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Technicals (simple, internal — called by get_technical_analysis)
# ---------------------------------------------------------------------------
@_tool_guard
def get_technicals(symbol: str, force_refresh: bool = False) -> str:
    """Compute basic technical indicators: SMA(20/50/200), RSI(14), MACD, and a simple trend signal."""
    sym = _check_symbol(symbol)
    source = "live"
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "technicals")
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    if not force_refresh:
        hist = _history_from_cache(sym, "1y")
        if hist is not None and not hist.empty:
            source = "cache"
    else:
        hist = None
    if hist is None or hist.empty or len(hist) < 50:
        hist = yf.Ticker(sym).history(period="1y", interval="1d", auto_adjust=True)
        source = "live"
    if hist.empty or len(hist) < 50:
        return json.dumps(
            {"symbol": sym, "error": "Insufficient price history.", "source": source}
        )
    close = hist["Close"].dropna()
    if close.empty:
        return json.dumps(
            {"symbol": sym, "error": "No valid close prices.", "source": source}
        )
    high, low = hist["High"], hist["Low"]
    import pandas_ta as ta

    sma20 = ta.sma(close, length=20).iloc[-1]
    sma50 = ta.sma(close, length=50).iloc[-1]
    sma200 = ta.sma(close, length=200).iloc[-1] if len(close) >= 200 else None
    rsi_series = ta.rsi(close, length=14)
    rsi = rsi_series.iloc[-1] if rsi_series is not None else None
    macd_result = ta.macd(close, fast=12, slow=26, signal=9)
    macd_hist = (
        macd_result["MACDh_12_26_9"].iloc[-1] if macd_result is not None else None
    )
    price = close.iloc[-1]
    signals = []
    if price > sma20:
        signals.append("above SMA20")
    else:
        signals.append("below SMA20")
    if sma200 is not None:
        if sma50 > sma200:
            signals.append("golden cross zone (SMA50 > SMA200)")
        else:
            signals.append("death cross zone (SMA50 < SMA200)")
    if rsi > 70:
        signals.append("RSI overbought (>70)")
    elif rsi < 30:
        signals.append("RSI oversold (<30)")
    else:
        signals.append("RSI neutral")
    signals.append("MACD bullish" if macd_hist > 0 else "MACD bearish")
    result = {
        "symbol": sym,
        "price": round(float(price), 2),
        "sma20": round(float(sma20), 2),
        "sma50": round(float(sma50), 2),
        "sma200": round(float(sma200), 2) if sma200 is not None else None,
        "rsi_14": round(float(rsi), 1) if not pd.isna(rsi) else None,
        "macd_histogram": round(float(macd_hist), 3),
        "signals": signals,
        "source": source,
    }
    _intraday_set(sym, "technicals", result)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Trend indicators (internal — called by get_technical_analysis)
# ---------------------------------------------------------------------------
@_tool_guard
def get_trend_indicators(symbol: str, force_refresh: bool = False) -> str:
    """Compute trend-following indicators: EMA(12/26), MACD, ADX(14), Parabolic SAR, and Aroon(25)."""
    sym = _check_symbol(symbol)
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "trend_indicators")
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    hist = _get_ohlcv(sym, period="1y", force_refresh=force_refresh)
    if hist is None or len(hist) < 30:
        return json.dumps({"symbol": sym, "error": "Insufficient OHLCV history."})
    import pandas_ta as ta

    o, h, l, c, v = (
        hist["Open"],
        hist["High"],
        hist["Low"],
        hist["Close"],
        hist["Volume"],
    )
    ema12 = ta.ema(c, length=12)
    ema26 = ta.ema(c, length=26)
    macd_result = ta.macd(c, fast=12, slow=26, signal=9)
    macd_line = (
        macd_result["MACD_12_26_9"]
        if macd_result is not None
        else pd.Series(index=c.index, dtype=float)
    )
    macd_signal = (
        macd_result["MACDs_12_26_9"]
        if macd_result is not None
        else pd.Series(index=c.index, dtype=float)
    )
    macd_hist = (
        macd_result["MACDh_12_26_9"]
        if macd_result is not None
        else pd.Series(index=c.index, dtype=float)
    )
    adx_result = ta.adx(h, l, c, length=14)
    adx14 = (
        adx_result["ADX_14"]
        if adx_result is not None
        else pd.Series(index=c.index, dtype=float)
    )
    psar_result = ta.psar(h, l, c, af=0.02, max_af=0.2)
    if psar_result is not None:
        sar_col = [
            col
            for col in psar_result.columns
            if "PSAR" in col.upper() or "sar" in col.lower()
        ]
        psar = (
            psar_result[sar_col[0]]
            if sar_col
            else pd.Series(index=c.index, dtype=float)
        )
    else:
        psar = pd.Series(index=c.index, dtype=float)
    aroon_result = ta.aroon(h, l, length=25)
    aroon_up = (
        aroon_result["AROONU_25"]
        if aroon_result is not None
        else pd.Series(index=c.index, dtype=float)
    )
    aroon_down = (
        aroon_result["AROOND_25"]
        if aroon_result is not None
        else pd.Series(index=c.index, dtype=float)
    )
    result = {
        "symbol": sym,
        "ema12": round(float(ema12.iloc[-1]), 2),
        "ema26": round(float(ema26.iloc[-1]), 2),
        "macd_line": round(float(macd_line.iloc[-1]), 3),
        "macd_signal": round(float(macd_signal.iloc[-1]), 3),
        "macd_histogram": round(float(macd_hist.iloc[-1]), 3),
        "adx_14": (
            round(float(adx14.iloc[-1]), 1) if not pd.isna(adx14.iloc[-1]) else None
        ),
        "adx_trend_strength": (
            "strong trend"
            if not pd.isna(adx14.iloc[-1]) and adx14.iloc[-1] > 25
            else "weak/no trend" if not pd.isna(adx14.iloc[-1]) else None
        ),
        "parabolic_sar": round(float(psar.iloc[-1]), 2),
        "sar_signal": (
            "bullish (price above SAR)"
            if c.iloc[-1] > psar.iloc[-1]
            else "bearish (price below SAR)"
        ),
        "aroon_up_25": (
            round(float(aroon_up.iloc[-1]), 1)
            if not pd.isna(aroon_up.iloc[-1])
            else None
        ),
        "aroon_down_25": (
            round(float(aroon_down.iloc[-1]), 1)
            if not pd.isna(aroon_down.iloc[-1])
            else None
        ),
    }
    _intraday_set(sym, "trend_indicators", result)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Momentum indicators (internal — called by get_technical_analysis)
# ---------------------------------------------------------------------------
@_tool_guard
def get_momentum_indicators(symbol: str, force_refresh: bool = False) -> str:
    """Compute momentum/oscillator indicators: Stochastic, CCI(20), Williams %R(14), ROC(12), Momentum(10), StochRSI(14)."""
    sym = _check_symbol(symbol)
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "momentum_indicators")
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    hist = _get_ohlcv(sym, period="1y", force_refresh=force_refresh)
    if hist is None or len(hist) < 30:
        return json.dumps({"symbol": sym, "error": "Insufficient OHLCV history."})
    import pandas_ta as ta

    o, h, l, c, v = (
        hist["Open"],
        hist["High"],
        hist["Low"],
        hist["Close"],
        hist["Volume"],
    )
    stoch_result = ta.stoch(h, l, c, k=14, d=3)
    pct_k = (
        stoch_result["STOCHk_14_3_3"]
        if stoch_result is not None
        else pd.Series(index=c.index, dtype=float)
    )
    pct_d = (
        stoch_result["STOCHd_14_3_3"]
        if stoch_result is not None
        else pd.Series(index=c.index, dtype=float)
    )
    cci20 = ta.cci(h, l, c, length=20)
    williams_r = ta.willr(h, l, c, length=14)
    roc12 = ta.roc(c, length=12)
    momentum10 = ta.mom(c, length=10)
    stoch_rsi_result = ta.stochrsi(c, length=14)
    stoch_rsi = (
        stoch_rsi_result["STOCHRSIk_14_14_3_3"]
        if stoch_rsi_result is not None
        else pd.Series(index=c.index, dtype=float)
    )

    def safe_round(x, nd=2):
        return round(float(x), nd) if not pd.isna(x) else None

    result = {
        "symbol": sym,
        "stoch_pct_k": safe_round(pct_k.iloc[-1], 1),
        "stoch_pct_d": safe_round(pct_d.iloc[-1], 1),
        "stoch_signal": (
            "overbought"
            if not pd.isna(pct_k.iloc[-1]) and pct_k.iloc[-1] > 80
            else (
                "oversold"
                if not pd.isna(pct_k.iloc[-1]) and pct_k.iloc[-1] < 20
                else "neutral"
            )
        ),
        "cci_20": safe_round(cci20.iloc[-1], 1),
        "cci_signal": (
            "overbought"
            if not pd.isna(cci20.iloc[-1]) and cci20.iloc[-1] > 100
            else (
                "oversold"
                if not pd.isna(cci20.iloc[-1]) and cci20.iloc[-1] < -100
                else "neutral"
            )
        ),
        "williams_r_14": safe_round(williams_r.iloc[-1], 1),
        "williams_r_signal": (
            "overbought"
            if not pd.isna(williams_r.iloc[-1]) and williams_r.iloc[-1] > -20
            else (
                "oversold"
                if not pd.isna(williams_r.iloc[-1]) and williams_r.iloc[-1] < -80
                else "neutral"
            )
        ),
        "roc_12": safe_round(roc12.iloc[-1], 2),
        "momentum_10": safe_round(momentum10.iloc[-1], 2),
        "stoch_rsi_14": safe_round(stoch_rsi.iloc[-1], 1),
    }
    _intraday_set(sym, "momentum_indicators", result)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Volatility indicators (internal — called by get_technical_analysis)
# ---------------------------------------------------------------------------
@_tool_guard
def get_volatility_indicators(symbol: str, force_refresh: bool = False) -> str:
    """Compute volatility indicators: Bollinger Bands(20,2), ATR(14), Keltner Channel(20,2), Donchian Channel(20)."""
    sym = _check_symbol(symbol)
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "volatility_indicators")
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    hist = _get_ohlcv(sym, period="1y", force_refresh=force_refresh)
    if hist is None or len(hist) < 30:
        return json.dumps({"symbol": sym, "error": "Insufficient OHLCV history."})
    import pandas_ta as ta

    o, h, l, c, v = (
        hist["Open"],
        hist["High"],
        hist["Low"],
        hist["Close"],
        hist["Volume"],
    )
    bb_result = ta.bbands(c, length=20, lower_std=2, upper_std=2)
    if bb_result is not None:
        bb_upper = bb_result["BBU_20_2_2"]
        bb_mid = bb_result["BBM_20_2_2"]
        bb_lower = bb_result["BBL_20_2_2"]
        bb_pct_b = bb_result["BBB_20_2_2"]
    else:
        bb_upper = bb_mid = bb_lower = bb_pct_b = pd.Series(index=c.index, dtype=float)
    sma20 = bb_mid
    atr14 = ta.atr(h, l, c, length=14)
    kc_result = ta.kc(h, l, c, length=20, scalar=2)
    if kc_result is not None:
        kc_upper = kc_result["KCUe_20_2"]
        kc_lower = kc_result["KCLe_20_2"]
    else:
        kc_upper = kc_lower = pd.Series(index=c.index, dtype=float)
    donchian_result = ta.donchian(h, l, length=20)
    if donchian_result is not None:
        donchian_upper = donchian_result["DCU_20_20"]
        donchian_lower = donchian_result["DCL_20_20"]
    else:
        donchian_upper = donchian_lower = pd.Series(index=c.index, dtype=float)
    std20 = c.rolling(20).std()

    def safe_round(x, nd=2):
        return round(float(x), nd) if not pd.isna(x) else None

    result = {
        "symbol": sym,
        "price": safe_round(c.iloc[-1]),
        "bollinger_upper": safe_round(bb_upper.iloc[-1]),
        "bollinger_mid_sma20": safe_round(sma20.iloc[-1]),
        "bollinger_lower": safe_round(bb_lower.iloc[-1]),
        "bollinger_pct_b": safe_round(bb_pct_b.iloc[-1], 3),
        "bollinger_signal": (
            "near/above upper band"
            if not pd.isna(bb_pct_b.iloc[-1]) and bb_pct_b.iloc[-1] > 0.95
            else (
                "near/below lower band"
                if not pd.isna(bb_pct_b.iloc[-1]) and bb_pct_b.iloc[-1] < 0.05
                else "mid-range"
            )
        ),
        "atr_14": safe_round(atr14.iloc[-1]),
        "atr_pct_of_price": (
            safe_round(100 * atr14.iloc[-1] / c.iloc[-1], 2)
            if not pd.isna(atr14.iloc[-1])
            else None
        ),
        "keltner_upper": safe_round(kc_upper.iloc[-1]),
        "keltner_lower": safe_round(kc_lower.iloc[-1]),
        "rolling_stddev_20": safe_round(std20.iloc[-1]),
        "donchian_upper_20": safe_round(donchian_upper.iloc[-1]),
        "donchian_lower_20": safe_round(donchian_lower.iloc[-1]),
    }
    _intraday_set(sym, "volatility_indicators", result)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Volume indicators (internal — called by get_technical_analysis)
# ---------------------------------------------------------------------------
@_tool_guard
def get_volume_indicators(symbol: str, force_refresh: bool = False) -> str:
    """Compute volume-based indicators: OBV, VWAP, MFI(14), CMF(20), A/D Line, Volume Oscillator."""
    sym = _check_symbol(symbol)
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "volume_indicators")
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    hist = _get_ohlcv(sym, period="1y", force_refresh=force_refresh)
    if hist is None or len(hist) < 30:
        return json.dumps({"symbol": sym, "error": "Insufficient OHLCV history."})
    import pandas_ta as ta

    o, h, l, c, v = (
        hist["Open"],
        hist["High"],
        hist["Low"],
        hist["Close"],
        hist["Volume"],
    )
    obv = ta.obv(c, v)

    def _obv_change_pct(periods: int):
        if len(obv) <= periods:
            return None
        past = obv.iloc[-(periods + 1)]
        now = obv.iloc[-1]
        if past == 0:
            return None
        return 100 * (now - past) / abs(past)

    def _price_change_pct(periods: int):
        if len(c) <= periods:
            return None
        past = c.iloc[-(periods + 1)]
        now = c.iloc[-1]
        if past == 0:
            return None
        return 100 * (now - past) / past

    obv_chg_5d = _obv_change_pct(5)
    obv_chg_20d = _obv_change_pct(20)
    obv_chg_60d = _obv_change_pct(60)
    obv_chg_6mo = _obv_change_pct(min(126, len(obv) - 1))
    price_chg_6mo = _price_change_pct(min(126, len(c) - 1))

    def _trend_label(chg):
        if chg is None:
            return None
        return "rising" if chg > 0 else "falling" if chg < 0 else "flat"

    divergence = None
    if obv_chg_6mo is not None and price_chg_6mo is not None:
        if price_chg_6mo > 5 and obv_chg_6mo < 0:
            divergence = "bearish divergence: price up over 6mo while OBV down — rally not confirmed by cumulative volume"
        elif price_chg_6mo < -5 and obv_chg_6mo > 0:
            divergence = "bullish divergence: price down over 6mo while OBV up — selloff not confirmed by cumulative volume"
        else:
            divergence = (
                "no major divergence: OBV and price direction broadly agree over 6mo"
            )
    typical_price = (h + l + c) / 3
    vwap20 = (
        ta.vwap(h, l, c, v).rolling(20).mean()
        if hasattr(ta, "vwap")
        else (typical_price * v).rolling(20).sum() / v.rolling(20).sum()
    )
    mfi14 = ta.mfi(h, l, c, v, length=14)
    cmf20 = ta.cmf(h, l, c, v, length=20)
    ad_line = ta.ad(h, l, c, v)
    vol_sma5 = v.rolling(5).mean()
    vol_sma20 = v.rolling(20).mean()
    vol_osc = 100 * (vol_sma5 - vol_sma20) / vol_sma20

    def safe_round(x, nd=2):
        return round(float(x), nd) if not pd.isna(x) else None

    result = {
        "symbol": sym,
        "obv": safe_round(obv.iloc[-1], 0),
        "obv_trend_5d": _trend_label(obv_chg_5d),
        "obv_trend_20d": _trend_label(obv_chg_20d),
        "obv_trend_60d": _trend_label(obv_chg_60d),
        "obv_trend_6mo": _trend_label(obv_chg_6mo),
        "obv_pct_change_6mo": (
            round(obv_chg_6mo, 1) if obv_chg_6mo is not None else None
        ),
        "price_pct_change_6mo": (
            round(price_chg_6mo, 1) if price_chg_6mo is not None else None
        ),
        "obv_price_divergence": divergence,
        "vwap_20d": safe_round(vwap20.iloc[-1]),
        "price_vs_vwap": "above VWAP" if c.iloc[-1] > vwap20.iloc[-1] else "below VWAP",
        "mfi_14": safe_round(mfi14.iloc[-1], 1),
        "mfi_signal": (
            "overbought"
            if not pd.isna(mfi14.iloc[-1]) and mfi14.iloc[-1] > 80
            else (
                "oversold"
                if not pd.isna(mfi14.iloc[-1]) and mfi14.iloc[-1] < 20
                else "neutral"
            )
        ),
        "chaikin_money_flow_20": safe_round(cmf20.iloc[-1], 3),
        "cmf_signal": (
            "accumulation"
            if not pd.isna(cmf20.iloc[-1]) and cmf20.iloc[-1] > 0
            else "distribution"
        ),
        "accumulation_distribution_line": safe_round(ad_line.iloc[-1], 0),
        "volume_oscillator_5_20": safe_round(vol_osc.iloc[-1], 1),
    }
    _intraday_set(sym, "volume_indicators", result)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Pivot points (internal — called by get_technical_analysis)
# ---------------------------------------------------------------------------
@_tool_guard
def get_pivot_points(symbol: str, force_refresh: bool = False) -> str:
    """Compute classic floor-trader pivot points (Pivot, R1-R3, S1-S3)."""
    sym = _check_symbol(symbol)
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "pivot_points")
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    hist = _get_ohlcv(sym, period="1mo", force_refresh=force_refresh)
    if hist is None or len(hist) < 2:
        return json.dumps({"symbol": sym, "error": "Insufficient OHLCV history."})
    prior = hist.iloc[-2]
    ph, pl, pc = float(prior["High"]), float(prior["Low"]), float(prior["Close"])
    current_price = float(hist["Close"].iloc[-1])
    pivot = (ph + pl + pc) / 3
    r1 = 2 * pivot - pl
    s1 = 2 * pivot - ph
    r2 = pivot + (ph - pl)
    s2 = pivot - (ph - pl)
    r3 = ph + 2 * (pivot - pl)
    s3 = pl - 2 * (ph - pivot)
    levels = {
        "S3": s3,
        "S2": s2,
        "S1": s1,
        "Pivot": pivot,
        "R1": r1,
        "R2": r2,
        "R3": r3,
    }
    nearest_level = min(levels.items(), key=lambda kv: abs(kv[1] - current_price))
    result = {
        "symbol": sym,
        "current_price": round(current_price, 2),
        "pivot": round(pivot, 2),
        "r1": round(r1, 2),
        "r2": round(r2, 2),
        "r3": round(r3, 2),
        "s1": round(s1, 2),
        "s2": round(s2, 2),
        "s3": round(s3, 2),
        "nearest_level": nearest_level[0],
        "position": "above pivot" if current_price > pivot else "below pivot",
    }
    _intraday_set(sym, "pivot_points", result)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Relative strength vs benchmark
# ---------------------------------------------------------------------------
@_tool_guard
def get_relative_strength(
    symbol: str,
    benchmark: str = "SPY",
    period: str = "6mo",
    force_refresh: bool = False,
) -> str:
    """Compare a symbol's performance against a benchmark index."""
    sym = _check_symbol(symbol)
    bench = _check_benchmark(benchmark)
    rs_cache_key = f"relative_strength_{bench}_{period}"
    if not force_refresh:
        cached_intraday = _intraday_get(sym, rs_cache_key)
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    sym_hist = None
    if not force_refresh:
        sym_hist = _history_from_cache(sym, period)
    if sym_hist is None or sym_hist.empty:
        sym_hist = yf.Ticker(sym).history(
            period=period, interval="1d", auto_adjust=True
        )
    if sym_hist is None or sym_hist.empty:
        return json.dumps({"symbol": sym, "error": "No price data for symbol."})
    sym_hist = sym_hist.dropna(subset=["Close"])
    bench_hist = _get_benchmark_ohlcv(bench, period=period)
    if bench_hist is None or bench_hist.empty:
        return json.dumps(
            {"symbol": sym, "benchmark": bench, "error": "No price data for benchmark."}
        )
    sym_close = sym_hist["Close"]
    bench_close = bench_hist["Close"]
    sym_close.index = pd.to_datetime(sym_close.index).tz_localize(None).normalize()
    bench_close.index = pd.to_datetime(bench_close.index).tz_localize(None).normalize()
    aligned = pd.concat(
        [sym_close.rename("sym"), bench_close.rename("bench")], axis=1, join="inner"
    ).dropna()
    if len(aligned) < 10:
        return json.dumps(
            {
                "symbol": sym,
                "benchmark": bench,
                "error": "Insufficient overlapping history to compare.",
            }
        )
    sym_return_pct = (sym_close.iloc[-1] / sym_close.iloc[0] - 1) * 100
    bench_return_pct = (bench_close.iloc[-1] / bench_close.iloc[0] - 1) * 100
    excess_return_pct = sym_return_pct - bench_return_pct
    rs_line = aligned["sym"] / aligned["bench"]
    rs_line_normalized = 100 * rs_line / rs_line.iloc[0]
    rs_trend_5d = (
        "rising"
        if rs_line_normalized.iloc[-1] > rs_line_normalized.iloc[-6]
        else "falling" if len(rs_line_normalized) > 6 else None
    )
    read = (
        f"{sym} {'outperformed' if excess_return_pct > 0 else 'underperformed'} "
        f"{bench} by {abs(round(excess_return_pct, 1))} percentage points over {period}."
    )
    result = {
        "symbol": sym,
        "benchmark": bench,
        "period": period,
        "symbol_return_pct": round(float(sym_return_pct), 2),
        "benchmark_return_pct": round(float(bench_return_pct), 2),
        "excess_return_pct": round(float(excess_return_pct), 2),
        "relative_strength_trend_5d": rs_trend_5d,
        "outperforming": bool(excess_return_pct > 0),
        "read": read,
    }
    _intraday_set(sym, rs_cache_key, result)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Risk-adjusted returns
# ---------------------------------------------------------------------------
@_tool_guard
def get_risk_adjusted_returns(
    symbol: str, period: str = "1y", force_refresh: bool = False
) -> str:
    """Compute risk-adjusted return metrics: Sharpe, Sortino, max drawdown, Calmar."""
    sym = _check_symbol(symbol)
    ra_cache_key = f"risk_adjusted_{period}"
    if not force_refresh:
        cached_intraday = _intraday_get(sym, ra_cache_key)
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    hist = None
    if not force_refresh:
        hist = _history_from_cache(sym, period)
    if hist is None or hist.empty:
        hist = yf.Ticker(sym).history(period=period, interval="1d", auto_adjust=True)
    if hist is None or hist.empty or len(hist) < 30:
        return json.dumps({"symbol": sym, "error": "Insufficient price history."})
    close = hist["Close"].dropna()
    daily_returns = close.pct_change().dropna()
    trading_days_per_year = 252
    n_days = len(daily_returns)
    total_return = close.iloc[-1] / close.iloc[0] - 1
    annualized_return = (1 + total_return) ** (trading_days_per_year / n_days) - 1
    annualized_vol = daily_returns.std() * np.sqrt(trading_days_per_year)
    daily_rf = config.RISK_FREE_RATE_ANNUAL / trading_days_per_year
    excess_daily_returns = daily_returns - daily_rf
    sharpe = (
        (excess_daily_returns.mean() / excess_daily_returns.std())
        * np.sqrt(trading_days_per_year)
        if excess_daily_returns.std() != 0
        else None
    )
    downside_returns = excess_daily_returns[excess_daily_returns < 0]
    downside_std = downside_returns.std()
    sortino = (
        (excess_daily_returns.mean() / downside_std) * np.sqrt(trading_days_per_year)
        if downside_std and downside_std != 0
        else None
    )
    cumulative = (1 + daily_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown_pct = drawdown.min() * 100
    calmar = (
        annualized_return / abs(max_drawdown_pct / 100)
        if max_drawdown_pct != 0
        else None
    )

    def safe_round(x, nd=2):
        return round(float(x), nd) if x is not None and not pd.isna(x) else None

    result = {
        "symbol": sym,
        "period": period,
        "actual_trading_days_used": n_days,
        "actual_years_used": round(n_days / 252, 1),
        "annualized_return_pct": safe_round(annualized_return * 100),
        "annualized_volatility_pct": safe_round(annualized_vol * 100),
        "sharpe_ratio": safe_round(sharpe, 3),
        "sortino_ratio": safe_round(sortino, 3),
        "max_drawdown_pct": safe_round(max_drawdown_pct),
        "calmar_ratio": safe_round(calmar, 3),
        "risk_free_rate_used_pct": round(config.RISK_FREE_RATE_ANNUAL * 100, 2),
        "read": (
            f"Sharpe {safe_round(sharpe,2)}: "
            + (
                "strong risk-adjusted return"
                if sharpe and sharpe > 1
                else (
                    "weak/negative risk-adjusted return"
                    if sharpe and sharpe < 0
                    else (
                        "modest risk-adjusted return"
                        if sharpe is not None
                        else "unavailable"
                    )
                )
            )
            + f". Max drawdown {safe_round(max_drawdown_pct)}% over the period."
        ),
    }
    _intraday_set(sym, ra_cache_key, result)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Quant factors + composite score
# ---------------------------------------------------------------------------
@_tool_guard
def get_quant_factors(symbol: str, force_refresh: bool = False) -> str:
    """Compute quant factor signals: value, momentum, quality, leverage, squeeze, with composite score 0-100."""
    sym = _check_symbol(symbol)
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "quant_factors")
        if cached_intraday is not None:
            return json.dumps({**cached_intraday, "source": "intraday_cache"})
    fund = json.loads(get_fundamentals(sym))
    hist = _get_ohlcv(sym, period="1y", force_refresh=force_refresh)
    if hist is None or hist.empty:
        hist = _history_from_cache(sym, "1y")
    if hist is None or hist.empty:
        hist = yf.Ticker(sym).history(period="1y", interval="1d", auto_adjust=True)
    if hist is None or hist.empty:
        hist = None
    factors = {}
    score = 50
    # VALUE FACTORS (bidirectional)
    peg = fund.get("pegRatio")
    forward_pe = fund.get("forwardPE")
    if peg is not None:
        peg_pass = peg > 0 and peg < 1.2 and (forward_pe is None or forward_pe < 20)
        factors["peg_ratio"] = peg
        factors["peg_signal"] = (
            "undervalued (PEG<1.2, fwdPE<20)" if peg_pass else "expensive on PEG basis"
        )
        score += 12 if peg_pass else -12
    else:
        factors["peg_ratio"] = None
        factors["peg_signal"] = "unavailable"
    pfcf = None
    try:
        with open(_cache_file_path(sym)) as f:
            raw = json.load(f)
        cashflow = raw.get("cashflow_annual", {})
        fcf = None
        for line_item, values in cashflow.items():
            if "Free Cash Flow" in line_item and isinstance(values, dict):
                dates = sorted(values.keys(), reverse=True)
                if dates:
                    fcf = values[dates[0]]
                    break
        market_cap = fund.get("marketCap")
        if fcf is not None and market_cap and fcf > 0:
            pfcf = market_cap / fcf
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    if pfcf is not None:
        pfcf_pass = pfcf < 15
        factors["price_to_fcf"] = round(pfcf, 2)
        factors["pfcf_signal"] = (
            "cheap on FCF basis (P/FCF<15)" if pfcf_pass else "expensive on FCF basis"
        )
        score += 10 if pfcf_pass else -10
    else:
        factors["price_to_fcf"] = None
        factors["pfcf_signal"] = (
            "unavailable (could not parse cashflow statement or FCF is negative)"
        )
    # MOMENTUM (bidirectional — computed separately from composite_score as of Fix 3,
    # but still returned as a field for downstream use)
    need_extra = hist is not None and len(hist) <= 252
    if need_extra:
        try:
            extra = _get_ohlcv(sym, period="2y", force_refresh=False)
            if extra is not None and not extra.empty:
                if extra.index.tz is not None:
                    extra.index = extra.index.tz_localize(None)
                if hist.index.tz is not None:
                    hist.index = hist.index.tz_localize(None)
                hist = pd.concat([hist, extra]).drop_duplicates().sort_index()
        except Exception:
            pass
    if hist is not None and len(hist) > 252:
        close = hist["Close"]
        ret_12mo = close.pct_change(252).iloc[-1]
        ret_1mo = close.pct_change(21).iloc[-1]
        momentum_12_1 = (
            (ret_12mo - ret_1mo) * 100
            if not (pd.isna(ret_12mo) or pd.isna(ret_1mo))
            else None
        )
        factors["momentum_12_1_pct"] = (
            round(float(momentum_12_1), 2) if momentum_12_1 is not None else None
        )
        if momentum_12_1 is not None and momentum_12_1 > 0:
            factors["momentum_signal"] = "positive 12-1 momentum"
        elif momentum_12_1 is not None:
            factors["momentum_signal"] = "negative 12-1 momentum"
        else:
            factors["momentum_signal"] = "unavailable"
    else:
        factors["momentum_12_1_pct"] = None
        factors["momentum_signal"] = (
            "unavailable (insufficient history, needs >252 trading days)"
        )
    # BREAKOUT (one-sided catalyst — absence is not bearish)
    if hist is not None and len(hist) >= 50:
        vol_ma50 = hist["Volume"].rolling(50).mean().iloc[-1]
        current_vol = hist["Volume"].iloc[-1]
        lookback = min(252, len(hist))
        is_52wk_high = bool(
            hist["Close"].iloc[-1] >= hist["Close"].rolling(lookback).max().iloc[-1]
        )
        volume_confirmed_breakout = bool(
            not pd.isna(vol_ma50)
            and vol_ma50 > 0
            and current_vol > (vol_ma50 * 2.5)
            and is_52wk_high
        )
        factors["volume_confirmed_52wk_breakout"] = volume_confirmed_breakout
        if volume_confirmed_breakout:
            score += 8
    else:
        factors["volume_confirmed_52wk_breakout"] = None
    # REVENUE GROWTH (bidirectional, only when we have >=3 years of data)
    revenue_growth_inflection = None
    try:
        with open(_cache_file_path(sym)) as f:
            raw = json.load(f)
        income = raw.get("income_stmt_annual", {})
        revenue_by_year = {}
        for line_item, values in income.items():
            if "Total Revenue" in line_item and isinstance(values, dict):
                for date_str, val in values.items():
                    revenue_by_year[date_str] = val
        sorted_years = sorted(revenue_by_year.keys(), reverse=True)
        if len(sorted_years) >= 3:
            r0, r1, r2 = [revenue_by_year[y] for y in sorted_years[:3]]
            if r1 and r2 and r0:
                growth_y1 = (r0 - r1) / abs(r1)
                growth_y2 = (r1 - r2) / abs(r2)
                revenue_growth_inflection = bool(growth_y1 > growth_y2)
                factors["revenue_growth_yoy_latest_pct"] = round(growth_y1 * 100, 1)
                factors["revenue_growth_yoy_prior_pct"] = round(growth_y2 * 100, 1)
    except (OSError, json.JSONDecodeError, KeyError, ZeroDivisionError):
        pass
    if revenue_growth_inflection is not None:
        factors["revenue_growth_accelerating"] = revenue_growth_inflection
        score += 10 if revenue_growth_inflection else -10
    else:
        factors["revenue_growth_accelerating"] = None
        factors.setdefault("revenue_growth_yoy_latest_pct", None)
        factors.setdefault("revenue_growth_yoy_prior_pct", None)
    # LEVERAGE (bidirectional — rebalanced to match new scale)
    debt_to_equity = fund.get("debtToEquity")
    factors["debt_to_equity"] = debt_to_equity
    if debt_to_equity is not None:
        if debt_to_equity > 200:
            score -= 10
            factors["debt_signal"] = "high leverage risk (D/E > 2.0x)"
        elif debt_to_equity < 50:
            score += 10
            factors["debt_signal"] = "conservative balance sheet (D/E < 0.5x)"
        else:
            factors["debt_signal"] = "acceptable leverage"
    else:
        factors["debt_signal"] = "unavailable"
    # SHORT SQUEEZE (one-sided catalyst)
    short_pct_float = fund.get("shortPercentOfFloat")
    short_ratio = fund.get("shortRatio")
    if short_pct_float is not None and short_ratio is not None:
        squeeze_setup = bool(short_pct_float > 0.15 and short_ratio > 5)
        factors["short_pct_of_float"] = round(short_pct_float * 100, 1)
        factors["short_ratio_days_to_cover"] = short_ratio
        factors["short_squeeze_setup"] = squeeze_setup
        if squeeze_setup:
            score += 8
    else:
        factors["short_squeeze_setup"] = None
    # COMPOSITE SCORE
    score = max(0, min(100, score))
    factors["composite_score"] = score
    factors["composite_score_note"] = (
        "Score starts at 50 (neutral). Bidirectional factors (PEG, P/FCF, momentum, "
        "revenue inflection, leverage) add or subtract. One-sided catalysts (breakout, "
        "squeeze) only add. Missing/unavailable data contributes 0. This is a simple "
        "additive heuristic, not a backtested or statistically validated model."
    )
    _intraday_set(sym, "quant_factors", {"symbol": sym, **factors})
    return json.dumps({"symbol": sym, **factors})


# ---------------------------------------------------------------------------
# Tool: Comprehensive technical analysis (aggregator)
# ---------------------------------------------------------------------------
@_tool_guard
def get_technical_analysis(symbol: str, force_refresh: bool = False) -> str:
    """Comprehensive technical analysis merging price, trend, momentum, volatility, volume, and pivots."""
    sym = _check_symbol(symbol)
    result = {"symbol": sym, "source": None}
    tool_calls = [
        (
            get_price_data,
            {"symbol": sym, "period": "6mo", "force_refresh": force_refresh},
        ),
        (get_technicals, {"symbol": sym, "force_refresh": force_refresh}),
        (get_trend_indicators, {"symbol": sym, "force_refresh": force_refresh}),
        (get_momentum_indicators, {"symbol": sym, "force_refresh": force_refresh}),
        (get_volatility_indicators, {"symbol": sym, "force_refresh": force_refresh}),
        (get_volume_indicators, {"symbol": sym, "force_refresh": force_refresh}),
        (get_pivot_points, {"symbol": sym, "force_refresh": force_refresh}),
    ]
    skip_keys = {"symbol", "error", "source", "period"}
    for fn, kwargs in tool_calls:
        try:
            data = json.loads(fn(**kwargs))
            if isinstance(data, dict) and "error" not in data:
                for k, v in data.items():
                    if k not in skip_keys:
                        result[k] = v
                if result["source"] is None:
                    result["source"] = data.get("source")
        except Exception:
            continue
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool: Cross-sectional comparison / ranking
# ---------------------------------------------------------------------------
@_tool_guard
def compare_symbols(
    symbols: list[str] | None = None,
    metric: str = "period_return_pct",
    force_refresh: bool = False,
) -> str:
    """Rank multiple watchlist symbols against each other on a chosen metric."""
    syms = []
    for s in symbols or config.WATCHLIST:
        try:
            syms.append(_check_symbol(s))
        except ValueError:
            continue
    summary_path = config.CACHE_DIR / "watchlist_summary.json"
    if not _cache_is_stale(summary_path, max_age_hours=config.SIDECAR_MAX_AGE_HOURS):
        try:
            with open(summary_path, "r") as f:
                summary = json.load(f)
            rows = []
            for sym in syms:
                entry = summary.get("watchlist", {}).get(sym, {})
                value = entry.get(metric)
                if value is not None:
                    rows.append({"symbol": sym, metric: value})
            if rows:
                rows.sort(key=lambda r: r[metric], reverse=True)
                return json.dumps(
                    {
                        "metric": metric,
                        "ranking": rows,
                        "source": "sidecar",
                        "sidecar_generated_at": summary.get("generated_at"),
                    }
                )
        except (OSError, json.JSONDecodeError):
            pass
    rows = []
    for sym in syms:
        try:
            if metric in ("period_return_pct", "annualized_volatility_pct"):
                data = json.loads(
                    get_price_data(sym, period="6mo", force_refresh=force_refresh)
                )
            elif metric in ("rsi_14", "macd_histogram"):
                data = json.loads(
                    get_technical_analysis(sym, force_refresh=force_refresh)
                )
            elif metric in (
                "sharpe_ratio",
                "sortino_ratio",
                "max_drawdown_pct",
                "calmar_ratio",
            ):
                data = json.loads(
                    get_risk_adjusted_returns(
                        sym, period="1y", force_refresh=force_refresh
                    )
                )
            elif metric == "excess_return_pct":
                data = json.loads(
                    get_relative_strength(
                        sym, benchmark="SPY", period="6mo", force_refresh=force_refresh
                    )
                )
            elif metric == "composite_score":
                data = json.loads(get_quant_factors(sym, force_refresh=force_refresh))
            else:
                data = json.loads(get_fundamentals(sym, force_refresh=force_refresh))
            value = data.get(metric)
            if value is not None:
                rows.append({"symbol": sym, metric: value})
        except Exception as e:
            rows.append({"symbol": sym, "error": str(e)})
    valid = [r for r in rows if metric in r]
    valid.sort(key=lambda r: r[metric], reverse=True)
    return json.dumps({"metric": metric, "ranking": valid, "source": "live_fallback"})


# ---------------------------------------------------------------------------
# Tool: News headlines
# ---------------------------------------------------------------------------
def _extract_headline(item: dict) -> dict:
    content = item.get("content", item) if isinstance(item, dict) else {}
    provider = content.get("provider")
    canonical = content.get("canonicalUrl")
    return {
        "title": content.get("title"),
        "publisher": (
            (provider or {}).get("displayName")
            if isinstance(provider, dict)
            else content.get("publisher")
        ),
        "link": (
            (canonical or {}).get("url")
            if isinstance(canonical, dict)
            else content.get("link")
        ),
    }


@_tool_guard
def get_news_headlines(symbol: str, limit: int = 5, force_refresh: bool = False) -> str:
    """Get recent news headlines for a symbol."""
    sym = _check_symbol(symbol)
    if not force_refresh:
        cached = _load_cached_symbol_json(sym)
        if cached and cached.get("news"):
            items = [_extract_headline(n) for n in cached["news"][:limit]]
            return json.dumps({"symbol": sym, "headlines": items, "source": "cache"})
    try:
        news = _with_timeout(lambda: yf.Ticker(sym).news, 30.0, []) or []
    except Exception as e:
        return json.dumps({"symbol": sym, "error": str(e), "source": "live"})
    items = [_extract_headline(n) for n in news[:limit]]
    return json.dumps({"symbol": sym, "headlines": items, "source": "live"})


# ---------------------------------------------------------------------------
# Tool: Insider transactions (SEC EDGAR)
# ---------------------------------------------------------------------------
def _lookup_cik(ticker: str) -> str | None:
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        req = urllib.request.Request(url, headers={"User-Agent": config.SEC_UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                return str(entry["cik_str"]).zfill(10)
    except Exception:
        pass
    return None


@_tool_guard
def get_insider_transactions(
    symbol: str, days_back: int = 90, force_refresh: bool = False
) -> str:
    """Fetch recent SEC insider transaction filings (Forms 3, 4, 5)."""
    sym = _check_symbol(symbol)
    days_back = min(days_back, 365)
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "insider_transactions")
        if cached_intraday is not None:
            return json.dumps(
                {"symbol": sym, **cached_intraday, "source": "intraday_cache"}
            )
    cik = _lookup_cik(sym)
    if not cik:
        return json.dumps(
            {
                "symbol": sym,
                "insider_activity": [],
                "total_filings": 0,
                "note": "Could not find CIK for this symbol.",
                "source": "live",
            }
        )
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        req = urllib.request.Request(url, headers={"User-Agent": config.SEC_UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return json.dumps(
            {
                "symbol": sym,
                "error": f"Failed to fetch SEC filings: {e}",
                "source": "live",
            }
        )
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    descriptions = recent.get("primaryDocDescription", [])
    primary_docs = recent.get("primaryDocument", [])
    accession_numbers = recent.get("accessionNumber", [])
    insider_forms = {"3", "4", "5"}
    results = []
    cutoff = datetime.now() - timedelta(days=days_back)
    for i, form in enumerate(forms):
        if form not in insider_forms:
            continue
        fd_str = filing_dates[i] if i < len(filing_dates) else ""
        try:
            fd = datetime.strptime(fd_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        if fd < cutoff.date():
            continue
        desc = descriptions[i] if i < len(descriptions) else ""
        acc = accession_numbers[i] if i < len(accession_numbers) else ""
        doc = primary_docs[i] if i < len(primary_docs) else ""
        acc_clean = acc.replace("-", "")
        sec_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_clean}/{doc}"
            if doc
            else ""
        )
        filing_xml = None
        insider_name = ""
        transaction_summary = ""
        if doc and acc_clean:
            try:
                xml_url = (
                    f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_clean}/{doc}"
                )
                xml_req = urllib.request.Request(
                    xml_url, headers={"User-Agent": config.SEC_UA}
                )
                with urllib.request.urlopen(xml_req, timeout=10) as xresp:
                    raw = xresp.read().decode("utf-8", errors="replace")
                if form == "4":
                    nm = re.search(r"<rptOwnerName>([^<]+)</rptOwnerName>", raw)
                    if nm:
                        insider_name = nm.group(1).strip()
                    txns = re.findall(
                        r"<transactionDate>([^<]*)</transactionDate>.*?"
                        r"<transactionShares>([^<]*)</transactionShares>.*?"
                        r"<transactionPricePerShare>([^<]*)</transactionPricePerShare>.*?"
                        r"<transactionAcquiredDisposedCode>\s*<value>([AD])</value>",
                        raw,
                        re.DOTALL,
                    )
                    parts = []
                    for txn_date, shares, price, code in txns[:5]:
                        action = "Acquired (Buy)" if code == "A" else "Disposed (Sell)"
                        parts.append(
                            f"{action} {shares} shares @ ${price} on {txn_date}"
                        )
                    transaction_summary = "; ".join(parts) if parts else desc
                elif form in ("3", "5"):
                    nm = re.search(r"<rptOwnerName>([^<]+)</rptOwnerName>", raw)
                    if nm:
                        insider_name = nm.group(1).strip()
                    transaction_summary = desc
            except Exception:
                transaction_summary = desc
                insider_name = ""
        results.append(
            {
                "filing_date": fd_str,
                "form_type": form,
                "insider_name": insider_name or "See filing",
                "transaction_summary": (
                    transaction_summary[:300] if transaction_summary else desc[:300]
                ),
                "sec_url": sec_url,
            }
        )
    results.sort(key=lambda x: x["filing_date"], reverse=True)
    out = {"insider_activity": results[:25], "total_filings": len(results)}
    _intraday_set(sym, "insider_transactions", out)
    return json.dumps({"symbol": sym, **out, "source": "live"})


# ---------------------------------------------------------------------------
# Tool: Candlestick patterns
# ---------------------------------------------------------------------------
@_tool_guard
def get_candlestick_patterns(symbol: str, force_refresh: bool = False) -> str:
    """Detect candlestick patterns (doji, hammer, engulfing, inside bar, etc.)."""
    sym = _check_symbol(symbol)
    if not force_refresh:
        cached_intraday = _intraday_get(sym, "candlestick_patterns")
        if cached_intraday is not None:
            return json.dumps(
                {"symbol": sym, **cached_intraday, "source": "intraday_cache"}
            )
    hist = _get_ohlcv(sym, period="3mo", force_refresh=force_refresh)
    if hist is None or len(hist) < 20:
        return json.dumps({"symbol": sym, "error": "Insufficient OHLCV history."})
    import pandas_ta as ta

    o, h, l, c, v = (
        hist["Open"],
        hist["High"],
        hist["Low"],
        hist["Close"],
        hist["Volume"],
    )
    patterns = []
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            cdl = ta.cdl_pattern(o, h, l, c, name="all")
        if cdl is not None and not cdl.empty:
            last = cdl.iloc[-1]
            for col in cdl.columns:
                val = last.get(col)
                if val is not None and val != 0:
                    name = col.replace("CDL_", "").replace("_", " ").title()
                    direction = "bullish" if val > 0 else "bearish"
                    patterns.append(
                        {
                            "name": name,
                            "signal": direction,
                            "strength": (
                                "strong"
                                if abs(val) > 100
                                else "moderate" if abs(val) > 50 else "weak"
                            ),
                        }
                    )
    except Exception:
        pass
    try:
        doji = ta.cdl_doji(o, h, l, c)
        if doji is not None and not doji.empty:
            last_doji = doji.iloc[-1]
            if last_doji and last_doji != 0:
                patterns.append(
                    {
                        "name": "Doji",
                        "signal": "neutral (indecision)",
                        "strength": "moderate",
                    }
                )
    except Exception:
        pass
    try:
        inside = ta.cdl_inside(o, h, l, c)
        if inside is not None and not inside.empty:
            last_inside = inside.iloc[-1]
            if last_inside and last_inside != 0:
                direction = "bullish" if last_inside > 0 else "bearish"
                patterns.append(
                    {"name": "Inside Bar", "signal": direction, "strength": "moderate"}
                )
    except Exception:
        pass
    last_idx = -1
    last_candle = {
        "date": (
            str(hist.index[last_idx].date())
            if hasattr(hist.index[last_idx], "date")
            else ""
        ),
        "open": round(float(o.iloc[last_idx]), 2),
        "high": round(float(h.iloc[last_idx]), 2),
        "low": round(float(l.iloc[last_idx]), 2),
        "close": round(float(c.iloc[last_idx]), 2),
        "volume": int(v.iloc[last_idx]),
        "body_pct": round(
            abs(c.iloc[last_idx] - o.iloc[last_idx])
            / (h.iloc[last_idx] - l.iloc[last_idx] + 1e-10)
            * 100,
            1,
        ),
    }
    result = {"patterns": patterns, "last_candle": last_candle}
    _intraday_set(sym, "candlestick_patterns", result)
    return json.dumps({"symbol": sym, **result, "source": "live"})


# ---------------------------------------------------------------------------
# Cooldown: exclude recently stopped-out tickers from screening
# ---------------------------------------------------------------------------
def _get_cooldown_exclusions() -> set[str]:
    """Return tickers that were stopped out within STOPOUT_COOLDOWN_DAYS."""
    import re as _re

    excl: set[str] = set()
    cutoff = datetime.now() - timedelta(days=config.STOPOUT_COOLDOWN_DAYS)
    for d in config.closed_trades_dirs():
        if not d.is_dir():
            continue
        for fp in d.glob("*.md"):
            stem = fp.stem
            parts = stem.split("--", 1)
            if len(parts) == 2:
                date_str, ticker = parts
            else:
                continue
            ticker = ticker.upper()
            # Remove any trailing --N sequence suffix
            ticker = _re.sub(r"--\d+$", "", ticker)
            if ticker not in config.WATCHLIST:
                continue
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                continue
            # Read content to check if this was a stop-out
            try:
                raw = fp.read_text(encoding="utf-8")
            except Exception:
                continue
            yaml_outcome = _parse_yaml_outcome(raw)
            if yaml_outcome is not None and yaml_outcome.strip(">| \t\n"):
                # YAML frontmatter present with non-empty outcome
                outcome_lower = yaml_outcome.lower()
                if any(kw in outcome_lower for kw in ["stop", "loss"]):
                    excl.add(ticker)
            else:
                # No YAML or empty outcome — search full text
                if _re.search(r"(stopped\s+out|\boutcome.*\bstop)", raw, _re.IGNORECASE):
                    excl.add(ticker)
    return excl


def _parse_yaml_outcome(raw: str) -> str | None:
    """Extract 'outcome:' value from YAML frontmatter."""
    if not raw.startswith("---"):
        return None
    end = raw.find("---", 3)
    if end == -1:
        return None
    for line in raw[3:end].strip().split("\n"):
        if line.strip().startswith("outcome:"):
            return line.split(":", 1)[1].strip()
    return None


# ---------------------------------------------------------------------------
# Tool: Screening — Python-based pre-filter (NEW)
# ---------------------------------------------------------------------------
@_tool_guard
def run_screening(mode: str = "full") -> str:
    """Read cached yf_data, compute composite scores, return top 10 tickers.

    Args:
        mode: "fasset" for the 44-ticker curated list, "full" for all 100+ (default).

    Uses watchlist_summary.json if available. Falls back to on-the-fly
    scoring from individual cached symbol data. Recently stopped-out tickers
    are excluded from screening (cooldown: {config.STOPOUT_COOLDOWN_DAYS}d).

    Scoring: fundamental_quality * 0.35 + momentum_12_1 * 0.35 +
             rsi_neutrality * 0.15 + sharpe_ratio * 0.15
    """
    watchlist = config.get_watchlist(mode)

    def _score_one(qs, momentum_12_1, rsi_14, sharpe_ratio):
        weight_present = 0.0
        s = 0.0
        if qs is not None:
            s += float(qs) * 0.35
            weight_present += 0.35
        if momentum_12_1 is not None:
            clipped = max(-30, min(30, float(momentum_12_1)))
            mom_score = (clipped + 30) / 60 * 20 - 10  # -30→-10, 0→0, +30→+10
            s += mom_score * 0.35
            weight_present += 0.35
        if rsi_14 is not None:
            rsi_val = float(rsi_14)
            rsi_score = (
                (50 - abs(rsi_val - 50)) / 50 * 10
            )  # 0 (extreme) to 10 (neutral)
            s += rsi_score * 0.15
            weight_present += 0.15
        if sharpe_ratio is not None:
            sharpe_score = max(
                0, min(10, (float(sharpe_ratio) + 1) * 5)
            )  # -1→0, 0→5, 1→10
            s += sharpe_score * 0.15
            weight_present += 0.15
        return max(0, min(100, s)), weight_present

    def _build_top(scored):
        for r in scored:
            r["data_completeness"] = f"{r['weight_present']:.0%}"
        complete = [r for r in scored if r["weight_present"] >= 0.5]
        incomplete = [r for r in scored if r["weight_present"] < 0.5]
        complete.sort(key=lambda r: r["composite_score"], reverse=True)
        incomplete.sort(key=lambda r: r["composite_score"], reverse=True)
        ordered = complete + incomplete
        for r in ordered:
            del r["weight_present"]
        return ordered[:10]

    exclusions = _get_cooldown_exclusions()
    if exclusions:
        print(f"[SCREENING] Cooldown exclusions: {', '.join(sorted(exclusions))}")

    active_watchlist = [s for s in watchlist if s not in exclusions]

    # Fundamental quality gate: exclude tickers with deeply negative margins
    # or no earnings power (both trailing and forward P/E unavailable).
    # This filters out crypto miners and other structurally unprofitable names
    # that would otherwise rank high on momentum alone.
    def _passes_fundamental_gate(sym: str) -> bool:
        try:
            fund = json.loads(get_fundamentals(sym))
        except Exception:
            return True  # can't determine — let through (data may be stale)
        profit_margins = fund.get("profitMargins")
        if profit_margins is not None and profit_margins < -0.50:
            return False
        trailing_pe = fund.get("trailingPE")
        forward_pe = fund.get("forwardPE")
        if trailing_pe is None and forward_pe is None:
            return False
        return True

    filtered = [s for s in active_watchlist if _passes_fundamental_gate(s)]
    dropped = [s for s in active_watchlist if s not in filtered]
    if dropped:
        print(
            f"[SCREENING] Fundamental quality gate excluded: {', '.join(sorted(dropped))}"
        )
    active_watchlist = filtered

    summary_path = config.CACHE_DIR / "watchlist_summary.json"
    if not _cache_is_stale(summary_path, max_age_hours=config.SIDECAR_MAX_AGE_HOURS):
        try:
            with open(summary_path, "r") as f:
                summary = json.load(f)
            watchlist_data = summary.get("watchlist", {})
            scored = []
            for sym in active_watchlist:
                entry = watchlist_data.get(sym, {})
                qs = entry.get("composite_score")
                if qs is None:
                    continue
                momentum_12_1 = entry.get("momentum_12_1_pct")
                rsi_14 = entry.get("rsi_14")
                sharpe_ratio = entry.get("sharpe_ratio")
                s, weight_present = _score_one(qs, momentum_12_1, rsi_14, sharpe_ratio)
                scored.append(
                    {
                        "symbol": sym,
                        "composite_score": round(s, 1),
                        "quant_score": qs,
                        "momentum_12_1_pct": momentum_12_1,
                        "rsi_14": rsi_14,
                        "sharpe_ratio": sharpe_ratio,
                        "weight_present": weight_present,
                    }
                )
            if len(scored) > 0:
                return json.dumps(
                    {
                        "top_candidates": _build_top(scored),
                        "total_screened": len(scored),
                        "source": "sidecar",
                        "method": "fundamental_quality*0.35 + momentum_12_1*0.35 + rsi_neutrality*0.15 + sharpe_ratio*0.15",
                    }
                )
        except (OSError, json.JSONDecodeError):
            pass

    result_list = []
    for sym in active_watchlist:
        try:
            qf = json.loads(get_quant_factors(sym))
            qs = qf.get("composite_score", 50)
            momentum_12_1 = qf.get("momentum_12_1_pct")
            ta_data = json.loads(get_technical_analysis(sym))
            rsi_14 = ta_data.get("rsi_14")
            ra_data = json.loads(get_risk_adjusted_returns(sym, period="1y"))
            sharpe_ratio = ra_data.get("sharpe_ratio")
            s, weight_present = _score_one(qs, momentum_12_1, rsi_14, sharpe_ratio)
            result_list.append(
                {
                    "symbol": sym,
                    "composite_score": round(s, 1),
                    "quant_score": qs,
                    "momentum_12_1_pct": momentum_12_1,
                    "rsi_14": rsi_14,
                    "sharpe_ratio": sharpe_ratio,
                    "weight_present": weight_present,
                }
            )
        except Exception:
            continue
    return json.dumps(
        {
            "top_candidates": _build_top(result_list),
            "total_screened": len(result_list),
            "source": "live",
            "method": "fundamental_quality*0.35 + momentum_12_1*0.35 + rsi_neutrality*0.15 + sharpe_ratio*0.15",
        }
    )


# ---------------------------------------------------------------------------
# Tool: Portfolio exposure check
# ---------------------------------------------------------------------------
@_tool_guard
def check_portfolio_exposure(new_symbols: list[str] | None = None) -> str:
    """Check existing open trades for sector/symbol overlap before opening new positions."""
    mem = config.active_memories_root()
    open_dir = mem / "open_trades"
    existing = []
    if open_dir.is_dir():
        for fp in open_dir.glob("*.md"):
            try:
                content = fp.read_text(encoding="utf-8")
                if content.startswith("---"):
                    end = content.index("---", 3)
                    yaml_text = content[3:end].strip()
                    lines = yaml_text.split("\n")
                    entry = {"file": fp.name}
                    for line in lines:
                        if ":" in line:
                            k, v = line.split(":", 1)
                            entry[k.strip()] = v.strip().strip("'\"")
                    existing.append(entry)
            except Exception:
                continue
    sectors = {}
    for e in existing:
        sym = e.get("symbol", "")
        if sym:
            fund_path = config.CACHE_DIR / f"{sym}.json"
            if fund_path.exists():
                try:
                    data = json.loads(fund_path.read_text(encoding="utf-8"))
                    info = data.get("info", {})
                    sectors[sym] = info.get("sector", "Unknown")
                except Exception:
                    sectors[sym] = "Unknown"
            else:
                sectors[sym] = "Unknown"
    warnings = []
    if new_symbols and existing:
        existing_syms = {e.get("symbol", "") for e in existing}
        new_set = {s.upper() for s in new_symbols}
        overlap = existing_syms & new_set
        if overlap:
            warnings.append(
                f"Already have open positions in: {', '.join(sorted(overlap))}"
            )
        existing_sectors_list = [sectors.get(s, "Unknown") for s in existing_syms if s]
        for ns in new_set:
            new_sector = "Unknown"
            fund_path = config.CACHE_DIR / f"{ns}.json"
            if fund_path.exists():
                try:
                    data = json.loads(fund_path.read_text(encoding="utf-8"))
                    new_sector = data.get("info", {}).get("sector", "Unknown")
                except Exception:
                    pass
            same_sector = [
                s for s in existing_sectors_list if s == new_sector and s != "Unknown"
            ]
            if same_sector:
                warnings.append(
                    f"{ns} ({new_sector}) would add concentration — "
                    f"already have {len(same_sector)} position(s) in {new_sector}"
                )
    return json.dumps(
        {
            "existing_open_trades": existing,
            "sectors": sectors,
            "proposed_new_symbols": new_symbols,
            "warnings": warnings,
            "trade_count": len(existing),
        }
    )


# ---------------------------------------------------------------------------
# Diagnostic: intraday cache status
# ---------------------------------------------------------------------------
@_tool_guard
def get_intraday_cache_status() -> str:
    """Return a summary of what's currently in the intraday cache."""
    now = datetime.now().timestamp()
    entries = []
    for key, entry in _intraday_cache.items():
        age_min = round((now - entry["fetched_at"]) / 60, 1)
        entries.append(
            {
                "key": key,
                "age_minutes": age_min,
                "expires_in_minutes": round(config.INTRADAY_CACHE_MINUTES - age_min, 1),
            }
        )
    ohlcv_entries = []
    for key, entry in _intraday_ohlcv_cache.items():
        age_min = round((now - entry["fetched_at"]) / 60, 1)
        ohlcv_entries.append(
            {
                "key": key,
                "age_minutes": age_min,
                "rows": len(entry["df"]),
            }
        )
    return json.dumps(
        {
            "intraday_cache_minutes": config.INTRADAY_CACHE_MINUTES,
            "tool_cache_entries": len(entries),
            "ohlcv_cache_entries": len(ohlcv_entries),
            "tool_cache": entries,
            "ohlcv_cache": ohlcv_entries,
        }
    )
