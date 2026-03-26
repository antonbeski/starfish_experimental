"""
=============================================================
  GLOBAL STOCK MARKET DASHBOARD - Flask Single File App
=============================================================
  Deploy to Vercel:
    1. Push this file (app.py) to your GitHub repo root
    2. Also create these two small files in your repo root:

  ── vercel.json ──────────────────────────────────────────
  {
    "builds": [{"src": "app.py", "use": "@vercel/python"}],
    "routes": [{"src": "/(.*)", "dest": "app.py"}]
  }

  ── requirements.txt ─────────────────────────────────────
  flask==3.0.3
  requests==2.31.0
  flask-caching==2.3.0

  ── Vercel Environment Variable ──────────────────────────
  Name : FMP_API_KEY
  Value: <your Financial Modeling Prep API key>
=============================================================
"""

import os
import requests
from flask import Flask, jsonify, request, render_template_string
from functools import lru_cache
import time

app = Flask(__name__)

# ─── Config ────────────────────────────────────────────────
FMP_BASE = "https://financialmodelingprep.com/stable"
FMP_KEY  = os.environ.get("FMP_API_KEY", "demo")

# simple in-memory cache: (result, timestamp)
_cache: dict = {}
CACHE_TTL = 60  # seconds

def fmp(endpoint: str, params: dict = None) -> any:
    """Call FMP API with caching."""
    p = params or {}
    p["apikey"] = FMP_KEY
    cache_key = endpoint + str(sorted(p.items()))
    now = time.time()
    if cache_key in _cache:
        data, ts = _cache[cache_key]
        if now - ts < CACHE_TTL:
            return data
    url = f"{FMP_BASE}/{endpoint.lstrip('/')}"
    try:
        r = requests.get(url, params=p, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        data = {"error": str(e)}
    _cache[cache_key] = (data, now)
    return data


# ──────────────────────────────────────────────────────────
#  API ROUTES  (Flask → FMP proxy)
# ──────────────────────────────────────────────────────────

@app.route("/api/indices")
def api_indices():
    symbols = ["^GSPC", "^IXIC", "^DJI", "^RUT", "^FTSE", "^N225", "^HSI", "^GDAXI", "^FCHI", "^STOXX50E"]
    joined = ",".join(symbols)
    data = fmp("batch-quote-short", {"symbols": joined})
    return jsonify(data)

@app.route("/api/gainers")
def api_gainers():
    return jsonify(fmp("biggest-gainers"))

@app.route("/api/losers")
def api_losers():
    return jsonify(fmp("biggest-losers"))

@app.route("/api/actives")
def api_actives():
    return jsonify(fmp("most-actives"))

@app.route("/api/quote/<symbol>")
def api_quote(symbol):
    return jsonify(fmp("quote", {"symbol": symbol}))

@app.route("/api/profile/<symbol>")
def api_profile(symbol):
    return jsonify(fmp("profile", {"symbol": symbol}))

@app.route("/api/history/<symbol>")
def api_history(symbol):
    period = request.args.get("period", "3month")
    data = fmp("historical-price-eod/light", {"symbol": symbol, "serietype": "line"})
    if isinstance(data, list):
        # slice based on period
        limits = {"1month": 22, "3month": 66, "6month": 130, "1year": 252, "5year": 1260}
        lim = limits.get(period, 66)
        data = data[:lim]
    return jsonify(data)

@app.route("/api/income/<symbol>")
def api_income(symbol):
    return jsonify(fmp("income-statement", {"symbol": symbol, "limit": 5}))

@app.route("/api/balance/<symbol>")
def api_balance(symbol):
    return jsonify(fmp("balance-sheet-statement", {"symbol": symbol, "limit": 5}))

@app.route("/api/cashflow/<symbol>")
def api_cashflow(symbol):
    return jsonify(fmp("cash-flow-statement", {"symbol": symbol, "limit": 5}))

@app.route("/api/ratios/<symbol>")
def api_ratios(symbol):
    return jsonify(fmp("ratios-ttm", {"symbol": symbol}))

@app.route("/api/news")
def api_news():
    limit = request.args.get("limit", 24)
    return jsonify(fmp("news/stock-latest", {"limit": limit}))

@app.route("/api/sector")
def api_sector():
    return jsonify(fmp("sector-performance-snapshot"))

@app.route("/api/commodities")
def api_commodities():
    return jsonify(fmp("batch-commodity-quotes"))

@app.route("/api/forex")
def api_forex():
    pairs = ["EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD","USDCHF","NZDUSD","USDCNY","USDINR","USDBRL"]
    joined = ",".join(pairs)
    return jsonify(fmp("batch-quote-short", {"symbols": joined}))

@app.route("/api/crypto")
def api_crypto():
    coins = ["BTCUSD","ETHUSD","XRPUSD","BNBUSD","SOLUSD","ADAUSD","DOGEUSD","AVAXUSD","DOTUSD","MATICUSD"]
    joined = ",".join(coins)
    return jsonify(fmp("batch-quote-short", {"symbols": joined}))

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    return jsonify(fmp("search-name", {"query": q, "limit": 10}))

@app.route("/api/peers/<symbol>")
def api_peers(symbol):
    return jsonify(fmp("stock-peers", {"symbol": symbol}))

@app.route("/api/earnings/<symbol>")
def api_earnings(symbol):
    return jsonify(fmp("earnings", {"symbol": symbol, "limit": 8}))

@app.route("/api/analyst/<symbol>")
def api_analyst(symbol):
    return jsonify(fmp("analyst-estimates", {"symbol": symbol, "limit": 4}))

@app.route("/api/price-target/<symbol>")
def api_price_target(symbol):
    return jsonify(fmp("price-target-consensus", {"symbol": symbol}))


# ──────────────────────────────────────────────────────────
#  MAIN HTML PAGE
# ──────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GlobalMarkets — Live Financial Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
<style>
:root{
  --bg:#070b14;
  --bg2:#0d1220;
  --bg3:#111827;
  --border:#1e2d45;
  --accent:#00d4aa;
  --accent2:#3b82f6;
  --red:#ef4444;
  --green:#22c55e;
  --yellow:#f59e0b;
  --text:#e2e8f0;
  --muted:#64748b;
  --card:#0d1828;
  --card2:#111d2e;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);font-family:'Space Mono',monospace;font-size:13px;overflow-x:hidden}
::selection{background:var(--accent);color:#000}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}

/* HEADER */
header{
  position:sticky;top:0;z-index:100;
  background:rgba(7,11,20,.92);backdrop-filter:blur(16px);
  border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;height:56px;
}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none}
.logo-mark{
  width:32px;height:32px;background:var(--accent);
  clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
  display:flex;align-items:center;justify-content:center;
  font-family:'Syne',sans-serif;font-weight:800;font-size:14px;color:#000;
}
.logo-text{font-family:'Syne',sans-serif;font-weight:800;font-size:18px;letter-spacing:-0.5px;color:var(--text)}
.logo-text span{color:var(--accent)}
nav{display:flex;gap:2px}
.nav-btn{
  background:none;border:none;color:var(--muted);cursor:pointer;
  padding:6px 14px;border-radius:6px;font-family:'Space Mono',monospace;
  font-size:12px;transition:all .2s;letter-spacing:.5px;
}
.nav-btn:hover,.nav-btn.active{color:var(--accent);background:rgba(0,212,170,.08)}
.header-right{display:flex;align-items:center;gap:12px}
.search-wrap{position:relative}
#global-search{
  background:var(--bg3);border:1px solid var(--border);color:var(--text);
  padding:7px 12px 7px 36px;border-radius:8px;font-family:'Space Mono',monospace;
  font-size:12px;width:220px;transition:all .2s;
}
#global-search:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,212,170,.1);width:260px}
.search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--muted);pointer-events:none}
#search-results{
  position:absolute;top:calc(100% + 6px);left:0;right:0;min-width:280px;
  background:var(--bg3);border:1px solid var(--border);border-radius:10px;
  box-shadow:0 20px 60px rgba(0,0,0,.6);z-index:200;display:none;overflow:hidden;
}
.sr-item{
  padding:10px 14px;cursor:pointer;border-bottom:1px solid var(--border);
  transition:background .15s;display:flex;justify-content:space-between;align-items:center;
}
.sr-item:last-child{border-bottom:none}
.sr-item:hover{background:rgba(0,212,170,.06)}
.sr-sym{font-weight:700;color:var(--accent);font-size:13px}
.sr-name{color:var(--muted);font-size:11px;margin-top:1px}
.sr-ex{font-size:10px;color:var(--muted);background:var(--bg);padding:2px 6px;border-radius:3px}
.ticker-bar{
  background:var(--bg2);border-bottom:1px solid var(--border);
  overflow:hidden;height:32px;display:flex;align-items:center;
}
.ticker-track{
  display:flex;gap:0;animation:tickerScroll 40s linear infinite;white-space:nowrap;
}
.ticker-track:hover{animation-play-state:paused}
@keyframes tickerScroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.tick-item{
  padding:0 24px;display:flex;align-items:center;gap:8px;
  border-right:1px solid var(--border);font-size:11px;flex-shrink:0;
}
.tick-sym{font-weight:700;color:var(--text)}
.tick-price{color:var(--muted)}
.pos{color:var(--green)}
.neg{color:var(--red)}

