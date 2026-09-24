// Minisceongo Creek bank erosion explainer: animation player + project assistant (RAG over the project notes).

const WEBLLM_URL = "https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.85/+esm";
const MODELS = [
  { id: "Qwen3.5-9B-q4f16_1-MLC", name: "Qwen3.5 9B", tag: "best answers", size: "4.7 GB", vram: "about 6.5 GB", thinking: true },
  { id: "Qwen3.5-4B-q4f16_1-MLC", name: "Qwen3.5 4B", tag: "balanced", size: "2.2 GB", vram: "about 4 GB", thinking: true },
  { id: "Qwen3.5-2B-q4f16_1-MLC", name: "Qwen3.5 2B", tag: "light", size: "1.0 GB", vram: "about 2.3 GB", thinking: true },
  { id: "Llama-3.1-8B-Instruct-q4f16_1-MLC", name: "Llama 3.1 8B", tag: "alternative", size: "4.2 GB", vram: "about 5 GB", thinking: false },
  { id: "Llama-3.2-3B-Instruct-q4f16_1-MLC", name: "Llama 3.2 3B", tag: "light", size: "1.7 GB", vram: "about 2.3 GB", thinking: false },
];
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
const BUDGET = { browser: 1300, server: 2600, notes: 700 };        // words of project notes per question
const CTX_TOKENS = 3300;                                            // browser models run with a 4,096-token window

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

function search(query, step, budget) {
  const q = [...new Set(tokens(query, true))];
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
    return { c, s };
  }).sort((a, b2) => b2.s - a.s);
  let picked = scored.filter((x) => x.s > 0).slice(0, 8);
  if (!picked.length) picked = CHUNKS.filter((c) => c.steps.includes(step)).slice(0, 3).map((c) => ({ c, s: 0 }));
  const out = [];
  let words = 0;
  for (const { c } of picked) {
    if (out.length && words + c.words > budget) continue;
    out.push(c); words += c.words;
    if (out.length >= 6) break;
  }
  return out;
}

// ================================================================================================ assistant
let mode = "notes";              // notes | browser | server
let engine = null, webllm = null, activeModel = null;
let server = null;               // { url, model }
let history = [];                // [{role, content}] of earlier exchanges (model modes only)
let busy = false, stopFlag = false, abortCtl = null;

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
  $("setupSummary").textContent = ready ? text : "not loaded (answers show the matching notes)";
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
  if (mode === "browser") {
    while (estTokens(msgs()) > CTX_TOKENS && h.length) h = h.slice(2);
    while (estTokens(msgs()) > CTX_TOKENS && used.length > 1) used = used.slice(0, -1);
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
    addMsg("bot", `<div class="who">From the project notes</div>${body}<p class="small">Load a model (Model, above) to get a written answer instead of the matching notes.</p>`);
    return;
  }

  const hits = search(question, step, BUDGET[mode]);
  const { messages, used } = buildMessages(question, step, caption, hits);
  const who = mode === "browser" ? activeModel.name : server.model;
  const box = addMsg("bot", `<div class="who">${esc(who)}</div><div class="body"><p class="thinking">Thinking…</p></div>`);
  const body = box.querySelector(".body");
  busy = true; stopFlag = false;
  $("sendBtn").disabled = true; $("stopBtn").hidden = false;
  let text = "";
  try {
    const onText = (t) => { text = t; body.innerHTML = md(stripThink(t)) || '<p class="thinking">Thinking…</p>'; $("messages").scrollTop = $("messages").scrollHeight; };
    text = mode === "browser" ? await streamBrowser(messages, onText) : await streamServer(messages, onText);
    text = stripThink(text);
    body.innerHTML = md(text);
    if (!text.trim() && !stopFlag) body.innerHTML = "<p>No answer came back. Try asking in a different way.</p>";
    if (text.trim()) history.push({ role: "user", content: question }, { role: "assistant", content: text });
  } catch (e) {
    body.innerHTML = md(stripThink(text));
    if (!(e && e.name === "AbortError")) {
      const hint = mode === "server" ? " Check that the server is running and allows this page (see Model, above)." : "";
      body.insertAdjacentHTML("beforeend", `<p class="small">Something went wrong: ${esc(String(e && e.message || e))}.${hint}</p>`);
    }
  } finally {
    if (stopFlag) body.insertAdjacentHTML("beforeend", "<p class=\"small\">Stopped.</p>");
    box.insertAdjacentHTML("beforeend", sourcesHtml(used));
    busy = false; abortCtl = null;
    $("sendBtn").disabled = false; $("stopBtn").hidden = true;
    $("messages").scrollTop = $("messages").scrollHeight;
  }
}

// ------------------------------------------------------------------------------------------------ model setup
async function webgpuOk() {
  if (!("gpu" in navigator)) return false;
  try { return !!(await navigator.gpu.requestAdapter()); } catch (e) { return false; }
}

function modelNote() {
  const m = MODELS.find((x) => x.id === $("modelSel").value);
  $("modelNote").textContent = `${m.name}: one-time download of ${m.size}, then kept in this browser. Needs ${m.vram} of graphics memory; if loading fails, pick a smaller model. Runs on your computer; questions are not sent anywhere.`;
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
    setStatus(`${m.name} ready`, true);
    $("modelNote").textContent = `${m.name} is loaded and runs on this computer. Ask away.`;
    addMsg("note", `${esc(m.name)} is ready. Answers now come from the model, using the matching project notes.`);
  } catch (e) {
    engine = null; activeModel = null; mode = server ? "server" : "notes";
    setStatus(server ? server.model : "Notes only", !!server);
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
  setStatus(`${model} (own server)`, true);
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
  if (!(await webgpuOk())) {
    $("loadBtn").disabled = true; sel.disabled = true;
    $("modelNote").textContent = "This browser cannot run models (no WebGPU). Use Chrome or Edge on a computer, or connect your own model server below.";
  }
  $("loadBtn").addEventListener("click", loadModel);
  $("srvBtn").addEventListener("click", useServer);
  for (const r of document.querySelectorAll('input[name="engine"]')) {
    r.addEventListener("change", () => {
      const srv = $("engServer").checked;
      $("serverBox").hidden = !srv; $("browserBox").hidden = srv;
      if (srv && server) { mode = "server"; setStatus(`${server.model} (own server)`, true); }
      else if (!srv && engine) { mode = "browser"; setStatus(`${activeModel.name} ready`, true); }
      else if (!srv && !engine) { mode = "notes"; setStatus("Notes only", false); }
    });
  }
  $("askForm").addEventListener("submit", (e) => { e.preventDefault(); ask($("q").value); });
  $("q").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask($("q").value); } });
  $("q").addEventListener("focus", () => { if (playing) pause(); });
  $("stopBtn").addEventListener("click", () => {
    stopFlag = true;
    if (abortCtl) abortCtl.abort();
    if (mode === "browser" && engine) { try { engine.interruptGenerate(); } catch (e) { /* not generating */ } }
  });
  $("clearBtn").addEventListener("click", () => { $("messages").textContent = ""; history = []; welcome(); });
  welcome();
}

function welcome() {
  addMsg("bot", `<div class="who">Project assistant</div><p>Ask me anything about this study: why a step was done, what a number means, or what happened at a station. I answer only from the project notes and list the notes I used.</p><p class="small">Right now I show the matching notes. For written answers, open <strong>Model</strong> above and load an open-source model (runs on your computer), or connect your own model server.</p>`);
}

initPlayer().catch((e) => { $("caption").textContent = "Could not load the animation: " + e.message; });
initAssistant().catch((e) => addMsg("note", "Could not load the project notes: " + esc(e.message)));
