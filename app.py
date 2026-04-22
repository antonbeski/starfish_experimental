"""
Satellite Intelligence Flask App - Single File with Embedded HTML
Vercel-compatible | Inline satellite maps via Leaflet.js (no API keys)
"""

from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>SATINTEL — Satellite Intelligence Platform</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  :root {
    --bg: #030a0f;
    --surface: #071520;
    --border: #0e3a5a;
    --accent: #00d4ff;
    --accent2: #00ff9d;
    --accent3: #ff6b35;
    --text: #c8e8f5;
    --text-dim: #4a7a99;
    --danger: #ff3860;
    --glow: 0 0 20px rgba(0,212,255,0.3);
    --glow2: 0 0 20px rgba(0,255,157,0.3);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: var(--bg); color: var(--text);
    font-family: 'Rajdhani', sans-serif;
    min-height: 100vh; overflow-x: hidden;
  }
  body::before {
    content:''; position:fixed; inset:0;
    background-image:
      linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events:none; z-index:0;
  }
  body::after {
    content:''; position:fixed; top:-50%; left:-50%;
    width:200%; height:200%;
    background:
      radial-gradient(ellipse at 30% 20%, rgba(0,80,120,0.15) 0%, transparent 60%),
      radial-gradient(ellipse at 70% 80%, rgba(0,60,40,0.1) 0%, transparent 60%);
    pointer-events:none; z-index:0;
    animation: drift 20s ease-in-out infinite alternate;
  }
  @keyframes drift { from{transform:translate(0,0)} to{transform:translate(3%,2%)} }

  .corner-deco { position:fixed; width:80px; height:80px; pointer-events:none; z-index:2; opacity:0.25; }
  .corner-deco.tl { top:16px; left:16px; border-top:1px solid var(--accent); border-left:1px solid var(--accent); }
  .corner-deco.tr { top:16px; right:16px; border-top:1px solid var(--accent); border-right:1px solid var(--accent); }
  .corner-deco.bl { bottom:16px; left:16px; border-bottom:1px solid var(--accent); border-left:1px solid var(--accent); }
  .corner-deco.br { bottom:16px; right:16px; border-bottom:1px solid var(--accent); border-right:1px solid var(--accent); }

  .scanline {
    position:fixed; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg, transparent, rgba(0,212,255,0.3), transparent);
    animation:scan 8s linear infinite; pointer-events:none; z-index:9999;
  }
  @keyframes scan { from{top:0;opacity:1} to{top:100vh;opacity:0} }

  /* HEADER */
  header {
    position:relative; z-index:1;
    padding:28px 28px 0;
    max-width:1300px; margin:0 auto 36px;
  }
  .header-inner {
    display:flex; align-items:center;
    justify-content:space-between;
    border-bottom:1px solid var(--border); padding-bottom:18px;
  }
  .logo { display:flex; align-items:center; gap:14px; }
  .logo-icon {
    width:42px; height:42px;
    border:2px solid var(--accent); border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    box-shadow:var(--glow);
    animation:spin 10s linear infinite; position:relative;
  }
  .logo-icon::before {
    content:''; position:absolute; inset:5px; border-radius:50%;
    border:1px solid rgba(0,212,255,0.35); border-top-color:var(--accent);
    animation:spin 3s linear infinite reverse;
  }
  @keyframes spin { to{transform:rotate(360deg)} }
  .logo-icon svg { width:18px; height:18px; color:var(--accent); animation:spinR 10s linear infinite; }
  @keyframes spinR { to{transform:rotate(-360deg)} }
  .logo-text {
    font-family:'Orbitron',monospace; font-size:1.45rem; font-weight:900;
    letter-spacing:0.1em; color:var(--accent); text-shadow:var(--glow);
  }
  .logo-sub {
    font-family:'Share Tech Mono',monospace; font-size:0.62rem;
    color:var(--text-dim); letter-spacing:0.2em; text-transform:uppercase;
  }
  .status-bar { display:flex; gap:20px; font-family:'Share Tech Mono',monospace; font-size:0.68rem; color:var(--text-dim); }
  .status-item { display:flex; align-items:center; gap:6px; }
  .status-dot {
    width:7px; height:7px; border-radius:50%;
    background:var(--accent2); box-shadow:0 0 8px var(--accent2);
    animation:blink 2s ease-in-out infinite;
  }
  .status-dot.amber { background:var(--accent3); box-shadow:0 0 8px var(--accent3); }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

  /* CONTAINER */
  .container {
    position:relative; z-index:1;
    max-width:1300px; margin:0 auto;
    padding:0 28px 60px;
  }

  /* SEARCH */
  .search-section { text-align:center; margin-bottom:48px; }
  .search-eyebrow {
    font-family:'Orbitron',monospace; font-size:0.68rem;
    letter-spacing:0.3em; color:var(--text-dim); text-transform:uppercase; margin-bottom:10px;
  }
  .search-headline {
    font-size:2.1rem; font-weight:700; line-height:1.1; margin-bottom:8px;
    background:linear-gradient(135deg, var(--text) 0%, var(--accent) 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  }
  .search-desc { color:var(--text-dim); font-size:1rem; font-weight:300; margin-bottom:28px; }
  .search-box { display:flex; max-width:500px; margin:0 auto; position:relative; }
  .search-box::before {
    content:'TICKER'; position:absolute; left:14px; top:50%; transform:translateY(-50%);
    font-family:'Share Tech Mono',monospace; font-size:0.58rem; letter-spacing:0.15em;
    color:var(--text-dim); z-index:2; pointer-events:none;
  }
  #ticker-input {
    flex:1; background:var(--surface); border:1px solid var(--border); border-right:none;
    color:var(--accent); font-family:'Orbitron',monospace; font-size:1.05rem; font-weight:700;
    letter-spacing:0.15em; padding:15px 14px 15px 72px; outline:none; text-transform:uppercase;
    transition:border-color 0.2s, box-shadow 0.2s; border-radius:4px 0 0 4px;
  }
  #ticker-input::placeholder { color:var(--text-dim); font-size:0.8rem; }
  #ticker-input:focus { border-color:var(--accent); box-shadow:var(--glow); }
  #analyze-btn {
    background:var(--accent); color:var(--bg); border:none;
    padding:15px 24px; font-family:'Orbitron',monospace; font-size:0.7rem; font-weight:700;
    letter-spacing:0.15em; cursor:pointer; transition:all 0.2s;
    border-radius:0 4px 4px 0; white-space:nowrap; overflow:hidden; position:relative;
  }
  #analyze-btn::after {
    content:''; position:absolute; inset:0;
    background:rgba(255,255,255,0.12); transform:translateX(-100%); transition:transform 0.3s;
  }
  #analyze-btn:hover::after { transform:translateX(0); }
  #analyze-btn:hover { box-shadow:var(--glow); }
  #analyze-btn:disabled { opacity:0.5; cursor:not-allowed; }

  #error-box {
    display:none; background:rgba(255,56,96,0.08);
    border:1px solid var(--danger); border-radius:4px; padding:12px 16px;
    font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:var(--danger);
    max-width:500px; margin:14px auto 0; letter-spacing:0.05em;
  }

  /* SECTOR PILLS */
  .sector-browse {
    margin-top:28px; text-align:center;
  }
  .sector-browse-label {
    font-family:'Share Tech Mono',monospace; font-size:0.62rem;
    letter-spacing:0.22em; color:var(--text-dim); text-transform:uppercase; margin-bottom:12px;
  }
  .sector-pills {
    display:flex; flex-wrap:wrap; justify-content:center; gap:8px; max-width:900px; margin:0 auto;
  }
  .sector-pill {
    display:flex; align-items:center; gap:7px;
    background:var(--surface); border:1px solid var(--border);
    border-radius:3px; padding:8px 14px;
    font-family:'Share Tech Mono',monospace; font-size:0.68rem; letter-spacing:0.07em;
    color:var(--text-dim); cursor:pointer; transition:all 0.2s; white-space:nowrap;
  }
  .sector-pill:hover, .sector-pill.active {
    border-color:var(--accent); color:var(--accent);
    background:rgba(0,212,255,0.07); box-shadow:var(--glow);
  }
  .sector-pill .pill-icon { font-size:0.9rem; }
  .sector-divider {
    display:flex; align-items:center; gap:14px;
    max-width:500px; margin:22px auto 0;
    font-family:'Share Tech Mono',monospace; font-size:0.6rem; letter-spacing:0.18em; color:var(--text-dim);
  }
  .sector-divider::before, .sector-divider::after {
    content:''; flex:1; height:1px; background:var(--border);
  }

  /* LOADING */
  #loading {
    display:none; text-align:center; padding:48px;
    font-family:'Share Tech Mono',monospace; color:var(--accent);
    font-size:0.82rem; letter-spacing:0.1em;
  }
  .loader-orbit {
    width:48px; height:48px;
    border:2px solid var(--border); border-top-color:var(--accent);
    border-radius:50%; animation:spin 0.8s linear infinite; margin:0 auto 14px;
  }

  /* RESULTS */
  #results { display:none; animation:fadeUp 0.5s ease-out; }
  @keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }

  /* Company card */
  .company-card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:6px; padding:26px 30px; margin-bottom:30px;
    position:relative; overflow:hidden;
  }
  .company-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg, transparent, var(--accent), transparent);
  }
  .company-header {
    display:flex; align-items:flex-start; justify-content:space-between;
    gap:20px; flex-wrap:wrap; margin-bottom:18px;
  }
  .ticker-badge {
    display:inline-block; font-family:'Orbitron',monospace; font-size:0.62rem;
    letter-spacing:0.2em; color:var(--accent); background:rgba(0,212,255,0.08);
    border:1px solid rgba(0,212,255,0.3); padding:3px 9px; border-radius:2px; margin-bottom:7px;
  }
  .company-name { font-size:1.7rem; font-weight:700; color:var(--text); margin-bottom:4px; }
  .company-meta { font-size:0.88rem; color:var(--text-dim); }
  .company-stats { display:flex; gap:22px; flex-wrap:wrap; }
  .stat { text-align:center; }
  .stat-val {
    font-family:'Orbitron',monospace; font-size:1.05rem; font-weight:700;
    color:var(--accent2); text-shadow:var(--glow2);
  }
  .stat-val.sm { font-size:0.75rem; letter-spacing:0.04em; }
  .stat-label {
    font-size:0.68rem; color:var(--text-dim); letter-spacing:0.1em;
    text-transform:uppercase; font-family:'Share Tech Mono',monospace; margin-top:2px;
  }
  .company-desc {
    font-size:0.93rem; color:var(--text-dim); line-height:1.6;
    font-weight:300; border-top:1px solid var(--border); padding-top:14px;
  }

  .section-label {
    font-family:'Orbitron',monospace; font-size:0.63rem;
    letter-spacing:0.3em; color:var(--text-dim); text-transform:uppercase;
    margin-bottom:14px; display:flex; align-items:center; gap:10px;
  }
  .section-label::after { content:''; flex:1; height:1px; background:var(--border); }

  .signals-grid { display:flex; flex-wrap:wrap; gap:9px; margin-bottom:32px; }
  .signal-chip {
    background:rgba(0,255,157,0.06); border:1px solid rgba(0,255,157,0.2);
    border-radius:3px; padding:7px 13px; font-size:0.88rem; font-weight:500; color:var(--accent2);
  }

  /* LOCATION CARDS */
  .locations-grid {
    display:grid;
    grid-template-columns:repeat(auto-fill, minmax(340px, 1fr));
    gap:22px; margin-bottom:36px;
  }
  .loc-card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:6px; overflow:hidden;
    transition:border-color 0.25s, transform 0.25s, box-shadow 0.25s;
  }
  .loc-card:hover {
    border-color:var(--accent); transform:translateY(-3px);
    box-shadow:0 10px 36px rgba(0,0,0,0.5), 0 0 20px rgba(0,212,255,0.08);
  }

  /* Leaflet map */
  .loc-map-wrap {
    width:100%; height:220px; position:relative; background:#061018;
  }
  .loc-map-leaf { width:100%; height:100%; }

  /* HUD overlays on map */
  .map-hud {
    position:absolute; inset:0; pointer-events:none; z-index:498;
  }
  .map-hud::before {
    content:''; position:absolute; top:8px; left:8px;
    width:20px; height:20px;
    border-top:1px solid rgba(0,212,255,0.55); border-left:1px solid rgba(0,212,255,0.55);
  }
  .map-hud::after {
    content:''; position:absolute; bottom:8px; right:8px;
    width:20px; height:20px;
    border-bottom:1px solid rgba(0,212,255,0.55); border-right:1px solid rgba(0,212,255,0.55);
  }
  .map-crosshair {
    position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
    width:22px; height:22px; pointer-events:none; z-index:499;
  }
  .map-crosshair::before, .map-crosshair::after {
    content:''; position:absolute; background:rgba(0,212,255,0.65);
  }
  .map-crosshair::before { width:1px; height:100%; left:50%; top:0; }
  .map-crosshair::after  { width:100%; height:1px; top:50%; left:0; }
  .map-scan {
    position:absolute; top:0; left:0; right:0; height:1px;
    background:linear-gradient(90deg, transparent, rgba(0,212,255,0.55), transparent);
    pointer-events:none; z-index:499; animation:mapscan 4s linear infinite;
  }
  @keyframes mapscan { from{top:0;opacity:1} to{top:100%;opacity:0} }

  /* Layer toggle buttons */
  .map-layer-btns {
    position:absolute; top:8px; right:8px; z-index:500;
    display:flex; flex-direction:column; gap:4px;
  }
  .layer-btn {
    background:rgba(3,10,15,0.88); border:1px solid var(--border);
    color:var(--text-dim); font-family:'Share Tech Mono',monospace;
    font-size:0.58rem; letter-spacing:0.07em; padding:4px 8px;
    cursor:pointer; border-radius:2px; transition:all 0.15s; white-space:nowrap;
  }
  .layer-btn.active, .layer-btn:hover {
    border-color:var(--accent); color:var(--accent); background:rgba(0,212,255,0.1);
  }

  /* Card body */
  .loc-body { padding:13px 15px 15px; }
  .loc-name { font-size:0.93rem; font-weight:600; color:var(--text); margin-bottom:5px; line-height:1.3; }
  .loc-coords {
    font-family:'Share Tech Mono',monospace; font-size:0.65rem;
    color:var(--text-dim); margin-bottom:10px; letter-spacing:0.04em;
  }
  .source-row { display:flex; gap:5px; flex-wrap:wrap; }
  .src-badge {
    font-family:'Share Tech Mono',monospace; font-size:0.6rem;
    letter-spacing:0.06em; padding:3px 8px; border-radius:2px; border:1px solid;
  }
  .src-badge.esri  { color:#7ec8e3; border-color:rgba(126,200,227,0.3); }
  .src-badge.sent  { color:var(--accent2); border-color:rgba(0,255,157,0.3); }
  .src-badge.osm   { color:#f0a500; border-color:rgba(240,165,0,0.3); }

  footer {
    position:relative; z-index:1; text-align:center; padding:22px;
    border-top:1px solid var(--border);
    font-family:'Share Tech Mono',monospace; font-size:0.62rem;
    color:var(--text-dim); letter-spacing:0.15em; text-transform:uppercase;
  }

  /* Leaflet tweak: hide default attribution clutter */
  .leaflet-control-attribution { display:none !important; }

  @media (max-width:640px) {
    .header-inner { flex-direction:column; gap:12px; }
    .search-headline { font-size:1.55rem; }
    .search-box { flex-direction:column; }
    #ticker-input { border-right:1px solid var(--border); border-bottom:none; border-radius:4px 4px 0 0; }
    #analyze-btn { border-radius:0 0 4px 4px; }
    .locations-grid { grid-template-columns:1fr; }
    .company-header { flex-direction:column; }
    .status-bar { flex-wrap:wrap; gap:10px; }
  }
</style>
</head>
<body>

<div class="scanline"></div>
<div class="corner-deco tl"></div>
<div class="corner-deco tr"></div>
<div class="corner-deco bl"></div>
<div class="corner-deco br"></div>

<header>
  <div class="header-inner">
    <div class="logo">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 2v4M12 18v4M2 12h4M18 12h4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
        </svg>
      </div>
      <div>
        <div class="logo-text">SATINTEL</div>
        <div class="logo-sub">Satellite Intelligence Platform</div>
      </div>
    </div>
    <div class="status-bar">
      <div class="status-item"><span class="status-dot"></span>ESRI IMAGERY LIVE</div>
      <div class="status-item"><span class="status-dot"></span>S2 10M ACTIVE</div>
      <div class="status-item"><span class="status-dot amber"></span>OSM OVERLAY</div>
    </div>
  </div>
</header>

<div class="container">

  <div class="search-section">
    <div class="search-eyebrow">// EQUITY SATELLITE MONITOR //</div>
    <div class="search-headline">Track Any Stock From Orbit</div>
    <div class="search-desc">Enter a ticker symbol to view live satellite imagery of sector monitoring targets</div>
    <div class="search-box">
      <input type="text" id="ticker-input" placeholder="WMT, AMZN, XOM, TSLA…" maxlength="10" autocomplete="off" spellcheck="false" />
      <button id="analyze-btn" onclick="analyze()">&#9654; SCAN</button>
    </div>
    <div id="error-box"></div>

    <div class="sector-divider">OR BROWSE BY GICS SECTOR</div>

    <div class="sector-browse">
      <div class="sector-browse-label">// SELECT A SECTOR TO VIEW SATELLITE TARGETS //</div>
      <div class="sector-pills">
        <div class="sector-pill" onclick="browseSector('Energy')"><span class="pill-icon">🛢️</span>ENERGY</div>
        <div class="sector-pill" onclick="browseSector('Basic Materials')"><span class="pill-icon">⛏️</span>BASIC MATERIALS</div>
        <div class="sector-pill" onclick="browseSector('Industrials')"><span class="pill-icon">🏭</span>INDUSTRIALS</div>
        <div class="sector-pill" onclick="browseSector('Consumer Cyclical')"><span class="pill-icon">🛍️</span>CONSUMER CYCLICAL</div>
        <div class="sector-pill" onclick="browseSector('Consumer Defensive')"><span class="pill-icon">🛒</span>CONSUMER DEFENSIVE</div>
        <div class="sector-pill" onclick="browseSector('Healthcare')"><span class="pill-icon">🏥</span>HEALTHCARE</div>
        <div class="sector-pill" onclick="browseSector('Financial Services')"><span class="pill-icon">🏦</span>FINANCIAL SERVICES</div>
        <div class="sector-pill" onclick="browseSector('Technology')"><span class="pill-icon">💻</span>TECHNOLOGY</div>
        <div class="sector-pill" onclick="browseSector('Communication Services')"><span class="pill-icon">📡</span>COMMUNICATION SVCS</div>
        <div class="sector-pill" onclick="browseSector('Utilities')"><span class="pill-icon">⚡</span>UTILITIES</div>
        <div class="sector-pill" onclick="browseSector('Real Estate')"><span class="pill-icon">🏢</span>REAL ESTATE</div>
      </div>
    </div>
  </div>

  <div id="loading">
    <div class="loader-orbit"></div>
    <div style="letter-spacing:0.12em">ACQUIRING SATELLITE TARGETS…</div>
  </div>

  <div id="results"></div>

</div>

<footer>SATINTEL v3.0 &nbsp;|&nbsp; ESRI WORLD IMAGERY · SENTINEL-2 · OSM &nbsp;|&nbsp; VISUAL ANALYSIS ONLY — NOT FOR TRADING</footer>

<script>
/* ─── MAP REGISTRY ────────────────────────────────────────────────────────── */
const maps = {};   // mapId → { map, layers, current }

/* ─── TILE DEFINITIONS (all free, no API key) ────────────────────────────── */
function makeLayers() {
  return {
    esri: L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19, attribution: 'Esri' }
    ),
    clarity: L.tileLayer(
      'https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 21, attribution: 'Esri Clarity' }
    ),
    osm: L.tileLayer(
      'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      { maxZoom: 19, attribution: 'OSM' }
    ),
    toner: L.tileLayer(
      'https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png',
      { maxZoom: 18, attribution: 'Stadia/Stamen' }
    ),
  };
}

