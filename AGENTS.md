# AGENTS.md

## Project

Modular Python app (Fasset v2). A Deep Agents (LangGraph-based) finance analyst agent using `deepseek/deepseek-v4-flash` via OpenRouter.

## File Structure

```
config.py          ← WATCHLIST, model constants, .env loading, memory-root routing
tools.py           ← 20 consolidated tool functions (13 agent-facing + 7 internal)
memory.py          ← MemoryManager: lessons, open/closed trades, signals_log, daily context
agents.py          ← Subagent definitions (TA, FA, Expert) + main agent builder + composite backend
finance_agent.py   ← Entry point: stream runner + compliance check
.env               ← API keys and model config (git-ignored if repo exists)
agent_fs/memories/ ← SHARED learning brain (lessons + signal win rates)
  lessons.md       ← Consolidated principles
  signals_log/     ← Signal win-rate tracking (deterministic, recomputed)
agent_fs/users/<u>/memories/ ← Per-user memory (git-ignored)
  open_trades/     ← Current positions
  pending_entries/ ← Conditional entries
  watchlist/       ← Candidates + rejects
  closed_trades/   ← Resolved positions
yf_data/           ← Cached yfinance data (companion scripts)
fasset_web/        ← Django project (settings, urls)
webapp/            ← Django app
  agent_service.py ← Threaded SSE runner: per-user agent, RUN_LOCK, post-run sync
  memory_sync.py   ← Memory tree → DB projection (Trade/Lesson/SignalLog) + load_positions
  learning.py      ← Deterministic signal win-rate reinforcement from closed trades
  models.py        ← Trade, Lesson, SignalLog, ChatMessage
  management/commands/import_memories.py ← One-time legacy memory → per-user migration
```

## Environment

Both system Python 3.12 and venv work. For the configured venv (adjust path):

```powershell
python finance_agent.py
```

Dependencies: `deepagents`, `langchain-openai`, `yfinance`, `pandas`, `pandas-ta`, `python-dotenv`, `numpy`

## Setup

1. **`.env` file** — create in project root:
```
OPENROUTER_API_KEY=sk-or-v1-...
MODEL_NAME=deepseek/deepseek-v4-pro
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

2. **Companion scripts** — refresh cached data before running scans:
```powershell
python fetch_yfinance_data.py
python build_watchlist_summary.py
```

3. **No Unsloth Studio required** — this agent uses OpenRouter, not local models.

## Running

```powershell
python finance_agent.py
```

The `__main__` block runs a hardcoded scan query (rank by composite_score, top 3 ideas). No CLI argument parsing.

## Webapp (Django)

The agent is also exposed as a Django webapp (`manage.py runserver`). Two screens: Market scan (fresh scan + positions) and Chat (streamed conversation). Auth is DRF token → session login.

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py import_memories <username>   # one-time: move legacy shared positions → per-user memory root
.venv\Scripts\python.exe manage.py issue_token <username>       # prints a login token
.venv\Scripts\python.exe manage.py runserver                    # http://127.0.0.1:8000
```

- `fasset_web/` — Django project (settings read `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` from `.env`)
- `webapp/` — app: `agent_service.py` (threaded SSE runner + compliance), `memory_sync.py` (memory → DB projection), `learning.py` (deterministic reinforcement), `streaming.py` (SSE framing), `views.py`, templates + Tailwind CDN frontend
- Runs are serialized by a global `RUN_LOCK` (shared filesystem memory is not concurrency-safe)
- Each run is bound to the logged-in user: the agent's backend routes that user's positions to `agent_fs/users/<u>/memories`, while lessons/signals stay shared
- Chat history is DB-backed (`ChatMessage`) keyed by user + session id

## Architecture (v2 — Refactored)

### Model
- `deepseek/deepseek-v4-pro` via OpenRouter (`ChatOpenAI`), temperature 0. API key from `.env`.

### Subagents

| Subagent | Tools | Output |
|----------|-------|--------|
| `technical-analyst` | get_technical_analysis, get_candlestick_patterns, get_relative_strength, get_risk_adjusted_returns | JSON: trend, momentum_score, key_levels, overall_score, conviction |
| `fundamentals-analyst` | get_fundamentals, get_news_headlines, get_insider_transactions, get_quant_factors | JSON: valuation, growth_score, insider_activity, quant_score, overall_score, conviction |
| `financial-expert` | (none) | JSON: direction, entry_zone, stop_loss, targets, conviction, rationale |

