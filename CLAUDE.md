# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Fasset v2 — a modular Python finance analyst agent powered by Deep Agents (LangGraph-based) using `deepseek/deepseek-v4-pro` via OpenRouter. Scans a 44-stock watchlist, runs parallel technical + fundamental deep-dives, and produces structured trade recommendations with entry zones, stops, and targets. Exposed as both a CLI script and a Django webapp.

Full architecture docs are in `AGENTS.md`. This file covers what you need to be productive — commands, non-obvious patterns, and gotchas.

## Commands

```powershell
# CLI — run the agent once with a hardcoded query
python finance_agent.py

# Webapp — first-time setup
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py import_memories <username>    # one-time: migrate legacy shared positions → per-user memory
.venv\Scripts\python.exe manage.py issue_token <username>        # prints a DRF login token

# Webapp — run the dev server
.venv\Scripts\python.exe manage.py runserver                      # http://127.0.0.1:8000

# Data refresh (run before scans for fresh yfinance data)
python fetch_yfinance_data.py
python build_watchlist_summary.py
```

There are **no tests, no linter config, no type checker, no CI, no `pyproject.toml` or `requirements.txt`**. Dependencies are installed ad-hoc into `.venv/`: `deepagents`, `langchain-openai`, `yfinance`, `pandas`, `pandas-ta`, `python-dotenv`, `numpy`, `django`, `djangorestframework`.

## Architecture (supplement to AGENTS.md)

### Module dependency chain

```
config.py  →  tools.py  →  memory.py  →  agents.py  →  finance_agent.py (CLI)
                                                     →  webapp/agent_service.py (Web)
```

`config.py` is imported by everything. `tools.py` is pure functions (no config import beyond caching paths). `agents.py` imports from `tools.py` and `config.py`, applies monkey-patches, and exposes `build_agent()`. The webapp layer wraps `build_agent()` with threading, SSE, and DB sync — it never modifies core agent logic.

### Three monkey-patches (applied at `build_agent()` time in `agents.py`)

These are critical to the agent's function — do not remove without understanding each one:

1. **`write_file` overwrite mode** — Patches `FilesystemBackend.write()` and `FilesystemMiddleware._create_write_file_tool()` to add an `overwrite` boolean parameter. Without this, the agent can't update existing memory files. Uses `_write_tls` (thread-local) to carry the flag from the tool wrapper to the backend.

2. **`write_todos` content alias** — The DeepSeek model sometimes sends `content` instead of `todos` in `write_todos` calls. Creates a Pydantic v2-compatible subclass of `WriteTodosInput` that accepts both field names.

3. **`edit_file` no-op guard** — Rejects `edit_file` calls where `old_string == new_string`, returning a ToolMessage error instead of letting the filesystem middleware loop forever.

All three patches use `functools.wraps` and handle both sync (`tool.func`) and async (`tool.coroutine`) paths.

### Compliance check system

Both the CLI (`finance_agent.py`) and webapp (`webapp/agent_service.py`) run a two-phase post-execution compliance check on scan queries:

- **Phase 1 — Carryover review**: Verifies every pre-existing open/pending trade was reviewed during the run. If any were missed, warns.
- **Phase 2 — Symbol tracking**: Verifies every ticker that had a tool called on it has a memory file written (open/pending/watchlist/closed). If any are missing, auto-creates a reject entry in `watchlist/`.

The CLI prints compliance results to stdout. The webapp emits them as SSE events. The compliance check is the safety net for the agent "forgetting" to log a ticker — it prevents silent data loss.

### Per-user memory routing

`agents.create_backend(username)` builds a `CompositeBackend`:
- `/memories/open_trades/`, `/memories/pending_entries/`, `/memories/watchlist/`, `/memories/closed_trades/` → user-specific `FilesystemBackend` instances rooted at `agent_fs/users/<user>/memories/<sub>/`
- `/memories/` (bare) and everything else → shared `FilesystemBackend` rooted at `agent_fs/memories/`

The composite strips the route prefix before delegating, so `/memories/open_trades/AAPL.md` reaches the user's backend as `/AAPL.md`. The shared backend handles `lessons.md` and `signals_log/`.

`config.set_active_memories_root()` is called under `RUN_LOCK` so filesystem-side tools (`check_portfolio_exposure`, cooldown exclusions) read the correct user's memory. Defaults to the shared brain for CLI usage.

