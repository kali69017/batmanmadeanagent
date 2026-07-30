"""
Deep Agents Finance Analyst — Fasset v2

Modular architecture: config.py → tools.py → memory.py → agents.py → finance_agent.py

Run:
    python finance_agent.py
"""
import json
import io
import re
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import config
from agents import build_agent
from tools import _save_intraday_cache, get_technical_analysis, get_fundamentals
from tools import get_relative_strength, get_risk_adjusted_returns
from tools import get_quant_factors, get_insider_transactions
from tools import get_candlestick_patterns


if __name__ == "__main__":

    def _fmt_tool_args(args_str: str, width: int = 90) -> str:
        if not args_str:
            return ""
        try:
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
        except (json.JSONDecodeError, TypeError):
            args = args_str
        if isinstance(args, dict):
            lines = []
            for k, v in args.items():
                val = str(v)
                if len(val) > width - len(k) - 4:
                    val = val[:width - len(k) - 7] + "..."
                lines.append(f"    {k}: {val}")
            return "\n".join(lines)
        return f"    {args}"

    def _fmt_tool_result(content: str, width: int = 90) -> str:
        s = str(content)
        if len(s) > width:
            return s[:width - 3] + "..."
        return s

    def _print_divider(char="─", length=80):
        print(char * length)

    def _print_node_header(node_name: str):
        print(f"\n\033[1;36m{'='*80}\033[0m")
        print(f"\033[1;36m  NODE: {node_name}\033[0m")
        print(f"\033[1;36m{'='*80}\033[0m")

    def _print_thinking(text: str):
        thinking_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            print(f"\n\033[2;37m\u2764 THINKING:\033[0m")
            for line in thinking.split("\n"):
                print(f"  \033[2;37m{line}\033[0m")
            after = text[thinking_match.end():].strip()
            if after:
                print(f"\n\033[1;33m\u1F4DD RESPONSE:\033[0m")
                print(after)
        else:
            print(f"\n\033[1;33m\u1F4DD RESPONSE:\033[0m")
            print(text)

    def _print_tool_call(name: str, args: str):
        print(f"\n\033[1;32m\u1F527 TOOL CALL: {name}\033[0m")
        print(f"\033[2;32m{_fmt_tool_args(args)}\033[0m")

    def _print_tool_result(name: str, result: str):
        print(f"\n\033[1;35m\u1F4E6 TOOL RESULT [{name}]:\033[0m")
        print(f"\033[2;35m{_fmt_tool_result(result)}\033[0m")

    def _print_subagent(name: str, action: str):
        print(f"\n\033[1;33m\u1F916 SUB-AGENT [{name}]: {action}\033[0m")



    query = (
        "Scan the full market now and suggest me good trade ideas with entry zone, target price and stoploss price as well."
    )

    '''query = (
        "Scan the watchlist and tell me if any stocks are worth buying right now. "
        "If you find good trade ideas, give me the top ones with entry zones, "
        "stop losses, targets, and rationale. If no stocks are good to buy now, "
        "just suggest the best candidates as watchlist items with the condition "
        "that needs to be met before entry."
    )'''

    is_scan_query = any(kw in query.lower() for kw in ["scan", "screen", "rank", "best", "top", "suggest", "watchlist", "market leaders"])

    mem = config.AGENT_FS_ROOT / "memories"
    _pre_run_open: set[str] = set()
    open_dir = mem / "open_trades"
    pending_dir = mem / "pending_entries"
    watch_dir = mem / "watchlist"
    closed_dir = mem / "closed_trades"
    if open_dir.is_dir():
        _pre_run_open = {f.stem for f in open_dir.glob("*.md")}
    if pending_dir.is_dir():
        _pre_run_open |= {f.stem for f in pending_dir.glob("*.md")}
    _written_memory_files: set[str] = set()
    _reviewed_trade_files: set[str] = set()
    _tool_called_symbols: set[str] = set()

    TOOLS_THAT_TAKE_SYMBOL = {
        "get_price_data", "get_technical_analysis", "get_fundamentals",
        "get_relative_strength", "get_risk_adjusted_returns",
        "get_momentum_indicators", "get_trend_indicators",
        "get_volatility_indicators", "get_volume_indicators",
        "get_pivot_points", "get_quant_factors",
        "get_insider_transactions", "get_candlestick_patterns",
    }

    print(f"\n\033[1;37m{'='*80}\033[0m")
    print(f"\033[1;37m  FASST V2 — FASSET PORTFOLIO ANALYST\033[0m")
    print(f"\033[1;37m  Model: {config.MODEL_NAME}\033[0m")
    print(f"\033[1;37m  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\033[0m")
    print(f"\033[1;37m{'='*80}\033[0m")
    print(f"\033[1;37m  QUERY: {query}\033[0m")
    print(f"\033[1;37m{'='*80}\033[0m")

    agent, backend = build_agent()

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        stream_mode="updates",
        subgraphs=True,
    ):
        if isinstance(chunk, tuple) and len(chunk) == 2:
            namespace, updates = chunk
            ns_str = " > ".join(str(n) for n in namespace) if namespace else "main"
            print(f"\n\033[1;33m\u1F4C2 NAMESPACE: {ns_str}\033[0m")
        else:
            updates = chunk

        if not isinstance(updates, dict):
            continue

        for node_name, node_output in updates.items():
            _print_node_header(node_name)

            if isinstance(node_output, dict):
                messages = node_output.get("messages", [])
                if messages:
                    for msg in messages:
                        msg_type = type(msg).__name__
                        if hasattr(msg, "type"):
                            msg_type = msg.type

                        if msg_type == "ai":
                            content = msg.content if hasattr(msg, "content") else str(msg)
                            tool_calls = msg.tool_calls if hasattr(msg, "tool_calls") else []

                            if content:
                                _print_thinking(content)

                            for tc in tool_calls:
                                func_name = tc.get("name", "?") if isinstance(tc, dict) else getattr(tc, "name", "?")
                                func_args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
                                if func_name in TOOLS_THAT_TAKE_SYMBOL:
                                    sym = func_args.get("symbol") if isinstance(func_args, dict) else None
                                    if sym:
                                        _tool_called_symbols.add(sym)
                                if func_name in ("write_file", "edit_file") and isinstance(func_args, dict):
                                    fp = func_args.get("file_path", "")
                                    if "/memories/" in fp:
                                        _written_memory_files.add(fp)
                                if func_name == "read_file" and isinstance(func_args, dict):
                                    fp = func_args.get("file_path", "")
                                    if "/memories/open_trades/" in fp:
                                        _reviewed_trade_files.add(fp)
                                _print_tool_call(func_name, json.dumps(func_args, indent=2) if isinstance(func_args, dict) else str(func_args))

                        elif msg_type == "tool":
                            content = msg.content if hasattr(msg, "content") else str(msg)
                            name = msg.name if hasattr(msg, "name") else "?"
                            _print_tool_result(name, content)

                        elif msg_type == "human":
                            content = msg.content if hasattr(msg, "content") else str(msg)
                            print(f"\n\033[1;34m\u1F464 USER:\033[0m {content}")

                        else:
                            print(f"\n\033[2;37m[{msg_type}]\033[0m {str(msg)[:200]}")

                for k, v in node_output.items():
                    if k == "messages":
                        continue
                    v_str = str(v)
                    if len(v_str) > 200:
                        v_str = v_str[:200] + "..."
                    print(f"\n\033[2;37m  {k}: {v_str}\033[0m")

            elif isinstance(node_output, list):
                for item in node_output:
                    if hasattr(item, "type"):
                        print(f"\n\033[2;37m  [{item.type}] {str(item)[:200]}\033[0m")
                    else:
                        print(f"\n\033[2;37m  {str(item)[:200]}\033[0m")
            else:
                print(f"\n\033[2;37m  {str(node_output)[:300]}\033[0m")

    _save_intraday_cache()

    print(f"\n\033[1;37m{'='*80}\033[0m")
    print(f"\033[1;37m  FINAL ANSWER\033[0m")
    print(f"\033[1;37m{'='*80}\033[0m")

    # Compliance check
    print(f"\n\033[1;33m{'='*80}\033[0m")
    print(f"\033[1;33m  POST-RUN COMPLIANCE CHECK\033[0m")
    print(f"\033[1;33m{'='*80}\033[0m")

    if is_scan_query:
        reviewed = set()
        for fp in _written_memory_files:
            if fp.startswith("/memories/open_trades/") or fp.startswith("/memories/pending_entries/"):
                reviewed.add(Path(fp).stem)
        for fp in _reviewed_trade_files:
            if fp.startswith("/memories/open_trades/") or fp.startswith("/memories/pending_entries/"):
                reviewed.add(Path(fp).stem)
        unresolved = _pre_run_open - reviewed
        if unresolved:
            print(f"  \033[1;33m\u26A0 Phase 1: {len(unresolved)} open trade(s) were not written during this run:\033[0m")
            for s in sorted(unresolved):
                print(f"    - {s}")
        else:
            n_reviewed = len(_pre_run_open)
            if n_reviewed:
                print(f"  \033[1;32m\u2705 Phase 1 OK: All {n_reviewed} carryover open trade(s) reviewed.\033[0m")
            else:
                print(f"  \033[1;32m\u2705 Phase 1 OK: No carryover open trades.\033[0m")

    if is_scan_query and _tool_called_symbols:
        tracked_syms: set[str] = set()
        for fp in _written_memory_files:
            p = Path(fp)
            parts = p.stem.split("--")
            ticker = (parts[-1] if len(parts) > 1 else parts[0]).upper()
            if ticker in config.WATCHLIST:
                tracked_syms.add(ticker)
        for d, exists in [(open_dir, open_dir and open_dir.is_dir()),
                          (pending_dir, pending_dir and pending_dir.is_dir()),
                          (watch_dir, watch_dir and watch_dir.is_dir()),
                          (closed_dir, closed_dir and closed_dir.is_dir())]:
            if exists:
                for f in d.glob("*.md"):
                    parts = f.stem.split("--")
                    ticker = (parts[-1] if len(parts) > 1 else parts[0]).upper()
                    if ticker in config.WATCHLIST:
                        tracked_syms.add(ticker)
        missing = _tool_called_symbols - tracked_syms
        if missing:
            print(f"  \033[1;31m\u26A0 Scan compliance: {len(missing)} analyzed symbol(s) have no entry:\033[0m")
            for s in sorted(missing):
                print(f"    - {s}")
            today = datetime.now().strftime("%Y-%m-%d")
            for s in sorted(missing):
                fp = Path(str(watch_dir)) / f"{s}.md"
                body = (
                    f"---\n"
                    f"date: {today}\n"
                    f"ticker: {s}\n"
                    f"direction: reject\n"
                    f"entry_price: null\n"
                    f"exit_price: null\n"
                    f"rationale: >\n"
                    f"  Auto-logged by compliance check.\n"
                    f"signals_used: []\n"
                    f"outcome: completed\n"
                    f"return_realized_pct: null\n"
                    f"lessons: >\n"
                    f"  Agent oversight: analyzed but did not log.\n"
                    f"---\n"
                )
                fp.write_text(body, encoding="utf-8")
                print(f"    \u2192 Created watchlist/reject entry for {s}")
        else:
            print(f"  \033[1;32m\u2705 Scan compliance OK: All {len(_tool_called_symbols)} analyzed symbols tracked.\033[0m")

    print(f"\n\033[2;37m(Compliance check complete)\033[0m")
