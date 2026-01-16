import streamlit as st
import pandas as pd
import re
from pathlib import Path

# --------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------
st.set_page_config(
    page_title="Seguimiento POI-PEI-PDC",
    page_icon="logo_icon.png",
    layout="wide"
)

# --------------------------------------
# ESTILOS PERSONALIZADOS 
# --------------------------------------
st.markdown("""
<style>
body, .stApp {
    background-color: #ffffff;
}
[data-testid="stSidebar"] {
    background-color: #1e293b !important;
}
[data-testid="stSidebar"] * {
    color: white !important;
    font-weight: 500;
    font-size: 15px;
}
[data-testid="stSidebar"] .css-1v0mbdj[aria-selected="true"] {
    background-color: #334155 !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 6px;
}
[data-testid="stSidebar"] a:hover {
    background-color: #475569 !important;
    color: white !important;
    border-radius: 6px;
}
a {
    text-decoration: none !important;
    color: inherit;
}
</style>
""", unsafe_allow_html=True)

st.image("pe.JPG", width=150)
st.title("Visor Institucional de Monitoreo")
st.markdown("Consulta unificada del estado de los planes PEI–POI y PDC por unidad ejecutora o región.")

# -------------------------
# CARGA DE ARCHIVOS
# -------------------------
@st.cache_data
def cargar_excel_local(path, **read_kwargs):
    f = Path(path)
    if not f.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {f.resolve()}")
    try:
        return pd.read_excel(f, **read_kwargs)
    except Exception as e:
        raise RuntimeError(f"Error leyendo {f.name}: {e}")

pei_df = None
pdc_df = None
errores = []

try:
    pei_df = cargar_excel_local("monitoreoPEI-POI.xlsx", sheet_name=0)
except Exception as e:
    errores.append(f"PEI–POI: {e}")

try:
    pdc_df = cargar_excel_local("monitoreoPDC.xlsx", sheet_name="pdc")
except Exception as e:
    errores.append(f"PDC: {e}")

if errores:
    for msg in errores:
        st.error(f"No se pudo cargar {msg}")

# -------------------------
# PREPARACIÓN DE DATOS
# -------------------------
def preparar_datos(df):
    df = df.copy()
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(" ", "_")
          .str.replace("-", "_")
    )
    if "id_ue" in df.columns:
        df["id_ue"] = df["id_ue"].astype(str).str.replace(".0", "", regex=False)
    else:
        df["id_ue"] = ""
    for col in ["nombre_departamento", "nombre_provincia", "nombre_unidad_ejecutora"]:
        if col not in df.columns:
            df[col] = ""
    df["codigo_nombre"] = (
        df["nombre_departamento"].astype(str).str.upper().fillna("SIN DEPTO") + " - " +
        df["nombre_provincia"].astype(str).str.upper().fillna("SIN PROV") + " - [" +
        df["id_ue"] + "] " +
        df["nombre_unidad_ejecutora"].astype(str)
    )
    # Generar nivel de gobierno si no existe
    if "nivel_de_gobierno" not in df.columns:
        condiciones = [
            df["nombre_unidad_ejecutora"].str.contains("MINISTERIO|NACIONAL|SECTOR", case=False, na=False),
            df["nombre_unidad_ejecutora"].str.contains("GOBIERNO REGIONAL", case=False, na=False),
            df["nombre_unidad_ejecutora"].str.contains("MUNICIPALIDAD PROVINCIAL", case=False, na=False),
            df["nombre_unidad_ejecutora"].str.contains("MUNICIPALIDAD DISTRITAL", case=False, na=False),
        ]
        opciones = ["Gobierno nacional", "Gobierno regional", "Municipalidad provincial", "Municipalidad distrital"]
        df["nivel_de_gobierno"] = "Otro"
        for cond, val in zip(condiciones, opciones):
            df.loc[cond, "nivel_de_gobierno"] = val
    return df

if pei_df is not None:
    pei_df = preparar_datos(pei_df)
if pdc_df is not None:
    pdc_df = preparar_datos(pdc_df)

