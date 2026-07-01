/* Intelligent Interaction Layer — Frontend App */
"use strict";

const IDLE_WARN_MS   = 4 * 60 * 1000;
const IDLE_LOGOUT_MS = 5 * 60 * 1000;

let ws = null;
let info = null;
let currentModel = null;
let streamEl = null;
let streamRaw = "";
let pendingTags = null;
let idleWarn, idleOut, idleInterval;

// ── Markdown renderer ───────────────────────────────────────────────────────
function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function renderMd(raw) {
  const blocks = [];
  // Extract fenced code blocks
  let s = raw.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const i = blocks.length;
    blocks.push(`<pre><code>${esc(code.trim())}</code></pre>`);
    return `\x00B${i}\x00`;
  });
  // Extract inline code
  s = s.replace(/`([^`\n]+)`/g, (_, c) => {
    const i = blocks.length;
    blocks.push(`<code>${esc(c)}</code>`);
    return `\x00B${i}\x00`;
  });
  // Escape remaining text
  s = esc(s);
  // Block markdown
  s = s.replace(/^## (.+)$/gm,       '<div class="mh2">$1</div>');
  s = s.replace(/^### (.+)$/gm,      '<div class="mh3">$1</div>');
  s = s.replace(/^\*\* (.+)$/gm,     '<div class="mh3">$1</div>');
  s = s.replace(/^[\*\-] (.+)$/gm,   '<div class="mli">$1</div>');
  s = s.replace(/^\d+\.\s(.+)$/gm,   '<div class="mli">$1</div>');
  // Inline markdown
  s = s.replace(/\*\*(.+?)\*\*/g,    '<strong>$1</strong>');
  s = s.replace(/\*([^*\n]+?)\*/g,   '<em>$1</em>');
  // Line breaks
  s = s.replace(/\n\n/g, '<br><br>');
  s = s.replace(/\n/g,   '<br>');
  // Restore blocks
  s = s.replace(/\x00B(\d+)\x00/g, (_, i) => blocks[+i]);
  return s;
}

// ── Utilities ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

function show(id) { $(id).classList.remove("hidden"); }
function hide(id) { $(id).classList.add("hidden"); }

function scrollBottom() {
  const m = $("msgs");
  m.scrollTop = m.scrollHeight;
}

// ── Auth ─────────────────────────────────────────────────────────────────────
async function checkAuth() {
  try {
    const r = await fetch("/api/me");
    if (r.ok) { info = await r.json(); showChat(); }
    else showLogin();
  } catch { showLogin(); }
}

async function doLogin() {
  const btn = $("login-btn"), err = $("login-err");
  btn.disabled = true; btn.textContent = "Signing in…";
  err.classList.add("hidden");

  const form = new FormData();
  form.append("username", $("u").value.trim());
  form.append("password", $("p").value);

  const r = await fetch("/api/login", { method: "POST", body: form });
  if (r.ok) { info = null; await checkAuth(); }
  else {
    err.textContent = "Invalid username or password";
    err.classList.remove("hidden");
    btn.disabled = false; btn.textContent = "Sign In";
  }
}

async function doLogout() {
  clearIdle();
  await fetch("/api/logout", { method: "POST" });
  if (ws) { ws.close(); ws = null; }
  showLogin();
}

// ── Views ─────────────────────────────────────────────────────────────────────
function showLogin() {
  show("login-view"); hide("chat-view");
  $("u").value = ""; $("p").value = "";
  $("login-btn").disabled = false; $("login-btn").textContent = "Sign In";
  $("login-err").classList.add("hidden");
}

function showChat() {
  hide("login-view"); show("chat-view");
  stopLoginSlideshow();
  initChat();
}

// ── Chat init ─────────────────────────────────────────────────────────────────
function initChat() {
  // User chip
  $("user-chip").textContent = `${info.display_name} · ${info.role_label}`;

  // Model selector — always include the default so the control never renders blank
  const sel = $("model-sel");
  const opts = info.models.slice();
  if (info.default_model && !opts.includes(info.default_model)) {
    opts.unshift(info.default_model);
  }
  sel.innerHTML = opts.map(m => {
    const isDefault = m === info.default_model;
    return `<option value="${m}">${m}${isDefault ? " (default)" : ""}</option>`;
  }).join("");
  currentModel = info.default_model || opts[0];
  sel.value = currentModel;
  sel.onchange = () => {
    currentModel = sel.value;
    wsSend({ type: "model_change", model: currentModel });
  };

  // Service boxes
  const list = $("service-list");
  list.innerHTML = Object.entries(info.services).map(([id, label]) =>
    `<div class="svc" id="svc-${id}"><div class="svc-dot"></div><span>${label}</span></div>`
  ).join("");

  // Suggested questions
  $("qs-list").innerHTML = info.questions.map(q =>
    `<div class="q-chip" title="${esc(q)}">${esc(q.length > 55 ? q.slice(0, 54) + "…" : q)}</div>`
  ).join("");
  $("qs-list").querySelectorAll(".q-chip").forEach((chip, i) =>
    chip.addEventListener("click", () => submitText(info.questions[i]))
  );

  // Welcome hero (empty state)
  renderHero();

  connectWS();
  startIdle();
}

// ── Welcome hero ──────────────────────────────────────────────────────────────
function renderHero() {
  const org = info.organization ? ` · ${esc(info.organization)}` : "";
  const starters = (info.questions || []).slice(0, 4);
  const spark = `<svg width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"/></svg>`;
  const cards = starters.map((q, i) =>
    `<div class="hero-card" data-qi="${i}">
       <div class="hero-card-icon">${spark}</div>
       <span>${esc(q)}</span>
     </div>`
  ).join("");

  $("msgs").innerHTML = `
    <div class="chat-hero" id="chat-hero">
      <img src="/static/images/ce_logo.svg" class="hero-logo" alt="Intelligent Interaction Layer logo">
      <h1 class="hero-title">Welcome, <span>${esc(info.display_name)}</span></h1>
      <div class="hero-role">${esc(info.role_label)}${org}</div>
      <div class="hero-divider"></div>
      <p class="hero-sub">Your AI assistant for <strong>Circular Economy</strong> analysis —
         carbon footprint, circularity, and material reuse. Pick a starting point or type your own question.</p>
      <div class="hero-cards">${cards}</div>
    </div>`;

  $("msgs").querySelectorAll(".hero-card").forEach(el =>
    el.addEventListener("click", () => submitText(info.questions[+el.dataset.qi]))
  );

  // Hero already shows starters — hide the bottom suggestion bar to avoid duplication
  hide("qs-panel");
}

