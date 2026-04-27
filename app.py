from flask import Flask, render_template_string, jsonify, request, Response
import requests
import threading
import time
import math
import base64
from datetime import datetime, timedelta

app = Flask(__name__)

# ── Token Manager ─────────────────────────────────────────────────────────────
# Credentials from api.py — edit here if they change
_CDSE_USERNAME = "antbsk0@gmail.com"
_CDSE_PASSWORD = "7mK2C=Ysp)PmqE@"
_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
_REFRESH_INTERVAL = 27 * 60   # refresh every 27 min (token valid 30 min)

class TokenManager:
    def __init__(self):
        self.token: str = ""
        self.fetched_at: datetime | None = None
        self.expires_at: datetime | None = None
        self.lock = threading.Lock()
        self._refresh()                       # fetch immediately on startup
        self._start_background_refresh()

    def _refresh(self):
        try:
            resp = requests.post(
                _TOKEN_URL,
                data={
                    "client_id": "cdse-public",
                    "username": _CDSE_USERNAME,
                    "password": _CDSE_PASSWORD,
                    "grant_type": "password",
                },
                timeout=15,
            )
            resp.raise_for_status()
            payload = resp.json()
            with self.lock:
                self.token = payload["access_token"]
                self.fetched_at = datetime.utcnow()
                # Copernicus tokens carry `expires_in` (seconds)
                expires_in = payload.get("expires_in", 1800)
                self.expires_at = self.fetched_at + timedelta(seconds=expires_in)
            print(f"[TokenManager] Token refreshed at {self.fetched_at.strftime('%H:%M:%S')} UTC "
                  f"(expires in {expires_in}s)")
        except Exception as exc:
            print(f"[TokenManager] ERROR refreshing token: {exc}")

    def _start_background_refresh(self):
        def _loop():
            while True:
                time.sleep(_REFRESH_INTERVAL)
                self._refresh()
        t = threading.Thread(target=_loop, daemon=True)
        t.start()

    def get(self) -> str:
        with self.lock:
            return self.token

    def status(self) -> dict:
        with self.lock:
            remaining = None
            if self.expires_at:
                remaining = max(0, int((self.expires_at - datetime.utcnow()).total_seconds()))
            return {
                "fetched_at": self.fetched_at.strftime("%H:%M:%S UTC") if self.fetched_at else "—",
                "expires_at": self.expires_at.strftime("%H:%M:%S UTC") if self.expires_at else "—",
                "remaining_seconds": remaining,
                "token_prefix": self.token[:16] + "…" if self.token else "none",
            }

_token_mgr = TokenManager()

