import functools
import json as _json
import threading
from datetime import datetime

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend

from langchain.agents.middleware.todo import TodoListMiddleware
from langchain_openai import ChatOpenAI

import config
from tools import (
    get_price_data,
    get_fundamentals,
    get_technical_analysis,
    get_relative_strength,
    get_risk_adjusted_returns,
    get_quant_factors,
    compare_symbols,
    get_news_headlines,
    get_insider_transactions,
    get_candlestick_patterns,
    check_portfolio_exposure,
    get_intraday_cache_status,
    run_screening,
    _save_intraday_cache,
)

TODAY = datetime.now().strftime("%Y-%m-%d")


def create_model():
    return ChatOpenAI(
        model=config.MODEL_NAME,
        base_url=config.BASE_URL,
        api_key=config.API_KEY,
        temperature=0,
        timeout=120,
        max_retries=2,
    )


# Per-user memory routes: positions stay in the user's root; lessons, signals,
# and the shared brain resolve through the default/shared backend.
_USER_MEMORY_SUBDIRS = ("open_trades", "pending_entries", "watchlist", "closed_trades")


def create_backend(username: str | None = None):
    """Build the agent's filesystem backend.

    With a username, returns a CompositeBackend routing per-user memory
    directories (open/pending/watchlist/closed trades) to that user's root
    while the shared learning brain (lessons.md, signals_log/) stays global.
    Without a username, returns the shared brain backend directly.

    Each routed directory gets its own backend rooted at that directory,
    because the composite strips the full route prefix before delegating
    (e.g. `/memories/open_trades/X.md` -> `/X.md` relative to the
    open_trades root).
    """
    shared_backend = FilesystemBackend(
        root_dir=str(config.SHARED_MEMORY_ROOT), virtual_mode=True
    )
    if not username:
        return shared_backend
    user_root = config.user_memory_root(username)
    routes: dict[str, FilesystemBackend] = {}
    for sub in _USER_MEMORY_SUBDIRS:
        subdir = user_root / sub
        subdir.mkdir(parents=True, exist_ok=True)
        routes[f"/memories/{sub}/"] = FilesystemBackend(
            root_dir=str(subdir), virtual_mode=True
        )
    # The bare /memories/ prefix and anything else in the shared brain resolve
    # through the shared backend; without this route, `/memories/lessons.md`
    # would be looked up as `<shared>/memories/lessons.md`.
    routes["/memories/"] = shared_backend
    return CompositeBackend(default=shared_backend, routes=routes)