### Main Agent Tools
- `run_screening` — Python-based pre-filter, reads cached data, returns top 10 via composite scoring
- `compare_symbols` — cross-sectional ranking
- `get_price_data` — single-symbol price/return stats
- `check_portfolio_exposure` — sector overlap check
- `get_intraday_cache_status` — diagnostic

### Execution Flow (4 phases per session)

1. **Review & Learn** — Read lessons.md + open_trades/, resolve any closed positions, update signals_log/
2. **Screen** — `run_screening()` → top 10 candidates (Python pandas scoring, ~100 tokens)
3. **Parallel Deep Dive** — Fire 20 `task()` calls in one turn: TA(tkr1)+FA(tkr1)...×10. All execute concurrently.
4. **Expert Synthesis** — Fire 10 `task()` calls in one turn: Expert(tkr1)...×10. Then rank, write picks, rejections, and update memory.

### Parallelism Model
Deep Agents allows multiple `task()` calls in a single turn — they execute concurrently. This gives zero-config parallelism:
- Turn 2: 20 parallel subagents (10 TA + 10 FA)
- Turn 3: 10 parallel Expert subagents

### Token Efficiency
- **Python pre-filter** reduces 44 tickers to top 10 numerically (~100 tokens vs ~5000+ if LLM reasoned about each)
- **Context isolation** — each subagent only loads one ticker's data
- **Concise JSON contract** — subagents return structured data, not prose
- **Consolidated tools** — 20 tools (down from ~30), removed redundant individual indicator tools

### Memory System
- **Shared learning brain** (`agent_fs/memories/`) — `lessons.md` (consolidated ticker-agnostic principles, max ~25 bullets) + `signals_log/` (per-signal win-rate tracking, e.g., rsi_divergence.md with `triggered_correctly`/`triggered_falsely`).
- **Per-user memory** (`agent_fs/users/<u>/memories/`) — `open_trades/`, `pending_entries/`, `watchlist/`, `closed_trades/`. Files are `YYYY-MM-DD--TICKER.md` with YAML frontmatter.
- **Composite backend** — `agents.create_backend(username)` builds one `FilesystemBackend` per user subdir (`/memories/open_trades/`, `/memories/pending_entries/`, `/memories/watchlist/`, `/memories/closed_trades/`, each rooted at the subdir itself) plus `/memories/` → shared brain. The agent only ever touches the filesystem; the DB is a synced projection.
- **Active root** — `config.set_active_memories_root()` is set per-run under `RUN_LOCK`; `tools.py` filesystem tools (`check_portfolio_exposure`, cooldown exclusions) read it via `config.active_memories_root()` (defaults to shared brain for CLI/dev).
- **Closed trades** are required to record `signals_used: [...]` + `return_realized_pct`; a stopped-out trade counts as a miss per signal.
- **DB projection** (`webapp/memory_sync.py`) — `sync_all(username)` upserts `Trade`/`Lesson`/`SignalLog` rows; `load_positions(username)` is DB-backed for the UI (watchlist deduped per-ticker).
- **Deterministic reinforcement** (`webapp/learning.py`) — after every run, recomputes per-signal win rates from closed-trade outcomes and rewrites the shared `signals_log/*.md` + `SignalLog` rows. Manual counts are preserved as a seed until trades with explicit `signals_used` accumulate.
- Memory files use `write_file` with `overwrite=True` for updates.

### Symbol Whitelist
`WATCHLIST` (44 tickers) enforced inside every tool via `_check_symbol()` — raises `ValueError` on out-of-list tickers. Tool layer is the real security boundary.

### yfinance Schema Drift
`get_news_headlines` handles shifting yfinance response schemas (content/nested dict fallbacks). yfinance changes frequently; news parsing may break on version updates.

## No tests, lint, CI

There are no tests, linter config, type checker, `requirements.txt`, or `pyproject.toml`. If adding tooling, pin runtime deps: `deepagents`, `langchain-openai`, `yfinance`, `pandas`, `pandas-ta`, `python-dotenv`, `numpy`.
