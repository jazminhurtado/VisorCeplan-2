import streamlit as st
import pandas as pd
import re
from pathlib import Path

# Opcional: si ya lo pones en Inicio.py, puedes quitar esta línea.
#st.set_page_config(page_title="Monitoreo Institucional", layout="wide")
# --------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------
st.set_page_config(
    page_title="Seguimiento POI-PEI-PDC",
    page_icon="logo_icon.png",  # Asegúrate que el ícono esté en raíz
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
# CARGA DE ARCHIVOS (LOCAL)
# -------------------------
@st.cache_data
def cargar_excel_local(path, **read_kwargs):
    """Lee un Excel local con manejo de errores y cache."""
    f = Path(path)
    if not f.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {f.resolve()}")
    try:
        # engine se detecta, pero si diera problema, usa engine="openpyxl"
        return pd.read_excel(f, **read_kwargs)
    except Exception as e:
        raise RuntimeError(f"Error leyendo {f.name}: {e}")

pei_df = None
pdc_df = None
errores = []

# PEI–POI
try:
    # OJO: respeta exactamente el nombre y mayúsculas/minúsculas
    pei_df = cargar_excel_local("monitoreoPEI-POI.xlsx", sheet_name=0)
except Exception as e:
    errores.append(f"PEI–POI: {e}")

# PDC
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
    # Normalizar id_ue
    if "id_ue" in df.columns:
        df["id_ue"] = df["id_ue"].astype(str).str.replace(".0", "", regex=False)
    else:
        df["id_ue"] = ""
    # Construir etiqueta de búsqueda
    for col in ["nombre_departamento", "nombre_provincia", "nombre_unidad_ejecutora"]:
        if col not in df.columns:
            df[col] = ""
    df["codigo_nombre"] = (
        df["nombre_departamento"].astype(str).str.upper().fillna("SIN DEPTO") + " - " +
        df["nombre_provincia"].astype(str).str.upper().fillna("SIN PROV") + " - [" +
        df["id_ue"] + "] " +
        df["nombre_unidad_ejecutora"].astype(str)
    )
    return df

if pei_df is not None:
    pei_df = preparar_datos(pei_df)
if pdc_df is not None:
    pdc_df = preparar_datos(pdc_df)

# -------------------------
# UI
# -------------------------
plan = st.selectbox("Selecciona el plan a visualizar", ["PEI–POI", "PDC"])

def limpiar_busqueda_pei():
    st.session_state["unidad_pei"] = ""

def limpiar_busqueda_pdc():
    st.session_state["unidad_pdc"] = ""

# --------- PEI–POI ---------
if plan == "PEI–POI":
    if pei_df is None:
        st.warning("No se cargaron datos de PEI–POI. Verifica que el archivo **monitoreoPEI-POI.xlsx** esté en la raíz del repo.")
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
        st.warning("No se cargaron datos de PDC. Verifica que **monitoreoPDC.xlsx** exista en la raíz del repo y la hoja **pdc**.")
    else:
        st.subheader("Visor PDC - Plan de Desarrollo Concertado")
        # ----------- PDC -----------
elif plan == "PDC":
    if pdc_df is None:
        st.warning("No se cargaron datos de PDC. Verifique que **monitoreoPDC.xlsx** exista en la raíz del repo y la hoja **pdc** esté bien nombrada.")
    else:
        st.subheader("Visor PDC - Plan de Desarrollo Concertado")

        # NUEVO BLOQUE PARA TABLA DE RESUMEN
        resumen_pdc = pdc_df.groupby("nivel_gobierno")["tiene_pdc"].agg([
            ("Formulados", lambda x: (x == 1).sum()),
            ("Pendientes", lambda x: (x == 0).sum()),
        ]).reset_index()
        resumen_pdc["Total"] = resumen_pdc["Formulados"] + resumen_pdc["Pendientes"]
        resumen_total = pd.DataFrame({
            "nivel_gobierno": ["Total"],
            "Formulados": [resumen_pdc["Formulados"].sum()],
            "Pendientes": [resumen_pdc["Pendientes"].sum()],
            "Total": [resumen_pdc["Total"].sum()],
        })
        resumen_pdc = pd.concat([resumen_pdc, resumen_total], ignore_index=True)
        st.dataframe(resumen_pdc, hide_index=True, use_container_width=True)

        opciones = [""] + sorted(pdc_df["codigo_nombre"].dropna().unique())
        unidad = st.selectbox("🔍 Buscar o seleccionar unidad ejecutora:", options=opciones, key="unidad_pdc")
        st.button("🧹 Limpiar búsqueda", on_click=limpiar_busqueda_pdc)

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
                        st.write(f"**{col.replace('_', ' ').capitalize()}:** {filtro[col].values[0]}")

    st.markdown("<center><small>App elaborada por la Dirección Nacional de Coordinación y Planeamiento (DNCP) - CEPLAN</small></center>", unsafe_allow_html=True)

    