# Compatibility shim so all existing code that reads COPERNICUS_TOKEN still works
def COPERNICUS_TOKEN() -> str:   # noqa: N802 — intentional function-as-constant pattern
    return _token_mgr.get()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SENTINEL EYE — Satellite Viewer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  :root {
    --void: #050810;
    --deep: #0a1020;
    --panel: #0e1628;
    --border: #1a2840;
    --accent: #00e5ff;
    --accent2: #7c3aed;
    --warn: #f59e0b;
    --text: #c8d8f0;
    --muted: #4a6080;
    --success: #10b981;
    --danger: #ef4444;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--void);
    color: var(--text);
    font-family: 'Space Mono', monospace;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* Scanline overlay */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0, 229, 255, 0.015) 2px,
      rgba(0, 229, 255, 0.015) 4px
    );
    pointer-events: none;
    z-index: 9999;
  }

  /* ── HEADER ── */
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    height: 56px;
    background: var(--deep);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
    position: relative;
    z-index: 100;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .logo-icon {
    width: 32px;
    height: 32px;
    border: 2px solid var(--accent);
    border-radius: 50%;
    position: relative;
    animation: orbit-spin 6s linear infinite;
  }

  .logo-icon::before {
    content: '';
    position: absolute;
    inset: 4px;
    background: var(--accent);
    border-radius: 50%;
    opacity: 0.3;
  }

  .logo-icon::after {
    content: '';
    position: absolute;
    top: -6px; left: 50%;
    transform: translateX(-50%);
    width: 6px; height: 6px;
    background: var(--accent);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--accent);
  }

  @keyframes orbit-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .logo-text {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 18px;
    letter-spacing: 0.15em;
    color: #fff;
  }

  .logo-text span {
    color: var(--accent);
  }

  .header-status {
    display: flex;
    align-items: center;
    gap: 20px;
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 0.05em;
  }

  .status-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border: 1px solid var(--border);
    border-radius: 20px;
    background: rgba(0,229,255,0.04);
  }

  .status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--success);
    box-shadow: 0 0 6px var(--success);
    animation: pulse-dot 2s ease-in-out infinite;
  }

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .utc-clock {
    font-size: 12px;
    color: var(--accent);
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.05em;
  }

  /* ── MAIN LAYOUT ── */
  .app-body {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  /* ── SIDEBAR ── */
  .sidebar {
    width: 320px;
    flex-shrink: 0;
    background: var(--panel);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    z-index: 50;
  }

  .sidebar-section {
    padding: 16px;
    border-bottom: 1px solid var(--border);
  }

  .section-label {
    font-size: 9px;
    letter-spacing: 0.2em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  /* Search */
  .search-wrap {
    position: relative;
  }

  .search-input {
    width: 100%;
    background: var(--deep);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 10px 40px 10px 14px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    border-radius: 4px;
    outline: none;
    transition: border-color 0.2s;
  }

  .search-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(0,229,255,0.1);
  }

  .search-input::placeholder { color: var(--muted); }

  .search-btn {
    position: absolute;
    right: 0; top: 0; bottom: 0;
    width: 40px;
    background: none;
    border: none;
    color: var(--accent);
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity 0.2s;
  }
  .search-btn:hover { opacity: 0.7; }

  .search-results {
    margin-top: 8px;
    display: none;
    flex-direction: column;
    gap: 2px;
    max-height: 160px;
    overflow-y: auto;
  }

  .search-result-item {
    padding: 8px 12px;
    background: var(--deep);
    border: 1px solid var(--border);
    border-radius: 3px;
    cursor: pointer;
    font-size: 11px;
    color: var(--text);
    transition: border-color 0.15s, background 0.15s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .search-result-item:hover {
    border-color: var(--accent);
    background: rgba(0,229,255,0.05);
    color: var(--accent);
  }

  /* Layer selector */
  .layer-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }

  .layer-btn {
    padding: 8px 10px;
    background: var(--deep);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
    line-height: 1.4;
  }

  .layer-btn.active {
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(0,229,255,0.07);
    box-shadow: 0 0 8px rgba(0,229,255,0.15);
  }

  .layer-btn:hover:not(.active) {
    border-color: var(--muted);
    color: var(--text);
  }

  .layer-name { font-weight: 700; display: block; }
  .layer-desc { color: var(--muted); font-size: 9px; margin-top: 2px; display: block; }
  .layer-btn.active .layer-desc { color: rgba(0,229,255,0.6); }

  /* Date picker */
  .date-row {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .date-input {
    flex: 1;
    background: var(--deep);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 8px 10px;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    border-radius: 4px;
    outline: none;
    transition: border-color 0.2s;
  }

  .date-input:focus { border-color: var(--accent); }
  .date-label { font-size: 9px; color: var(--muted); }

  /* Cloud cover slider */
  .slider-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
  }

  .slider-label { font-size: 10px; color: var(--muted); white-space: nowrap; }
  .slider-val { font-size: 11px; color: var(--accent); min-width: 32px; text-align: right; }

  input[type=range] {
    flex: 1;
    appearance: none;
    height: 3px;
    background: var(--border);
    border-radius: 2px;
    outline: none;
    cursor: pointer;
  }

  input[type=range]::-webkit-slider-thumb {
    appearance: none;
    width: 14px; height: 14px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 6px var(--accent);
    cursor: pointer;
  }

  /* Apply button */
  .apply-btn {
    width: 100%;
    padding: 12px;
    background: linear-gradient(135deg, var(--accent2), var(--accent));
    border: none;
    border-radius: 4px;
    color: #fff;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.15em;
    cursor: pointer;
    transition: opacity 0.2s, transform 0.1s;
    text-transform: uppercase;
  }

  .apply-btn:hover { opacity: 0.9; }
  .apply-btn:active { transform: scale(0.98); }
  .apply-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  /* Info panel */
  .info-panel {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
  }

  .info-card {
    background: var(--deep);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 12px;
    margin-bottom: 10px;
  }

  .info-card-label {
    font-size: 9px;
    letter-spacing: 0.15em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 6px;
  }

  .info-card-value {
    font-size: 12px;
    color: var(--text);
    word-break: break-all;
  }

  .info-card-value.highlight { color: var(--accent); }

  .log-area {
    font-size: 10px;
    color: var(--muted);
    line-height: 1.8;
    max-height: 120px;
    overflow-y: auto;
  }

  .log-entry { padding: 2px 0; }
  .log-entry.ok { color: var(--success); }
  .log-entry.err { color: var(--danger); }
  .log-entry.info { color: var(--accent); }

  /* ── MAP ── */
  .map-wrap {
    flex: 1;
    position: relative;
    overflow: hidden;
  }

  #map {
    width: 100%;
    height: 100%;
  }

  /* Leaflet dark override */
  .leaflet-container {
    background: var(--void) !important;
  }

  .leaflet-control-zoom {
    border: 1px solid var(--border) !important;
    background: var(--panel) !important;
  }

  .leaflet-control-zoom a {
    background: var(--panel) !important;
    color: var(--accent) !important;
    border-color: var(--border) !important;
    font-family: 'Space Mono', monospace !important;
    line-height: 26px !important;
  }

  .leaflet-control-zoom a:hover {
    background: var(--deep) !important;
  }

  /* Map overlay coords */
  .map-coords {
    position: absolute;
    bottom: 12px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(10,16,32,0.85);
    border: 1px solid var(--border);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 11px;
    color: var(--muted);
    pointer-events: none;
    z-index: 1000;
    backdrop-filter: blur(4px);
    letter-spacing: 0.05em;
  }

  .map-coords span { color: var(--accent); }

  /* Loading overlay */
  .map-loading {
    position: absolute;
    inset: 0;
    background: rgba(5,8,16,0.75);
    display: none;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 16px;
    z-index: 500;
    backdrop-filter: blur(2px);
  }

  .map-loading.show { display: flex; }

  .loader-ring {
    width: 48px; height: 48px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .loader-text {
    font-size: 11px;
    color: var(--accent);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    animation: blink 1.2s ease-in-out infinite;
  }

  @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

  /* Toast */
  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 10px 18px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 9999;
    display: none;
    border: 1px solid;
    font-family: 'Space Mono', monospace;
    animation: toast-in 0.3s ease;
  }

  @keyframes toast-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .toast.ok { background: rgba(16,185,129,0.15); border-color: var(--success); color: var(--success); }
  .toast.err { background: rgba(239,68,68,0.15); border-color: var(--danger); color: var(--danger); }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--deep); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon"></div>
    <div class="logo-text">SENTINEL<span>EYE</span></div>
  </div>
  <div class="header-status">
    <div class="status-pill">
      <div class="status-dot"></div>
      <span>COPERNICUS LIVE</span>
    </div>
    <div class="status-pill" id="tokenPill" title="Token auto-refreshes every 27 min">
      <div class="status-dot" id="tokenDot" style="background:var(--success);box-shadow:0 0 6px var(--success)"></div>
      <span>TOKEN&nbsp;<span id="tokenCountdown">--:--</span></span>
    </div>
    <div class="utc-clock" id="utcClock">--:--:-- UTC</div>
  </div>
