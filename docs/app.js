// Minisceongo Creek bank erosion explainer: animation player + project assistant (RAG over the project notes).

const WEBLLM_URL = "https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.85/+esm";
const MODELS = [
  { id: "Qwen3.5-9B-q4f16_1-MLC", name: "Qwen3.5 9B", tag: "best answers", size: "4.7 GB", vram: "about 6.5 GB", thinking: true },
  { id: "Qwen3.5-4B-q4f16_1-MLC", name: "Qwen3.5 4B", tag: "balanced", size: "2.2 GB", vram: "about 4 GB", thinking: true },
  { id: "Qwen3.5-2B-q4f16_1-MLC", name: "Qwen3.5 2B", tag: "light", size: "1.0 GB", vram: "about 2.3 GB", thinking: true },
  { id: "Llama-3.1-8B-Instruct-q4f16_1-MLC", name: "Llama 3.1 8B", tag: "alternative", size: "4.2 GB", vram: "about 5 GB", thinking: false },
  { id: "Llama-3.2-3B-Instruct-q4f16_1-MLC", name: "Llama 3.2 3B", tag: "light", size: "1.7 GB", vram: "about 2.3 GB", thinking: false },
];
// Models for "On this computer": installed once through Ollama (free, open source) and kept on the PC, not in the browser.
// size = download size; requires = oldest Ollama version that runs the model with thinking switched off.
const LOCAL_MODELS = [
  { id: "qwen3.5:9b", name: "Qwen3.5 9B", tag: "best answers", size: "6.6 GB", ram: "16 GB", requires: "0.17.1" },
  { id: "qwen3.5:4b", name: "Qwen3.5 4B", tag: "lighter and faster", size: "3.4 GB", ram: "8 GB", requires: "0.17.1" },
  { id: "qwen3:8b", name: "Qwen3 8B", tag: "for older Ollama versions", size: "5.2 GB", ram: "16 GB", requires: "0.9.0" },
];
const OLLAMA = "http://127.0.0.1:11434";
const SETUP_FILE = "setup/Install_Local_AI.bat";
const SETUP_SOURCE = "https://github.com/Faisal-B-Ashraf/minisceongo-creek-erosion/blob/main/docs/setup/Install_Local_AI.bat";
const SUGGEST = [
  ["What is the short answer?", "Why only the south bank?", "What data did the study use?"],
  ["Why use 40-ft squares?", "What does the fit score measure?", "Why not match trees or the creek?", "Why take the middle value?"],
  ["How is the red score worked out?", "Why average several years?", "Why was the 2004 photo left out?"],
  ["Why doesn't the line go through dark roofs?", "How does the cheapest path work?", "Is the centreline the deepest point?"],
  ["Why a station every 10 ft?", "What are the five sections of the M?", "How long are the cross lines?"],
  ["What is lidar?", "Why was the 2011 survey 6.7 ft off?", "How were the two surveys lined up?", "What does the hillside wave mean?"],
  ["What is a DEM?", "Why is there no data under the water?", "Why not merge the two surveys?"],
  ["How is the bank face found?", "Why measure at three heights?", "What is the error limit?"],
  ["Which stations really moved?", "What does 'set back' mean?", "What do the blue bars mean?"],
  ["Why is the bank eroding at stations 72 to 75?", "How fast is it moving?", "What should happen next?"],
];
const BUDGET = { browser: 1300, local: 1800, server: 2600, notes: 700 };   // words of project notes per question
const CTX_TOKENS = { browser: 3300, local: 7000 };                         // context windows: 4,096 (browser), 8,192 (Ollama)

const $ = (id) => document.getElementById(id);
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// ================================================================================================ player
let MAN = null, FR = [], STARTS = [], CUM = [], TOTAL = 0;
let cur = 0, playing = !reduceMotion, timer = null, speed = 1, lastStep = -1;
const images = new Map();

function loadImage(idx) {
  if (images.has(idx)) return images.get(idx);
  const p = new Promise((resolve) => {
    const im = new Image();
    im.onload = () => resolve(im);
    im.onerror = () => resolve(null);
    im.src = "frames/" + FR[idx].f;
  });
  images.set(idx, p);
  return p;
}

async function preloadAll() {
  const order = [];
  for (let k = 0; k < FR.length; k++) order.push(k);
  let next = 0;
  const worker = async () => { while (next < order.length) { await loadImage(order[next++]); } };
  await Promise.all([worker(), worker(), worker(), worker()]);
}

function stepOf(idx) { return FR[idx].k; }

function renderPlayer() {
  const f = FR[cur], k = f.k;
  $("frame").src = "frames/" + f.f;
  $("frame").alt = MAN.captions[f.c];
  $("caption").textContent = MAN.captions[f.c];
  $("stepNo").textContent = `Step ${k + 1} of ${MAN.steps.length}`;
  $("stepTitle").textContent = MAN.steps[k];
  const pct = 100 * (CUM[cur] + f.d) / TOTAL;
  $("fill").style.width = pct + "%";
  $("bar").setAttribute("aria-valuenow", String(Math.round(pct)));
  $("playBtn").textContent = playing ? "Pause" : "Play";
  if (k !== lastStep) {
    lastStep = k;
    [...$("steps").querySelectorAll("button")].forEach((b, j) => {
      if (j === k) b.setAttribute("aria-current", "step"); else b.removeAttribute("aria-current");
    });
    $("ctxStep").textContent = `Step ${k + 1} · ${MAN.steps[k]}`;
    renderSuggestions(k);
  }
}

async function show(idx) {
  cur = Math.max(0, Math.min(FR.length - 1, idx));
  await loadImage(cur);
  renderPlayer();
}

function schedule() {
  clearTimeout(timer);
  if (playing) timer = setTimeout(tick, FR[cur].d / speed);
}

async function tick() {
  if (cur >= FR.length - 1) { playing = false; renderPlayer(); return; }
  await loadImage(cur + 1);
  if (!playing) return;
  await show(cur + 1);
  schedule();
}

