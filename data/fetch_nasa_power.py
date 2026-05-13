"""
data/fetch_nasa_power.py
------------------------
Fetches real climate data from NASA POWER API for all 34 Katsina LGAs.
Replaces the geographic proxy model with real observed climate variables.

NASA POWER API: https://power.larc.nasa.gov/api/
- Free, no API key required
- Returns daily/monthly/annual climate data at any lat/lon
- Coverage: global, 1981–present

Variables fetched per LGA centroid:
  T2M_MAX  — Maximum temperature at 2m (°C)     → extreme_heat_freq
  T2M_MIN  — Minimum temperature at 2m (°C)     → temperature range
  PRECTOTCORR — Precipitation corrected (mm/day) → flood_risk
  RH2M     — Relative humidity at 2m (%)        → drought support
  WS2M     — Wind speed at 2m (m/s)             → dust/desertification

Usage:
  python data/fetch_nasa_power.py
  
Output:
  data/processed/nasa_power_katsina_climate.csv
"""

import requests
import pandas as pd
import numpy as np
import time
import os

# ── Katsina LGA Centroids (lat, lon) ────────────────────────────────────────
# Source: GRID3 NGA Operational Wards v2.0 — LGA centroid approximations
KATSINA_LGAS = {
    "Bakori":       (11.58, 7.43),
    "Batagarawa":   (12.98, 7.55),
    "Batsari":      (12.55, 7.30),
    "Baure":        (12.75, 8.58),
    "Bindawa":      (12.97, 7.98),
    "Charanchi":    (12.42, 7.55),
    "Dan Musa":     (13.15, 7.68),
    "Dandume":      (11.78, 7.57),
    "Danja":        (11.92, 7.75),
    "Daura":        (13.03, 8.32),
    "Dutsi":        (13.28, 8.05),
    "Dutsin-Ma":    (12.45, 7.50),
    "Faskari":      (11.78, 7.30),
    "Funtua":       (11.53, 7.32),
    "Ingawa":       (12.80, 7.37),
    "Jibia":        (13.33, 7.22),
    "Kafur":        (12.25, 7.62),
    "Kaita":        (13.08, 7.45),
    "Kankara":      (12.52, 7.47),
    "Kankia":       (12.93, 7.60),
    "Katsina":      (12.99, 7.60),
    "Kurfi":        (12.70, 7.47),
    "Kusada":       (12.35, 7.80),
    "Mai'Adua":     (13.18, 8.52),
    "Malumfashi":   (11.80, 7.62),
    "Mani":         (12.48, 8.13),
    "Mashi":        (13.00, 8.00),
    "Matazu":       (12.08, 7.28),
    "Musawa":       (11.98, 7.88),
    "Rimi":         (12.18, 7.93),
    "Sabuwa":       (11.62, 7.57),
    "Safana":       (12.05, 7.17),
    "Sandamu":      (12.65, 7.73),
    "Zango":        (12.85, 8.73),
}

# ── NASA POWER API Config ────────────────────────────────────────────────────
BASE_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
PARAMS_BASE = {
    "parameters": "T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M",
    "community": "RE",
    "format": "JSON",
    "start": "2001",
    "end": "2022",
    "header": "true"
}


def fetch_lga_climate(lga_name: str, lat: float, lon: float, retries: int = 3) -> dict:
    """Fetch 20-year climatology for a single LGA centroid."""
    params = {**PARAMS_BASE, "latitude": lat, "longitude": lon}
    
    for attempt in range(retries):
        try:
            r = requests.get(BASE_URL, params=params, timeout=30)
            if r.status_code == 200:
                data = r.json()
                props = data.get("properties", {}).get("parameter", {})
                
                # Annual means across all months
                def annual_mean(var):
                    monthly = props.get(var, {})
                    vals = [v for k, v in monthly.items() if k != "ANN" and v != -999]
                    return round(np.mean(vals), 2) if vals else None
                
                def annual_max(var):
                    monthly = props.get(var, {})
                    vals = [v for k, v in monthly.items() if k != "ANN" and v != -999]
                    return round(max(vals), 2) if vals else None

                return {
                    "lga": lga_name,
                    "lat": lat,
                    "lon": lon,
                    "t2m_max_mean": annual_mean("T2M_MAX"),    # mean of monthly max temps
                    "t2m_max_peak": annual_max("T2M_MAX"),     # hottest month average
                    "t2m_min_mean": annual_mean("T2M_MIN"),
                    "precip_mean":  annual_mean("PRECTOTCORR"),# mm/day annual mean
                    "rh2m_mean":    annual_mean("RH2M"),       # humidity %
                    "ws2m_mean":    annual_mean("WS2M"),       # wind speed
                    "status": "ok"
                }
            else:
                print(f"  HTTP {r.status_code} for {lga_name} (attempt {attempt+1})")
                time.sleep(2)
        except Exception as e:
            print(f"  Error for {lga_name} (attempt {attempt+1}): {e}")
            time.sleep(3)
    
    return {"lga": lga_name, "lat": lat, "lon": lon, "status": "failed"}