function initMap(id, lat, lon) {
  if (maps[id]) return;
  const el = document.getElementById(id);
  if (!el) return;

  const map = L.map(el, {
    center: [lat, lon], zoom: 17,
    zoomControl: true,
    attributionControl: false,
    dragging: true,
    scrollWheelZoom: false,
    doubleClickZoom: true,
  });

  const layers = makeLayers();
  layers.esri.addTo(map);
  maps[id] = { map, layers, current: 'esri' };

  // Ensure tiles render after DOM paint
  setTimeout(() => map.invalidateSize(), 80);
}

function switchLayer(mapId, key) {
  const reg = maps[mapId];
  if (!reg || reg.current === key) return;
  reg.map.removeLayer(reg.layers[reg.current]);
  reg.layers[key].addTo(reg.map);
  reg.current = key;

  // Update button highlight
  document.querySelectorAll(`[data-mapid="${mapId}"] .layer-btn`).forEach(b => {
    b.classList.toggle('active', b.dataset.layer === key);
  });
}

/* ─── ANALYZE ─────────────────────────────────────────────────────────────── */
document.getElementById('ticker-input')
  .addEventListener('keydown', e => { if (e.key === 'Enter') analyze(); });

async function analyze() {
  const ticker = document.getElementById('ticker-input').value.trim().toUpperCase();
  if (!ticker) { shake(document.getElementById('ticker-input')); return; }

  const btn     = document.getElementById('analyze-btn');
  const loading = document.getElementById('loading');
  const results = document.getElementById('results');
  const errBox  = document.getElementById('error-box');

  btn.disabled = true;
  loading.style.display = 'block';
  results.style.display = 'none';
  errBox.style.display  = 'none';
  Object.keys(maps).forEach(k => delete maps[k]);

  try {
    const res  = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker })
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || 'Unknown error');
    render(data);
  } catch(err) {
    errBox.textContent = '\u26a0  ' + err.message;
    errBox.style.display = 'block';
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

/* ─── RENDER ──────────────────────────────────────────────────────────────── */
function render(d) {
  const results = document.getElementById('results');

  const statsHtml = [
    d.market_cap !== 'N/A'
      ? `<div class="stat"><div class="stat-val">${x(d.market_cap)}</div><div class="stat-label">Mkt Cap</div></div>` : '',
    d.employees  !== 'N/A'
      ? `<div class="stat"><div class="stat-val" style="font-size:.9rem">${x(d.employees)}</div><div class="stat-label">Employees</div></div>` : '',
    d.sector     !== 'Unknown'
      ? `<div class="stat"><div class="stat-val sm">${x(d.sector)}</div><div class="stat-label">Sector</div></div>` : '',
  ].join('');

  const locsHtml = d.locations.map((loc, i) => {
    const mid = `map-${i}`;
    return `
      <div class="loc-card" data-mapid="${mid}">
        <div class="loc-map-wrap">
          <div id="${mid}" class="loc-map-leaf"></div>
          <div class="map-hud"></div>
          <div class="map-crosshair"></div>
          <div class="map-scan"></div>
          <div class="map-layer-btns">
            <button class="layer-btn active" data-layer="esri"    onclick="switchLayer('${mid}','esri')">&#128752; ESRI SAT</button>
            <button class="layer-btn"        data-layer="clarity" onclick="switchLayer('${mid}','clarity')">&#10024; CLARITY</button>
            <button class="layer-btn"        data-layer="osm"     onclick="switchLayer('${mid}','osm')">&#128506; STREET</button>
            <button class="layer-btn"        data-layer="toner"   onclick="switchLayer('${mid}','toner')">&#9632; B&amp;W</button>
          </div>
        </div>
        <div class="loc-body">
          <div class="loc-name">${x(loc.name)}</div>
          <div class="loc-coords">LAT ${loc.lat.toFixed(4)} &nbsp;/&nbsp; LON ${loc.lon.toFixed(4)} &nbsp;·&nbsp; ZOOM 17</div>
          <div class="source-row">
            <span class="src-badge esri">ESRI WORLD IMAGERY</span>
            <span class="src-badge sent">SENTINEL-2 10M</span>
            <span class="src-badge osm">OSM REFERENCE</span>
          </div>
        </div>
      </div>`;
  }).join('');

  results.innerHTML = `
    <div class="company-card">
      <div class="company-header">
        <div>
          <div class="ticker-badge">${x(d.ticker)}</div>
          <div class="company-name">${x(d.company)}</div>
          <div class="company-meta">${x(d.industry)} &nbsp;&middot;&nbsp; ${x(d.hq_location)}</div>
        </div>
        <div class="company-stats">${statsHtml}</div>
      </div>
      ${d.description ? `<div class="company-desc">${x(d.description)}</div>` : ''}
    </div>

    <div class="section-label">Satellite Monitoring Signals</div>
    <div class="signals-grid">${d.signals.map(s=>`<div class="signal-chip">${x(s)}</div>`).join('')}</div>

    <div class="section-label">Live Satellite Imagery &mdash; ${x(d.sector)} Targets</div>
    <div class="locations-grid">${locsHtml}</div>
  `;

  results.style.display = 'block';
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Boot all Leaflet maps after DOM is in the page
  requestAnimationFrame(() => {
    d.locations.forEach((loc, i) => initMap(`map-${i}`, loc.lat, loc.lon));
  });
}

/* ─── BROWSE BY SECTOR ────────────────────────────────────────────────────── */
async function browseSector(sectorName) {
  // Highlight active pill
  document.querySelectorAll('.sector-pill').forEach(p => {
    p.classList.toggle('active', p.textContent.trim().toLowerCase().includes(sectorName.toLowerCase().split(' ')[0]));
  });

  const loading = document.getElementById('loading');
  const results = document.getElementById('results');
  const errBox  = document.getElementById('error-box');

  loading.style.display = 'block';
  results.style.display = 'none';
  errBox.style.display  = 'none';
  Object.keys(maps).forEach(k => delete maps[k]);

  // Clear ticker input to avoid confusion
  document.getElementById('ticker-input').value = '';

  try {
    const res  = await fetch('/sector', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sector: sectorName })
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || 'Unknown error');
    renderSector(data);
  } catch(err) {
    errBox.textContent = '\u26a0  ' + err.message;
    errBox.style.display = 'block';
  } finally {
    loading.style.display = 'none';
  }
}