async function go(idx) { await show(idx); schedule(); }
function pause() { playing = false; clearTimeout(timer); renderPlayer(); }
function togglePlay() {
  if (!playing && cur >= FR.length - 1) cur = 0;
  playing = !playing;
  go(cur);
}
function nextStep() { const k = stepOf(cur); if (k < MAN.steps.length - 1) go(STARTS[k + 1]); }
function prevStep() { const k = stepOf(cur); go(cur - STARTS[k] > 2 || k === 0 ? STARTS[k] : STARTS[k - 1]); }

async function initPlayer() {
  MAN = await (await fetch("frames.json")).json();
  FR = MAN.frames;
  let acc = 0;
  for (const f of FR) { CUM.push(acc); acc += f.d; }
  TOTAL = acc;
  STARTS = MAN.steps.map((_, k) => FR.findIndex((f) => f.k === k));
  const ol = $("steps");
  MAN.steps.forEach((s, k) => {
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.type = "button";
    b.innerHTML = `<span class="n">${k + 1}</span>`;
    b.append(document.createTextNode(s));
    b.addEventListener("click", () => go(STARTS[k]));
    li.append(b); ol.append(li);
    const m = document.createElement("div");
    m.className = "mark"; m.style.left = (100 * CUM[STARTS[k]] / TOTAL) + "%";
    $("bar").append(m);
  });
  $("playBtn").addEventListener("click", togglePlay);
  $("nextBtn").addEventListener("click", nextStep);
  $("backBtn").addEventListener("click", prevStep);
  $("restartBtn").addEventListener("click", () => { playing = true; go(0); });
  $("speedSel").addEventListener("change", (e) => { speed = parseFloat(e.target.value); schedule(); });
  const seek = (clientX) => {
    const r = $("bar").getBoundingClientRect();
    const t = Math.max(0, Math.min(1, (clientX - r.left) / r.width)) * TOTAL;
    const n = CUM.findIndex((c, j) => c + FR[j].d > t);
    go(n < 0 ? FR.length - 1 : n);
  };
  $("bar").addEventListener("click", (e) => seek(e.clientX));
  $("bar").addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") { e.preventDefault(); go(cur + 1); }
    if (e.key === "ArrowLeft") { e.preventDefault(); go(cur - 1); }
  });
  document.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, select, button, [contenteditable], .bar, summary")) return;
    if (e.code === "Space") { e.preventDefault(); togglePlay(); }
    else if (e.code === "ArrowRight") { nextStep(); }
    else if (e.code === "ArrowLeft") { prevStep(); }
  });
  await Promise.all(FR.slice(0, STARTS[1]).map((_, j) => loadImage(j)));
  await go(0);
  preloadAll();
}

// ================================================================================================ notes search (BM25)
const STOP = new Set(("a an the and or but if of to in on at by for with from as is are was were be been being it its this that " +
  "these those there here what which who whom why how when where do does did doing can could would should will shall may might " +
  "must i you we they he she them our your my me us about into over under than then so such not no yes also just only very " +
  "much many more most some any each every all both between within without per via up down out off again once same other own").split(" "));
const SYN = {
  rectangle: "square", rectangles: "squares", box: "square", boxes: "squares", window: "square", windows: "squares",
  laser: "lidar", lasers: "lidar", centerline: "centreline", center: "centre", centers: "centres", color: "colour",
  colors: "colours", gray: "grey", eroding: "erosion", eroded: "erosion", erode: "erosion", meter: "metre",
  meters: "metres", dtm: "dem",
};

// Light suffix stripping, applied the same way to the notes and the question ("squares"/"square", "moved"/"move").
function stem(w) {
  if (/^\d/.test(w)) return w;
  if (w.length > 5 && w.endsWith("ing")) w = w.slice(0, -3);
  else if (w.length > 4 && (w.endsWith("ies") || w.endsWith("ied"))) w = w.slice(0, -3) + "y";
  else if (w.length > 4 && w.endsWith("ed")) w = w.slice(0, -2);
  else if (w.length > 4 && /(ss|x|z|ch|sh)es$/.test(w)) w = w.slice(0, -2);
  else if (w.length > 3 && w.endsWith("s") && !/(ss|us|is)$/.test(w)) w = w.slice(0, -1);
  if (w.length >= 4 && w.endsWith("e")) w = w.slice(0, -1);
  return w;
}

function tokens(text, expand = false) {
  const out = [];
  for (let w of text.toLowerCase().split(/[^a-z0-9.\-]+/)) {
    w = w.replace(/^[.\-]+|[.\-]+$/g, "");
    if (!w || STOP.has(w)) continue;
    if (expand && SYN[w]) out.push(stem(SYN[w]));
    out.push(stem(w));
    if (w.includes("-")) for (const p of w.split("-")) if (p && !STOP.has(p)) out.push(stem(p));
  }
  return out;
}

let CHUNKS = [], DF = new Map(), AVGDL = 1;
function buildIndex(chunks) {
  CHUNKS = chunks.map((c) => {
    const toks = tokens(c.title + " " + c.title + " " + c.text);
    const tf = new Map();
    for (const t of toks) tf.set(t, (tf.get(t) || 0) + 1);
    for (const t of tf.keys()) DF.set(t, (DF.get(t) || 0) + 1);
    return { ...c, tf, len: toks.length, words: c.text.split(/\s+/).length };
  });
  AVGDL = CHUNKS.reduce((s, c) => s + c.len, 0) / CHUNKS.length;
}

// Station numbers named in a question: "station 74", "stations 72 to 75".
function stationsIn(query) {
  const out = new Set();
  const re = /\bstations?\s+(\d{1,3})(?:\s*(?:to|-|–|and|through)\s*(\d{1,3}))?/gi;
  let m;
  while ((m = re.exec(query))) {
    const a = +m[1], b = m[2] ? +m[2] : a;
    if (a > 127) continue;
    if (b >= a && b <= 127 && b - a <= 12) for (let n = a; n <= b; n++) out.add(n);
    else out.add(a);
  }
  return [...out];
}
const mentions = (c, n) => c.text.includes(`Station ${n} (`) || c.title.includes(`Station ${n} `);

