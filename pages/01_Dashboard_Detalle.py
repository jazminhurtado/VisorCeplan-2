import streamlit as st
import pandas as pd
import altair as alt

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
st.title("Estado de Instrumentos PDC – PEI – POI")
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

        # --- GRÁFICO DE BARRAS PERSONALIZADO ---
        conteo_niveles = df_filtrado['nivel_gobierno'].value_counts().reset_index()
        conteo_niveles.columns = ['Nivel de Gobierno', 'Cantidad']

        chart = alt.Chart(conteo_niveles).mark_bar().encode(
            x=alt.X('Nivel de Gobierno:N', sort='-y', title='Nivel de Gobierno'),
            y=alt.Y('Cantidad:Q', title='Cantidad'),
            tooltip=['Nivel de Gobierno', 'Cantidad']
        ).properties(
            width=700,
            height=400,
            title='Cantidad de entidades por Nivel de Gobierno'
        )

        etiquetas = alt.Chart(conteo_niveles).mark_text(
            align='center',
            baseline='bottom',
            dy=-5  # Desplazamiento hacia arriba
        ).encode(
            x='Nivel de Gobierno:N',
            y='Cantidad:Q',
            text='Cantidad:Q'
        )

        st.altair_chart(chart + etiquetas, use_container_width=True)

    else:
        st.sidebar.error("⚠️ La columna 'nivel_gobierno' no fue encontrada.")
        df_filtrado = df_pdc.copy()
else:
    df_filtrado = df_pdc.copy()

# --- VISUALIZACIÓN DE TABLA ---
st.subheader("Vista previa de datos - EstadoPDC")
st.dataframe(df_filtrado, use_container_width=True)
