from flask import Flask, render_template_string, request, jsonify
from pytrends.request import TrendReq
import pandas as pd
import json
import traceback
from datetime import datetime, timedelta
import time

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TrendScope — Google Trends Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #050508;
    --surface: #0d0d14;
    --card: #111118;
    --border: #1e1e2e;
    --accent: #00ff9d;
    --accent2: #ff3cac;
    --accent3: #7b5ea7;
    --accent4: #f7c59f;
    --text: #e8e8f0;
    --muted: #5a5a7a;
    --glow: rgba(0,255,157,0.15);
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(0,255,157,0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,157,0.025) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }
  .container { max-width: 1400px; margin: 0 auto; padding: 0 24px; position: relative; z-index: 1; }

  header {
    padding: 32px 24px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1400px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }
  .logo { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }
  .logo span { color: var(--accent); }
  .logo small {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: var(--muted);
    display: block;
    letter-spacing: 3px;
    margin-top: 2px;
  }
  .status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 12px var(--accent);
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.3)} }

  .hero {
    padding: 60px 24px 40px;
    max-width: 1400px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }
  .hero h1 {
    font-size: clamp(32px, 5vw, 60px);
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -2px;
  }
  .hero h1 em {
    font-style: normal;
    color: transparent;
    -webkit-text-stroke: 1px var(--accent);
  }
  .hero p {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: var(--muted);
    margin-top: 10px;
    letter-spacing: 1px;
  }

  .search-panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px;
    margin: 0 24px 28px;
    max-width: 1352px;
    margin-left: auto;
    margin-right: auto;
    position: relative;
    z-index: 1;
  }
  .search-panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    border-radius: 16px 16px 0 0;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
  }
  .search-row {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: flex-end;
  }
  .field-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: 1;
    min-width: 150px;
  }
  .field-group label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
  }
  .field-group input,
  .field-group select {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 11px 14px;
    color: var(--text);
    font-family: 'Syne', sans-serif;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    width: 100%;
  }
  .field-group input:focus,
  .field-group select:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--glow);
  }
  .field-group input::placeholder { color: var(--muted); }
  select option { background: #0d0d14; }

  .btn-analyze {
    background: var(--accent);
    color: #000;
    border: none;
    border-radius: 8px;
    padding: 11px 28px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
    letter-spacing: 0.5px;
  }
  .btn-analyze:hover { background: #00e68a; transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,255,157,0.3); }
  .btn-analyze:active { transform: translateY(0); }

  .tabs-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
    position: relative;
    z-index: 1;
  }
  .tabs {
    display: flex;
    gap: 2px;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
    scrollbar-width: none;
  }
  .tabs::-webkit-scrollbar { display: none; }
  .tab-btn {
    background: none;
    border: none;
    padding: 10px 16px;
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: var(--muted);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    transition: all 0.2s;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: -1px;
  }
  .tab-btn:hover { color: var(--text); }
  .tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

  .content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 28px 24px 60px;
    position: relative;
    z-index: 1;
  }
  .tab-pane { display: none; }
  .tab-pane.active { display: block; }

  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    position: relative;
  }
  .card-title {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .card-title::before {
    content: '';
    width: 3px; height: 12px;
    background: var(--accent);
    border-radius: 2px;
    flex-shrink: 0;
  }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  @media(max-width:900px) { .grid-2 { grid-template-columns: 1fr; } }

  .chart-wrap { position: relative; height: 300px; }
  .chart-wrap-tall { position: relative; height: 400px; }

  #loader {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(5,5,8,0.88);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 16px;
    backdrop-filter: blur(6px);
  }
  #loader.show { display: flex; }
  .loader-ring {
    width: 44px; height: 44px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loader-text {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: var(--accent);
    letter-spacing: 3px;
  }

  #alert-box {
    display: none;
    background: rgba(255,60,172,0.1);
    border: 1px solid var(--accent2);
    border-radius: 8px;
    padding: 12px 18px;
    margin: 0 24px 16px;
    max-width: 1352px;
    margin-left: auto;
    margin-right: auto;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: var(--accent2);
    position: relative;
    z-index: 1;
  }
  #alert-box.show { display: block; }

  .stats-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
  .stat-pill {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    flex: 1;
    min-width: 110px;
  }
  .stat-val {
    font-size: 30px;
    font-weight: 800;
    color: var(--accent);
    line-height: 1;
  }
  .stat-lbl {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: var(--muted);
    letter-spacing: 2px;
    margin-top: 4px;
    text-transform: uppercase;
  }

  .data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .data-table th {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 2px;
    color: var(--muted);
    text-align: left;
    padding: 8px 10px;
    border-bottom: 1px solid var(--border);
    text-transform: uppercase;
  }
  .data-table td {
    padding: 9px 10px;
    border-bottom: 1px solid rgba(30,30,46,0.5);
    color: var(--text);
  }
  .data-table tr:last-child td { border-bottom: none; }
  .data-table tr:hover td { background: rgba(0,255,157,0.03); }
  .badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 1px;
    font-weight: 700;
  }
  .badge-rise { background: rgba(0,255,157,0.15); color: var(--accent); }
  .badge-top  { background: rgba(247,197,159,0.15); color: var(--accent4); }

  .bar-track {
    background: var(--surface);
    border-radius: 3px;
    height: 5px;
    overflow: hidden;
    margin-top: 4px;
    flex: 1;
  }
  .bar-fill {
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, var(--accent3), var(--accent));
    transition: width 0.6s cubic-bezier(0.16,1,0.3,1);
  }

  .region-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 7px 0;
    border-bottom: 1px solid rgba(30,30,46,0.4);
  }
  .region-item:last-child { border-bottom: none; }
  .region-name { flex: 1.2; font-size: 12px; }
  .region-val {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: var(--accent);
    min-width: 32px;
    text-align: right;
  }

  .trend-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(30,30,46,0.4);
  }
  .trend-item:last-child { border-bottom: none; }
  .trend-num {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: var(--muted);
    min-width: 22px;
  }
  .trend-kw { flex: 1; font-size: 13px; font-weight: 600; }
  .trend-traffic { font-family: 'Space Mono', monospace; font-size: 10px; color: var(--accent2); }

  .empty {
    text-align: center;
    padding: 48px 20px;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 1px;
  }

  .placeholder-state {
    min-height: 280px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 12px;
    color: var(--muted);
  }
  .placeholder-state .big { font-size: 44px; opacity: 0.2; }
  .placeholder-state p {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    text-align: center;
    line-height: 1.8;
  }

  .kw-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    margin: 4px;
  }
  .kw-tag .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