function search(query, step, budget) {
  const q = [...new Set(tokens(query, true))];
  const st = stationsIn(query);
  const N = CHUNKS.length, k1 = 1.2, b = 0.75;
  const scored = CHUNKS.map((c) => {
    let s = 0;
    for (const t of q) {
      const f = c.tf.get(t);
      if (!f) continue;
      const idf = Math.log(1 + (N - DF.get(t) + 0.5) / (DF.get(t) + 0.5));
      s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * c.len / AVGDL));
    }
    if (s > 0 && c.steps.includes(step)) s *= 1.35;
    for (const n of st) if (mentions(c, n)) s += 50;          // the station's own line always comes first
    return { c, s };
  }).sort((a, b2) => b2.s - a.s);
  let picked = scored.filter((x) => x.s > 0).slice(0, 8);
  if (!picked.length) picked = CHUNKS.filter((c) => c.steps.includes(step)).slice(0, 3).map((c) => ({ c, s: 0 }));
  const out = [];
  let words = 0;
  for (let { c } of picked) {
    // per-station tables: keep only the lines for the stations asked about
    if (st.length && c.title.startsWith("Per-station results")) {
      const lines = c.text.split("\n").filter((l) => st.some((n) => l.includes(`Station ${n} (`)));
      if (lines.length) c = { ...c, text: lines.join("\n"), words: lines.join(" ").split(/\s+/).length };
    }
    if (out.length && words + c.words > budget) continue;
    out.push(c); words += c.words;
    if (out.length >= 6) break;
  }
  return out;
}

// ================================================================================================ assistant
let mode = "notes";              // notes | local | browser | server
let engine = null, webllm = null, activeModel = null;
let local = null;                // { id, name, think, warm }: the model in use through Ollama on this computer
let server = null;               // { url, model }
let history = [];                // [{role, content}] of earlier exchanges (model modes only)
let busy = false, stopFlag = false, abortCtl = null;

const store = {                  // remembers the reader's model on this computer (private windows may refuse)
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* not kept */ } },
};

function esc(s) { return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function inline(s) { return s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>"); }
// Join hard-wrapped lines: a line that does not start a list item continues the line before it.
function unwrap(text) {
  const out = [];
  for (const line of text.split("\n")) {
    const t = line.trim();
    if (!t) { out.push(""); continue; }
    const item = /^([-*•]|\d+[.)])\s+/.test(t);
    if (!item && out.length && out[out.length - 1] !== "") out[out.length - 1] += " " + t;
    else out.push(t);
  }
  return out.join("\n");
}
function md(text) {
  let html = "", list = null;
  for (const raw of esc(unwrap(text)).split("\n")) {
    const line = raw.trimEnd();
    const ub = line.match(/^\s*[-*•]\s+(.*)/), nb = line.match(/^\s*\d+[.)]\s+(.*)/);
    if (ub || nb) {
      const t = ub ? "ul" : "ol";
      if (list !== t) { if (list) html += `</${list}>`; html += `<${t}>`; list = t; }
      html += `<li>${inline((ub || nb)[1])}</li>`;
      continue;
    }
    if (list) { html += `</${list}>`; list = null; }
    if (line.trim()) html += `<p>${inline(line)}</p>`;
  }
  if (list) html += `</${list}>`;
  return html;
}
function stripThink(t) { return t.replace(/<think>[\s\S]*?(<\/think>|$)/g, "").replace(/^\s+/, ""); }

function addMsg(cls, html) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  d.innerHTML = html;
  $("messages").append(d);
  $("messages").scrollTop = $("messages").scrollHeight;
  return d;
}

function sourcesHtml(hits) {
  const items = hits.map((c) => {
    const t = unwrap(c.text);
    return `<li><b>${esc(c.title)}</b><span>${esc(t.length > 420 ? t.slice(0, 420) + "…" : t)}</span></li>`;
  }).join("");
  return `<details class="sources"><summary>Sources from the project notes (${hits.length})</summary><ol>${items}</ol></details>`;
}

function renderSuggestions(step) {
  const box = $("suggest");
  box.textContent = "";
  for (const q of SUGGEST[step] || []) {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = q;
    b.addEventListener("click", () => ask(q));
    box.append(b);
  }
}

function setStatus(text, ready) {
  $("statusPill").textContent = text;
  $("statusPill").classList.toggle("ready", !!ready);
  $("setupSummary").textContent = ready ? text : "not set up (answers show the matching notes)";
}

function refreshStatus() {
  if (mode === "local") setStatus(`${local.name} · this computer`, true);
  else if (mode === "browser") setStatus(`${activeModel.name} · browser`, true);
  else if (mode === "server") setStatus(`${server.model} · own server`, true);
  else setStatus("Notes only", false);
}

function systemPrompt(step, caption, hits) {
  const notes = hits.map((c, n) => `[${n + 1}] ${c.title}\n${c.text}`).join("\n\n");
  return `You are the project assistant for a desktop study of the Minisceongo Creek "M" bend behind Samsondale Avenue in West Haverstraw, New York. The study measured how the creek's south bank (the house side) moved between two lidar surveys (19 November 2011 and 15 April 2022).

Rules:
- Answer ONLY from the project notes below. If the notes do not cover the question, say "The project notes don't cover that." and, if useful, say what they do cover.
- Use plain, simple English for someone who is not a specialist. Explain any technical word you use.
- Keep it short: 2 to 5 sentences, or up to 5 short bullets for lists or steps.
- Copy numbers, units (feet) and station numbers exactly from the notes. Never invent numbers.
- The viewer is watching an animated walk-through of the method. They are on step ${step + 1} of 10, "${MAN.steps[step]}". The screen says: "${caption}" When they say "this", "here" or "these", they mean what is on that screen.

Project notes:
${notes}`;
}

function estTokens(msgs) { return Math.round(msgs.reduce((s, m) => s + m.content.split(/\s+/).length, 0) * 1.45); }

