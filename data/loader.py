"""
data/loader.py
--------------
Loads LGA-level vulnerability indicators for Northwest Nigeria.
Currently uses synthetic seed data modelled on real Katsina State LGA profiles.
Replace with real downloaded datasets as they become available.

Data sources to integrate:
- IOM DTM Nigeria Displacement Data (HDX)
- GRID3 Nigeria Health Facilities
- NBS Population Estimates by LGA
- OCHA Flood Exposure Nigeria
- NCDC Outbreak Records (meningitis, cholera)
"""

import pandas as pd
import numpy as np

# All 34 LGAs of Katsina State + select LGAs from adjacent NW states
KATSINA_LGAS = [
    "Bakori", "Batagarawa", "Batsari", "Baure", "Bindawa",
    "Charanchi", "Dan Musa", "Dandume", "Danja", "Daura",
    "Dutsi", "Dutsin-Ma", "Faskari", "Funtua", "Ingawa",
    "Jibia", "Kafur", "Kaita", "Kankara", "Kankia",
    "Katsina", "Kurfi", "Kusada", "Mai'Adua", "Malumfashi",
    "Mani", "Mashi", "Matazu", "Musawa", "Rimi",
    "Sabuwa", "Safana", "Sandamu", "Zango"
]

NW_SAMPLE_LGAS = [
    ("Gusau", "Zamfara"), ("Anka", "Zamfara"),
    ("Sokoto North", "Sokoto"), ("Binji", "Sokoto"),
    ("Kano Municipal", "Kano"), ("Gezawa", "Kano"),
    ("Birni Kebbi", "Kebbi"), ("Argungu", "Kebbi"),
]

def _synthetic_indicators(lga: str, state: str, seed: int) -> dict:
    """
    Generate synthetic but geographically plausible indicators.
    Each LGA gets deterministic values based on its name hash + seed offset.
    Replace individual fields with real data as downloads complete.
    """
    rng = np.random.default_rng(abs(hash(lga + state)) % (2**31) + seed)

    # Climate exposure indicators (0–100, higher = more exposed)
    flood_risk          = rng.uniform(10, 95)
    drought_index       = rng.uniform(20, 90)
    extreme_heat_freq   = rng.uniform(30, 95)  # NW Nigeria is hot
    desertification     = rng.uniform(15, 85)

    # Health system indicators (0–100, higher = more fragile)
    facility_density_inv = rng.uniform(20, 90)   # inverted: low density = high score
    skilled_birth_inv    = rng.uniform(10, 85)
    outbreak_history     = rng.uniform(5,  80)

    # Child & maternal vulnerability (0–100)
    under5_density      = rng.uniform(30, 90)
    malnutrition_rate   = rng.uniform(20, 85)
    oosc_rate           = rng.uniform(15, 90)    # out-of-school children

    # Socioeconomic stress (0–100)
    poverty_headcount   = rng.uniform(40, 95)    # NW Nigeria high poverty
    women_exclusion     = rng.uniform(30, 90)
    displacement_score  = rng.uniform(5,  85)

    return {
        "lga": lga,
        "state": state,
        # Raw indicators (for transparency)
        "flood_risk": round(flood_risk, 1),
        "drought_index": round(drought_index, 1),
        "extreme_heat_freq": round(extreme_heat_freq, 1),
        "desertification": round(desertification, 1),
        "facility_density_inv": round(facility_density_inv, 1),
        "skilled_birth_inv": round(skilled_birth_inv, 1),
        "outbreak_history": round(outbreak_history, 1),
        "under5_density": round(under5_density, 1),
        "malnutrition_rate": round(malnutrition_rate, 1),
        "oosc_rate": round(oosc_rate, 1),
        "poverty_headcount": round(poverty_headcount, 1),
        "women_exclusion": round(women_exclusion, 1),
        "displacement_score": round(displacement_score, 1),
    }


def load_lga_data() -> pd.DataFrame:
    """
    Returns a DataFrame of LGA-level indicators.
    Priority: real CSVs in data/real/ → fallback to synthetic seed data.
    """
    import os

    real_path = os.path.join(os.path.dirname(__file__), "real", "lga_indicators.csv")
    if os.path.exists(real_path):
        df = pd.read_csv(real_path)
        print(f"[HazardIQ] Loaded real data: {len(df)} LGAs from {real_path}")
        return df

    # Build synthetic dataset
    records = []
    for lga in KATSINA_LGAS:
        records.append(_synthetic_indicators(lga, "Katsina", seed=42))
    for lga, state in NW_SAMPLE_LGAS:
        records.append(_synthetic_indicators(lga, state, seed=42))

    df = pd.DataFrame(records)
    print(f"[HazardIQ] Using synthetic seed data: {len(df)} LGAs")
    return df