</header>

<div class="app-body">
  <div class="sidebar">

    <!-- SEARCH -->
    <div class="sidebar-section">
      <div class="section-label">Location Search</div>
      <div class="search-wrap">
        <input class="search-input" id="searchInput" type="text"
               placeholder="Search city, country, coordinates…"
               autocomplete="off">
        <button class="search-btn" onclick="searchLocation()">⌕</button>
      </div>
      <div class="search-results" id="searchResults"></div>
    </div>

    <!-- LAYER -->
    <div class="sidebar-section">
      <div class="section-label">Satellite Layer</div>
      <div class="layer-grid">
        <button class="layer-btn active" data-layer="TRUE-COLOR" onclick="selectLayer(this)">
          <span class="layer-name">TRUE COLOR</span>
          <span class="layer-desc">Natural RGB</span>
        </button>
        <button class="layer-btn" data-layer="FALSE-COLOR" onclick="selectLayer(this)">
          <span class="layer-name">FALSE COLOR</span>
          <span class="layer-desc">NIR vegetation</span>
        </button>
        <button class="layer-btn" data-layer="NDVI" onclick="selectLayer(this)">
          <span class="layer-name">NDVI</span>
          <span class="layer-desc">Vegetation index</span>
        </button>
        <button class="layer-btn" data-layer="MOISTURE-INDEX" onclick="selectLayer(this)">
          <span class="layer-name">MOISTURE</span>
          <span class="layer-desc">Soil/water index</span>
        </button>
        <button class="layer-btn" data-layer="SWIR" onclick="selectLayer(this)">
          <span class="layer-name">SWIR</span>
          <span class="layer-desc">Shortwave IR</span>
        </button>
        <button class="layer-btn" data-layer="GEOLOGY" onclick="selectLayer(this)">
          <span class="layer-name">GEOLOGY</span>
          <span class="layer-desc">Geological bands</span>
        </button>
      </div>
    </div>

    <!-- DATE RANGE -->
    <div class="sidebar-section">
      <div class="section-label">Date Range</div>
      <div style="display:flex;flex-direction:column;gap:8px;">
        <div>
          <div class="date-label" style="margin-bottom:4px;">FROM</div>
          <input class="date-input" type="date" id="dateFrom">
        </div>
        <div>
          <div class="date-label" style="margin-bottom:4px;">TO</div>
          <input class="date-input" type="date" id="dateTo">
        </div>
      </div>
      <div class="slider-row">
        <span class="slider-label">Cloud cover ≤</span>
        <input type="range" id="cloudSlider" min="0" max="100" value="30"
               oninput="document.getElementById('cloudVal').textContent=this.value+'%'">
        <span class="slider-val" id="cloudVal">30%</span>
      </div>
      <div style="margin-top:12px;">
        <button class="apply-btn" id="applyBtn" onclick="applyLayer()">
          ⬡ LOAD SATELLITE DATA
        </button>
      </div>
    </div>

    <!-- INFO -->
    <div class="info-panel">
      <div class="section-label" style="font-size:9px;letter-spacing:.2em;color:var(--muted);text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:8px;">
        Session Log <span style="flex:1;height:1px;background:var(--border);display:block;"></span>
      </div>
      <div class="info-card">
        <div class="info-card-label">Active Layer</div>
        <div class="info-card-value highlight" id="infoLayer">TRUE-COLOR</div>
      </div>
      <div class="info-card">
        <div class="info-card-label">View Center</div>
        <div class="info-card-value" id="infoCenter">20.00°N, 77.00°E</div>
      </div>
      <div class="info-card">
        <div class="info-card-label">Zoom Level</div>
        <div class="info-card-value" id="infoZoom">5</div>
      </div>
      <div class="log-area" id="logArea">
        <div class="log-entry info">▸ System initialised</div>
        <div class="log-entry info">▸ Copernicus token loaded</div>
      </div>
    </div>

  </div>

  <!-- MAP -->
  <div class="map-wrap">
    <div id="map"></div>
    <div class="map-loading" id="mapLoading">
      <div class="loader-ring"></div>
      <div class="loader-text">FETCHING SATELLITE DATA…</div>
    </div>
    <div class="map-coords" id="mapCoords">
      LAT <span id="coordLat">--</span> &nbsp;|&nbsp; LON <span id="coordLon">--</span>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