/* LAYOUT */
.page{display:none;animation:fadeUp .3s ease}
.page.active{display:block}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
main{padding:20px 24px 40px;max-width:1600px;margin:0 auto}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.grid-5{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}
.col-span-2{grid-column:span 2}
.col-span-3{grid-column:span 3}

/* CARDS */
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.card-header{
  display:flex;justify-content:space-between;align-items:center;
  padding:14px 18px;border-bottom:1px solid var(--border);
}
.card-title{font-family:'Syne',sans-serif;font-weight:700;font-size:14px;letter-spacing:.3px}
.card-body{padding:16px 18px}
.card-tag{
  font-size:10px;padding:3px 8px;border-radius:20px;letter-spacing:.5px;
  background:rgba(0,212,170,.1);color:var(--accent);border:1px solid rgba(0,212,170,.2);
}
.card-tag.red{background:rgba(239,68,68,.1);color:var(--red);border-color:rgba(239,68,68,.2)}
.card-tag.blue{background:rgba(59,130,246,.1);color:var(--accent2);border-color:rgba(59,130,246,.2)}

/* INDEX CARDS */
.idx-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}
.idx-card{
  background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:14px 16px;cursor:pointer;transition:all .2s;position:relative;overflow:hidden;
}
.idx-card::after{
  content:'';position:absolute;bottom:0;left:0;right:0;height:2px;
  background:var(--accent);transform:scaleX(0);transform-origin:left;
  transition:transform .3s;
}
.idx-card:hover::after,.idx-card.selected::after{transform:scaleX(1)}
.idx-card:hover,.idx-card.selected{border-color:rgba(0,212,170,.3);background:var(--card2)}
.idx-name{font-size:11px;color:var(--muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px}
.idx-price{font-family:'Syne',sans-serif;font-weight:700;font-size:18px;margin-bottom:2px}
.idx-chg{font-size:12px}

/* TABLES */
table{width:100%;border-collapse:collapse}
th{text-align:left;padding:8px 12px;color:var(--muted);font-size:11px;letter-spacing:.5px;border-bottom:1px solid var(--border);font-weight:400}
td{padding:9px 12px;border-bottom:1px solid rgba(30,45,69,.5);font-size:12px;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(255,255,255,.02)}
.sym-cell{font-weight:700;color:var(--accent);font-size:13px}
.sym-sub{font-size:10px;color:var(--muted);margin-top:1px}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700}
.badge.up{background:rgba(34,197,94,.15);color:var(--green)}
.badge.dn{background:rgba(239,68,68,.15);color:var(--red)}
.num-right{text-align:right}

/* STATS ROW */
.stat-row{display:flex;gap:0;border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:16px}
.stat-item{flex:1;padding:14px 16px;border-right:1px solid var(--border);text-align:center}
.stat-item:last-child{border-right:none}
.stat-label{font-size:10px;color:var(--muted);letter-spacing:.5px;text-transform:uppercase;margin-bottom:4px}
.stat-value{font-family:'Syne',sans-serif;font-weight:700;font-size:15px}
.stat-sub{font-size:11px;color:var(--muted);margin-top:2px}

/* SECTION HEADERS */
.section-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;margin-top:24px}
.section-title{font-family:'Syne',sans-serif;font-weight:700;font-size:16px;display:flex;align-items:center;gap:8px}
.section-title::before{content:'';width:3px;height:18px;background:var(--accent);border-radius:2px;display:inline-block}
.btn-sm{
  background:none;border:1px solid var(--border);color:var(--muted);
  padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Space Mono',monospace;
  font-size:11px;transition:all .2s;
}
.btn-sm:hover,.btn-sm.active{border-color:var(--accent);color:var(--accent);background:rgba(0,212,170,.06)}
.btn-group{display:flex;gap:4px}

/* CHART CONTAINERS */
.chart-wrap{position:relative;height:220px}
.chart-wrap-lg{position:relative;height:320px}
.chart-wrap-sm{position:relative;height:160px}

/* NEWS */
.news-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.news-card{
  background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:14px;cursor:pointer;transition:all .2s;text-decoration:none;color:inherit;display:block;
}
.news-card:hover{border-color:rgba(0,212,170,.3);background:var(--card2);transform:translateY(-2px)}
.news-sym{
  display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;
  background:rgba(0,212,170,.1);color:var(--accent);margin-bottom:8px;
}
.news-title{font-size:12px;line-height:1.5;margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.news-meta{font-size:10px;color:var(--muted);display:flex;justify-content:space-between}
.news-img{width:100%;height:100px;object-fit:cover;border-radius:6px;margin-bottom:8px;background:var(--bg3)}

/* SECTOR BARS */
.sector-item{margin-bottom:10px}
.sector-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;font-size:12px}
.sector-bar-wrap{height:5px;background:var(--bg3);border-radius:3px;overflow:hidden}
.sector-bar{height:100%;border-radius:3px;transition:width 1s ease}

/* STOCK PAGE */
.stock-hero{
  background:linear-gradient(135deg,var(--card) 0%,var(--card2) 100%);
  border:1px solid var(--border);border-radius:14px;padding:24px;margin-bottom:20px;
}
.stock-header{display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:16px}
.stock-company{display:flex;align-items:center;gap:14px}
.stock-logo{
  width:52px;height:52px;border-radius:10px;background:var(--bg3);
  display:flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;
  font-weight:800;font-size:16px;color:var(--accent);border:1px solid var(--border);
  overflow:hidden;
}
.stock-logo img{width:100%;height:100%;object-fit:contain;padding:4px}
.stock-name{font-family:'Syne',sans-serif;font-weight:800;font-size:22px}
.stock-sym-ex{font-size:12px;color:var(--muted);margin-top:2px}
.stock-price-block{text-align:right}
.stock-price{font-family:'Syne',sans-serif;font-weight:800;font-size:36px}
.stock-change{font-size:16px;margin-top:4px}
.tab-bar{display:flex;gap:2px;margin-bottom:16px;border-bottom:1px solid var(--border);padding-bottom:0}
.tab-btn{
  padding:9px 16px;border:none;background:none;color:var(--muted);cursor:pointer;
  font-family:'Space Mono',monospace;font-size:12px;border-bottom:2px solid transparent;
  margin-bottom:-1px;transition:all .2s;
}
.tab-btn.active,.tab-btn:hover{color:var(--accent);border-bottom-color:var(--accent)}
.tab-pane{display:none}
.tab-pane.active{display:block;animation:fadeUp .25s ease}

/* FINANCIAL TABLE */
.fin-table th{background:var(--bg3);position:sticky;top:0}
.fin-table td:first-child{color:var(--muted);font-size:11px}

/* SPINNER / LOADER */
.loader{display:flex;align-items:center;justify-content:center;padding:40px;color:var(--muted)}
.spinner{
  width:24px;height:24px;border:2px solid var(--border);
  border-top-color:var(--accent);border-radius:50%;
  animation:spin .7s linear infinite;margin-right:10px;
}
@keyframes spin{to{transform:rotate(360deg)}}

/* PILL STATS (stock overview) */
.pill-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px}
.pill{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:12px}
.pill-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.pill-value{font-family:'Syne',sans-serif;font-weight:700;font-size:14px}

/* GAUGE */
.gauge-wrap{display:flex;flex-direction:column;align-items:center;padding:10px 0}
.gauge-label{font-size:11px;color:var(--muted);margin-top:6px}
.gauge-value{font-family:'Syne',sans-serif;font-weight:700;font-size:22px;margin-top:4px}

/* PROGRESS BAR */
.progress-wrap{background:var(--bg3);border-radius:4px;height:6px;overflow:hidden;margin:4px 0}
.progress-fill{height:100%;border-radius:4px;transition:width 1s ease}

/* TOOLTIP STYLE */
.ct{position:fixed;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:10px 14px;pointer-events:none;z-index:999;font-size:12px;display:none;box-shadow:0 10px 30px rgba(0,0,0,.5)}

