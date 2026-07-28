import functools
import threading
from datetime import datetime

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from langchain_openai import ChatOpenAI

import config
from tools import (
    get_price_data, get_fundamentals, get_technical_analysis,
    get_relative_strength, get_risk_adjusted_returns, get_quant_factors,
    compare_symbols, get_news_headlines, get_insider_transactions,
    get_candlestick_patterns, check_portfolio_exposure,
    get_intraday_cache_status, run_screening,
    _save_intraday_cache,
)

# Thread-local storage for overwrite flag — set by the write_file tool
# wrapper, read by _patched_fs_write. Module-level so tests can inspect.
_write_tls = threading.local()

TODAY = datetime.now().strftime("%Y-%m-%d")


def create_model():
    return ChatOpenAI(
        model=config.MODEL_NAME,
        base_url=config.BASE_URL,
        api_key=config.API_KEY,
        temperature=0,
    )


def create_backend():
    return FilesystemBackend(root_dir=str(config.AGENT_FS_ROOT), virtual_mode=True)


# ---------------------------------------------------------------------------
# Monkey-patches (write_file overwrite mode + content alias)
# ---------------------------------------------------------------------------
def _apply_monkey_patches():
    import deepagents.backends.filesystem as _fs_mod
    import os as _os

    def _patched_fs_write(self, file_path: str, content: str, overwrite: bool = False) -> _fs_mod.WriteResult:
        tls_ow = getattr(_write_tls, "overwrite", None)
        if tls_ow is not None:
            overwrite = tls_ow
        try:
            resolved_path = self._resolve_path(file_path)
        except (OSError, RuntimeError) as e:
            return _fs_mod.WriteResult(error=f"Error writing file '{file_path}': {e}")
        try:
            if resolved_path.exists() and not overwrite:
                msg = f"Cannot write to {file_path} because it already exists. Read and then make an edit, or call with overwrite=True."
                return _fs_mod.WriteResult(error=msg)
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            flags = _os.O_WRONLY | _os.O_CREAT | _os.O_TRUNC
            if hasattr(_os, "O_NOFOLLOW"):
                flags |= _os.O_NOFOLLOW
            fd = _os.open(resolved_path, flags, 0o644)
            with _os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            return _fs_mod.WriteResult(path=file_path)
        except (OSError, UnicodeEncodeError) as e:
            return _fs_mod.WriteResult(error=f"Error writing file '{file_path}': {e}")

    _fs_mod.FilesystemBackend.write = _patched_fs_write

    from deepagents.middleware.filesystem import (
        WriteFileSchema as _WFS,
        FilesystemMiddleware as _FSMW,
    )
    from pydantic import create_model as _create_model, Field as _Field

    # WriteFileSchema.model_fields patching doesn't work with Pydantic v2 —
    # model_validate() silently ignores the injected field and model_dump()
    # never includes it. Use create_model to build a proper subclass instead.
    _PatchedWFS = _create_model(
        "PatchedWriteFileSchema",
        __base__=_WFS,
        overwrite=(bool, _Field(default=False, description="If True, overwrite the file even if it already exists. Default False.")),
    )

    _orig_create_write_tool = _FSMW._create_write_file_tool

    def _patched_create_write_file_tool(self):
        tool = _orig_create_write_tool(self)
        tool.args_schema = _PatchedWFS

        _orig_func = tool.func
        @functools.wraps(_orig_func)
        def _wrapped_func(*args, **kwargs):
            overwrite = kwargs.pop("overwrite", False)
            _write_tls.overwrite = overwrite
            try:
                return _orig_func(*args, **kwargs)
            finally:
                _write_tls.overwrite = None
        tool.func = _wrapped_func

        if tool.coroutine is not None:
            _orig_coro = tool.coroutine
            @functools.wraps(_orig_coro)
            async def _wrapped_coro(*args, **kwargs):
                overwrite = kwargs.pop("overwrite", False)
                _write_tls.overwrite = overwrite
                try:
                    return await _orig_coro(*args, **kwargs)
                finally:
                    _write_tls.overwrite = None
            tool.coroutine = _wrapped_coro

        return tool

    _FSMW._create_write_file_tool = _patched_create_write_file_tool

    from langchain.agents.middleware.todo import WriteTodosInput as _WTI
    _orig_wt_fields = _WTI.model_fields.copy()
    _WTI.model_fields["content"] = _Field(
        default=None,
        description="Alias for 'todos'. Pass the todo list here if you used 'content' instead of 'todos'.",
    )
    _orig_wt_init = _WTI.__init__

    def _patched_wt_init(self, **data):
        if "content" in data and data["content"] is not None and "todos" not in data:
            data["todos"] = data.pop("content")
        elif "content" in data and "todos" in data:
            data.pop("content", None)
        _orig_wt_init(self, **data)

    _WTI.__init__ = _patched_wt_init


