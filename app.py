import streamlit as st
import pandas as pd
import numpy as np
import json
import os

st.set_page_config(
    page_title="Exportaciones Mundiales",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global de Streamlit ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace !important;
}
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    letter-spacing: -0.02em;
}
.stApp { background-color: #080810; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
section[data-testid="stSidebar"] {
    background-color: #0d0d1a !important;
    border-right: 1px solid #1e1e3a;
}
section[data-testid="stSidebar"] * { color: #b0aec8 !important; }
div[data-testid="metric-container"] {
    background: #0d0d1a;
    border: 1px solid #1e1e3a;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    transition: border-color .2s;
}
div[data-testid="metric-container"]:hover { border-color: #3a3a6a; }
div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; font-size: 1.8rem !important; }
div[data-testid="stMetricDelta"] { font-family: 'DM Mono', monospace !important; font-size: .78rem !important; }
.stSlider > div > div > div { background: #1e1e3a !important; }
.stMultiSelect [data-baseweb="tag"] {
    background-color: #1e1e3a !important;
    border: 1px solid #3a3a6a !important;
}
div[data-testid="stSelectbox"] > div { background: #0d0d1a !important; border-color: #1e1e3a !important; }
hr { border-color: #1e1e3a; }
.stExpander { border: 1px solid #1e1e3a !important; background: #0d0d1a !important; border-radius: 6px !important; }

/* Título hero */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(1.8rem, 4vw, 2.8rem);
    font-weight: 800;
    color: #f0eee8;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: .2rem;
}
.hero-sub {
    font-family: 'DM Mono', monospace;
    font-size: .78rem;
    color: #5a5a8a;
    letter-spacing: .08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: .68rem;
    color: #5a5a8a;
    letter-spacing: .12em;
    text-transform: uppercase;
    margin-bottom: .6rem;
    border-left: 2px solid #3a3a6a;
    padding-left: .6rem;
}
</style>
""", unsafe_allow_html=True)

# ── Datos ──────────────────────────────────────────────────────────────────────
REGIONES = ["China", "USA", "Europa", "Resto América", "India", "Australia/Oceanía", "Resto del Mundo"]

COLORES = {
    "China":             "#FF4455",
    "USA":               "#4488FF",
    "Europa":            "#2DDBA4",
    "Resto América":     "#FFAA22",
    "India":             "#FF77BB",
    "Australia/Oceanía": "#66BBFF",
    "Resto del Mundo":   "#666688",
}

DATA_RAW = {
    1965: [2,   14,  38,  8,   1,   2,   35],
    1970: [2,   14,  37,  8,   1,   2,   36],
    1975: [2,   13,  37,  8,   1,   2,   37],
    1980: [2,   13,  36,  8,   1,   2,   38],
    1985: [3,   15,  36,  7,   1,   2,   36],
    1990: [3,   14,  40,  6,   1,   2,   34],
    1995: [5,   15,  38,  6,   1,   2,   33],
    2000: [7,   17,  37,  6,   2,   2,   29],
    2005: [10,  16,  38,  6,   2,   2,   26],
    2010: [13,  13,  34,  7,   3,   2,   28],
    2015: [15,  13,  32,  8,   3,   2,   27],
    2020: [16,  13,  31,  8,   3,   2,   27],
    2024: [18,  13,  29,  9,   4,   2,   25],
}

def build_dataframe(raw):
    pivot = sorted(raw.keys())
    years = list(range(1965, 2025))
    rows = []
    for y in years:
        if y in raw:
            vals = raw[y]
        else:
            lo = max(p for p in pivot if p <= y)
            hi = min(p for p in pivot if p >= y)
            t  = (y - lo) / (hi - lo)
            vals = [raw[lo][i] + t * (raw[hi][i] - raw[lo][i]) for i in range(len(REGIONES))]
        total = sum(vals)
        vals  = [v / total * 100 for v in vals]
        for region, val in zip(REGIONES, vals):
            rows.append({"Año": y, "Región": region, "Participación (%)": round(val, 2)})
    return pd.DataFrame(rows)

df = build_dataframe(DATA_RAW)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙ Configuración")
    st.markdown("---")
    year_range = st.slider("Período", 1965, 2024, (1965, 2024))
    st.markdown("---")
    regiones_sel = st.multiselect("Regiones", REGIONES, default=REGIONES)
    st.markdown("---")
    tipo = st.selectbox("Tipo de gráfico", ["Área apilada", "Líneas", "Barras apiladas"])
    st.markdown("---")
    año_pie = st.slider("Año para distribución", 1965, 2024, 2024)
    st.markdown("---")
    st.markdown("<span style='font-size:.7rem;color:#3a3a6a'>Datos estimados · OMC · FMI · Banco Mundial</span>", unsafe_allow_html=True)

# ── Filtrar ────────────────────────────────────────────────────────────────────
if not regiones_sel:
    st.warning("Seleccioná al menos una región.")
    st.stop()

df_f = df[(df["Año"] >= year_range[0]) & (df["Año"] <= year_range[1]) & (df["Región"].isin(regiones_sel))]

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">Exportaciones Mundiales</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-sub">Distribución por región de destino · {year_range[0]}–{year_range[1]}</div>', unsafe_allow_html=True)

# ── Métricas ───────────────────────────────────────────────────────────────────
def get_val(region, year):
    v = df[(df["Región"] == region) & (df["Año"] == year)]["Participación (%)"].values
    return v[0] if len(v) else 0.0

metrics = [
    ("🇨🇳 China",    "China"),
    ("🇺🇸 USA",      "USA"),
    ("🇪🇺 Europa",   "Europa"),
    ("🇮🇳 India",    "India"),
]
cols = st.columns(4)
for col, (label, region) in zip(cols, metrics):
    v_end   = get_val(region, year_range[1])
    v_start = get_val(region, year_range[0])
    delta   = round(v_end - v_start, 1)
    col.metric(label, f"{v_end:.1f}%", f"{delta:+.1f}pp vs {year_range[0]}")

st.markdown("---")

# ── Preparar datos para el componente HTML ────────────────────────────────────
years_list = sorted(df_f["Año"].unique().tolist())
datasets_payload = []
for region in regiones_sel:
    sub = df_f[df_f["Región"] == region].sort_values("Año")
    datasets_payload.append({
        "label":  region,
        "color":  COLORES.get(region, "#aaaaaa"),
        "values": sub["Participación (%)"].tolist(),
    })

pie_data = []
for region in regiones_sel:
    val = get_val(region, año_pie)
    pie_data.append({"label": region, "color": COLORES.get(region, "#aaa"), "value": round(val, 2)})

cambios = []
for region in regiones_sel:
    v0 = get_val(region, year_range[0])
    v1 = get_val(region, year_range[1])
    cambios.append({"label": region, "color": COLORES.get(region, "#aaa"), "delta": round(v1 - v0, 2)})
cambios.sort(key=lambda x: x["delta"])

payload = {
    "years":    years_list,
    "datasets": datasets_payload,
    "chartType": tipo,
    "pie":      pie_data,
    "pieYear":  año_pie,
    "cambios":  cambios,
    "yearStart": year_range[0],
    "yearEnd":   year_range[1],
}

# ── Leer e inyectar HTML ───────────────────────────────────────────────────────
html_path = os.path.join(os.path.dirname(__file__), "components", "chart.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_raw = f.read()

data_injection = f"<script>window.__DASH_DATA__ = {json.dumps(payload)};</script>"
html_final = html_raw.replace("<!-- DATA_INJECT -->", data_injection)

import streamlit.components.v1 as components
components.html(html_final, height=1080, scrolling=False)