// ── State ──────────────────────────────────────────────────────────────────
let map, sentinelLayer = null;
let currentLayer = 'TRUE-COLOR';

// ── UTC Clock ──────────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  const h = String(now.getUTCHours()).padStart(2,'0');
  const m = String(now.getUTCMinutes()).padStart(2,'0');
  const s = String(now.getUTCSeconds()).padStart(2,'0');
  document.getElementById('utcClock').textContent = h+':'+m+':'+s+' UTC';
}
setInterval(updateClock, 1000);
updateClock();

// ── Token Countdown ────────────────────────────────────────────────────────
async function updateTokenStatus() {
  try {
    const res = await fetch('/token-status');
    const d = await res.json();
    const sec = d.remaining_seconds;
    if (sec === null || sec === undefined) return;
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    document.getElementById('tokenCountdown').textContent = m + ':' + s;
    const dot = document.getElementById('tokenDot');
    if (sec < 120) {
      dot.style.background = 'var(--danger)';
      dot.style.boxShadow = '0 0 6px var(--danger)';
    } else if (sec < 300) {
      dot.style.background = 'var(--warn)';
      dot.style.boxShadow = '0 0 6px var(--warn)';
    } else {
      dot.style.background = 'var(--success)';
      dot.style.boxShadow = '0 0 6px var(--success)';
    }
  } catch(e) { /* silent */ }
}
updateTokenStatus();
setInterval(updateTokenStatus, 30000);