/* CRYPTO / FOREX CARDS */
.asset-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.asset-card{
  background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:14px;transition:all .2s;
}
.asset-card:hover{border-color:rgba(0,212,170,.25);background:var(--card2)}
.asset-icon{font-size:22px;margin-bottom:8px}
.asset-name{font-size:11px;color:var(--muted);margin-bottom:2px}
.asset-price{font-family:'Syne',sans-serif;font-weight:700;font-size:16px;margin-bottom:2px}
.asset-chg{font-size:12px}

/* RESPONSIVE */
@media(max-width:1200px){
  .grid-4,.grid-5{grid-template-columns:repeat(3,1fr)}
  .idx-grid{grid-template-columns:repeat(3,1fr)}
  .asset-grid{grid-template-columns:repeat(3,1fr)}
  .news-grid{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:900px){
  .grid-3,.grid-4,.grid-5{grid-template-columns:repeat(2,1fr)}
  .grid-2{grid-template-columns:1fr}
  .idx-grid{grid-template-columns:repeat(2,1fr)}
  .pill-grid{grid-template-columns:repeat(2,1fr)}
  .asset-grid{grid-template-columns:repeat(2,1fr)}
  .news-grid{grid-template-columns:1fr}
  nav{display:none}
  .stat-row{flex-wrap:wrap}
  .stat-item{min-width:50%}
}
@media(max-width:600px){
  main{padding:14px 14px 40px}
  .idx-grid{grid-template-columns:1fr 1fr}
  #global-search{width:160px}
}

/* ANIMATIONS */
.fade-in{animation:fadeUp .4s ease both}
.stagger-1{animation-delay:.05s}
.stagger-2{animation-delay:.1s}
.stagger-3{animation-delay:.15s}
.stagger-4{animation-delay:.2s}

/* Market status */
.market-status{
  display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);
}
.status-dot{width:7px;height:7px;border-radius:50%;background:var(--green);animation:pulse 2s ease-in-out infinite}
.status-dot.closed{background:var(--red);animation:none}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(1.3)}}

/* Empty state */
.empty{padding:40px;text-align:center;color:var(--muted)}
.empty svg{margin:0 auto 12px;opacity:.3}

/* Description clamp */
.desc{color:var(--muted);font-size:12px;line-height:1.7;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;font-family:'Space Mono',monospace}
.desc.expanded{-webkit-line-clamp:unset}
.show-more{color:var(--accent);cursor:pointer;font-size:11px;margin-top:4px;display:inline-block}
</style>
</head>
<body>

<div class="ct" id="tooltip"></div>

<!-- HEADER -->
<header>
  <a class="logo" href="#" onclick="showPage('dashboard');return false">
    <div class="logo-mark">G</div>
    <span class="logo-text">Global<span>Markets</span></span>
  </a>
  <nav>
    <button class="nav-btn active" onclick="showPage('dashboard')">Dashboard</button>
    <button class="nav-btn" onclick="showPage('markets')">Markets</button>
    <button class="nav-btn" onclick="showPage('crypto-page')">Crypto</button>
    <button class="nav-btn" onclick="showPage('forex-page')">Forex</button>
    <button class="nav-btn" onclick="showPage('commodities-page')">Commodities</button>
    <button class="nav-btn" onclick="showPage('news-page')">News</button>
  </nav>
  <div class="header-right">
    <div class="market-status" id="market-status">
      <div class="status-dot" id="status-dot"></div>
      <span id="status-text">Market Open</span>
    </div>
    <div class="search-wrap">
      <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input type="text" id="global-search" placeholder="Search symbol or company..." autocomplete="off">
      <div id="search-results"></div>
    </div>
  </div>
</header>

<!-- TICKER BAR -->
<div class="ticker-bar">
  <div class="ticker-track" id="ticker-track">
    <div class="tick-item"><span class="tick-sym">Loading…</span></div>
  </div>
</div>

<!-- PAGES -->
<main>

<!-- ══════════════════════════════════════
     DASHBOARD PAGE
══════════════════════════════════════ -->
<div class="page active" id="dashboard">

  <!-- Indices strip -->
  <div class="idx-grid" id="idx-grid">
    <div class="loader"><div class="spinner"></div>Loading indices…</div>
  </div>

  <!-- Main 2-col layout -->
  <div style="display:grid;grid-template-columns:1fr 360px;gap:16px">

    <!-- Left column -->
    <div>
      <!-- Index chart -->
      <div class="card" style="margin-bottom:16px">
        <div class="card-header">
          <span class="card-title" id="chart-title">S&P 500 — ^GSPC</span>
          <div style="display:flex;gap:6px;align-items:center">
            <div class="btn-group" id="period-btns">
              <button class="btn-sm" onclick="loadIndexChart('1month')">1M</button>
              <button class="btn-sm active" onclick="loadIndexChart('3month')">3M</button>
              <button class="btn-sm" onclick="loadIndexChart('6month')">6M</button>
              <button class="btn-sm" onclick="loadIndexChart('1year')">1Y</button>
              <button class="btn-sm" onclick="loadIndexChart('5year')">5Y</button>
            </div>
          </div>
        </div>
        <div class="card-body">
          <div class="chart-wrap-lg">
            <canvas id="index-chart"></canvas>
          </div>
        </div>
      </div>

      <!-- Gainers / Losers / Active tabs -->
      <div class="card">
        <div class="card-header">
          <div class="tab-bar" style="border:none;margin:0;padding:0">
            <button class="tab-btn active" onclick="switchMoverTab('gainers',this)">🚀 Top Gainers</button>
            <button class="tab-btn" onclick="switchMoverTab('losers',this)">📉 Top Losers</button>
            <button class="tab-btn" onclick="switchMoverTab('active',this)">🔥 Most Active</button>
          </div>
          <span class="card-tag" id="mover-tag">US Markets</span>
        </div>
        <div id="mover-body"><div class="loader"><div class="spinner"></div>Loading…</div></div>
      </div>
    </div>

    <!-- Right column -->
    <div style="display:flex;flex-direction:column;gap:16px">

      <!-- Sector Performance -->
      <div class="card">
        <div class="card-header"><span class="card-title">Sector Performance</span><span class="card-tag">Today</span></div>
        <div class="card-body" id="sector-body"><div class="loader" style="padding:20px"><div class="spinner"></div></div></div>
      </div>

      <!-- Quick Stats -->
      <div class="card">
        <div class="card-header"><span class="card-title">Market Snapshot</span></div>
        <div class="card-body" id="snapshot-body"><div class="loader" style="padding:20px"><div class="spinner"></div></div></div>
      </div>

    </div>
  </div>

  <!-- News -->
  <div class="section-head"><div class="section-title">Latest Market News</div><button class="btn-sm" onclick="showPage('news-page')">View All →</button></div>
  <div class="news-grid" id="home-news"><div class="loader"><div class="spinner"></div>Loading news…</div></div>

</div>


<!-- ══════════════════════════════════════
     MARKETS PAGE
══════════════════════════════════════ -->
<div class="page" id="markets">
  <div class="section-head" style="margin-top:0"><div class="section-title">Global Markets</div></div>

  <div class="grid-2" style="margin-bottom:16px">
    <div class="card">
      <div class="card-header"><span class="card-title">Major Indices</span></div>
      <div id="markets-indices"><div class="loader"><div class="spinner"></div></div></div>
    </div>
    <div class="card">
      <div class="card-header"><span class="card-title">Sector Heatmap</span><span class="card-tag blue">P/E Ratios</span></div>
      <div class="card-body" id="markets-sector"><div class="loader" style="padding:20px"><div class="spinner"></div></div></div>
    </div>
  </div>

  <div class="grid-3">
    <div class="card">
      <div class="card-header"><span class="card-title">🚀 Top Gainers</span></div>
      <div id="m-gainers"><div class="loader"><div class="spinner"></div></div></div>
    </div>
    <div class="card">
      <div class="card-header"><span class="card-title">📉 Top Losers</span></div>
      <div id="m-losers"><div class="loader"><div class="spinner"></div></div></div>
    </div>
    <div class="card">
      <div class="card-header"><span class="card-title">🔥 Most Active</span></div>
      <div id="m-active"><div class="loader"><div class="spinner"></div></div></div>
    </div>
  </div>
</div>


<!-- ══════════════════════════════════════
     CRYPTO PAGE
══════════════════════════════════════ -->
<div class="page" id="crypto-page">
  <div class="section-head" style="margin-top:0"><div class="section-title">Cryptocurrency Markets</div><span class="card-tag">Live Prices</span></div>
  <div class="asset-grid" id="crypto-grid"><div class="loader"><div class="spinner"></div>Loading…</div></div>
  <div style="margin-top:20px" class="card">
    <div class="card-header"><span class="card-title">Crypto Performance Table</span></div>
    <div id="crypto-table"></div>
  </div>
