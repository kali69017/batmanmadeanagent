# AGENTS.md

## Project

Modular Python app (Fasset v2). A Deep Agents (LangGraph-based) finance analyst agent using `deepseek/deepseek-v4-flash` via OpenRouter.

## File Structure

```
config.py          ← WATCHLIST, model constants, .env loading
tools.py           ← 20 consolidated tool functions (13 agent-facing + 7 internal)
memory.py          ← MemoryManager: lessons, open/closed trades, signals_log, daily context
agents.py          ← Subagent definitions (TA, FA, Expert) + main agent builder
finance_agent.py   ← Entry point: stream runner + compliance check
.env               ← API keys and model config (git-ignored if repo exists)
agent_fs/memories/ ← Cross-session persistent memory
  lessons.md       ← Consolidated principles
  open_trades/     ← Current positions
  closed_trades/   ← Resolved positions
  watchlist/       ← Candidates + rejects
  signals_log/     ← Signal win-rate tracking
yf_data/           ← Cached yfinance data (companion scripts)
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

### Memory System (LLM-managed)
- `lessons.md` — consolidated ticker-agnostic principles (max ~25 bullets)
- `open_trades/` — YYYY-MM-DD--TICKER.md with YAML frontmatter
- `signals_log/` — per-signal win-rate tracking (e.g., rsi_divergence.md with triggered_correctly/triggered_falsely)
- Memory files use `write_file` with `overwrite=True` for updates

### Symbol Whitelist
`WATCHLIST` (44 tickers) enforced inside every tool via `_check_symbol()` — raises `ValueError` on out-of-list tickers. Tool layer is the real security boundary.

### yfinance Schema Drift
`get_news_headlines` handles shifting yfinance response schemas (content/nested dict fallbacks). yfinance changes frequently; news parsing may break on version updates.

## No tests, lint, CI

There are no tests, linter config, type checker, `requirements.txt`, or `pyproject.toml`. If adding tooling, pin runtime deps: `deepagents`, `langchain-openai`, `yfinance`, `pandas`, `pandas-ta`, `python-dotenv`, `numpy`.