# -------------------------
# UI
# -------------------------
plan = st.selectbox("Selecciona el plan a visualizar", ["PEI–POI", "PDC"])

# ================================
# TABLAS RESUMEN DINÁMICAS
# ================================
def mostrar_tabla_resumen(df, titulo):
    st.markdown(f"### 📊 {titulo}")
    st.markdown("""
    <style>
    .resumen-table td, .resumen-table th {
        border: 1px solid #ccc;
        padding: 8px 12px;
        text-align: center;
    }
    .resumen-table {
        border-collapse: collapse;
        width: 80%;
        margin-top: 10px;
        margin-bottom: 30px;
    }
    .resumen-table thead {
        background-color: #1e293b;
        color: white;
    }
    .resumen-table tbody tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    </style>
    """, unsafe_allow_html=True)

    html = "<table class='resumen-table'><thead><tr>"
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df.iterrows():
        html += "<tr>"
        for val in row:
            html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

if plan == "PEI–POI" and pei_df is not None:
def pick_column(df, nombre_parcial):
    return next((col for col in df.columns if nombre_parcial in col), None)

col_gob = pick_column(pei_df, "nivel_de_gobierno")
col_for = pick_column(pei_df, "formulados_pliegos_con_pei")
col_pen = pick_column(pei_df, "pendientes_pliegos_sin_pei")
col_tot = pick_column(pei_df, "total_pliegos")

if all([col_gob, col_for, col_pen, col_tot]):
    resumen_pei = pei_df.groupby(col_gob, dropna=False).agg({
        col_for: "sum",
        col_pen: "sum",
        col_tot: "sum"
    }).reset_index()
    resumen_pei.columns = ["Nivel de Gobierno", "Formulados", "Pendientes", "Total"]
    resumen_pei.loc["Total"] = resumen_pei[["Formulados", "Pendientes", "Total"]].sum(numeric_only=True)
    resumen_pei.at["Total", "Nivel de Gobierno"] = "Total"
    mostrar_tabla_resumen(resumen_pei, "Resumen PEI")
else:
    st.warning("❌ No se encontraron todas las columnas necesarias para el resumen PEI.")

    resumen_pei.columns = ["Nivel de Gobierno", "Formulados", "Pendientes", "Total"]
    resumen_pei.loc["Total"] = resumen_pei[["Formulados", "Pendientes", "Total"]].sum(numeric_only=True)
    resumen_pei.at["Total", "Nivel de Gobierno"] = "Total"

    resumen_poi = pei_df.groupby("nivel_de_gobierno", dropna=False).agg({
        "formulados_en_elaborado": "sum",
        "pendientes_ues_sin_poi_2026_2028": "sum",
        "total_ues*": "sum"
    }).reset_index()
    resumen_poi.columns = ["Nivel de Gobierno", "Formulados", "Pendientes", "Total"]
    resumen_poi.loc["Total"] = resumen_poi[["Formulados", "Pendientes", "Total"]].sum(numeric_only=True)
    resumen_poi.at["Total", "Nivel de Gobierno"] = "Total"

    mostrar_tabla_resumen(resumen_pei, "Resumen PEI")
    mostrar_tabla_resumen(resumen_poi, "Resumen POI")

elif plan == "PDC" and pdc_df is not None:
    resumen_pdc = pdc_df.groupby("nivel_de_gobierno", dropna=False).agg({
        "formulados_entidades_con_pdc": "sum",
        "pendientes_entidades_sin_pdc": "sum",
        "total_pliegos": "sum"
    }).reset_index()
    resumen_pdc.columns = ["Nivel de Gobierno", "Formulados", "Pendientes", "Total"]
    resumen_pdc.loc["Total"] = resumen_pdc[["Formulados", "Pendientes", "Total"]].sum(numeric_only=True)
    resumen_pdc.at["Total", "Nivel de Gobierno"] = "Total"
    mostrar_tabla_resumen(resumen_pdc, "Resumen PDC")

