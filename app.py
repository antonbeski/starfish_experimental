"""
SATINTEL — Satellite Intelligence Platform
Sector-only browsing | GICS 11 sectors | 12 expanded footage targets per sector
Vercel-compatible | Inline satellite maps via Leaflet.js (no API keys)
"""

from flask import Flask, request, jsonify

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
    max-width:1400px; margin:0 auto 32px;
  }
  .header-inner {
    display:flex; align-items:center; justify-content:space-between;
    border-bottom:1px solid var(--border); padding-bottom:18px;
  }
  .logo { display:flex; align-items:center; gap:14px; }
  .logo-icon {
    width:42px; height:42px; border:2px solid var(--accent); border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    box-shadow:var(--glow); animation:spin 10s linear infinite; position:relative;
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
  .container { position:relative; z-index:1; max-width:1400px; margin:0 auto; padding:0 28px 60px; }

  /* SECTOR PANEL */
  .sector-panel { margin-bottom:40px; }
  .panel-eyebrow {
    font-family:'Orbitron',monospace; font-size:0.65rem;
    letter-spacing:0.3em; color:var(--text-dim); text-transform:uppercase;
    margin-bottom:8px; text-align:center;
  }
  .panel-headline {
    font-size:2rem; font-weight:700; line-height:1.1; margin-bottom:6px; text-align:center;
    background:linear-gradient(135deg, var(--text) 0%, var(--accent) 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  }
  .panel-desc { color:var(--text-dim); font-size:0.95rem; font-weight:300; margin-bottom:26px; text-align:center; }

  .gics-grid {
    display:grid;
    grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
    gap:10px;
  }
  .gics-card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:5px; padding:16px 18px;
    cursor:pointer; transition:all 0.22s;
    display:flex; flex-direction:column; gap:6px;
    position:relative; overflow:hidden;
  }
  .gics-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity:0; transition:opacity 0.22s;
  }
  .gics-card:hover::before, .gics-card.active::before { opacity:1; }
  .gics-card:hover, .gics-card.active {
    border-color:var(--accent); background:rgba(0,212,255,0.06);
    transform:translateY(-2px);
    box-shadow:0 8px 28px rgba(0,0,0,0.4), var(--glow);
  }
  .gics-icon { font-size:1.5rem; line-height:1; }
  .gics-name {
    font-family:'Orbitron',monospace; font-size:0.58rem;
    letter-spacing:0.1em; color:var(--accent); text-transform:uppercase; font-weight:700;
  }
  .gics-count { font-family:'Share Tech Mono',monospace; font-size:0.6rem; color:var(--text-dim); }
  .gics-card.active .gics-count { color:var(--accent2); }

  /* LOADING */
  #loading {
    display:none; text-align:center; padding:48px;
    font-family:'Share Tech Mono',monospace; color:var(--accent);
    font-size:0.82rem; letter-spacing:0.1em;
  }
  .loader-orbit {
    width:48px; height:48px; border:2px solid var(--border); border-top-color:var(--accent);
    border-radius:50%; animation:spin 0.8s linear infinite; margin:0 auto 14px;
  }

  /* RESULTS */
  #results { display:none; animation:fadeUp 0.5s ease-out; }
  @keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }

  .sector-header-card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:6px; padding:22px 28px; margin-bottom:26px;
    position:relative; overflow:hidden;
    display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px;
  }
  .sector-header-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg, transparent, var(--accent), transparent);
  }
  .sector-title-group { display:flex; align-items:center; gap:16px; }
  .sector-big-icon { font-size:2.4rem; line-height:1; }
  .sector-badge {
    font-family:'Share Tech Mono',monospace; font-size:0.6rem;
    letter-spacing:0.2em; color:var(--accent); background:rgba(0,212,255,0.08);
    border:1px solid rgba(0,212,255,0.3); padding:3px 10px; border-radius:2px;
    margin-bottom:6px; display:inline-block;
  }
  .sector-name-big { font-size:1.7rem; font-weight:700; color:var(--text); }
  .sector-sub { font-size:0.88rem; color:var(--text-dim); margin-top:3px; }
  .sector-stats { display:flex; gap:24px; flex-wrap:wrap; }
  .stat { text-align:center; }
  .stat-val {
    font-family:'Orbitron',monospace; font-size:1.1rem; font-weight:700;
    color:var(--accent2); text-shadow:var(--glow2);
  }
  .stat-label {
    font-size:0.65rem; color:var(--text-dim); letter-spacing:0.1em;
    text-transform:uppercase; font-family:'Share Tech Mono',monospace; margin-top:2px;
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
    grid-template-columns:repeat(auto-fill, minmax(310px, 1fr));
    gap:18px; margin-bottom:36px;
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
  .loc-map-wrap { width:100%; height:200px; position:relative; background:#061018; }
  .loc-map-leaf { width:100%; height:100%; }

  .map-hud { position:absolute; inset:0; pointer-events:none; z-index:498; }
  .map-hud::before {
    content:''; position:absolute; top:8px; left:8px; width:20px; height:20px;
    border-top:1px solid rgba(0,212,255,0.55); border-left:1px solid rgba(0,212,255,0.55);
  }
  .map-hud::after {
    content:''; position:absolute; bottom:8px; right:8px; width:20px; height:20px;
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

  .map-layer-btns {
    position:absolute; top:8px; right:8px; z-index:500;
    display:flex; flex-direction:column; gap:4px;
  }
  .layer-btn {
    background:rgba(3,10,15,0.88); border:1px solid var(--border);
    color:var(--text-dim); font-family:'Share Tech Mono',monospace;
    font-size:0.55rem; letter-spacing:0.07em; padding:4px 8px;
    cursor:pointer; border-radius:2px; transition:all 0.15s; white-space:nowrap;
  }
  .layer-btn.active, .layer-btn:hover {
    border-color:var(--accent); color:var(--accent); background:rgba(0,212,255,0.1);
  }

  .loc-body { padding:12px 14px 14px; }
  .loc-name { font-size:0.9rem; font-weight:600; color:var(--text); margin-bottom:4px; line-height:1.3; }
  .loc-tag {
    font-family:'Share Tech Mono',monospace; font-size:0.58rem;
    color:var(--accent3); letter-spacing:0.06em; margin-bottom:6px;
    display:inline-block; background:rgba(255,107,53,0.1);
    border:1px solid rgba(255,107,53,0.25); padding:2px 7px; border-radius:2px;
  }
  .loc-coords {
    font-family:'Share Tech Mono',monospace; font-size:0.6rem;
    color:var(--text-dim); margin-bottom:9px; letter-spacing:0.04em;
  }
  .source-row { display:flex; gap:5px; flex-wrap:wrap; }
  .src-badge {
    font-family:'Share Tech Mono',monospace; font-size:0.57rem;
    letter-spacing:0.06em; padding:2px 7px; border-radius:2px; border:1px solid;
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
  .leaflet-control-attribution { display:none !important; }

  @media (max-width:700px) {
    .header-inner { flex-direction:column; gap:12px; }
    .panel-headline { font-size:1.5rem; }
    .gics-grid { grid-template-columns: repeat(2, 1fr); }
    .locations-grid { grid-template-columns:1fr; }
    .sector-header-card { flex-direction:column; }
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

  <div class="sector-panel">
    <div class="panel-eyebrow">// GICS SECTOR SATELLITE MONITOR //</div>
    <div class="panel-headline">Select a Sector — View From Orbit</div>
    <div class="panel-desc">Choose any of the 11 GICS sectors to load all satellite monitoring targets</div>

    <div class="gics-grid" id="gics-grid">
      <div class="gics-card" onclick="browseSector('Energy')" data-sector="Energy">
        <div class="gics-icon">🛢️</div>
        <div class="gics-name">Energy</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Basic Materials')" data-sector="Basic Materials">
        <div class="gics-icon">⛏️</div>
        <div class="gics-name">Basic Materials</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Industrials')" data-sector="Industrials">
        <div class="gics-icon">🏭</div>
        <div class="gics-name">Industrials</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Consumer Cyclical')" data-sector="Consumer Cyclical">
        <div class="gics-icon">🛍️</div>
        <div class="gics-name">Consumer Cyclical</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Consumer Defensive')" data-sector="Consumer Defensive">
        <div class="gics-icon">🛒</div>
        <div class="gics-name">Consumer Defensive</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Healthcare')" data-sector="Healthcare">
        <div class="gics-icon">🏥</div>
        <div class="gics-name">Healthcare</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Financial Services')" data-sector="Financial Services">
        <div class="gics-icon">🏦</div>
        <div class="gics-name">Financial Services</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Technology')" data-sector="Technology">
        <div class="gics-icon">💻</div>
        <div class="gics-name">Technology</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Communication Services')" data-sector="Communication Services">
        <div class="gics-icon">📡</div>
        <div class="gics-name">Communication Services</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Utilities')" data-sector="Utilities">
        <div class="gics-icon">⚡</div>
        <div class="gics-name">Utilities</div>
        <div class="gics-count">12 targets</div>
      </div>
      <div class="gics-card" onclick="browseSector('Real Estate')" data-sector="Real Estate">
        <div class="gics-icon">🏢</div>
        <div class="gics-name">Real Estate</div>
        <div class="gics-count">12 targets</div>
      </div>
    </div>
  </div>

  <div id="loading">
    <div class="loader-orbit"></div>
    <div style="letter-spacing:0.12em">ACQUIRING SATELLITE TARGETS…</div>
  </div>

  <div id="results"></div>

</div>

<footer>SATINTEL v4.0 &nbsp;|&nbsp; ESRI WORLD IMAGERY · SENTINEL-2 · OSM &nbsp;|&nbsp; GICS 11-SECTOR COVERAGE &nbsp;|&nbsp; VISUAL ANALYSIS ONLY</footer>

<script>
const maps = {};

function makeLayers() {
  return {
    esri: L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19 }
    ),
    clarity: L.tileLayer(
      'https://clarity.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 21 }
    ),
    osm: L.tileLayer(
      'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      { maxZoom: 19 }
    ),
    toner: L.tileLayer(
      'https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png',
      { maxZoom: 18 }
    ),
  };
}

function initMap(id, lat, lon) {
  if (maps[id]) return;
  const el = document.getElementById(id);
  if (!el) return;
  const map = L.map(el, {
    center: [lat, lon], zoom: 16,
    zoomControl: true, attributionControl: false,
    dragging: true, scrollWheelZoom: false, doubleClickZoom: true,
  });
  const layers = makeLayers();
  layers.esri.addTo(map);
  maps[id] = { map, layers, current: 'esri' };
  setTimeout(() => map.invalidateSize(), 80);
}

function switchLayer(mapId, key) {
  const reg = maps[mapId];
  if (!reg || reg.current === key) return;
  reg.map.removeLayer(reg.layers[reg.current]);
  reg.layers[key].addTo(reg.map);
  reg.current = key;
  document.querySelectorAll(`[data-mapid="${mapId}"] .layer-btn`).forEach(b => {
    b.classList.toggle('active', b.dataset.layer === key);
  });
}

const SECTOR_ICONS = {
  'Energy':'🛢️','Basic Materials':'⛏️','Industrials':'🏭',
  'Consumer Cyclical':'🛍️','Consumer Defensive':'🛒','Healthcare':'🏥',
  'Financial Services':'🏦','Technology':'💻','Communication Services':'📡',
  'Utilities':'⚡','Real Estate':'🏢'
};

async function browseSector(sectorName) {
  document.querySelectorAll('.gics-card').forEach(c => {
    c.classList.toggle('active', c.dataset.sector === sectorName);
  });

  const loading = document.getElementById('loading');
  const results = document.getElementById('results');

  loading.style.display = 'block';
  results.style.display = 'none';
  Object.keys(maps).forEach(k => { try { maps[k].map.remove(); } catch(e){} delete maps[k]; });

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
    results.innerHTML = `<div style="text-align:center;padding:40px;font-family:'Share Tech Mono',monospace;color:var(--danger);font-size:0.8rem;">&#9888; ${x(err.message)}</div>`;
    results.style.display = 'block';
  } finally {
    loading.style.display = 'none';
  }
}

function renderSector(d) {
  const results = document.getElementById('results');
  const icon = SECTOR_ICONS[d.sector] || '🛰️';

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
          ${loc.tag ? `<div class="loc-tag">${x(loc.tag)}</div>` : ''}
          <div class="loc-coords">LAT ${loc.lat.toFixed(4)} &nbsp;/&nbsp; LON ${loc.lon.toFixed(4)}</div>
          <div class="source-row">
            <span class="src-badge esri">ESRI WORLD</span>
            <span class="src-badge sent">SENTINEL-2</span>
            <span class="src-badge osm">OSM</span>
          </div>
        </div>
      </div>`;
  }).join('');

  results.innerHTML = `
    <div class="sector-header-card">
      <div class="sector-title-group">
        <div class="sector-big-icon">${icon}</div>
        <div>
          <div class="sector-badge">GICS SECTOR</div>
          <div class="sector-name-big">${x(d.sector)}</div>
          <div class="sector-sub">Global Coverage &nbsp;&middot;&nbsp; ${d.locations.length} Satellite Targets Active</div>
        </div>
      </div>
      <div class="sector-stats">
        <div class="stat"><div class="stat-val">${d.locations.length}</div><div class="stat-label">Targets</div></div>
        <div class="stat"><div class="stat-val">${d.signals.length}</div><div class="stat-label">Signals</div></div>
        <div class="stat"><div class="stat-val">LIVE</div><div class="stat-label">Feed</div></div>
      </div>
    </div>

    <div class="section-label">Satellite Monitoring Signals</div>
    <div class="signals-grid">${d.signals.map(s=>`<div class="signal-chip">${x(s)}</div>`).join('')}</div>

    <div class="section-label">Live Satellite Imagery &mdash; ${x(d.sector)} (${d.locations.length} Targets)</div>
    <div class="locations-grid">${locsHtml}</div>
  `;

  results.style.display = 'block';
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });

  requestAnimationFrame(() => {
    d.locations.forEach((loc, i) => initMap(`map-${i}`, loc.lat, loc.lon));
  });
}

function x(s) {
  if (typeof s !== 'string') return String(s ?? '');
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body>
</html>"""


# ─── 12 LOCATIONS PER GICS SECTOR ─────────────────────────────────────────────
SECTOR_LOCATIONS = {
    "Energy": [
        {"name": "Cushing Oil Storage Hub (Cushing, OK)",          "tag": "CRUDE STORAGE",   "lat": 35.9823,  "lon": -96.7665},
        {"name": "Houston Ship Channel (Houston, TX)",              "tag": "PETROCHEMICAL",   "lat": 29.7372,  "lon": -95.2707},
        {"name": "Sabine Pass LNG Terminal (Cameron, LA)",          "tag": "LNG EXPORT",      "lat": 29.7286,  "lon": -93.8700},
        {"name": "Permian Basin Oil Fields (Midland, TX)",          "tag": "OIL PRODUCTION",  "lat": 31.9973,  "lon": -102.0779},
        {"name": "Port Arthur Refinery (Port Arthur, TX)",          "tag": "REFINING",        "lat": 29.8988,  "lon": -93.9321},
        {"name": "Eagle Ford Shale Play (DeWitt County, TX)",       "tag": "SHALE PLAY",      "lat": 28.9500,  "lon": -97.8500},
        {"name": "Bakken Oil Fields (Williston, ND)",               "tag": "SHALE PLAY",      "lat": 48.1470,  "lon": -103.6180},
        {"name": "Freeport LNG Terminal (Freeport, TX)",            "tag": "LNG EXPORT",      "lat": 28.9400,  "lon": -95.3600},
        {"name": "Canadian Oil Sands (Fort McMurray, AB)",          "tag": "OIL SANDS",       "lat": 56.7267,  "lon": -111.3790},
        {"name": "Motiva Refinery (Port Arthur, TX)",               "tag": "REFINING",        "lat": 29.8760,  "lon": -93.8960},
        {"name": "Ras Tanura Oil Terminal (Saudi Arabia)",          "tag": "CRUDE EXPORT",    "lat": 26.6447,  "lon": 50.1592},
        {"name": "Rotterdam Oil Terminal (Netherlands)",            "tag": "IMPORT HUB",      "lat": 51.9179,  "lon": 4.0571},
    ],
    "Basic Materials": [
        {"name": "BHP Escondida Copper Mine (Chile)",               "tag": "COPPER MINE",     "lat": -24.2500, "lon": -69.0700},
        {"name": "Nucor Steel Mill (Charlotte, NC)",                "tag": "STEEL MILL",      "lat": 35.2271,  "lon": -80.8431},
        {"name": "Barrick Goldstrike Mine (Elko, NV)",              "tag": "GOLD MINE",       "lat": 40.8324,  "lon": -115.7631},
        {"name": "Albemarle Lithium (Kings Mountain, NC)",          "tag": "LITHIUM MINING",  "lat": 35.2454,  "lon": -81.3412},
        {"name": "Rio Tinto Pilbara Iron Ore (W. Australia)",       "tag": "IRON ORE",        "lat": -22.7000, "lon": 117.7500},
        {"name": "Freeport-McMoRan Grasberg Mine (Indonesia)",      "tag": "COPPER/GOLD",     "lat": -4.0570,  "lon": 137.1170},
        {"name": "Potash Corp Mine (Esterhazy, SK, Canada)",        "tag": "POTASH MINE",     "lat": 50.6481,  "lon": -102.0818},
        {"name": "U.S. Steel Gary Works (Gary, IN)",                "tag": "STEEL MILL",      "lat": 41.6031,  "lon": -87.3320},
        {"name": "Codelco Chuquicamata Mine (Chile)",               "tag": "COPPER MINE",     "lat": -22.3160, "lon": -68.9170},
        {"name": "Newmont Boddington Mine (W. Australia)",          "tag": "GOLD MINE",       "lat": -32.7833, "lon": 116.3833},
        {"name": "Vale Carajás Iron Ore (Pará, Brazil)",            "tag": "IRON ORE",        "lat": -6.0667,  "lon": -50.1333},
        {"name": "Mosaic Phosphate Plant (Riverview, FL)",          "tag": "PHOSPHATE",       "lat": 27.8417,  "lon": -82.3343},
    ],
    "Industrials": [
        {"name": "Amazon Fulfillment Center (Robbinsville, NJ)",    "tag": "E-COMMERCE DC",  "lat": 40.2115,  "lon": -74.5932},
        {"name": "FedEx World Hub (Memphis, TN)",                   "tag": "AIR CARGO HUB",  "lat": 35.0423,  "lon": -89.9762},
        {"name": "UPS Worldport (Louisville, KY)",                  "tag": "AIR CARGO HUB",  "lat": 38.1781,  "lon": -85.7360},
        {"name": "Port of Los Angeles (San Pedro, CA)",             "tag": "CONTAINER PORT",  "lat": 33.7361,  "lon": -118.2922},
        {"name": "Port of Long Beach (Long Beach, CA)",             "tag": "CONTAINER PORT",  "lat": 33.7536,  "lon": -118.2160},
        {"name": "Boeing Everett Factory (Everett, WA)",            "tag": "AIRCRAFT MFG",   "lat": 47.9209,  "lon": -122.2615},
        {"name": "Caterpillar Plant (Peoria, IL)",                  "tag": "HEAVY MACHINERY","lat": 40.6936,  "lon": -89.5890},
        {"name": "Port of Rotterdam (Netherlands)",                 "tag": "CONTAINER PORT",  "lat": 51.9179,  "lon": 4.4806},
        {"name": "Norfolk Southern Intermodal (Atlanta, GA)",       "tag": "RAIL INTERMODAL", "lat": 33.7490,  "lon": -84.3880},
        {"name": "Lockheed Skunk Works (Palmdale, CA)",             "tag": "AEROSPACE MFG",  "lat": 34.6291,  "lon": -118.0838},
        {"name": "GE Aviation Plant (Cincinnati, OH)",              "tag": "ENGINE MFG",     "lat": 39.1031,  "lon": -84.5120},
        {"name": "Port of Shanghai Yangshan (China)",               "tag": "CONTAINER PORT",  "lat": 30.6204,  "lon": 122.0525},
    ],
    "Consumer Cyclical": [
        {"name": "Home Depot HQ (Atlanta, GA)",                     "tag": "HOME IMPROVEMENT","lat": 33.7490,  "lon": -84.3880},
        {"name": "Amazon HQ2 (Arlington, VA)",                      "tag": "E-COMMERCE",      "lat": 38.8899,  "lon": -77.0847},
        {"name": "AutoNation Dealership (Fort Lauderdale, FL)",      "tag": "AUTO DEALER",     "lat": 26.1224,  "lon": -80.1373},
        {"name": "Lowe's Distribution (Mooresville, NC)",           "tag": "HOME IMPROVEMENT","lat": 35.5845,  "lon": -80.8098},
        {"name": "Ford River Rouge Complex (Dearborn, MI)",         "tag": "AUTO ASSEMBLY",   "lat": 42.3016,  "lon": -83.1583},
        {"name": "Tesla Gigafactory Texas (Austin, TX)",            "tag": "EV ASSEMBLY",     "lat": 30.2240,  "lon": -97.6180},
        {"name": "Toyota Plant (Georgetown, KY)",                   "tag": "AUTO ASSEMBLY",   "lat": 38.2098,  "lon": -84.5555},
        {"name": "MGM Grand (Las Vegas, NV)",                       "tag": "GAMING/LEISURE",  "lat": 36.1024,  "lon": -115.1701},
        {"name": "Carnival Port of Miami (Miami, FL)",              "tag": "CRUISE TERMINAL", "lat": 25.7742,  "lon": -80.1700},
        {"name": "Marriott HQ Campus (Bethesda, MD)",               "tag": "HOSPITALITY",     "lat": 38.9850,  "lon": -77.0947},
        {"name": "IKEA Distribution (Perryville, MD)",              "tag": "RETAIL DIST.",    "lat": 39.5601,  "lon": -76.0722},
        {"name": "Wynn Resorts (Las Vegas, NV)",                    "tag": "GAMING/LEISURE",  "lat": 36.1264,  "lon": -115.1661},
    ],
    "Consumer Defensive": [
        {"name": "Walmart HQ (Bentonville, AR)",                    "tag": "RETAIL HQ",       "lat": 36.3729,  "lon": -94.2088},
        {"name": "Costco Warehouse (Issaquah, WA)",                 "tag": "WAREHOUSE RETAIL","lat": 47.5301,  "lon": -122.0326},
        {"name": "Procter & Gamble HQ (Cincinnati, OH)",            "tag": "CPG MFG",         "lat": 39.0968,  "lon": -84.5120},
        {"name": "Kroger Distribution Center (Cincinnati, OH)",     "tag": "GROCERY DC",      "lat": 39.1031,  "lon": -84.5120},
        {"name": "Tyson Foods Plant (Springdale, AR)",              "tag": "FOOD PROCESSING", "lat": 36.1867,  "lon": -94.1288},
        {"name": "Anheuser-Busch Brewery (St. Louis, MO)",          "tag": "BEVERAGE MFG",    "lat": 38.5942,  "lon": -90.2107},
        {"name": "Coca-Cola HQ (Atlanta, GA)",                      "tag": "BEVERAGE HQ",     "lat": 33.7937,  "lon": -84.3863},
        {"name": "Archer Daniels Midland (Decatur, IL)",            "tag": "GRAIN PROCESSING","lat": 39.8428,  "lon": -88.9548},
        {"name": "Cargill Grain Terminal (New Orleans, LA)",        "tag": "GRAIN EXPORT",    "lat": 29.9511,  "lon": -90.0715},
        {"name": "PepsiCo HQ (Purchase, NY)",                       "tag": "BEVERAGE HQ",     "lat": 41.0534,  "lon": -73.7162},
        {"name": "Altria Tobacco Plant (Richmond, VA)",             "tag": "TOBACCO MFG",     "lat": 37.5407,  "lon": -77.4360},
        {"name": "General Mills Plant (Minneapolis, MN)",           "tag": "FOOD MFG",        "lat": 44.9778,  "lon": -93.2650},
    ],
    "Healthcare": [
        {"name": "Johnson & Johnson Campus (New Brunswick, NJ)",    "tag": "PHARMA HQ",       "lat": 40.4870,  "lon": -74.4457},
        {"name": "Mayo Clinic (Rochester, MN)",                     "tag": "MEDICAL CENTER",  "lat": 44.0224,  "lon": -92.4663},
        {"name": "Cardinal Health DC (Dublin, OH)",                 "tag": "PHARMA DISTRIB.", "lat": 40.0992,  "lon": -83.1141},
        {"name": "McKesson HQ (Las Colinas, TX)",                   "tag": "PHARMA DISTRIB.", "lat": 32.8709,  "lon": -97.0570},
        {"name": "Pfizer Research Campus (Groton, CT)",             "tag": "DRUG RESEARCH",   "lat": 41.3554,  "lon": -72.0754},
        {"name": "Merck Plant (Rahway, NJ)",                        "tag": "PHARMA MFG",      "lat": 40.6082,  "lon": -74.2774},
        {"name": "Cleveland Clinic (Cleveland, OH)",                "tag": "MEDICAL CENTER",  "lat": 41.5021,  "lon": -81.6209},
        {"name": "Abbott Labs (Abbott Park, IL)",                   "tag": "MEDTECH MFG",     "lat": 42.2842,  "lon": -87.9300},
        {"name": "Boston Scientific (Marlborough, MA)",             "tag": "MEDTECH MFG",     "lat": 42.3487,  "lon": -71.5298},
        {"name": "AstraZeneca Campus (Gaithersburg, MD)",           "tag": "BIOPHARMA",       "lat": 39.1318,  "lon": -77.2219},
        {"name": "Eli Lilly Plant (Indianapolis, IN)",              "tag": "PHARMA MFG",      "lat": 39.7908,  "lon": -86.1467},
        {"name": "Johns Hopkins Medical (Baltimore, MD)",           "tag": "MEDICAL CENTER",  "lat": 39.2974,  "lon": -76.5928},
    ],
    "Financial Services": [
        {"name": "NYSE — Wall Street (New York, NY)",               "tag": "STOCK EXCHANGE",  "lat": 40.7069,  "lon": -74.0089},
        {"name": "Goldman Sachs HQ (New York, NY)",                 "tag": "INVESTMENT BANK", "lat": 40.7143,  "lon": -74.0138},
        {"name": "Berkshire Hathaway HQ (Omaha, NE)",              "tag": "CONGLOMERATE",    "lat": 41.2565,  "lon": -95.9345},
        {"name": "JPMorgan Chase HQ (New York, NY)",                "tag": "MEGABANK",        "lat": 40.7525,  "lon": -73.9773},
        {"name": "Bank of America HQ (Charlotte, NC)",              "tag": "MEGABANK",        "lat": 35.2271,  "lon": -80.8431},
        {"name": "Citadel HQ (Chicago, IL)",                        "tag": "HEDGE FUND",      "lat": 41.8827,  "lon": -87.6261},
        {"name": "Visa HQ (Foster City, CA)",                       "tag": "PAYMENTS",        "lat": 37.5541,  "lon": -122.2760},
        {"name": "CME Group (Chicago, IL)",                         "tag": "FUTURES EXCHANGE","lat": 41.8827,  "lon": -87.6344},
        {"name": "Fidelity Investments (Boston, MA)",               "tag": "ASSET MGMT",      "lat": 42.3584,  "lon": -71.0598},
        {"name": "Wells Fargo HQ (San Francisco, CA)",              "tag": "MEGABANK",        "lat": 37.7929,  "lon": -122.3969},
        {"name": "Blackstone HQ (New York, NY)",                    "tag": "PRIVATE EQUITY",  "lat": 40.7614,  "lon": -73.9776},
        {"name": "London Stock Exchange (London, UK)",              "tag": "STOCK EXCHANGE",  "lat": 51.5156,  "lon": -0.0977},
    ],
    "Technology": [
        {"name": "Apple Park (Cupertino, CA)",                      "tag": "TECH HQ",         "lat": 37.3346,  "lon": -122.0090},
        {"name": "Googleplex (Mountain View, CA)",                  "tag": "TECH HQ",         "lat": 37.4220,  "lon": -122.0841},
        {"name": "Microsoft Campus (Redmond, WA)",                  "tag": "TECH HQ",         "lat": 47.6423,  "lon": -122.1391},
        {"name": "TSMC Fab 18 (Tainan, Taiwan)",                    "tag": "CHIP FAB",        "lat": 22.9908,  "lon": 120.2133},
        {"name": "NVIDIA HQ (Santa Clara, CA)",                     "tag": "GPU DESIGN",      "lat": 37.3688,  "lon": -121.9689},
        {"name": "Intel Fab (Chandler, AZ)",                        "tag": "CHIP FAB",        "lat": 33.3062,  "lon": -111.8413},
        {"name": "Samsung Austin Fab (Austin, TX)",                 "tag": "CHIP FAB",        "lat": 30.4515,  "lon": -97.6120},
        {"name": "Amazon AWS Data Center (Ashburn, VA)",            "tag": "CLOUD DC",        "lat": 39.0437,  "lon": -77.4875},
        {"name": "Meta Data Center (Prineville, OR)",               "tag": "CLOUD DC",        "lat": 44.3049,  "lon": -120.8340},
        {"name": "Tesla Gigafactory Nevada (Sparks, NV)",           "tag": "BATTERY MFG",     "lat": 39.5374,  "lon": -119.4408},
        {"name": "ASML HQ (Veldhoven, Netherlands)",                "tag": "CHIP EQUIPMENT",  "lat": 51.4003,  "lon": 5.4190},
        {"name": "Foxconn Zhengzhou (China)",                       "tag": "CONTRACT MFG",    "lat": 34.7460,  "lon": 113.6253},
    ],
    "Communication Services": [
        {"name": "Googleplex (Mountain View, CA)",                  "tag": "SEARCH/AD",       "lat": 37.4220,  "lon": -122.0841},
        {"name": "Meta HQ (Menlo Park, CA)",                        "tag": "SOCIAL MEDIA",    "lat": 37.4845,  "lon": -122.1477},
        {"name": "AT&T HQ (Dallas, TX)",                            "tag": "TELECOM",         "lat": 32.7813,  "lon": -96.7974},
        {"name": "Netflix HQ (Los Gatos, CA)",                      "tag": "STREAMING",       "lat": 37.2358,  "lon": -121.9624},
        {"name": "Comcast HQ (Philadelphia, PA)",                   "tag": "CABLE/MEDIA",     "lat": 39.9526,  "lon": -75.1652},
        {"name": "Disney Studios (Burbank, CA)",                    "tag": "MEDIA/CONTENT",   "lat": 34.1575,  "lon": -118.3267},
        {"name": "Verizon HQ (Basking Ridge, NJ)",                  "tag": "TELECOM",         "lat": 40.6862,  "lon": -74.5311},
        {"name": "T-Mobile HQ (Bellevue, WA)",                      "tag": "TELECOM",         "lat": 47.6152,  "lon": -122.1944},
        {"name": "Intelsat Satellite Farm (Lyles, TN)",             "tag": "SATELLITE COMM",  "lat": 35.6951,  "lon": -87.4294},
        {"name": "Warner Bros. Studios (Burbank, CA)",              "tag": "MEDIA/CONTENT",   "lat": 34.1548,  "lon": -118.3373},
        {"name": "SpaceX Starlink (Boca Chica, TX)",                "tag": "SATELLITE COMM",  "lat": 25.9971,  "lon": -97.1553},
        {"name": "YouTube Data Center (The Dalles, OR)",            "tag": "CLOUD DC",        "lat": 45.5940,  "lon": -121.1790},
    ],
    "Utilities": [
        {"name": "Hoover Dam (Boulder City, NV)",                   "tag": "HYDRO POWER",     "lat": 36.0161,  "lon": -114.7377},
        {"name": "Duke Energy McGuire Nuclear (Cornelius, NC)",     "tag": "NUCLEAR POWER",   "lat": 35.4327,  "lon": -80.9479},
        {"name": "NextEra Solar Farm (Blythe, CA)",                 "tag": "SOLAR FARM",      "lat": 33.6173,  "lon": -114.5965},
        {"name": "Constellation Nuclear (Perry, OH)",               "tag": "NUCLEAR POWER",   "lat": 41.8000,  "lon": -81.1434},
        {"name": "Topaz Solar Farm (San Luis Obispo, CA)",          "tag": "SOLAR FARM",      "lat": 35.3600,  "lon": -120.0700},
        {"name": "Alta Wind Energy Center (Tehachapi, CA)",         "tag": "WIND FARM",       "lat": 34.9500,  "lon": -118.5500},
        {"name": "Robert Moses Niagara Plant (Lewiston, NY)",       "tag": "HYDRO POWER",     "lat": 43.1723,  "lon": -79.0490},
        {"name": "Glen Canyon Dam (Page, AZ)",                      "tag": "HYDRO POWER",     "lat": 36.9388,  "lon": -111.4838},
        {"name": "Hornsdale Wind Farm (S. Australia)",              "tag": "WIND + BATTERY",  "lat": -33.0670, "lon": 138.0010},
        {"name": "Palo Verde Nuclear Plant (Tonopah, AZ)",          "tag": "NUCLEAR POWER",   "lat": 33.3889,  "lon": -112.8625},
        {"name": "Walney Offshore Wind (Irish Sea, UK)",            "tag": "OFFSHORE WIND",   "lat": 54.0500,  "lon": -3.5667},
        {"name": "Gemasolar Thermosolar Plant (Seville, Spain)",    "tag": "SOLAR THERMAL",   "lat": 37.5600,  "lon": -5.3300},
    ],
    "Real Estate": [
        {"name": "Mall of America — Simon (Bloomington, MN)",       "tag": "RETAIL REIT",     "lat": 44.8549,  "lon": -93.2422},
        {"name": "Prologis Warehouse (Joliet, IL)",                 "tag": "INDUSTRIAL REIT", "lat": 41.5250,  "lon": -88.0817},
        {"name": "Public Storage (Glendale, CA)",                   "tag": "STORAGE REIT",    "lat": 34.1425,  "lon": -118.2551},
        {"name": "Equinix Data Center (Ashburn, VA)",               "tag": "DATA CENTER REIT","lat": 39.0437,  "lon": -77.4875},
        {"name": "Welltower Senior Care (Toledo, OH)",              "tag": "HEALTHCARE REIT", "lat": 41.6529,  "lon": -83.5379},
        {"name": "American Tower HQ (Boston, MA)",                  "tag": "CELL TOWER REIT", "lat": 42.3601,  "lon": -71.0589},
        {"name": "SBA Communications (Boca Raton, FL)",            "tag": "CELL TOWER REIT", "lat": 26.3683,  "lon": -80.1289},
        {"name": "Realty Income (San Diego, CA)",                   "tag": "RETAIL REIT",     "lat": 32.7157,  "lon": -117.1611},
        {"name": "Boston Properties Prudential (Boston, MA)",       "tag": "OFFICE REIT",     "lat": 42.3471,  "lon": -71.0824},
        {"name": "Crown Castle Tower (Houston, TX)",                "tag": "CELL TOWER REIT", "lat": 29.7604,  "lon": -95.3698},
        {"name": "Ventas Senior Housing (Chicago, IL)",             "tag": "HEALTHCARE REIT", "lat": 41.8827,  "lon": -87.6233},
        {"name": "Iron Mountain Data Center (Manassas, VA)",        "tag": "DATA CENTER REIT","lat": 38.7509,  "lon": -77.4752},
    ],
}

SECTOR_SIGNALS = {
    "Energy": [
        "🛢️ Oil tank shadow volume analysis", "🚢 Tanker traffic & fleet positioning",
        "🔥 Flare intensity & burn-off detection", "🏗️ Rig count & drilling activity",
        "🌡️ Pipeline thermal signatures", "📦 Refinery throughput estimation",
    ],
    "Basic Materials": [
        "⛏️ Mine pit excavation progress", "🏭 Plant steam & smoke plume analysis",
        "📦 Stockpile volume estimation", "🚛 Haul truck count & activity",
        "🌿 Tailings pond level monitoring", "🏗️ Processing facility expansion",
    ],
    "Industrials": [
        "📦 Container yard density & flow", "🚢 Ship traffic & berth occupancy",
        "🏭 Factory roof heat signature", "✈️ Air cargo apron utilization",
        "🚛 Truck dwell time at docks", "🏗️ Facility construction progress",
    ],
    "Consumer Cyclical": [
        "🅿️ Parking lot footfall & occupancy", "🏗️ Construction & expansion progress",
        "🚗 Dealership lot inventory count", "🛳️ Cruise ship berthing activity",
        "🏨 Hotel parking & occupancy proxy", "🏬 Retail strip foot traffic",
    ],
    "Consumer Defensive": [
        "🅿️ Store parking lot occupancy", "🚗 Vehicle count & dwell trends",
        "📦 Loading dock & trailer activity", "🌾 Grain silo & storage levels",
        "🏭 Food processing plant activity", "🚛 Distribution center truck flow",
    ],
    "Healthcare": [
        "🏥 Hospital parking & facility occupancy", "🏗️ Campus construction & expansion",
        "🚑 Emergency bay utilization", "📦 Pharma distribution center activity",
        "🧪 Research facility thermal signatures", "🚛 Medical supply chain flow",
    ],
    "Financial Services": [
        "🏢 Office tower occupancy patterns", "🚗 Commuter traffic & parking",
        "🏗️ HQ campus construction progress", "🌆 Central district footfall",
        "📡 Data center antenna arrays", "🔒 Secure facility perimeter monitoring",
    ],
    "Technology": [
        "🏭 Gigafactory expansion tracking", "🅿️ Campus employee count proxy",
        "🏗️ Data center construction progress", "💨 Cooling tower plume & heat output",
        "🚛 Chip equipment delivery tracking", "🔧 Fab cleanroom roof activity",
    ],
    "Communication Services": [
        "📡 Antenna array density mapping", "🏗️ Data center expansion progress",
        "🅿️ Campus footfall & occupancy", "🛰️ Uplink dish orientation tracking",
        "🚀 Satellite launch facility activity", "🏢 Studio lot utilization",
    ],
    "Utilities": [
        "☀️ Solar panel array output area", "💧 Reservoir & dam water level",
        "🌬️ Wind turbine blade activity", "☢️ Nuclear cooling tower plume",
        "⚡ Transmission line corridor monitoring", "🔥 Power plant stack emissions",
    ],
    "Real Estate": [
        "🅿️ Mall & retail parking occupancy", "🏗️ Development site progress",
        "🚗 Residential traffic & occupancy", "📡 Cell tower & antenna count",
        "🏥 Senior housing facility monitoring", "🏢 Office campus occupancy proxy",
    ],
}


# ── ROUTES ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return HTML


@app.route("/sector", methods=["POST"])
def sector_browse():
    body = request.get_json(silent=True) or {}
    sector_name = body.get("sector", "").strip()

    if not sector_name:
        return jsonify({"error": "Sector name is required."}), 400

    if sector_name not in SECTOR_LOCATIONS:
        return jsonify({"error": f"Unknown sector: '{sector_name}'."}), 404

    return jsonify({
        "sector":    sector_name,
        "signals":   SECTOR_SIGNALS.get(sector_name, []),
        "locations": SECTOR_LOCATIONS[sector_name],
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