function buildMessages(question, step, caption, hits) {
  let h = history.slice(-4).map((m) => ({ role: m.role, content: m.content.length > 700 ? m.content.slice(0, 700) + "…" : m.content }));
  let used = hits.slice();
  let msgs = () => [{ role: "system", content: systemPrompt(step, caption, used) }, ...h, { role: "user", content: question }];
  const limit = CTX_TOKENS[mode];
  if (limit) {
    while (estTokens(msgs()) > limit && h.length) h = h.slice(2);
    while (estTokens(msgs()) > limit && used.length > 1) used = used.slice(0, -1);
  }
  return { messages: msgs(), used };
}

async function streamBrowser(messages, onText) {
  const req = { messages, stream: true, temperature: 0.3, max_tokens: 600 };
  if (activeModel.thinking) req.extra_body = { enable_thinking: false };
  const chunks = await engine.chat.completions.create(req);
  let text = "";
  for await (const ch of chunks) {
    const d = ch.choices?.[0]?.delta?.content || "";
    if (d) { text += d; onText(text); }
    if (stopFlag) { try { engine.interruptGenerate(); } catch (e) { /* already stopped */ } break; }
  }
  return text;
}

async function streamServer(messages, onText) {
  abortCtl = new AbortController();
  const res = await fetch(server.url, {
    method: "POST", signal: abortCtl.signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: server.model, messages, stream: true, temperature: 0.3, max_tokens: 800 }),
  });
  if (!res.ok || !res.body) throw new Error(`The server answered ${res.status} ${res.statusText}`.trim());
  const reader = res.body.getReader(), dec = new TextDecoder();
  let buf = "", text = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop();
    for (const line of lines) {
      const t = line.trim();
      if (!t.startsWith("data:")) continue;
      const data = t.slice(5).trim();
      if (data === "[DONE]") return text;
      try {
        const d = JSON.parse(data).choices?.[0]?.delta?.content || "";
        if (d) { text += d; onText(text); }
      } catch (e) { /* keep-alive or partial line */ }
    }
  }
  return text;
}

// Ollama streams one JSON object per line.
async function readLines(res, onObj) {
  const reader = res.body.getReader(), dec = new TextDecoder();
  let buf = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();
      for (const line of lines) if (line.trim()) onObj(JSON.parse(line));
    }
    if (buf.trim()) onObj(JSON.parse(buf));
  } catch (e) {
    reader.cancel().catch(() => {});
    throw e;
  }
}

async function errorOf(res) {
  const t = await res.text().catch(() => "");
  try { return JSON.parse(t).error || `${res.status} ${res.statusText}`; } catch (e) { return (t || `${res.status} ${res.statusText}`).trim(); }
}

async function streamLocal(messages, onText) {
  abortCtl = new AbortController();
  const req = { model: local.id, messages, stream: true, keep_alive: "20m",
    options: { temperature: 0.4, top_p: 0.8, num_ctx: 8192, num_predict: 700 } };
  if (local.think) req.think = false;                    // answer straight away instead of reasoning first
  const send = () => fetch(OLLAMA + "/api/chat", {
    method: "POST", signal: abortCtl.signal, headers: { "Content-Type": "application/json" }, body: JSON.stringify(req),
  });
  let res = await send();
  if (!res.ok && req.think === false) {                  // a model that cannot switch thinking off: ask again without it
    const msg = await errorOf(res);
    if (!/think/i.test(msg)) throw new Error(msg);
    delete req.think; local.think = false;
    res = await send();
  }
  if (!res.ok || !res.body) throw new Error(await errorOf(res));
  let text = "";
  await readLines(res, (o) => {
    if (o.error) throw new Error(o.error);
    const d = (o.message && o.message.content) || "";
    if (d) { text += d; onText(text); }
  });
  return text;
}

function localHint(msg) {
  if (/memory/i.test(msg)) return " The model needs more memory than this computer has free. Close other programs, or pick a smaller model (Model, above).";
  if (/not found/i.test(msg)) return " The model is no longer on this computer. Set it up again (Model, above).";
  return " Is Ollama still running? Start it from the Start menu (or Applications), then ask again.";
}

async function ask(question) {
  question = question.trim();
  if (!question || busy || !MAN) return;
  if (playing) { pause(); addMsg("note", "Paused the animation while you ask."); }
  const step = stepOf(cur), caption = MAN.captions[FR[cur].c];
  addMsg("user", `<p>${esc(question)}</p>`);
  $("q").value = "";

  if (mode === "notes") {
    const hits = search(question, step, BUDGET.notes).slice(0, 2);
    const body = hits.map((c) => `<div class="passage"><h4>${esc(c.title)}</h4>${md(c.text)}</div>`).join("");
    addMsg("bot", `<div class="who">From the project notes</div>${body}<p class="small">These are the matching notes. <button type="button" class="linkbtn" data-act="offer">Get written answers instead</button></p>`);
    return;
  }

  const hits = search(question, step, BUDGET[mode]);
  const { messages, used } = buildMessages(question, step, caption, hits);
  const who = mode === "browser" ? activeModel.name : mode === "local" ? local.name : server.model;
  const box = addMsg("bot", `<div class="who">${esc(who)}</div><div class="body"><p class="thinking">Thinking…</p></div>`);
  const body = box.querySelector(".body");
  busy = true; stopFlag = false;
  $("sendBtn").disabled = true; $("stopBtn").hidden = false;
  let text = "";
  try {
    const onText = (t) => { text = t; body.innerHTML = md(stripThink(t)) || '<p class="thinking">Thinking…</p>'; $("messages").scrollTop = $("messages").scrollHeight; };
    text = mode === "browser" ? await streamBrowser(messages, onText)
      : mode === "local" ? await streamLocal(messages, onText) : await streamServer(messages, onText);
    text = stripThink(text);
    body.innerHTML = md(text);
    if (!text.trim() && !stopFlag) body.innerHTML = "<p>No answer came back. Try asking in a different way.</p>";
    if (text.trim()) history.push({ role: "user", content: question }, { role: "assistant", content: text });
  } catch (e) {
    body.innerHTML = md(stripThink(text));
    if (!(e && e.name === "AbortError")) {
      const msg = String(e && e.message || e);
      const hint = mode === "server" ? " Check that the server is running and allows this page (see Model, above)."
        : mode === "local" ? localHint(msg) : "";
      body.insertAdjacentHTML("beforeend", `<p class="small">Something went wrong: ${esc(msg)}.${hint}</p>`);
    }
  } finally {
    if (stopFlag) body.insertAdjacentHTML("beforeend", "<p class=\"small\">Stopped.</p>");
    box.insertAdjacentHTML("beforeend", sourcesHtml(used));
    busy = false; abortCtl = null;
    $("sendBtn").disabled = false; $("stopBtn").hidden = true;
    $("messages").scrollTop = $("messages").scrollHeight;
  }
}