# ---------------------------------------------------------------------------
# Monkey-patches
# ---------------------------------------------------------------------------
def _apply_monkey_patches():
    # =========================================================================
    # Fix 1: write_todos content alias + JSON string deserialization
    # =========================================================================
    # DeepSeek sometimes sends `content` instead of `todos`, and sometimes
    # serializes the todo list as a JSON string instead of a native list.
    # Both variants are handled here.
    import langchain.agents.middleware.todo as _todo_mod
    from langchain.agents.middleware.todo import (
        WriteTodosInput as _WTI,
        _write_todos as _orig_write_todos_func,
        _awrite_todos as _orig_awrite_todos_func,
        Todo as _Todo,
    )
    from langchain.tools import ToolRuntime as _ToolRuntime
    from pydantic import create_model as _create_model, Field as _Field

    _PatchedWTI = _create_model(
        "PatchedWriteTodosInput",
        __base__=_WTI,
        todos=(
            list[_Todo] | None,
            _Field(default=None),
        ),
        content=(
            str | list | None,
            _Field(
                default=None,
                description="Alias for 'todos'. Accepts a list of todo dicts or a JSON string. Ignored if 'todos' is also provided.",
            ),
        ),
    )

    def _normalize_todos(todos, content):
        """Resolve todos from either the todos or content parameter.

        Handles three cases:
        1. `todos` is provided natively → use as-is
        2. `content` is a native list → use as todos fallback
        3. `content` is a JSON string → parse into todos
        """
        if todos:
            return todos
        if not content:
            return None
        # Case 3: JSON string
        if isinstance(content, str):
            try:
                parsed = _json.loads(content)
                if isinstance(parsed, list):
                    return parsed
            except (TypeError, ValueError, _json.JSONDecodeError):
                pass
            return None
        # Case 2: native list
        if isinstance(content, list):
            return content
        return None

    def _patched_write_todos(
        runtime: _ToolRuntime,
        todos: list[_Todo] | None = None,
        content: str | list | None = None,
    ):
        return _orig_write_todos_func(runtime, _normalize_todos(todos, content) or [])

    def _patched_awrite_todos(
        runtime: _ToolRuntime,
        todos: list[_Todo] | None = None,
        content: str | list | None = None,
    ):
        return _orig_awrite_todos_func(runtime, _normalize_todos(todos, content) or [])

    _todo_mod.WriteTodosInput = _PatchedWTI
    _todo_mod._write_todos = _patched_write_todos
    _todo_mod._awrite_todos = _patched_awrite_todos

    # =========================================================================
    # Fix 2: edit_file no-op guard — reject old_string == new_string
    # =========================================================================
    from deepagents.middleware.filesystem import FilesystemMiddleware as _FSMW
    from langchain_core.messages import ToolMessage as _TM

    _orig_create_edit_tool = _FSMW._create_edit_file_tool

    def _patched_create_edit_file_tool(self):
        tool = _orig_create_edit_tool(self)

        _orig_func = tool.func

        @functools.wraps(_orig_func)
        def _wrapped_edit_func(*args, **kwargs):
            old_string = kwargs.get("old_string", "")
            new_string = kwargs.get("new_string", "")
            if old_string and old_string == new_string:
                return _TM(
                    content="Error: old_string is identical to new_string — nothing to change. Provide different content for new_string.",
                    name="edit_file",
                    tool_call_id=(
                        kwargs.get("runtime").tool_call_id
                        if hasattr(kwargs.get("runtime"), "tool_call_id")
                        else ""
                    ),
                    status="error",
                )
            return _orig_func(*args, **kwargs)

        tool.func = _wrapped_edit_func

        if tool.coroutine is not None:
            _orig_coro = tool.coroutine

            @functools.wraps(_orig_coro)
            async def _wrapped_edit_coro(*args, **kwargs):
                old_string = kwargs.get("old_string", "")
                new_string = kwargs.get("new_string", "")
                if old_string and old_string == new_string:
                    return _TM(
                        content="Error: old_string is identical to new_string — nothing to change. Provide different content for new_string.",
                        name="edit_file",
                        tool_call_id=(
                            kwargs.get("runtime").tool_call_id
                            if hasattr(kwargs.get("runtime"), "tool_call_id")
                            else ""
                        ),
                        status="error",
                    )
                return await _orig_coro(*args, **kwargs)

            tool.coroutine = _wrapped_edit_coro

        return tool

    _FSMW._create_edit_file_tool = _patched_create_edit_file_tool


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

CRITICAL RULES:
- When a ticker has negative earnings or a large trailing loss, report the
  number as-is. Do NOT assert "one-time charges," "impairments," or other
  explanations for the loss unless you have verified this claim through a
  specific tool call. State the earnings decline factually and flag it as
  unverified if you cannot confirm the cause.
- When evaluating valuation (PEG, P/E, P/FCF), compare to the ticker's
  sector context if available. A PEG of 5x in Healthcare may be normal;
  in Tech it is extreme. Be consistent across tickers.

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

CRITICAL: Entry zones, stops, and targets MUST be grounded in the TA and
FA data you receive. Follow these rules:
- The entry_zone must be anchored to the TA key_levels (support/resistance)
  and current price provided in the TA summary.
- entry_zone high must not exceed the TA resistance level (if available).
- entry_zone low must be near the TA support level (if available).
- stop_loss must be below the TA support level.
- Target prices must be at or below the TA resistance level for T1,
  and can extend beyond resistance for T2 but with explicit justification.
- Never invent prices that deviate more than 10% from the current price
  provided in the TA data. If the TA data lacks key levels, set
  entry_zone to null values and explain why.
- If the TA summary includes a latest_close price, the entry zone must be
  within 10% of it in either direction. An entry zone of $63 when the
  stock trades at $145 is a hallucination — flag it as "inconsistent with
  current price" and set entry_zone to null.

Return ONLY valid JSON with these fields:
{{
  "ticker": "<string>",
  "direction": "long|hold|pass",
  "entry_zone": {{"low": <float|null>, "high": <float|null>}},
  "stop_loss": <float|null>,
  "targets": [{{"price": <float>, "timeframe": "<string>"}}],
  "conviction": "HIGH|MEDIUM|LOW",
  "rationale": "<1-3 sentence rationale referencing both TA and FA>"
}}

