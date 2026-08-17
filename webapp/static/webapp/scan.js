/* Staff-only manual scan UI. Reuses the scan-stream SSE endpoint. */
(function () {
  "use strict";
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  let running = false;

  function log(text, cls) {
    const box = $("#scan-log");
    if (!box) return;
    const line = document.createElement("div");
    line.className = "font-mono text-xs py-1 " + (cls || "text-muted");
    line.textContent = text;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
  }

  function setDot(state) {
    const dot = $("#ticker-dot");
    if (dot) dot.className = "ticker-dot " + state;
  }

  function setStatus(text, state) {
    const s = $("#scan-status");
    if (s) s.textContent = text;
    setDot(state || "idle");
  }

  function setBusy(busy) {
    running = busy;
    $$(".scan-btn").forEach((b) => { b.disabled = busy; });
  }

  async function consumeSSE(url, onEvent) {
    const res = await fetch(url, { headers: { Accept: "text/event-stream" } });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) >= 0) {
        const frame = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        const line = frame.split("\n").find(l => l.startsWith("data: "));
        if (line) { try { onEvent(JSON.parse(line.slice(6))); } catch (_) {} }
      }
    }
  }

  function startScan(mode) {
    if (running) return;
    setBusy(true);
    $("#scan-log").innerHTML = "";
    setStatus("starting " + mode + " scan…", "busy");

    consumeSSE("/api/scan-stream?mode=" + mode, (ev) => {
      switch (ev.type) {
        case "status": log(ev.message, "text-ink"); break;
        case "node": log("· " + ev.name, "text-muted"); break;
        case "subagent": {
          const tkr = ev.args && ev.args.ticker ? " · " + ev.args.ticker : "";
          log("▸ " + (ev.name || "task") + tkr, "text-ink"); break;
        }
        case "compliance": log((ev.level === "warn" ? "⚠ " : "✓ ") + ev.message, ev.level === "warn" ? "text-stop" : "text-signal"); break;
        case "daily_signals": log("✓ generated " + ev.count + " signals", "text-signal"); break;
        case "error": log("✕ " + ev.message, "text-stop"); break;
        case "done": setStatus("done", "done"); setBusy(false); break;
      }
    }).catch((err) => {
      setStatus("error: " + err.message, "error");
      log("✕ " + err.message, "text-stop");
      setBusy(false);
    });
  }

  $$(".scan-btn").forEach((btn) => {
    btn.addEventListener("click", () => startScan(btn.dataset.mode));
  });
})();