</style>
</head>
<body>

<div id="loader">
  <div class="loader-ring"></div>
  <div class="loader-text">FETCHING TRENDS DATA ...</div>
</div>

<header>
  <div class="logo">
    Trend<span>Scope</span>
    <small>GOOGLE TRENDS INTELLIGENCE DASHBOARD</small>
  </div>
  <div class="status-dot"></div>
</header>

<div class="hero">
  <h1>Decode What the<br>World is <em>Searching</em></h1>
  <p>// interest over time &bull; regional breakdown &bull; related topics &bull; trending queries</p>
</div>

<div id="alert-box"></div>

<div class="search-panel">
  <div class="search-row">
    <div class="field-group" style="flex:2;min-width:200px">
      <label>Primary Keyword</label>
      <input type="text" id="keyword" placeholder="e.g. Bitcoin, Artificial Intelligence, Climate Change" />
    </div>
    <div class="field-group">
      <label>Compare Keywords (comma-separated, max 4 extras)</label>
      <input type="text" id="compare_kw" placeholder="e.g. Ethereum, NFT" />
    </div>
    <div class="field-group">
      <label>Timeframe</label>
      <select id="timeframe">
        <option value="now 1-d">Last 24 Hours</option>
        <option value="now 7-d">Last 7 Days</option>
        <option value="today 1-m">Last 30 Days</option>
        <option value="today 3-m" selected>Last 90 Days</option>
        <option value="today 12-m">Last 12 Months</option>
        <option value="today 5-y">Last 5 Years</option>
        <option value="all">All Time</option>
      </select>
    </div>
    <div class="field-group">
      <label>Region</label>
      <select id="geo">
        <option value="">Worldwide</option>
        <option value="US">United States</option>
        <option value="GB">United Kingdom</option>
        <option value="IN">India</option>
        <option value="CA">Canada</option>
        <option value="AU">Australia</option>
        <option value="DE">Germany</option>
        <option value="FR">France</option>
        <option value="JP">Japan</option>
        <option value="BR">Brazil</option>
        <option value="SG">Singapore</option>
        <option value="KR">South Korea</option>
        <option value="ZA">South Africa</option>
      </select>
    </div>
    <div class="field-group">
      <label>Category</label>
      <select id="cat">
        <option value="0">All Categories</option>
        <option value="7">Finance</option>
        <option value="8">Food &amp; Drink</option>
        <option value="174">Technology</option>
        <option value="11">Health</option>
        <option value="57">Sports</option>
        <option value="958">Business &amp; Industrial</option>
        <option value="16">News</option>
        <option value="22">Arts &amp; Entertainment</option>
        <option value="71">Travel</option>
      </select>
    </div>
    <div class="field-group">
      <label>Property</label>
      <select id="gprop">
        <option value="">Web Search</option>
        <option value="images">Image Search</option>
        <option value="news">News Search</option>
        <option value="youtube">YouTube</option>
        <option value="froogle">Shopping</option>
      </select>
    </div>
    <button class="btn-analyze" onclick="analyze()">&#9654; Analyze</button>
  </div>