function renderSector(d) {
  const results = document.getElementById('results');

  const locsHtml = d.locations.map((loc, i) => {
    const mid = `map-${i}`;
    return `
      <div class="loc-card" data-mapid="${mid}">
        <div class="loc-map-wrap">
          <div id="${mid}" class="loc-map-leaf"></div>
          <div class="map-hud"></div>
          <div class="map-crosshair"></div>
          <div class="map-scan"></div>
          <div class="map-layer-btns">
            <button class="layer-btn active" data-layer="esri"    onclick="switchLayer('${mid}','esri')">&#128752; ESRI SAT</button>
            <button class="layer-btn"        data-layer="clarity" onclick="switchLayer('${mid}','clarity')">&#10024; CLARITY</button>
            <button class="layer-btn"        data-layer="osm"     onclick="switchLayer('${mid}','osm')">&#128506; STREET</button>
            <button class="layer-btn"        data-layer="toner"   onclick="switchLayer('${mid}','toner')">&#9632; B&amp;W</button>
          </div>
        </div>
        <div class="loc-body">
          <div class="loc-name">${x(loc.name)}</div>
          <div class="loc-coords">LAT ${loc.lat.toFixed(4)} &nbsp;/&nbsp; LON ${loc.lon.toFixed(4)} &nbsp;·&nbsp; ZOOM 17</div>
          <div class="source-row">
            <span class="src-badge esri">ESRI WORLD IMAGERY</span>
            <span class="src-badge sent">SENTINEL-2 10M</span>
            <span class="src-badge osm">OSM REFERENCE</span>
          </div>
        </div>
      </div>`;
  }).join('');

  results.innerHTML = `
    <div class="company-card">
      <div class="company-header">
        <div>
          <div class="ticker-badge">GICS SECTOR</div>
          <div class="company-name">${x(d.sector)}</div>
          <div class="company-meta">GICS Classification &nbsp;&middot;&nbsp; ${d.locations.length} Satellite Targets</div>
        </div>
      </div>
    </div>

    <div class="section-label">Satellite Monitoring Signals</div>
    <div class="signals-grid">${d.signals.map(s=>`<div class="signal-chip">${x(s)}</div>`).join('')}</div>

    <div class="section-label">Live Satellite Imagery &mdash; ${x(d.sector)} Targets</div>
    <div class="locations-grid">${locsHtml}</div>
  `;

  results.style.display = 'block';
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });

  requestAnimationFrame(() => {
    d.locations.forEach((loc, i) => initMap(`map-${i}`, loc.lat, loc.lon));
  });
}

