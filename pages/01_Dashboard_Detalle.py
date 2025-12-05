# 01_Dashboard_Detalle.py con fuente actualizada para estadoPDC y ajustes iniciales

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Dashboard Detalle", layout="wide")

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
GID_PDC_ESTADO  = "200314121"  # ACTUALIZADO SEGÚN INDICACIÓN

# ---------------------------------------------
# FUNCIONES PARA CARGAR LOS DATOS
# ---------------------------------------------
@st.cache_data(ttl=600)
def load_data(url, gid):
    full_url = f"{url}/export?format=csv&gid={gid}"
    return pd.read_csv(full_url, dtype=str)

# ---------------------------------------------
# TÍTULO
# ---------------------------------------------
st.markdown("# 🗂️ Seguimiento de instrumentos PEI, POI y PDC")

# ---------------------------------------------
# SELECCIÓN DEL PLAN - ORDEN ACTUALIZADO
# ---------------------------------------------
plan = st.selectbox("Selecciona el plan", ["PDC", "PEI", "POI"])

# ---------------------------------------------
# CARGA DE DATOS
# ---------------------------------------------
df_uni = load_data(URL_UNIVERSO, GID_UNIVERSO)
df_pei = load_data(URL_PEI_EDIT, GID_PEI_ESTADO)
df_poi = load_data(URL_POI_EDIT, GID_POI_REG)
df_pdc = load_data(URL_PDC_EDIT, GID_PDC_ESTADO)

# ---------------------------------------------
# FILTROS BÁSICOS (eliminado: ¿Tiene PDC?)
# ---------------------------------------------
niveles = df_uni["nivel"].dropna().unique().tolist()
departamentos = df_uni["departamento"].dropna().unique().tolist()

col1, col2 = st.columns(2)
sel_nivel = col1.multiselect("Nivel de Gobierno", niveles, default=niveles)
sel_dep = col2.multiselect("Departamento", departamentos, default=departamentos)

filtro = (
    df_uni["nivel"].isin(sel_nivel) &
    df_uni["departamento"].isin(sel_dep)
)

base = df_uni[filtro].copy()

# ---------------------------------------------
# CONSTRUCCIÓN DEL CUADRO SEGÚN PLAN
# ---------------------------------------------
if plan == "PDC":
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
    st.markdown("### Distribución por Nivel de Gobierno")
    df_graf = base.groupby(["nivel", "con_pdc"]).size().reset_index(name="total")
    df_graf["con_pdc"] = df_graf["con_pdc"].replace({True: "Con PDC", False: "Sin PDC"})
    fig = px.bar(df_graf, x="total", y="nivel", color="con_pdc", orientation="h", text_auto=True)
    fig.update_layout(height=400, xaxis_title="Entidades", yaxis_title="Nivel")
    st.plotly_chart(fig, use_container_width=True)

    # Tabla
    st.markdown("### Detalle de entidades")
    st.dataframe(base[["unidad_id", "nombre", "nivel", "departamento", "estado", "vigencia"]], use_container_width=True)

# NOTA: Los bloques para PEI y POI se mantienen igual por ahora

# ---------------------------------------------
# Fin