</div>

<div class="tabs-container">
  <div class="tabs">
    <button class="tab-btn active" data-tab="overview" onclick="switchTab(this,'overview')">Overview</button>
    <button class="tab-btn" data-tab="regions" onclick="switchTab(this,'regions')">Regions</button>
    <button class="tab-btn" data-tab="related" onclick="switchTab(this,'related')">Related Topics</button>
    <button class="tab-btn" data-tab="queries" onclick="switchTab(this,'queries')">Related Queries</button>
    <button class="tab-btn" data-tab="trending" onclick="switchTab(this,'trending')">Trending Now</button>
    <button class="tab-btn" data-tab="compare" onclick="switchTab(this,'compare')">Comparison</button>
    <button class="tab-btn" data-tab="hourly" onclick="switchTab(this,'hourly')">Hourly</button>
  </div>
</div>

<div class="content">

  <!-- OVERVIEW -->
  <div class="tab-pane active" id="tab-overview">
    <div id="overview-placeholder" class="placeholder-state">
      <div class="big">&#128225;</div>
      <p>ENTER A KEYWORD ABOVE<br>AND CLICK ANALYZE TO BEGIN</p>
    </div>
    <div id="overview-content" style="display:none">
      <div class="stats-row" id="stats-row"></div>
      <div class="card">
        <div class="card-title">Interest Over Time (indexed 0-100)</div>
        <div class="chart-wrap"><canvas id="iotChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- REGIONS -->
  <div class="tab-pane" id="tab-regions">
    <div id="regions-placeholder" class="placeholder-state">
      <div class="big">&#127758;</div>
      <p>RUN ANALYSIS TO SEE REGIONAL BREAKDOWN</p>
    </div>
    <div id="regions-content" style="display:none">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Interest by Country</div>
          <div id="countries-list"></div>
        </div>
        <div class="card">
          <div class="card-title">Interest by City</div>
          <div id="cities-list"></div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">Top 10 Countries — Bar Chart</div>
        <div class="chart-wrap"><canvas id="regionsChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- RELATED TOPICS -->
  <div class="tab-pane" id="tab-related">
    <div id="related-placeholder" class="placeholder-state">
      <div class="big">&#128279;</div>
      <p>RUN ANALYSIS TO DISCOVER RELATED TOPICS</p>
    </div>
    <div id="related-content" style="display:none">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Top Related Topics</div>
          <div id="related-top-list"></div>
        </div>
        <div class="card">
          <div class="card-title">Rising Related Topics</div>
          <div id="related-rising-list"></div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">Rising Topics — Value Chart</div>
        <div class="chart-wrap"><canvas id="risingTopicsChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- QUERIES -->
  <div class="tab-pane" id="tab-queries">
    <div id="queries-placeholder" class="placeholder-state">
      <div class="big">&#128269;</div>
      <p>RUN ANALYSIS TO EXTRACT RELATED QUERIES</p>
    </div>
    <div id="queries-content" style="display:none">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Top Queries</div>
          <div id="top-queries-list"></div>
        </div>
        <div class="card">
          <div class="card-title">Rising Queries</div>
          <div id="rising-queries-list"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- TRENDING -->
  <div class="tab-pane" id="tab-trending">
    <div class="grid-2">
      <div class="card">
        <div class="card-title">Daily Trending Searches</div>
        <div id="daily-trending-list">
          <div class="empty">Click Analyze to load trending searches</div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">Top Trending — Volume Rank</div>
        <div class="chart-wrap"><canvas id="trendingChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- COMPARISON -->
  <div class="tab-pane" id="tab-compare">
    <div id="compare-placeholder" class="placeholder-state">
      <div class="big">&#9889;</div>
      <p>ADD COMPARISON KEYWORDS IN THE SEARCH BAR<br>THEN CLICK ANALYZE</p>
    </div>
    <div id="compare-content" style="display:none">
      <div id="kw-tags" style="margin-bottom:16px"></div>
      <div class="card">
        <div class="card-title">Keyword Comparison — Interest Over Time</div>
        <div class="chart-wrap-tall"><canvas id="compareChart"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">Average Interest Score per Keyword</div>
        <div class="chart-wrap"><canvas id="compareBarChart"></canvas></div>
      </div>
    </div>
  </div>

  <!-- HOURLY -->
  <div class="tab-pane" id="tab-hourly">
    <div id="hourly-placeholder" class="placeholder-state">
      <div class="big">&#9201;</div>
      <p>RUN ANALYSIS TO FETCH GRANULAR HOURLY DATA<br>(LAST 7 DAYS)</p>
    </div>
    <div id="hourly-content" style="display:none">
      <div class="card">
        <div class="card-title">Hourly Interest — Last 7 Days</div>
        <div class="chart-wrap-tall"><canvas id="hourlyChart"></canvas></div>
      </div>
    </div>
  </div>

