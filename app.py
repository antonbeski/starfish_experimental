import pandas as pd
import folium
from folium.plugins import HeatMap
import requests, gzip, io, os
from datetime import datetime

# ── 1. Auto-download DB-IP free city CSV (updates monthly) ──────────────────
year  = datetime.now().strftime("%Y")
month = datetime.now().strftime("%m")
url   = f"https://download.db-ip.com/free/dbip-city-lite-{year}-{month}.csv.gz"

CSV_PATH = "hosts.csv"

if not os.path.exists(CSV_PATH):
    print(f"Downloading DB-IP free dataset from:\n  {url}")
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with gzip.open(io.BytesIO(r.content)) as f:
        raw = pd.read_csv(
            f,
            header=None,
            names=["ip_start", "ip_end", "continent", "country",
                   "state", "city", "latitude", "longitude"],
            low_memory=False
        )
    # Keep only rows with valid coordinates
    raw = raw.dropna(subset=["latitude", "longitude"])
    raw["latitude"]  = pd.to_numeric(raw["latitude"],  errors="coerce")
    raw["longitude"] = pd.to_numeric(raw["longitude"], errors="coerce")
    raw = raw.dropna(subset=["latitude", "longitude"])

    # Round coords to ~50km grid and count IP blocks per cell → device density
    raw["lat_r"] = raw["latitude"].round(1)
    raw["lon_r"] = raw["longitude"].round(1)
    df = (raw.groupby(["lat_r", "lon_r"])
             .size()
             .reset_index(name="count"))
    df.rename(columns={"lat_r": "latitude", "lon_r": "longitude"}, inplace=True)
    df.to_csv(CSV_PATH, index=False)
    print(f"Saved {len(df):,} grid cells to {CSV_PATH}")
else:
    print(f"Loading existing {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

# ── 2. Build heatmap data ────────────────────────────────────────────────────
df = df.dropna(subset=["latitude", "longitude"])

if "count" in df.columns:
    heat_data = df[["latitude", "longitude", "count"]].values.tolist()
else:
    heat_data = df[["latitude", "longitude"]].values.tolist()

# ── 3. Build Folium heatmap ──────────────────────────────────────────────────
m = folium.Map(
    location=[20, 0],
    zoom_start=2,
    tiles="CartoDB dark_matter",   # dark terminal-style basemap
    prefer_canvas=True
)

HeatMap(
    heat_data,
    name="Device Density",
    radius=6,
    blur=10,
    max_zoom=6,
    min_opacity=0.3,
    gradient={
        "0.2": "#003300",
        "0.4": "#00aa00",
        "0.6": "#ffff00",
        "0.8": "#ff6600",
        "1.0": "#ff0000"
    }
).add_to(m)

# Title overlay
title_html = """
<div style="
    position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
    z-index: 9999; background: rgba(0,0,0,0.75);
    color: #00ff88; font-family: monospace; font-size: 16px;
    padding: 8px 20px; border: 1px solid #00ff88; border-radius: 4px;
    pointer-events: none;">
    🌐 Global Internet Device Density — DB-IP {year}-{month}
</div>
""".replace("{year}", year).replace("{month}", month)
m.get_root().html.add_child(folium.Element(title_html))

folium.LayerControl().add_to(m)

# ── 4. Save ──────────────────────────────────────────────────────────────────
OUT = "device_density_heatmap.html"
m.save(OUT)
print(f"✓ Saved → {OUT}  ({len(heat_data):,} heat points)")
