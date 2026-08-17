# Fasset Agent — Architecture & Reference

The Fasset agent is a modular Python finance-analysis agent built on **Deep Agents** (LangGraph-based) that scans a stock watchlist and produces structured trade recommendations. This document covers the agent's own code (the "engine") — for the Django web interface, see [WEBAPP.md](WEBAPP.md).

---

## 1. What it is

The agent is a **portfolio analyst** that:

1. Reviews existing positions and closed trades for lessons
2. Screens a watchlist numerically (Python, not LLM)
3. Deep-dives the top candidates using parallel subagents
4. Synthesizes recommendations with entry zones, stops, and targets
5. Writes results to a filesystem memory tree

It runs in two modes:
- **CLI** (`finance_agent.py`) — a terminal stream runner
- **Webapp** (Django) — the same engine exposed over SSE

The LLM is `deepseek/deepseek-v4-pro` (or whatever `MODEL_NAME` is set to) via OpenRouter, invoked through `ChatOpenAI` at `temperature=0`.

---

## 2. Module dependency chain

```
config.py  →  tools.py  →  memory.py  →  agents.py  →  finance_agent.py (CLI)
                                                     →  webapp/agent_service.py (Web)
```

| Module | Role |
|--------|------|
| `config.py` | Environment, watchlists, paths, caching TTLs. Imported by everything. |
| `tools.py` | All 20 tool functions (data fetching, analysis, screening). Pure functions + caching. |
| `memory.py` | Legacy `MemoryManager` for filesystem CRUD + daily context builder. |
| `agents.py` | Subagent definitions, `build_agent()`, composite backend, monkey-patches. |
| `finance_agent.py` | CLI entry point, stream rendering, compliance check. |

The webapp layer wraps `build_agent()` — it never modifies core agent logic.

---

## 3. Key components

### 3.1 Model factory (`agents.create_model`)

Returns a `ChatOpenAI` instance:
```python
ChatOpenAI(model=config.MODEL_NAME, base_url=config.BASE_URL,
           api_key=config.API_KEY, temperature=0)
```

`config` reads these from `.env`:
- `OPENROUTER_API_KEY`
- `MODEL_NAME` (default `deepseek/deepseek-v4-pro`)
- `OPENROUTER_BASE_URL` (default `https://openrouter.ai/api/v1`)

### 3.2 Backend (`agents.create_backend`)

Builds the agent's virtual filesystem. With a username, returns a `CompositeBackend` that routes position directories per-user while the learning brain stays shared:

| Virtual path | Resolves to |
|---|---|
| `/memories/open_trades/*` | `agent_fs/users/<user>/memories/open_trades/*` |
| `/memories/pending_entries/*` | `agent_fs/users/<user>/memories/pending_entries/*` |
| `/memories/watchlist/*` | `agent_fs/users/<user>/memories/watchlist/*` |
| `/memories/closed_trades/*` | `agent_fs/users/<user>/memories/closed_trades/*` |
| `/memories/lessons.md` | `agent_fs/memories/lessons.md` (shared) |
| `/memories/signals_log/*` | `agent_fs/memories/signals_log/*` (shared) |

The composite **strips the route prefix** before delegating — `/memories/open_trades/NVDA.md` reaches the open_trades backend as `/NVDA.md`.

### 3.3 Subagents (`agents.py`)

Three subagents, defined as plain dicts (`name`, `description`, `system_prompt`, `tools`):

| Subagent | Tools | Output (JSON) |
|----------|-------|---------------|
| `technical-analyst` | `get_technical_analysis`, `get_candlestick_patterns`, `get_relative_strength`, `get_risk_adjusted_returns` | trend, momentum_score, key_levels, overall_score, conviction |
| `fundamentals-analyst` | `get_fundamentals`, `get_news_headlines`, `get_insider_transactions`, `get_quant_factors` | valuation, growth_score, insider_activity, quant_score, conviction |
| `financial-expert` | *(none — pure synthesis)* | direction, entry_zone, stop_loss, targets, conviction, rationale |

Subagents are delegated to via `task("technical-analyst", ticker="X")`. The main agent **cannot** call the deep-dive tools directly — they only exist on the subagents.