// ── Default Dates ──────────────────────────────────────────────────────────
(function setDates() {
  const today = new Date();
  const prior = new Date(today); prior.setDate(prior.getDate() - 30);
  const fmt = d => d.toISOString().split('T')[0];
  document.getElementById('dateTo').value = fmt(today);
  document.getElementById('dateFrom').value = fmt(prior);
})();

// ── Map Init ───────────────────────────────────────────────────────────────
map = L.map('map', {
  center: [20, 77],
  zoom: 5,
  zoomControl: true,
  attributionControl: false
});

// Dark base tiles
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  maxZoom: 19
}).addTo(map);

map.on('mousemove', e => {
  document.getElementById('coordLat').textContent = e.latlng.lat.toFixed(4) + '°';
  document.getElementById('coordLon').textContent = e.latlng.lng.toFixed(4) + '°';
});

map.on('moveend', () => {
  const c = map.getCenter();
  document.getElementById('infoCenter').textContent =
    Math.abs(c.lat).toFixed(4)+'°'+(c.lat>=0?'N':'S')+', '+
    Math.abs(c.lng).toFixed(4)+'°'+(c.lng>=0?'E':'W');
  document.getElementById('infoZoom').textContent = map.getZoom();
});

// ── Log ────────────────────────────────────────────────────────────────────
function log(msg, type='info') {
  const area = document.getElementById('logArea');
  const el = document.createElement('div');
  el.className = 'log-entry ' + type;
  const icons = {info:'▸', ok:'✓', err:'✕'};
  el.textContent = (icons[type]||'▸') + ' ' + msg;
  area.appendChild(el);
  area.scrollTop = area.scrollHeight;
}

// ── Toast ──────────────────────────────────────────────────────────────────
function showToast(msg, type='ok') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast ' + type;
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3500);
}

// ── Layer Selection ────────────────────────────────────────────────────────
function selectLayer(btn) {
  document.querySelectorAll('.layer-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentLayer = btn.dataset.layer;
  document.getElementById('infoLayer').textContent = currentLayer;
  log('Layer selected: '+currentLayer);
}

// ── Build WMS URL via backend ──────────────────────────────────────────────
async function applyLayer() {
  const dateFrom = document.getElementById('dateFrom').value;
  const dateTo   = document.getElementById('dateTo').value;
  const cloud    = document.getElementById('cloudSlider').value;
  const btn      = document.getElementById('applyBtn');

  if (!dateFrom || !dateTo) { showToast('Set date range first', 'err'); return; }

  btn.disabled = true;
  document.getElementById('mapLoading').classList.add('show');
  log('Requesting '+currentLayer+' imagery…');

  try {
    // Remove existing satellite layer
    if (sentinelLayer) { map.removeLayer(sentinelLayer); sentinelLayer = null; }

    const bounds = map.getBounds();
    const params = new URLSearchParams({
      layer: currentLayer,
      dateFrom, dateTo,
      cloud,
      minLon: bounds.getWest(),
      minLat: bounds.getSouth(),
      maxLon: bounds.getEast(),
      maxLat: bounds.getNorth()
    });

    const res = await fetch('/wms-url?' + params);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Backend error');

    sentinelLayer = L.tileLayer.wms(data.wms_url, {
      layers: data.layer_id,
      format: 'image/jpeg',
      transparent: false,
      version: '1.3.0',
      time: data.time_range,
      maxcc: cloud,
      opacity: 0.95,
      maxZoom: 18,
      headers: { Authorization: 'Bearer ' + data.token }
    });

    // Since Leaflet WMS doesn't support custom headers natively,
    // we use the tile URL with the token embedded via the backend proxy
    sentinelLayer = L.tileLayer(data.tile_url + '&z={z}&x={x}&y={y}', {
      maxZoom: 18,
      opacity: 0.9,
      tileSize: 256,
      attribution: '© Copernicus/ESA'
    });

    sentinelLayer.addTo(map);
    log('Layer loaded: '+currentLayer, 'ok');
    showToast('Satellite layer loaded ✓');

    document.getElementById('infoLayer').textContent = currentLayer + ' ✓';

  } catch(err) {
    log('Error: '+err.message, 'err');
    showToast('Failed: '+err.message, 'err');

    // Fallback: load WMS directly from Sentinel Hub public endpoint
    loadDirectWMS(dateFrom, dateTo, cloud);
  } finally {
    btn.disabled = false;
    document.getElementById('mapLoading').classList.remove('show');
  }
}

// ── Direct WMS fallback (Sentinel Hub WMS with token) ─────────────────────
function loadDirectWMS(dateFrom, dateTo, cloud) {
  if (sentinelLayer) { map.removeLayer(sentinelLayer); sentinelLayer = null; }

  // Use Copernicus Browser WMS endpoint
  const wmsBase = 'https://sh.dataspace.copernicus.eu/ogc/wms/TOKEN_PLACEHOLDER';
  // We'll fetch via our backend proxy which injects the auth header
  const proxyUrl = '/proxy-tile?layer='+currentLayer+
    '&dateFrom='+dateFrom+'&dateTo='+dateTo+'&cloud='+cloud+
    '&z={z}&x={x}&y={y}';

  sentinelLayer = L.tileLayer(proxyUrl, {
    maxZoom: 18,
    opacity: 0.9,
    tileSize: 256,
    attribution: '© Copernicus/ESA'
  });

  sentinelLayer.addTo(map);
  log('Fallback WMS layer active', 'ok');
}

// ── Location Search ────────────────────────────────────────────────────────
let searchTimeout;
document.getElementById('searchInput').addEventListener('input', function() {
  clearTimeout(searchTimeout);
  const q = this.value.trim();
  if (q.length < 3) { hideResults(); return; }
  searchTimeout = setTimeout(() => geocode(q), 400);
});

document.getElementById('searchInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') { clearTimeout(searchTimeout); searchLocation(); }
  if (e.key === 'Escape') hideResults();
});