</div>

<script>
const COLORS = ['#00ff9d','#ff3cac','#7b5ea7','#f7c59f','#38bdf8'];
let charts = {};

function switchTab(btn, name) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
}

function showLoader(v) {
  document.getElementById('loader').classList.toggle('show', v);
}
function showAlert(msg) {
  const el = document.getElementById('alert-box');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 8000);
}

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

const baseChartOpts = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: '#5a5a7a', font: { family: "'Space Mono'", size: 10 }, boxWidth: 12 } },
    tooltip: {
      backgroundColor: '#111118',
      borderColor: '#1e1e2e',
      borderWidth: 1,
      titleColor: '#e8e8f0',
      bodyColor: '#5a5a7a',
      titleFont: { family: "'Space Mono'" },
      bodyFont: { family: "'Space Mono'" },
    }
  },
  scales: {
    x: {
      ticks: { color: '#5a5a7a', font: { family: "'Space Mono'", size: 9 }, maxRotation: 45, maxTicksLimit: 14 },
      grid: { color: 'rgba(30,30,46,0.7)' }
    },
    y: {
      ticks: { color: '#5a5a7a', font: { family: "'Space Mono'", size: 9 } },
      grid: { color: 'rgba(30,30,46,0.7)' },
      min: 0
    }
  }
};

function makeLineChart(id, labels, datasets, extraOpts={}) {
  destroyChart(id);
  const ctx = document.getElementById(id).getContext('2d');
  charts[id] = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      ...baseChartOpts,
      interaction: { mode: 'index', intersect: false },
      ...extraOpts,
      scales: {
        ...baseChartOpts.scales,
        y: { ...baseChartOpts.scales.y, max: 100 }
      }
    }
  });
}

function makeBarChart(id, labels, data, color, horizontal=false) {
  destroyChart(id);
  const ctx = document.getElementById(id).getContext('2d');
  charts[id] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: Array.isArray(color) ? color : color,
        borderRadius: 4,
        borderSkipped: false,
      }]
    },
    options: {
      ...baseChartOpts,
      indexAxis: horizontal ? 'y' : 'x',
      plugins: { ...baseChartOpts.plugins, legend: { display: false } },
    }
  });
}

