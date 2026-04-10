#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import tempfile
import shutil
import cgi
from datetime import datetime

# Optional: hide urllib3 LibreSSL warning spam in console output
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL*")

APP_NAME = "CodePilot"
APP_TAGLINE = "Intelligent Python Code Analyzer & Optimizer"
HOST = os.environ.get("CP_HOST", "127.0.0.1")
PORT = int(os.environ.get("CP_PORT", "8787"))
DESTINATION_FOLDER = "/Users/valentingempp/Documents/Fichier créer projet PI2"
ACTIONS = [
    ("optimize", "Optimize (format/imports/unused vars)"),
    ("report-html", "Generate HTML report"),
    ("doc-ai", "Generate docs (AI)"),
    ("doc-html", "Generate docs (HTML)"),
    ("readme", "Generate README.md"),
    ("requirements", "Generate requirements.txt"),
    ("all", "Run everything"),
]

LOGO_SVG = r"""
<svg width="34" height="34" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="CodePilot AI logo" role="img">
  <defs>
    <linearGradient id="g" x1="10" y1="8" x2="54" y2="56" gradientUnits="userSpaceOnUse">
      <stop stop-color="#7C3AED"/>
      <stop offset="0.45" stop-color="#22C55E"/>
      <stop offset="1" stop-color="#38BDF8"/>
    </linearGradient>
    <filter id="s" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.25"/>
    </filter>
  </defs>
  <g filter="url(#s)">
    <path d="M32 6C18.2 6 7 17.2 7 31s11.2 25 25 25 25-11.2 25-25S45.8 6 32 6Z" fill="#0B1220"/>
    <path d="M23 22l-9 9 9 9" stroke="url(#g)" stroke-width="4.6" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M41 22l9 9-9 9" stroke="url(#g)" stroke-width="4.6" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M28 42l8-20" stroke="url(#g)" stroke-width="4.6" stroke-linecap="round"/>
  </g>
</svg>
"""


def _options_html() -> str:
    return "".join([f'<option value="{cmd}">{label}</option>' for cmd, label in ACTIONS])


