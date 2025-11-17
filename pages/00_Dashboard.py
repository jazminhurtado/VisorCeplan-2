# 00_Dashboard.py actualizado COMPLETO para usar Excel desde OneDrive (versión final)

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import json
from pathlib import Path
import unicodedata

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Dashboard CEPLAN", layout="wide")

# OneDrive - archivo único con múltiples hojas
URL_EXCEL = "https://onedrive.live.com/download?resid=57B77F10EE9CEE37!193"

CODIGOS_A_DEPARTAMENTOS = {
    "1": "AMAZONAS", "2": "ANCASH", "3": "APURIMAC", "4": "AREQUIPA",
    "5": "AYACUCHO", "6": "CAJAMARCA", "7": "CALLAO", "8": "CUSCO",
    "9": "HUANCAVELICA", "10": "HUANUCO", "11": "ICA", "12": "JUNIN",
    "13": "LA LIBERTAD", "14": "LAMBAYEQUE", "15": "LIMA", "16": "LORETO",
    "17": "MADRE DE DIOS", "18": "MOQUEGUA", "19": "PASCO", "20": "PIURA",
    "21": "PUNO", "22": "SAN MARTIN", "23": "TACNA", "24": "TUMBES", "25": "UCAYALI"
}

# ------------------ UTILS ------------------
def _norm(s):
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().upper()

@st.cache_data(ttl=600)
def load_resumen():
    df = pd.read_excel(URL_EXCEL, sheet_name="Resumen", header=None).fillna("")

    def buscar_valores(df, texto_clave, col_emitido_offset=1, col_pendiente_offset=2):
        for i, row in df.iterrows():
            for j, val in enumerate(row):
                if str(val).strip().upper() == texto_clave.upper():
                    try:
                        emitido = int(str(df.iloc[i, j + col_emitido_offset]).replace(",", ""))
                        pendiente = int(str(df.iloc[i, j + col_pendiente_offset]).replace(",", ""))
                        return (emitido, pendiente)
                    except:
                        return (0, 0)
        return (0, 0)

    pdc = buscar_valores(df, "TOTAL", 1, 2)
    pei = buscar_valores(df, "TOTAL", 2, 3)
    poi = buscar_valores(df, "TOTAL UES*", 2, 3)
    return {"PDC": pdc, "PEI": pei, "POI": poi}

@st.cache_data(ttl=600)
def load_universo():
    df = pd.read_excel(URL_EXCEL, sheet_name="Data_UEs", dtype=str).fillna("")
    df.columns = df.columns.str.strip().str.lower()
    col_dep = next((c for c in df.columns if "departamento" in c or "region" in c), None)
    col_uid = next((c for c in df.columns if "unidad" in c or "codigo" in c or "id" in c), None)
    if not col_uid or not col_dep:
        st.error("❌ Columnas clave no encontradas en Data_UEs")
        st.stop()
    df["departamento"] = df[col_dep].map(lambda x: CODIGOS_A_DEPARTAMENTOS.get(str(x).strip(), str(x)))
    df["departamento"] = df["departamento"].map(_norm)
    df["unidad_id"] = df[col_uid].astype(str)
    return df[["unidad_id", "departamento"]]

@st.cache_data(ttl=600)
def load_it_pei():
    df = pd.read_excel(URL_EXCEL, sheet_name="IT_PEI", dtype=str).fillna("")
    col_uid = next((c for c in df.columns if "unidad" in c.lower() or "codigo" in c.lower()), None)
    col_estado = next((c for c in df.columns if "estado" in c.lower()), None)
    if not col_uid or not col_estado:
        st.error("❌ Columnas clave no encontradas en IT_PEI")
        st.stop()
    df.rename(columns={col_uid: "unidad_id"}, inplace=True)
    df["formulado_flag"] = df[col_estado].str.lower().str.contains("aprob|emit|ajust|public").astype(int)
    return df[["unidad_id", "formulado_flag"]]

@st.cache_data(ttl=600)
def load_poi_registro():
    df = pd.read_excel(URL_EXCEL, sheet_name="Registro_POI", dtype=str).fillna("")
    col_uid = next((c for c in df.columns if "unidad" in c.lower() or "codigo" in c.lower()), None)
    col_estado = next((c for c in df.columns if "estado" in c.lower()), None)
    if not col_uid or not col_estado:
        st.error("❌ Columnas clave no encontradas en Registro_POI")
        st.stop()
    df.rename(columns={col_uid: "unidad_id"}, inplace=True)
    df["emitido_flag"] = df[col_estado].str.lower().str.contains("aprob|ajust|consist|seguim").astype(int)
    return df[["unidad_id", "emitido_flag"]]

@st.cache_data(ttl=24*3600)
def load_geojson():
    for path in [Path("pages/peru_departa.geojson"), Path("peru_departa.geojson")]:
        if path.exists():
            gj = json.loads(path.read_text(encoding="utf-8"))
            for ft in gj["features"]:
                name = str(ft["properties"].get("NOMBDEP") or ft["properties"].get("name"))
                ft["properties"]["dep_key"] = _norm(name)
            return gj
    return None

# ------------------ VISUALIZACIÓN ------------------
def kpi_card(title, formulados, pendientes):
    total = formulados + pendientes
    pct = (formulados / total * 100) if total else 0
    color = "#308446" if pct >= 80 else "#F1C40F" if pct >= 50 else "#cc3333"
    st.metric(label=title, value=f"{pct:.1f}%", delta=f"{formulados}/{total}", delta_color="normal")

def resumen_grafico(titulo, formulados, pendientes):
    total = formulados + pendientes
    pct_form = round((formulados / total) * 100) if total > 0 else 0
    pct_pend = 100 - pct_form

    fig = go.Figure()
    fig.add_trace(go.Bar(y=[titulo], x=[formulados], name="Formulados", orientation='h', marker_color="#308446"))
    fig.add_trace(go.Bar(y=[titulo], x=[pendientes], name="Pendientes", orientation='h', marker_color="#cc3333"))

    fig.update_layout(barmode='stack', height=250, margin=dict(l=20, r=20, t=40, b=20), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# ------------------ APP ------------------

if st.button("🔄 Refrescar datos"):
    st.cache_data.clear()
    st.rerun()

st.title("📊 Estado Situacional de los Planes del SINAPLAN")

datos = load_resumen()
pdc_e, pdc_p = datos["PDC"]
pei_e, pei_p = datos["PEI"]
poi_e, poi_p = datos["POI"]

c1, c2, c3 = st.columns(3)
with c1:
    kpi_card("PDC", pdc_e, pdc_p)
with c2:
    kpi_card("PEI", pei_e, pei_p)
with c3:
    kpi_card("POI", poi_e, poi_p)

col1, col2 = st.columns(2)
with col1:
    resumen_grafico("Estado PDC", pdc_e, pdc_p)
    resumen_grafico("Estado PEI", pei_e, pei_p)
    resumen_grafico("Estado POI", poi_e, poi_p)

with col2:
    st.info("🌍 El mapa departamental puede ser activado si se incluye el archivo GeoJSON 'peru_departa.geojson' en la carpeta del proyecto.")
