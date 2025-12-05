# 01_Dashboard_Detalle.py (versión con selector horizontal y fondo como imagen)
# - Selector horizontal de planes
# - Fondo claro tipo visor CEPLAN

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Dashboard Detalle", layout="wide")

# Estilos personalizados para fondo y botones
st.markdown("""
    <style>
        .stApp {
            background-color: #F7FAFC;
        }
        section[data-testid="stSidebar"] {
            background-color: #1B2B49;
            color: white;
        }
        .css-1v0mbdj.edgvbvh3 {  /* Texto título sidebar */
            color: white;
        }
        .css-17eq0hr {  /* Botones multiselect */
            background-color: #E53935;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------
# ENLACES A GOOGLE SHEETS
# ---------------------------------------------
URL_UNIVERSO    = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/edit"
URL_PEI_EDIT    = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/edit"
URL_POI_EDIT    = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/edit"
URL_PDC_EDIT    = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/edit"

GID_UNIVERSO    = "1288416966"
GID_PEI_ESTADO  = "1704733507"
GID_POI_REG     = "1447296183"
GID_PDC_ESTADO  = "200314121"

@st.cache_data(ttl=600)
def load_data(url, gid):
    full_url = f"{url}/export?format=csv&gid={gid}"
    return pd.read_csv(full_url, dtype=str)

# ---------------------------------------------
# TITULO Y REFRESH
# ---------------------------------------------
st.title("Dashboard General – Estado de Instrumentos (PEI – POI – PDC)")

with st.expander("Refrescar (releer Google Sheets)"):
    st.cache_data.clear()
    st.success("Datos actualizados")

# ---------------------------------------------
# SELECTOR HORIZONTAL DE PLANES (PDC – PEI – POI)
# ---------------------------------------------
col1, col2, col3 = st.columns(3)
with col1: pdc_opt = st.button("PDC")
with col2: pei_opt = st.button("PEI")
with col3: poi_opt = st.button("POI")

# Variable seleccionada
if 'plan' not in st.session_state:
    st.session_state.plan = "PDC"
if pdc_opt: st.session_state.plan = "PDC"
if pei_opt: st.session_state.plan = "PEI"
if poi_opt: st.session_state.plan = "POI"

plan = st.session_state.plan

# ---------------------------------------------
# FILTROS BÁSICOS (sidebar limpio)
# ---------------------------------------------
df_uni = load_data(URL_UNIVERSO, GID_UNIVERSO)
niveles = df_uni["nivel"].dropna().unique().tolist()
departamentos = df_uni["departamento"].dropna().unique().tolist()

st.sidebar.subheader("Nivel de Gobierno")
sel_nivel = st.sidebar.multiselect("", niveles, default=niveles)

st.sidebar.subheader("Departamento")
sel_dep = st.sidebar.multiselect("", departamentos, default=departamentos)

filtro = (
    df_uni["nivel"].isin(sel_nivel) &
    df_uni["departamento"].isin(sel_dep)
)

base = df_uni[filtro].copy()

# ---------------------------------------------
# BLOQUE PDC
# ---------------------------------------------
if plan == "PDC":
    df_pdc = load_data(URL_PDC_EDIT, GID_PDC_ESTADO)
    df_cruz = df_pdc.rename(columns={
        df_pdc.columns[0]: "unidad_id",
        df_pdc.columns[4]: "estado",
        df_pdc.columns[5]: "vigencia"
    })
    df_cruz["estado"] = df_cruz["estado"].fillna("No cuenta")
    df_cruz["con_pdc"] = df_cruz["estado"].str.lower().str.contains("emitido|aprob|public|ajust")
    base = base.merge(df_cruz[["unidad_id", "estado", "vigencia", "con_pdc"]], on="unidad_id", how="left")
    base["con_pdc"] = base["con_pdc"].fillna(False)
    base["estado"] = base["estado"].fillna("No cuenta")

    # KPIs
    total = len(base)
    con_pdc = base["con_pdc"].sum()
    sin_pdc = total - con_pdc
    brecha = (sin_pdc / total * 100) if total else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Entidades", f"{total}")
    k2.metric("Con PDC", f"{con_pdc}")
    k3.metric("Brecha", f"{brecha:.1f}%")

    # Gráfico
    st.markdown("### Cobertura por Nivel de Gobierno (Con PDC vs Sin PDC)")
    df_graf = base.groupby(["nivel", "con_pdc"]).size().reset_index(name="total")
    df_graf["con_pdc"] = df_graf["con_pdc"].replace({True: "Con PDC", False: "Sin PDC"})
    fig = px.bar(df_graf, x="nivel", y="total", color="con_pdc", barmode="stack", text_auto=True)
    fig.update_layout(height=400, xaxis_title="Nivel", yaxis_title="Entidades")
    st.plotly_chart(fig, use_container_width=True)

    # Tabla
    st.markdown("### Resumen por nivel")
    df_tabla = base.groupby("nivel").agg(
        total_entidades=("unidad_id", "count"),
        con_pdc=("con_pdc", "sum")
    ).reset_index()
    df_tabla["sin_pdc"] = df_tabla["total_entidades"] - df_tabla["con_pdc"]
    st.dataframe(df_tabla, use_container_width=True)

# BLOQUES PEI y POI pendientes

# FIN
