# pages/00_Dashboard.py
# ------------------------------------------
# Dashboard CEPLAN con KPIs, Gráficos y Mapa coroplético conectado   
# ------------------------------------------
import json, unicodedata
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import json

# --------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------
st.set_page_config(
    page_title="Dashboard CEPLAN",
    page_icon="logo_icon.png",
    layout="wide"
)

# --------------------------------------
# ESTILOS PERSONALIZADOS 
# --------------------------------------
st.markdown("""
<style>
h1 {
    margin-top: 5x;
    font-size: 2.5rem;
    font-weight: bold;
    color: #212529;
    text-align: center;
}

.block-container {
    padding-top: 2rem;
}

body, .stApp {
    background-color: #FFFFFF;
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

# --------------------------------------
# TÍTULO VISUALIZABLE
# --------------------------------------
st.markdown("""
<h1 style='
    margin-top: -20px;
    font-size: 2.7rem;
    font-weight: bold;
    color: #212529;
    text-align: center;
'>Estado Situacional de los Planes del SINAPLAN</h1>
""", unsafe_allow_html=True)

# -----------------------------
# Config
# -----------------------------
URL_PEI_POI_FILE_EDIT = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/edit"             
GID_DATA_UES     = "1259332810"   # Data_UEs
GID_IT_PEI       = "1704733507"   # IT PEI
GID_REGISTRO_POI = "1447296183"    # Registro POI
GID_RESUMEN_NAC  = "1288416966"   # hoja resumen

# ------------------------------------------
# Dashboard CEPLAN con KPIs, Gráficos y Mapa coroplético conectado   
# ------------------------------------------
import json, unicodedata
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

# --------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------
st.set_page_config(
    page_title="Dashboard CEPLAN",
    page_icon="logo_icon.png",
    layout="wide"
)

# --------------------------------------
# ESTILOS PERSONALIZADOS 
# --------------------------------------
st.markdown("""
<style>
h1 {
    margin-top: 5x;
    font-size: 2.5rem;
    font-weight: bold;
    color: #212529;
    text-align: center;
}

.block-container {
    padding-top: 2rem;
}

body, .stApp {
    background-color: #FFFFFF;
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

# Función nueva para obtener datos de PDC por nivel de gobierno
def get_pdc_nivel_gobierno():
    url = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/export?format=csv&gid=1288416966"
    df = pd.read_csv(url, header=None).fillna("")

    def buscar_valores(df, nombre_nivel):
        for i, row in df.iterrows():
            if str(row[0]).strip().lower() == nombre_nivel.lower():
                formulados = int(str(row[2]).replace(",", ""))
                pendientes = int(str(row[3]).replace(",", ""))
                return formulados, pendientes
        return 0, 0

    gr_form, gr_pend = buscar_valores(df, "Gobierno regional")
    gl_form, gl_pend = buscar_valores(df, "Gobierno local")
    return {
        "Gobierno Regional": (gr_form, gr_pend),
        "Gobierno Local": (gl_form, gl_pend)
    }


def get_pei_nivel_gobierno():
    url = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/export?format=csv&gid=1288416966"
    df = pd.read_csv(url, header=None).fillna("")

    # ✅ Verifica visualmente qué datos está leyendo
    print(df.head(20))  # Esto te permite ver si la fila es la correcta

    def buscar_valores(df, nombre_nivel):
        for i, row in df.iterrows():
            if str(row[0]).strip().lower() == nombre_nivel.lower():
                print(f"Encontrado: {nombre_nivel} ➤ fila {i} ➤ datos: {row[2]}, {row[3]}")
                try:
                    formulados = int(str(row[2]).replace(",", ""))
                    pendientes = int(str(row[3]).replace(",", ""))
                    return formulados, pendientes
                except:
                    print("⚠️ Error al convertir valores.")
                    return 0, 0
        print(f"❌ No se encontró: {nombre_nivel}")
        return 0, 0

    return {
        "Gobierno Nacional": buscar_valores(df, "Gobierno nacional"),
        "Gobierno Regional": buscar_valores(df, "Gobierno regional"),
        "Municipalidad Provincial": buscar_valores(df, "Municipalidad provincial"),
        "Municipalidad Distrital": buscar_valores(df, "Municipalidad distrital")
    }

def get_poi_nivel_gobierno():
    # Aquí colocas el código para leer desde Google Sheets
    url = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/export?format=csv&id=1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ&gid=1288416966"
    df = pd.read_csv(url).fillna("")

    # Extrae los valores correctos de POI según las cabeceras
    # Usa la misma lógica que para PEI o PDC
    def buscar_valores(df, nombre_nivel):
        for i, row in df.iterrows():
            if str(row[0]).strip().lower() == nombre_nivel.lower():
                try:
                    formulados = int(str(row[2]).replace(",", ""))
                    pendientes = int(str(row[3]).replace(",", ""))
                    return formulados, pendientes
                except:
                    return 0, 0
        return 0, 0 

    return {
        "Gobierno Nacional": buscar_valores(df, "Gobierno nacional"),
        "Gobierno Regional": buscar_valores(df, "Gobierno regional"),
        "Municipalidad Provincial": buscar_valores(df, "Municipalidad provincial"),
        "Municipalidad Distrital": buscar_valores(df, "Municipalidad distrital")
    }








def _edit_to_csv(file_edit: str, gid: str) -> str:
    file_id = file_edit.split("/d/")[1].split("/")[0]
    return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}"

def _norm(s: str) -> str:
    if s is None: return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().upper()

# -----------------------------
# Diccionario de códigos de departamentos a nombres
# -----------------------------
CODIGOS_A_DEPARTAMENTOS = {
    "1": "AMAZONAS","2": "ANCASH","3": "APURIMAC","4": "AREQUIPA",
    "5": "AYACUCHO","6": "CAJAMARCA","7": "CALLAO","8": "CUSCO",
    "9": "HUANCAVELICA","10": "HUANUCO","11": "ICA","12": "JUNIN",
    "13": "LA LIBERTAD","14": "LAMBAYEQUE","15": "LIMA","16": "LORETO",
    "17": "MADRE DE DIOS","18": "MOQUEGUA","19": "PASCO","20": "PIURA",
    "21": "PUNO","22": "SAN MARTIN","23": "TACNA","24": "TUMBES","25": "UCAYALI"
}

# -----------------------------
# Loaders
# -----------------------------
@st.cache_data(ttl=3600)
def load_resumen_departamental():
    departamentos = [
        "AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA",
        "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN", "LA LIBERTAD",
        "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO",
        "PIURA", "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"
    ]

    data = {
        "departamento": departamentos,
        "formulados": [60, 80, 45, 75, 30, 50, 85, 40, 55, 70, 90, 100, 35, 65, 95, 55, 60, 45, 70, 80, 90, 50, 60, 70, 80],
        "pendientes": [40, 20, 55, 25, 70, 50, 15, 60, 45, 30, 10, 0, 65, 35, 5, 45, 40, 55, 30, 20, 10, 50, 40, 30, 20]
    }

    df = pd.DataFrame(data)
    df["total"] = df["formulados"] + df["pendientes"]
    df["avance"] = round((df["formulados"] / df["total"]) * 100, 1)

    return {"PEI": df}

def render_map(plan: str):
    data_por_plan = load_resumen_departamental()
    if plan not in data_por_plan:
        st.warning("⚠️ Plan no encontrado.")
        return

    df = data_por_plan[plan].copy()

    def asignar_color(pct):
        if pct < 50:
            return "#cc3333"
        elif pct < 80:
            return "#F1C40F"
        else:
            return "#308446"

    df["color"] = df["avance"].apply(asignar_color)

    gj = load_geojson()
    if not gj:
        st.warning("⚠️ No se encontró el archivo GeoJSON.")
        return

    fig_map = px.choropleth(
        df,
        geojson=gj,
        locations="departamento",
        featureidkey="properties.dep_key",
        color="departamento",
        color_discrete_map={row["departamento"]: row["color"] for _, row in df.iterrows()},
        custom_data=["departamento", "avance", "formulados", "pendientes", "total"]
    )

    fig_map.update_traces(
        hovertemplate="""<b>📍 %{customdata[0]}</b><br><br>
📈 <b>Avance:</b> %{customdata[1]}%<br>
✅ <b>Formulados:</b> %{customdata[2]}<br>
⏳ <b>Pendientes:</b> %{customdata[3]}<br>
📊 <b>Total:</b> %{customdata[4]}<br><extra></extra>""",
        showlegend=True
    )

    fig_map.update_geos(fitbounds="locations", visible=False)

    fig_map.update_layout(
        height=700,
        font=dict(size=16),
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=-0.05,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        legend_itemclick=False,
        legend_itemdoubleclick=False
    )

    with st.container():
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.plotly_chart(fig_map, use_container_width=True)
        st.markdown("""<div style='display: flex; justify-content: center; gap: 30px; margin-top: -20px; font-size: 14px;'>
            <div style='display: flex; align-items: center;'>
                <div style='width: 18px; height: 18px; background-color: #CC3333; border-radius: 4px; margin-right: 8px;'></div>
                <span><strong>&lt; 50%</strong> (Bajo)</span>
            </div>
            <div style='display: flex; align-items: center;'>
                <div style='width: 18px; height: 18px; background-color: #F1C40F; border-radius: 4px; margin-right: 8px;'></div>
                <span><strong>50% - 79%</strong> (Medio)</span>
            </div>
            <div style='display: flex; align-items: center;'>
                <div style='width: 18px; height: 18px; background-color: #308446; border-radius: 4px; margin-right: 8px;'></div>
                <span><strong>≥ 80%</strong> (Alto)</span>
            </div>
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


st.radio("Selecciona plan para mapa:", options=["PEI", "POI", "PDC"], index=0, horizontal=True, key="plan_sel")
render_map(st.session_state["plan_sel"])

        

# Botón funcional fijado arriba a la izquierda
refresh_placeholder = st.empty()

st.markdown("""
<style>
div[data-testid="stVerticalBlock"] > div:first-child {
    position: relative;
}
#refrescar-btn {
    position: absolute;
    top: 15px;
    left: 15px;
    z-index: 9999;
}
</style>
""", unsafe_allow_html=True)

with refresh_placeholder.container():
    btn_clicked = st.button("🔄 Refrescar datos", key="refrescar", help="Actualiza datos desde Google Sheets", use_container_width=False)
    st.markdown("<div id='refrescar-btn'></div>", unsafe_allow_html=True)

if btn_clicked:
    st.cache_data.clear()
    st.rerun()


@st.cache_data(ttl=600, show_spinner="Leyendo Google Sheets…")
def cargar_datos_dashboard():
    import re
    import unicodedata

    SHEET_CSV = (
        "https://docs.google.com/spreadsheets/d/"
        "1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ" 
        "/export?format=csv&gid=1288416966"
    )

    def _norm(s: str) -> str:
        if s is None: return ""
        s = str(s)
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))
        s = s.lower().strip()
        s = re.sub(r"\s+", " ", s)
        return s

    def _norm_header(s: str) -> str:
        s = _norm(s)
        s = s.replace("%", " pct ")
        s = re.sub(r"[^a-z0-9 _-]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _to_int(x) -> int:
        s = str(x).strip()
        if s == "" or s.lower() in {"nan", "none"}:
            return 0
        s = s.replace(",", "").replace(" ", "")
        try:
            return int(float(s))
        except Exception:
            return 0

    def _find_header_row(df, header_tests) -> int:
        for i in range(min(len(df), 80)):
            row = [_norm_header(v) for v in df.iloc[i].tolist()]
            if all(any(all(k in _norm_header(c) for k in test) for c in row) for test in header_tests):
                return i
        return -1

    def _col_index(row: list, *must_have) -> int | None:
        for j, c in enumerate(row):
            h = _norm_header(c)
            if all(k in h for k in must_have):
                return j
        return None

    def _extract_totals(df, tipo: str) -> tuple[int, int]:
        if tipo == "PDC":
            headers = [["nivel", "gobierno"], ["total", "pliego"], ["entidades", "con", "pdc"], ["entidades", "sin", "pdc"]]
            match_val = "total"
            key_con, key_sin = ["con", "pdc"], ["sin", "pdc"]
        elif tipo == "PEI":
            headers = [["nivel", "gobierno"], ["total", "pliegos"], ["con", "pei"], ["sin", "pei"]]
            match_val = "total"
            key_con, key_sin = ["con", "pei"], ["sin", "pei"]
        else:  # POI
            headers = [
                ["nivel", "gobierno"],
                ["total", "ues"],
                ["formulados", "en", "elaborado"],
                ["pendientes", "sin", "poi"]
            ]
            match_val = "total"
            key_con  = ["formulados", "en", "elaborado"]
            key_sin  = ["pendientes", "sin", "poi"]

        hdr = _find_header_row(df, headers)
        if hdr < 0: return (0, 0)

        row = df.iloc[hdr].tolist()
        c_nivel = _col_index(row, "nivel", "gobierno")
        c_con = _col_index(row, *key_con)
        c_sin = _col_index(row, *key_sin)
        if tipo == "POI":
            if c_con is None and len(row) > 2: c_con = 2
            if c_sin is None and len(row) > 3: c_sin = 3

        if c_nivel is None or c_con is None or c_sin is None:
            return (0, 0)

        for i in range(hdr + 1, min(hdr + 60, len(df))):
            val = _norm(df.iat[i, c_nivel])
            if val.startswith(match_val):
                emitidos = _to_int(df.iat[i, c_con])
                pendientes = _to_int(df.iat[i, c_sin])
                return (emitidos, pendientes)
        return (0, 0)

    df = pd.read_csv(SHEET_CSV, header=None).fillna("")
    return {
        "PDC": _extract_totals(df, "PDC"),
        "PEI": _extract_totals(df, "PEI"),
        "POI": _extract_totals(df, "POI"),
    }

# -----------------------------
# Carga de datos desde hoja Resumen con detección robusta
# -----------------------------
try:
    datos = cargar_datos_dashboard()
except Exception as e:
    st.error(f"❌ Error al cargar datos: {e}")
    st.stop()

pdc_e, pdc_p = datos["PDC"]
pei_e, pei_p = datos["PEI"]
poi_e, poi_p = datos["POI"]

hover_pdc = st.session_state.get("hover_pdc", False)

# KPIs
# KPIs
c1, c2, c3 = st.columns([1, 1, 1], gap="small")

with c1:
    if "hover_pdc" not in st.session_state:
        st.session_state["hover_pdc"] = False

    # Crear un formulario invisible con submit implícito al hacer clic en el div
    with st.form("pdc_kpi_form"):
        # Estilos para hacer que el div sea clickeable
        st.markdown("""
        <style>
        .clickable-kpi {
            cursor: pointer;
        }
        </style>
        <div class="clickable-kpi" onclick="document.forms['pdc_kpi_form'].submit();">
        """, unsafe_allow_html=True)

        # Mostrar KPI visual
        kpi_card("PDC", pdc_e, pdc_p, "pliegos", "comprende los GN, GR, GL")

        st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("")

        if submitted:
            st.session_state["hover_pdc"] = True
            st.session_state["hover_pei"] = False  # Asegura que PEI se apague


with c2:
    if "hover_pei" not in st.session_state:
        st.session_state["hover_pei"] = False

    with st.form("pei_kpi_form"):
        st.markdown("""
        <style>
        .clickable-kpi {
            cursor: pointer;
        }
        </style>
        <div class="clickable-kpi" onclick="document.forms['pei_kpi_form'].submit();">
        """, unsafe_allow_html=True)

        kpi_card("PEI", pei_e, pei_p, "pliegos", "comprende los GN, GR, GL")

        st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("")

        if submitted:
            st.session_state["hover_pei"] = True
            st.session_state["hover_pdc"] = False  # Asegura que PDC se apague

with c3:
    if "hover_poi" not in st.session_state:
        st.session_state["hover_poi"] = False

    with st.form("poi_kpi_form"):
        st.markdown("""
        <style>
        .clickable-kpi {
            cursor: pointer;
        }
        </style>
        <div class="clickable-kpi" onclick="document.forms['poi_kpi_form'].submit();">
        """, unsafe_allow_html=True)

        kpi_card("POI", poi_e, poi_p, "UEs", "comprende los GN, GR, GL")

        st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("")

        if submitted:
            st.session_state["hover_poi"] = True
            st.session_state["hover_pei"] = False
            st.session_state["hover_pdc"] = False


# Mapa y Gráficos
col1, col2 = st.columns([2, 2])  

with col1:
   with col1:
    # Agrupamos título + radio en una sola fila horizontal
    st.markdown("""
    <style>
    .radio-label-inline {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: -10px;
    }
    </style>

    <div class="radio-label-inline">
        <span>Selecciona plan para mapa:</span>
    </div>
    """, unsafe_allow_html=True)

    # Radio funcional sin texto visible (ya lo pusimos arriba)
    plan_sel = st.radio(
        label="",
        options=["PEI", "POI", "PDC"],
        horizontal=True,
        label_visibility="collapsed"
    )

    render_map(plan_sel)

with col2:
    if st.session_state.get("hover_pdc", False):
        st.markdown("### Estado PDC por Nivel de Gobierno")
        datos_niveles = get_pdc_nivel_gobierno()
        for nivel, (form, pend) in datos_niveles.items():
            resumen_grafico(nivel, form, pend)

    elif st.session_state.get("hover_pei", False):
        st.markdown("### Estado PEI por Nivel de Gobierno")
        datos_niveles = get_pei_nivel_gobierno()
        for nivel, (form, pend) in datos_niveles.items():
            resumen_grafico(nivel, form, pend)


    elif st.session_state.get("hover_poi", False):
        st.markdown("### Estado POI por Nivel de Gobierno")
        datos_niveles = get_poi_nivel_gobierno()
        for nivel, (form, pend) in datos_niveles.items():
            resumen_grafico(nivel, form, pend)

 
    else:
        resumen_grafico("Estado PDC a Nivel Nacional", pdc_e, pdc_p)
        resumen_grafico("Estado PEI a Nivel Nacional", pei_e, pei_p)
        resumen_grafico("Estado POI a Nivel Nacional", poi_e, poi_p)











