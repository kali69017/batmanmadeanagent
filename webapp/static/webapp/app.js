/* ═══════════════════════════════════════════════════════════════════════════
   Reflex — Client-facing app
   Home (today's picks) / Portfolio / Pick detail / Ask.
   Clients see outcomes and reasoning, never the pipeline.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  };
  const fmtPrice = (v) => {
    if (v == null || v === "") return "–";
    const n = Number(v);
    return isNaN(n) ? String(v) : "$" + n.toFixed(2);
  };
  const fmtPct = (v) => {
    if (v == null || v === "") return "–";
    const n = Number(v);
    const sign = n > 0 ? "+" : "";
    return sign + n.toFixed(1) + "%";
  };
  const short = (s, n) => { s = String(s || ""); return s.length > n ? s.slice(0, n - 1) + "…" : s; };
  const getCookie = (name) => {
    const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? decodeURIComponent(m.pop()) : "";
  };

  // ── Company names (common tickers) ─────────────────────────────────────
  const COMPANY = {
    MSFT:"Microsoft", GOOG:"Alphabet", NVDA:"Nvidia", META:"Meta", ADBE:"Adobe",
    AMZN:"Amazon", AAPL:"Apple", AVGO:"Broadcom", TSLA:"Tesla", AMD:"AMD",
    V:"Visa", XOM:"Exxon Mobil", JNJ:"Johnson & Johnson", CAT:"Caterpillar",
    ABBV:"AbbVie", ARM:"Arm Holdings", PG:"Procter & Gamble", HD:"Home Depot",
    CVX:"Chevron", MRK:"Merck", AZN:"AstraZeneca", DELL:"Dell", IBM:"IBM",
    APH:"Amphenol", TJX:"TJX", ABT:"Abbott", UBER:"Uber", PFE:"Pfizer",
    PLD:"Prologis", CRM:"Salesforce", PH:"Parker Hannifin", SNOW:"Snowflake",
    NKE:"Nike", DAL:"Delta", RKLB:"Rocket Lab", RBLX:"Roblox", MSTR:"Strategy",
    RDDT:"Reddit", HUT:"Hut 8", RIOT:"Riot Platforms", HIMS:"Hims & Hers",
    MARA:"MARA", VEON:"Veon", SBET:"SharpLink", INTC:"Intel", QCOM:"Qualcomm",
    TXN:"Texas Instruments", MU:"Micron", LRCX:"Lam Research", AMAT:"Applied Materials",
    KLAC:"KLA", NOW:"ServiceNow", PANW:"Palo Alto Networks", CRWD:"CrowdStrike",
    WDAY:"Workday", DDOG:"Datadog", NET:"Cloudflare", PLTR:"Palantir", ZS:"Zscaler",
    TEAM:"Atlassian", MA:"Mastercard", PYPL:"PayPal", SQ:"Block", COIN:"Coinbase",
    HOOD:"Robinhood", JPM:"JPMorgan", BAC:"Bank of America", GS:"Goldman Sachs",
    MS:"Morgan Stanley", BLK:"BlackRock", SCHW:"Charles Schwab", C:"Citigroup",
    WFC:"Wells Fargo", LLY:"Eli Lilly", UNH:"UnitedHealth", BMY:"Bristol Myers",
    GILD:"Gilead", ISRG:"Intuitive Surgical", VRTX:"Vertex", REGN:"Regeneron",
    TMO:"Thermo Fisher", DHR:"Danaher", COP:"ConocoPhillips", SLB:"Schlumberger",
    EOG:"EOG Resources", MPC:"Marathon Petroleum", OXY:"Occidental", KMI:"Kinder Morgan",
    WMT:"Walmart", COST:"Costco", TGT:"Target", MCD:"McDonald's", SBUX:"Starbucks",
    LOW:"Lowe's", BKNG:"Booking Holdings", ORLY:"O'Reilly", BA:"Boeing", GE:"GE Aerospace",
    LMT:"Lockheed Martin", HON:"Honeywell", UNP:"Union Pacific", DE:"Deere",
    ETN:"Eaton", ITW:"Illinois Tool Works", NFLX:"Netflix", DIS:"Disney", T:"AT&T",
    VZ:"Verizon", TMUS:"T-Mobile", SPOT:"Spotify", F:"Ford", RIVN:"Rivian",
    FCX:"Freeport-McMoRan", NEM:"Newmont", DUK:"Duke Energy", SO:"Southern Co",
    NEE:"NextEra Energy", O:"Realty Income", SPG:"Simon Property", AMT:"American Tower",
    BABA:"Alibaba", JD:"JD.com", BAH:"Booz Allen", LULU:"Lululemon", DKNG:"DraftKings",
    CVNA:"Carvana", MRVL:"Marvell", ANET:"Arista Networks", SMCI:"Super Micro",
    BP:"BP", SHEL:"Shell", RTX:"RTX", NOC:"Northrop Grumman", KO:"Coca-Cola",
    PEP:"PepsiCo", NVS:"Novartis",
  };
  const companyName = (t) => COMPANY[t] || "";

  // ── Confidence badge ────────────────────────────────────────────────────
  function confidenceBadge(level) {
    const l = (level || "").toUpperCase();
    let cls = "med", label = "Medium";
    if (l === "HIGH") { cls = "high"; label = "High"; }
    else if (l === "LOW") { cls = "low"; label = "Low"; }
    return `<span class="conf-badge ${cls}">${label} confidence</span>`;
  }

  // ── Markdown renderer (for Ask) ────────────────────────────────────────
  function renderMarkdown(text) {
    if (!text) return "";
    let html = text;
    html = html.replace(/\n(\|.+\|)\n\|[-| :]+\|\n((?:\|.+\|\n?)+)/g, (_, h, r) => {
      const hcols = h.split("|").filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join("");
      const rows = r.trim().split("\n").map(row => `<tr>${row.split("|").filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join("")}</tr>`).join("");
      return `\n<div class="md-table-wrap"><table class="md-table"><thead><tr>${hcols}</tr></thead><tbody>${rows}</tbody></table></div>\n`;
    });
    html = html.replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2 class="md-h2">$1</h2>');
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/`([^`\n]+?)`/g, '<code class="md-code">$1</code>');
    html = html.replace(/^[*-] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul class="md-ul">$1</ul>');
    html = html.replace(/\n\n+/g, '</p><p class="md-p">');
    html = '<p class="md-p">' + html + '</p>';
    html = html.replace(/<p class="md-p"><\/p>/g, '');
    return html;
  }

  // ── Screen navigation ──────────────────────────────────────────────────
  const screens = { home: $("#screen-home"), portfolio: $("#screen-portfolio"), ask: $("#screen-ask"), pick: $("#screen-pick") };

  function switchScreen(name) {
    Object.keys(screens).forEach((k) => {
      screens[k].classList.toggle("hidden", k !== name);
      if (k === name) screens[k].classList.add("flex");
      else screens[k].classList.remove("flex");
    });
    $$(".rail-nav-btn, .mobile-nav-btn").forEach((btn) => {
      const active = btn.dataset.screen === name;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", String(active));
    });
    if (name === "portfolio") loadPortfolio();
    if (name === "ask") loadAskSuggestions();
  }

  $$(".rail-nav-btn, .mobile-nav-btn").forEach((btn) =>
    btn.addEventListener("click", () => switchScreen(btn.dataset.screen))
  );

  // ── Theme ──────────────────────────────────────────────────────────────
  const stored = localStorage.getItem("reflex-theme");
  if (stored === "dark") document.documentElement.setAttribute("data-theme", "dark");
  else if (stored === "light") document.documentElement.setAttribute("data-theme", "light");
  const themeBtn = $("#theme-toggle");
  if (themeBtn) themeBtn.addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme");
    if (cur === "dark") { document.documentElement.removeAttribute("data-theme"); localStorage.setItem("reflex-theme", "light"); }
    else { document.documentElement.setAttribute("data-theme", "dark"); localStorage.setItem("reflex-theme", "dark"); }
  });

  // ── Logout ─────────────────────────────────────────────────────────────
  const accountBtn = $("#account-btn");
  if (accountBtn) accountBtn.addEventListener("click", () => $("#logout-form").requestSubmit());

  // ═══════════════════════════════════════════════════════════════════════
  // HOME
  // ═══════════════════════════════════════════════════════════════════════
  async function loadHome() {
    try {
      const [signalsRes, portfolioRes] = await Promise.all([
        fetch("/api/today-signals"),
        fetch("/api/portfolio-summary"),
      ]);
      if (!signalsRes.ok || !portfolioRes.ok) throw new Error("load failed");
      const signalsData = await signalsRes.json();
      const portfolioData = await portfolioRes.json();

      renderUpdatedAt(signalsData);
      renderSnapshot(portfolioData);
      renderPicks(signalsData.signals || []);
    } catch (err) {
      console.error("loadHome failed:", err);
      $("#snapshot-line").textContent = "Couldn't load your portfolio.";
      $("#picks-empty").classList.remove("hidden");
      $("#picks-empty p").textContent = "Couldn't load today's picks.";
    }
  }

  function renderUpdatedAt(data) {
    const el = $("#updated-at");
    if (!el) return;
    const today = new Date().toISOString().slice(0, 10);
    const scanDate = data.scan_date || data.latest_scan;
    if (!scanDate) { el.textContent = ""; return; }
    if (scanDate === today) {
      el.textContent = "Updated today";
    } else {
      const d = new Date(scanDate + "T00:00:00");
      const days = Math.floor((new Date() - d) / (1000 * 60 * 60 * 24));
      el.textContent = days <= 1 ? "Updated yesterday" : "Last updated " + days + " days ago";
      el.style.color = "var(--warning)";
    }
  }

  function renderSnapshot(data) {
    const stats = data.stats || {};
    const pnl = stats.total_pnl_pct;
    $("#snapshot-count").textContent = stats.open_count != null ? stats.open_count : "–";
    $("#snapshot-winrate").textContent = stats.win_rate != null ? Math.round(stats.win_rate * 100) + "%" : "–";

    const pnlEl = $("#snapshot-pnl");
    if (pnl != null) {
      pnlEl.textContent = fmtPct(pnl);
      pnlEl.className = "snapshot-pnl " + (pnl >= 0 ? "pos" : "neg");
      $("#snapshot-line").textContent = pnl >= 0 ? "Your positions are up." : "Your positions are down.";
    } else {
      pnlEl.textContent = "—";
      pnlEl.className = "snapshot-pnl";
      $("#snapshot-line").textContent = "No open positions right now.";
    }
  }

  function renderPicks(signals) {
    const grid = $("#picks-grid");
    const empty = $("#picks-empty");
    if (!signals || !signals.length) {
      grid.classList.add("hidden");
      grid.innerHTML = "";
      empty.classList.remove("hidden");
      empty.querySelector("p").textContent = "No new picks today. Your active positions are unchanged.";
      return;
    }
    empty.classList.add("hidden");
    grid.classList.remove("hidden");
    grid.innerHTML = signals.map(s => buildPickCard(s)).join("");

    $$("#picks-grid .pick-card").forEach((card) => {
      card.addEventListener("click", () => showPickDetail(signals.find(s => s.ticker === card.dataset.ticker)));
    });
  }

  function buildPickCard(s) {
    const ticker = s.ticker || "?";
    const name = companyName(ticker);
    const isBuy = s.direction === "buy";
    const entry = (s.entry_low != null && s.entry_high != null)
      ? "$" + Number(s.entry_low).toFixed(2) + "–" + Number(s.entry_high).toFixed(2)
      : (s.entry_low != null ? "$" + Number(s.entry_low).toFixed(2) : "–");
    const why = short(s.reason || "", 110);

    return `
    <div class="pick-card" data-ticker="${ticker}">
      <div class="pick-card-header">
        <div>
          <span class="pick-ticker">${ticker}</span>
          ${name ? `<span class="pick-name">${name}</span>` : ""}
        </div>
        <span class="pick-badge ${isBuy ? "buy" : "hold"}">${isBuy ? "Buy" : "Hold"}</span>
      </div>
      <div class="pick-meta">
        <span>Buy range <strong>${entry}</strong></span>
      </div>
      ${why ? `<div class="pick-why">${why}</div>` : ""}
      <div class="pick-card-footer"><span class="text-xs text-muted">Tap for details →</span></div>
    </div>`;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // PICK DETAIL
  // ═══════════════════════════════════════════════════════════════════════
  let currentPick = null;

  function showPickDetail(pick) {
    if (!pick) return;
    currentPick = pick;
    const content = $("#pick-detail-content");
    const ticker = pick.ticker || "?";
    const name = companyName(ticker);
    const isBuy = pick.direction === "buy";

    content.innerHTML = `
      <div class="pick-detail-header">
        <div>
          <h1 class="pick-detail-ticker">${ticker}</h1>
          ${name ? `<span class="pick-detail-name">${name}</span>` : ""}
        </div>
        <span class="pick-badge ${isBuy ? "buy" : "hold"}">${isBuy ? "Buy" : "Hold"}</span>
      </div>

      ${pick.reason ? `<div class="pick-detail-block"><h3>Why we like this</h3><p>${short(pick.reason, 400)}</p></div>` : ""}

      <div class="pick-detail-block">
        <h3>The plan</h3>
        <div class="plan-grid">
          <div class="plan-cell"><div class="label">Buy range</div><div class="value">${pick.entry_low != null && pick.entry_high != null ? "$" + Number(pick.entry_low).toFixed(2) + " – $" + Number(pick.entry_high).toFixed(2) : "–"}</div></div>
          <div class="plan-cell"><div class="label">Target</div><div class="value">${pick.tp1 != null ? "$" + Number(pick.tp1).toFixed(2) + (pick.tp2 != null ? " / $" + Number(pick.tp2).toFixed(2) : "") : "–"}</div></div>
          <div class="plan-cell"><div class="label">Exit if it drops to</div><div class="value" style="color:var(--negative)">${pick.stop_loss != null ? "$" + Number(pick.stop_loss).toFixed(2) : "–"}</div></div>
        </div>
      </div>

      <button id="ask-about-pick" class="btn btn-primary">Ask about this pick</button>
    `;

    switchScreen("pick");

    const askBtn = $("#ask-about-pick");
    if (askBtn) askBtn.addEventListener("click", () => {
      switchScreen("ask");
      const input = $("#ask-input");
      if (input) { input.value = "Why is " + ticker + " a " + (isBuy ? "buy" : "hold") + "?"; input.focus(); }
    });
  }

  $("#pick-back").addEventListener("click", () => switchScreen("home"));

  // ═══════════════════════════════════════════════════════════════════════
  // PORTFOLIO
  // ═══════════════════════════════════════════════════════════════════════
  async function loadPortfolio() {
    try {
      const res = await fetch("/api/portfolio-summary");
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      renderPortfolio(data);
    } catch (err) {
      console.error("loadPortfolio failed:", err);
      $("#portfolio-content").innerHTML = `<div class="empty-state"><p class="text-muted">Couldn't load your portfolio.</p></div>`;
    }
  }

  function renderPortfolio(data) {
    const stats = data.stats || {};
    const container = $("#portfolio-content");
    let html = "";

    // Stats header
    html += `<div class="portfolio-stats">
      <div class="stat"><div class="label">Open</div><div class="value">${stats.open_count || 0}</div></div>
      <div class="stat"><div class="label">Waiting</div><div class="value">${stats.waiting_count || 0}</div></div>
      <div class="stat"><div class="label">Win rate</div><div class="value">${stats.win_rate != null ? Math.round(stats.win_rate * 100) + "%" : "–"}</div></div>
      <div class="stat"><div class="label">Avg return</div><div class="value">${stats.avg_return != null ? fmtPct(stats.avg_return) : "–"}</div></div>
    </div>`;

    // Active
    html += `<h2 class="section-heading">Active</h2>`;
    if (data.active && data.active.length) {
      html += `<div class="pos-list">`;
      data.active.forEach(a => {
        const pnl = a.pnl_pct;
        html += `<div class="pos-row" data-ticker="${a.ticker}">
          <div class="pos-ticker">${a.ticker} <span class="text-xs text-muted">${companyName(a.ticker)}</span></div>
          <div class="pos-prices">${fmtPrice(a.entry_price)} → ${fmtPrice(a.live_price)}</div>
          <div class="pos-pnl ${pnl >= 0 ? "pos" : "neg"}">${pnl != null ? fmtPct(pnl) : "–"}</div>
        </div>`;
      });
      html += `</div>`;
    } else {
      html += `<p class="text-sm text-muted mb-4">No active positions.</p>`;
    }

    // Waiting
    html += `<h2 class="section-heading">Waiting to trigger</h2>`;
    if (data.waiting && data.waiting.length) {
      html += `<div class="pos-list">`;
      data.waiting.forEach(w => {
        const zone = w.entry_low != null && w.entry_high != null ? "$" + Number(w.entry_low).toFixed(2) + " – $" + Number(w.entry_high).toFixed(2) : (w.entry_zone || "–");
        html += `<div class="pos-row" data-ticker="${w.ticker}">
          <div class="pos-ticker">${w.ticker} <span class="text-xs text-muted">${companyName(w.ticker)}</span></div>
          <div class="pos-prices">Buy range ${zone}</div>
          <div class="pos-pnl">waiting</div>
        </div>`;
      });
      html += `</div>`;
    } else {
      html += `<p class="text-sm text-muted mb-4">Nothing waiting to trigger.</p>`;
    }

    // Closed
    html += `<h2 class="section-heading">Closed</h2>`;
    if (data.closed && data.closed.length) {
      html += `<div class="pos-list">`;
      data.closed.slice(0, 10).forEach(c => {
        const ret = c.return_pct;
        const pnlCls = ret != null ? (ret >= 0 ? "pos" : "neg") : "";
        html += `<div class="pos-row">
          <div class="pos-ticker">${c.ticker} <span class="text-xs text-muted">${companyName(c.ticker)}</span></div>
          <div class="pos-prices">${short(c.outcome || "", 40)}</div>
          <div class="pos-pnl ${pnlCls}">${ret != null ? fmtPct(ret) : "–"}</div>
        </div>`;
      });
      html += `</div>`;
      if (data.closed.length > 10) html += `<p class="text-xs text-muted">…and ${data.closed.length - 10} more.</p>`;
    } else {
      html += `<p class="text-sm text-muted">No closed positions yet.</p>`;
    }

    container.innerHTML = html;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // ASK
  // ═══════════════════════════════════════════════════════════════════════
  const SUGGESTIONS = [
    "Why is NVDA a buy?",
    "What's my best performing pick this month?",
    "How is my portfolio doing?",
    "What should I watch this week?",
  ];

  function loadAskSuggestions() {
    const wrap = $("#ask-suggestions");
    if (!wrap || wrap.dataset.loaded) return;
    wrap.dataset.loaded = "1";
    wrap.innerHTML = SUGGESTIONS.map(s =>
      `<button class="suggestion-chip">${s}</button>`
    ).join("");
    $$("#ask-suggestions .suggestion-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const input = $("#ask-input");
        if (input) { input.value = chip.textContent; input.focus(); }
      });
    });
  }

  const askTranscript = $("#ask-transcript");
  const askInput = $("#ask-input");
  const askSend = $("#ask-send");

  function appendAsk(kind, text) {
    const empty = $("#ask-empty");
    if (empty && empty.parentNode === askTranscript) empty.remove();
    if (!askTranscript) return;
    if (kind === "user") {
      const wrap = el("div", "flex justify-end");
      wrap.appendChild(el("div", "chat-msg user fade-in-up", text));
      askTranscript.appendChild(wrap);
    } else if (kind === "agent") {
      const div = el("div", "chat-msg fade-in-up");
      div.innerHTML = renderMarkdown(text);
      askTranscript.appendChild(div);
    } else if (kind === "meta") {
      askTranscript.appendChild(el("div", "chat-msg meta fade-in-up", text));
    } else if (kind === "error") {
      askTranscript.appendChild(el("div", "chat-msg font-mono text-xs text-stop fade-in-up", "✕ " + text));
    }
    askTranscript.scrollTop = askTranscript.scrollHeight;
  }

  async function consumeSSE(url, onEvent) {
    const res = await fetch(url, { headers: { Accept: "text/event-stream" } });
    if (!res.ok) throw new Error("Request failed (HTTP " + res.status + ")");
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

  function setAskBusy(busy) {
    if (askSend) { askSend.disabled = busy; askSend.textContent = busy ? "Thinking…" : "Ask"; }
    if (askInput) askInput.disabled = busy;
  }

  async function sendAsk() {
    if (!askInput) return;
    const q = askInput.value.trim();
    if (!q || (askSend && askSend.disabled)) return;
    appendAsk("user", q);
    askInput.value = "";
    setAskBusy(true);
    try {
      await consumeSSE("/api/chat-stream?q=" + encodeURIComponent(q), (ev) => {
        if (ev.type === "response" && ev.content && ev.content.trim()) appendAsk("agent", ev.content.trim());
        else if (ev.type === "error") appendAsk("error", ev.message);
        else if (ev.type === "status") appendAsk("meta", "● " + ev.message);
      });
    } catch (err) {
      appendAsk("error", err.message);
    }
    setAskBusy(false);
    askInput.focus();
  }

  const askForm = $("#ask-form");
  if (askForm) askForm.addEventListener("submit", (e) => { e.preventDefault(); sendAsk(); });

  // ═══════════════════════════════════════════════════════════════════════
  // BOOT
  // ═══════════════════════════════════════════════════════════════════════
  switchScreen("home");
  loadHome();
})();