def score_climate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw NASA POWER climate variables to HazardIQ 0–100 scores.
    
    Scoring logic:
      extreme_heat_freq: based on t2m_max_peak — Katsina range ~35–45°C
                         Higher peak temp = higher score
      flood_risk:        based on precip_mean — inverted for Sahel
                         Very low precip = drought risk; high = flood risk
                         Uses seasonal variance as flood proxy
      drought_index:     based on rh2m_mean — low humidity = high drought
                         and precip below threshold
      desertification:   based on ws2m_mean + low precip + low RH
                         High wind + dry = high desertification risk
    """
    out = df.copy()
    
    # ── Extreme Heat (0–100) ─────────────────────────────────────────────────
    # Katsina peak temps: ~37°C (south) to ~44°C (north, pre-monsoon)
    # Normalize: 35°C = 0, 45°C = 100
    out["extreme_heat_freq"] = (
        ((out["t2m_max_peak"] - 35) / (45 - 35)) * 100
    ).clip(0, 100).round(1)
    
    # ── Flood Risk (0–100) ───────────────────────────────────────────────────
    # Sahel flood risk: paradoxically from intense seasonal rain on dry soil
    # Precip mean: 0.5mm/day (very dry) to 3.0mm/day (flood-prone)
    # Higher precip + Sahel = higher flood risk (surface runoff)
    out["flood_risk"] = (
        ((out["precip_mean"] - 0.3) / (3.0 - 0.3)) * 100
    ).clip(0, 100).round(1)
    
    # ── Drought Index (0–100) ────────────────────────────────────────────────
    # Low humidity + low precip = high drought
    # RH2M: 20% (very dry) to 70% (humid) → invert
    rh_score = (((70 - out["rh2m_mean"]) / (70 - 20)) * 100).clip(0, 100)
    precip_drought = (((1.5 - out["precip_mean"]) / 1.5) * 100).clip(0, 100)
    out["drought_index"] = (rh_score * 0.5 + precip_drought * 0.5).round(1)
    
    # ── Desertification (0–100) ──────────────────────────────────────────────
    # High wind + low RH + low precip = high desertification
    # WS2M: 2 m/s (calm) to 6 m/s (windy)
    wind_score = (((out["ws2m_mean"] - 2) / (6 - 2)) * 100).clip(0, 100)
    out["desertification"] = (
        wind_score * 0.4 + rh_score * 0.35 + precip_drought * 0.25
    ).round(1)
    
    return out


def main():
    print("=" * 60)
    print("HazardIQ — NASA POWER Climate Data Fetcher")
    print("Fetching 20-year climatology for 34 Katsina LGAs")
    print("=" * 60)
    
    results = []
    total = len(KATSINA_LGAS)
    
    for i, (lga, (lat, lon)) in enumerate(KATSINA_LGAS.items(), 1):
        print(f"[{i:02d}/{total}] Fetching: {lga} ({lat}, {lon})")
        result = fetch_lga_climate(lga, lat, lon)
        results.append(result)
        if result["status"] == "ok":
            print(f"       ✅ T2M_MAX={result['t2m_max_peak']}°C  "
                  f"Precip={result['precip_mean']}mm/day  "
                  f"RH={result['rh2m_mean']}%")
        else:
            print(f"       ❌ Failed — will use interpolation")
        time.sleep(0.8)  # Respectful API rate limiting
    
    df = pd.DataFrame(results)
    failed = df[df["status"] == "failed"]
    
    if len(failed) > 0:
        print(f"\n⚠️  {len(failed)} LGAs failed — interpolating from neighbours")
        for idx, row in failed.iterrows():
            # Interpolate from nearest successful LGAs
            ok = df[df["status"] == "ok"].copy()
            ok["dist"] = np.sqrt(
                (ok["lat"] - row["lat"])**2 + (ok["lon"] - row["lon"])**2
            )
            nearest = ok.nsmallest(3, "dist")
            for col in ["t2m_max_mean","t2m_max_peak","t2m_min_mean",
                        "precip_mean","rh2m_mean","ws2m_mean"]:
                df.at[idx, col] = nearest[col].mean()
            df.at[idx, "status"] = "interpolated"
    
    # Score the climate variables
    df = score_climate(df)
    
    # Save
    os.makedirs("data/processed", exist_ok=True)
    out_path = "data/processed/nasa_power_katsina_climate.csv"
    df.to_csv(out_path, index=False)
    
    print(f"\n✅ Climate data saved: {out_path}")
    print(f"   LGAs: ok={len(df[df['status']=='ok'])}  "
          f"interpolated={len(df[df['status']=='interpolated'])}  "
          f"failed={len(df[df['status']=='failed'])}")
    print(f"\nClimate Score Summary:")
    print(df[["lga","extreme_heat_freq","flood_risk",
              "drought_index","desertification"]].to_string(index=False))


if __name__ == "__main__":
    main()