# -------------------------
# BÚSQUEDA DETALLADA POR UE
# -------------------------
def limpiar_busqueda_pei():
    st.session_state["unidad_pei"] = ""

def limpiar_busqueda_pdc():
    st.session_state["unidad_pdc"] = ""

# --------- PEI–POI ---------
if plan == "PEI–POI":
    if pei_df is None:
        st.warning("No se cargaron datos de PEI–POI.")
    else:
        opciones = [""] + sorted(pei_df["codigo_nombre"].dropna().unique())
        unidad = st.selectbox("🔍 Buscar o seleccionar unidad ejecutora:", options=opciones, key="unidad_pei")
        st.button("🪑 Limpiar búsqueda", on_click=limpiar_busqueda_pei)

        if unidad:
            codigo_match = re.search(r"\[(\d+)\]", unidad)
            codigo = codigo_match.group(1) if codigo_match else ""
            filtro = pei_df[pei_df["id_ue"] == codigo]

            if not filtro.empty:
                st.subheader("Información PEI disponible:")
                columnas_pei = [
                    "tiene_pei", "tipo_pei", "periodo_ultimo_pei",
                    "pei_vigente", "estado_pei", "fase_pei",
                    "expediente", "nro_informe_tecnico", "fecha_informe_tecnico",
                    "especialista_asignado", "correo_electronico_especialista"
                ]
                for col in columnas_pei:
                    if col in filtro.columns and pd.notna(filtro[col].values[0]):
                        st.write(f"**{col.replace('_',' ').capitalize()}:** {filtro[col].values[0]}")

                st.subheader("Información POI disponible:")
                columnas_poi = [
                    "poi_2024_en_seguimiento", "poi_2025_en_seguimiento",
                    "poi_2025_en_consistenciado", "poi_2025_2027_en_elaboración",
                    "poi_2026_2028_en_elaboración", "poi_2026_2028_en_aprobado"
                ]
                for col in columnas_poi:
                    if col in filtro.columns and pd.notna(filtro[col].values[0]):
                        estado = str(filtro[col].values[0]).strip().lower()
                        icono = "✅" if "seguimiento" in estado else "🔆" if "aprobado" in estado else "🟡" if "consistenciado" in estado else "🔴"
                        etiqueta = col.replace("_", " ").capitalize().replace("Poi", "POI")
                        st.markdown(f"{icono} **{etiqueta}:** {filtro[col].values[0]}")

# ----------- PDC -----------
elif plan == "PDC":
    if pdc_df is None:
        st.warning("No se cargaron datos de PDC.")
    else:
        st.subheader("Visor PDC - Plan de Desarrollo Concertado")
        opciones = [""] + sorted(pdc_df["codigo_nombre"].dropna().unique())
        unidad = st.selectbox("🔍 Buscar o seleccionar unidad ejecutora:", options=opciones, key="unidad_pdc")
        st.button("🪑 Limpiar búsqueda", on_click=limpiar_busqueda_pdc)

        if unidad:
            codigo_match = re.search(r"\[(\d+)\]", unidad)
            codigo = codigo_match.group(1) if codigo_match else ""
            filtro = pdc_df[pdc_df["id_ue"] == codigo]

            if not filtro.empty:
                st.subheader("Información del PDC")
                columnas_pdc = [
                    "tiene_pdc", "tipo_pdc", "periodo_ultimo_pdc",
                    "pdc_vigente", "estado_pdc", "fase_pdc",
                    "expediente_pdc", "fecha_informe_tecnico_pdc",
                    "nro_informe_tecnico_pdc", "especialista_asignado_pdc",
                    "correo_electronico_especialista_pdc"
                ]
                for col in columnas_pdc:
                    if col in filtro.columns and pd.notna(filtro[col].values[0]):
                        st.write(f"**{col.replace('_',' ').capitalize()}:** {filtro[col].values[0]}")

# Pie
st.markdown("<center><small>App elaborada por la Dirección Nacional de Coordinación y Planeamiento (DNCP) - CEPLAN</small></center>", unsafe_allow_html=True)
