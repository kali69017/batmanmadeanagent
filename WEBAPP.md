# Fasset Webapp — Architecture & Reference

The Fasset webapp is a Django interface over the [agent engine](AGENT.md). It exposes the analyst through a browser terminal with three screens (Signals, Scan, Chat), persistent chat history, and a synced SQLite database. This document covers the webapp only — for the agent engine, see [AGENT.md](AGENT.md).

---

## 1. Project layout

```
manage.py                    ← Django CLI entry
fasset_web/                  ← Django project
├── settings.py              ← config (reads .env)
├── urls.py                  ← root URL conf
├── wsgi.py / asgi.py        ← servers
webapp/                      ← Django app
├── models.py                ← Trade, Lesson, SignalLog, ChatMessage, ChatSession, DailySignal, ScanRun
├── views.py                 ← HTTP + SSE endpoints
├── agent_service.py         ← threaded SSE runner, RUN_LOCK
├── streaming.py             ← SSE framing
├── memory_sync.py           ← memory tree → DB projection
├── learning.py              ← signal win-rate reinforcement
├── daily_signals.py         ← deterministic daily signal extraction
├── urls.py                  ← app URL conf
├── templates/webapp/        ← base.html, dashboard.html, login.html
├── static/webapp/           ← styles.css, app.js
└── management/commands/     ← import_memories, issue_token
```

---

## 2. Data model (`models.py`)

| Model | Purpose |
|-------|---------|
| `Trade` | A single trade/pick (open, pending, watchlist, closed). Unique per `(owner, kind, file_name)`. |
| `Lesson` | The shared learning brain (`lessons.md`), single row (pk=1). |
| `SignalLog` | Per-signal win-rate stats (`signals_log/*.md`). |
| `ChatMessage` | Durable per-user chat history, linked to a `ChatSession`. |
| `ChatSession` | A named conversation (title auto-derived from first message). |
| `DailySignal` | A clean daily trading signal (entry range, TP1/TP2, stop, reason). |
| `ScanRun` | Tracks when a scan ran and how many signals it generated. |

### Trade fields

`entry_price`, `entry_zone`, `stop_loss`, `exit_price`, `targets`, `horizon`, `risk_reward`, `direction`, `status`, `conviction`, `outcome`, `note`, `rationale`, `signals_used`, `return_realized_pct`, `raw`.

The `raw` field stores the full file content for the detail view.

---

## 3. Memory ↔ DB sync (`memory_sync.py`)

The **filesystem memory tree is the source of truth**. The agent writes files; the DB is a synced, queryable projection.

### 3.1 `parse_frontmatter(text)`

A defensive YAML-ish parser handling:
- Missing frontmatter (returns empty dict)
- Folded scalars (`key: >`), literal blocks (`key: |`), list items (`- item`)
- `null`/`true`/`false` values

### 3.2 Field mapping

The frontmatter uses different keys than the DB model. `_FIELD_MAP` translates:

| Frontmatter key | DB field |
|-----------------|----------|
| `symbol` / `ticker` | `ticker` |
| `stop` | `stop_loss` |
| `thesis` / `rejection_reason` | `rationale` |
| `entry_conditions` / `conditions_to_watch` | `note` |
| `horizon` | `horizon` |
| `risk_reward` | `risk_reward` |

Only truthy values are mapped (avoids later empty keys overwriting earlier populated ones).

### 3.3 `sync_all(username)`

Runs `sync_user_trades` + `sync_shared_lessons` + `sync_shared_signals`. Called after every run.

### 3.4 `load_positions(username)`

DB-backed read for the UI, grouped by kind (`open`, `pending`, `watchlist`, `closed`). Watchlist is deduped per-ticker (newest date wins). Optionally enriched with live prices from the yfinance cache via `_enrich_with_live_price()`.

---

## 4. Agent runner (`agent_service.py`)

### `AgentRunner`

Binds the agent to a logged-in user. Key responsibilities:
- Build the agent with the user's backend
- Run under a global `RUN_LOCK` (filesystem memory is not concurrency-safe)
- Set `config.active_memories_root` for the run
- Normalize LangGraph stream chunks into JSON-serializable SSE events
- Run post-run: `reinforce_learning()` → `sync_all()` → `generate_daily_signals()` (scan only)
- Run the two-phase compliance check

### `RUN_LOCK`

A process-level `threading.Lock` that serializes all runs. **Important limitation**: under a multi-process WSGI server (gunicorn `--workers N`), each process has its own lock, so concurrent scans across processes are still possible. For a single-process dev server this is fine.

### Chat history

`_store_turn()` persists each user/assistant message, capped at 10 turns (20 messages) per session. Chat sessions are auto-titled from the first message.

---

## 5. Streaming (`streaming.py`)

`sse_response(job)` wraps a callable as a `StreamingHttpResponse` with `text/event-stream`. A daemon thread runs the job; events are pushed to a queue and framed as `data: {json}\n\n`. On client disconnect (`GeneratorExit`), a `threading.Event` signals the worker to stop.

---

## 6. Views & API endpoints (`views.py` + `urls.py`)

### Pages
| URL | View | Notes |
|-----|------|-------|
| `/` / `/dashboard` | `dashboard` | `@login_required` |
| `/login` | `login_view` | token → session login |
| `/logout` | `logout_view` | POST only |

