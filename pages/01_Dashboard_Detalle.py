import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Dashboard Detalle",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- APLICAR ESTILO PARA FONDO Y TEXTO DEL SIDEBAR ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #15233C;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- TÍTULO Y BOTÓN REFRESCAR ---
st.title("Dashboard General – Estado de Instrumentos (PEI – POI – PDC)")
refresh = st.button("🔄 Refrescar datos")

# --- URL DE GOOGLE SHEETS (EstadoPDC) ---
URL_ESTADO_PDC = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/export?format=csv&gid=200314121"

# --- FUNCIÓN PARA CARGAR DATOS ---
@st.cache_data(show_spinner=True)
def load_data():
    try:
        df = pd.read_csv(URL_ESTADO_PDC)
        return df
    except Exception as e:
        st.error("⚠️ Error al cargar los datos desde Google Sheets. Verifica el enlace o el acceso público.")
        st.stop()

# --- CARGA DE DATOS ---
df_pdc = load_data()

# --- SIDEBAR ---
st.sidebar.markdown("## Planes")

# Selector tipo radio horizontal
selected_plan = st.sidebar.radio(
    "Selecciona el Plan",
    options=["PDC", "PEI", "POI"],
    index=0,
    horizontal=True
)

st.session_state.plan = selected_plan

# --- FILTRO NIVEL DE GOBIERNO (solo si PDC) ---
if st.session_state.plan == "PDC":
    niveles = df_pdc["NivelGobierno"].dropna().unique().tolist()
    seleccion_nivel = st.sidebar.multiselect("Nivel de Gobierno", opciones := niveles, default=opciones)
else:
    seleccion_nivel = []  # vacío para evitar errores lógicos si se usa luego

# --- VISUALIZACIÓN DE TABLA ---
st.subheader("Vista previa de datos - EstadoPDC")

# Filtrar si aplica
if seleccion_nivel:
    df_filtrado = df_pdc[df_pdc["NivelGobierno"].isin(seleccion_nivel)]
else:
    df_filtrado = df_pdc

st.dataframe(df_filtrado, use_container_width=True)