// ------------------------------------------------------------------------------------------------ AI on this computer (Ollama)
// A web page cannot install programs, so the page looks for Ollama on this computer, offers a small setup file when it is
// missing, then asks Ollama to download the model. The model is kept on the PC, not in the browser, and found again next time.
let ollama = { state: "unknown", version: null };   // state: ready (answers this page) | blocked | missing
let installed = [];                                 // chat models already in Ollama: [{ id, size }]
let setupRun = null;                                // the set-up in progress: { card, stop, ctl, act, choice }
let offerEl = null;                                 // the "want written answers?" message

const LOOPBACK = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
const PLATFORM = (() => {
  const ua = navigator.userAgent || "", uad = navigator.userAgentData;
  if ((uad && uad.mobile) || /android|iphone|ipad|ipod/i.test(ua)) return "phone";
  const p = (uad && uad.platform) || navigator.platform || ua;
  return /win/i.test(p) ? "windows" : /mac/i.test(p) ? "mac" : "other";
})();
const PHONE_NOTE = "Written answers need an AI model on a computer: open this page on a Windows, Mac or Linux computer to set it up. Here, answers show the matching project notes.";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const gb = (bytes) => (bytes / 1e9).toFixed(1) + " GB";
const localInfo = (id) => LOCAL_MODELS.find((m) => m.id === id) || { id, name: id, tag: "", size: "", ram: "", requires: "0" };
const hasModel = (id) => installed.some((m) => m.id === id);

function within(ms) {
  if (AbortSignal.timeout) return AbortSignal.timeout(ms);
  const c = new AbortController();
  setTimeout(() => c.abort(), ms);
  return c.signal;
}

function atLeast(version, need) {
  const a = String(version || "0").split(/[.-]/).map((x) => parseInt(x, 10) || 0), b = need.split(".").map(Number);
  for (let k = 0; k < 3; k++) if ((a[k] || 0) !== (b[k] || 0)) return (a[k] || 0) > (b[k] || 0);
  return true;
}

// Chrome and Edge ask the reader before a web site may reach programs on this computer ("local network access").
async function lnaState() {
  if (LOOPBACK || !navigator.permissions || !navigator.permissions.query) return "none";
  for (const name of ["loopback-network", "local-network-access", "local-network"]) {
    try { return (await navigator.permissions.query({ name })).state; } catch (e) { /* not a permission this browser has */ }
  }
  return "none";
}

// Is Ollama running on this computer, and does it let this page in?
async function probe(ms) {
  try {
    const r = await fetch(OLLAMA + "/api/version", { cache: "no-store", signal: within(ms) });
    if (!r.ok) return (ollama.state = "blocked");
    ollama.version = (await r.json()).version || "0";
    return (ollama.state = "ready");
  } catch (e) {
    try {   // an unreadable (opaque) reply means Ollama is there, but its list of allowed sites keeps this page out
      await fetch(OLLAMA + "/api/version", { mode: "no-cors", cache: "no-store", signal: within(3000) });
      return (ollama.state = "blocked");
    } catch (e2) { return (ollama.state = "missing"); }
  }
}

async function listLocal() {
  const j = await (await fetch(OLLAMA + "/api/tags", { cache: "no-store" })).json();
  installed = (j.models || []).filter((m) => {
    const fam = [m.details && m.details.family, ...((m.details && m.details.families) || [])].join(" ");
    // leave out embedding models, and cloud models (they would send the questions off this computer)
    return !/embed/i.test(m.name) && !/bert/i.test(fam) && !m.remote_host && !/[:-]cloud$/i.test(m.name);
  }).map((m) => ({ id: m.name, size: m.size }));
  renderLocalSel();
}

// The model to use without asking: the one used here last time, else one of ours that is already installed.
function preferred() {
  const last = store.get("mce.localModel");
  if (last && hasModel(last)) return last;
  const m = LOCAL_MODELS.find((x) => hasModel(x.id));
  return m ? m.id : null;
}

function renderLocalSel() {
  const sel = $("localSel"), keep = sel.value;
  sel.textContent = "";
  const add = (parent, value, text) => { const o = document.createElement("option"); o.value = value; o.textContent = text; parent.append(o); };
  const group = (label) => { const g = document.createElement("optgroup"); g.label = label; sel.append(g); return g; };
  if (installed.length) {
    const g = group("Already on this computer");
    for (const m of installed) { const i = localInfo(m.id); add(g, m.id, i.tag ? `${i.name} — ${i.tag}` : m.id); }
  }
  const more = LOCAL_MODELS.filter((m) => !hasModel(m.id));
  if (more.length) {
    const g = installed.length ? group("Download") : sel;
    for (const m of more) add(g, m.id, `${m.name} — ${m.tag} (${m.size})`);
  }
  const ids = [...sel.options].map((o) => o.value);
  sel.value = [keep, local && local.id, preferred(), LOCAL_MODELS[0].id].find((v) => v && ids.includes(v));
  localNote();
}