### 3.4 Main agent tools

The main agent (`build_agent`) has only these data tools:
- `run_screening` — numeric pre-filter, returns top 10
- `compare_symbols` — cross-sectional ranking
- `get_price_data` — single-symbol price/return stats
- `check_portfolio_exposure` — sector overlap check
- `get_intraday_cache_status` — diagnostic

Plus filesystem tools (`ls`, `read_file`, `write_file`, `edit_file`, `grep`, `glob`), `write_todos`, and `task()`.

### 3.5 Tools layer (`tools.py`)

Every tool that accepts a ticker calls `_check_symbol()` which raises `ValueError` for any symbol not in `config.WATCHLIST`. All tools are wrapped with `_tool_guard` which catches exceptions and returns JSON error payloads — the tool layer is the real security boundary.

The `WATCHLIST` is the union of `FASSET_WATCHLIST` (44 curated) and `EXPANDED_WATCHLIST` (92 additional) = 136 tickers total.

---

## 4. Execution flow (4 phases)

Enforced by the system prompt in `agents.py`:

### Phase 0 — Review & Learn
- Read `lessons.md`, `open_trades/`, `pending_entries/`, recent `closed_trades/`
- Fetch live prices via `get_price_data` for each open/pending position
- Compare live close against stop_loss and targets; close breached stops
- Every closed trade must record `signals_used: [...]` and `return_realized_pct`
- Update `lessons.md` with new generalizable insights

### Phase 1 — Screen
- Call `run_screening()` — pure Python scoring, no LLM reasoning
- Composite score = `fundamental_quality × 0.35 + momentum_12_1 × 0.35 + rsi_neutrality × 0.15 + sharpe_ratio × 0.15`
- Returns top 10 candidates (~100 tokens vs ~5000 if LLM reasoned about each)
- Excludes recently stopped-out tickers (cooldown, `STOPOUT_COOLDOWN_DAYS`=14d) and tickers failing the fundamental quality gate (profit margins < -50% or no P/E)

### Phase 2 — Parallel deep-dive
- Fire 20 `task()` calls in ONE turn: TA + FA for each of the top 10 tickers
- Deep Agents executes them concurrently
- Excludes tickers already in `open_trades/` or `pending_entries/`

### Phase 3 — Expert synthesis
- Fire 10 `task()` calls in ONE turn: one expert per ticker
- Expert has no data tools — pure synthesis of TA + FA JSON
- The current price is included in each task description to anchor entry zones and prevent hallucination

### Phase 4 — Rank & write
- Compare expert outputs by conviction
- Call `check_portfolio_exposure` before opening new positions
- Write picks to `open_trades/`, conditional entries to `pending_entries/`, rejects to `watchlist/`
- Update `lessons.md` and `signals_log/`

### Direct ticker questions

If the user asks about ONE specific ticker, the agent skips the screen and does a targeted deep-dive (TA + FA → expert) regardless of screening rank.

---

## 5. Monkey-patches (`agents._apply_monkey_patches`)

Applied at `build_agent()` time. Critical to the agent's function.

### 5.1 `write_todos` content alias + JSON string deserialization

DeepSeek sometimes sends `content` instead of `todos`, and sometimes serializes the list as a JSON string. The patch:
1. Adds `content: str | list | None` to `WriteTodosInput`
2. Overrides `todos` to be optional (`list | None`)
3. `_normalize_todos()` falls back to `content` (parsing JSON strings) when `todos` is empty

### 5.2 `edit_file` no-op guard

Rejects `edit_file` calls where `old_string == new_string`, returning a `ToolMessage` error instead of letting the filesystem middleware loop.

### Note on `write_file`

In deepagents **v0.7.5**, `write_file` **always overwrites** — there is no `overwrite` parameter and no "file exists" error. The system prompt was updated accordingly (no more `overwrite=True` instructions).

---

## 6. Memory system

### 6.1 Tree layout

