"""
scoring/engine.py
-----------------
Computes composite vulnerability scores for each LGA across four dimensions.
Weights are evidence-based and can be adjusted via config.

Dimensions:
  1. Climate Exposure          (weight: 30%)
  2. Health System Fragility   (weight: 25%)
  3. Child & Maternal Vulnerability (weight: 25%)
  4. Socioeconomic Stress      (weight: 20%)

All sub-scores and the overall score are normalised to 0–100.
Risk levels: Critical (≥75), High (50–74), Medium (30–49), Low (<30)
"""

import pandas as pd
import numpy as np

# Dimension weights (must sum to 1.0)
WEIGHTS = {
    "climate":       0.30,
    "health":        0.25,
    "child":         0.25,
    "socioeconomic": 0.20,
}

# Sub-indicator weights within each dimension (must sum to 1.0 per dimension)
CLIMATE_WEIGHTS = {
    "flood_risk":        0.35,
    "drought_index":     0.25,
    "extreme_heat_freq": 0.25,
    "desertification":   0.15,
}

HEALTH_WEIGHTS = {
    "facility_density_inv": 0.40,
    "skilled_birth_inv":    0.35,
    "outbreak_history":     0.25,
}

CHILD_WEIGHTS = {
    "under5_density":   0.30,
    "malnutrition_rate": 0.40,
    "oosc_rate":        0.30,
}

SOCIOECONOMIC_WEIGHTS = {
    "poverty_headcount":  0.40,
    "women_exclusion":    0.35,
    "displacement_score": 0.25,
}


def _weighted_score(df: pd.DataFrame, weights: dict) -> pd.Series:
    """Compute weighted sum of specified columns."""
    score = pd.Series(0.0, index=df.index)
    for col, w in weights.items():
        if col in df.columns:
            score += df[col] * w
    return score.clip(0, 100)


def _risk_level(score: float) -> str:
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 30:
        return "Medium"
    else:
        return "Low"


def compute_vulnerability_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes raw indicator DataFrame and returns enriched DataFrame
    with dimension scores, overall score, and risk level.
    """
    out = df.copy()

    # Dimension scores
    out["climate_score"]       = _weighted_score(df, CLIMATE_WEIGHTS).round(1)
    out["health_score"]        = _weighted_score(df, HEALTH_WEIGHTS).round(1)
    out["child_score"]         = _weighted_score(df, CHILD_WEIGHTS).round(1)
    out["socioeconomic_score"] = _weighted_score(df, SOCIOECONOMIC_WEIGHTS).round(1)

    # Overall composite score
    out["overall_score"] = (
        out["climate_score"]       * WEIGHTS["climate"] +
        out["health_score"]        * WEIGHTS["health"] +
        out["child_score"]         * WEIGHTS["child"] +
        out["socioeconomic_score"] * WEIGHTS["socioeconomic"]
    ).round(1)

    # Risk level classification
    out["risk_level"] = out["overall_score"].apply(_risk_level)

    # Rank
    out["vulnerability_rank"] = out["overall_score"].rank(
        ascending=False, method="min"
    ).astype(int)

    return out.sort_values("overall_score", ascending=False).reset_index(drop=True)
