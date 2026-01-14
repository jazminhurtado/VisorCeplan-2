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
    import pandas as pd
    import streamlit as st

    try:
        url = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/export?format=csv&gid=1288416966"
        df_raw = pd.read_csv(url, header=None).fillna("")

        # 🔍 Buscar fila del encabezado PEI
        fila_encabezado = None
        for i, row in df_raw.iterrows():
            row_text = " ".join(str(cell).lower() for cell in row)
            if "pliegos con pei" in row_text and "sin pei" in row_text:
                fila_encabezado = i
                break

        if fila_encabezado is None:
            st.warning("❌ No se encontró encabezado del bloque PEI.")
            return {nivel: (0, 0) for nivel in [
                "Gobierno Nacional", "Gobierno Regional", "Municipalidad Provincial", "Municipalidad Distrital"
            ]}

        # 🔁 Leer desde esa fila como encabezado
        df = pd.read_csv(url, header=fila_encabezado).fillna("")

        # Buscar columnas
        col_nivel = col_formulados = col_pendientes = None
        for col in df.columns:
            col_str = str(col).lower()
            if "nivel" in col_str and "gobierno" in col_str:
                col_nivel = col
            elif "pliegos con pei" in col_str and "formulados" in col_str:
                col_formulados = col
            elif "pendientes" in col_str and "sin pei" in col_str:
                col_pendientes = col

        if not col_nivel or not col_formulados or not col_pendientes:
            st.warning("❌ No se encontraron columnas clave de PEI.")
            return {nivel: (0, 0) for nivel in [
                "Gobierno Nacional", "Gobierno Regional", "Municipalidad Provincial", "Municipalidad Distrital"
            ]}

        def extraer(nivel):
            fila = df[df[col_nivel].str.strip().str.lower() == nivel.lower()]
            if fila.empty:
                return 0, 0
            try:
                formulados = int(str(fila.iloc[0][col_formulados]).replace(",", "").strip())
                pendientes = int(str(fila.iloc[0][col_pendientes]).replace(",", "").strip())
                return formulados, pendientes
            except Exception as e:
                st.warning(f"⚠️ Error en fila {nivel}: {e}")
                return 0, 0

        return {
            "Gobierno Nacional": extraer("Gobierno nacional"),
            "Gobierno Regional": extraer("Gobierno regional"),
            "Municipalidad Provincial": extraer("Municipalidad provincial"),
            "Municipalidad Distrital": extraer("Municipalidad distrital"),
        }

    except Exception as e:
        st.error(f"❌ Error general al cargar PEI: {e}")
        return {
            "Gobierno Nacional": (0, 0),
            "Gobierno Regional": (0, 0),
            "Municipalidad Provincial": (0, 0),
            "Municipalidad Distrital": (0, 0),
        }