function removeHero() {
  const h = $("chat-hero");
  if (h) h.remove();
  show("qs-panel");
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
function connectWS() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws/chat`);

  ws.onmessage = e => handle(JSON.parse(e.data));

  ws.onclose = e => {
    if (e.code === 4001) { doLogout(); return; }
    setTimeout(connectWS, 2000);
  };
  ws.onerror = () => setTimeout(connectWS, 3000);
}

function wsSend(data) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(data));
}

// ── Server message handler ────────────────────────────────────────────────────
function handle(d) {
  switch (d.type) {
    case "services_reset":  resetSvcs(); break;
    case "thinking":        showThinking(); break;
    case "tool_start":      hideThinking(); setSvc(d.tool, "running"); addTag(d.label); break;
    case "tool_done":       setSvc(d.tool, "done"); break;
    case "tool_error":      setSvc(d.tool, "failed"); break;
    case "stream_start":    hideThinking(); startStream(); break;
    case "token":           appendToken(d.content); break;
    case "done":            finalStream(d.next_steps); enableInput(); break;
    case "warning":         hideThinking(); addWarning(d.content); enableInput(); break;
    case "error":           hideThinking(); addError(d.content); enableInput(); break;
    case "cleared":
      hideThinking();
      renderHero();
      resetSvcs();
      break;
  }
}

// ── Message helpers ───────────────────────────────────────────────────────────
function addSystem(text) {
  const div = document.createElement("div");
  div.className = "msg system";
  div.innerHTML = `<div class="bubble">${renderMd(text)}</div>`;
  $("msgs").appendChild(div);
  scrollBottom();
}

function addUser(text) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = `<div class="bubble">${esc(text).replace(/\n/g,"<br>")}</div>
    <div class="msg-time">${now()}</div>`;
  $("msgs").appendChild(div);
  scrollBottom();
}

function addTag(label) {
  if (!pendingTags) {
    pendingTags = document.createElement("div");
    pendingTags.className = "tool-tags";
  }
  const t = document.createElement("span");
  t.className = "tool-tag";
  t.innerHTML = `⚙ ${esc(label)}`;
  pendingTags.appendChild(t);
}

function startStream() {
  streamRaw = "";
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.id = "_stream";

  if (pendingTags) { div.appendChild(pendingTags); pendingTags = null; }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.id = "_sbubble";
  bubble.innerHTML = '<span class="cursor"></span>';
  div.appendChild(bubble);
  $("msgs").appendChild(div);
  streamEl = bubble;
  scrollBottom();
}

function appendToken(tok) {
  if (!streamEl) startStream();
  streamRaw += tok;
  streamEl.innerHTML = renderMd(streamRaw) + '<span class="cursor"></span>';
  scrollBottom();
}

function finalStream(steps) {
  if (!streamEl) return;
  let html = renderMd(streamRaw);
  if (steps && steps.length) {
    html += `<div class="next-steps">
      <div class="next-steps-title">Suggested Next Steps</div>
      ${steps.map(s =>
        `<div class="next-step-item" data-q="${esc(s)}">${esc(s)}</div>`
      ).join("")}
    </div>`;
  }
  streamEl.innerHTML = html;
  streamEl.querySelectorAll(".next-step-item").forEach(el =>
    el.addEventListener("click", () => submitText(el.dataset.q))
  );
  const meta = document.createElement("div");
  meta.className = "msg-time"; meta.textContent = now();
  streamEl.parentElement.appendChild(meta);
  streamEl.removeAttribute("id");
  streamEl = null; streamRaw = "";
  scrollBottom();
}

function addWarning(msg) {
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.innerHTML = `<div class="warn-bubble">⚠ ${esc(msg)}</div>`;
  $("msgs").appendChild(div); scrollBottom();
}

function addError(msg) {
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.innerHTML = `<div class="err-bubble">✗ ${esc(msg)}</div>`;
  $("msgs").appendChild(div); scrollBottom();
}

// ── Service boxes ─────────────────────────────────────────────────────────────
function resetSvcs() {
  document.querySelectorAll(".svc").forEach(el => el.className = "svc");
  pendingTags = null;
}

function setSvc(id, status) {
  const el = document.getElementById(`svc-${id}`);
  if (el) el.className = `svc ${status}`;
}

// ── Input ─────────────────────────────────────────────────────────────────────
function disableInput() {
  $("send-btn").disabled = true;
  $("input").disabled = true;
}

function enableInput() {
  $("send-btn").disabled = false;
  $("input").disabled = false;
  $("input").focus();
}

function submitText(text) {
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;
  removeHero();
  addUser(text);
  disableInput();
  resetSvcs();
  wsSend({ type: "message", content: text, model: currentModel });
  resetIdle();
}

function sendInput() {
  const val = $("input").value.trim();
  if (!val) return;
  $("input").value = "";
  $("input").style.height = "auto";
  submitText(val);
}

// ── Inactivity ────────────────────────────────────────────────────────────────
function startIdle() {
  ["mousemove","keypress","click","scroll","touchstart","pointerdown"].forEach(e =>
    document.addEventListener(e, resetIdle, { passive: true, capture: true })
  );
  resetIdle();
}

function resetIdle() {
  clearIdle();
  hide("idle-banner");
  idleWarn = setTimeout(warnIdle, IDLE_WARN_MS);
  idleOut  = setTimeout(doLogout, IDLE_LOGOUT_MS);
}

function warnIdle() {
  show("idle-banner");
  let s = 60; $("idle-count").textContent = s;
  idleInterval = setInterval(() => {
    s--; $("idle-count").textContent = s;
    if (s <= 0) clearInterval(idleInterval);
  }, 1000);
}

function clearIdle() {
  clearTimeout(idleWarn); clearTimeout(idleOut); clearInterval(idleInterval);
}

window.__ceStay = resetIdle;

// ── Theme ─────────────────────────────────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem("ce-theme") || "dark";
  setTheme(saved);
}

function setTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  localStorage.setItem("ce-theme", t);
  const isDark = t === "dark";
  $("theme-icon-dark")  && ($("theme-icon-dark").classList.toggle("hidden", !isDark));
  $("theme-icon-light") && ($("theme-icon-light").classList.toggle("hidden", isDark));
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute("data-theme") || "dark";
  setTheme(cur === "dark" ? "light" : "dark");
}

// ── Status polling ────────────────────────────────────────────────────────────
async function pollStatus() {
  try {
    const r = await fetch("/api/status");
    if (!r.ok) return;
    const s = await r.json();

    const tools = $("st-tools");
    if (tools) {
      tools.className = "status-row " + (s.mcp_ok ? "ok" : "err");
      tools.querySelector("span:last-child").textContent = s.mcp_ok
        ? `CE Tools (${s.mcp_tools} active)` : "CE Tools unavailable";
    }

    const ollama = $("st-ollama");
    if (ollama) {
      ollama.className = "status-row " + (s.ollama_ok ? "ok" : "err");
      ollama.querySelector("span:last-child").textContent = s.ollama_ok
        ? "Ollama connected" : "Ollama offline";
    }

    const mcp = $("st-mcp");
    if (mcp) {
      mcp.className = "status-row " + (s.mcp_server_ok ? "ok" : "err");
      mcp.querySelector("span:last-child").textContent = s.mcp_server_ok
        ? "MCP Server :8002 ready" : "MCP Server offline";
    }
  } catch { /* server not yet up */ }
}

// ── Thinking bubble ───────────────────────────────────────────────────────────
let thinkingEl = null;

function showThinking() {
  if (thinkingEl) return;
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.id = "_thinking";
  div.innerHTML = `<div class="thinking-bubble">
    <div class="thinking-dots"><span></span><span></span><span></span></div>
    Analyzing with CE tools…
  </div>`;
  $("msgs").appendChild(div);
  thinkingEl = div;
  scrollBottom();
}

function hideThinking() {
  if (thinkingEl) { thinkingEl.remove(); thinkingEl = null; }
}

// ── Login slideshow ───────────────────────────────────────────────────────────
let _loginSlide = 0;
let _loginTimer = null;

function setLoginSlide(idx) {
  const count = 2;
  _loginSlide = idx;
  for (let i = 0; i < count; i++) {
    const slide = document.getElementById(`lr-slide-${i}`);
    const dot   = document.getElementById(`lr-dot-${i}`);
    if (slide) slide.classList.toggle("active", i === idx);
    if (dot)   dot.classList.toggle("active", i === idx);
  }
}

function startLoginSlideshow() {
  if (!document.getElementById("lr-slide-0")) return;
  _loginTimer = setInterval(() => {
    setLoginSlide((_loginSlide + 1) % 2);
  }, 5000);
}

function stopLoginSlideshow() {
  clearInterval(_loginTimer);
}

// ── Topbar date & clock ───────────────────────────────────────────────────────
function startClock() {
  const timeEl = $("tb-time"), dateEl = $("tb-date");
  if (!timeEl || !dateEl) return;
  const tick = () => {
    const d = new Date();
    timeEl.textContent = d.toLocaleTimeString([], {
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false
    });
    dateEl.textContent = d.toLocaleDateString([], {
      weekday: "short", day: "2-digit", month: "short", year: "numeric"
    });
  };
  tick();
  setInterval(tick, 1000);
}

// ── Diagram lightbox ──────────────────────────────────────────────────────────
function openDiagram(src, title) {
  $("diagram-img").src   = src;
  $("diagram-title").textContent = title;
  $("diagram-modal").classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeDiagram() {
  $("diagram-modal").classList.add("hidden");
  document.body.style.overflow = "";
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  startLoginSlideshow();
  startClock();
  checkAuth();
  pollStatus();
  setInterval(pollStatus, 30000);

  // Close modal on Escape
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeDiagram();
  });

  // Login
  $("login-form").addEventListener("submit", e => { e.preventDefault(); doLogin(); });
  $("pw-toggle").addEventListener("click", () => {
    const p = $("p");
    p.type = p.type === "password" ? "text" : "password";
  });

  // Theme
  $("theme-btn") && $("theme-btn").addEventListener("click", toggleTheme);

  // Logout / clear
  $("logout-btn").addEventListener("click", doLogout);
  $("clear-btn").addEventListener("click", () => {
    wsSend({ type: "clear" }); resetSvcs();
  });

  // Send
  $("send-btn").addEventListener("click", sendInput);
  $("input").addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendInput(); }
  });
  $("input").addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.max(84, Math.min(this.scrollHeight, 240)) + "px";
  });
});
