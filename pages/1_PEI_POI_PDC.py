import streamlit as st
import pandas as pd
import re
from pathlib import Path
# import pei_poi_tablas_alineadas as pp  ← ELIMINA o COMENTA ESTA LÍNEA



# -------------------------
# CONFIGURACIÓN GENERAL
# -------------------------
st.set_page_config(
    page_title="Seguimiento POI-PEI-PDC",
    page_icon="logo_icon.png",
    layout="wide"
)

# -------------------------
# ESTILOS
# -------------------------
st.markdown("""
<style>
body, .stApp { background-color: #ffffff; }
[data-testid="stSidebar"] { background-color: #1e293b !important; }
[data-testid="stSidebar"] * {
    color: white !important;
    font-weight: 500;
    font-size: 18px;
}

/* Aumentar tamaño de fuente del label del selectbox */
div[data-baseweb="select"] > div:first-child {
#label[data-testid="stSelectboxLabel"] {
    font-size: 18px !important;
    font-weight: 600;
    color: #1e293b; /* opcional: azul oscuro como en la cabecera */
}
</style>
""", unsafe_allow_html=True)


st.image("pe.JPG", width=150)
st.title("Visor Institucional de Monitoreo - Consulta del estado de los planes PDC-PEI-POI")
#st.markdown("Consulta unificada del estado de los planes **PEI–POI y PDC** por unidad ejecutora o región.")

# -------------------------
# FUNCIONES
# -------------------------
@st.cache_data
def cargar_excel_local(path, **kwargs):
    try:
        return pd.read_excel(path, **kwargs)
    except Exception as e:
        st.error(f"❌ Error al cargar archivo local: {e}")
        return pd.DataFrame()

@st.cache_data
def cargar_excel_google(url, hoja_nombre=None):
    try:
        file_id = url.split("/d/")[1].split("/")[0]
        url_xlsx = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        df = pd.read_excel(url_xlsx, sheet_name=hoja_nombre, header=None)
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar Google Sheet: {e}")
        return pd.DataFrame()


def construir_tabla(df, filas, nombres):
    tabla = df.iloc[filas].copy()
    tabla = tabla.dropna(axis=1, how="all")
    if tabla.shape[1] < len(nombres):
        st.error(f"❌ La tabla no tiene suficientes columnas. Se esperaban {len(nombres)}, pero solo hay {tabla.shape[1]}.")
        st.dataframe(tabla)
        return pd.DataFrame(columns=nombres)
    tabla = tabla.iloc[:, :len(nombres)]
    tabla.columns = nombres
    return tabla