</div>


<!-- ══════════════════════════════════════
     FOREX PAGE
══════════════════════════════════════ -->
<div class="page" id="forex-page">
  <div class="section-head" style="margin-top:0"><div class="section-title">Forex Markets</div><span class="card-tag">Major Pairs</span></div>
  <div class="asset-grid" id="forex-grid"><div class="loader"><div class="spinner"></div>Loading…</div></div>
  <div style="margin-top:20px" class="card">
    <div class="card-header"><span class="card-title">Currency Pairs Table</span></div>
    <div id="forex-table"></div>
  </div>
</div>


<!-- ══════════════════════════════════════
     COMMODITIES PAGE
══════════════════════════════════════ -->
<div class="page" id="commodities-page">
  <div class="section-head" style="margin-top:0"><div class="section-title">Commodities</div><span class="card-tag">Global</span></div>
  <div class="card">
    <div class="card-header"><span class="card-title">Commodities Overview</span></div>
    <div id="commodities-body"><div class="loader"><div class="spinner"></div>Loading…</div></div>
  </div>
</div>


<!-- ══════════════════════════════════════
     NEWS PAGE
══════════════════════════════════════ -->
<div class="page" id="news-page">
  <div class="section-head" style="margin-top:0"><div class="section-title">Financial News</div></div>
  <div class="news-grid" id="news-grid"><div class="loader"><div class="spinner"></div>Loading…</div></div>
</div>


<!-- ══════════════════════════════════════
     STOCK DETAIL PAGE
══════════════════════════════════════ -->
<div class="page" id="stock-page">
  <button class="btn-sm" onclick="historyBack()" style="margin-bottom:14px">← Back</button>
  <div id="stock-content"><div class="loader"><div class="spinner"></div>Loading stock data…</div></div>
</div>

</main>

<script>
// ═══════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════
let currentIndex = '^GSPC';
let currentIndexName = 'S&P 500';
let currentPeriod = '3month';
let indexChartInstance = null;
let moverData = {gainers:[],losers:[],active:[]};
let currentMover = 'gainers';
let pageHistory = ['dashboard'];

const FMT = new Intl.NumberFormat('en-US',{maximumFractionDigits:2});
const FMT2 = new Intl.NumberFormat('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const FMTB = new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:2});

function fmt(n){return n==null||isNaN(n)?'—':FMT.format(n)}
function fmt2(n){return n==null||isNaN(n)?'—':FMT2.format(n)}
function fmtB(n){return n==null||isNaN(n)?'—':FMTB.format(n)}
function fmtPct(n){if(n==null||isNaN(n))return'—';const s=parseFloat(n).toFixed(2);return(n>=0?'+':'')+s+'%'}
function colorClass(n){return parseFloat(n)>=0?'pos':'neg'}
function timeAgo(dt){
  const d=new Date(dt),now=new Date();
  const diff=(now-d)/1000;
  if(diff<60)return Math.round(diff)+'s ago';
  if(diff<3600)return Math.round(diff/60)+'m ago';
  if(diff<86400)return Math.round(diff/3600)+'h ago';
  return Math.round(diff/86400)+'d ago';
}
function cleanSymbol(s){return s.replace(/\^/,'').replace(/USD$/,'').replace(/=X$/,'')}
const CRYPTO_EMOJI={BTC:'₿',ETH:'Ξ',XRP:'✕',BNB:'◆',SOL:'◎',ADA:'₳',DOGE:'Ð',AVAX:'△',DOT:'●',MATIC:'⬡'};

// ═══════════════════════════════════════════
//  PAGE NAVIGATION
// ═══════════════════════════════════════════
function showPage(id, push=true){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>{
    b.classList.toggle('active', b.textContent.toLowerCase().includes(id.replace('-page','').replace('dashboard','dashboard').split('-')[0]));
  });
  const page = document.getElementById(id);
  if(!page) return;
  page.classList.add('active');
  if(push && pageHistory[pageHistory.length-1]!==id) pageHistory.push(id);
  window.scrollTo({top:0,behavior:'smooth'});
  // Lazy load page data
  const loaders={
    'markets': loadMarketsPage,
    'crypto-page': loadCryptoPage,
    'forex-page': loadForexPage,
    'commodities-page': loadCommoditiesPage,
    'news-page': loadNewsPage,
  };
  if(loaders[id]) loaders[id]();
}
function historyBack(){
  if(pageHistory.length>1){pageHistory.pop();showPage(pageHistory[pageHistory.length-1],false);}
}

// ═══════════════════════════════════════════
//  FETCH HELPERS
// ═══════════════════════════════════════════
async function apiFetch(path){
  const r = await fetch(path);
  return r.json();
}

// ═══════════════════════════════════════════
//  TICKER BAR
// ═══════════════════════════════════════════
async function loadTicker(){
  try{
    const data = await apiFetch('/api/indices');
    if(!Array.isArray(data)||!data.length) return;
    const items = data.map(q=>{
      const chg = q.change||0;
      const cls = chg>=0?'pos':'neg';
      return `<div class="tick-item">
        <span class="tick-sym">${q.symbol.replace('^','')}</span>
        <span class="tick-price">${fmt2(q.price)}</span>
        <span class="${cls}">${fmtPct(q.changesPercentage)}</span>
      </div>`;
    });
    const html = items.join('')+items.join(''); // duplicate for seamless loop
    const track = document.getElementById('ticker-track');
    track.innerHTML = html;
  }catch(e){}
}

// ═══════════════════════════════════════════
//  INDICES STRIP
// ═══════════════════════════════════════════
const INDEX_META = {
  '^GSPC':{name:'S&P 500',short:'SPX'},'^IXIC':{name:'NASDAQ',short:'IXIC'},
  '^DJI':{name:'Dow Jones',short:'DJIA'},'^RUT':{name:'Russell 2000',short:'RUT'},
  '^FTSE':{name:'FTSE 100',short:'FTSE'},'^N225':{name:'Nikkei 225',short:'N225'},
  '^HSI':{name:'Hang Seng',short:'HSI'},'^GDAXI':{name:'DAX',short:'DAX'},
  '^FCHI':{name:'CAC 40',short:'CAC'},'^STOXX50E':{name:'Euro Stoxx 50',short:'SX5E'}
};
async function loadIndices(){
  try{
    const data = await apiFetch('/api/indices');
    if(!Array.isArray(data)) return;
    const grid = document.getElementById('idx-grid');
    grid.innerHTML = data.map(q=>{
      const meta = INDEX_META[q.symbol]||{name:q.symbol,short:q.symbol};
      const chg = q.changesPercentage||0;
      const cls = chg>=0?'pos':'neg';
      return `<div class="idx-card ${q.symbol===currentIndex?'selected':''}" onclick="selectIndex('${q.symbol}','${meta.name}')">
        <div class="idx-name">${meta.short}</div>
        <div class="idx-price">${fmt2(q.price)}</div>
        <div class="idx-chg ${cls}">${fmtPct(chg)}</div>
      </div>`;
    }).join('');
  }catch(e){}
}

function selectIndex(sym, name){
  currentIndex = sym;
  currentIndexName = name;
  document.querySelectorAll('.idx-card').forEach(c=>c.classList.remove('selected'));
  event.currentTarget.classList.add('selected');
  document.getElementById('chart-title').textContent = name+' — '+sym;
  loadIndexChart(currentPeriod);
}

// ═══════════════════════════════════════════
//  INDEX CHART
// ═══════════════════════════════════════════
async function loadIndexChart(period){
  currentPeriod = period;
  document.querySelectorAll('#period-btns .btn-sm').forEach(b=>{
    b.classList.toggle('active',b.textContent.toLowerCase()===period.replace('month','m').replace('year','y'));
  });
  try{
    const data = await apiFetch(`/api/history/${encodeURIComponent(currentIndex)}?period=${period}`);
    if(!Array.isArray(data)||!data.length) return;
    const reversed = [...data].reverse();
    const labels = reversed.map(d=>d.date);
    const prices = reversed.map(d=>d.close||d.price);
    const up = prices[prices.length-1] >= prices[0];
    const color = up ? '#22c55e' : '#ef4444';
    const bgColor = up ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)';
    const ctx = document.getElementById('index-chart').getContext('2d');
    if(indexChartInstance) indexChartInstance.destroy();
    indexChartInstance = new Chart(ctx,{
      type:'line',
      data:{
        labels,
        datasets:[{
          data:prices,label:'Price',
          borderColor:color,backgroundColor:bgColor,
          borderWidth:2,fill:true,tension:0.3,
          pointRadius:0,pointHoverRadius:4,
          pointHoverBackgroundColor:color,
        }]
      },
      options:{
        responsive:true,maintainAspectRatio:false,
        plugins:{legend:{display:false},tooltip:{
          mode:'index',intersect:false,
          backgroundColor:'#111827',borderColor:'#1e2d45',borderWidth:1,
          titleColor:'#64748b',bodyColor:'#e2e8f0',
          callbacks:{label:ctx=>'$'+fmt2(ctx.parsed.y)}
        }},
        scales:{
          x:{grid:{color:'rgba(30,45,69,.4)',drawTicks:false},ticks:{color:'#64748b',maxTicksLimit:8,maxRotation:0}},
          y:{grid:{color:'rgba(30,45,69,.4)',drawTicks:false},ticks:{color:'#64748b',callback:v=>'$'+FMT.format(v)},position:'right'}
        },
        interaction:{mode:'index',intersect:false}
      }
    });
  }catch(e){}
}