### Three-tier data cache

1. `yf_data/combined_history.csv` — bulk OHLCV for all tickers (24h TTL)
2. `yf_data/<TICKER>.json` — per-symbol info + fundamentals (24h TTL)
3. `yf_data/_intraday_cache.pkl` — in-memory tool result cache (2h TTL, saved on exit via `_save_intraday_cache()`)

### Symbol security

Every tool function that accepts a ticker calls `_check_symbol()` from `tools.py` — raises `ValueError` for any ticker not in `config.WATCHLIST` (44 symbols). All tools are wrapped with `_tool_guard` which catches exceptions and returns JSON error payloads instead of crashing the agent loop. The tool layer is the real security boundary; the system prompt's "ONLY analyze these symbols" is a reminder, not enforcement.

### RUN_LOCK and thread safety

`webapp/agent_service.py` uses a global `threading.Lock()` (`RUN_LOCK`) to serialize agent runs. The filesystem memory tree is not concurrency-safe — two simultaneous runs could write conflicting files. The lock is acquired for the entire run duration, including compliance and post-run sync.

## Patterns for making changes

### Adding a new tool

1. Add the function in `tools.py` — include `_check_symbol()` if it takes a ticker, wrap with `_tool_guard` if it can fail
2. Add it to `TOOLS_THAT_TAKE_SYMBOL` in both `finance_agent.py` and `webapp/agent_service.py` if it accepts a symbol parameter (needed for compliance tracking)
3. Import it in `agents.py` and add to the appropriate subagent's `TOOLS` list or `MAIN_TOOLS`

### Adding a new subagent

1. Define `SYSTEM_PROMPT` + `TOOLS` + `create_X_subagent()` in `agents.py`, following the existing pattern (dict with `name`, `description`, `system_prompt`, `tools`)
2. Add it to the `subagents` list in `build_agent()`
3. Update the main system prompt if the agent needs to know when/how to delegate to it

### Modifying the memory file format

Memory files use YAML frontmatter with `---` delimiters. Both `memory.py` (legacy MemoryManager) and `webapp/memory_sync.py` (DB projection) parse these. Changes to the frontmatter schema must be reflected in both places, plus any agent system prompts that instruct the agent how to write these files.

### Adding a Django management command

Place it in `webapp/management/commands/`. Follow the existing pattern: subclass `BaseCommand`, add arguments via `add_arguments()`, implement `handle()`.

## Key files reference

| File | Role |
|------|------|
| `config.py` | Environment, WATCHLIST, paths, caching TTLs |
| `tools.py` | All 20 tool functions + caching + `_check_symbol` + `_tool_guard` |
| `agents.py` | Subagent definitions, `build_agent()`, composite backend, monkey-patches |
| `finance_agent.py` | CLI entry point, stream rendering, compliance check |
| `memory.py` | Legacy MemoryManager (filesystem CRUD, daily context builder) |
| `webapp/agent_service.py` | Threaded SSE runner, `RUN_LOCK`, per-user agent lifecycle |
| `webapp/memory_sync.py` | Memory tree → DB projection (`sync_all`, `load_positions`) |
| `webapp/learning.py` | Deterministic signal win-rate reinforcement from closed trades |
| `webapp/models.py` | Django ORM: `Trade`, `Lesson`, `SignalLog`, `ChatMessage` |
| `webapp/streaming.py` | SSE wire formatting utility |
| `webapp/views.py` | HTTP endpoints, DRF token auth, dashboard rendering |
| `agent_fs/skills/` | Declarative skill instructions injected into agent context |
| `deepagents-main/` | Vendored copy of the deepagents SDK (reference, not imported) |

## Important constraints

- **Long-only portfolio** — the expert subagent is instructed to never recommend short positions. Bearish signals produce "hold" or "pass".
- **No concurrency** — `RUN_LOCK` serializes all webapp runs. Do not remove this without making the memory tree concurrency-safe.
- **Filesystem is source of truth** — the agent writes memory files directly; the DB is a synced projection, never written by the agent. The two-phase compliance check is what keeps them consistent.
- **`.env` contains live secrets** — it's git-ignored, but never commit it or hardcode API keys elsewhere.
- **Stopout cooldown** — tickers that were recently stopped out (14 days, configurable via `STOPOUT_COOLDOWN_DAYS`) are excluded from screening.