```
agent_fs/                          ← AGENT_FS_ROOT
├── memories/                      ← SHARED_MEMORY_ROOT (shared brain)
│   ├── lessons.md                 ← consolidated rules (max ~25 bullets)
│   ├── signals_log/               ← per-signal win-rate files
│   └── closed_trades/             ← legacy shared closed trades
├── skills/                        ← declarative skill instructions
└── users/<user>/memories/         ← per-user (git-ignored)
    ├── open_trades/               ← filled positions (type: filled)
    ├── pending_entries/           ← pending triggers (type: pending)
    ├── watchlist/                 ← candidates + rejects
    └── closed_trades/             ← resolved positions
```

### 6.2 File format

`YYYY-MM-DD--TICKER.md` with YAML frontmatter:
```yaml
---
symbol: NVDA
type: filled          # or: pending
entry_price: 110.50
entry_zone: 108.00 - 112.00
stop: 105.00
targets:
  - 120.00
  - 130.00
thesis: >
  ... rationale ...
signals_used: [composite_screening_top10, rsi_divergence]
conviction: MEDIUM
---
```

### 6.3 `active_memories_root`

`config.set_active_memories_root()` is set per-run (under `RUN_LOCK` by the webapp) so filesystem-side tools read the correct user's memory. Defaults to the shared brain for CLI usage.

---

## 7. Compliance check

Both the CLI (`finance_agent.py`) and webapp (`agent_service.py`) run a two-phase post-run check on scan queries:

- **Phase 1 — Carryover review**: verify every pre-existing open/pending trade was reviewed during the run.
- **Phase 2 — Symbol tracking**: verify every ticker that had a tool called on it got a memory file. Missing tickers get an auto-created reject entry.

The compliance check is the safety net for the agent forgetting to log a ticker.

---

## 8. Data caching

Three-tier cache (`tools.py`):

| Tier | Path | TTL |
|------|------|-----|
| Bulk OHLCV | `yf_data/combined_history.csv` | 24h |
| Per-symbol JSON | `yf_data/<TICKER>.json` | 24h |
| In-memory intraday | `yf_data/_intraday_cache.pkl` | 2h (saved via `_save_intraday_cache()`) |

---

## 9. Screening details (`tools.run_screening`)

Signature: `run_screening(mode: str = "full")` — `mode="fasset"` for the 44-ticker list, `"full"` for all 136.

Steps:
1. Get cooldown exclusions (recently stopped-out tickers)
2. Filter by fundamental quality gate (profit margins < -50% or no P/E → excluded)
3. Score each ticker on the weighted composite
4. Return top 10, sorted by completeness (≥50% weight first)

---

## 10. Configuration

All config lives in `config.py` and `.env`:

| Env var | Default | Purpose |
|---------|---------|---------|
| `OPENROUTER_API_KEY` | — | OpenRouter API key (required) |
| `MODEL_NAME` | `deepseek/deepseek-v4-pro` | LLM model |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | API base |
| `AGENT_FS_ROOT` | `agent_fs` | Memory tree root |
| `YF_CACHE_DIR` | `yf_data` | yfinance cache dir |
| `STOPOUT_COOLDOWN_DAYS` | `14` | Screening cooldown after stop-out |
| `RISK_FREE_RATE_ANNUAL` | `0.045` | For Sharpe/Sortino calcs |

### Watchlists

- `config.FASSET_WATCHLIST` — 44 curated tickers
- `config.EXPANDED_WATCHLIST` — 92 additional tickers
- `config.FULL_WATCHLIST` (= `config.WATCHLIST`) — 136 total
- `config.get_watchlist(mode)` — returns the right list for a scan mode

---

## 11. Running (CLI)

```powershell
# Run the agent once with a hardcoded query
python finance_agent.py
```

The query is hardcoded in `finance_agent.py` (line ~87). There is no CLI argument parsing.

---

## 12. Dependencies

`deepagents` (v0.7.5), `langchain-openai`, `langchain-anthropic`, `langchain-google-genai`, `yfinance`, `pandas`, `pandas-ta`, `python-dotenv`, `numpy`, `pydantic`.

There is **no** `pyproject.toml`, `requirements.txt`, or lockfile at the project root — dependencies are managed ad-hoc in `.venv/`.
