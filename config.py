import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "deepseek/deepseek-v4-pro")
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

CACHE_DIR = Path(os.environ.get("YF_CACHE_DIR", "yf_data"))
CACHE_MAX_AGE_HOURS = float(os.environ.get("YF_CACHE_MAX_AGE_HOURS", "24"))
SIDECAR_MAX_AGE_HOURS = float(os.environ.get("YF_SIDECAR_MAX_AGE_HOURS", "24"))
NEWS_CACHE_MAX_AGE_HOURS = float(os.environ.get("YF_NEWS_CACHE_MAX_AGE_HOURS", "6"))
COMBINED_HISTORY_PATH = CACHE_DIR / "combined_history.csv"
HISTORY_CSV_MAX_AGE_HOURS = float(os.environ.get("YF_HISTORY_CSV_MAX_AGE_HOURS", "24"))
RISK_FREE_RATE_ANNUAL = float(os.environ.get("RISK_FREE_RATE_ANNUAL", "0.045"))
INTRADAY_CACHE_MINUTES = float(os.environ.get("YF_INTRADAY_CACHE_MINUTES", "120"))
INTRADAY_CACHE_FILE = Path(os.environ.get("YF_INTRADAY_CACHE_FILE", str(CACHE_DIR / "_intraday_cache.pkl")))

AGENT_FS_ROOT = Path(os.environ.get("AGENT_FS_ROOT", "agent_fs")).resolve()
AGENT_FS_ROOT.mkdir(parents=True, exist_ok=True)

STOPOUT_COOLDOWN_DAYS = int(os.environ.get("STOPOUT_COOLDOWN_DAYS", "14"))
CLOSED_TRADES_DIR = AGENT_FS_ROOT / "memories" / "closed_trades"

WATCHLIST = sorted([
    "MSFT", "GOOG", "NVDA", "META", "ADBE", "AMZN", "AAPL", "AVGO",
    "TSLA", "AMD", "V", "XOM", "JNJ", "CAT", "ABBV", "ARM", "PG", "HD",
    "CVX", "MRK", "AZN", "DELL", "IBM", "APH", "TJX", "ABT", "UBER", "PFE",
    "PLD", "CRM", "PH", "SNOW", "NKE", "DAL", "RKLB", "RBLX", "MSTR",
    "RDDT", "HUT", "RIOT", "HIMS", "MARA", "VEON", "SBET",
])

ALLOWED_BENCHMARKS = ["SPY", "QQQ", "DIA", "IWM"]

FUNDAMENTALS_FIELDS = [
    "marketCap", "trailingPE", "forwardPE", "pegRatio",
    "priceToBook", "profitMargins", "operatingMargins",
    "revenueGrowth", "earningsGrowth", "debtToEquity",
    "returnOnEquity", "dividendYield", "beta",
    "targetMeanPrice", "targetHighPrice", "targetLowPrice",
    "recommendationKey", "numberOfAnalystOpinions",
    "sector", "industry",
    "shortPercentOfFloat", "shortRatio", "sharesShort",
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
