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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace !important; }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; letter-spacing: -0.02em; }
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
    margin-bottom: .8rem;
}
.source-note {
    font-family: 'DM Mono', monospace;
    font-size: .65rem;
    color: #3a3a6a;
    border-left: 2px solid #1e1e3a;
    padding-left: .6rem;
    margin-bottom: 1.2rem;
    line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)

# ── Regiones y colores ─────────────────────────────────────────────────────────
REGIONES = [
    "China",
    "USA",
    "Europa (incl. UK)",
    "Japón",
    "India",
    "Resto de Asia",
    "Resto de América",
    "Oceanía",
    "Resto del Mundo",
]

COLORES = {
    "China":              "#FF4455",
    "USA":                "#4488FF",
    "Europa (incl. UK)":  "#2DDBA4",
    "Japón":              "#FFD166",
    "India":              "#FF77BB",
    "Resto de Asia":      "#F4845F",
    "Resto de América":   "#FFAA22",
    "Oceanía":            "#66BBFF",
    "Resto del Mundo":    "#666688",
}

# ── Datos históricos ───────────────────────────────────────────────────────────
# Participación estimada como destino de exportaciones mundiales (% del total)
# Fuentes: UNCTAD, OMC/WTO, FMI Direction of Trade Statistics (DOTS), Banco Mundial
#
# Notas metodológicas:
# - Europa incluye Reino Unido (UK) en todo el período, pre y post Brexit
# - Japón aparece separado por su peso propio: peak ~8% en los años 80-90
# - Resto de Asia: Corea del Sur, ASEAN, Taiwán, países del Golfo, etc.
# - Oceanía: Australia, Nueva Zelanda y Pacífico
# - China tenía <1% antes de 1980 según UNCTAD; crece con reformas Deng Xiaoping
# - Los valores suman 100 en cada año pivote

DATA_RAW = {
    #          CHN  USA  EUR   JPN  IND  ASIA  RLAM  OCE  RESTO
    1965: [    1,   14,  36,   5,   1,   8,    7,    2,   26 ],
    1970: [    1,   14,  36,   6,   1,   8,    7,    2,   25 ],
    1975: [    1,   13,  35,   7,   1,   9,    7,    2,   25 ],
    1980: [    1,   13,  34,   8,   1,   9,    7,    2,   25 ],
    1985: [    2,   15,  33,   8,   1,   10,   7,    2,   22 ],
    1990: [    3,   14,  36,   8,   1,   10,   6,    2,   20 ],
    1995: [    5,   15,  35,   7,   1,   12,   6,    2,   17 ],
    2000: [    7,   17,  34,   6,   2,   12,   6,    2,   14 ],
    2005: [   10,   16,  33,   5,   2,   13,   6,    2,   13 ],
    2010: [   13,   13,  30,   5,   3,   14,   7,    2,   13 ],
    2015: [   15,   13,  28,   4,   3,   15,   8,    2,   12 ],
    2020: [   16,   13,  27,   4,   3,   15,   8,    2,   12 ],
    2024: [   18,   13,  25,   3,   4,   16,   9,    2,   10 ],
}

def build_dataframe(raw):
    pivot = sorted(raw.keys())
    years = list(range(1965, 2025))
    rows  = []
    for y in years:
        if y in raw:
            vals = list(raw[y])
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
    st.markdown(
        "<span style='font-size:.62rem;color:#3a3a6a;line-height:1.8'>"
        "<b style='color:#5a5a8a'>Fuentes</b><br>"
        "UNCTAD · OMC · FMI DOTS<br>"
        "Banco Mundial · UN Comtrade<br><br>"
        "<b style='color:#5a5a8a'>Notas</b><br>"
        "Europa incluye UK en todo el período.<br>"
        "Datos estimados con interpolación<br>"
        "lineal entre años pivote."
        "</span>",
        unsafe_allow_html=True
    )

# ── Validación ─────────────────────────────────────────────────────────────────
if not regiones_sel:
    st.warning("Seleccioná al menos una región.")
    st.stop()

df_f = df[
    (df["Año"] >= year_range[0]) &
    (df["Año"] <= year_range[1]) &
    (df["Región"].isin(regiones_sel))
]

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">Exportaciones Mundiales</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="hero-sub">Distribución por región de destino · {year_range[0]}–{year_range[1]}</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="source-note">'
    'Fuente: UNCTAD · OMC · FMI Direction of Trade Statistics (DOTS) · Banco Mundial · UN Comtrade<br>'
    'Europa incluye Reino Unido en todo el período (pre y post Brexit) · '
    'Datos estimados con interpolación lineal entre años pivote'
    '</div>',
    unsafe_allow_html=True
)

# ── Métricas ───────────────────────────────────────────────────────────────────
def get_val(region, year):
    v = df[(df["Región"] == region) & (df["Año"] == year)]["Participación (%)"].values
    return round(v[0], 1) if len(v) else 0.0

metrics = [
    ("🇨🇳 China",             "China"),
    ("🇺🇸 USA",               "USA"),
    ("🇪🇺 Europa (incl. UK)", "Europa (incl. UK)"),
    ("🇯🇵 Japón",             "Japón"),
    ("🇮🇳 India",             "India"),
]
cols = st.columns(len(metrics))
for col, (label, region) in zip(cols, metrics):
    v_end   = get_val(region, year_range[1])
    v_start = get_val(region, year_range[0])
    delta   = round(v_end - v_start, 1)
    col.metric(label, f"{v_end:.1f}%", f"{delta:+.1f}pp vs {year_range[0]}")

st.markdown("---")

# ── Payload para el componente HTML ───────────────────────────────────────────
years_list = sorted(df_f["Año"].unique().tolist())

datasets_payload = []
for region in regiones_sel:
    sub = df_f[df_f["Región"] == region].sort_values("Año")
    datasets_payload.append({
        "label":  region,
        "color":  COLORES.get(region, "#aaaaaa"),
        "values": sub["Participación (%)"].tolist(),
    })

pie_data = [
    {"label": r, "color": COLORES.get(r, "#aaa"), "value": get_val(r, año_pie)}
    for r in regiones_sel
]

cambios = []
for region in regiones_sel:
    v0 = get_val(region, year_range[0])
    v1 = get_val(region, year_range[1])
    cambios.append({"label": region, "color": COLORES.get(region, "#aaa"), "delta": round(v1 - v0, 2)})
cambios.sort(key=lambda x: x["delta"])

payload = {
    "years":     years_list,
    "datasets":  datasets_payload,
    "chartType": tipo,
    "pie":       pie_data,
    "pieYear":   año_pie,
    "cambios":   cambios,
    "yearStart": year_range[0],
    "yearEnd":   year_range[1],
    "source":    "UNCTAD · OMC · FMI DOTS · Banco Mundial · UN Comtrade · Europa incluye UK · Datos estimados",
}

# ── Inyectar HTML ──────────────────────────────────────────────────────────────
html_path = os.path.join(os.path.dirname(__file__), "components", "chart.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_raw = f.read()

data_script = f"<script>window.__DASH_DATA__ = {json.dumps(payload)};</script>"
html_final  = html_raw.replace("<!-- DATA_INJECT -->", data_script)

import streamlit.components.v1 as components
components.html(html_final, height=1150, scrolling=False)
