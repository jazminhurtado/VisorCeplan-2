# ------------------------------------------
# Dashboard CEPLAN actualizado con enlaces publicados en CSV
# ------------------------------------------

import json, unicodedata, re
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------
st.set_page_config(
    page_title="Dashboard CEPLAN",
    page_icon="logo_icon.png",
    layout="wide"
)

# --------------------------------------
# URLs públicos en CSV (ya publicados)
# --------------------------------------
URL_RESUMEN_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR41jJ_0zU2UtGhu1lQ1g8STPxll9_VPwiJTxbwyHoscL2r8DZlfdb8vuv0HnpT3A/pub?gid=1026835295&single=true&output=csv"
URL_IT_PEI_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR41jJ_0zU2UtGhu1lQ1g8STPxll9_VPwiJTxbwyHoscL2r8DZlfdb8vuv0HnpT3A/pub?gid=1704733507&single=true&output=csv"
URL_REGISTRO_POI_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR41jJ_0zU2UtGhu1lQ1g8STPxll9_VPwiJTxbwyHoscL2r8DZlfdb8vuv0HnpT3A/pub?gid=1447296183&single=true&output=csv"
URL_DATA_UES_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR41jJ_0zU2UtGhu1lQ1g8STPxll9_VPwiJTxbwyHoscL2r8DZlfdb8vuv0HnpT3A/pub?gid=1259332810&single=true&output=csv"

# --------------------------------------
# Funciones auxiliares
# --------------------------------------
def _norm(s: str) -> str:
    if s is None: return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().upper()

# -----------------------------
# Códigos de departamentos
# -----------------------------
CODIGOS_A_DEPARTAMENTOS = {
    "1": "AMAZONAS", "2": "ANCASH", "3": "APURIMAC", "4": "AREQUIPA",
    "5": "AYACUCHO", "6": "CAJAMARCA", "7": "CALLAO", "8": "CUSCO",
    "9": "HUANCAVELICA", "10": "HUANUCO", "11": "ICA", "12": "JUNIN",
    "13": "LA LIBERTAD", "14": "LAMBAYEQUE", "15": "LIMA", "16": "LORETO",
    "17": "MADRE DE DIOS", "18": "MOQUEGUA", "19": "PASCO", "20": "PIURA",
    "21": "PUNO", "22": "SAN MARTIN", "23": "TACNA", "24": "TUMBES", "25": "UCAYALI"
}

# -----------------------------
# Cargar RESUMEN
# -----------------------------
@st.cache_data(ttl=600)
def load_resumen():
    df = pd.read_csv(URL_RESUMEN_CSV, header=None).fillna("")
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

# -----------------------------
# Cargar IT PEI
# -----------------------------
@st.cache_data(ttl=600)
def load_it_pei():
    raw = pd.read_csv(URL_IT_PEI_CSV, header=None, dtype=str).fillna("")
    header_row = next((i for i, row in raw.iterrows() if "unidad" in " ".join(row).lower() and "estado" in " ".join(row).lower()), None)
    if header_row is None:
        st.error("No se encontró encabezado en IT PEI")
        st.stop()
    df = pd.read_csv(URL_IT_PEI_CSV, header=header_row, dtype=str).fillna("")
    uid_col = next((c for c in df.columns if any(k in c.lower() for k in ["unidad", "codigo", "ue"])), None)
    estado_col = next((c for c in df.columns if "estado" in c.lower()), None)
    if not uid_col or not estado_col:
        st.error("No se encontró columna de unidad o estado en IT PEI")
        st.stop()
    df.rename(columns={uid_col: "unidad_id"}, inplace=True)
    df["unidad_id"] = df["unidad_id"].astype(str)
    df["formulado_flag"] = df[estado_col].str.lower().str.contains("aprob|emit|ajust|public").astype(int)
    return df[["unidad_id", "formulado_flag"]]

# -----------------------------
# Cargar POI
# -----------------------------
@st.cache_data(ttl=600)
def load_poi_registro():
    raw = pd.read_csv(URL_REGISTRO_POI_CSV, header=None, dtype=str).fillna("")
    header_row = next((i for i, row in raw.iterrows() if "unidad" in " ".join(row).lower() and "estado" in " ".join(row).lower()), None)
    if header_row is None:
        st.error("No se encontró encabezado en Registro POI")
        st.stop()
    df = pd.read_csv(URL_REGISTRO_POI_CSV, header=header_row, dtype=str).fillna("")
    uid_col = next((c for c in df.columns if any(k in c.lower() for k in ["unidad", "codigo", "ue"])), None)
    estado_col = next((c for c in df.columns if "estado" in c.lower()), None)
    if not uid_col or not estado_col:
        st.error("No se encontró columna de unidad o estado en Registro POI")
        st.stop()
    df.rename(columns={uid_col: "unidad_id"}, inplace=True)
    df["unidad_id"] = df["unidad_id"].astype(str)
    df["emitido_flag"] = df[estado_col].str.lower().str.contains("aprob|ajust|consist|seguim").astype(int)
    return df[["unidad_id", "emitido_flag"]]

# -----------------------------
# Cargar Data_UEs
# -----------------------------
@st.cache_data(ttl=600)
def load_universo():
    raw = pd.read_csv(URL_DATA_UES_CSV, header=None, dtype=str).fillna("")
    header_row = next((i for i, row in raw.iterrows() if "depart" in " ".join(row).lower() or "region" in " ".join(row).lower()), None)
    if header_row is None:
        st.error("No se encontró encabezado en Data_UEs")
        st.stop()
    df = pd.read_csv(URL_DATA_UES_CSV, header=header_row, dtype=str).fillna("")
    dep_col = next((c for c in df.columns if any(k in c.lower() for k in ["depa", "regi"])), None)
    uid_col = next((c for c in df.columns if any(k in c.lower() for k in ["unidad", "codigo", "ue"])), None)
    if not dep_col or not uid_col:
        st.error("No se encontró columna de departamento o unidad en Data_UEs")
        st.stop()
    df["departamento"] = df[dep_col].map(lambda x: CODIGOS_A_DEPARTAMENTOS.get(str(x).strip(), str(x))).map(_norm)
    df.rename(columns={uid_col: "unidad_id"}, inplace=True)
    df["unidad_id"] = df["unidad_id"].astype(str)
    return df[["unidad_id", "departamento"]]

# (Continúa con los KPIs, mapa y render principal como en tu código original...)
