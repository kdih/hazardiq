import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="HazardIQ — Climate & Health Risk Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Branding ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a3a5c 0%, #0d6e6e 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: #ffffff; margin: 0; font-size: 2rem; }
    .main-header p  { color: #a8d8d8; margin: 0.3rem 0 0; font-size: 1rem; }
    .metric-card {
        background: #f0f7f7;
        border-left: 4px solid #0d6e6e;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }
    .risk-critical { color: #c0392b; font-weight: bold; }
    .risk-high     { color: #e67e22; font-weight: bold; }
    .risk-medium   { color: #f1c40f; font-weight: bold; }
    .risk-low      { color: #27ae60; font-weight: bold; }
    .footer {
        text-align: center;
        color: #888;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
  <h1>🌍 HazardIQ</h1>
  <p>Climate & Health Risk Intelligence for Northwest Nigeria · Powered by KDIH · <a href="https://kdih.org" style="color:#a8d8d8;">kdih.org</a></p>
</div>
""", unsafe_allow_html=True)

# ── Load Data ────────────────────────────────────────────────────────────────
from data.loader import load_lga_data
from scoring.engine import compute_vulnerability_scores

@st.cache_data
def get_data():
    df = load_lga_data()
    return compute_vulnerability_scores(df)

df = get_data()

# ── Sidebar Filters ──────────────────────────────────────────────────────────
st.sidebar.image("assets/kdih_logo.png", use_column_width=True) if __import__("os").path.exists("assets/kdih_logo.png") else None
st.sidebar.title("Filters")

states = ["All States"] + sorted(df["state"].unique().tolist())
sel_state = st.sidebar.selectbox("State", states)

if sel_state != "All States":
    lgas = ["All LGAs"] + sorted(df[df["state"] == sel_state]["lga"].unique().tolist())
else:
    lgas = ["All LGAs"] + sorted(df["lga"].unique().tolist())
sel_lga = st.sidebar.selectbox("LGA", lgas)

risk_levels = st.sidebar.multiselect(
    "Risk Level",
    ["Critical", "High", "Medium", "Low"],
    default=["Critical", "High", "Medium", "Low"]
)

dimension = st.sidebar.selectbox(
    "Score Dimension",
    ["Overall Vulnerability", "Climate Exposure", "Health System Fragility",
     "Child & Maternal Vulnerability", "Socioeconomic Stress"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Data Sources**")
st.sidebar.markdown("- IOM DTM Nigeria (2025)\n- GRID3 Nigeria Wards\n- NBS Population Estimates\n- OCHA Flood Exposure\n- NCDC Outbreak Records")
st.sidebar.markdown("---")
st.sidebar.markdown("© 2026 KDIH · MIT License · [GitHub](https://github.com/kdih/hazardiq)")

# ── Filter Data ──────────────────────────────────────────────────────────────
filtered = df.copy()
if sel_state != "All States":
    filtered = filtered[filtered["state"] == sel_state]
if sel_lga != "All LGAs":
    filtered = filtered[filtered["lga"] == sel_lga]
filtered = filtered[filtered["risk_level"].isin(risk_levels)]

dim_col_map = {
    "Overall Vulnerability":        "overall_score",
    "Climate Exposure":             "climate_score",
    "Health System Fragility":      "health_score",
    "Child & Maternal Vulnerability":"child_score",
    "Socioeconomic Stress":         "socioeconomic_score"
}
score_col = dim_col_map[dimension]

# ── KPI Row ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("LGAs Assessed",    len(filtered))
col2.metric("Critical Risk",    int((filtered["risk_level"] == "Critical").sum()))
col3.metric("High Risk",        int((filtered["risk_level"] == "High").sum()))
col4.metric("Avg Vulnerability",f"{filtered['overall_score'].mean():.1f}/100")

st.markdown("---")

# ── Main Layout ──────────────────────────────────────────────────────────────
left, right = st.columns([1.6, 1])

with left:
    st.subheader(f"📊 {dimension} by LGA")
    chart_df = filtered.sort_values(score_col, ascending=True).tail(20)

    color_map = {"Critical": "#c0392b", "High": "#e67e22",
                 "Medium": "#f39c12", "Low": "#27ae60"}
    colors = chart_df["risk_level"].map(color_map)

    fig = go.Figure(go.Bar(
        x=chart_df[score_col],
        y=chart_df["lga"],
        orientation="h",
        marker_color=colors,
        text=chart_df[score_col].round(1),
        textposition="outside"
    ))
    fig.update_layout(
        height=500,
        xaxis_title="Score (0–100)",
        yaxis_title="",
        plot_bgcolor="white",
        margin=dict(l=10, r=40, t=10, b=30),
        xaxis=dict(range=[0, 110])
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("🔴 Highest Risk LGAs")
    top10 = filtered.nlargest(10, "overall_score")[
        ["lga", "state", "overall_score", "risk_level"]
    ].reset_index(drop=True)
    top10.index += 1

    def color_risk(val):
        c = {"Critical": "#c0392b", "High": "#e67e22",
             "Medium": "#f39c12", "Low": "#27ae60"}.get(val, "black")
        return f"color: {c}; font-weight: bold"

    styled = top10.style.applymap(color_risk, subset=["risk_level"])
    st.dataframe(styled, use_container_width=True, height=360)

    st.subheader("📈 Score Breakdown")
    if len(filtered) > 0:
        avg = filtered[["climate_score","health_score","child_score","socioeconomic_score"]].mean()
        radar_fig = go.Figure(go.Scatterpolar(
            r=avg.values.tolist() + [avg.values[0]],
            theta=["Climate", "Health System", "Child & Maternal",
                   "Socioeconomic", "Climate"],
            fill="toself",
            line_color="#0d6e6e",
            fillcolor="rgba(13,110,110,0.2)"
        ))
        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=280,
            margin=dict(l=40, r=40, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(radar_fig, use_container_width=True)

# ── Full Data Table ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 Full LGA Vulnerability Data")

display_cols = ["lga", "state", "overall_score", "risk_level",
                "climate_score", "health_score", "child_score", "socioeconomic_score"]
st.dataframe(
    filtered[display_cols].sort_values("overall_score", ascending=False).reset_index(drop=True),
    use_container_width=True,
    height=300
)

col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    csv = filtered[display_cols].to_csv(index=False)
    st.download_button("⬇️ Download CSV", csv, "hazardiq_vulnerability_data.csv", "text/csv")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  HazardIQ v1.0 · Built by <a href="https://kdih.org">Katsina Digital Innovation Hub (KDIH)</a> ·
  Open Source (MIT) · <a href="https://github.com/kdih/hazardiq">GitHub</a> ·
  Supported by Tony Elumelu Foundation
</div>
""", unsafe_allow_html=True)