async function searchLocation() {
  const q = document.getElementById('searchInput').value.trim();
  if (!q) return;
  geocode(q);
}

async function geocode(q) {
  try {
    const res = await fetch('/geocode?q='+encodeURIComponent(q));
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    const container = document.getElementById('searchResults');
    container.innerHTML = '';
    container.style.display = 'flex';

    if (!data.results || data.results.length === 0) {
      container.innerHTML = '<div class="search-result-item" style="color:var(--muted)">No results found</div>';
      return;
    }

    data.results.slice(0, 5).forEach(r => {
      const el = document.createElement('div');
      el.className = 'search-result-item';
      el.textContent = r.display_name;
      el.title = r.display_name;
      el.onclick = () => {
        map.flyTo([parseFloat(r.lat), parseFloat(r.lon)], 12, { duration: 1.5 });
        document.getElementById('searchInput').value = r.display_name.split(',')[0];
        hideResults();
        log('Navigated to: '+r.display_name.split(',')[0]);
      };
      container.appendChild(el);
    });
  } catch(err) {
    log('Geocode error: '+err.message, 'err');
  }
}

function hideResults() {
  const c = document.getElementById('searchResults');
  c.style.display = 'none';
}

document.addEventListener('click', e => {
  if (!e.target.closest('.search-wrap')) hideResults();
});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/token-status")
def token_status():
    """Returns live token metadata for the UI countdown."""
    return jsonify(_token_mgr.status())