function renderRegionList(containerId, items) {
  const el = document.getElementById(containerId);
  if (!items || items.length === 0) {
    el.innerHTML = '<div class="empty">No regional data available</div>';
    return;
  }
  el.innerHTML = items.slice(0, 15).map(item => `
    <div class="region-item">
      <div class="region-name">${item.name}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${item.value}%"></div></div>
      <div class="region-val">${item.value}</div>
    </div>
  `).join('');
}

function renderQueryTable(containerId, items, type) {
  const el = document.getElementById(containerId);
  if (!items || items.length === 0) {
    el.innerHTML = '<div class="empty">No data available</div>';
    return;
  }
  el.innerHTML = `
    <table class="data-table">
      <thead><tr><th>#</th><th>Query</th><th>Value</th><th>Tag</th></tr></thead>
      <tbody>
        ${items.slice(0, 20).map((q, i) => `
          <tr>
            <td style="color:var(--muted);font-family:'Space Mono';font-size:10px">${String(i+1).padStart(2,'0')}</td>
            <td>${q.query}</td>
            <td style="font-family:'Space Mono';color:${type==='rising'?'var(--accent)':'var(--accent4)'}">${q.value}</td>
            <td><span class="badge ${type==='rising'?'badge-rise':'badge-top'}">${type.toUpperCase()}</span></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

async function analyze() {
  document.getElementById('alert-box').classList.remove('show');
  const keyword = document.getElementById('keyword').value.trim();
  if (!keyword) { showAlert('Please enter a keyword to analyze.'); return; }

  const compare   = document.getElementById('compare_kw').value.trim();
  const timeframe = document.getElementById('timeframe').value;
  const geo       = document.getElementById('geo').value;
  const cat       = document.getElementById('cat').value;
  const gprop     = document.getElementById('gprop').value;

  showLoader(true);

  try {
    const resp = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword, compare, timeframe, geo, cat, gprop })
    });
    if (!resp.ok) throw new Error('Server error ' + resp.status);
    const d = await resp.json();
    if (d.error) { showAlert('Error: ' + d.error); showLoader(false); return; }
    renderAll(d, keyword);
  } catch(e) {
    showAlert('Request failed: ' + e.message);
  }
  showLoader(false);
}