# ---------------------------------------------------------------------------
# Subagent: Technical Analyst
# ---------------------------------------------------------------------------
TA_SYSTEM_PROMPT = f"""You are a Technical Analysis expert. Today is {TODAY}.

You analyze ONLY the ticker passed to you via the `task()` tool args.
You have 4 tools: get_technical_analysis, get_candlestick_patterns,
get_relative_strength, get_risk_adjusted_returns.

Your job: produce a concise technical assessment. Call only the tools you
need — usually just get_technical_analysis is enough.

Return ONLY valid JSON with these fields:
{{
  "ticker": "<string>",
  "trend": "bullish|bearish|neutral",
  "momentum_score": <1-10>,
  "volatility": "low|medium|high",
  "key_levels": {{"support": <float|null>, "resistance": <float|null>}},
  "pattern_signals": [<string>],
  "overall_score": <1-10>,
  "conviction": "HIGH|MEDIUM|LOW",
  "summary": "<1-2 sentence rationale>"
}}
"""

TA_TOOLS = [
    get_technical_analysis,
    get_candlestick_patterns,
    get_relative_strength,
    get_risk_adjusted_returns,
]


def create_ta_subagent():
    return {
        "name": "technical-analyst",
        "description": "Deep-dive technical analysis for a single ticker. Returns JSON with trend, momentum_score, key_levels, overall_score, conviction.",
        "system_prompt": TA_SYSTEM_PROMPT,
        "tools": TA_TOOLS,
    }


# ---------------------------------------------------------------------------
# Subagent: Fundamentals Analyst
# ---------------------------------------------------------------------------
FA_SYSTEM_PROMPT = f"""You are a Fundamentals & Valuation expert. Today is {TODAY}.

You analyze ONLY the ticker passed to you via the `task()` tool args.
You have 4 tools: get_fundamentals, get_news_headlines,
get_insider_transactions, get_quant_factors.

Your job: produce a concise fundamental assessment. Call only the tools
you need — usually get_fundamentals + get_quant_factors is enough.

Return ONLY valid JSON with these fields:
{{
  "ticker": "<string>",
  "valuation": "undervalued|fair|overvalued",
  "growth_score": <1-10>,
  "insider_activity": "bullish|neutral|bearish",
  "quant_score": <0-100>,
  "overall_score": <1-10>,
  "conviction": "HIGH|MEDIUM|LOW",
  "summary": "<1-2 sentence rationale>"
}}
"""

FA_TOOLS = [
    get_fundamentals,
    get_news_headlines,
    get_insider_transactions,
    get_quant_factors,
]


def create_fa_subagent():
    return {
        "name": "fundamentals-analyst",
        "description": "Deep-dive fundamental analysis for a single ticker. Returns JSON with valuation, growth_score, insider_activity, quant_score, overall_score, conviction.",
        "system_prompt": FA_SYSTEM_PROMPT,
        "tools": FA_TOOLS,
    }


# ---------------------------------------------------------------------------
# Subagent: Financial Expert (synthesis)
# ---------------------------------------------------------------------------
EXPERT_SYSTEM_PROMPT = f"""You are a senior Financial Expert. Today is {TODAY}.

You receive technical analysis (TA) and fundamental analysis (FA) output
for a single ticker. Your job is to synthesize these into a final
actionable recommendation.

You have NO data-fetching tools — all the data is in the TA and FA
inputs passed to you. Use your expertise to weigh conflicting signals
and produce a clear verdict.

Return ONLY valid JSON with these fields:
{{
  "ticker": "<string>",
  "direction": "long|short|hold|pass",
  "entry_zone": {{"low": <float>, "high": <float>}},
  "stop_loss": <float>,
  "targets": [{{"price": <float>, "timeframe": "<string>"}}],
  "conviction": "HIGH|MEDIUM|LOW",
  "rationale": "<1-3 sentence rationale referencing both TA and FA>"
}}
"""