def get_poi_nivel_gobierno():
    import pandas as pd
    import streamlit as st

    try:
        url = "https://docs.google.com/spreadsheets/d/1bpzY7fYHQrwqjVKvOV0CpypzbJIPaNUQ/export?format=csv&gid=1288416966"
        df = pd.read_csv(url, header=None).fillna("")

        # 🔍 Buscar la fila de encabezado de POI por contenido flexible
        fila_encabezado = None
        for i, row in df.iterrows():
            fila = [str(cell).strip().lower() for cell in row]
            if any("formulados" in cel and "elaborado" in cel for cel in fila) and \
               any("pendientes" in cel and "poi" in cel for cel in fila):
                fila_encabezado = i
                break

        if fila_encabezado is None:
            st.warning("❌ No se encontró encabezado del bloque POI.")
            return {nivel: (0, 0) for nivel in [
                "Gobierno Nacional", "Gobierno Regional", "Municipalidad Provincial", "Municipalidad Distrital"
            ]}

        # 🔁 Leer el dataframe real desde esa fila
        df = pd.read_csv(url, header=fila_encabezado).fillna("")

        # 🔍 Detectar columnas correctas de manera flexible
        col_nivel = None
        col_formulados = None
        col_pendientes = None

        for col in df.columns:
            nombre = str(col).strip().lower()
            if "nivel" in nombre and "gobierno" in nombre:
                col_nivel = col
            elif "formulados" in nombre and "elaborado" in nombre:
                col_formulados = col
            elif "pendientes" in nombre and "poi" in nombre:
                col_pendientes = col

        if not col_nivel or not col_formulados or not col_pendientes:
            st.warning("❌ No se encontraron columnas clave para POI.")
            return {nivel: (0, 0) for nivel in [
                "Gobierno Nacional", "Gobierno Regional", "Municipalidad Provincial", "Municipalidad Distrital"
            ]}

        def extraer(nivel):
            fila = df[df[col_nivel].str.strip().str.lower() == nivel.lower()]
            if fila.empty:
                return 0, 0
            try:
                formulados = int(str(fila.iloc[0][col_formulados]).replace(",", "").strip())
                pendientes = int(str(fila.iloc[0][col_pendientes]).replace(",", "").strip())
                return formulados, pendientes
            except Exception as e:
                st.warning(f"⚠️ Error en fila {nivel}: {e}")
                return 0, 0

        return {
            "Gobierno Nacional": extraer("Gobierno nacional"),
            "Gobierno Regional": extraer("Gobierno regional"),
            "Municipalidad Provincial": extraer("Municipalidad provincial"),
            "Municipalidad Distrital": extraer("Municipalidad distrital"),
        }

    except Exception as e:
        st.error(f"❌ Error general al cargar POI: {e}")
        return {
            "Gobierno Nacional": (0, 0),
            "Gobierno Regional": (0, 0),
            "Municipalidad Provincial": (0, 0),
            "Municipalidad Distrital": (0, 0),
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
@st.cache_data(ttl=600)
def load_resumen():
    url = _edit_to_csv(URL_PEI_POI_FILE_EDIT, GID_RESUMEN_NAC)
    df = pd.read_csv(url, header=None).fillna("")
    def buscar_valores(df, texto_clave, col_emitido_offset=1, col_pendiente_offset=2):
        for i, row in df.iterrows():
            for j, val in enumerate(row):
                if str(val).strip().upper() == texto_clave.upper():
                    try:
                        emitido = int(str(df.iloc[i, j + col_emitido_offset]).replace(",", ""))
                        pendiente = int(str(df.iloc[i, j + col_pendiente_offset]).replace(",", ""))
                        return (emitido, pendiente)
                    except:
                        return (0, 0)
        return (0, 0)
    pdc = buscar_valores(df, "TOTAL", 1, 2)
    pei = buscar_valores(df, "TOTAL", 2, 3)
    poi = buscar_valores(df, "TOTAL UES*", 2, 3)
    return {"PDC": pdc, "PEI": pei, "POI": poi}

@st.cache_data(ttl=600)
def load_universo():
    url = _edit_to_csv(URL_PEI_POI_FILE_EDIT, GID_DATA_UES)
    raw = pd.read_csv(url, header=None, dtype=str).fillna("")
    header_row = None
    for i, row in raw.iterrows():
        joined = " ".join(str(x).upper() for x in row.tolist())
        if "DEPART" in joined or "REGION" in joined:
            header_row = i
            break
    if header_row is None:
        st.error("❌ No encontré fila de encabezados en Data_UEs.")
        st.stop()
    df = pd.read_csv(url, header=header_row, dtype=str).fillna("")
    col_dep = None
    for c in df.columns:
        if any(k in str(c).lower() for k in ["depa", "región", "region"]):
            col_dep = c
            break
    if col_dep is None:
        st.error(f"❌ No se encontró columna de departamento. Encabezados: {list(df.columns)}")
        st.stop()

    # Normalizar y mapear departamentos
    df["departamento"] = df[col_dep].map(lambda x: CODIGOS_A_DEPARTAMENTOS.get(str(x).strip(), str(x)))
    df["departamento"] = df["departamento"].map(_norm)

    # Detectar unidad_id
    if "unidad_id" not in df.columns:
        for c in df.columns:
            if "unidad" in str(c).lower() or "ue" in str(c).lower() or "codigo" in str(c).lower():
                df.rename(columns={c: "unidad_id"}, inplace=True)
                break
    if "unidad_id" not in df.columns:
        st.error(f"❌ No encontré columna unidad en Data_UEs. Encabezados: {list(df.columns)}")
        st.stop()
    df["unidad_id"] = df["unidad_id"].astype(str)
    return df[["unidad_id","departamento"]]

@st.cache_data(ttl=600)
def load_it_pei():
    url = _edit_to_csv(URL_PEI_POI_FILE_EDIT, GID_IT_PEI)
    raw = pd.read_csv(url, header=None, dtype=str).fillna("")
    header_row = None
    for i, row in raw.iterrows():
        joined = " ".join(str(x).lower() for x in row.tolist())
        if "unidad" in joined and "estado" in joined:
            header_row = i
            break
    if header_row is None:
        st.error("❌ No encontré fila encabezado en IT PEI.")
        st.stop()
    df = pd.read_csv(url, header=header_row, dtype=str).fillna("")
    col_uid = None
    for c in df.columns:
        if "unidad" in str(c).lower() or "ue" in str(c).lower() or "codigo" in str(c).lower():
            col_uid = c
            break
    if col_uid is None:
        st.error(f"❌ No encontré unidad en IT PEI. Encabezados: {list(df.columns)}")
        st.stop()
    df.rename(columns={col_uid: "unidad_id"}, inplace=True)
    df["unidad_id"] = df["unidad_id"].astype(str)
    col_estado = None
    for c in df.columns:
        if "estado" in str(c).lower():
            col_estado = c
            break
    if col_estado is None:
        st.error(f"❌ No encontré estado en IT PEI. Encabezados: {list(df.columns)}")
        st.stop()
    df["formulado_flag"] = df[col_estado].str.lower().str.contains("aprob|emit|ajust|public").astype(int)
    return df[["unidad_id","formulado_flag"]]

@st.cache_data(ttl=600)
def load_poi_registro():
    url = _edit_to_csv(URL_PEI_POI_FILE_EDIT, GID_REGISTRO_POI)
    raw = pd.read_csv(url, header=None, dtype=str).fillna("")
    header_row = None
    for i, row in raw.iterrows():
        joined = " ".join(str(x).lower() for x in row.tolist())
        if "unidad" in joined and "estado" in joined:
            header_row = i
            break
    if header_row is None:
        st.error("❌ No encontré encabezado en POI.")
        st.stop()
    df = pd.read_csv(url, header=header_row, dtype=str).fillna("")
    col_uid = None
    for c in df.columns:
        if "unidad" in str(c).lower() or "ue" in str(c).lower() or "codigo" in str(c).lower():
            col_uid = c
            break
    if col_uid is None:
        st.error(f"❌ No encontré unidad en POI. Encabezados: {list(df.columns)}")
        st.stop()
    df.rename(columns={col_uid: "unidad_id"}, inplace=True)
    df["unidad_id"] = df["unidad_id"].astype(str)
    col_estado = None
    for c in df.columns:
        if "estado" in str(c).lower():
            col_estado = c
            break
    if col_estado is None:
        st.error(f"❌ No encontré estado en POI. Encabezados: {list(df.columns)}")
        st.stop()
    df["emitido_flag"] = df[col_estado].str.lower().str.contains("aprob|ajust|consist|seguim").astype(int)
    return df[["unidad_id","emitido_flag"]]

@st.cache_data(ttl=24*3600)
def load_geojson():
    for path in [Path("pages/peru_departa.geojson"), Path("peru_departa.geojson")]:
        if path.exists():
            gj = json.loads(path.read_text(encoding="utf-8"))
            for ft in gj["features"]:
                name = str(ft["properties"].get("NOMBDEP") or ft["properties"].get("name"))
                ft["properties"]["dep_key"] = _norm(name)
            return gj
    return None

# -----------------------------
# KPI Cards
# -----------------------------
def kpi_card(title, formulados, pendientes, unidad_label="entidades", nota=""):
    total = formulados + pendientes
    avance_pct = round((formulados / total) * 100) if total > 0 else 0

    if avance_pct < 50:
        color = "#cc3333"
    elif avance_pct < 80:
        color = "#F1C40F"
    else:
        color = "#308446"

    # Texto del tooltip con más detalle
    tooltip_text = (
        f"<b>Formulados: {formulados:,} / {total:,} {unidad_label}</b><br>"
        f"{nota}"
    )

    st.markdown(f"""
    <style>
        .kpi-card-hover {{
            border-radius: 18px;
            padding: 1.5rem;
            background-color: #ffffff;
            text-align: center;
            transition: transform 0.2s ease-in-out;
            box-shadow: 6px 6px 12px rgba(0,0,0,0.1);
            border: 1px solid #e5e7eb;
            min-height: 180px;
            width: 280px; /* <--- Ajuste aquí */
            max-width: 350px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .kpi-card-hover:hover {{
            transform: translateY(-6px);
            box-shadow: 10px 10px 18px rgba(0,0,0,0.15); 
        }}
        .kpi-container {{
            background-color:white;
            padding:22px;
            width:360px;
            border-radius:16px;
            text-align:center;
            box-shadow: -5px -5px 14px rgba(192,192,192,0.7);
            position: relative;
        }}
        .tooltip {{
            position: relative;
            display: inline-block;
        }}
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 240px;
            background-color: #555;
            color: #fff;
            font-size: 14px;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 1;
            bottom: 130%;
            left: 50%;
            margin-left: -120px;
            opacity: 0;
            transition: opacity 0.3s;
            line-height: 1.4;
        }}
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
    </style>

    <div class="kpi-card-hover">
        <div style="font-size:25px; font-weight:bold; color:black;">
            {title}
            <span class="tooltip"> 🔎
                <span class="tooltiptext">{tooltip_text}</span>
            </span>
        </div>
        <div style="font-size:45px; font-weight:bold; color:{color};">{avance_pct}%</div>
        <div style="font-size:18px; color:{color};">Avance</div>
        <div style="font-size:17px; color:#555;">
            Total: {total:,} {unidad_label}
        </div>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------
# Gráfico de barras
# -----------------------------
def resumen_grafico(titulo, formulados, pendientes,
                    color_emitido="#308446", color_pendiente="#cc3333"):
    total = formulados + pendientes
    pct_form = round((formulados / total) * 100) if total > 0 else 0
    pct_pend = 100 - pct_form

    fig = go.Figure()

    # Barras
    fig.add_trace(go.Bar(
        y=[titulo], x=[formulados],
        name="Formulados",
        orientation='h',
        marker_color=color_emitido,
        text=[f"{formulados:,}"],
        textposition="inside",
        insidetextanchor='start',
        textfont=dict(size=14)
    ))

    fig.add_trace(go.Bar(
        y=[titulo], x=[pendientes],
        name="Pendientes",
        orientation='h',
        marker_color=color_pendiente,
        text=[f"{pendientes:,}"],
        textposition="inside",
        insidetextanchor='end',
        textfont=dict(size=14)
    ))

    # Añadir % como anotaciones arriba
    fig.add_annotation(
        x=formulados / 2,
        y=0,
        text=f"<b>{pct_form}%</b> Formulados",
        showarrow=False,
        yshift=35,
        font=dict(color=color_emitido, size=15)
    )
    fig.add_annotation(
        x=formulados + (pendientes / 2),
        y=0,
        text=f"<b>{pct_pend}%</b> Pendientes",
        showarrow=False,
        yshift=35,
        font=dict(color=color_pendiente, size=15)
    )

    fig.update_layout(
        title=dict(
            text=f"<b>{titulo}</b>",
            x=0.5,
            font=dict(size=16, color="darkred")
        ),
        barmode='stack',
        height=210,
        margin=dict(l=20, r=20, t=60, b=30),
        showlegend=True,
        xaxis=dict(title='', showgrid=False),
        yaxis=dict(title='', showticklabels=False)
    )

    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Mapa
# -----------------------------
@st.cache_data(ttl=3600)
def load_resumen_departamental():
    # Datos por departamento para los 3 planes
    data = {
        "PEI": pd.DataFrame({
            "departamento": [
                "AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA",
                "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN",
                "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA",
                "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"
            ],
            "formulados": [38, 88, 48, 44, 68, 94, 13, 90, 53, 58, 30, 45, 88, 38, 220, 73, 10, 30, 14, 77, 57, 72, 55, 2, 2],
            "pendientes": [49, 82, 40, 67, 59, 39, 0, 30, 52, 30, 15, 45, 17, 7, 63, 56, 3, 23, 14, 10, 8, 33, 25, 6, 2]
        }),
        "POI": pd.DataFrame({
            "departamento": [
                "AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA",
                "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN",
                "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA",
                "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"
            ],
            "formulados": [32, 84, 43, 45, 46, 79, 13, 90, 50, 55, 44, 67, 80, 81, 312, 73, 11, 20, 15, 52, 45, 46, 42, 12, 40],
            "pendientes": [75, 126, 45, 96, 93, 88, 0, 69, 47, 48, 41, 97, 59, 29, 116, 56, 5, 20, 19, 44, 66, 57, 36, 13, 5]
        }),
        "PDC": pd.DataFrame({
            "departamento": [
                "AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA",
                "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN",
                "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA",
                "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"
            ],
            "formulados": [2, 10, 24, 6, 18, 7, 6, 20, 27, 27, 3, 13, 13, 5, 40, 2, 1, 2, 9, 2, 4, 3, 11, 2, 12],
            "pendientes": [83, 157, 62, 105, 107, 126, 25, 97, 76, 78, 41, 112, 82, 34, 132, 52, 11, 9, 21, 62, 107, 76, 63, 6, 8]
        })
    }

    # Calcular totales y avance por fila
    for k, df in data.items():
        df["departamento"] = df["departamento"].map(_norm)
        df["total"] = df["formulados"] + df["pendientes"]
        df["avance"] = round((df["formulados"] / df["total"]) * 100, 1)

    return data


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
    fig_map.update_layout(
    clickmode="none",
    legend_itemclick=False,
    legend_itemdoubleclick=False
)


    fig_map.update_traces(
        hovertemplate="""<b>📍 %{customdata[0]}</b><br><br>
📈 <b>Avance:</b> %{customdata[1]}%<br>
✅ <b>Formulados:</b> %{customdata[2]}<br>
⏳ <b>Pendientes:</b> %{customdata[3]}<br>
📊 <b>Total:</b> %{customdata[4]}<br><extra></extra>"""
    )

    fig_map.update_geos(fitbounds="locations", visible=False) 
    fig_map.update_layout(
    height=700,
    font=dict(size=16),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(
        orientation="v",
        yanchor="top",
        y=0.98,
        xanchor="left",   # <--- este es CLAVE
        x=-0.05,          # <--- esto lo empuja hacia la izquierda
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor='rgba(0,0,0,0.1)',
        borderwidth=1
    )
)


    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("""<div style='display: flex; gap: 30px; margin-top: -150px; font-size: 14px;'>
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


# 🌍 Sincronizar mapa con KPI clickeado
if st.session_state.get("hover_pdc", False):
    plan_sel = "PDC"
elif st.session_state.get("hover_pei", False):
    plan_sel = "PEI"
elif st.session_state.get("hover_poi", False): 
    plan_sel = "POI"
else:
    plan_sel = "NINGUNO"

with col1:
 with col1:
    if plan_sel == "NINGUNO":
        # Mostrar mapa neutral con un solo color
        df_base = load_resumen_departamental()["PDC"].copy()
        df_base["avance"] = 0  # Todos al 0%
        df_base["color"] = "#B3DDF2"  # celeste pasterl
        gj = load_geojson()
        fig = px.choropleth(
            df_base,
            geojson=gj,
            locations="departamento",
            featureidkey="properties.dep_key",
            color="departamento",
            color_discrete_map={row["departamento"]: "#B3DDF2" for _, row in df_base.iterrows()},
            custom_data=["departamento"]
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            height=700, 
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=-0.15 # esto empuja la leyenda a la izquierda
            )
        )    
        fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><extra></extra>")
        st.plotly_chart(fig, use_container_width=True)
    else:
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