# IMPORTANT:
# We do NOT use an f-string here (no f"""..."""), so your JS/CSS can contain normal { } safely.
HTML_TEMPLATE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{{APP_NAME}} • Web UI</title>
<style>
  :root {
    --bg0: #070A12;
    --bg1: #0B1020;
    --card: rgba(255,255,255,0.06);
    --card2: rgba(255,255,255,0.08);
    --stroke: rgba(255,255,255,0.12);
    --text: rgba(255,255,255,0.92);
    --muted: rgba(255,255,255,0.60);
    --muted2: rgba(255,255,255,0.42);
    --shadow: 0 12px 40px rgba(0,0,0,0.45);
    --shadow2: 0 8px 20px rgba(0,0,0,0.30);

    --accentA: #7C3AED;
    --accentB: #22C55E;
    --accentC: #38BDF8;

    --radius: 18px;
  }

  [data-theme="light"] {
    --bg0: #EEF2FF;
    --bg1: #F5F7FF;
    --card: rgba(0,0,0,0.03);
    --card2: rgba(0,0,0,0.04);
    --stroke: rgba(0,0,0,0.10);
    --text: rgba(10, 15, 25, 0.92);
    --muted: rgba(10, 15, 25, 0.60);
    --muted2: rgba(10, 15, 25, 0.45);
    --shadow: 0 12px 40px rgba(10,15,25,0.12);
    --shadow2: 0 8px 20px rgba(10,15,25,0.10);
  }

  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0;
    color: var(--text);
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
    background:
      radial-gradient(1200px 600px at 20% -10%, rgba(124,58,237,0.35), transparent 60%),
      radial-gradient(900px 600px at 110% 20%, rgba(34,197,94,0.20), transparent 55%),
      radial-gradient(900px 700px at 50% 120%, rgba(56,189,248,0.18), transparent 60%),
      linear-gradient(180deg, var(--bg0), var(--bg1));
  }

  .wrap {
    max-width: 1200px;
    margin: 0 auto;
    padding: 18px 16px 22px;
  }

  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 14px 14px;
    border: 1px solid var(--stroke);
    background: linear-gradient(180deg, var(--card2), var(--card));
    border-radius: var(--radius);
    box-shadow: var(--shadow2);
    backdrop-filter: blur(10px);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 240px;
  }
  .brand .title {
    display: flex;
    flex-direction: column;
    line-height: 1.1;
  }
  .brand .title b { font-size: 15px; letter-spacing: 0.2px; }
  .brand .title span { color: var(--muted); font-size: 12px; margin-top: 3px; }

  .pill {
    font-size: 12px;
    color: var(--muted);
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.04);
    padding: 8px 10px;
    border-radius: 999px;
  }

  .toggle {
    display: inline-flex;
    align-items: center;
    gap: 10px;
  }
  .switch {
    width: 46px; height: 26px;
    border-radius: 999px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.06);
    position: relative;
    cursor: pointer;
  }
  .knob {
    position: absolute;
    width: 20px; height: 20px;
    top: 2.5px; left: 3px;
    border-radius: 999px;
    background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(255,255,255,0.75));
    box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    transition: transform 160ms ease;
  }
  [data-theme="light"] .knob { transform: translateX(20px); }

  .grid {
    margin-top: 14px;
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 14px;
    min-height: calc(100vh - 130px);
  }

  .card {
    border: 1px solid var(--stroke);
    background: linear-gradient(180deg, var(--card2), var(--card));
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    backdrop-filter: blur(12px);
    overflow: hidden;
  }
  .card .head {
    padding: 14px 14px 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .card .head h3 {
    margin: 0;
    font-size: 13px;
    letter-spacing: 0.35px;
    text-transform: uppercase;
    color: var(--muted);
  }
  .card .body { padding: 0 14px 14px; }

  .divider {
    height: 1px;
    background: var(--stroke);
    margin: 0 14px;
  }

  label {
    display: block;
    font-size: 12px;
    color: var(--muted);
    margin: 12px 0 6px;
  }

  select, input[type="text"] {
    width: 100%;
    padding: 11px 12px;
    border-radius: 12px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.06);
    color: var(--text);
    outline: none;
    font-size: 14px;
    transition: box-shadow 160ms ease, border-color 160ms ease;
  }
  [data-theme="light"] select,
  [data-theme="light"] input[type="text"] {
    background: rgba(0,0,0,0.03);
  }
  select:focus, input[type="text"]:focus {
    border-color: rgba(56,189,248,0.55);
    box-shadow: 0 0 0 4px rgba(56,189,248,0.16);
  }

  .row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  .row2 {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 10px;
    align-items: end;
  }

  .btn {
    appearance: none;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.06);
    color: var(--text);
    padding: 11px 12px;
    border-radius: 12px;
    cursor: pointer;
    font-weight: 800;
    letter-spacing: 0.2px;
    transition: transform 120ms ease, background 120ms ease, opacity 120ms ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    user-select: none;
  }
  .btn:hover { transform: translateY(-1px); background: rgba(255,255,255,0.09); }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn.primary {
    border-color: rgba(124,58,237,0.55);
    background: linear-gradient(135deg, rgba(124,58,237,0.95), rgba(56,189,248,0.78));
    box-shadow: 0 14px 38px rgba(124,58,237,0.25);
  }
  .btn.danger { border-color: rgba(239,68,68,0.55); background: rgba(239,68,68,0.10); }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 10px;
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--stroke);
    color: var(--muted);
    font-size: 12px;
  }

  .check {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 12px;
    padding: 10px 10px;
    border-radius: 14px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.04);
  }
  .check input { width: 18px; height: 18px; accent-color: var(--accentC); }

  .right {
    display: grid;
    grid-template-rows: auto 1fr auto;
    gap: 14px;
  }

  .console {
    height: 100%;
    min-height: 360px;
    border-radius: var(--radius);
    border: 1px solid rgba(255,255,255,0.10);
    background: linear-gradient(180deg, rgba(11,18,32,0.98), rgba(11,18,32,0.85));
    box-shadow: var(--shadow);
    overflow: hidden;
    display: grid;
    grid-template-rows: auto 1fr;
  }
  .console .bar {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.10);
    display:flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
  }
  .dots { display:flex; gap: 7px; align-items:center; }
  .dot { width: 10px; height: 10px; border-radius: 99px; opacity: 0.9; }
  .dot.r { background:#EF4444; }
  .dot.y { background:#F59E0B; }
  .dot.g { background:#22C55E; }
  .console pre {
    margin: 0;
    padding: 12px;
    white-space: pre-wrap;
    word-break: break-word;
    overflow: auto;
    color: #E5E7EB;
    background: transparent;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    font-size: 12.5px;
    line-height: 1.45;
  }

  .status {
    display:flex;
    justify-content: space-between;
    align-items:center;
    gap: 10px;
    color: var(--muted);
    font-size: 12px;
  }

  .toast {
    position: fixed;
    right: 18px;
    bottom: 18px;
    background: rgba(0,0,0,0.75);
    color: white;
    border: 1px solid rgba(255,255,255,0.18);
    padding: 12px 12px;
    border-radius: 14px;
    box-shadow: 0 16px 50px rgba(0,0,0,0.45);
    max-width: 360px;
    opacity: 0;
    transform: translateY(12px);
    transition: opacity 180ms ease, transform 180ms ease;
    pointer-events: none;
    backdrop-filter: blur(10px);
  }
  [data-theme="light"] .toast { background: rgba(10,15,25,0.86); }
  .toast.show { opacity: 1; transform: translateY(0); }

  .kbd {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 8px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,0.06);
    color: var(--muted);
  }

  @media (max-width: 980px) {
    .grid { grid-template-columns: 1fr; }
  }
</style>
</head>

<body data-theme="dark">
<div class="wrap">

  <div class="topbar">
    <div class="brand">
      <div>{{LOGO_SVG}}</div>
      <div class="title">
        <b>{{APP_NAME}}</b>
        <span>{{APP_TAGLINE}}</span>
      </div>
    </div>

    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap; justify-content:flex-end;">
      <div class="pill">Local only • {{HOST}}:{{PORT}}</div>
      <div class="toggle">
        <span class="pill">Theme</span>
        <div class="switch" id="themeSwitch" title="Toggle light/dark">
          <div class="knob"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="grid">

    <div class="card">
      <div class="head">
        <h3>Actions</h3>
        <span class="chip">CLI launcher</span>
      </div>
      <div class="divider"></div>
      <div class="body">
        <label for="action">Action</label>
        <select id="action">
          {{OPTIONS_HTML}}
        </select>

        <div class="check">
          <input type="checkbox" id="inplace" />
          <div>
            <div style="font-weight:800;">Modify files in place</div>
            <div style="color:var(--muted2); font-size:12px; margin-top:2px;">Only for <b>optimize</b> (adds <span class="kbd">--inplace</span>)</div>
          </div>
        </div>

        <div class="card" style="margin-top:14px;">
          <div class="head">
            <h3>Upload</h3>
            <span class="chip" id="uploadChip">No upload</span>
          </div>
          <div class="divider"></div>
          <div class="body">

            <div id="dropzone" style="
              border: 1px dashed var(--stroke);
              background: rgba(255,255,255,0.04);
              border-radius: 16px;
              padding: 14px;
              text-align: center;
              color: var(--muted);
              cursor: pointer;
              user-select: none;
            ">
              Drop a file/folder here<br/>
              <span style="color:var(--muted2); font-size:12px;">or click to select</span>
            </div>

            <div style="display:none;">
              <input id="fileInput" type="file" />
              <input id="folderInput" type="file" webkitdirectory directory multiple />
            </div>

            <div style="margin-top:12px; display:flex; gap:10px; flex-wrap:wrap;">
              <button class="btn" id="pickFile">Pick file</button>
              <button class="btn" id="pickFolder">Pick folder</button>
              <button class="btn danger" id="clearUpload" disabled>Clear upload</button>
            </div>

            <div style="margin-top:10px; color:var(--muted2); font-size:12px; line-height:1.45;">
              Uploaded content is stored locally in a temp folder and used as target when you run an action.
            </div>

          </div>
        </div>

        <div style="margin-top:12px; color:var(--muted2); font-size:12px; line-height:1.45;">
          Tip — You can use a folder as target (e.g. <span class="kbd">src/ai_code_agent</span>) to process multiple files.
          <br><br>
          The UI runs: <span class="kbd">python -m ai_code_agent.cli ...</span>
        </div>
      </div>
    </div>

    <div class="right">

      <div class="card">
        <div class="head">
          <h3>Target</h3>
          <span class="chip" id="chipState">Ready</span>
        </div>
        <div class="divider"></div>
        <div class="body">

          <label for="path">Path (file or folder)</label>
          <input id="path" type="text" placeholder="e.g. src/ai_code_agent or src/ai_code_agent/test_tutor.py" />

          <div class="row">
            <div>
              <label for="output">HTML output</label>
              <input id="output" type="text" value="analysis_report.html" />
            </div>
            <div>
              <label>&nbsp;</label>
              <button class="btn" id="openReport" disabled>Open HTML</button>
            </div>
          </div>

          <div class="row2" style="margin-top: 12px;">
            <div class="status" id="status">
              <span>Ready.</span>
              <span style="color:var(--muted2)">Shortcuts: <span class="kbd">⌘</span>+<span class="kbd">Enter</span> run, <span class="kbd">Esc</span> stop</span>
            </div>
            <div style="display:flex; gap:10px; justify-content:flex-end; flex-wrap:wrap;">
              <button class="btn" id="openOptimized" disabled>Open optimized</button>
              <button class="btn" id="clear">Clear</button>
              <button class="btn danger" id="stop" disabled>Stop</button>
              <button class="btn primary" id="run">Run</button>
            </div>
          </div>

        </div>
      </div>

      <div class="console">
        <div class="bar">
          <div class="dots">
            <div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
          </div>
          <div class="chip" id="cmdPreview">Command: —</div>
        </div>
        <pre id="console">$ </pre>
      </div>

      <div class="status">
        <span>Server: <span class="kbd">web_gui.py</span> • Project root enforced • PYTHONPATH includes <span class="kbd">src/</span></span>
        <span id="footInfo"></span>
      </div>

    </div>

  </div>
</div>

<div class="toast" id="toast"></div>

<script>
  const el = (id) => document.getElementById(id);

  let lastOutputReport = "analysis_report.html";
  let lastOutputDoc = "docstrings_report.html";
  let outputTouched = false;
  let lastAction = null;

  // server-side uploaded target path (file or upload folder)
  let uploadedTarget = null;

  function toast(msg) {
    const t = el("toast");
    t.textContent = msg;
    t.classList.add("show");
    setTimeout(() => t.classList.remove("show"), 1800);
  }

  function log(s) {
    const c = el("console");
    c.textContent += s;
    c.scrollTop = c.scrollHeight;
  }

  function setStatus(s, chipText=null) {
    el("status").firstElementChild.textContent = s;
    if (chipText) el("chipState").textContent = chipText;
  }

  function cmdPreviewText() {
    const action = el("action").value;
    const chosenPath = el("path").value.trim() || uploadedTarget || "<path>";
    const inplace = el("inplace").checked;
    const out = el("output").value.trim() || (action === "doc-html" ? "docstrings_report.html" : "analysis_report.html");

    let cmd = `python -m ai_code_agent.cli ${action} ${chosenPath}`;
    if (action === "optimize" && inplace) cmd += " --inplace";
    if (action === "report-html") cmd += ` --output ${out}`;
    if (action === "doc-html") cmd += `  (will rename docstrings_report.html -> ${out})`;
    if (action === "all") {
      return `python -m ai_code_agent.cli all ${chosenPath} --output-dir ~/Downloads/CodePilot_Result_TIMESTAMP`;
    }
    return cmd;
  }

  function refreshUI() {
    const action = el("action").value;

    el("inplace").disabled = action !== "optimize";
    if (action !== "optimize") el("inplace").checked = false;

    if (!outputTouched) {
      if (action === "report-html") {
        el("output").value = lastOutputReport || "analysis_report.html";
      } else if (action === "doc-html") {
        el("output").value = lastOutputDoc || "docstrings_report.html";
      } else if (action === "readme") {
        el("output").value = "README.md";
      } else if (action === "requirements") {
        el("output").value = "requirements.txt";
      }
      else if (action === "all") {
        el("output").value = "Auto folder in Downloads";
      }
    }

    el("cmdPreview").textContent = "Command: " + cmdPreviewText();
  }

  // Theme
  let theme = localStorage.getItem("cp_theme") || "dark";
  document.body.setAttribute("data-theme", theme);
  el("themeSwitch").addEventListener("click", () => {
    theme = (document.body.getAttribute("data-theme") === "dark") ? "light" : "dark";
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("cp_theme", theme);
    toast("Theme: " + theme);
  });

  el("output").addEventListener("input", () => { outputTouched = true; });

  el("action").addEventListener("change", () => {
    if (lastAction === "report-html") lastOutputReport = el("output").value.trim() || "analysis_report.html";
    if (lastAction === "doc-html") lastOutputDoc = el("output").value.trim() || "docstrings_report.html";
    outputTouched = false;
    lastAction = el("action").value;
    refreshUI();
  });

  el("path").addEventListener("input", refreshUI);
  el("inplace").addEventListener("change", refreshUI);

  lastAction = el("action").value;
  refreshUI();

  let running = false;

  el("clear").addEventListener("click", () => {
    el("console").textContent = "$ ";
    toast("Console cleared");
  });

  el("openReport").addEventListener("click", async () => {
    const r = await fetch("/open-html", { method: "POST" });
    const j = await r.json();
    if (!j.ok) alert(j.error || "Cannot open HTML.");
  });

  el("openOptimized").addEventListener("click", async () => {
    const r = await fetch("/open-optimized", { method: "POST" });
    const j = await r.json();
    if (!j.ok) alert(j.error || "Cannot open optimized file.");
  });

  async function runAction() {
    if (running) return;
    running = true;

    el("run").disabled = true;
    el("stop").disabled = false;
    el("openReport").disabled = true;
    el("openOptimized").disabled = true;

    const chosenPath = el("path").value.trim() || uploadedTarget || "";

    const payload = {
      action: el("action").value,
      path: chosenPath,
      inplace: el("inplace").checked,
      output: el("output").value.trim()
    };

    const pretty = cmdPreviewText();
    log("\n\n$ " + pretty + "\n");
    setStatus("Running…", "Running");

    const resp = await fetch("/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await resp.json();

    if (!data.ok) {
      log("\n[ERROR] " + (data.error || "Unknown error") + "\n");
      setStatus("Error.", "Error");
      toast("Error");
    } else {
      if (data.output) log(data.output);
      log("\n[EXIT] Return code: " + data.returncode + "\n");

      setStatus("Done.", "Done");
      toast("Done");

      if (data.html_path) el("openReport").disabled = false;
      if (data.optimized_path) el("openOptimized").disabled = false;

      if (data.info) el("footInfo").textContent = data.info;
    }

    el("run").disabled = false;
    el("stop").disabled = true;
    running = false;
  }

  el("run").addEventListener("click", runAction);

  el("stop").addEventListener("click", async () => {
    const r = await fetch("/stop", { method: "POST" });
    const j = await r.json();
    if (j.ok) {
      log("\n[STOP] Terminate signal sent.\n");
      setStatus("Stopping…", "Stopping");
      toast("Stopping");
    } else {
      log("\n[STOP] " + (j.error || "Failed") + "\n");
      toast("Stop failed");
    }
  });

  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      runAction();
    }
    if (e.key === "Escape") el("stop").click();
  });

  // ------------------------------
  // Upload handling (file / folder)
  // ------------------------------
  function setUploadState(label, ok) {
    const chip = el("uploadChip");
    if (!chip) return;
    chip.textContent = label;
    chip.style.opacity = ok ? "1" : "0.75";
  }

  function enableUploadClear(enabled) {
    const b = el("clearUpload");
    if (b) b.disabled = !enabled;
  }

  function setTargetPathFromUpload(path) {
    uploadedTarget = path || null;

    if (uploadedTarget) {
      el("path").value = uploadedTarget; // show user
      toast("Upload ready: target set");
      setUploadState("Ready", true);
      enableUploadClear(true);
    } else {
      setUploadState("No upload", false);
      enableUploadClear(false);
    }
    refreshUI();
  }

  function buildFormData(files) {
    const fd = new FormData();
    for (const f of files) {
      const rel = f.webkitRelativePath || f.name; // keep folder structure when possible
      fd.append("files", f, rel);
    }
    return fd;
  }

  async function uploadFiles(files, kind = "file") {
    if (!files || files.length === 0) return;

    setStatus("Uploading…", "Uploading");
    setUploadState("Uploading…", false);

    const fd = buildFormData(files);
    fd.append("kind", kind);

    const resp = await fetch("/upload", { method: "POST", body: fd });
    const data = await resp.json();

    if (!data.ok) {
      setStatus("Upload error.", "Error");
      setUploadState("Error", false);
      toast(data.error || "Upload failed");
      return;
    }

    setTargetPathFromUpload(data.target_path);
    setStatus("Ready.", "Ready");
    toast(`Uploaded (${data.count || files.length})`);
  }

  (function initUploadUI() {
    const dz = el("dropzone");
    const fileInput = el("fileInput");
    const folderInput = el("folderInput");
    const pickFile = el("pickFile");
    const pickFolder = el("pickFolder");
    const clearUpload = el("clearUpload");

    if (!dz || !fileInput || !folderInput || !pickFile || !pickFolder || !clearUpload) return;

    setUploadState("No upload", false);
    enableUploadClear(false);

    dz.addEventListener("click", () => fileInput.click());

    dz.addEventListener("dragover", (e) => {
      e.preventDefault();
      dz.style.background = "rgba(255,255,255,0.07)";
      dz.style.borderColor = "rgba(56,189,248,0.55)";
    });

    dz.addEventListener("dragleave", () => {
      dz.style.background = "rgba(255,255,255,0.04)";
      dz.style.borderColor = "var(--stroke)";
    });

    dz.addEventListener("drop", async (e) => {
      e.preventDefault();
      dz.style.background = "rgba(255,255,255,0.04)";
      dz.style.borderColor = "var(--stroke)";

      const files = Array.from(e.dataTransfer.files || []);
      await uploadFiles(files, "drop");
    });

    pickFile.addEventListener("click", () => fileInput.click());
    pickFolder.addEventListener("click", () => folderInput.click());

    fileInput.addEventListener("change", async () => {
      const files = Array.from(fileInput.files || []);
      fileInput.value = "";
      await uploadFiles(files, "file");
    });

    folderInput.addEventListener("change", async () => {
      const files = Array.from(folderInput.files || []);
      folderInput.value = "";
      await uploadFiles(files, "folder");
    });

    clearUpload.addEventListener("click", async () => {
      try { await fetch("/clear-upload", { method: "POST" }); } catch (_) {}
      uploadedTarget = null;
      setUploadState("No upload", false);
      enableUploadClear(false);
      toast("Upload cleared");
      refreshUI();
    });
  })();