function localNote() {
  const id = $("localSel").value, m = localInfo(id), inUse = !!(local && local.id === id && mode === "local");
  $("localNote").textContent = (inUse ? `${m.name} is installed on this computer and in use.`
    : hasModel(id) ? `${m.name} is already on this computer: nothing to download.`
    : `${m.name}: one-time download of ${m.size}, kept on this computer (not in the browser). Works best with ${m.ram} of memory.`)
    + " It runs in Ollama, a free, open-source program; your questions never leave this computer.";
  $("localBtn").textContent = inUse ? "In use" : hasModel(id) && ollama.state === "ready" ? "Use this model" : "Set up";
  $("localBtn").disabled = inUse || !!setupRun;
  const hint = ollama.state !== "ready" ? "Anything already on this computer is not downloaded again."
    : hasModel(id) ? "It is already on this computer, so nothing is downloaded." : "Ollama is already on this computer, so only the model is downloaded.";
  for (const s of document.querySelectorAll(".offer-model")) s.textContent = hasModel(id) ? m.name : `${m.name} (${m.size})`;
  for (const s of document.querySelectorAll(".offer-hint")) s.textContent = hint;
}

async function connectLocal(id) {
  let caps = [];
  try {
    const r = await fetch(OLLAMA + "/api/show", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model: id }) });
    if (r.ok) caps = (await r.json()).capabilities || [];
  } catch (e) { /* older Ollama: no list of capabilities */ }
  local = { id, name: localInfo(id).name, think: caps.includes("thinking") || /^qwen3/i.test(id), warm: false };
  mode = "local"; history = [];
  store.set("mce.localModel", id);
  $("engLocal").checked = true; showBox("local");
  refreshStatus(); renderLocalSel();
}

// Load the model into memory while the reader types, so the first answer starts sooner.
function warmLocal() {
  if (mode !== "local" || !local || local.warm) return;
  local.warm = true;
  fetch(OLLAMA + "/api/chat", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: local.id, messages: [], keep_alive: "20m" }),
  }).catch(() => { if (local) local.warm = false; });
}

// On opening the page: use a model that is already installed, without asking or downloading anything.
async function autoLocal() {
  if (PLATFORM === "phone") return;
  const lna = await lnaState();
  if (lna === "prompt" || lna === "denied") return;      // checking now would pop up a browser question; wait for the reader
  if ((await probe(2500)) !== "ready") return;
  await listLocal();
  const id = preferred();
  if (id) await connectLocal(id);
}

function offer() {
  if (PLATFORM === "phone") { addMsg("note", PHONE_NOTE); return; }
  if (offerEl && offerEl.isConnected) { offerEl.scrollIntoView({ block: "nearest" }); return; }
  offerEl = addMsg("bot setupcard", `<div class="who">Written answers</div>
    <p>For written answers I need a free, open-source AI model on this computer: <strong class="offer-model"></strong>. It is installed once and stays on your PC (not in the browser), so next time it is ready straight away. Your questions never leave your computer.</p>
    <div class="row"><button type="button" class="primary" data-act="setup">Yes, set it up</button><button type="button" data-act="notnow">Not now</button><button type="button" class="linkbtn" data-act="choices">Other choices</button></div>
    <p class="small offer-hint"></p>`);
  localNote();
}

function needOllama(st, m) {
  const lead = st === "blocked"
    ? `<p><strong>Ollama is on this computer but does not let this page in yet.</strong> One setting fixes that; nothing is installed again.</p>`
    : st === "old"
      ? `<p><strong>Ollama on this computer is too old for ${esc(m.name)}</strong> (it has version ${esc(ollama.version)}; the model needs ${m.requires} or newer).</p>`
      : `<p><strong>One-time setup.</strong> The model runs in Ollama, a free, open-source program that is not on this computer yet (or is not running).</p>`;
  const then = hasModel(m.id) ? "" : ` and downloads ${esc(m.name)} (${m.size}) if it is not there yet`;
  let steps;
  if (PLATFORM === "windows") {
    steps = `<ol>
      <li><a class="btn primary" href="${SETUP_FILE}" download="Install_Local_AI.bat">Download the setup file</a> <span class="small">Windows,&nbsp;5&nbsp;KB</span></li>
      <li>Open it from your downloads. If Windows says it protected your PC, choose <b>More info</b>, then <b>Run anyway</b>.</li>
      <li>Come back here: this page carries on by itself${then}.</li>
    </ol>
    <details class="small"><summary>What does the setup file do?</summary><p>It installs Ollama from ollama.com (about 1 GB, no administrator rights needed) or updates it, lets this walk-through's web site talk to it, and starts it. Nothing else is changed. <a href="${SETUP_SOURCE}" target="_blank" rel="noopener">Read the file</a></p></details>`;
  } else {
    const allow = PLATFORM === "mac" ? `launchctl setenv OLLAMA_ORIGINS "${location.origin}"` : `OLLAMA_ORIGINS="${location.origin}"`;
    steps = `<ol>
      ${st === "blocked" ? "" : `<li>${st === "old" ? "Update" : "Install"} Ollama from <a href="https://ollama.com/download" target="_blank" rel="noopener">ollama.com/download</a> and open it.</li>`}
      ${LOOPBACK ? "" : PLATFORM === "mac"
        ? `<li>Let this page use it: in Terminal, run <code>${esc(allow)}</code> <button type="button" class="linkbtn" data-act="copy" data-text="${esc(allow)}">Copy</button>, then quit Ollama from the menu bar and open it again.</li>`
        : `<li>Let this page use it: set <code>${esc(allow)}</code> for the Ollama service and restart it (<a href="https://docs.ollama.com/faq" target="_blank" rel="noopener">how</a>).</li>`}
      <li>Come back here: this page carries on by itself${then}.</li>
    </ol>`;
  }
  return `${lead}${steps}<p class="small wait">Waiting for Ollama…</p><div class="row"><button type="button" data-act="cancel">Cancel</button></div>`;
}

async function waitText(st) {
  if ((await lnaState()) === "denied") return "Your browser is blocking this page from reaching apps on this computer. Click the icon at the left of the web address, allow access to apps and devices on your network, then reload the page.";
  if (st === "blocked") return "Ollama found. Waiting for it to let this page in…";
  if (st === "ready") return `Ollama ${ollama.version} found. Waiting for the update…`;
  return "Waiting for Ollama…";
}

// Check every 3 seconds, for up to 30 minutes or until the reader cancels.
async function pollUntil(run, test) {
  for (const end = Date.now() + 30 * 60e3; Date.now() < end && !run.stop;) {
    await sleep(3000);
    if (!run.stop && await test()) return true;
  }
  return false;
}

