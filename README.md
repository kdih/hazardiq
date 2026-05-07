# 🌍 HazardIQ

**Climate & Health Risk Intelligence for Northwest Nigeria**

> *Know the risk. Protect the child.*

Built by [Katsina Digital Innovation Hub (KDIH)](https://kdih.org) · Supported by Tony Elumelu Foundation  
License: MIT · Open Source

---

## What is HazardIQ?

HazardIQ is an open-source, AI-assisted Climate & Health Vulnerability Scoring System that aggregates climate, demographic, health facility, and social data to generate actionable risk scores at LGA and ward level across Katsina State and Northwest Nigeria.

Children and women in Northwest Nigeria face compounding climate and health risks — extreme heat, seasonal flooding, drought, desertification, and climate-driven disease outbreaks — yet no accessible, ward-level decision-support tool exists. HazardIQ bridges that gap.

---

## Features

- **LGA-level vulnerability scoring** across four dimensions
- **Interactive dashboard** built with Streamlit + Plotly
- **Downloadable reports** (CSV) for government and programme use
- **Open-source** and adaptable for any UNICEF programme country
- **Low-bandwidth friendly** — runs on standard government devices

---

## Vulnerability Dimensions

| Dimension | Weight | Indicators |
|---|---|---|
| Climate Exposure | 30% | Flood risk, drought index, extreme heat, desertification |
| Health System Fragility | 25% | Facility density, skilled birth attendance, outbreak history |
| Child & Maternal Vulnerability | 25% | Under-5 density, malnutrition, out-of-school children |
| Socioeconomic Stress | 20% | Poverty headcount, women's exclusion, displacement |

---

## Risk Classification

| Level | Score | Meaning |
|---|---|---|
| 🔴 Critical | ≥ 75 | Immediate prioritisation required |
| 🟠 High | 50–74 | Urgent intervention needed |
| 🟡 Medium | 30–49 | Monitor and plan |
| 🟢 Low | < 30 | Maintain current coverage |

---

## Data Sources

- [IOM DTM Nigeria Displacement Data](https://data.humdata.org) (HDX)
- [GRID3 Nigeria — Operational Wards & Health Facilities](https://grid3.org/country/nigeria)
- [NBS Nigeria — Subnational Population Estimates](https://nigerianstat.gov.ng)
- [OCHA Nigeria — Flood Exposure Data](https://data.humdata.org)
- [NCDC Nigeria — Weekly Epidemiological Reports](https://ncdc.gov.ng)

All datasets are publicly available and open-licensed.

---

## Quick Start

```bash
git clone https://github.com/kdih/hazardiq.git
cd hazardiq
pip install -r requirements.txt
streamlit run app.py
```

---

## Project Structure

```
hazardiq/
├── app.py                  # Main Streamlit application
├── requirements.txt
├── scoring/
│   └── engine.py           # Vulnerability scoring logic
├── data/
│   ├── loader.py           # Data loading (real + synthetic fallback)
│   └── real/               # Drop real downloaded datasets here
│       └── lga_indicators.csv
└── assets/
    └── kdih_logo.png
```

---

## Adding Real Data

1. Download datasets from HDX (see Data Sources above)
2. Process with the included Python scripts in `data/`
3. Save as `data/real/lga_indicators.csv` with the required column schema
4. The app automatically detects and loads real data over synthetic seed data

---

## Geographic Coverage

**Phase 1:** Katsina State — 34 LGAs, 361 wards  
**Phase 2:** Full Northwest Nigeria — Zamfara, Sokoto, Kebbi, Kano, Kaduna, Jigawa  
**Phase 3:** National scale with UNICEF country office integration

---

## Licence

MIT License. Free to use, adapt, and deploy. Attribution appreciated.

---

## Contact

**Mubarak Jibril** — Founder & Executive Director, KDIH  
[kdih.org](https://kdih.org) · [LinkedIn](https://linkedin.com/in/mubarak-jibril-67864185)