function renderAll(d, keyword) {

  // -- OVERVIEW --
  document.getElementById('overview-placeholder').style.display = 'none';
  document.getElementById('overview-content').style.display = 'block';

  const iot  = d.interest_over_time || {};
  const dates = iot.dates || [];
  const vals  = (iot.values || {})[keyword] || [];
  const avg   = vals.length ? Math.round(vals.reduce((a,b)=>a+b,0)/vals.length) : 0;
  const peak  = vals.length ? Math.max(...vals) : 0;
  const last  = vals[vals.length-1] ?? 0;
  const first = vals[0] ?? 0;
  const trendStr = vals.length >= 2
    ? (last > first ? '&#9650; Rising' : (last < first ? '&#9660; Falling' : '&#8212; Stable'))
    : '&#8212; N/A';
  const trendColor = last > first ? 'var(--accent)' : 'var(--accent2)';

  document.getElementById('stats-row').innerHTML = `
    <div class="stat-pill">
      <div class="stat-val">${avg}</div>
      <div class="stat-lbl">Avg Interest</div>
    </div>
    <div class="stat-pill">
      <div class="stat-val">${peak}</div>
      <div class="stat-lbl">Peak Score</div>
    </div>
    <div class="stat-pill">
      <div class="stat-val">${last}</div>
      <div class="stat-lbl">Latest Score</div>
    </div>
    <div class="stat-pill">
      <div class="stat-val" style="color:${trendColor};font-size:18px">${trendStr}</div>
      <div class="stat-lbl">Trend Direction</div>
    </div>
    <div class="stat-pill">
      <div class="stat-val" style="font-size:20px">${dates.length}</div>
      <div class="stat-lbl">Data Points</div>
    </div>
  `;

  if (dates.length && vals.length) {
    makeLineChart('iotChart', dates, [{
      label: keyword,
      data: vals,
      borderColor: '#00ff9d',
      backgroundColor: 'rgba(0,255,157,0.07)',
      borderWidth: 2,
      pointRadius: dates.length > 100 ? 0 : 2,
      fill: true,
      tension: 0.35
    }]);
  }

  // -- REGIONS --
  document.getElementById('regions-placeholder').style.display = 'none';
  document.getElementById('regions-content').style.display = 'block';

  const ibr = d.interest_by_region || {};
  renderRegionList('countries-list', ibr.countries || []);
  renderRegionList('cities-list', ibr.cities || []);

  const topC = (ibr.countries || []).slice(0, 12);
  if (topC.length) {
    makeBarChart('regionsChart',
      topC.map(c => c.name),
      topC.map(c => c.value),
      'rgba(123,94,167,0.85)',
      true
    );
  }

  // -- RELATED TOPICS --
  document.getElementById('related-placeholder').style.display = 'none';
  document.getElementById('related-content').style.display = 'block';

  const rt = d.related_topics || {};
  const topTopics    = rt.top    || [];
  const risingTopics = rt.rising || [];

  document.getElementById('related-top-list').innerHTML = topTopics.length
    ? `<table class="data-table">
        <thead><tr><th>Topic</th><th>Type</th><th>Value</th></tr></thead>
        <tbody>${topTopics.slice(0,15).map(t=>`
          <tr>
            <td>${t.topic_title}</td>
            <td style="color:var(--muted);font-size:11px">${t.topic_type||''}</td>
            <td style="font-family:'Space Mono';color:var(--accent4)">${t.value}</td>
          </tr>`).join('')}
        </tbody></table>`
    : '<div class="empty">No top topics found</div>';

  document.getElementById('related-rising-list').innerHTML = risingTopics.length
    ? `<table class="data-table">
        <thead><tr><th>Topic</th><th>Type</th><th>Value</th></tr></thead>
        <tbody>${risingTopics.slice(0,15).map(t=>`
          <tr>
            <td>${t.topic_title}</td>
            <td style="color:var(--muted);font-size:11px">${t.topic_type||''}</td>
            <td style="font-family:'Space Mono';color:var(--accent)">${t.value}</td>
          </tr>`).join('')}
        </tbody></table>`
    : '<div class="empty">No rising topics found</div>';

  if (risingTopics.length) {
    const rs = risingTopics.slice(0, 8);
    makeBarChart('risingTopicsChart',
      rs.map(t => t.topic_title.substring(0, 22)),
      rs.map(t => { const n = parseInt(t.value); return isNaN(n) ? 0 : Math.min(n, 50000); }),
      'rgba(255,60,172,0.8)'
    );
  }

  // -- QUERIES --
  document.getElementById('queries-placeholder').style.display = 'none';
  document.getElementById('queries-content').style.display = 'block';

  const rq = d.related_queries || {};
  renderQueryTable('top-queries-list',    rq.top    || [], 'top');
  renderQueryTable('rising-queries-list', rq.rising || [], 'rising');

  // -- TRENDING --
  const trending = d.trending_searches || [];
  const trendEl  = document.getElementById('daily-trending-list');
  if (trending.length) {
    trendEl.innerHTML = trending.slice(0, 20).map((t, i) => `
      <div class="trend-item">
        <div class="trend-num">${String(i+1).padStart(2,'0')}</div>
        <div class="trend-kw">${t.title || t}</div>
        <div class="trend-traffic">${t.traffic || ''}</div>
      </div>
    `).join('');

    const top10 = trending.slice(0, 10);
    makeBarChart('trendingChart',
      top10.map(t => (t.title || t).substring(0, 18)),
      top10.map((_, i) => 10 - i),
      'rgba(56,189,248,0.8)'
    );
  } else {
    trendEl.innerHTML = '<div class="empty">No trending data available for this region</div>';
  }

  // -- COMPARISON --
  const allKws = Object.keys(iot.values || {});
  if (allKws.length > 1) {
    document.getElementById('compare-placeholder').style.display = 'none';
    document.getElementById('compare-content').style.display    = 'block';

    document.getElementById('kw-tags').innerHTML = allKws.map((kw, i) => `
      <span class="kw-tag">
        <span class="dot" style="background:${COLORS[i % COLORS.length]}"></span>
        ${kw}
      </span>
    `).join('');

    const datasets = allKws.map((kw, i) => ({
      label: kw,
      data: (iot.values[kw] || []),
      borderColor: COLORS[i % COLORS.length],
      backgroundColor: COLORS[i % COLORS.length] + '12',
      borderWidth: 2,
      pointRadius: dates.length > 100 ? 0 : 1,
      fill: false,
      tension: 0.3
    }));
    makeLineChart('compareChart', dates, datasets);

    const avgs = allKws.map(kw => {
      const v = iot.values[kw] || [];
      return v.length ? Math.round(v.reduce((a,b)=>a+b,0)/v.length) : 0;
    });
    destroyChart('compareBarChart');
    const ctx2 = document.getElementById('compareBarChart').getContext('2d');
    charts['compareBarChart'] = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: allKws,
        datasets: [{
          data: avgs,
          backgroundColor: allKws.map((_, i) => COLORS[i % COLORS.length]),
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        ...baseChartOpts,
        plugins: { ...baseChartOpts.plugins, legend: { display: false } },
        scales: {
          ...baseChartOpts.scales,
          y: { ...baseChartOpts.scales.y, max: 100 }
        }
      }
    });
  } else {
    document.getElementById('compare-placeholder').style.display = 'flex';
    document.getElementById('compare-content').style.display = 'none';
  }

  // -- HOURLY --
  const hourly = d.hourly_interest || {};
  if (hourly.dates && hourly.dates.length) {
    document.getElementById('hourly-placeholder').style.display = 'none';
    document.getElementById('hourly-content').style.display = 'block';
    makeLineChart('hourlyChart', hourly.dates, [{
      label: keyword + ' (hourly)',
      data: hourly.values || [],
      borderColor: '#f7c59f',
      backgroundColor: 'rgba(247,197,159,0.06)',
      borderWidth: 1.5,
      pointRadius: 0,
      fill: true,
      tension: 0.2
    }]);
  }
}

