import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="HazardIQ — Climate & Health Risk Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Severity palette (hazard-map standard) ───────────────────────────────────
SEV = {"Critical": "#b02418", "High": "#d98a1f", "Medium": "#e8c84a", "Low": "#4a8b5a"}
NAVY = "#1b3a5b"

# ── Styles ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    .block-container {{ padding-top: 1.5rem; }}
    .hiq-header {{
        background: {NAVY};
        padding: 1.1rem 1.4rem;
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 1.1rem;
    }}
    .hiq-header .brand {{ display: flex; align-items: center; gap: 9px; }}
    .hiq-header .brand h1 {{ font-size: 1.15rem; font-weight: 600; color: #fff; margin: 0; }}
    .hiq-header .brand span {{ font-size: 0.85rem; color: #9fb3c8; }}
    .hiq-header .live {{ font-size: 0.7rem; color: #cfe8d4; border: 1px solid #4a7a5a;
        padding: 2px 8px; border-radius: 3px; }}
    .hiq-alert {{
        background: #fbeaea; border: 1px solid #e3b0b0; border-left: 4px solid #b02418;
        padding: 0.85rem 1.1rem; margin-bottom: 1.1rem;
    }}
    .hiq-alert .lbl {{ font-size: 0.7rem; font-weight: 600; color: #b02418;
        text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px; }}
    .hiq-alert .txt {{ font-size: 0.9rem; color: #5e1410; line-height: 1.5; }}
    .hiq-footer {{ text-align: center; color: #8a8a8a; font-size: 0.78rem;
        margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid #e6e6e6; }}
    /* flatten Streamlit metric cards into bordered grid cells */
    div[data-testid="stMetric"] {{
        border: 1px solid #e0e0e0; padding: 0.85rem 1rem; background: #fff;
    }}
    div[data-testid="stMetricValue"] {{ font-size: 1.5rem; font-weight: 600; }}
    div[data-testid="stMetricLabel"] {{ font-size: 0.72rem; color: #5f5f5f; }}
</style>
""", unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────────────────
from data.loader import load_lga_data
from scoring.engine import compute_vulnerability_scores

@st.cache_data
def get_data():
    return compute_vulnerability_scores(load_lga_data())

df = get_data()

# ── Sidebar ──────────────────────────────────────────────────────────────────
if os.path.exists("assets/kdih_logo.png"):
    st.sidebar.image("assets/kdih_logo.png", use_container_width=True)
st.sidebar.title("Filters")

states = ["All States"] + sorted(df["state"].unique().tolist())
sel_state = st.sidebar.selectbox("State", states)

if sel_state != "All States":
    lgas = ["All LGAs"] + sorted(df[df["state"] == sel_state]["lga"].unique().tolist())
else:
    lgas = ["All LGAs"] + sorted(df["lga"].unique().tolist())
sel_lga = st.sidebar.selectbox("LGA", lgas)

risk_levels = st.sidebar.multiselect(
    "Risk Level", ["Critical", "High", "Medium", "Low"],
    default=["Critical", "High", "Medium", "Low"]
)
dimension = st.sidebar.selectbox(
    "Score Dimension",
    ["Overall Vulnerability", "Climate Exposure", "Health System Fragility",
     "Child & Maternal Vulnerability", "Socioeconomic Stress"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("**Data Sources**")
st.sidebar.markdown(
    "- IOM DTM Nigeria (2025)\n- GRID3 Nigeria Wards\n- NASA POWER Climate\n"
    "- NBS Population Estimates\n- NCDC Outbreak Records"
)
st.sidebar.markdown("---")
st.sidebar.markdown("© 2026 KDIH · MIT License · [GitHub](https://github.com/kdih/hazardiq)")

# ── Filter ───────────────────────────────────────────────────────────────────
filtered = df.copy()
if sel_state != "All States":
    filtered = filtered[filtered["state"] == sel_state]
if sel_lga != "All LGAs":
    filtered = filtered[filtered["lga"] == sel_lga]
filtered = filtered[filtered["risk_level"].isin(risk_levels)]

dim_col_map = {
    "Overall Vulnerability": "overall_score",
    "Climate Exposure": "climate_score",
    "Health System Fragility": "health_score",
    "Child & Maternal Vulnerability": "child_score",
    "Socioeconomic Stress": "socioeconomic_score",
}
score_col = dim_col_map[dimension]

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hiq-header">
  <div class="brand">
    <h1>HazardIQ</h1><span>· Northwest Nigeria</span>
  </div>
  <span class="live">Live data</span>
</div>
""", unsafe_allow_html=True)

# ── Critical alert (only when a critical LGA is in view) ─────────────────────
crit = filtered[filtered["risk_level"] == "Critical"].sort_values("overall_score", ascending=False)
if len(crit) > 0:
    top = crit.iloc[0]
    extra = ""
    if "displaced" in top.index and pd.notna(top.get("displaced")):
        try:
            extra = f" {int(top['displaced']):,} displaced."
        except Exception:
            extra = ""
    st.markdown(f"""
    <div class="hiq-alert">
      <div class="lbl">Critical alert</div>
      <div class="txt"><b>{top['lga']} LGA</b> — vulnerability score {top['overall_score']:.1f}/100,
      the highest in view and classified critical.{extra}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Metric row ───────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("LGAs assessed", len(filtered))
c2.metric("Critical", int((filtered["risk_level"] == "Critical").sum()))
c3.metric("High risk", int((filtered["risk_level"] == "High").sum()))
c4.metric("Mean score", f"{filtered['overall_score'].mean():.1f}" if len(filtered) else "N/A")

st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

# ── Ranking + table ──────────────────────────────────────────────────────────
left, right = st.columns([1.7, 1])

with left:
    st.markdown(f"**{dimension} by LGA** — top {min(20, len(filtered))} of {len(df)}")
    if len(filtered) > 0:
        chart_df = filtered.sort_values(score_col, ascending=True).tail(20)
        colors = chart_df["risk_level"].map(SEV).fillna("#888888")
        fig = go.Figure(go.Bar(
            x=chart_df[score_col], y=chart_df["lga"], orientation="h",
            marker_color=colors, marker_line_width=0,
            text=chart_df[score_col].round(1), textposition="outside",
            textfont=dict(size=11, color="#333"),
        ))
        fig.update_layout(
            height=520, xaxis_title="Score (0–100)", yaxis_title="",
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=10, r=40, t=6, b=30),
            xaxis=dict(range=[0, 110], showgrid=True, gridcolor="#eee",
                       zeroline=False, tickfont=dict(size=11)),
            yaxis=dict(tickfont=dict(size=11)),
            font=dict(family="sans-serif"),
            bargap=0.28,
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        # severity legend
        chips = "".join(
            f"<span style='font-size:0.72rem;color:#555;display:inline-flex;"
            f"align-items:center;gap:5px;margin-right:16px;'>"
            f"<span style='width:11px;height:11px;background:{c};display:inline-block;'></span>"
            f"{lvl}</span>"
            for lvl, c in SEV.items()
        )
        st.markdown(f"<div style='margin-top:4px'>Severity: {chips}</div>",
                    unsafe_allow_html=True)
    else:
        st.info("No data matches the current filters.")

with right:
    st.markdown("**Highest-risk LGAs**")
    if len(filtered) > 0:
        top10 = (filtered.nlargest(10, "overall_score")
                 [["lga", "state", "overall_score", "risk_level"]]
                 .reset_index(drop=True))
        top10.index += 1

        def color_risk(val):
            return f"color: {SEV.get(val, '#333')}; font-weight: 600"

        styled = top10.style.map(color_risk, subset=["risk_level"]) \
                            .format({"overall_score": "{:.1f}"})
        st.dataframe(styled, width="stretch", height=388)

# ── Full table + download ────────────────────────────────────────────────────
st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
st.markdown("**Full LGA vulnerability data**")
display_cols = ["lga", "state", "overall_score", "risk_level",
                "climate_score", "health_score", "child_score", "socioeconomic_score"]
display_cols = [c for c in display_cols if c in filtered.columns]
if len(filtered) > 0:
    st.dataframe(
        filtered[display_cols].sort_values("overall_score", ascending=False)
                .reset_index(drop=True),
        width="stretch", height=300
    )
    csv = filtered[display_cols].to_csv(index=False)
    st.download_button("Download CSV", csv,
                       "hazardiq_vulnerability_data.csv", "text/csv")
else:
    st.info("No data available for the selected filters.")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hiq-footer">
  HazardIQ v1.0 · Built by <a href="https://kdih.org">Katsina Digital Innovation Hub (KDIH)</a> ·
  Open Source (MIT) · <a href="https://github.com/kdih/hazardiq">GitHub</a> ·
  Supported by Tony Elumelu Foundation
</div>
""", unsafe_allow_html=True)
