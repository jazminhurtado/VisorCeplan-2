import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
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
st.title("Estado de Instrumentos")
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

# --- FILTRO SOLO PARA PDC ---
if selected_plan == "PDC":
    # Normalizar el nombre de columna en caso haya espacios o mayúsculas
    df_pdc.columns = df_pdc.columns.str.strip().str.lower()

    if 'nivel_gobierno' in df_pdc.columns:
        niveles = df_pdc['nivel_gobierno'].dropna().unique().tolist()
        niveles.sort()

        seleccion_nivel = st.sidebar.multiselect(
            "Nivel de Gobierno",
            options=niveles,
            default=niveles
        )

        df_filtrado = df_pdc[df_pdc['nivel_gobierno'].isin(seleccion_nivel)]

            # --- GRÁFICO DE BARRAS PERSONALIZADO CON MATPLOTLIB ---
        conteo_nivel = df_filtrado['nivel_gobierno'].value_counts()

        fig, ax = plt.subplots(figsize=(8, 5))

        # Colores neutros personalizados
        colors = ['#4A90E2', '#7B8B99']

        # Crear barras
        bars = ax.bar(conteo_nivel.index, conteo_nivel.values, color=colors)

        # Etiquetas encima de cada barra
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 20, f'{int(height)}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')

        # Estilo de texto de ejes
        ax.set_xlabel("Nivel de Gobierno", fontsize=12, fontweight='bold')
        ax.set_ylabel("Cantidad", fontsize=12, fontweight='bold')
        ax.set_title("Cantidad de entidades por Nivel de Gobierno", fontsize=14, fontweight='bold')

        # Ejes con texto horizontal
        plt.xticks(rotation=0, fontsize=11, fontweight='bold')
        plt.yticks(fontsize=11)

        st.pyplot(fig)


  

  
    
    
    
    
    else:
        st.sidebar.error("⚠️ La columna 'nivel_gobierno' no fue encontrada.")
        df_filtrado = df_pdc.copy()

    # --- VISUALIZACIÓN DE TABLA ---
    st.subheader("Vista previa de datos - EstadoPDC")
    st.dataframe(df_filtrado, use_container_width=True)

else:
    st.warning("🔧 Visualización aún no implementada para este plan.")