async function pull(run, m, show) {
  show(`<p><strong>Downloading ${esc(m.name)} to this computer</strong></p><div class="progress"><div class="pbar"></div></div>
    <p class="small pstat">Starting…</p><div class="row"><button type="button" data-act="pause">Pause</button><button type="button" data-act="cancel">Cancel</button></div>`);
  const bar = run.card.querySelector(".pbar"), stat = run.card.querySelector(".pstat");
  run.ctl = new AbortController();
  const res = await fetch(OLLAMA + "/api/pull", {
    method: "POST", signal: run.ctl.signal, headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: m.id, stream: true }),
  });
  if (!res.ok || !res.body) throw new Error(await errorOf(res));
  const parts = new Map();
  let status = "";
  await readLines(res, (o) => {
    if (o.error) throw new Error(o.error);
    status = o.status || status;
    if (o.digest && o.total) parts.set(o.digest, [o.completed || 0, o.total]);
    let done = 0, total = 0;
    for (const [c, t] of parts.values()) { done += c; total += t; }
    if (/^(verifying|writing|removing|success)/.test(status)) { bar.style.width = "100%"; stat.textContent = "Finishing…"; }
    else if (total) {
      const pct = Math.min(100, Math.floor(100 * done / total));
      bar.style.width = pct + "%";
      stat.textContent = `${gb(done)} of ${gb(total)} (${pct}%) · keep this page open`;
    }
  });
  run.ctl = null;
  if (status !== "success") throw new Error("the download did not finish");
}

// Yes, set it up: find (or install) Ollama, download the model if it is missing, then connect.
async function setupLocal(id) {
  if (setupRun || busy) return;
  if (PLATFORM === "phone") { addMsg("note", PHONE_NOTE); return; }
  const m = localInfo(id);
  if (ollama.state === "ready" && hasModel(id) && !(offerEl && offerEl.isConnected)) {    // switching between installed models
    await connectLocal(id);
    addMsg("note", `Now using ${esc(m.name)} on this computer.`);
    return;
  }
  const run = setupRun = { stop: false, ctl: null, choice: null };
  run.card = offerEl && offerEl.isConnected ? offerEl : addMsg("bot setupcard", "");
  offerEl = null;
  run.act = (act) => {
    if (act === "cancel") { run.stop = true; if (run.ctl) run.ctl.abort(); }
    if (act === "pause" && run.ctl) run.ctl.abort();
    if (run.choice) run.choice(act);
  };
  const show = (html) => { run.card.innerHTML = `<div class="who">AI on this computer</div>${html}`; run.card.scrollIntoView({ block: "nearest" }); };
  const choose = (html) => new Promise((resolve) => { show(html); run.choice = (act) => { run.choice = null; resolve(act); }; });
  const okVersion = () => atLeast(ollama.version, m.requires);
  localNote();
  let downloaded = false;
  try {
    const lna = await lnaState();
    show(`<p>Checking this computer…</p>${lna === "prompt" ? `<p class="small">Your browser may ask whether this site may connect to apps on this device. Choose <b>Allow</b>: that is how the page reaches the AI on your computer.</p>` : ""}`);
    const st = await probe(60000);
    if (st === "ready") await listLocal();
    if (st !== "ready" || (!hasModel(id) && !okVersion())) {
      show(needOllama(st === "ready" ? "old" : st, m));
      const wait = run.card.querySelector(".wait");
      const found = await pollUntil(run, async () => {
        const s = await probe(2500);
        if (s === "ready" && okVersion()) return true;
        wait.textContent = await waitText(s);
        return false;
      });
      if (!found) { show(`<p>Set-up stopped. You can start it again any time under <b>Model</b>, above.</p>`); return; }
      await listLocal();
    }
    while (!hasModel(id) && !downloaded) {
      try {
        await pull(run, m, show);
        downloaded = true;
        await listLocal();
      } catch (e) {
        if (!(e && e.name === "AbortError")) throw e;
        const act = run.stop ? "cancel" : await choose(`<p>Download paused. Ollama keeps what it has so far.</p>
          <div class="row"><button type="button" class="primary" data-act="resume">Continue</button><button type="button" data-act="cancel">Cancel</button></div>`);
        if (act !== "resume") { show(`<p>Download stopped. Ollama keeps what it has, so setting up again carries on from there.</p>`); return; }
      }
    }
    await connectLocal(id);
    warmLocal();
    show(`<p class="ok"><strong>&#10003; ${esc(m.name)} is ready on this computer.</strong></p>
      <p>${downloaded ? "It is installed now" : "It was already installed, so nothing was downloaded"}. Ask away: next time you open this page it connects by itself.</p>`);
  } catch (e) {
    const msg = String(e && e.message || e);
    const hint = /newer version/i.test(msg) ? "Ollama needs updating: run the setup file again, or pick Qwen3 8B under Model, above. "
      : /dial tcp|no such host|timeout|registry|tls|certificate/i.test(msg) ? "Ollama could not download the model: check the internet connection (some company networks block ollama.com), then try again. "
      : /space|disk/i.test(msg) ? "The computer may be short of disk space for the model. "
      : /failed to fetch|networkerror|load failed/i.test(msg) ? "Ollama stopped answering: check that it is running (Start menu or Applications), then try again. " : "";
    show(`<p>Set-up hit a problem: ${esc(msg)}.</p>
      <p class="small">${hint}Meanwhile, questions still get the matching project notes.</p>
      <div class="row"><button type="button" class="primary" data-act="setup">Try again</button></div>`);
    offerEl = run.card;                                  // "Try again" reuses this message
  } finally {
    setupRun = null;
    localNote();
  }
}

