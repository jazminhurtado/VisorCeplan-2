# Dashboard_Detalle_V2.py actualizado con columnas correctas para POI: Id_UE y ESTADO_UE

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import urllib.error

st.set_page_config(page_title="Dashboard Detalle V2", layout="wide")

# ---------------------------------
# URLS y GIDs
# ---------------------------------
FILE_ID = "1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ"
GID_UNIVERSO = "1288416966"
GID_IT_PEI = "1704733507"
GID_REGISTRO_POI = "1447296183"
GID_ESTADO_PDC = "1778012106"

# ---------------------------------
# Funciones carga seguras
# ---------------------------------
def construir_urls_csv(file_id, gid):
    return [
        f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}",
        f"https://docs.google.com/spreadsheets/d/{file_id}/pub?gid={gid}&single=true&output=csv",
        f"https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&gid={gid}"
    ]

def leer_hoja(gid):
    errores = []
    for url in construir_urls_csv(FILE_ID, gid):
        try:
            return pd.read_csv(url, dtype=str)
        except urllib.error.HTTPError as e:
            errores.append(f"{url} -> {e}")
        except Exception as e:
            errores.append(f"{url} -> {e}")
    st.error("No se pudo cargar la hoja de Google Sheets. Asegúrate de que esté publicada como CSV.")
    st.code("\n".join(errores))
    st.stop()

@st.cache_data(ttl=600)
def cargar_datos():
    df_ues = leer_hoja(GID_UNIVERSO)
    df_pei = leer_hoja(GID_IT_PEI)
    df_poi = leer_hoja(GID_REGISTRO_POI)
    df_pdc = leer_hoja(GID_ESTADO_PDC)
    return df_ues, df_pei, df_poi, df_pdc

# ---------------------------------
# Procesamiento
# ---------------------------------
def normalizar_estado(col):
    s = col.fillna("").str.lower()
    return np.select([
        s.str.contains("aprob|emit|ajust|public"),
        s.str.contains("elab"),
        s == ""
    ], ["Emitido", "En elaboración", "Pendiente"], default="En proceso")

# ---------------------------------
# MAIN
# ---------------------------------
st.title("📊 Dashboard Detalle por Instrumento")

plan_sel = st.selectbox("Selecciona el instrumento", ["PEI", "POI", "PDC"])

st.markdown("---")

# Carga
df_ues, df_pei, df_poi, df_pdc = cargar_datos()

# Cruce base
df = df_ues.copy()

# Normalización por plan
if plan_sel == "PEI":
    df_cruz = df_pei.rename(columns={
        df_pei.columns[0]: "unidad_id",
        df_pei.columns[5]: "vigencia",
        df_pei.columns[7]: "estado"
    })
    df_cruz["estado"] = normalizar_estado(df_cruz["estado"])
    df_cruz["emitido"] = df_cruz["estado"] == "Emitido"
    df = df.merge(df_cruz[["unidad_id", "estado", "vigencia", "emitido"]], on="unidad_id", how="left")

elif plan_sel == "POI":
    df_poi.columns = df_poi.columns.str.strip()
    st.warning("Columnas detectadas en 'Registro POI':")
    st.code(list(df_poi.columns))
    if "Id_UE" not in df_poi.columns or "ESTADO_UE" not in df_poi.columns:
        st.error("❌ La hoja 'Registro POI' debe contener las columnas 'Id_UE' y 'ESTADO_UE'. Verifica el nombre exacto y publica bien el CSV.")
        st.stop()
    df_cruz = df_poi.rename(columns={"Id_UE": "unidad_id", "ESTADO_UE": "estado"})
    df_cruz["estado"] = normalizar_estado(df_cruz["estado"])
    df_cruz["emitido"] = df_cruz["estado"] == "Emitido"
    df = df.merge(df_cruz[["unidad_id", "estado", "emitido"]], on="unidad_id", how="left")

elif plan_sel == "PDC":
    df_cruz = df_pdc.rename(columns={
        df_pdc.columns[0]: "unidad_id",
        df_pdc.columns[4]: "estado",
        df_pdc.columns[5]: "vigencia"
    })
    df_cruz["estado"] = normalizar_estado(df_cruz["estado"])
    df_cruz["emitido"] = df_cruz["estado"] == "Emitido"
    df = df.merge(df_cruz[["unidad_id", "estado", "vigencia", "emitido"]], on="unidad_id", how="left")

# Limpieza
df["estado"] = df["estado"].fillna("Pendiente")
df["emitido"] = df["emitido"].fillna(False)

# ---------------------------------
# FILTROS
# ---------------------------------
niveles = df["nivel"].dropna().unique().tolist()
departamentos = df["departamento"].dropna().unique().tolist()
estados = df["estado"].dropna().unique().tolist()

col1, col2, col3 = st.columns(3)
sel_nivel = col1.multiselect("Nivel de Gobierno", niveles, default=niveles)
sel_dep = col2.multiselect("Departamento", departamentos, default=departamentos)
sel_est = col3.multiselect("Estado del Plan", estados, default=estados)

filtro = (
    df["nivel"].isin(sel_nivel) &
    df["departamento"].isin(sel_dep) &
    df["estado"].isin(sel_est)
)

df_filtrado = df[filtro]

# ---------------------------------
# KPIs
# ---------------------------------
total = len(df_filtrado)
emitidos = df_filtrado["emitido"].sum()
pendientes = total - emitidos
avance = (emitidos / total * 100) if total else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Entidades Filtradas", f"{total}")
k2.metric("Emitidos", f"{emitidos}")
k3.metric("Pendientes", f"{pendientes}")
k4.metric("% Avance", f"{avance:.1f}%")

# ---------------------------------
# Gráfico
# ---------------------------------
st.markdown("### Cobertura por Nivel de Gobierno")
graf_data = df_filtrado.groupby(["nivel", "estado"]).size().reset_index(name="n")
fig = px.bar(graf_data, x="n", y="nivel", color="estado", orientation="h", text_auto=True)
fig.update_layout(height=400, xaxis_title="Entidades", yaxis_title="Nivel")
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------
# Tabla
# ---------------------------------
st.markdown("### Detalle de Entidades")
cols = ["unidad_id", "nombre", "nivel", "departamento", "estado", "vigencia"] if "vigencia" in df_filtrado.columns else ["unidad_id", "nombre", "nivel", "departamento", "estado"]
st.dataframe(df_filtrado[cols], use_container_width=True)

# ---------------------------------
# Exportar CSV
# ---------------------------------
st.download_button(
    "📥 Descargar CSV",
    df_filtrado[cols].to_csv(index=False).encode("utf-8"),
    file_name=f"detalle_{plan_sel.lower()}.csv",
    mime="text/csv"
)  

# Fin