// ═══════════════════════════════════════════
//  MOVERS (Gainers / Losers / Active)
// ═══════════════════════════════════════════
async function loadMovers(){
  try{
    const [g,l,a] = await Promise.all([
      apiFetch('/api/gainers'),apiFetch('/api/losers'),apiFetch('/api/actives')
    ]);
    moverData = {gainers:Array.isArray(g)?g:[],losers:Array.isArray(l)?l:[],active:Array.isArray(a)?a:[]};
    renderMovers(currentMover);
  }catch(e){
    document.getElementById('mover-body').innerHTML='<div class="empty">Failed to load</div>';
  }
}
function switchMoverTab(type, btn){
  currentMover = type;
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderMovers(type);
}
function renderMovers(type){
  const data = moverData[type]||[];
  if(!data.length){document.getElementById('mover-body').innerHTML='<div class="empty">No data</div>';return;}
  const rows = data.slice(0,10).map(s=>{
    const chg = s.changesPercentage||s.change||0;
    const cls = parseFloat(chg)>=0?'pos':'neg';
    return `<tr onclick="loadStockPage('${s.symbol}')" style="cursor:pointer">
      <td><div class="sym-cell">${s.symbol}</div><div class="sym-sub">${(s.name||'').slice(0,28)}</div></td>
      <td class="num-right">${fmt2(s.price)}</td>
      <td class="num-right"><span class="badge ${parseFloat(chg)>=0?'up':'dn'}">${fmtPct(chg)}</span></td>
      <td class="num-right" style="color:var(--muted)">${fmtB(s.volume||0)}</td>
    </tr>`;
  }).join('');
  document.getElementById('mover-body').innerHTML=`
    <table><thead><tr>
      <th>Symbol</th><th class="num-right">Price</th>
      <th class="num-right">Change</th><th class="num-right">Volume</th>
    </tr></thead><tbody>${rows}</tbody></table>`;
}

// ═══════════════════════════════════════════
//  SECTOR PERFORMANCE
// ═══════════════════════════════════════════
async function loadSectors(){
  try{
    const data = await apiFetch('/api/sector');
    if(!Array.isArray(data)||!data.length){document.getElementById('sector-body').innerHTML='<div class="empty">No data</div>';return;}
    const sorted = [...data].sort((a,b)=>parseFloat(b.changesPercentage)-parseFloat(a.changesPercentage));
    const max = Math.max(...sorted.map(s=>Math.abs(parseFloat(s.changesPercentage))));
    document.getElementById('sector-body').innerHTML = sorted.map(s=>{
      const pct = parseFloat(s.changesPercentage)||0;
      const w = max>0?(Math.abs(pct)/max*100):0;
      const color = pct>=0?'var(--green)':'var(--red)';
      const cls = pct>=0?'pos':'neg';
      return `<div class="sector-item">
        <div class="sector-row">
          <span>${s.sector||s.name}</span>
          <span class="${cls}">${fmtPct(pct)}</span>
        </div>
        <div class="sector-bar-wrap"><div class="sector-bar" style="width:${w}%;background:${color}"></div></div>
      </div>`;
    }).join('');
  }catch(e){}
}