def mostrar_tabla_resumen(df, titulo):
    #st.subheader(f"📊 {titulo}")

    html_table = df.to_html(index=False, border=0, classes='tabla-resumen')

    st.markdown("""
    <style>
    .tabla-resumen {
        width: 60%;
        margin-left: 0;
        margin-right: auto;
        border-collapse: collapse;
        font-family: sans-serif;
        font-size: 15px;
    }
    .tabla-resumen thead th {
        background-color: #1e293b;
        color: white;
        font-weight: bold;
        text-align: center;
        padding: 8px;
    }
    .tabla-resumen tbody td {
        text-align: center;
        padding: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(html_table, unsafe_allow_html=True)



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
    return df

# -------------------------
# CARGA DE ARCHIVOS
# -------------------------
pei_df = cargar_excel_local("monitoreoPEI-POI.xlsx", sheet_name=0)
pdc_df = cargar_excel_local("monitoreoPDC.xlsx", sheet_name="pdc")

if not pei_df.empty:
    pei_df = preparar_datos(pei_df)
if not pdc_df.empty:
    pdc_df = preparar_datos(pdc_df)

# -------------------------
# GOOGLE SHEET PDC RESUMEN
# -------------------------
# Nombre exacto de la hoja donde está la tabla resumen
nombre_hoja_pdc = "Dash_Data_UEs"

# Cargar hoja correcta desde Google Sheets
df_pdc_sheet = cargar_excel_google(
    "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/edit?usp=sharing",
    hoja_nombre=nombre_hoja_pdc
)



# Construir la tabla resumen desde filas correctas
resumen_pdc = construir_tabla(
    df_pdc_sheet,
    filas=slice(1, 4),
    nombres=["Nivel de Gobierno", "Total Pliegos", "Formulados", "Pendientes"]
)




# -------------------------
# UI PRINCIPAL
# -------------------------
plan = st.selectbox("Selecciona el plan a visualizar", ["PDC", "PEI–POI"])

if plan == "PDC":
    mostrar_tabla_resumen(resumen_pdc, "Tabla Resumen PDC (Google Sheet)")

def limpiar_busqueda_pei(): st.session_state["unidad_pei"] = ""
def limpiar_busqueda_pdc(): st.session_state["unidad_pdc"] = ""

if plan == "PEI–POI":
    st.subheader("📊 Tablas Resumen PEI y POI")

    # Cargar hoja desde Google Sheets
    hoja = "Dash_Data_UEs"
    url = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/edit?usp=sharing"
    file_id = url.split("/d/")[1].split("/")[0]
    url_xlsx = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"

    # Cargar Excel completo
    try:
        df_all = pd.read_excel(url_xlsx, sheet_name=hoja, header=None)
    except Exception as e:
        st.error(f"❌ No se pudo cargar el archivo desde Google Sheets: {e}")
        st.stop()

 # Extraer tabla PEI
pei = df_all.iloc[7:12, 0:4].copy()
pei.columns = ["Nivel de Gobierno", "Formulados", "Pendientes", "Total"]
pei = pei.reset_index(drop=True)

# Extraer tabla POI
poi = df_all.iloc[16:21, 0:4].copy()
poi.columns = ["Nivel de Gobierno", "Formulados", "Pendientes", "Total"]
poi = poi.reset_index(drop=True)



    # Reordenar columnas: "Total" al final
    def reordenar(df):
        cols = [col for col in df.columns if col.lower() != "total"]
        if "Total" in df.columns:
            cols.append("Total")
        return df[cols]

    pei = reordenar(pei)
    poi = reordenar(poi)

    # Convertir a HTML
    html_pei = pei.to_html(index=False, border=0, classes='tabla-resumen')
    html_poi = poi.to_html(index=False, border=0, classes='tabla-resumen')

    # Mostrar lado a lado con estilos
    st.markdown("""
    <style>
    .tabla-resumen {
        width: 100%;
        border-collapse: collapse;
        font-family: sans-serif;
        font-size: 14px;
        margin: 0 10px;
    }
    .tabla-resumen thead th {
        background-color: #1e293b;
        color: white;
        font-weight: bold;
        text-align: center;
        padding: 8px;
    }
    .tabla-resumen tbody td {
        text-align: center;
        padding: 8px;
    }
    .tabla-container {
        display: flex;
        justify-content: space-around;
        gap: 30px;
        margin-top: 20px;
    }
    </style>
    <div class="tabla-container">
        <div>
            <h4 style='text-align:center'>PEI</h4>
            {0}
        </div>
        <div>
            <h4 style='text-align:center'>POI</h4>
            {1}
        </div>
    </div>
    """.format(html_pei, html_poi), unsafe_allow_html=True)



elif plan == "PDC":
    if pdc_df.empty:
        st.warning("No se cargaron datos de PDC.")
    else:
        st.subheader("Visor PDC - Plan de Desarrollo Concertado")
        opciones = [""] + sorted(pdc_df["codigo_nombre"].dropna().unique())
        unidad = st.selectbox("🔍 Buscar o seleccionar unidad ejecutora:", options=opciones, key="unidad_pdc")
        st.button("🪑 Limpiar búsqueda", on_click=limpiar_busqueda_pdc)

        if unidad:
            match = re.search(r"\[(\d+)\]", unidad)
            codigo = match.group(1) if match else ""
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

# -------------------------
# PIE
# -------------------------
st.markdown("<center><small>App elaborada por la Dirección Nacional de Coordinación y Planeamiento (DNCP) - CEPLAN</small></center>", unsafe_allow_html=True)