</script>
</body>
</html>
"""


def build_html() -> str:
    html = HTML_TEMPLATE
    html = html.replace("{{APP_NAME}}", APP_NAME)
    html = html.replace("{{APP_TAGLINE}}", APP_TAGLINE)
    html = html.replace("{{HOST}}", HOST)
    html = html.replace("{{PORT}}", str(PORT))
    html = html.replace("{{LOGO_SVG}}", LOGO_SVG)
    html = html.replace("{{OPTIONS_HTML}}", _options_html())
    return html


HTML = build_html()


class Handler(BaseHTTPRequestHandler):
    server_version = "CodePilotAI/2.2"

    def _send(self, code=200, content_type="application/json", body=b"{}"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    # ---------- Upload helpers ----------
    def _parse_multipart(self):
        ctype, _pdict = cgi.parse_header(self.headers.get("content-type", ""))
        if ctype != "multipart/form-data":
            raise ValueError("Expected multipart/form-data")

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("content-type"),
            },
        )
        return form

    @staticmethod
    def _safe_relpath(name: str) -> str:
        name = (name or "").replace("\\", "/").lstrip("/")

        # remove Windows drive (C:)
        if ":" in name.split("/")[0]:
            name = "/".join(name.split("/")[1:])

        norm = os.path.normpath(name).replace("\\", "/")
        while norm.startswith("../") or norm == "..":
            norm = norm[3:] if norm.startswith("../") else ""
        if norm in ("", ".", "/"):
            norm = "uploaded_file"
        return norm

    def _ensure_upload_root(self):
        root = getattr(self.server, "upload_root", None)
        if root and os.path.isdir(root):
            return root
        root = tempfile.mkdtemp(prefix="codepilot_upload_")
        self.server.upload_root = root
        return root

    def _clear_upload_root(self):
        root = getattr(self.server, "upload_root", None)
        if root and os.path.isdir(root):
            shutil.rmtree(root, ignore_errors=True)
        self.server.upload_root = None

    def _handle_upload(self):
        form = self._parse_multipart()
        kind = form.getfirst("kind", "file")

        fields = form["files"] if "files" in form else []
        if not isinstance(fields, list):
            fields = [fields]

        if not fields or (len(fields) == 1 and not getattr(fields[0], "filename", None)):
            raise ValueError("No files received.")

        # Reset previous upload
        self._clear_upload_root()
        root = self._ensure_upload_root()

        saved = []
        uploaded_map = []  # store temp path + relative original name

        for item in fields:
            filename = getattr(item, "filename", None)
            if not filename:
                continue

            rel = self._safe_relpath(filename)
            out_path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            with open(out_path, "wb") as f:
                shutil.copyfileobj(item.file, f)

            saved.append(out_path)
            uploaded_map.append({
                "relative_name": rel,
                "temp_path": out_path,
            })

        if not saved:
            raise ValueError("Upload parsing failed (no valid files).")

        # Keep upload info on server
        self.server.uploaded_files_map = uploaded_map

        # target: single file => file ; otherwise => root folder
        if len(saved) == 1 and kind == "file":
            target = saved[0]
        else:
            target = root

        return {"ok": True, "count": len(saved), "target_path": target}

    # ---------- HTTP ----------
    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/" or p.path == "/index.html":
            body = HTML.encode("utf-8")
            self._send(200, "text/html; charset=utf-8", body)
            return
        self._send(404, "text/plain; charset=utf-8", b"Not Found")

    def do_POST(self):
        p = urlparse(self.path)

        # Upload routes
        if p.path == "/upload":
            try:
                payload = self._handle_upload()
                self._send(200, "application/json", json.dumps(payload).encode("utf-8"))
            except Exception as e:
                self._send(200, "application/json", json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            return

        if p.path == "/clear-upload":
            try:
                self._clear_upload_root()
                self._send(200, "application/json", b'{"ok": true}')
            except Exception as e:
                self._send(200, "application/json", json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            return

        if p.path == "/run":
            data = self._json()
            try:
                produced_html = None
                action = (data.get("action") or "").strip()
                target_path = (data.get("path") or "").strip()
                inplace = bool(data.get("inplace"))
                output = (data.get("output") or "").strip()

                valid_actions = [a[0] for a in ACTIONS]
                if action not in valid_actions:
                    raise ValueError("Unknown action.")
                if not target_path:
                    raise ValueError("Please provide a path (file or folder).")
                if not os.path.exists(target_path):
                    raise ValueError(f"Path does not exist: {target_path}")

                if not output:
                    output = "docstrings_report.html" if action == "doc-html" else "analysis_report.html"
                if not os.path.isabs(output):
                    output = os.path.join(self._output_base_dir(target_path), output)

                cmd = [sys.executable, "-m", "ai_code_agent.cli", action, target_path]
                if action == "optimize" and inplace:
                    cmd.append("--inplace")
                if action in {"report-html", "doc-html", "readme", "requirements"}:
                    cmd += ["--output", output]
                if action == "all":
                    downloads_dir = os.path.expanduser("~/Downloads")
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_dir = os.path.join(downloads_dir, f"CodePilot_Result_{stamp}")
                    cmd += ["--output-dir", output_dir]

                predicted_optimized = None
                if action == "optimize" and (not inplace):
                    base, ext = os.path.splitext(target_path)
                    if ext.lower() == ".py":
                        predicted_optimized = os.path.abspath(base + "_optimized.py")

                project_root = os.path.dirname(os.path.abspath(__file__))
                env = os.environ.copy()
                src_path = os.path.join(project_root, "src")
                env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

                self.server.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=project_root,
                    env=env
                )
                out, _ = self.server.current_process.communicate()
                # Base directory where generated files should exist
                if os.path.isfile(target_path):
                    output_base_dir = os.path.dirname(target_path)
                else:
                    output_base_dir = target_path

                # Detect produced HTML
                if action == "report-html":
                    candidate = output if os.path.isabs(output) else os.path.join(output_base_dir, output)
                    if os.path.exists(candidate):
                        produced_html = candidate

                elif action == "doc-html":
                    candidate = output if os.path.isabs(output) else os.path.join(output_base_dir, output)
                    generated_default = os.path.join(output_base_dir, "docstrings_report.html")

                    if os.path.exists(candidate):
                        produced_html = candidate
                    elif os.path.exists(generated_default):
                        produced_html = generated_default

                self.server.last_html_path = produced_html
                self.server.last_optimized_path = None

                # Detect optimized files
                if action == "optimize":
                    for root_dir, _, files in os.walk(output_base_dir):
                        for f in files:
                            if f.endswith("_optimized.py"):
                                self.server.last_optimized_path = os.path.join(root_dir, f)
                                break

                # Copy generated files to destination folder
                try:
                    os.makedirs(DESTINATION_FOLDER, exist_ok=True)

                    # optimized files
                    for root_dir, _, files in os.walk(output_base_dir):
                        for f in files:
                            if f.endswith("_optimized.py"):
                                src = os.path.join(root_dir, f)
                                dst = os.path.join(DESTINATION_FOLDER, f)
                                shutil.copy2(src, dst)

                    # html files
                    for html_name in ["analysis_report.html", "docstrings_report.html"]:
                        html_path = os.path.join(output_base_dir, html_name)
                        if os.path.exists(html_path):
                            shutil.copy2(html_path, os.path.join(DESTINATION_FOLDER, html_name))

                    if produced_html and os.path.exists(produced_html):
                        shutil.copy2(
                            produced_html,
                            os.path.join(DESTINATION_FOLDER, os.path.basename(produced_html))
                        )

                    # README from upload
                    readme_path = os.path.join(output_base_dir, "README.md")
                    if os.path.exists(readme_path):
                        shutil.copy2(readme_path, os.path.join(DESTINATION_FOLDER, "README.md"))

                    # requirements from upload
                    req_path = os.path.join(output_base_dir, "requirements.txt")
                    if os.path.exists(req_path):
                        shutil.copy2(req_path, os.path.join(DESTINATION_FOLDER, "requirements.txt"))

                except Exception as e:
                    print("Copy generated files error:", e)

                rc = self.server.current_process.returncode
                self.server.current_process = None

                produced_html = None
                if action == "report-html":
                    candidate = output if os.path.isabs(output) else os.path.abspath(output)
                    if os.path.exists(candidate):
                        produced_html = candidate
                elif action == "doc-html":
                    generated = os.path.abspath("docstrings_report.html")
                    if os.path.exists(generated):
                        desired = output.strip() or "docstrings_report.html"
                        desired_path = desired if os.path.isabs(desired) else os.path.abspath(desired)
                        if os.path.abspath(generated) != os.path.abspath(desired_path):
                            try:
                                if os.path.exists(desired_path):
                                    os.remove(desired_path)
                                os.replace(generated, desired_path)
                                produced_html = desired_path
                            except Exception:
                                produced_html = generated
                        else:
                            produced_html = generated
                if action == "all":
                    os.makedirs(output_dir, exist_ok=True)
                else:
                    output_dir = None

                self.server.last_html_path = produced_html
                self.server.last_optimized_path = predicted_optimized if predicted_optimized and os.path.exists(predicted_optimized) else None

                payload = {
                    "ok": True,
                    "returncode": rc,
                    "output": out,
                    "html_path": self.server.last_html_path,
                    "optimized_path": self.server.last_optimized_path,
                    "info": f"Ran in: {project_root}"
                }
                self._send(200, "application/json", json.dumps(payload).encode("utf-8"))
            except Exception as e:
                self._send(200, "application/json", json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            return

        if p.path == "/stop":
            try:
                proc = getattr(self.server, "current_process", None)
                if proc is None:
                    self._send(200, "application/json", b'{"ok": false, "error": "No process running."}')
                    return
                proc.terminate()
                self._send(200, "application/json", b'{"ok": true}')
            except Exception as e:
                self._send(200, "application/json", json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            return

        if p.path == "/open-html":
            try:
                htmlp = getattr(self.server, "last_html_path", None)
                if not htmlp or not os.path.exists(htmlp):
                    self._send(200, "application/json", b'{"ok": false, "error": "No HTML available."}')
                    return
                self._open_file(htmlp)
                self._send(200, "application/json", b'{"ok": true}')
            except Exception as e:
                self._send(200, "application/json", json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            return

        if p.path == "/open-optimized":
            try:
                opt = getattr(self.server, "last_optimized_path", None)
                if not opt or not os.path.exists(opt):
                    self._send(200, "application/json", b'{"ok": false, "error": "No optimized file available."}')
                    return
                self._open_file(opt)
                self._send(200, "application/json", b'{"ok": true}')
            except Exception as e:
                self._send(200, "application/json", json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            return

        self._send(404, "text/plain; charset=utf-8", b"Not Found")

    @staticmethod
    def _open_file(path: str):
        if sys.platform.startswith("darwin"):
            subprocess.Popen(["open", path])
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", path])

    def _output_base_dir(self, target_path: str) -> str:
        if os.path.isdir(target_path):
            return target_path
        return os.path.dirname(target_path)


def main():
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    httpd.current_process = None
    httpd.last_html_path = None
    httpd.last_optimized_path = None
    httpd.upload_root = None

    import webbrowser
    webbrowser.open(f"http://{HOST}:{PORT}")
    print(f"{APP_NAME} Web UI: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if httpd.current_process:
                httpd.current_process.terminate()
        except Exception:
            pass

        try:
            if getattr(httpd, "upload_root", None):
                shutil.rmtree(httpd.upload_root, ignore_errors=True)
        except Exception:
            pass

        httpd.server_close()


if __name__ == "__main__":
    main()