document.getElementById('keyword').addEventListener('keydown', e => {
  if (e.key === 'Enter') analyze();
});
</script>
</body>
</html>
"""

pytrends = TrendReq(hl='en-US', tz=330, timeout=(10, 25), retries=2, backoff_factor=0.5)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    keyword   = data.get('keyword', '').strip()
    compare   = data.get('compare', '').strip()
    timeframe = data.get('timeframe', 'today 3-m')
    geo       = data.get('geo', '')
    cat       = int(data.get('cat', 0))
    gprop     = data.get('gprop', '')

    if not keyword:
        return jsonify({'error': 'Keyword is required'})

    kw_list = [keyword]
    if compare:
        extras = [k.strip() for k in compare.split(',') if k.strip()]
        kw_list = (kw_list + extras)[:5]

    result = {}

    # ---------- Interest Over Time ----------
    try:
        pytrends.build_payload(kw_list, cat=cat, timeframe=timeframe, geo=geo, gprop=gprop)
        time.sleep(0.4)
        iot_df = pytrends.interest_over_time()
        if iot_df is not None and not iot_df.empty:
            if 'isPartial' in iot_df.columns:
                iot_df = iot_df.drop(columns=['isPartial'])
            result['interest_over_time'] = {
                'dates':  [str(d)[:10] for d in iot_df.index.tolist()],
                'values': {col: iot_df[col].tolist() for col in iot_df.columns}
            }
        else:
            result['interest_over_time'] = {'dates': [], 'values': {}}
    except Exception as e:
        result['interest_over_time'] = {'dates': [], 'values': {}, 'error': str(e)}

    # ---------- Interest by Region ----------
    try:
        pytrends.build_payload([keyword], cat=cat, timeframe=timeframe, geo=geo, gprop=gprop)
        time.sleep(0.4)

        def region_list(resolution):
            df = pytrends.interest_by_region(resolution=resolution, inc_low_vol=False, inc_geo_code=False)
            if df is None or df.empty:
                return []
            col = keyword if keyword in df.columns else df.columns[0]
            df = df.sort_values(col, ascending=False)
            return [{'name': str(idx), 'value': int(row[col])}
                    for idx, row in df.iterrows() if int(row[col]) > 0]

        result['interest_by_region'] = {
            'countries': region_list('COUNTRY')[:30],
            'cities':    region_list('CITY')[:30]
        }
    except Exception as e:
        result['interest_by_region'] = {'countries': [], 'cities': [], 'error': str(e)}

    # ---------- Related Topics ----------
    try:
        pytrends.build_payload([keyword], cat=cat, timeframe=timeframe, geo=geo, gprop=gprop)
        time.sleep(0.4)
        rt = pytrends.related_topics()
        top_t, rise_t = [], []
        if rt and keyword in rt:
            top_df  = rt[keyword].get('top')
            rise_df = rt[keyword].get('rising')
            if top_df is not None and not top_df.empty:
                top_t = [{'topic_title': str(r.get('topic_title','')),
                          'topic_type':  str(r.get('topic_type','')),
                          'value':       str(r.get('value',''))}
                         for _, r in top_df.iterrows()]
            if rise_df is not None and not rise_df.empty:
                rise_t = [{'topic_title': str(r.get('topic_title','')),
                           'topic_type':  str(r.get('topic_type','')),
                           'value':       str(r.get('value',''))}
                          for _, r in rise_df.iterrows()]
        result['related_topics'] = {'top': top_t[:20], 'rising': rise_t[:20]}
    except Exception as e:
        result['related_topics'] = {'top': [], 'rising': [], 'error': str(e)}

    # ---------- Related Queries ----------
    try:
        pytrends.build_payload([keyword], cat=cat, timeframe=timeframe, geo=geo, gprop=gprop)
        time.sleep(0.4)
        rq = pytrends.related_queries()
        top_q, rise_q = [], []
        if rq and keyword in rq:
            top_df  = rq[keyword].get('top')
            rise_df = rq[keyword].get('rising')
            if top_df is not None and not top_df.empty:
                top_q = [{'query': str(r.get('query','')), 'value': str(r.get('value',''))}
                         for _, r in top_df.iterrows()]
            if rise_df is not None and not rise_df.empty:
                rise_q = [{'query': str(r.get('query','')), 'value': str(r.get('value',''))}
                          for _, r in rise_df.iterrows()]
        result['related_queries'] = {'top': top_q[:25], 'rising': rise_q[:25]}
    except Exception as e:
        result['related_queries'] = {'top': [], 'rising': [], 'error': str(e)}

    # ---------- Trending Searches ----------
    try:
        time.sleep(0.4)
        geo_map = {
            'US':'united_states','GB':'united_kingdom','IN':'india',
            'CA':'canada','AU':'australia','DE':'germany',
            'FR':'france','JP':'japan','BR':'brazil','SG':'singapore',
            'KR':'south_korea','ZA':'south_africa'
        }
        trend_geo = geo_map.get(geo, 'united_states')
        ts_df = pytrends.trending_searches(pn=trend_geo)
        trending = []
        if ts_df is not None and not ts_df.empty:
            trending = [{'title': str(t), 'traffic': ''} for t in ts_df[0].tolist()]
        result['trending_searches'] = trending[:25]
    except Exception as e:
        result['trending_searches'] = []

    # ---------- Hourly Interest ----------
    try:
        time.sleep(0.5)
        now   = datetime.now()
        start = now - timedelta(days=7)
        hourly_df = pytrends.get_historical_interest(
            [keyword],
            year_start=start.year, month_start=start.month, day_start=start.day, hour_start=0,
            year_end=now.year,   month_end=now.month,   day_end=now.day,   hour_end=23,
            cat=cat, geo=geo, gprop=gprop, sleep=1
        )
        if hourly_df is not None and not hourly_df.empty:
            if 'isPartial' in hourly_df.columns:
                hourly_df = hourly_df.drop(columns=['isPartial'])
            col = keyword if keyword in hourly_df.columns else hourly_df.columns[0]
            result['hourly_interest'] = {
                'dates':  [str(d)[:16] for d in hourly_df.index.tolist()],
                'values': hourly_df[col].tolist()
            }
        else:
            result['hourly_interest'] = {'dates': [], 'values': []}
    except Exception as e:
        result['hourly_interest'] = {'dates': [], 'values': [], 'error': str(e)}

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
