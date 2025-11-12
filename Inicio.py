import streamlit as st
from pathlib import Path

# ---------- CONFIGURACIÓN GENERAL ----------
st.set_page_config(
    page_title="Visor CEPLAN",
    page_icon="logo_icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- REDIRECCIÓN ----------
query_params = st.query_params
_go = query_params.get("go", [None])[0] if isinstance(query_params.get("go"), list) else query_params.get("go")

page_routes = {
    "dash": "00_Dashboard",
    "dashdet": "01_Dashboard_Detalle",
    "pei": "1_PEI_POI_PDC",
    "pn": "2_Politicas_Nacionales",
    "at": "3_Asistencia_Tecnica"
}

if _go and _go in page_routes:
    st.switch_page(f"pages/{page_routes[_go]}.py")

# ---------- ESTILOS PERSONALIZADOS ----------
st.markdown("""
<style>

/* Fondo */
body, .stApp {
    background-color: #f0f4f8;
}

/* Tarjetas */
.card {
    border-radius: 18px;
    padding: 1.5rem;
    background-color: #E0E5EB;
    text-align: center;
    transition: transform 0.2s ease-in-out;
    box-shadow: 6px 6px 12px rgba(0,0,0,0.1);
    border: 1px solid #e5e7eb;
    min-height: 220px;
    display: flex;
    flex-direction: column;
    justify-content: center;

}
.card:hover {
    transform: translateY(-6px);
    box-shadow: 10px 10px 18px rgba(0,0,0,0.15); 
}
.card-icon {
    font-size: 2.6rem;
    margin-bottom: 0.4rem;
}
.card-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: #000000;
}
.card-desc {
    font-size: 0.9rem;
    color: #374151;
    margin-top: 0.5rem;
}
.section-title {
    text-align: center;
    font-size: 2.3rem;
    font-weight: 900;
    margin-top: 1.5rem;
    margin-bottom: 0.2rem;
    color: #0f172a;
}

/* Sidebar elegante */
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

/* Logo */
.logo-card img {
    width: 130px;
    margin-bottom: 1rem;
}
a {
    text-decoration: none !important ;
    color: inherit;
}

</style>
""", unsafe_allow_html=True)

# ---------- LOGO CENTRAL ----------
logo_path = Path("ceplan1.png")  # Ajusta tu logo si es otro
c1, c2, c3 = st.columns([4, 2, 4])
with c2:
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=False, width=130)
    else:
        st.markdown("### CEPLAN", unsafe_allow_html=True)

# ---------- TÍTULO CENTRAL ----------
st.markdown("<div class='section-title'>Bienvenido al Visor <b>CEPLAN</b></div>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#6b7280;'>Consulta Políticas Nacionales, PDC, PEI y POI fácilmente</p>", unsafe_allow_html=True)

# ---------- TARJETAS HORIZONTALES (USANDO st.columns) ----------
cols = st.columns(5)

def tarjeta(col, icono, titulo, desc, go):
    with col:
        st.markdown(f"""
        <a href="?go={go}" target="_self">
            <div class="card">
                <div class="card-icon">{icono}</div>
                <div class="card-title">{titulo}</div>
                <div class="card-desc">{desc}</div>
            </div>
        </a>
        """, unsafe_allow_html=True)

tarjeta(cols[0], "📊", "DASHBOARD", "Vista general para seguimiento de instrumentos.", "dash")
tarjeta(cols[1], "🔍", "DASHBOARD DETALLE", "Vista por instrumento POI–PEI–PDC, con filtros.", "dashdet")
tarjeta(cols[2], "📂", "INSTRUMENTOS DE GESTIÓN", "Monitoreo institucional de PEI – POI – PDC.", "pei")
tarjeta(cols[3], "🏛️", "POLÍTICAS NACIONALES", "Consulta de Políticas Nacionales aprobadas y en proceso.", "pn")
tarjeta(cols[4], "☎️", "ASISTENCIA TÉCNICA", "Vista de las Asistencias técnicas de los instrumentos de gestión.", "at")

# ---------- FOOTER ----------
st.markdown(
    """
    <hr style='border: none; border-top: 1px solid #d1d5db; margin-top: 60px;' />

    <p style='text-align:center; color:#9ca3af; font-size:1rem;'>    
        App elaborada por la <b>Dirección Nacional de Coordinación y Planeamiento (DNCP)</b> – CEPLAN
    </p>
    """,
    unsafe_allow_html=True
)


