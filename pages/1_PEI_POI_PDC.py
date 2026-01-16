import streamlit as st
import pandas as pd

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
body, .stApp { background-color: #ffffff; }
[data-testid="stSidebar"] { background-color: #1e293b !important; }
[data-testid="stSidebar"] * {
    color: white !important;
    font-weight: 500;
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

st.image("pe.JPG", width=150)
st.title("Visor Institucional de Monitoreo")
st.markdown(
    "Consulta unificada del estado de los planes **PEI–POI y PDC** por unidad ejecutora o región."
)

# --------------------------------------
# FUNCIÓN: CARGAR Google Sheet
# --------------------------------------
@st.cache_data
def cargar_excel_google(url):
    try:
        file_id = url.split("/d/")[1].split("/")[0]
        url_descarga = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        df = pd.read_excel(url_descarga, sheet_name=0, header=None)
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar Google Sheet: {e}")
        return pd.DataFrame()

# --------------------------------------
# FUNCIÓN: Construcción segura de tabla
# --------------------------------------
def construir_tabla(df, filas, columnas, nombres):
    tabla = df.iloc[filas, columnas].copy()
    tabla = tabla.dropna(axis=1, how="all")

    if tabla.shape[1] < len(nombres):
        st.error(f"❌ La tabla no tiene suficientes columnas. Se esperaban {len(nombres)}, pero solo hay {tabla.shape[1]}.")
        st.dataframe(tabla)
        return pd.DataFrame(columns=nombres)

    tabla = tabla.iloc[:, :len(nombres)]
    tabla.columns = nombres
    return tabla

# --------------------------------------
# FUNCIÓN: Mostrar tabla formateada
# --------------------------------------
def mostrar_tabla_resumen(df, titulo):
    st.subheader(f"📊 {titulo}")
    st.dataframe(df, use_container_width=True, hide_index=True)

# --------------------------------------
# CARGA DEL GOOGLE SHEET
# --------------------------------------
url_sheet = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/edit?usp=sharing"
df_resumen = cargar_excel_google(url_sheet)

# --------------------------------------
# DEFINIR TABLAS SEGÚN POSICIONES
# --------------------------------------
resumen_pdc = construir_tabla(
    df_resumen,
    filas=slice(1, 4),
    columnas=slice(0, 4),
    nombres=["Nivel de Gobierno", "Total Pliegos", "Formulados", "Pendientes"]
)

resumen_pei = construir_tabla(
    df_resumen,
    filas=slice(7, 12),
    columnas=slice(0, 4),
    nombres=["Nivel de Gobierno", "Total Pliegos", "Formulados", "Pendientes"]
)

resumen_poi = construir_tabla(
    df_resumen,
    filas=slice(16, 21),
    columnas=slice(0, 4),
    nombres=["Nivel de Gobierno", "Total UEs", "Formulados", "Pendientes"]
)

# --------------------------------------
# SELECCIÓN Y VISUALIZACIÓN
# --------------------------------------
plan = st.selectbox("Selecciona el plan a visualizar", ["PEI–POI", "PDC"])

if plan == "PEI–POI":
    mostrar_tabla_resumen(resumen_pei, "Resumen PEI")
    mostrar_tabla_resumen(resumen_poi, "Resumen POI")

elif plan == "PDC":
    mostrar_tabla_resumen(resumen_pdc, "Resumen PDC")

# --------------------------------------
# PIE DE PÁGINA
# --------------------------------------
st.markdown(
    "<center><small>"
    "App elaborada por la Dirección Nacional de Coordinación y Planeamiento (DNCP) - CEPLAN"
    "</small></center>",
    unsafe_allow_html=True
)