@app.route("/geocode")
def geocode():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"error": "No query"}), 400
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 5, "addressdetails": 0},
            headers={"User-Agent": "SentinelEye/1.0"},
            timeout=8,
        )
        r.raise_for_status()
        return jsonify({"results": r.json()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/wms-url")
def wms_url():
    """Returns WMS endpoint info for the frontend to use."""
    layer = request.args.get("layer", "TRUE-COLOR")
    date_from = request.args.get("dateFrom")
    date_to = request.args.get("dateTo")
    cloud = request.args.get("cloud", "30")

    # Map friendly names to Sentinel Hub layer names
    layer_map = {
        "TRUE-COLOR": "TRUE-COLOR",
        "FALSE-COLOR": "FALSE-COLOR",
        "NDVI": "NDVI",
        "MOISTURE-INDEX": "MOISTURE-INDEX",
        "SWIR": "SWIR",
        "GEOLOGY": "GEOLOGY",
    }

    sh_layer = layer_map.get(layer, "TRUE-COLOR")

    # Copernicus Sentinel Hub WMS base URL
    wms_base = "https://sh.dataspace.copernicus.eu/ogc/wms/1635b3a9-a94a-4e94-b82b-f1dda13ab684"

    return jsonify(
        {
            "wms_url": wms_base,
            "layer_id": sh_layer,
            "time_range": f"{date_from}/{date_to}",
            "token": COPERNICUS_TOKEN(),
            "tile_url": f"/proxy-tile?layer={sh_layer}&dateFrom={date_from}&dateTo={date_to}&cloud={cloud}",
        }
    )


# ── Evalscripts for each layer (Sentinel Hub Process API) ─────────────────────
# These are JavaScript snippets executed server-side by Sentinel Hub to render
# each band combination. No instance UUID needed — Bearer token is sufficient.
EVALSCRIPTS = {
    "TRUE-COLOR": """
//VERSION=3
function setup(){return{input:["B04","B03","B02","dataMask"],output:{bands:4}}}
function evaluatePixel(s){
  return[3.5*s.B04,3.5*s.B03,3.5*s.B02,s.dataMask];
}""",
    "FALSE-COLOR": """
//VERSION=3
function setup(){return{input:["B08","B04","B03","dataMask"],output:{bands:4}}}
function evaluatePixel(s){
  return[2.5*s.B08,2.5*s.B04,2.5*s.B03,s.dataMask];
}""",
    "NDVI": """
//VERSION=3
function setup(){return{input:["B08","B04","dataMask"],output:{bands:4}}}
function evaluatePixel(s){
  var ndvi=(s.B08-s.B04)/(s.B08+s.B04);
  var r,g,b;
  if(ndvi<-0.2){r=0.75;g=0.75;b=0.75;}
  else if(ndvi<0){r=0.86;g=0.86;b=0.86;}
  else if(ndvi<0.1){r=1;g=0.98;b=0.8;}
  else if(ndvi<0.2){r=0.78;g=0.88;b=0.52;}
  else if(ndvi<0.3){r=0.36;g=0.73;b=0.36;}
  else if(ndvi<0.4){r=0.13;g=0.55;b=0.13;}
  else{r=0;g=0.39;b=0;}
  return[r,g,b,s.dataMask];
}""",
    "MOISTURE-INDEX": """
//VERSION=3
function setup(){return{input:["B8A","B11","dataMask"],output:{bands:4}}}
function evaluatePixel(s){
  var mi=(s.B8A-s.B11)/(s.B8A+s.B11);
  var r,g,b;
  if(mi<-0.8){r=0.5;g=0;b=0;}
  else if(mi<-0.4){r=1;g=0;b=0;}
  else if(mi<0){r=1;g=0.6;b=0;}
  else if(mi<0.2){r=1;g=1;b=0.6;}
  else if(mi<0.4){r=0.6;g=0.8;b=1;}
  else{r=0;g=0.4;b=1;}
  return[r,g,b,s.dataMask];
}""",
    "SWIR": """
//VERSION=3
function setup(){return{input:["B12","B8A","B04","dataMask"],output:{bands:4}}}
function evaluatePixel(s){
  return[2.5*s.B12,2.5*s.B8A,2.5*s.B04,s.dataMask];
}""",
    "GEOLOGY": """
//VERSION=3
function setup(){return{input:["B12","B11","B02","dataMask"],output:{bands:4}}}
function evaluatePixel(s){
  return[2.5*s.B12,2.5*s.B11,2.5*s.B02,s.dataMask];
}""",
}

# ── Tile helpers ───────────────────────────────────────────────────────────────
def xyz_to_wgs84_bbox(z, x, y):
    """Return (min_lon, min_lat, max_lon, max_lat) for an XYZ tile."""
    z, x, y = int(z), int(x), int(y)
    n = 2 ** z
    lon_w = x / n * 360.0 - 180.0
    lon_e = (x + 1) / n * 360.0 - 180.0
    lat_n = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_s = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return lon_w, lat_s, lon_e, lat_n


def xyz_to_epsg3857(z, x, y):
    """Return (minX, minY, maxX, maxY) in EPSG:3857 metres for an XYZ tile."""
    z, x, y = int(z), int(x), int(y)
    R = 6378137.0
    n = 2 ** z
    left  = x / n * 2 * math.pi * R - math.pi * R
    right = (x + 1) / n * 2 * math.pi * R - math.pi * R
    top = math.log(math.tan(math.pi / 4 + math.atan(math.sinh(math.pi * (1 - 2 * y / n))) / 2)) * R
    bot = math.log(math.tan(math.pi / 4 + math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))) / 2)) * R
    return left, bot, right, top


EMPTY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQ"
    "AABjkB6QAAAABJRU5ErkJggg=="
)


