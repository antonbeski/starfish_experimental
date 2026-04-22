"""
Satellite Intelligence Flask App
- Input a ticker → fetches company info via yfinance
- Finds relevant locations (HQ, known store clusters)
- Generates Sentinel-2 / EO Browser deep links for parking lot imagery
- Returns sector-based satellite monitoring targets
"""

from flask import Flask, render_template, request, jsonify
import yfinance as yf

app = Flask(__name__)

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
}

DEFAULT_LOCATIONS = [
    {"name": "Port of LA/Long Beach (CA)", "lat": 33.7361, "lon": -118.2922},
    {"name": "Newark Airport Cargo (NJ)", "lat": 40.6895, "lon": -74.1745},
    {"name": "Chicago O'Hare Cargo (IL)", "lat": 41.9742, "lon": -87.9073},
    {"name": "Dallas/Fort Worth Hub (TX)", "lat": 32.8998, "lon": -97.0403},
]


def make_sentinel_link(lat, lon, name=""):
    """Generate Sentinel Hub EO Browser deep link for a location."""
    # EO Browser URL with Sentinel-2 L2A preset, 10m, true color
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
    """Generate USGS Earth Explorer link for Landsat 8/9."""
    return (
        f"https://earthexplorer.usgs.gov/"
        f"?center={lat},{lon}&zoom=15"
    )


def make_google_maps_link(lat, lon):
    """Satellite view via Google Maps."""
    return f"https://www.google.com/maps/@{lat},{lon},17z/data=!3m1!1e3"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    ticker_symbol = data.get("ticker", "").strip().upper()

    if not ticker_symbol:
        return jsonify({"error": "Ticker is required"}), 400

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
    except Exception as e:
        return jsonify({"error": f"Could not fetch ticker data: {str(e)}"}), 500

    # Basic company info
    company_name = info.get("longName") or info.get("shortName") or ticker_symbol
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")
    hq_city = info.get("city", "")
    hq_state = info.get("state", "")
    hq_country = info.get("country", "")
    hq_address = info.get("address1", "")
    employees = info.get("fullTimeEmployees", 0)
    market_cap = info.get("marketCap", 0)
    website = info.get("website", "")
    description = info.get("longBusinessSummary", "")[:300] + "..." if info.get("longBusinessSummary") else ""

    # HQ coordinates (yfinance doesn't provide lat/lon — we use city/state for display)
    hq_location = ", ".join(filter(None, [hq_city, hq_state, hq_country]))

    # Pick sector-relevant satellite targets
    sector_targets = SECTOR_LOCATIONS.get(sector, DEFAULT_LOCATIONS)

    # Build enriched location cards
    locations = []
    for loc in sector_targets:
        locations.append({
            "name": loc["name"],
            "lat": loc["lat"],
            "lon": loc["lon"],
            "sentinel_link": make_sentinel_link(loc["lat"], loc["lon"], loc["name"]),
            "usgs_link": make_usgs_link(loc["lat"], loc["lon"]),
            "google_maps_link": make_google_maps_link(loc["lat"], loc["lon"]),
            "embed_map": f"https://www.google.com/maps/embed/v1/place?key=AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY&q={loc['lat']},{loc['lon']}&zoom=17&maptype=satellite"
        })

    # Satellite signal type based on sector
    SECTOR_SIGNALS = {
        "Consumer Defensive": ["🅿️ Parking lot occupancy", "🚗 Vehicle count trends", "📦 Loading dock activity"],
        "Consumer Cyclical": ["🅿️ Parking lot footfall", "🏗️ Construction progress", "🚗 Dealership lot inventory"],
        "Industrials": ["📦 Container yard density", "🚢 Ship traffic at ports", "🏭 Factory roof heat signature"],
        "Energy": ["🛢️ Oil storage tank shadow (volume)", "🚢 Tanker traffic", "🔥 Flare activity"],
        "Basic Materials": ["⛏️ Mine excavation progress", "🏭 Plant smoke & steam", "📦 Stockpile size"],
        "Technology": ["🏭 Gigafactory expansion", "🅿️ Campus employee count", "🏗️ Data center construction"],
        "Real Estate": ["🅿️ Mall parking occupancy", "🏗️ Development progress", "🚗 Residential traffic"],
    }
    signals = SECTOR_SIGNALS.get(sector, ["🛰️ General area activity", "🅿️ Parking patterns", "🚗 Traffic flow"])

    return jsonify({
        "ticker": ticker_symbol,
        "company": company_name,
        "sector": sector,
        "industry": industry,
        "hq_location": hq_location,
        "hq_address": hq_address,
        "employees": f"{employees:,}" if employees else "N/A",
        "market_cap": f"${market_cap / 1e9:.1f}B" if market_cap else "N/A",
        "website": website,
        "description": description,
        "signals": signals,
        "locations": locations,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