/* ─── UTILS ───────────────────────────────────────────────────────────────── */
function x(s) {
  if (typeof s !== 'string') return String(s ?? '');
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function shake(el) {
  el.animate(
    [{transform:'translateX(0)'},{transform:'translateX(-7px)'},{transform:'translateX(7px)'},{transform:'translateX(0)'}],
    {duration:280, iterations:2}
  );
}
</script>
</body>
</html>"""


# ─── Sector → Satellite-monitorable location clusters ──────────────────────
SECTOR_LOCATIONS = {
    "Consumer Defensive": [
        {"name": "Walmart Supercenter (Bentonville, AR)", "lat": 36.3729,  "lon": -94.2088},
        {"name": "Costco Warehouse (Issaquah, WA)",       "lat": 47.5301,  "lon": -122.0326},
        {"name": "Target HQ (Minneapolis, MN)",           "lat": 44.9778,  "lon": -93.2650},
        {"name": "Kroger (Cincinnati, OH)",                "lat": 39.1031,  "lon": -84.5120},
    ],
    "Consumer Cyclical": [
        {"name": "Home Depot HQ (Atlanta, GA)",              "lat": 33.7490, "lon": -84.3880},
        {"name": "AutoNation Dealership (Fort Lauderdale)",  "lat": 26.1224, "lon": -80.1373},
        {"name": "AMC Theater (Leawood, KS)",                "lat": 38.9067, "lon": -94.6328},
        {"name": "Lowe's Distribution (Mooresville, NC)",    "lat": 35.5845, "lon": -80.8098},
    ],
    "Industrials": [
        {"name": "Amazon Fulfillment (Robbinsville, NJ)",  "lat": 40.2115, "lon": -74.5932},
        {"name": "FedEx Hub (Memphis, TN)",                "lat": 35.0423, "lon": -89.9762},
        {"name": "UPS Hub (Louisville, KY)",               "lat": 38.1781, "lon": -85.7360},
        {"name": "Port of Los Angeles (San Pedro, CA)",    "lat": 33.7361, "lon": -118.2922},
    ],
    "Energy": [
        {"name": "Cushing Oil Storage (Cushing, OK)",      "lat": 35.9823, "lon": -96.7665},
        {"name": "Houston Ship Channel (Houston, TX)",     "lat": 29.7372, "lon": -95.2707},
        {"name": "Sabine Pass LNG Terminal (LA)",          "lat": 29.7286, "lon": -93.8700},
        {"name": "Permian Basin Oil Fields (Midland, TX)", "lat": 31.9973, "lon": -102.0779},
    ],
    "Basic Materials": [
        {"name": "BHP Copper Mine (Escondida, Chile)",     "lat": -24.2500, "lon": -69.0700},
        {"name": "Nucor Steel Mill (Charlotte, NC)",       "lat": 35.2271,  "lon": -80.8431},
        {"name": "Barrick Gold Mine (Elko, NV)",           "lat": 40.8324,  "lon": -115.7631},
        {"name": "Albemarle Lithium (Kings Mountain, NC)", "lat": 35.2454,  "lon": -81.3412},
    ],
    "Technology": [
        {"name": "Tesla Gigafactory Texas (Austin, TX)", "lat": 30.2240, "lon": -97.6180},
        {"name": "Apple Park (Cupertino, CA)",           "lat": 37.3346, "lon": -122.0090},
        {"name": "Amazon HQ (Seattle, WA)",              "lat": 47.6159, "lon": -122.3360},
        {"name": "TSMC Fab (Hsinchu, Taiwan)",           "lat": 24.7814, "lon": 120.9969},
    ],
    "Real Estate": [
        {"name": "Simon Mall (Indianapolis, IN)",     "lat": 39.7684, "lon": -86.1581},
        {"name": "Prologis Warehouse (Joliet, IL)",   "lat": 41.5250, "lon": -88.0817},
        {"name": "Public Storage (Glendale, CA)",     "lat": 34.1425, "lon": -118.2551},
        {"name": "CBRE Office Park (Dallas, TX)",     "lat": 32.7767, "lon": -96.7970},
    ],
    "Healthcare": [
        {"name": "J&J Campus (New Brunswick, NJ)", "lat": 40.4870, "lon": -74.4457},
        {"name": "Mayo Clinic (Rochester, MN)",    "lat": 44.0224, "lon": -92.4663},
        {"name": "Cardinal Health DC (Dublin, OH)","lat": 40.0992, "lon": -83.1141},
        {"name": "McKesson HQ (Las Colinas, TX)",  "lat": 32.8709, "lon": -97.0570},
    ],
    "Financial Services": [
        {"name": "NYSE (New York, NY)",              "lat": 40.7069, "lon": -74.0089},
        {"name": "Goldman Sachs HQ (New York, NY)", "lat": 40.7143, "lon": -74.0138},
        {"name": "Berkshire HQ (Omaha, NE)",         "lat": 41.2565, "lon": -95.9345},
        {"name": "JPMorgan HQ (New York, NY)",       "lat": 40.7525, "lon": -73.9773},
    ],
    "Communication Services": [
        {"name": "Google Campus (Mountain View, CA)", "lat": 37.4220, "lon": -122.0841},
        {"name": "Meta HQ (Menlo Park, CA)",          "lat": 37.4845, "lon": -122.1477},
        {"name": "AT&T HQ (Dallas, TX)",              "lat": 32.7813, "lon": -96.7974},
        {"name": "Netflix HQ (Los Gatos, CA)",        "lat": 37.2358, "lon": -121.9624},
    ],
    "Utilities": [
        {"name": "Hoover Dam (Boulder City, NV)",      "lat": 36.0161, "lon": -114.7377},
        {"name": "Duke Energy Plant (Charlotte, NC)",  "lat": 35.2271, "lon": -80.8431},
        {"name": "NextEra Solar Farm (Blythe, CA)",    "lat": 33.6173, "lon": -114.5965},
        {"name": "Constellation Nuclear (Perry, OH)",  "lat": 41.8000, "lon": -81.1434},
    ],
}

DEFAULT_LOCATIONS = [
    {"name": "Port of LA/Long Beach (CA)", "lat": 33.7361, "lon": -118.2922},
    {"name": "Newark Airport Cargo (NJ)",  "lat": 40.6895, "lon": -74.1745},
    {"name": "Chicago O'Hare Cargo (IL)",  "lat": 41.9742, "lon": -87.9073},
    {"name": "Dallas/Fort Worth Hub (TX)", "lat": 32.8998, "lon": -97.0403},
]

SECTOR_SIGNALS = {
    "Consumer Defensive":     ["🅿️ Parking lot occupancy", "🚗 Vehicle count trends", "📦 Loading dock activity"],
    "Consumer Cyclical":      ["🅿️ Parking lot footfall", "🏗️ Construction progress", "🚗 Dealership lot inventory"],
    "Industrials":            ["📦 Container yard density", "🚢 Ship traffic at ports", "🏭 Factory roof heat signature"],
    "Energy":                 ["🛢️ Oil tank shadow volume", "🚢 Tanker traffic", "🔥 Flare activity"],
    "Basic Materials":        ["⛏️ Mine excavation progress", "🏭 Plant steam & smoke", "📦 Stockpile size"],
    "Technology":             ["🏭 Gigafactory expansion", "🅿️ Campus employee count", "🏗️ Data center construction"],
    "Real Estate":            ["🅿️ Mall parking occupancy", "🏗️ Development progress", "🚗 Residential traffic"],
    "Healthcare":             ["🏥 Facility expansion", "🅿️ Hospital lot occupancy", "🏗️ Campus construction"],
    "Financial Services":     ["🏢 Office occupancy patterns", "🏗️ HQ construction", "🚗 Commuter traffic"],
    "Communication Services": ["🏗️ Data center expansion", "📡 Antenna arrays", "🅿️ Campus footfall"],
    "Utilities":              ["☀️ Solar farm output area", "💧 Reservoir water level", "🌬️ Wind turbine arrays"],
}


# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return HTML


@app.route("/analyze", methods=["POST"])
def analyze():
    body = request.get_json(silent=True) or {}
    ticker_symbol = body.get("ticker", "").strip().upper()

    if not ticker_symbol:
        return jsonify({"error": "Ticker symbol is required."}), 400

    try:
        ticker = yf.Ticker(ticker_symbol)
        info   = ticker.info or {}
    except Exception as e:
        return jsonify({"error": f"Could not fetch ticker data: {e}"}), 500

    company_name = info.get("longName") or info.get("shortName") or ""
    if not company_name and not info.get("sector"):
        return jsonify({"error": f"No data found for '{ticker_symbol}'. Check the symbol."}), 404

    company_name = company_name or ticker_symbol
    sector       = info.get("sector")   or "Unknown"
    industry     = info.get("industry") or "Unknown"
    hq_location  = ", ".join(filter(None, [
        info.get("city") or "", info.get("state") or "", info.get("country") or ""
    ]))
    employees    = info.get("fullTimeEmployees") or 0
    market_cap   = info.get("marketCap") or 0
    desc_raw     = info.get("longBusinessSummary") or ""
    description  = (desc_raw[:300] + "…") if len(desc_raw) > 300 else desc_raw

    targets   = SECTOR_LOCATIONS.get(sector, DEFAULT_LOCATIONS)
    signals   = SECTOR_SIGNALS.get(
        sector, ["🛰️ General area activity", "🅿️ Parking patterns", "🚗 Traffic flow"]
    )

    return jsonify({
        "ticker":      ticker_symbol,
        "company":     company_name,
        "sector":      sector,
        "industry":    industry,
        "hq_location": hq_location,
        "employees":   f"{employees:,}" if employees else "N/A",
        "market_cap":  f"${market_cap / 1e9:.1f}B" if market_cap else "N/A",
        "description": description,
        "signals":     signals,
        "locations":   targets,
    })


@app.route("/sector", methods=["POST"])
def sector_browse():
    body = request.get_json(silent=True) or {}
    sector_name = body.get("sector", "").strip()

    if not sector_name:
        return jsonify({"error": "Sector name is required."}), 400

    targets = SECTOR_LOCATIONS.get(sector_name, DEFAULT_LOCATIONS)
    signals = SECTOR_SIGNALS.get(
        sector_name, ["🛰️ General area activity", "🅿️ Parking patterns", "🚗 Traffic flow"]
    )

    if sector_name not in SECTOR_LOCATIONS:
        return jsonify({"error": f"Unknown sector: '{sector_name}'."}), 404

    return jsonify({
        "sector":    sector_name,
        "signals":   signals,
        "locations": targets,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
