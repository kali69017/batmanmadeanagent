import os
from pathlib import Path

from dotenv import load_dotenv

# Project root — config.py lives at the repo root. Anchor paths here so they
# resolve correctly regardless of the process working directory (e.g. on
# PythonAnywhere, where the WSGI process and Always-on Task have different CWDs).
_BASE_DIR = Path(__file__).resolve().parent

load_dotenv(_BASE_DIR / ".env")

MODEL_NAME = os.getenv("MODEL_NAME", "deepseek/deepseek-v4-pro")
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

CACHE_DIR = Path(os.environ.get("YF_CACHE_DIR", str(_BASE_DIR / "yf_data")))
CACHE_MAX_AGE_HOURS = float(os.environ.get("YF_CACHE_MAX_AGE_HOURS", "24"))
SIDECAR_MAX_AGE_HOURS = float(os.environ.get("YF_SIDECAR_MAX_AGE_HOURS", "24"))
NEWS_CACHE_MAX_AGE_HOURS = float(os.environ.get("YF_NEWS_CACHE_MAX_AGE_HOURS", "6"))
COMBINED_HISTORY_PATH = CACHE_DIR / "combined_history.csv"
HISTORY_CSV_MAX_AGE_HOURS = float(os.environ.get("YF_HISTORY_CSV_MAX_AGE_HOURS", "24"))
RISK_FREE_RATE_ANNUAL = float(os.environ.get("RISK_FREE_RATE_ANNUAL", "0.045"))
INTRADAY_CACHE_MINUTES = float(os.environ.get("YF_INTRADAY_CACHE_MINUTES", "120"))
INTRADAY_CACHE_FILE = Path(
    os.environ.get("YF_INTRADAY_CACHE_FILE", str(CACHE_DIR / "_intraday_cache.pkl"))
)

AGENT_FS_ROOT = Path(os.environ.get("AGENT_FS_ROOT", str(_BASE_DIR / "agent_fs"))).resolve()
AGENT_FS_ROOT.mkdir(parents=True, exist_ok=True)

STOPOUT_COOLDOWN_DAYS = int(os.environ.get("STOPOUT_COOLDOWN_DAYS", "14"))

# Shared "learning brain" (lessons + signals win rates). Fed by all users.
SHARED_MEMORY_ROOT = AGENT_FS_ROOT / "memories"
# Per-user memory roots (positions, pending entries, watchlist, closed trades).
USERS_ROOT = AGENT_FS_ROOT / "users"

# Legacy/shared path to closed trades. Kept for backward-compat references;
# per-run tooling uses active_memories_root()/closed_trades_dirs() instead.
CLOSED_TRADES_DIR = SHARED_MEMORY_ROOT / "closed_trades"

# The per-run memory root. Set under RUN_LOCK while a user's agent runs so
# filesystem-side tools (check_portfolio_exposure, cooldown exclusions) read
# that user's memory. Defaults to the shared brain for CLI/dev usage.
_active_memories_root: Path | None = None


def user_memory_root(username: str) -> Path:
    """Absolute path to a user's memories directory."""
    return USERS_ROOT / username / "memories"


def set_active_memories_root(root: Path | None) -> None:
    """Set the memories root for the currently running agent session."""
    global _active_memories_root
    _active_memories_root = root


def active_memories_root() -> Path:
    """Memories root for the current run (shared brain when unset)."""
    return _active_memories_root if _active_memories_root is not None else SHARED_MEMORY_ROOT


def closed_trades_dirs() -> list[Path]:
    """Closed-trade directories to scan: the active user's plus shared/legacy."""
    dirs: list[Path] = []
    for base in (active_memories_root(), SHARED_MEMORY_ROOT):
        d = base / "closed_trades"
        if d not in dirs:
            dirs.append(d)
    return dirs

WATCHLIST = sorted(
    [
        "MSFT",
        "GOOG",
        "NVDA",
        "META",
        "ADBE",
        "AMZN",
        "AAPL",
        "AVGO",
        "TSLA",
        "AMD",
        "V",
        "XOM",
        "JNJ",
        "CAT",
        "ABBV",
        "ARM",
        "PG",
        "HD",
        "CVX",
        "MRK",
        "AZN",
        "DELL",
        "IBM",
        "APH",
        "TJX",
        "ABT",
        "UBER",
        "PFE",
        "PLD",
        "CRM",
        "PH",
        "SNOW",
        "NKE",
        "DAL",
        "RKLB",
        "RBLX",
        "MSTR",
        "RDDT",
        "HUT",
        "RIOT",
        "HIMS",
        "MARA",
        "VEON",
        "SBET",
    ]
)

