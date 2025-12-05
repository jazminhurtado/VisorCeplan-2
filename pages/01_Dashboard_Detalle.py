import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Dashboard Detalle",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- TÍTULO Y BOTÓN REFRESCAR ---
st.title("Dashboard General – Estado de Instrumentos (PDC – PEI – POI)")
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

# Selector horizontal al fondo del sidebar
st.sidebar.markdown("<div style='margin-top:80px'></div>", unsafe_allow_html=True)
st.sidebar.markdown("### <center>Seleccionar Instrumento</center>", unsafe_allow_html=True)
col1, col2, col3 = st.sidebar.columns(3)
if 'plan' not in st.session_state:
    st.session_state.plan = "PDC"
if col1.button("PDC"):
    st.session_state.plan = "PDC"
if col2.button("PEI"):
    st.session_state.plan = "PEI"
if col3.button("POI"):
    st.session_state.plan = "POI"

# --- VISUALIZACIÓN DE TABLA ---
st.subheader("Vista previa de datos - EstadoPDC")
st.dataframe(df_pdc, use_container_width=True)