@app.route("/proxy-tile")
def proxy_tile():
    """
    Fetch a Sentinel-2 L2A tile via the Sentinel Hub Process API.

    The Process API (api/v1/process) works with a plain Bearer token —
    no configuration instance UUID required. It accepts an evalscript
    that defines the band maths + output colour mapping.
    """
    layer     = request.args.get("layer", "TRUE-COLOR")
    date_from = request.args.get("dateFrom")
    date_to   = request.args.get("dateTo")
    cloud     = request.args.get("cloud", "30")
    z         = request.args.get("z", "5")
    x         = request.args.get("x", "0")
    y         = request.args.get("y", "0")

    evalscript = EVALSCRIPTS.get(layer, EVALSCRIPTS["TRUE-COLOR"])
    lon_w, lat_s, lon_e, lat_n = xyz_to_wgs84_bbox(z, x, y)

    # Sentinel Hub Process API endpoint for Copernicus Data Space
    PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

    payload = {
        "input": {
            "bounds": {
                "bbox": [lon_w, lat_s, lon_e, lat_n],
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": f"{date_from}T00:00:00Z",
                        "to":   f"{date_to}T23:59:59Z",
                    },
                    "maxCloudCoverage": int(cloud),
                    "mosaickingOrder": "leastCC",   # use least-cloudy scene
                },
            }],
        },
        "output": {
            "width":  512,
            "height": 512,
            "responses": [{"identifier": "default", "format": {"type": "image/png"}}],
        },
        "evalscript": evalscript,
    }

    try:
        hdrs = {
            "Authorization": f"Bearer {COPERNICUS_TOKEN()}",
            "Content-Type":  "application/json",
            "Accept":        "image/png",
        }
        r = requests.post(PROCESS_URL, json=payload, headers=hdrs, timeout=30)
        ct = r.headers.get("Content-Type", "")

        if r.status_code == 200 and "image" in ct:
            return Response(r.content, content_type=ct)

        print(f"[proxy-tile] {r.status_code} layer={layer} z={z} x={x} y={y}")
        print(f"[proxy-tile] body: {r.text[:500]}")
        return Response(EMPTY_PNG, content_type="image/png")

    except Exception as exc:
        print(f"[proxy-tile] exception: {exc}")
        return Response(EMPTY_PNG, content_type="image/png")


@app.route("/debug-tile")
def debug_tile():
    """
    Visit http://localhost:5000/debug-tile to verify Copernicus connectivity.
    Returns JSON showing the API response for one test tile over India.
    """
    from datetime import date, timedelta
    today     = date.today().isoformat()
    month_ago = (date.today() - timedelta(days=30)).isoformat()

    # Test tile: z=8, x=180, y=110 — covers southern India
    lon_w, lat_s, lon_e, lat_n = xyz_to_wgs84_bbox(8, 180, 110)

    payload = {
        "input": {
            "bounds": {
                "bbox": [lon_w, lat_s, lon_e, lat_n],
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {"from": f"{month_ago}T00:00:00Z", "to": f"{today}T23:59:59Z"},
                    "maxCloudCoverage": 50,
                    "mosaickingOrder": "leastCC",
                },
            }],
        },
        "output": {
            "width": 256, "height": 256,
            "responses": [{"identifier": "default", "format": {"type": "image/png"}}],
        },
        "evalscript": EVALSCRIPTS["TRUE-COLOR"],
    }

    hdrs = {
        "Authorization": f"Bearer {COPERNICUS_TOKEN()}",
        "Content-Type":  "application/json",
        "Accept":        "image/png",
    }
    try:
        r = requests.post("https://sh.dataspace.copernicus.eu/api/v1/process",
                          json=payload, headers=hdrs, timeout=20)
        return jsonify({
            "status":         r.status_code,
            "content_type":   r.headers.get("Content-Type"),
            "content_length": len(r.content),
            "body_preview":   r.text[:600] if "image" not in r.headers.get("Content-Type","") else "<<IMAGE OK>>",
            "token_ok":       COPERNICUS_TOKEN() != "",
            "bbox_tested":    [lon_w, lat_s, lon_e, lat_n],
        })
    except Exception as exc:
        return jsonify({"error": str(exc)})


if __name__ == "__main__":
    print("="*55)
    print("  SENTINEL EYE — Satellite Viewer")
    print("  Token auto-refresh: every 27 min (daemon thread)")
    print("  Open http://localhost:5000 in your browser")
    print("="*55)
    app.run(debug=True, host="0.0.0.0", port=5000)