function onMessagesClick(e) {
  const b = e.target.closest("[data-act]");
  if (!b) return;
  const act = b.dataset.act, cardEl = b.closest(".setupcard");
  if (act === "offer") offer();
  else if (act === "setup") setupLocal($("localSel").value);
  else if (act === "notnow") {
    if (cardEl === offerEl) offerEl = null;
    cardEl.className = "msg note";
    cardEl.innerHTML = "OK. Answers show the matching project notes. You can set up written answers any time under <b>Model</b>, above.";
  } else if (act === "choices") {
    $("setup").open = true; $("engLocal").checked = true; showBox("local");
    $("setup").scrollIntoView({ block: "nearest" }); $("localSel").focus();
  } else if (act === "copy") {
    if (navigator.clipboard) navigator.clipboard.writeText(b.dataset.text).then(() => { b.textContent = "Copied"; }, () => {});
  } else if (setupRun && cardEl === setupRun.card) setupRun.act(act);
}

// ------------------------------------------------------------------------------------------------ model setup
function showBox(which) {
  $("localBox").hidden = which !== "local";
  $("browserBox").hidden = which !== "browser";
  $("serverBox").hidden = which !== "server";
}

async function webgpuOk() {
  if (!("gpu" in navigator)) return false;
  try { return !!(await navigator.gpu.requestAdapter()); } catch (e) { return false; }
}

function modelNote() {
  const m = MODELS.find((x) => x.id === $("modelSel").value);
  $("modelNote").textContent = `${m.name}: download of ${m.size} into this browser's storage. The browser may clear it, and it has to load into memory again on every visit, so "On this computer" starts faster. Needs ${m.vram} of graphics memory; if loading fails, pick a smaller model. Questions are not sent anywhere.`;
}

async function loadModel() {
  const m = MODELS.find((x) => x.id === $("modelSel").value);
  $("loadBtn").disabled = true; $("modelSel").disabled = true;
  $("progWrap").hidden = false; $("progBar").style.width = "0%";
  setStatus("Loading…", false);
  try {
    if (!webllm) webllm = await import(WEBLLM_URL);
    if (engine) { try { await engine.unload(); } catch (e) { /* nothing loaded */ } }
    engine = await webllm.CreateMLCEngine(m.id, {
      initProgressCallback: (r) => {
        $("progBar").style.width = Math.round((r.progress || 0) * 100) + "%";
        $("modelNote").textContent = r.text || "";
      },
    });
    activeModel = m; mode = "browser"; history = [];
    refreshStatus(); localNote();
    $("modelNote").textContent = `${m.name} is loaded and runs in this browser. Ask away.`;
    addMsg("note", `${esc(m.name)} is ready. Answers now come from the model, using the matching project notes.`);
  } catch (e) {
    engine = null; activeModel = null;
    if (mode === "browser") mode = local ? "local" : server ? "server" : "notes";
    refreshStatus();
    $("modelNote").textContent = `Could not load ${m.name}: ${String(e && e.message || e)}. It may need more graphics memory than this computer has; try a smaller model.`;
  } finally {
    $("loadBtn").disabled = false; $("modelSel").disabled = false;
    $("progWrap").hidden = true;
  }
}

function useServer() {
  const url = $("srvUrl").value.trim(), model = $("srvModel").value.trim();
  if (!url || !model) { addMsg("note", "Enter the server address and a model name first."); return; }
  server = { url, model }; mode = "server"; history = [];
  refreshStatus(); localNote();
  addMsg("note", `Using ${esc(model)} at ${esc(url)}. If answers fail, check the server is running and allows this page (see the note under the server address).`);
}

async function initAssistant() {
  const chunks = await (await fetch("knowledge/chunks.json")).json();
  buildIndex(chunks);
  const sel = $("modelSel");
  for (const m of MODELS) {
    const o = document.createElement("option");
    o.value = m.id; o.textContent = `${m.name} — ${m.tag} (${m.size})`;
    sel.append(o);
  }
  sel.addEventListener("change", modelNote);
  modelNote();
  webgpuOk().then((ok) => {
    if (ok) return;
    $("loadBtn").disabled = true; sel.disabled = true;
    $("modelNote").textContent = "This browser cannot run models (no WebGPU). Use \"On this computer\" instead, or Chrome or Edge on a computer.";
  });
  renderLocalSel();
  $("localSel").addEventListener("change", localNote);
  $("localBtn").addEventListener("click", () => setupLocal($("localSel").value));
  $("loadBtn").addEventListener("click", loadModel);
  $("srvBtn").addEventListener("click", useServer);
  for (const r of document.querySelectorAll('input[name="engine"]')) {
    r.addEventListener("change", () => {
      const which = document.querySelector('input[name="engine"]:checked').value;
      showBox(which);
      // switch to a model already set up there; otherwise keep the current one until the reader sets one up
      if (which === "local" && local) mode = "local";
      else if (which === "browser" && engine) mode = "browser";
      else if (which === "server" && server) mode = "server";
      refreshStatus(); localNote();
    });
  }
  $("messages").addEventListener("click", onMessagesClick);
  $("askForm").addEventListener("submit", (e) => { e.preventDefault(); ask($("q").value); });
  $("q").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask($("q").value); } });
  $("q").addEventListener("focus", () => { if (playing) pause(); warmLocal(); });
  $("stopBtn").addEventListener("click", () => {
    stopFlag = true;
    if (abortCtl) abortCtl.abort();
    if (mode === "browser" && engine) { try { engine.interruptGenerate(); } catch (e) { /* not generating */ } }
  });
  $("clearBtn").addEventListener("click", () => {
    if (setupRun) setupRun.act("cancel");
    $("messages").textContent = ""; offerEl = null; history = [];
    welcome();
  });
  try { await autoLocal(); } catch (e) { /* not there: the welcome message offers the set-up instead */ }
  welcome();
}

function welcome() {
  addMsg("bot", `<div class="who">Project assistant</div><p>Ask me anything about this study: why a step was done, what a number means, or what happened at a station. I answer only from the project notes and list the notes I used.</p>`);
  if (mode === "local") addMsg("note", `Using ${esc(local.name)} on this computer (already installed, nothing to download).`);
  else if (mode === "notes") offer();
}

initPlayer().catch((e) => { $("caption").textContent = "Could not load the animation: " + e.message; });
initAssistant().catch((e) => addMsg("note", "Could not load the project notes: " + esc(e.message)));
