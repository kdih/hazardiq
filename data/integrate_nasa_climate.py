"""
data/integrate_nasa_climate.py
-------------------------------
Merges real NASA POWER climate data into lga_indicators.csv,
replacing the geographic proxy model with actual observed values.

Run once after fetch_nasa_power.py completes:
  python data/integrate_nasa_climate.py

Output: data/real/lga_indicators.csv (updated in place)
"""

import pandas as pd
import numpy as np
import os

def main():
    print("=" * 60)
    print("HazardIQ — NASA POWER Climate Integration")
    print("=" * 60)

    # ── Load datasets ────────────────────────────────────────────
    nasa_path  = "data/processed/nasa_power_katsina_climate.csv"
    indic_path = "data/real/lga_indicators.csv"

    if not os.path.exists(nasa_path):
        print(f"❌ NASA data not found: {nasa_path}")
        print("   Run: python data/fetch_nasa_power.py first")
        return

    if not os.path.exists(indic_path):
        print(f"❌ Indicators not found: {indic_path}")
        return

    nasa = pd.read_csv(nasa_path)
    indic = pd.read_csv(indic_path)

    print(f"NASA POWER data: {len(nasa)} LGAs")
    print(f"Current indicators: {len(indic)} LGAs")

    # ── Normalise LGA names for merging ─────────────────────────
    nasa["lga_key"]   = nasa["lga"].str.strip().str.title()
    indic["lga_key"]  = indic["lga"].str.strip().str.title()

    # ── Show before state ────────────────────────────────────────
    print("\nBEFORE (proxy climate scores — sample):")
    print(indic[["lga","flood_risk","drought_index",
                 "extreme_heat_freq","desertification"]].head(5).to_string(index=False))

    # ── Merge NASA climate scores ────────────────────────────────
    climate_cols = ["lga_key","extreme_heat_freq","flood_risk",
                    "drought_index","desertification",
                    "t2m_max_peak","precip_mean","rh2m_mean","ws2m_mean","status"]

    nasa_slim = nasa[climate_cols].copy()

    merged = indic.drop(
        columns=["flood_risk","drought_index","extreme_heat_freq","desertification"],
        errors="ignore"
    ).merge(nasa_slim, on="lga_key", how="left")

    # ── Check coverage ───────────────────────────────────────────
    missing = merged[merged["extreme_heat_freq"].isna()]["lga"].tolist()
    if missing:
        print(f"\n⚠️  {len(missing)} LGAs unmatched: {missing}")
        print("   Filling with state mean...")
        for col in ["extreme_heat_freq","flood_risk","drought_index","desertification"]:
            state_mean = merged[col].mean()
            merged[col] = merged[col].fillna(round(state_mean, 1))

    # ── Clean up ─────────────────────────────────────────────────
    merged = merged.drop(columns=["lga_key"], errors="ignore")

    # ── Show after state ─────────────────────────────────────────
    print("\nAFTER (real NASA POWER climate scores — sample):")
    print(merged[["lga","flood_risk","drought_index",
                  "extreme_heat_freq","desertification",
                  "t2m_max_peak","precip_mean"]].head(5).to_string(index=False))

    # ── Save ─────────────────────────────────────────────────────
    merged.to_csv(indic_path, index=False)
    print(f"\n✅ lga_indicators.csv updated with real NASA POWER climate data")
    print(f"   Records: {len(merged)}")

    real_count = len(merged[merged["status"] == "ok"])
    interp_count = len(merged[merged["status"] == "interpolated"])
    print(f"   Real API data: {real_count} LGAs")
    print(f"   Interpolated:  {interp_count} LGAs")

    # ── Summary stats ────────────────────────────────────────────
    print("\nClimate Score Summary (final):")
    print(merged[["lga","extreme_heat_freq","flood_risk",
                  "drought_index","desertification",
                  "t2m_max_peak"]].sort_values(
        "extreme_heat_freq", ascending=False
    ).to_string(index=False))

    print("\n🌍 HazardIQ climate layer is now powered by real NASA POWER data.")
    print("   Restart Streamlit to see updated scores: streamlit run app.py")


if __name__ == "__main__":
    main()