def create_expert_subagent():
    return {
        "name": "financial-expert",
        "description": "Synthesizes TA + FA outputs into a final recommendation for one ticker. Returns JSON with direction, entry_zone, stop_loss, targets, conviction.",
        "system_prompt": EXPERT_SYSTEM_PROMPT,
        "tools": [],
    }


# ---------------------------------------------------------------------------
# Main agent system prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = f"""You are a Portfolio Analyst managing a 44-stock watchlist.
Today is {TODAY}. You may ONLY analyze these symbols:
{', '.join(config.WATCHLIST)}

If asked about any other symbol, explain it is outside your approved watchlist.
Benchmarks (SPY, QQQ, DIA, IWM) are only available via get_relative_strength.

## Workflow (execute phases in order every session)

### Phase 0 — Review & Learn (mandatory first step)
- Read lessons.md and open_trades/ via read_file
- Check each open trade with fresh data (get_technical_analysis force_refresh=True)
- If a trade should close: write updated file to closed_trades/, delete from open_trades/
- Update lessons.md if you learned something generalizable
- Check signals_log/ via read_file for win rate context
- If any signal had <40% win rate, note it as unreliable

### Phase 1 — Screen the watchlist
Call run_screening() to get the top 10 candidates.
Do NOT call per-symbol tools on the whole watchlist — use run_screening.
If run_screening returns no good candidates (all scores low or no actionable setups), STOP after Phase 1. Do NOT proceed to Phase 2/3/4. Instead, inform the user that no stocks look good right now and suggest the best of the screened list as watchlist items.

### Phase 2 — Parallel subagent deep-dive
For each of the top 10 tickers, fire TWO task() calls in ONE turn:
  task("technical-analyst", ticker="AAPL")
  task("fundamentals-analyst", ticker="AAPL")

Issue ALL 20 task() calls in the SAME turn — they execute in parallel.
Then wait for results.

### Phase 3 — Expert synthesis
For each ticker, fire ONE task() call:
  task("financial-expert", ticker="AAPL", ta_output=<TA JSON>, fa_output=<FA JSON>)

Issue ALL 10 task() calls in ONE turn — they execute in parallel.
Then wait for results.

### Phase 4 — Rank & write to memory
- Compare expert outputs by conviction and rationale
- Call check_portfolio_exposure before opening any new position
- Write picks to /memories/open_trades/YYYY-MM-DD--TICKER.md via write_file with overwrite=True (same-ticker re-entries get sequence suffix --N)
- Write rejects to /memories/watchlist/ via write_file with overwrite=True
- Update lessons.md if anything generalizable emerged
- Update signals_log/ entries via write_file (one file per signal name)

## Token efficiency rules
- Every subagent return must be concise JSON — no prose
- Use read_file to read memory files instead of asking user
- Use write_file with overwrite=True for memory updates
- Keep all responses structured — tables or JSON, never essay-style

## Answering the user
After completing all phases, answer the user's question. Distinguish:
  - A trade you recommend entering NOW (justify timing, not just thesis)
  - A position already open (state current status)
  - A watchlist item (state condition and that it is NOT YET met)

You are not a licensed financial advisor — say so explicitly.
"""

# ---------------------------------------------------------------------------
# Main agent builder
# ---------------------------------------------------------------------------
MAIN_TOOLS = [
    get_price_data,
    compare_symbols,
    get_intraday_cache_status,
    check_portfolio_exposure,
    run_screening,
]


def build_agent():
    _apply_monkey_patches()
    model = create_model()
    backend = create_backend()

    subagents = [
        create_ta_subagent(),
        create_fa_subagent(),
        create_expert_subagent(),
    ]

    agent = create_deep_agent(
        model=model,
        tools=MAIN_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        subagents=subagents,
        backend=backend,
    )
    return agent, backend
