import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from modules.gsheet import load_data

# --- Configuración de página ---
st.set_page_config(page_title="Dashboard Detalle", layout="wide")

# --- Constantes ---
URL_ESTADO_PDC = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/export?format=csv&id=1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ&gid=200314121"

# --- Cargar datos con caché ---
@st.cache_data(ttl=1800)
def cargar_datos():
    df_pdc = pd.read_csv(URL_ESTADO_PDC, dtype=str)
    return df_pdc

# --- Layout Principal ---
st.title("Dashboard General – Estado de Instrumentos (PEI – POI – PDC)")

# Botón para recargar datos si es necesario
if st.button("🔄 Refrescar datos"):
    st.cache_data.clear()
    st.experimental_rerun()

# --- Cargar datos ---
df_pdc = cargar_datos()

# --- Filtros Sidebar ---
st.sidebar.title("Planes")

# Selección de tipo de plan
plan = st.sidebar.radio("Selecciona el Plan", ["PDC", "PEI", "POI"], index=0, horizontal=True)

# Mostrar selectbox de nivel de gobierno SOLO para PDC
niveles_disponibles = df_pdc['nivel_gobierno'].dropna().unique().tolist()
niveles_ordenados = sorted(niveles_disponibles)
niveles_seleccionados = []
if plan == "PDC":
    niveles_seleccionados = st.sidebar.multiselect("Nivel de Gobierno", opciones=niveles_ordenados, default=niveles_ordenados)

# --- Título por plan ---
st.subheader(f"Vista previa de datos - Estado{plan}")

# --- Filtrado por nivel de gobierno si aplica ---
if plan == "PDC" and niveles_seleccionados:
    df_filtrado = df_pdc[df_pdc['nivel_gobierno'].isin(niveles_seleccionados)]
else:
    df_filtrado = df_pdc.copy()

# --- Mostrar tabla de vista previa ---
st.dataframe(df_filtrado.head(30), use_container_width=True)

# --- Gráfico de barras por Nivel de Gobierno ---
st.subheader("Distribución por Nivel de Gobierno")
conteo_niveles = df_filtrado['nivel_gobierno'].value_counts().sort_index()

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(conteo_niveles.index, conteo_niveles.values, color="#3399FF")
ax.set_title("Cantidad de Entidades por Nivel de Gobierno")
ax.set_ylabel("Cantidad")
ax.set_xlabel("Nivel de Gobierno")
ax.grid(axis='y', linestyle='--', alpha=0.7)

for i, v in enumerate(conteo_niveles.values):
    ax.text(i, v + 1, str(v), ha='center', va='bottom')

st.pyplot(fig)