Field rules by direction (keep the schema consistent — no mixing):
- direction "long": entry_zone, stop_loss, and targets MUST all be populated numbers.
- direction "hold" or "pass": entry_zone MUST be {{"low": null, "high": null}},
  stop_loss MUST be null, and targets MUST be []. Do NOT include entry levels
  when you are not recommending a new long entry — "hold" means keep/avoid, it
  is not a fresh entry with a zone, stop, and targets.

IMPORTANT: This portfolio is long-only. Do NOT recommend short positions. If the stock looks bearish, recommend "hold" or "pass" instead.
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
SYSTEM_PROMPT = f"""You are a Portfolio Analyst managing a {len(config.WATCHLIST)}-stock watchlist.
Today is {TODAY}. You may ONLY analyze these {len(config.WATCHLIST)} symbols.

Two scan modes are available:
- **Fasset Scan** ({len(config.FASSET_WATCHLIST)} tickers): curated list available on Fasset exchange.
- **Full Scan** ({len(config.WATCHLIST)} tickers): expanded coverage across all sectors.

When calling run_screening(), pass mode='fasset' for the curated list or mode='full' for all tickers. The user will tell you which mode they want.

If asked about any symbol outside the {len(config.WATCHLIST)}-ticker watchlist, explain it is outside your approved universe.
Benchmarks (SPY, QQQ, DIA, IWM) are only available via get_relative_strength.

## Your tools (do not try to use tools outside this list)
You (the main agent) have ONLY these data tools:
  get_price_data, compare_symbols, get_intraday_cache_status,
  check_portfolio_exposure, run_screening
plus filesystem tools (ls, read_file, write_file, edit_file, grep, glob),
write_todos, and the task() tool for delegating to subagents.

## Memory layout (use these exact paths)
- /memories/lessons.md — consolidated trading lessons (shared brain)
- /memories/signals_log/ — one file per signal, with win-rate stats (shared brain)
- /memories/open_trades/ — filled positions (this user's portfolio)
- /memories/pending_entries/ — pending entry-zone triggers (this user's portfolio)
- /memories/watchlist/ — candidates and rejects (this user's portfolio)
- /memories/closed_trades/ — resolved positions (this user's portfolio)
Always address memory files through the subpaths above (e.g. ls /memories/open_trades).
Do not rely on a bare `ls /memories` to list positions — the shared brain and the
user's position folders are separate; list each subdirectory directly.

The deep-dive tools get_technical_analysis, get_candlestick_patterns,
get_relative_strength, get_risk_adjusted_returns, get_fundamentals,
get_news_headlines, get_insider_transactions, and get_quant_factors do NOT
exist on your toolset. They are ONLY available to the subagents
technical-analyst and fundamentals-analyst. To analyze any ticker's technicals
or fundamentals you MUST delegate with task("technical-analyst", ticker="X")
and task("fundamentals-analyst", ticker="X"). Never attempt to call these
deep-dive tools directly — if a tool name is not in the list above, do not
call it; delegate instead.

## Direct ticker questions (not a scan)
If the user asks about ONE specific ticker (e.g. "what do you think about MSFT?"),
do NOT run the full Phase 1 screen and do NOT stop because the ticker is not in
a screening top-10. Instead, immediately do a targeted deep-dive:
1. task("technical-analyst", ticker="X") and task("fundamentals-analyst", ticker="X")
   fired in the SAME turn.
2. After both return, task("financial-expert", ticker="X", ta_output=<TA JSON>,
   fa_output=<FA JSON>) including the current price from get_price_data.
Then answer with the expert's verdict. Still do Phase 0 review of open trades
first if there are carryover positions.

## Workflow (execute phases in order every session)

### Phase 0 — Review & Learn (mandatory first step)
- Read lessons.md, open_trades/ (filled positions), and pending_entries/ via read_file
- Review recent closed_trades/ files first — carry the win/loss context (which signals worked, which failed) into this session's decisions.
- For EACH open trade (type: filled) and each pending entry, fetch LIVE data with get_price_data (your only live-price tool). Never report a position from the memory file alone.
- Compare the live close to the position's stop_loss, T1, and T2 from the memory file. If a stop is breached, write the updated file to closed_trades/ immediately. If a stop is approaching (within ~3%), tighten or flag it.
- If a trade should close: write updated file to closed_trades/, delete from open_trades/
- Every closed-trade file MUST include `signals_used: [...]` (the signal names that drove the entry, e.g. ["composite_screening_top10", "extreme_oversold_fa_backstop"]) plus numeric `return_realized_pct` so win rates can be computed. If a trade was stopped out, that is a counted miss for every signal in signals_used.
- Update lessons.md with any new generalizable insights (MANDATORY — do this every run)
- Check signals_log/ via read_file for win rate context
- If any signal had <40% win rate, note it as unreliable
- IMPORTANT: Distinguish between open_trades/ (type: filled — positions you actually entered) and pending_entries/ (type: pending — entry zone not yet triggered). Count only filled entries as real open positions.
- IMPORTANT: When reporting active positions, show BOTH the live price from get_price_data AND the stored entry/stop/target levels, and reference any applicable lessons. The answer must reflect current market status, not just the memory files.

### Phase 1 — Screen the watchlist
Call run_screening() to get the top 10 candidates.
Do NOT call per-symbol tools on the whole watchlist — use run_screening.
If run_screening returns no good candidates (all scores low or no actionable setups), STOP after Phase 1 ONLY for scan requests. Do NOT proceed to Phase 2/3/4 for the screen. Instead, inform the user that no stocks look good right now and suggest the best of the screened list as watchlist items.
EXCEPTION: if the user asked about a specific ticker directly (see "Direct ticker questions" above), deep-dive that ticker via task() regardless of its screening rank — this overrides the STOP rule.

### Phase 2 — Parallel subagent deep-dive
For each of the top 10 tickers, fire TWO task() calls in ONE turn:
  task("technical-analyst", ticker="AAPL")
  task("fundamentals-analyst", ticker="AAPL")

IMPORTANT: Before Phase 2, check open_trades/ and pending_entries/ via ls. Exclude any ticker that already has an open trade (type: filled) or a pending entry. Only deep-dive NEW candidates NOT already in the portfolio.

Issue ALL 20 task() calls in the SAME turn — they execute in parallel.
Then wait for results.

### Phase 3 — Expert synthesis (MANDATORY for every Phase 2 ticker)
For each ticker that passed through Phase 2, fire ONE task() call:
  task("financial-expert", ticker="AAPL", ta_output=<TA JSON>, fa_output=<FA JSON>)

IMPORTANT: Every ticker that received Phase 2 deep-dive MUST also receive a Phase 3
expert synthesis. No exceptions. If you skip a ticker here, explain why in
the final report. The expert subagent resolves TA vs FA conflicts — skipping
it means the ticker's recommendation is incomplete.

CRITICAL: In each task description, include the CURRENT PRICE from the
get_price_data or get_technical_analysis tool output. Format:
  "Current price: $XXX. TA support: $XX, TA resistance: $YY."
This anchors the expert's entry zone to real prices and prevents hallucination.

Issue ALL task() calls in ONE turn — they execute in parallel.
Then wait for results.

### Phase 4 — Rank & write to memory
- Compare expert outputs by conviction and rationale
- Call check_portfolio_exposure before opening any new position
- Write filled positions (type: filled) to /memories/open_trades/YYYY-MM-DD--TICKER.md via write_file
- Write pending entries (type: pending — waiting for entry zone to trigger) to /memories/pending_entries/YYYY-MM-DD--TICKER.md via write_file
- All trade files MUST include a YAML field `type: filled` or `type: pending` in the frontmatter
- Write rejects to /memories/watchlist/ via write_file
- MANDATORY: Write a watchlist or reject file for EVERY ticker that passed through Phase 2-3. No ticker goes unlogged.
- Update lessons.md with any new generalizable insights (MANDATORY)
- Update signals_log/ entries via write_file (one file per signal name). For each signal you used, ensure a file exists — initialize new signal files on first use (triggered_correctly: 0, triggered_falsely: 0).

## Token efficiency rules
- Every subagent return must be concise JSON — no prose
- Use read_file to read memory files instead of asking user
- Use write_file for memory updates (overwrites if file already exists)
- Keep all responses structured — tables or JSON, never essay-style

## Answering the user
After completing all phases, answer the user's question. Distinguish:
  - A trade you recommend entering NOW (justify timing, not just thesis)
  - A position already open (state current status, distinguish between filled and pending)
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


def build_agent(username: str | None = None):
    _apply_monkey_patches()
    model = create_model()
    backend = create_backend(username)

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
        middleware=[TodoListMiddleware()],
    )
    return agent, backend