// ═══════════════════════════════════════════
//  MARKET SNAPSHOT (right panel)
// ═══════════════════════════════════════════
async function loadSnapshot(){
  try{
    const [g,l,a] = await Promise.all([
      apiFetch('/api/gainers'),apiFetch('/api/losers'),apiFetch('/api/actives')
    ]);
    const gainers = Array.isArray(g)?g:[];
    const losers  = Array.isArray(l)?l:[];
    const total   = gainers.length + losers.length;
    const bullPct = total>0?Math.round(gainers.length/(total)*100):50;
    document.getElementById('snapshot-body').innerHTML=`
      <div style="margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px">
          <span style="color:var(--green)">▲ Advancing ${gainers.length}</span>
          <span style="color:var(--red)">▼ Declining ${losers.length}</span>
        </div>
        <div style="height:8px;background:rgba(239,68,68,.3);border-radius:4px;overflow:hidden">
          <div style="height:100%;width:${bullPct}%;background:var(--green);border-radius:4px"></div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
        ${gainers.slice(0,1).map(s=>`<div class="pill"><div class="pill-label">Top Gainer</div><div class="pill-value" style="color:var(--green)">${s.symbol}</div><div style="font-size:11px;color:var(--green)">${fmtPct(s.changesPercentage)}</div></div>`).join('')}
        ${losers.slice(0,1).map(s=>`<div class="pill"><div class="pill-label">Top Loser</div><div class="pill-value" style="color:var(--red)">${s.symbol}</div><div style="font-size:11px;color:var(--red)">${fmtPct(s.changesPercentage)}</div></div>`).join('')}
      </div>
      <div style="margin-top:10px">
        <div class="pill-label" style="margin-bottom:6px">Most Active Today</div>
        ${(Array.isArray(a)?a:[]).slice(0,3).map(s=>`<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);font-size:12px"><span style="color:var(--accent);font-weight:700;cursor:pointer" onclick="loadStockPage('${s.symbol}')">${s.symbol}</span><span>${fmt2(s.price)}</span><span class="${colorClass(s.changesPercentage)}">${fmtPct(s.changesPercentage)}</span></div>`).join('')}
      </div>`;
  }catch(e){}
}

// ═══════════════════════════════════════════
//  HOME NEWS
// ═══════════════════════════════════════════
async function loadHomeNews(){
  try{
    const data = await apiFetch('/api/news?limit=6');
    renderNewsGrid(data, 'home-news');
  }catch(e){}
}

function renderNewsGrid(data, containerId){
  const arr = Array.isArray(data)?data:[];
  if(!arr.length){document.getElementById(containerId).innerHTML='<div class="empty">No news found</div>';return;}
  document.getElementById(containerId).innerHTML = arr.slice(0,24).map(n=>`
    <a href="${n.url||'#'}" target="_blank" rel="noopener" class="news-card fade-in">
      ${n.image?`<img class="news-img" src="${n.image}" alt="" onerror="this.style.display='none'">`:''}
      ${n.symbol?`<div class="news-sym">${n.symbol}</div>`:'<div class="news-sym">MARKETS</div>'}
      <div class="news-title">${n.title||''}</div>
      <div class="news-meta">
        <span>${n.site||n.publisher||''}</span>
        <span>${timeAgo(n.publishedDate||n.date||'')}</span>
      </div>
    </a>`).join('');
}

// ═══════════════════════════════════════════
//  MARKETS PAGE
// ═══════════════════════════════════════════
async function loadMarketsPage(){
  const mi = document.getElementById('markets-indices');
  if(!mi||mi.querySelector('table')) return; // already loaded
  try{
    const data = await apiFetch('/api/indices');
    if(!Array.isArray(data)) return;
    const rows = data.map(q=>{
      const meta = INDEX_META[q.symbol]||{name:q.symbol};
      const chg = q.changesPercentage||0;
      return `<tr>
        <td><div class="sym-cell">${q.symbol.replace('^','')}</div><div class="sym-sub">${meta.name}</div></td>
        <td class="num-right">${fmt2(q.price)}</td>
        <td class="num-right"><span class="badge ${chg>=0?'up':'dn'}">${fmtPct(chg)}</span></td>
        <td class="num-right" style="color:var(--muted)">${fmtB(q.volume||0)}</td>
      </tr>`;
    }).join('');
    mi.innerHTML=`<table><thead><tr><th>Index</th><th class="num-right">Price</th><th class="num-right">Change</th><th class="num-right">Volume</th></tr></thead><tbody>${rows}</tbody></table>`;

    // Sector for markets page
    const sd = await apiFetch('/api/sector');
    if(Array.isArray(sd)){
      const sorted=[...sd].sort((a,b)=>parseFloat(b.changesPercentage)-parseFloat(a.changesPercentage));
      const max=Math.max(...sorted.map(s=>Math.abs(parseFloat(s.changesPercentage))));
      document.getElementById('markets-sector').innerHTML=sorted.map(s=>{
        const p=parseFloat(s.changesPercentage)||0;
        const w=max>0?(Math.abs(p)/max*100):0;
        const c=p>=0?'var(--green)':'var(--red)';
        return `<div class="sector-item"><div class="sector-row"><span>${s.sector||s.name}</span><span class="${p>=0?'pos':'neg'}">${fmtPct(p)}</span></div><div class="sector-bar-wrap"><div class="sector-bar" style="width:${w}%;background:${c}"></div></div></div>`;
      }).join('');
    }

    // Gainers/Losers/Active for markets page
    const [g,l,a]=await Promise.all([apiFetch('/api/gainers'),apiFetch('/api/losers'),apiFetch('/api/actives')]);
    const tbl=(data,id)=>{
      if(!Array.isArray(data)){document.getElementById(id).innerHTML='<div class="empty">No data</div>';return;}
      const rows=data.slice(0,10).map(s=>`<tr onclick="loadStockPage('${s.symbol}')" style="cursor:pointer"><td><div class="sym-cell">${s.symbol}</div><div class="sym-sub">${(s.name||'').slice(0,22)}</div></td><td class="num-right">${fmt2(s.price)}</td><td class="num-right"><span class="badge ${parseFloat(s.changesPercentage||s.change||0)>=0?'up':'dn'}">${fmtPct(s.changesPercentage||s.change||0)}</span></td></tr>`).join('');
      document.getElementById(id).innerHTML=`<table><thead><tr><th>Symbol</th><th class="num-right">Price</th><th class="num-right">Chg%</th></tr></thead><tbody>${rows}</tbody></table>`;
    };
    tbl(g,'m-gainers');tbl(l,'m-losers');tbl(a,'m-active');
  }catch(e){}
}

// ═══════════════════════════════════════════
//  CRYPTO PAGE
// ═══════════════════════════════════════════
async function loadCryptoPage(){
  const cg=document.getElementById('crypto-grid');
  if(!cg||cg.querySelector('.asset-card')) return;
  try{
    const data=await apiFetch('/api/crypto');
    if(!Array.isArray(data)){cg.innerHTML='<div class="empty">No data</div>';return;}
    const NAMES={BTCUSD:'Bitcoin',ETHUSD:'Ethereum',XRPUSD:'Ripple',BNBUSD:'BNB',SOLUSD:'Solana',ADAUSD:'Cardano',DOGEUSD:'Dogecoin',AVAXUSD:'Avalanche',DOTUSD:'Polkadot',MATICUSD:'Polygon'};
    cg.innerHTML=data.map(c=>{
      const sym=c.symbol.replace('USD','');
      const chg=c.changesPercentage||0;
      const emoji=CRYPTO_EMOJI[sym]||'◎';
      return `<div class="asset-card" onclick="loadStockPage('${c.symbol}')">
        <div class="asset-icon">${emoji}</div>
        <div class="asset-name">${NAMES[c.symbol]||sym}</div>
        <div class="asset-price">$${fmt2(c.price)}</div>
        <div class="asset-chg ${colorClass(chg)}">${fmtPct(chg)}</div>
      </div>`;
    }).join('');

    const rows=data.map(c=>{
      const chg=c.changesPercentage||0;
      return `<tr onclick="loadStockPage('${c.symbol}')" style="cursor:pointer">
        <td><div class="sym-cell">${c.symbol.replace('USD','')}</div></td>
        <td class="num-right">$${fmt2(c.price)}</td>
        <td class="num-right"><span class="badge ${chg>=0?'up':'dn'}">${fmtPct(chg)}</span></td>
        <td class="num-right" style="color:var(--muted)">${fmtB(c.volume||0)}</td>
        <td class="num-right" style="color:var(--muted)">${fmtB(c.marketCap||0)}</td>
      </tr>`;
    }).join('');
    document.getElementById('crypto-table').innerHTML=`<table><thead><tr><th>Asset</th><th class="num-right">Price</th><th class="num-right">24h Change</th><th class="num-right">Volume</th><th class="num-right">Mkt Cap</th></tr></thead><tbody>${rows}</tbody></table>`;
  }catch(e){}
}

// ═══════════════════════════════════════════
//  FOREX PAGE
// ═══════════════════════════════════════════
async function loadForexPage(){
  const fg=document.getElementById('forex-grid');
  if(!fg||fg.querySelector('.asset-card')) return;
  try{
    const data=await apiFetch('/api/forex');
    if(!Array.isArray(data)){fg.innerHTML='<div class="empty">No data</div>';return;}
    const FLAGS={EUR:'🇪🇺',GBP:'🇬🇧',JPY:'🇯🇵',AUD:'🇦🇺',CAD:'🇨🇦',CHF:'🇨🇭',NZD:'🇳🇿',CNY:'🇨🇳',INR:'🇮🇳',BRL:'🇧🇷',USD:'🇺🇸'};
    fg.innerHTML=data.map(c=>{
      const sym=c.symbol.replace('=X','');
      const flag=FLAGS[sym.slice(0,3)]||'💱';
      const chg=c.changesPercentage||0;
      return `<div class="asset-card">
        <div class="asset-icon">${flag}</div>
        <div class="asset-name">${sym}</div>
        <div class="asset-price">${fmt(c.price)}</div>
        <div class="asset-chg ${colorClass(chg)}">${fmtPct(chg)}</div>
      </div>`;
    }).join('');

    const rows=data.map(c=>{
      const chg=c.changesPercentage||0;
      return `<tr><td class="sym-cell">${c.symbol.replace('=X','')}</td><td class="num-right">${fmt2(c.price)}</td><td class="num-right"><span class="badge ${chg>=0?'up':'dn'}">${fmtPct(chg)}</span></td><td class="num-right" style="color:var(--muted)">${fmtB(c.volume||0)}</td></tr>`;
    }).join('');
    document.getElementById('forex-table').innerHTML=`<table><thead><tr><th>Pair</th><th class="num-right">Rate</th><th class="num-right">Change</th><th class="num-right">Volume</th></tr></thead><tbody>${rows}</tbody></table>`;
  }catch(e){}
}

// ═══════════════════════════════════════════
//  COMMODITIES PAGE
// ═══════════════════════════════════════════
async function loadCommoditiesPage(){
  const cb=document.getElementById('commodities-body');
  if(!cb||cb.querySelector('table')) return;
  try{
    const data=await apiFetch('/api/commodities');
    if(!Array.isArray(data)){cb.innerHTML='<div class="empty">No data</div>';return;}
    const rows=data.slice(0,30).map(c=>{
      const chg=c.changesPercentage||0;
      return `<tr>
        <td><div class="sym-cell">${c.symbol}</div><div class="sym-sub">${(c.name||'').slice(0,30)}</div></td>
        <td class="num-right">${fmt2(c.price)}</td>
        <td class="num-right"><span class="badge ${chg>=0?'up':'dn'}">${fmtPct(chg)}</span></td>
        <td class="num-right" style="color:var(--muted)">${fmt2(c.dayLow||0)} / ${fmt2(c.dayHigh||0)}</td>
        <td class="num-right" style="color:var(--muted)">${fmtB(c.volume||0)}</td>
      </tr>`;
    }).join('');
    cb.innerHTML=`<table><thead><tr><th>Commodity</th><th class="num-right">Price</th><th class="num-right">Change</th><th class="num-right">Day Range</th><th class="num-right">Volume</th></tr></thead><tbody>${rows}</tbody></table>`;
  }catch(e){}
}

// ═══════════════════════════════════════════
//  NEWS PAGE
// ═══════════════════════════════════════════
async function loadNewsPage(){
  const ng=document.getElementById('news-grid');
  if(!ng||ng.querySelector('.news-card')) return;
  try{
    const data=await apiFetch('/api/news?limit=24');
    renderNewsGrid(data,'news-grid');
  }catch(e){}
}

// ═══════════════════════════════════════════
//  STOCK DETAIL PAGE
// ═══════════════════════════════════════════
let stockChartInstance=null;
async function loadStockPage(symbol){
  showPage('stock-page');
  const sc=document.getElementById('stock-content');
  sc.innerHTML='<div class="loader"><div class="spinner"></div>Loading '+symbol+'…</div>';
  try{
    const [quote,profile]=await Promise.all([
      apiFetch('/api/quote/'+symbol),
      apiFetch('/api/profile/'+symbol)
    ]);
    const q=Array.isArray(quote)&&quote.length?quote[0]:(quote||{});
    const p=Array.isArray(profile)&&profile.length?profile[0]:(profile||{});
    const chg=q.changesPercentage||0;
    const logo=p.image||p.logo||'';
    const sym=cleanSymbol(symbol);
    sc.innerHTML=`
      <div class="stock-hero">
        <div class="stock-header">
          <div class="stock-company">
            <div class="stock-logo">${logo?`<img src="${logo}" alt="" onerror="this.style.display='none'">`:''}${sym.slice(0,2)}</div>
            <div>
              <div class="stock-name">${p.companyName||q.name||symbol}</div>
              <div class="stock-sym-ex">${symbol} · ${p.exchangeShortName||p.exchange||''} · ${p.sector||''} ${p.industry?'· '+p.industry:''}</div>
              ${p.website?`<a href="${p.website}" target="_blank" style="color:var(--accent);font-size:11px">${p.website}</a>`:''}
            </div>
          </div>
          <div class="stock-price-block">
            <div class="stock-price">${q.currency==='USD'||!q.currency?'$':''}${fmt2(q.price||p.price)}</div>
            <div class="stock-change ${colorClass(chg)}">${fmtPct(chg)} ${fmt2(Math.abs(q.change||0))}</div>
            <div style="font-size:11px;color:var(--muted);margin-top:4px">Updated: ${q.timestamp?new Date(q.timestamp*1000).toLocaleTimeString():''}</div>
          </div>
        </div>
        <div class="stat-row" style="margin-top:16px">
          <div class="stat-item"><div class="stat-label">Open</div><div class="stat-value">${fmt2(q.open)}</div></div>
          <div class="stat-item"><div class="stat-label">High</div><div class="stat-value" style="color:var(--green)">${fmt2(q.dayHigh||q.high)}</div></div>
          <div class="stat-item"><div class="stat-label">Low</div><div class="stat-value" style="color:var(--red)">${fmt2(q.dayLow||q.low)}</div></div>
          <div class="stat-item"><div class="stat-label">Volume</div><div class="stat-value">${fmtB(q.volume)}</div></div>
          <div class="stat-item"><div class="stat-label">Avg Vol</div><div class="stat-value">${fmtB(q.avgVolume)}</div></div>
          <div class="stat-item"><div class="stat-label">Mkt Cap</div><div class="stat-value">${fmtB(q.marketCap||p.mktCap)}</div></div>
          <div class="stat-item"><div class="stat-label">P/E</div><div class="stat-value">${fmt2(q.pe||p.pe)}</div></div>
          <div class="stat-item"><div class="stat-label">52W Range</div><div class="stat-value" style="font-size:11px">${fmt2(q.yearLow)} – ${fmt2(q.yearHigh)}</div></div>
        </div>
      </div>

      <div class="tab-bar">
        <button class="tab-btn active" onclick="switchStockTab('overview',this)">Overview</button>
        <button class="tab-btn" onclick="switchStockTab('financials',this)">Financials</button>
        <button class="tab-btn" onclick="switchStockTab('analyst',this)">Analyst</button>
        <button class="tab-btn" onclick="switchStockTab('news',this)">News</button>
      </div>

      <div class="tab-pane active" id="st-overview">
        <div style="display:grid;grid-template-columns:1fr 340px;gap:16px">
          <div>
            <div class="card" style="margin-bottom:16px">
              <div class="card-header">
                <span class="card-title">Price Chart</span>
                <div class="btn-group" id="stock-period-btns">
                  <button class="btn-sm" onclick="loadStockChart('${symbol}','1month',this)">1M</button>
                  <button class="btn-sm active" onclick="loadStockChart('${symbol}','3month',this)">3M</button>
                  <button class="btn-sm" onclick="loadStockChart('${symbol}','6month',this)">6M</button>
                  <button class="btn-sm" onclick="loadStockChart('${symbol}','1year',this)">1Y</button>
                  <button class="btn-sm" onclick="loadStockChart('${symbol}','5year',this)">5Y</button>
                </div>
              </div>
              <div class="card-body"><div class="chart-wrap-lg"><canvas id="stock-chart"></canvas></div></div>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;gap:14px">
            ${p.description?`<div class="card"><div class="card-header"><span class="card-title">About</span></div><div class="card-body"><p class="desc" id="stock-desc">${p.description}</p><span class="show-more" onclick="toggleDesc()">Show more</span></div></div>`:''}
            <div class="card">
              <div class="card-header"><span class="card-title">Key Stats</span></div>
              <div class="card-body" style="padding:0">
                <table>
                  ${[
                    ['Beta',fmt2(q.beta||p.beta)],
                    ['EPS (TTM)',fmt2(q.eps)],
                    ['Forward P/E',fmt2(p.forwardPE)],
                    ['P/B',fmt2(p.priceToBookRatio)],
                    ['ROE',p.returnOnEquity?(parseFloat(p.returnOnEquity)*100).toFixed(1)+'%':'—'],
                    ['Div Yield',p.lastDiv?fmt2(p.lastDiv):'—'],
                    ['Shares Out.',fmtB(p.sharesOutstanding)],
                    ['Employees',fmtB(p.fullTimeEmployees)],
                  ].map(([l,v])=>`<tr><td style="color:var(--muted);font-size:11px">${l}</td><td class="num-right">${v||'—'}</td></tr>`).join('')}
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="tab-pane" id="st-financials">
        <div class="loader" id="fin-loader"><div class="spinner"></div>Loading financials…</div>
        <div id="fin-content"></div>
      </div>

      <div class="tab-pane" id="st-analyst">
        <div class="loader" id="analyst-loader"><div class="spinner"></div>Loading analyst data…</div>
        <div id="analyst-content"></div>
      </div>

      <div class="tab-pane" id="st-news">
        <div class="loader" id="snews-loader"><div class="spinner"></div>Loading news…</div>
        <div class="news-grid" id="stock-news-grid"></div>
      </div>
    `;
    loadStockChart(symbol,'3month');
    loadStockFinancials(symbol);
    loadStockAnalyst(symbol);
    loadStockNews(symbol);
  }catch(e){sc.innerHTML='<div class="empty">Error loading stock data</div>';}
}

function toggleDesc(){
  const el=document.getElementById('stock-desc');
  el.classList.toggle('expanded');
  event.target.textContent=el.classList.contains('expanded')?'Show less':'Show more';
}

function switchStockTab(tab,btn){
  document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('st-'+tab).classList.add('active');
  btn.classList.add('active');
}

async function loadStockChart(symbol,period,btn){
  if(btn){
    document.querySelectorAll('#stock-period-btns .btn-sm').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
  }
  const canvas=document.getElementById('stock-chart');
  if(!canvas) return;
  try{
    const data=await apiFetch(`/api/history/${encodeURIComponent(symbol)}?period=${period}`);
    if(!Array.isArray(data)||!data.length) return;
    const rev=[...data].reverse();
    const labels=rev.map(d=>d.date);
    const prices=rev.map(d=>d.close||d.price);
    const up=prices[prices.length-1]>=prices[0];
    const color=up?'#22c55e':'#ef4444';
    const ctx=canvas.getContext('2d');
    if(stockChartInstance) stockChartInstance.destroy();
    stockChartInstance=new Chart(ctx,{
      type:'line',
      data:{labels,datasets:[{data:prices,label:'Price',borderColor:color,backgroundColor:up?'rgba(34,197,94,0.07)':'rgba(239,68,68,0.07)',borderWidth:2,fill:true,tension:0.3,pointRadius:0,pointHoverRadius:4,pointHoverBackgroundColor:color}]},
      options:{responsive:true,maintainAspectRatio:false,
        plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false,backgroundColor:'#111827',borderColor:'#1e2d45',borderWidth:1,titleColor:'#64748b',bodyColor:'#e2e8f0',callbacks:{label:c=>'$'+fmt2(c.parsed.y)}}},
        scales:{x:{grid:{color:'rgba(30,45,69,.4)',drawTicks:false},ticks:{color:'#64748b',maxTicksLimit:8,maxRotation:0}},y:{grid:{color:'rgba(30,45,69,.4)',drawTicks:false},ticks:{color:'#64748b',callback:v=>'$'+FMT.format(v)},position:'right'}},
        interaction:{mode:'index',intersect:false}}
    });
  }catch(e){}
}

async function loadStockFinancials(symbol){
  try{
    const [inc,bal,cf]=await Promise.all([
      apiFetch('/api/income/'+symbol),
      apiFetch('/api/balance/'+symbol),
      apiFetch('/api/cashflow/'+symbol)
    ]);
    const loader=document.getElementById('fin-loader');
    const content=document.getElementById('fin-content');
    if(loader) loader.style.display='none';

    const fmtFin=(n)=>{if(n==null||isNaN(n))return'—';const v=Math.abs(n);let s=n<0?'-':'';if(v>=1e12)return s+fmtB(v/1e12)+'T';if(v>=1e9)return s+(v/1e9).toFixed(2)+'B';if(v>=1e6)return s+(v/1e6).toFixed(1)+'M';return s+FMT.format(n);};

    const buildTable=(data,fields,title)=>{
      if(!Array.isArray(data)||!data.length) return `<div class="empty">No ${title} data</div>`;
      const yrs=data.slice(0,5);
      const hdr=yrs.map(y=>`<th class="num-right">${y.date?y.date.slice(0,4):''} ${y.period||''}</th>`).join('');
      const rows=fields.map(([key,label])=>{
        const cells=yrs.map(y=>{
          const v=y[key];
          const formatted=fmtFin(v);
          const color=v>0?'':'color:var(--red)';
          return `<td class="num-right" style="${color}">${formatted}</td>`;
        }).join('');
        return `<tr><td style="color:var(--muted);font-size:11px">${label}</td>${cells}</tr>`;
      }).join('');
      return `<h4 style="font-family:'Syne',sans-serif;font-size:13px;margin:16px 0 8px;color:var(--muted)">${title}</h4>
        <div style="overflow-x:auto"><table class="fin-table"><thead><tr><th style="min-width:160px">Metric</th>${hdr}</tr></thead><tbody>${rows}</tbody></table></div>`;
    };

    const incFields=[['revenue','Revenue'],['grossProfit','Gross Profit'],['operatingIncome','Operating Income'],['netIncome','Net Income'],['ebitda','EBITDA'],['eps','EPS'],['epsdiluted','EPS Diluted']];
    const balFields=[['totalAssets','Total Assets'],['totalCurrentAssets','Current Assets'],['cashAndCashEquivalents','Cash & Equiv.'],['totalDebt','Total Debt'],['totalLiabilities','Total Liabilities'],['totalStockholdersEquity','Shareholders Equity']];
    const cfFields=[['operatingCashFlow','Operating CF'],['capitalExpenditure','CapEx'],['freeCashFlow','Free Cash Flow'],['dividendsPaid','Dividends Paid'],['netCashUsedForInvestingActivites','Investing CF'],['netCashProvidedByOperatingActivities','Operating CF']];

    if(content) content.innerHTML=buildTable(inc,incFields,'Income Statement')+buildTable(bal,balFields,'Balance Sheet')+buildTable(cf,cfFields,'Cash Flow');
  }catch(e){
    const c=document.getElementById('fin-content');
    if(c) c.innerHTML='<div class="empty">Could not load financial data</div>';
    const l=document.getElementById('fin-loader');
    if(l) l.style.display='none';
  }
}

async function loadStockAnalyst(symbol){
  try{
    const [pt,grades]=await Promise.all([
      apiFetch('/api/price-target/'+symbol),
      apiFetch('/api/analyst/'+symbol)
    ]);
    const loader=document.getElementById('analyst-loader');
    const content=document.getElementById('analyst-content');
    if(loader) loader.style.display='none';

    const ptData=Array.isArray(pt)?pt[0]:pt||{};
    const estData=Array.isArray(grades)?grades:[];

    const ptHtml=`<div class="card" style="margin-bottom:16px">
      <div class="card-header"><span class="card-title">Price Target Consensus</span></div>
      <div class="card-body">
        <div class="stat-row" style="margin-bottom:0">
          <div class="stat-item"><div class="stat-label">Target High</div><div class="stat-value" style="color:var(--green)">$${fmt2(ptData.targetHigh)}</div></div>
          <div class="stat-item"><div class="stat-label">Target Median</div><div class="stat-value">$${fmt2(ptData.targetMedian||ptData.targetConsensus)}</div></div>
          <div class="stat-item"><div class="stat-label">Target Low</div><div class="stat-value" style="color:var(--red)">$${fmt2(ptData.targetLow)}</div></div>
          <div class="stat-item"><div class="stat-label">Consensus</div><div class="stat-value" style="color:var(--accent)">$${fmt2(ptData.targetConsensus)}</div></div>
        </div>
      </div>
    </div>`;

    const estHtml=estData.length?`<div class="card"><div class="card-header"><span class="card-title">Analyst Estimates</span></div>
      <div style="overflow-x:auto"><table><thead><tr><th>Period</th><th class="num-right">Est. Revenue</th><th class="num-right">Est. EPS</th><th class="num-right">EPS Avg</th></tr></thead>
      <tbody>${estData.slice(0,6).map(e=>`<tr><td>${e.date||''} ${e.period||''}</td><td class="num-right">${fmtB(e.estimatedRevenueAvg||0)}</td><td class="num-right">${fmt2(e.estimatedEpsAvg)}</td><td class="num-right">${fmt2(e.estimatedEpsHigh)}</td></tr>`).join('')}
      </tbody></table></div></div>`:'';

    if(content) content.innerHTML=ptHtml+estHtml;
  }catch(e){
    const l=document.getElementById('analyst-loader');
    if(l) l.style.display='none';
  }
}

async function loadStockNews(symbol){
  try{
    const r=await fetch(`/api/news?limit=12`);
    const data=await r.json();
    const loader=document.getElementById('snews-loader');
    if(loader) loader.style.display='none';
    const arr=Array.isArray(data)?data.slice(0,9):[];
    const grid=document.getElementById('stock-news-grid');
    if(grid) grid.innerHTML=arr.map(n=>`
      <a href="${n.url||'#'}" target="_blank" class="news-card">
        ${n.image?`<img class="news-img" src="${n.image}" alt="" onerror="this.style.display='none'">`:''}
        <div class="news-sym">${n.symbol||'MARKETS'}</div>
        <div class="news-title">${n.title||''}</div>
        <div class="news-meta"><span>${n.site||''}</span><span>${timeAgo(n.publishedDate||'')}</span></div>
      </a>`).join('');
  }catch(e){}
}

// ═══════════════════════════════════════════
//  GLOBAL SEARCH
// ═══════════════════════════════════════════
let searchTimer=null;
document.getElementById('global-search').addEventListener('input',function(){
  clearTimeout(searchTimer);
  const q=this.value.trim();
  const box=document.getElementById('search-results');
  if(q.length<2){box.style.display='none';return;}
  searchTimer=setTimeout(async()=>{
    try{
      const data=await apiFetch('/api/search?q='+encodeURIComponent(q));
      const arr=Array.isArray(data)?data.slice(0,8):[];
      if(!arr.length){box.style.display='none';return;}
      box.innerHTML=arr.map(s=>`<div class="sr-item" onclick="selectSearchResult('${s.symbol}')">
        <div><div class="sr-sym">${s.symbol}</div><div class="sr-name">${(s.name||'').slice(0,36)}</div></div>
        <div class="sr-ex">${s.exchangeShortName||s.exchange||''}</div>
      </div>`).join('');
      box.style.display='block';
    }catch(e){}
  },300);
});
document.addEventListener('click',e=>{
  if(!e.target.closest('.search-wrap')) document.getElementById('search-results').style.display='none';
});
function selectSearchResult(sym){
  document.getElementById('global-search').value='';
  document.getElementById('search-results').style.display='none';
  loadStockPage(sym);
}

// ═══════════════════════════════════════════
//  MARKET STATUS
// ═══════════════════════════════════════════
function checkMarketStatus(){
  const now=new Date();
  const utc=now.getTime()+now.getTimezoneOffset()*60000;
  const ny=new Date(utc+(3600000*-5)); // EST (approx)
  const day=ny.getDay();
  const h=ny.getHours();
  const m=ny.getMinutes();
  const mins=h*60+m;
  const isWeekday=day>=1&&day<=5;
  const isOpen=isWeekday&&mins>=570&&mins<960; // 9:30 - 16:00 EST
  const dot=document.getElementById('status-dot');
  const txt=document.getElementById('status-text');
  if(dot) dot.className='status-dot'+(isOpen?'':' closed');
  if(txt) txt.textContent=isOpen?'Market Open':'Market Closed';
}

// ═══════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════
async function init(){
  checkMarketStatus();
  await Promise.all([
    loadTicker(),
    loadIndices(),
    loadMovers(),
    loadSectors(),
    loadSnapshot(),
    loadHomeNews(),
  ]);
  loadIndexChart('3month');
  // Refresh ticker every 60s
  setInterval(()=>{loadTicker();loadIndices();},60000);
}

init();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


# Vercel WSGI entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
