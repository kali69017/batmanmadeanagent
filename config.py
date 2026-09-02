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
EXPANDED_WATCHLIST = sorted([
    "A", "AA", "AAL", "AAON", "AAPL", "ABBV", "ABNB", "ABT", "ACAD", "ACI",
    "ACIW", "ACLS", "ACN", "ADBE", "ADC", "ADEA", "ADI", "ADM", "ADP", "ADSK",
    "AEE", "AEHR", "AEIS", "AEM", "AEO", "AEP", "AES", "AFG", "AFL", "AFRM",
    "AG", "AGYS", "AI", "AIG", "AIZ", "AJG", "AKAM", "ALAB", "ALB", "ALGM",
    "ALGN", "ALGT", "ALK", "ALKS", "ALL", "ALLE", "ALNY", "ALRM", "AMAT", "AMBA",
    "AMD", "AME", "AMKR", "AMT", "AMZN", "AN", "ANET", "ANF", "ANGI", "AON",
    "AOS", "APA", "APD", "APH", "APLD", "APO", "APPF", "APPN", "APPS", "AR",
    "ARCB", "ARE", "ARES", "ARM", "ARVN", "ARW", "ARWR", "ASAN", "ASH", "ASML",
    "ASO", "ASTS", "ASX", "ATHM", "ATO", "ATRC", "AU", "AVAV", "AVGO", "AVPT",
    "AVT", "AVY", "AWK", "AXON", "AXP", "AXTI", "AZN", "AZO", "BA", "BABA",
    "BAC", "BAH", "BALL", "BAM", "BAND", "BAP", "BAX", "BB", "BBD", "BBVA",
    "BBWI", "BBY", "BCS", "BDC", "BDX", "BE", "BEAM", "BELFA", "BELFB", "BEN",
    "BG", "BGS", "BHE", "BHP", "BIDU", "BIIB", "BILI", "BILL", "BJ", "BKNG",
    "BKR", "BLDP", "BLK", "BLKB", "BLSH", "BMBL", "BMI", "BMO", "BMRN", "BMY",
    "BNS", "BNTX", "BOOT", "BOX", "BP", "BR", "BRZE", "BSBR", "BSP", "BSX",
    "BSY", "BTI", "BUD", "BURL", "BX", "BXP", "C", "CACI", "CAG", "CAKE",
    "CALM", "CAMT", "CAR", "CARR", "CASY", "CAT", "CB", "CBRS", "CC", "CCC",
    "CCI", "CCJ", "CCK", "CCL", "CCOI", "CDNS", "CDW", "CE", "CEG", "CELH",
    "CF", "CFG", "CGNX", "CHD", "CHEF", "CHKP", "CHRD", "CHRW", "CHTR", "CHWY",
    "CHYM", "CI", "CIB", "CIEN", "CIFR", "CINF", "CL", "CLBT", "CLF", "CLS",
    "CLX", "CM", "CMC", "CMCSA", "CMG", "CMI", "CMS", "CNA", "CNC", "CNI",
    "CNQ", "CNX", "COF", "COHR", "COHU", "COIN", "COKE", "COO", "COP", "CORZ",
    "COST", "CP", "CPAY", "CPB", "CPT", "CR", "CRDO", "CRL", "CRM", "CROX",
    "CRS", "CRSP", "CRUS", "CRWD", "CRWV", "CSCO", "CSL", "CSQR", "CSX", "CTAS",
    "CTSH", "CTVA", "CUBE", "CUZ", "CVE", "CVLT", "CVNA", "CVS", "CVX", "CW",
    "CX", "D", "DAL", "DAR", "DBX", "DD", "DDOG", "DE", "DECK", "DELL",
    "DEO", "DG", "DGII", "DHI", "DHR", "DIN", "DIOD", "DIS", "DKNG", "DKS",
    "DLO", "DLR", "DLTR", "DNN", "DOC", "DOCN", "DOCU", "DOMO", "DOV", "DOW",
    "DOX", "DPZ", "DRI", "DSGX", "DT", "DTE", "DUK", "DUOL", "DV", "DVN",
    "DXC", "DXCM", "E", "EBAY", "ECL", "EDU", "EEFT", "EGHT", "EGP", "EIX",
    "EL", "ELV", "EME", "EMN", "EMR", "ENB", "ENPH", "ENTG", "EOG", "EPAM",
    "EPD", "EQIX", "EQNR", "EQT", "ERIC", "ERIE", "ES", "ESE", "ESS", "ESTC",
    "ET", "ETN", "ETR", "ETSY", "EVER", "EVRG", "EVTC", "EW", "EWBC", "EXC",
    "EXEL", "EXLS", "EXPD", "EXPE", "EXR", "EXTR", "F", "FANG", "FAST", "FCX",
    "FDX", "FE", "FFIV", "FHN", "FICO", "FIG", "FIS", "FISV", "FITB", "FIVE",
    "FIVN", "FIZZ", "FLEX", "FLO", "FMC", "FMX", "FN", "FND", "FNV", "FORM",
    "FOUR", "FOXA", "FR", "FROG", "FRSH", "FRT", "FSLR", "FSLY", "FTI", "FTNT",
    "FTV", "FUL", "FWONK", "FWRD", "G", "GATX", "GBX", "GD", "GDDY", "GE",
    "GEHC", "GEN", "GFI", "GFS", "GGAL", "GGG", "GIB", "GILD", "GIS", "GKOS",
    "GL", "GLOB", "GLPI", "GLW", "GM", "GNRC", "GO", "GOLD", "GOOGL", "GPC",
    "GPI", "GPN", "GRAB", "GRMN", "GRND", "GS", "GSAT", "GSK", "GTES", "GTLB",
    "GWRE", "GWW", "HAIN", "HAL", "HALO", "HAS", "HBAN", "HCA", "HD", "HDB",
    "HEI", "HELE", "HIG", "HII", "HIW", "HL", "HLT", "HMC", "HMN", "HON",
    "HOOD", "HPE", "HPP", "HPQ", "HSBC", "HST", "HSY", "HTZ", "HUBG", "HUBS",
    "HUM", "HUN", "HUYA", "HWM", "HXL", "IBM", "IBN", "ICHR", "ICUI", "IDCC",
    "IDXX", "IEX", "IFF", "ILMN", "IMKTA", "IMO", "IMVT", "INCY", "INFQ", "INFY",
    "INGM", "INGR", "INSM", "INSP", "INTA", "INTC", "INTU", "INVH", "IONQ", "IONS",
    "IOT", "IP", "IPGP", "IQ", "IQMX", "IQV", "IRDM", "IRM", "IRTC", "ISRG",
    "IT", "ITRI", "ITUB", "ITW", "IVZ", "J", "JAZZ", "JBHT", "JBL", "JBLU",
    "JBS", "JCI", "JD", "JJSF", "JKHY", "JNJ", "JPM", "KBR", "KC", "KD",
    "KDP", "KEY", "KEYS", "KGC", "KHC", "KIM", "KKR", "KLAC", "KLIC", "KMB",
    "KMI", "KMPR", "KMX", "KN", "KNX", "KO", "KR", "KRC", "KRO", "KROS",
    "KSPI", "KSS", "KTOS", "KVUE", "KVYO", "L", "LAD", "LAMR", "LCID", "LDOS",
    "LEN", "LEVI", "LFUS", "LHX", "LI", "LIF", "LII", "LIN", "LITE", "LLY",
    "LMT", "LNC", "LNT", "LOGI", "LOW", "LPL", "LRCX", "LSCC", "LSTR", "LULU",
    "LUMN", "LUV", "LYB", "LYFT", "LYG", "LYV", "M", "MA", "MAA", "MANH",
    "MAR", "MAS", "MAT", "MBGL", "MCD", "MCHP", "MDB", "MDLZ", "MDT", "MET",
    "META", "MFC", "MFG", "MGY", "MHK", "MIDD", "MKL", "MKSI", "MLM", "MMM",
    "MNDY", "MNST", "MO", "MOG-A", "MOH", "MOMO", "MOS", "MPC", "MPWR", "MRK",
    "MRNA", "MRVL", "MS", "MSFT", "MSI", "MSTR", "MTB", "MTCH", "MTD", "MTDR",
    "MTSI", "MU", "MXL", "NATL", "NAVN", "NBIX", "NCLH", "NCNO", "NDSN", "NEE",
    "NEM", "NET", "NFLX", "NGG", "NI", "NICE", "NIO", "NIQ", "NKE", "NMR",
    "NNN", "NOC", "NOG", "NOK", "NOV", "NOVT", "NOW", "NSC", "NSIT", "NTAP",
    "NTCT", "NTDOY", "NTES", "NTLA", "NTNX", "NTR", "NTRS", "NTSK", "NUE", "NVAX",
    "NVCR", "NVDA", "NVMI", "NVR", "NVS", "NWG", "NXPI", "NXT", "O", "OCTV",
    "ODFL", "OKE", "OKTA", "OLED", "OLLI", "OLN", "OMCL", "ON", "ONB", "ONTO",
    "OPFI", "ORCL", "ORI", "ORLY", "OSIS", "OTEX", "OTIS", "OUST", "OVV", "OXY",
    "P", "PAAS", "PAG", "PAGS", "PANW", "PARA", "PATH", "PAY", "PAYC", "PAYP",
    "PAYX", "PB", "PBR", "PCAR", "PCG", "PCOR", "PCTY", "PCVX", "PD", "PDD",
    "PEG", "PEGA", "PEN", "PENG", "PEP", "PFE", "PFG", "PFGC", "PG", "PGR",
    "PH", "PHM", "PI", "PINS", "PKG", "PLD", "PLTK", "PLTR", "PLUG", "PLXS",
    "PM", "PNC", "PNR", "PNW", "PODD", "PONY", "POOL", "POWI", "PPG", "PPL",
    "PR", "PRU", "PSA", "PSN", "PSO", "PSX", "PTC", "PTRN", "PUBM", "PVH",
    "PWR", "PYPL", "Q", "QBTS", "QCOM", "QLYS", "QRVO", "QSR", "QTWO", "RAL",
    "RARE", "RBRK", "RCL", "REG", "REGN", "RELX", "RELY", "REXR", "RF", "RGA",
    "RGEN", "RH", "RIO", "RIVN", "RJF", "RKLB", "RL", "RMBS", "RMD", "RNG",
    "ROK", "ROKU", "ROL", "ROP", "ROST", "RPD", "RRC", "RS", "RSG", "RTX",
    "RUN", "RVLV", "RXO", "RXRX", "RY", "RYTM", "S", "SAH", "SAIA", "SAIC",
    "SAIL", "SAN", "SANM", "SAP", "SBAC", "SBUX", "SCCO", "SCHW", "SCL", "SEDG",
    "SFM", "SFTBY", "SHAK", "SHEL", "SHOO", "SHOP", "SHW", "SIGI", "SIMO", "SITM",
    "SJM", "SKHY", "SKYW", "SLAB", "SLB", "SLF", "SM", "SMCI", "SMFG", "SMTC",
    "SNAP", "SNDK", "SNDR", "SNOW", "SNPS", "SNX", "SNY", "SO", "SOFI", "SONY",
    "SPG", "SPOT", "SPSC", "SPT", "SRAD", "SRE", "SRPT", "SSNC", "SSRM", "ST",
    "STAG", "STE", "STLA", "STLD", "STM", "STT", "STX", "STZ", "SU", "SUZ",
    "SWK", "SWKS", "SYF", "SYK", "SYNA", "SYY", "T", "TAL", "TAP", "TCEHY",
    "TCOM", "TD", "TDC", "TDG", "TDY", "TEAM", "TECH", "TEL", "TENB", "TER",
    "TFC", "TFX", "TGT", "THG", "TJX", "TM", "TMO", "TMUS", "TNDM", "TOL",
    "TOST", "TPR", "TRGP", "TRMB", "TRN", "TRNO", "TROW", "TROX", "TRV", "TSCO",
    "TSEM", "TSLA", "TSM", "TSN", "TTAN", "TTD", "TTE", "TTMI", "TTWO", "TU",
    "TWLO", "TXN", "TXRH", "TXT", "TYL", "U", "UA", "UAL", "UBER", "UCTT",
    "UDR", "UEC", "UFCS", "UGA", "UHS", "UI", "UL", "ULCC", "ULTA", "UMC",
    "UNFI", "UNG", "UNH", "UNP", "UPS", "UPST", "URBN", "USB", "USFD", "USO",
    "UTHR", "V", "VALE", "VECO", "VEEV", "VERA", "VFC", "VIAV", "VICI", "VICR",
    "VIPS", "VIV", "VKTX", "VLO", "VLY", "VMC", "VNOM", "VNT", "VOD", "VRNS",
    "VRSN", "VRTX", "VSAT", "VSH", "VST", "VZ", "W", "WAB", "WAT", "WB",
    "WBD", "WCN", "WDAY", "WDC", "WEC", "WELL", "WERN", "WEX", "WFC", "WING",
    "WIT", "WIX", "WK", "WLK", "WM", "WMB", "WMK", "WMT", "WOLF", "WOR",
    "WPM", "WRB", "WSE", "WSM", "WST", "WTS", "WTW", "WU", "WWD", "XENE",
    "XOM", "XPEV", "XPO", "XRAY", "XYL", "XYZ", "YELP", "YETI", "YEXT", "YMM",
    "YOU", "YUM", "ZBH", "ZBRA", "ZETA", "ZION", "ZM", "ZS", "ZTO", "ZTS"
])

# Full scan — the union of Fasset and Expanded lists (100+ tickers).
FULL_WATCHLIST = sorted(set(FASSET_WATCHLIST) | set(EXPANDED_WATCHLIST))

# List 2 — temporary 5-ticker test list.
LIST_2 = ["AAPL", "MSFT", "NVDA", "GOOG", "META"]

# ── ACTIVE WATCHLIST ─────────────────────────────────────────────────────
# The agent screens and validates against WATCHLIST. To switch between the
# 5-ticker test list and the full 136-ticker list, change ONLY the right-hand
# side of this ONE assignment:
#   LIST_2          → 5-ticker test list (for testing)
#   FULL_WATCHLIST  → all 136 tickers (production, current)
WATCHLIST = FULL_WATCHLIST


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
