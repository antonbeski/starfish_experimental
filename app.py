"""
Satellite Intelligence Flask App - Single File with Embedded HTML
Vercel-compatible deployment
"""

from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>SATINTEL — Satellite Intelligence Platform</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet" />
<style>
  :root {
    --bg: #030a0f;
    --surface: #071520;
    --surface2: #0a1f30;
    --border: #0e3a5a;
    --accent: #00d4ff;
    --accent2: #00ff9d;
    --accent3: #ff6b35;
    --text: #c8e8f5;
    --text-dim: #4a7a99;
    --danger: #ff3860;
    --glow: 0 0 20px rgba(0, 212, 255, 0.3);
    --glow2: 0 0 20px rgba(0, 255, 157, 0.3);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Rajdhani', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Animated grid background */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  body::after {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at 30% 20%, rgba(0, 80, 120, 0.15) 0%, transparent 60%),
                radial-gradient(ellipse at 70% 80%, rgba(0, 60, 40, 0.1) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
    animation: drift 20s ease-in-out infinite alternate;
  }

  @keyframes drift {
    from { transform: translate(0, 0); }
    to { transform: translate(3%, 2%); }
  }

  .container {
    position: relative;
    z-index: 1;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px 60px;
  }

  /* HEADER */
  header {
    position: relative;
    z-index: 1;
    padding: 32px 24px 0;
    max-width: 1200px;
    margin: 0 auto 40px;
  }

  .header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    padding-bottom: 20px;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .logo-icon {
    width: 44px;
    height: 44px;
    border: 2px solid var(--accent);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--glow);
    animation: rotate-ring 8s linear infinite;
    position: relative;
  }

  .logo-icon::before {
    content: '';
    position: absolute;
    inset: 4px;
    border-radius: 50%;
    border: 1px solid rgba(0,212,255,0.4);
    border-top-color: var(--accent);
    animation: rotate-ring 3s linear infinite reverse;
  }

  .logo-icon svg { width: 20px; height: 20px; color: var(--accent); }

  @keyframes rotate-ring {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .logo-text {
    font-family: 'Orbitron', monospace;
    font-size: 1.5rem;
    font-weight: 900;
    letter-spacing: 0.1em;
    color: var(--accent);
    text-shadow: var(--glow);
  }

  .logo-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.2em;
    text-transform: uppercase;
  }

  .status-bar {
    display: flex;
    gap: 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent2);
    box-shadow: 0 0 8px var(--accent2);
    animation: blink 2s ease-in-out infinite;
  }

  .status-dot.amber { background: var(--accent3); box-shadow: 0 0 8px var(--accent3); }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  /* SEARCH SECTION */
  .search-section {
    text-align: center;
    margin-bottom: 48px;
  }

  .search-title {
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.3em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 12px;
  }

  .search-headline {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 8px;
    background: linear-gradient(135deg, var(--text) 0%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .search-desc {
    color: var(--text-dim);
    font-size: 1rem;
    font-weight: 300;
    margin-bottom: 32px;
  }

  .search-box {
    display: flex;
    gap: 0;
    max-width: 520px;
    margin: 0 auto;
    position: relative;
  }

  .search-box::before {
    content: 'TICKER';
    position: absolute;
    left: 16px;
    top: 50%;
    transform: translateY(-50%);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    color: var(--text-dim);
    z-index: 2;
  }

  #ticker-input {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-right: none;
    color: var(--accent);
    font-family: 'Orbitron', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    padding: 16px 16px 16px 76px;
    outline: none;
    text-transform: uppercase;
    transition: border-color 0.2s, box-shadow 0.2s;
    border-radius: 4px 0 0 4px;
  }

  #ticker-input::placeholder {
    color: var(--text-dim);
    font-size: 0.85rem;
    letter-spacing: 0.1em;
  }

  #ticker-input:focus {
    border-color: var(--accent);
    box-shadow: var(--glow);
  }

  #analyze-btn {
    background: var(--accent);
    color: var(--bg);
    border: none;
    padding: 16px 28px;
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    cursor: pointer;
    transition: all 0.2s;
    border-radius: 0 4px 4px 0;
    white-space: nowrap;
    position: relative;
    overflow: hidden;
  }

  #analyze-btn::after {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(255,255,255,0.1);
    transform: translateX(-100%);
    transition: transform 0.3s;
  }

  #analyze-btn:hover::after { transform: translateX(0); }
  #analyze-btn:hover { box-shadow: var(--glow); }
  #analyze-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  /* LOADING */
  #loading {
    display: none;
    text-align: center;
    padding: 40px;
    font-family: 'Share Tech Mono', monospace;
    color: var(--accent);
    font-size: 0.85rem;
    letter-spacing: 0.1em;
  }

  .loader-orbit {
    width: 50px;
    height: 50px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto 16px;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .loading-text::after {
    content: '...';
    animation: dots 1.5s steps(4, end) infinite;
  }

  @keyframes dots {
    0%, 25% { content: '.'; }
    50% { content: '..'; }
    75%, 100% { content: '...'; }
  }

  /* ERROR */
  #error-box {
    display: none;
    background: rgba(255, 56, 96, 0.1);
    border: 1px solid var(--danger);
    border-radius: 4px;
    padding: 14px 18px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    color: var(--danger);
    max-width: 520px;
    margin: 16px auto 0;
    letter-spacing: 0.05em;
  }

  /* RESULTS */
  #results {
    display: none;
    animation: fadeUp 0.5s ease-out;
  }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* COMPANY CARD */
  .company-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 28px 32px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
  }

  .company-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
  }

  .company-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
    margin-bottom: 20px;
  }

  .company-name-wrap {}

  .ticker-badge {
    display: inline-block;
    font-family: 'Orbitron', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: var(--accent);
    background: rgba(0, 212, 255, 0.08);
    border: 1px solid rgba(0, 212, 255, 0.3);
    padding: 3px 10px;
    border-radius: 2px;
    margin-bottom: 8px;
  }

  .company-name {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.1;
    margin-bottom: 4px;
  }

  .company-meta {
    font-size: 0.9rem;
    color: var(--text-dim);
  }

  .company-stats {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
  }

  .stat {
    text-align: center;
  }

  .stat-val {
    font-family: 'Orbitron', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--accent2);
    text-shadow: var(--glow2);
  }

  .stat-label {
    font-size: 0.7rem;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-family: 'Share Tech Mono', monospace;
    margin-top: 2px;
  }

  .company-desc {
    font-size: 0.95rem;
    color: var(--text-dim);
    line-height: 1.6;
    font-weight: 300;
    border-top: 1px solid var(--border);
    padding-top: 16px;
  }

  /* SIGNALS */
  .section-label {
    font-family: 'Orbitron', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.3em;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  .signals-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 36px;
  }

  .signal-chip {
    background: rgba(0, 255, 157, 0.06);
    border: 1px solid rgba(0, 255, 157, 0.2);
    border-radius: 3px;
    padding: 8px 14px;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--accent2);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* LOCATIONS GRID */
  .locations-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 36px;
  }

  .loc-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
    position: relative;
  }

  .loc-card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
  }

  .loc-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(0,212,255,0.03), transparent);
    pointer-events: none;
  }

  .loc-map {
    width: 100%;
    height: 180px;
    border: none;
    display: block;
    filter: saturate(0.7) brightness(0.85);
    transition: filter 0.3s;
  }

  .loc-card:hover .loc-map {
    filter: saturate(1) brightness(1);
  }

  .loc-body {
    padding: 14px 16px;
  }

  .loc-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 6px;
    line-height: 1.3;
  }

  .loc-coords {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-dim);
    margin-bottom: 12px;
    letter-spacing: 0.05em;
  }

  .loc-links {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }

  .loc-link {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 10px;
    border-radius: 3px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-decoration: none;
    transition: all 0.2s;
    border: 1px solid;
  }

  .loc-link.sentinel {
    color: var(--accent);
    border-color: rgba(0, 212, 255, 0.3);
    background: rgba(0, 212, 255, 0.05);
  }

  .loc-link.sentinel:hover {
    background: rgba(0, 212, 255, 0.15);
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
  }

  .loc-link.usgs {
    color: var(--accent2);
    border-color: rgba(0, 255, 157, 0.3);
    background: rgba(0, 255, 157, 0.05);
  }

  .loc-link.usgs:hover {
    background: rgba(0, 255, 157, 0.15);
    box-shadow: 0 0 10px rgba(0, 255, 157, 0.2);
  }

  .loc-link.gmaps {
    color: var(--accent3);
    border-color: rgba(255, 107, 53, 0.3);
    background: rgba(255, 107, 53, 0.05);
  }

  .loc-link.gmaps:hover {
    background: rgba(255, 107, 53, 0.15);
    box-shadow: 0 0 10px rgba(255, 107, 53, 0.2);
  }

  /* SCAN LINE EFFECT */
  .scanline {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(0,212,255,0.3), transparent);
    animation: scan 6s linear infinite;
    pointer-events: none;
    z-index: 9999;
  }

  @keyframes scan {
    from { top: 0; opacity: 1; }
    to { top: 100vh; opacity: 0; }
  }

  /* FOOTER */
  footer {
    position: relative;
    z-index: 1;
    text-align: center;
    padding: 24px;
    border-top: 1px solid var(--border);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.15em;
    text-transform: uppercase;
  }

  /* CORNER DECORATION */
  .corner-deco {
    position: fixed;
    width: 80px;
    height: 80px;
    pointer-events: none;
    z-index: 2;
    opacity: 0.3;
  }

  .corner-deco.tl { top: 16px; left: 16px; border-top: 1px solid var(--accent); border-left: 1px solid var(--accent); }
  .corner-deco.tr { top: 16px; right: 16px; border-top: 1px solid var(--accent); border-right: 1px solid var(--accent); }
  .corner-deco.bl { bottom: 16px; left: 16px; border-bottom: 1px solid var(--accent); border-left: 1px solid var(--accent); }
  .corner-deco.br { bottom: 16px; right: 16px; border-bottom: 1px solid var(--accent); border-right: 1px solid var(--accent); }

  @media (max-width: 600px) {
    .header-inner { flex-direction: column; gap: 12px; }
    .status-bar { font-size: 0.6rem; gap: 12px; }
    .company-header { flex-direction: column; }
    .search-headline { font-size: 1.6rem; }
    .search-box { flex-direction: column; }
    #ticker-input { border-right: 1px solid var(--border); border-bottom: none; border-radius: 4px 4px 0 0; }
    #analyze-btn { border-radius: 0 0 4px 4px; }
    .locations-grid { grid-template-columns: 1fr; }
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
      <div class="status-item"><span class="status-dot"></span>S2 LIVE</div>
      <div class="status-item"><span class="status-dot"></span>LANDSAT SYNC</div>
      <div class="status-item"><span class="status-dot amber"></span>EO BROWSER</div>
    </div>
  </div>
</header>

<div class="container">

  <div class="search-section">
    <div class="search-title">// EQUITY SATELLITE MONITOR //</div>
    <div class="search-headline">Track Any Stock From Orbit</div>
    <div class="search-desc">Enter a ticker to surface sector-relevant satellite imagery targets</div>
    <div class="search-box">
      <input type="text" id="ticker-input" placeholder="e.g. WMT, AMZN, XOM" maxlength="10" autocomplete="off" spellcheck="false" />
      <button id="analyze-btn" onclick="analyze()">▶ SCAN</button>
    </div>
    <div id="error-box"></div>
  </div>

  <div id="loading">
    <div class="loader-orbit"></div>
    <div class="loading-text">ACQUIRING SATELLITE TARGETS</div>
  </div>

  <div id="results"></div>

</div>

<footer>SATINTEL v2.0 — EO BROWSER · SENTINEL-2 · LANDSAT 8/9 — DATA FOR RESEARCH PURPOSES ONLY</footer>

<script>
const input = document.getElementById('ticker-input');
input.addEventListener('keydown', e => { if (e.key === 'Enter') analyze(); });

async function analyze() {
  const ticker = input.value.trim().toUpperCase();
  if (!ticker) return shake(input);

  const btn = document.getElementById('analyze-btn');
  const loading = document.getElementById('loading');
  const results = document.getElementById('results');
  const errorBox = document.getElementById('error-box');

  btn.disabled = true;
  loading.style.display = 'block';
  results.style.display = 'none';
  errorBox.style.display = 'none';

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker })
    });
    const data = await res.json();

    if (!res.ok || data.error) {
      throw new Error(data.error || 'Unknown error');
    }

    renderResults(data);
  } catch (err) {
    errorBox.textContent = '⚠ ' + err.message;
    errorBox.style.display = 'block';
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

function renderResults(d) {
  const results = document.getElementById('results');

  const statsHtml = [
    d.market_cap !== 'N/A' ? `<div class="stat"><div class="stat-val">${d.market_cap}</div><div class="stat-label">Market Cap</div></div>` : '',
    d.employees !== 'N/A' ? `<div class="stat"><div class="stat-val">${d.employees}</div><div class="stat-label">Employees</div></div>` : '',
    d.sector !== 'Unknown' ? `<div class="stat"><div class="stat-val" style="font-size:0.75rem;letter-spacing:0.05em">${d.sector}</div><div class="stat-label">Sector</div></div>` : '',
  ].join('');

  const signalsHtml = d.signals.map(s =>
    `<div class="signal-chip">${s}</div>`
  ).join('');

  const locsHtml = d.locations.map(loc => `
    <div class="loc-card">
      <iframe class="loc-map"
        loading="lazy"
        referrerpolicy="no-referrer-when-downgrade"
        src="${escHtml(loc.embed_map)}"
        allowfullscreen></iframe>
      <div class="loc-body">
        <div class="loc-name">${escHtml(loc.name)}</div>
        <div class="loc-coords">LAT ${loc.lat.toFixed(4)} / LON ${loc.lon.toFixed(4)}</div>
        <div class="loc-links">
          <a class="loc-link sentinel" href="${escHtml(loc.sentinel_link)}" target="_blank" rel="noopener">
            🛰 SENTINEL-2
          </a>
          <a class="loc-link usgs" href="${escHtml(loc.usgs_link)}" target="_blank" rel="noopener">
            🌍 USGS
          </a>
          <a class="loc-link gmaps" href="${escHtml(loc.google_maps_link)}" target="_blank" rel="noopener">
            📍 MAPS
          </a>
        </div>
      </div>
    </div>
  `).join('');

  results.innerHTML = `
    <div class="company-card">
      <div class="company-header">
        <div class="company-name-wrap">
          <div class="ticker-badge">${escHtml(d.ticker)}</div>
          <div class="company-name">${escHtml(d.company)}</div>
          <div class="company-meta">${escHtml(d.industry)} · ${escHtml(d.hq_location)}</div>
        </div>
        <div class="company-stats">${statsHtml}</div>
      </div>
      ${d.description ? `<div class="company-desc">${escHtml(d.description)}</div>` : ''}
    </div>

    <div class="section-label">Satellite Monitoring Signals</div>
    <div class="signals-grid">${signalsHtml}</div>

    <div class="section-label">Satellite Imagery Targets</div>
    <div class="locations-grid">${locsHtml}</div>
  `;

  results.style.display = 'block';
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function escHtml(str) {
  if (typeof str !== 'string') return String(str ?? '');
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function shake(el) {
  el.style.animation = 'none';
  el.offsetHeight;
  el.style.animation = 'shakeInput 0.3s ease';
  setTimeout(() => el.style.animation = '', 300);
}
</script>
</body>
</html>"""


# ─── Sector → Known satellite-monitorable location clusters ───────────────────
SECTOR_LOCATIONS = {
    "Consumer Defensive": [
        {"name": "Walmart Supercenter (Bentonville, AR)", "lat": 36.3729, "lon": -94.2088},
        {"name": "Costco Warehouse (Issaquah, WA)", "lat": 47.5301, "lon": -122.0326},
        {"name": "Target Store (Minneapolis, MN)", "lat": 44.9778, "lon": -93.2650},
        {"name": "Kroger (Cincinnati, OH)", "lat": 39.1031, "lon": -84.5120},
    ],
    "Consumer Cyclical": [
        {"name": "Home Depot (Atlanta, GA)", "lat": 33.7490, "lon": -84.3880},
        {"name": "AutoNation Dealership (Fort Lauderdale, FL)", "lat": 26.1224, "lon": -80.1373},
        {"name": "AMC Movie Theater (Leawood, KS)", "lat": 38.9067, "lon": -94.6328},
        {"name": "Lowe's Distribution (Mooresville, NC)", "lat": 35.5845, "lon": -80.8098},
    ],
    "Industrials": [
        {"name": "Amazon Fulfillment Center (Robbinsville, NJ)", "lat": 40.2115, "lon": -74.5932},
        {"name": "FedEx Hub (Memphis, TN)", "lat": 35.0423, "lon": -89.9762},
        {"name": "UPS Hub (Louisville, KY)", "lat": 38.1781, "lon": -85.7360},
        {"name": "Port of Los Angeles (San Pedro, CA)", "lat": 33.7361, "lon": -118.2922},
    ],
    "Energy": [
        {"name": "Cushing Oil Storage (Cushing, OK)", "lat": 35.9823, "lon": -96.7665},
        {"name": "Houston Ship Channel (Houston, TX)", "lat": 29.7372, "lon": -95.2707},
        {"name": "Sabine Pass LNG Terminal (Cameron, LA)", "lat": 29.7286, "lon": -93.8700},
        {"name": "Permian Basin Oil Fields (Midland, TX)", "lat": 31.9973, "lon": -102.0779},
    ],
    "Basic Materials": [
        {"name": "BHP Copper Mine (Escondida, Chile)", "lat": -24.2500, "lon": -69.0700},
        {"name": "Nucor Steel Mill (Charlotte, NC)", "lat": 35.2271, "lon": -80.8431},
        {"name": "Barrick Gold Mine (Elko, NV)", "lat": 40.8324, "lon": -115.7631},
        {"name": "Albemarle Lithium (Kings Mountain, NC)", "lat": 35.2454, "lon": -81.3412},
    ],
    "Technology": [
        {"name": "Tesla Gigafactory Texas (Austin, TX)", "lat": 30.2240, "lon": -97.6180},
        {"name": "Apple Campus (Cupertino, CA)", "lat": 37.3346, "lon": -122.0090},
        {"name": "Amazon HQ (Seattle, WA)", "lat": 47.6159, "lon": -122.3360},
        {"name": "TSMC Fab (Hsinchu, Taiwan)", "lat": 24.7814, "lon": 120.9969},
    ],
    "Real Estate": [
        {"name": "Simon Mall (Indianapolis, IN)", "lat": 39.7684, "lon": -86.1581},
        {"name": "Prologis Warehouse (Joliet, IL)", "lat": 41.5250, "lon": -88.0817},
        {"name": "Public Storage (Glendale, CA)", "lat": 34.1425, "lon": -118.2551},
        {"name": "CBRE Office Park (Dallas, TX)", "lat": 32.7767, "lon": -96.7970},
    ],
    "Healthcare": [
        {"name": "Johnson & Johnson Campus (New Brunswick, NJ)", "lat": 40.4870, "lon": -74.4457},
        {"name": "Pfizer HQ (New York, NY)", "lat": 40.7589, "lon": -73.9851},
        {"name": "Mayo Clinic (Rochester, MN)", "lat": 44.0224, "lon": -92.4663},
        {"name": "Cardinal Health DC (Dublin, OH)", "lat": 40.0992, "lon": -83.1141},
    ],
    "Financial Services": [
        {"name": "NYSE (New York, NY)", "lat": 40.7069, "lon": -74.0089},
        {"name": "Goldman Sachs HQ (New York, NY)", "lat": 40.7143, "lon": -74.0138},
        {"name": "Berkshire HQ (Omaha, NE)", "lat": 41.2565, "lon": -95.9345},
        {"name": "JPMorgan HQ (New York, NY)", "lat": 40.7525, "lon": -73.9773},
    ],
    "Communication Services": [
        {"name": "Google Campus (Mountain View, CA)", "lat": 37.4220, "lon": -122.0841},
        {"name": "Meta HQ (Menlo Park, CA)", "lat": 37.4845, "lon": -122.1477},
        {"name": "AT&T HQ (Dallas, TX)", "lat": 32.7813, "lon": -96.7974},
        {"name": "Netflix HQ (Los Gatos, CA)", "lat": 37.2358, "lon": -121.9624},
    ],
    "Utilities": [
        {"name": "Hoover Dam (Boulder City, NV)", "lat": 36.0161, "lon": -114.7377},
        {"name": "Duke Energy Plant (Charlotte, NC)", "lat": 35.2271, "lon": -80.8431},
        {"name": "NextEra Solar Farm (Blythe, CA)", "lat": 33.6173, "lon": -114.5965},
        {"name": "Constellation Nuclear (Warrensville, OH)", "lat": 41.4331, "lon": -81.5129},
    ],
}

DEFAULT_LOCATIONS = [
    {"name": "Port of LA/Long Beach (CA)", "lat": 33.7361, "lon": -118.2922},
    {"name": "Newark Airport Cargo (NJ)", "lat": 40.6895, "lon": -74.1745},
    {"name": "Chicago O'Hare Cargo (IL)", "lat": 41.9742, "lon": -87.9073},
    {"name": "Dallas/Fort Worth Hub (TX)", "lat": 32.8998, "lon": -97.0403},
]

SECTOR_SIGNALS = {
    "Consumer Defensive": ["🅿️ Parking lot occupancy", "🚗 Vehicle count trends", "📦 Loading dock activity"],
    "Consumer Cyclical": ["🅿️ Parking lot footfall", "🏗️ Construction progress", "🚗 Dealership lot inventory"],
    "Industrials": ["📦 Container yard density", "🚢 Ship traffic at ports", "🏭 Factory roof heat signature"],
    "Energy": ["🛢️ Oil storage tank shadow (volume)", "🚢 Tanker traffic", "🔥 Flare activity"],
    "Basic Materials": ["⛏️ Mine excavation progress", "🏭 Plant smoke & steam", "📦 Stockpile size"],
    "Technology": ["🏭 Gigafactory expansion", "🅿️ Campus employee count", "🏗️ Data center construction"],
    "Real Estate": ["🅿️ Mall parking occupancy", "🏗️ Development progress", "🚗 Residential traffic"],
    "Healthcare": ["🏥 Facility expansion", "🅿️ Hospital lot occupancy", "🏗️ Campus construction"],
    "Financial Services": ["🏢 Office occupancy patterns", "🏗️ Building construction", "🚗 Commuter traffic"],
    "Communication Services": ["🏗️ Data center expansion", "📡 Antenna arrays", "🅿️ Campus footfall"],
    "Utilities": ["☀️ Solar farm output area", "💧 Reservoir water levels", "🌬️ Wind turbine arrays"],
}


def make_sentinel_link(lat, lon):
    return (
        f"https://apps.sentinel-hub.com/eo-browser/"
        f"?zoom=17&lat={lat}&lng={lon}"
        f"&themeId=DEFAULT-THEME"
        f"&visualizationUrl=https%3A%2F%2Fservices.sentinel-hub.com%2Fogc%2Fwms%2Fbd86bcc0-f318-402b-a145-015f85b9427e"
        f"&datasetId=S2L2A"
        f"&fromTime=2026-01-01T00%3A00%3A00.000Z"
        f"&toTime=2026-04-22T23%3A59%3A59.999Z"
        f"&layerId=1_TRUE_COLOR"
    )


def make_usgs_link(lat, lon):
    return f"https://earthexplorer.usgs.gov/?center={lat},{lon}&zoom=15"


def make_google_maps_link(lat, lon):
    return f"https://www.google.com/maps/@{lat},{lon},17z/data=!3m1!1e3"


def make_embed_map(lat, lon):
    # Use OpenStreetMap embed (no API key needed, free, works on Vercel)
    return (
        f"https://www.openstreetmap.org/export/embed.html"
        f"?bbox={lon-0.01}%2C{lat-0.01}%2C{lon+0.01}%2C{lat+0.01}"
        f"&layer=mapnik&marker={lat}%2C{lon}"
    )


@app.route("/")
def index():
    return HTML


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    ticker_symbol = data.get("ticker", "").strip().upper()

    if not ticker_symbol:
        return jsonify({"error": "Ticker symbol is required"}), 400

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info or {}
    except Exception as e:
        return jsonify({"error": f"Could not fetch ticker data: {str(e)}"}), 500

    # Validate we got real data
    company_name = info.get("longName") or info.get("shortName") or ""
    if not company_name and not info.get("sector"):
        return jsonify({"error": f"No data found for ticker '{ticker_symbol}'. Please check the symbol."}), 404

    company_name = company_name or ticker_symbol
    sector = info.get("sector") or "Unknown"
    industry = info.get("industry") or "Unknown"
    hq_city = info.get("city") or ""
    hq_state = info.get("state") or ""
    hq_country = info.get("country") or ""
    employees = info.get("fullTimeEmployees") or 0
    market_cap = info.get("marketCap") or 0
    description_raw = info.get("longBusinessSummary") or ""
    description = (description_raw[:300] + "...") if len(description_raw) > 300 else description_raw

    hq_location = ", ".join(filter(None, [hq_city, hq_state, hq_country]))

    sector_targets = SECTOR_LOCATIONS.get(sector, DEFAULT_LOCATIONS)

    locations = []
    for loc in sector_targets:
        locations.append({
            "name": loc["name"],
            "lat": loc["lat"],
            "lon": loc["lon"],
            "sentinel_link": make_sentinel_link(loc["lat"], loc["lon"]),
            "usgs_link": make_usgs_link(loc["lat"], loc["lon"]),
            "google_maps_link": make_google_maps_link(loc["lat"], loc["lon"]),
            "embed_map": make_embed_map(loc["lat"], loc["lon"]),
        })

    signals = SECTOR_SIGNALS.get(sector, ["🛰️ General area activity", "🅿️ Parking patterns", "🚗 Traffic flow"])

    return jsonify({
        "ticker": ticker_symbol,
        "company": company_name,
        "sector": sector,
        "industry": industry,
        "hq_location": hq_location,
        "employees": f"{employees:,}" if employees else "N/A",
        "market_cap": f"${market_cap / 1e9:.1f}B" if market_cap else "N/A",
        "description": description,
        "signals": signals,
        "locations": locations,
    })


# Vercel needs the app object exposed at module level
# For local dev:
if __name__ == "__main__":
    app.run(debug=True, port=5000)