### API (all return JSON, auth via `@_require_auth` returning 401 JSON, not HTML redirect)
| URL | View | Purpose |
|-----|------|---------|
| `/api/positions` | `positions_view` | grouped positions |
| `/api/today-signals` | `today_signals_view` | today's daily signals + latest scan date |
| `/api/scan-stream?mode=full\|fasset` | `scan_stream` | SSE scan stream |
| `/api/chat-stream?q=...` | `chat_stream` | SSE chat stream |
| `/api/chat-sessions` | `chat_sessions_view` | list sessions |
| `/api/chat-sessions/<key>/messages` | `chat_session_detail` | session messages |
| `/api/chat-sessions/<key>/delete` | `chat_session_delete` | POST, delete session |
| `/api/new-chat` | `new_chat_session` | fresh session |
| `/api/reset-chat` | `reset_chat_view` | POST, clear current session |
| `/api/health` | `health_view` | health check |

---

## 7. Reinforcement learning (`learning.py`)

`reinforce_learning()` recomputes per-signal win rates from closed-trade outcomes after every run.

Attribution:
- A closed trade contributes to a signal only if `signals_used` lists it explicitly
- Win/loss decided from: `return_realized_pct` (≥0 → win) → outcome text (token-boundary regex matching) → exit vs entry price

The outcome-text matcher uses regex with `(?:^|_|\s)word(?:$|_|\s)` boundaries so `stop_loss_hit` correctly matches `loss`/`stop` without `hit` causing a false win.

---

## 8. Daily signals (`daily_signals.py`)

`generate_daily_signals(username)` extracts clean signals deterministically from the memory files (no LLM call — the data is already there):

- **Open positions** → `hold` signals
- **Pending entries** → `buy` signals

Each signal: ticker, direction, entry range (from `entry_zone`), TP1/TP2 (from `targets`), stop loss, and a reason (from `thesis`/`rationale`).

Called automatically after a scan completes. Results stored in `DailySignal` and `ScanRun` (for scan-date tracking).

---

## 9. Frontend

### 9.1 Design system (`static/webapp/styles.css`)

A self-contained CSS design system (no Tailwind CDN, no build step). Uses CSS custom properties for a cool clinical palette with full dark-mode support via `[data-theme="dark"]` and `prefers-color-scheme`.

Key tokens: `--bg`, `--surface`, `--card`, `--border`, `--text`, `--accent` (cyan-teal), `--positive`/`--negative` (semantic green/red). Mono-first typography (JetBrains Mono + Space Grotesk for display).

### 9.2 Application (`static/webapp/app.js`)

A single IIFE containing:
- Screen navigation (Signals / Scan / Chat)
- Markdown renderer for chat messages (headings, bold, tables, lists)
- Phase tracker + progress bar for scans
- Live ticker cards during deep-dive
- Positions table (sortable, clickable rows → detail view)
- Chat session management (list, load, delete, new)
- Daily signals rendering
- Theme toggle (persisted in `localStorage`)

### 9.3 Screens

1. **Signals** (default) — clean daily signals for non-technical users. Shows scan date, freshness warning, and simple cards with entry range, TP1/TP2, stop, and reason.
2. **Scan** — the full pipeline view with progress bar, phase panel, ticker cards, and the positions table.
3. **Chat** — markdown-rendered conversation with structured ticker cards.

---

## 10. Authentication

- **Login**: user pastes a DRF token; the view matches it to a `Token` and logs in the user (`django.contrib.auth.login`).
- **Token generation**: `python manage.py issue_token <username>` prints a token.
- **API auth**: `@_require_auth` returns `401 JSON` for unauthenticated requests (no HTML redirect, so `fetch` handles it cleanly).

---

## 11. Setup & running

```powershell
# First-time setup
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py import_memories <username>   # migrate legacy shared → per-user
.venv\Scripts\python.exe manage.py issue_token <username>        # print a login token

# Run
.venv\Scripts\python.exe manage.py runserver                     # http://127.0.0.1:8000
```

`.env` must contain:
- `OPENROUTER_API_KEY`
- `DJANGO_SECRET_KEY` (required — no fallback)
- `DJANGO_DEBUG=1` (for dev; default is `0`)
- `DJANGO_ALLOWED_HOSTS=*` (dev)

---

## 12. Migrations

`webapp/migrations/` tracks schema changes:
- `0001_initial` — Trade, Lesson, SignalLog, ChatMessage
- `0002_chat_sessions` — added ChatSession + ChatMessage.session
- `0003_extra_trade_fields` — added entry_zone, horizon, risk_reward
- `0004_daily_signals` — added DailySignal, ScanRun

---

## 13. Known limitations

- **`RUN_LOCK` is per-process** — not safe under multi-worker WSGI. Use a single process or add a distributed lock.
- **No tests, no CI, no linter config** — the project is developed ad-hoc.
- **Static files** — `DEBUG=True` is required for `runserver` to serve them. For production, set `STATIC_ROOT` and run `collectstatic`.
- **Live prices** come from the yfinance cache, which must be refreshed by running the companion `fetch_yfinance_data.py` script (not in the repo).