# Fasset Scan — the curated 44-ticker list available on Fasset exchange.
FASSET_WATCHLIST = sorted(WATCHLIST)

# Expanded list — additional liquid, well-known tickers for broader coverage.
EXPANDED_WATCHLIST = sorted(
    [
        # Mega/Semis
        "INTC", "QCOM", "TXN", "MU", "LRCX", "AMAT", "KLAC",
        # Software / Cloud / Cyber
        "NOW", "PANW", "CRWD", "WDAY", "DDOG", "NET", "PLTR", "ZS", "TEAM",
        # Fintech / Payments
        "MA", "PYPL", "SQ", "COIN", "HOOD",
        # Banks / Finance
        "JPM", "BAC", "GS", "MS", "BLK", "SCHW", "C", "WFC",
        # Healthcare / Biotech
        "LLY", "UNH", "BMY", "GILD", "ISRG", "VRTX", "REGN", "TMO", "DHR",
        # Energy
        "COP", "SLB", "EOG", "MPC", "OXY", "KMI",
        # Consumer / Retail
        "WMT", "COST", "TGT", "MCD", "SBUX", "LOW", "BKNG", "ORLY",
        # Industrial / Aerospace
        "BA", "GE", "LMT", "HON", "UNP", "DE", "ETN", "ITW",
        # Media / Telecom
        "NFLX", "DIS", "T", "VZ", "TMUS", "SPOT",
        # EV / Auto
        "F", "RIVN",
        # Materials / Mining
        "FCX", "NEM",
        # Utilities
        "DUK", "SO", "NEE",
        # REITs
        "O", "SPG", "AMT",
        # China Tech / ADRs
        "BABA", "JD",
        # Other large-cap
        "BAH", "LULU", "DKNG", "CVNA",
        # Semis / AI adjacent
        "MRVL", "ANET", "SMCI",
        # Oil & Gas majors
        "BP", "SHEL",
        # Aerospace & Defense
        "RTX", "NOC",
        # Food & Beverage
        "KO", "PEP",
        # Pharma
        "NVS",
    ]
)

# Full scan — the union of Fasset and Expanded lists (100+ tickers).
FULL_WATCHLIST = sorted(set(FASSET_WATCHLIST) | set(EXPANDED_WATCHLIST))

# List 2 — temporary 5-ticker test list.
LIST_2 = ["AAPL", "MSFT", "NVDA", "GOOG", "META"]

# ── ACTIVE WATCHLIST ─────────────────────────────────────────────────────
# The agent screens and validates against WATCHLIST. To switch between the
# 5-ticker test list and the full 136-ticker list, change ONLY the right-hand
# side of this ONE assignment:
#   LIST_2          → 5-ticker test list (current, for testing)
#   FULL_WATCHLIST  → all 136 tickers (production)
WATCHLIST = LIST_2


def get_watchlist(mode: str = "full") -> list[str]:
    """Return the watchlist for a given scan mode.

    Args:
        mode: "fasset" for the curated 44, "full" for the active list (default).
    """
    if mode == "fasset":
        return FASSET_WATCHLIST
    return WATCHLIST

ALLOWED_BENCHMARKS = ["SPY", "QQQ", "DIA", "IWM"]

FUNDAMENTALS_FIELDS = [
    "marketCap",
    "trailingPE",
    "forwardPE",
    "pegRatio",
    "priceToBook",
    "profitMargins",
    "operatingMargins",
    "revenueGrowth",
    "earningsGrowth",
    "debtToEquity",
    "returnOnEquity",
    "dividendYield",
    "beta",
    "targetMeanPrice",
    "targetHighPrice",
    "targetLowPrice",
    "recommendationKey",
    "numberOfAnalystOpinions",
    "sector",
    "industry",
    "shortPercentOfFloat",
    "shortRatio",
    "sharesShort",
    "sharesShortPriorMonth",
]

SEC_UA = "SampleCompany contact@example.com"

FRED_SERIES = {
    "GDP": "Gross Domestic Product (Billions)",
    "CPIAUCSL": "Consumer Price Index (All Urban)",
    "UNRATE": "Unemployment Rate (%)",
    "FEDFUNDS": "Federal Funds Rate (%)",
    "DGS10": "10-Year Treasury Yield (%)",
    "DGS2": "2-Year Treasury Yield (%)",
    "T10Y2Y": "10Y-2Y Yield Spread (%)",
    "VIXCLS": "CBOE Volatility Index",
    "T5YIE": "5-Year Breakeven Inflation Rate (%)",
    "RECPROUSM156N": "Recession Probability (%)",
}
