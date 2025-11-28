import re
import io
import unicodedata
import pandas as pd
import streamlit as st
from natsort import natsorted
from fpdf import FPDF

# --------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------
st.set_page_config(
    page_title="Políticas Nacionales",
    page_icon="logo_icon.png",  # Asegúrate que el ícono esté en raíz
    layout="wide"
)

# --------------------------------------
# ESTILOS PERSONALIZADOS COMO INICIO.PY
# --------------------------------------
st.markdown("""
<style>
body, .stApp {
    background-color: #ffffff;
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


# ============ Utilidades de normalización ============
def _norm(s: str) -> str:
    if pd.isna(s): return ""
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join([c for c in s if not unicodedata.combining(c)])
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _norm_header(s: str) -> str:
    if s is None: return ""
    s = _norm(str(s))
    s = s.replace("%","pct")
    s = re.sub(r"[^a-z0-9 _-]+"," ", s)
    s = s.replace("  "," ").strip()
    return s

def _split_multi(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    s = str(val).strip()
    if not s:
        return []
    parts = re.split(r"[;\n|\u2022]+", s)
    parts = [p.strip() for p in parts if p.strip()]
    return parts

# ============ Carga de datos ============
@st.cache_data
def load_data():
    df = pd.read_excel("matriz_consistencia_pn.xlsx", sheet_name="47aprobadas")
    cols_map = {c: _norm_header(c) for c in df.columns}
    df.rename(columns=cols_map, inplace=True)

    def pick(*cands, fallback=None):
        for c in cands:
            if c in df.columns:
                return c
        return fallback

    col_pn   = pick("politica_nacional_pn", "politica")
    col_nro  = pick("nro_pn", "nro")
    col_est  = pick("estado")
    col_tipo = pick("tipo")
    col_per  = pick("periodo")
    col_ml   = pick("marco_legal")
    col_pp   = pick("problema_publico")
    col_cond = pick("conductor")
    col_int  = pick("intervinientes")
    col_it   = pick("informe_tecnico")
    col_ds   = pick("decreto_supremo_aprobacion")
    col_op   = pick("objetivo_prioritario")
    col_lin  = pick("lineamiento")
    col_srv  = pick("servicio")
    col_prov = pick("proveedor_del_servicio")
    col_receptor = pick("persona_receptor_servicio")

    cols = dict(pn=col_pn, nro=col_nro, estado=col_est, tipo=col_tipo, periodo=col_per,
                marco_legal=col_ml, problema_publico=col_pp, conductor=col_cond,
                intervinientes=col_int, informe=col_it, ds=col_ds,
                op=col_op, lin=col_lin, servicios=col_srv,
                proveedores=col_prov, receptor=col_receptor)

    df["__nombre_normalizado"] = df[cols["pn"]].map(_norm) if cols["pn"] else ""
    df["__nro_str"] = df[cols["nro"]].astype(str).str.strip() if cols["nro"] else ""
    df["__nro_normalizado"] = df["__nro_str"].map(_norm)
    df["__opcion_combo"] = df["__nro_str"] + " - " + df[cols["pn"]]

    return df, cols

df, COLS = load_data()

# ============ UI ============
#st.image("pn.jpg", width=80)
#st.title("Visor - Consulta de Políticas Nacionales del Perú")
# TÍTULO COMPACTO Y AL RAS
st.markdown("""
<style>
.titulo-visor {
    font-size: 46px;
    font-weight: 700;
    color: #1e293b;
    margin-top: -50px;
    margin-bottom: 5px;
}
</style>

<div class="titulo-visor">
    Visor de Políticas Nacionales del Perú  
</div>
""", unsafe_allow_html=True)


# =============================
# TABLA VISUAL DE PN POR TIPO Y ESTADO
# =============================
#st.markdown("###       Resumen de Políticas Nacionales por Tipo y Estado")
# Quitar duplicados por número de PN
col_tipo = COLS["tipo"]
col_estado = COLS["estado"]
col_nro = COLS["nro"]

df_clean = df.drop_duplicates(subset=col_nro)
df_clean["estado_norm"] = df_clean[col_estado].str.lower().str.strip()
df_clean["tipo_norm"] = df_clean[col_tipo].str.lower().str.strip()

# Mapear nombres presentables
tipo_map = {"sectorial": "Sectorial", "multisectorial": "Multisectorial"}
estado_map = {"aprobada": "Aprobadas ✅", "en proceso": "En Proceso ⏳"}

df_clean["tipo_final"] = df_clean["tipo_norm"].map(tipo_map).fillna("Otro")
df_clean["estado_final"] = df_clean["estado_norm"].map(estado_map).fillna("Otro")

# Generar tabla resumen
resumen_estado = pd.crosstab(df_clean["tipo_final"], df_clean["estado_final"])
resumen_estado["Total 📊"] = resumen_estado.sum(axis=1)
fila_total = pd.DataFrame(resumen_estado.sum(axis=0)).T
fila_total.index = ["Total"]
resumen_estado = pd.concat([resumen_estado, fila_total])

# Mostrar tabla con estilo
st.markdown("""
<style>
.pn-tabla-resumen td, .pn-tabla-resumen th {
    border: 1px solid #ccc;
    padding: 8px 12px;
    text-align: center;
}
.pn-tabla-resumen {
    border-collapse: collapse;
    width: 80%;
    margin-top: 10px;
    margin-bottom: 30px;
}
.pn-tabla-resumen thead {
    background-color: #1e293b;
    color: white;
}
.pn-tabla-resumen tbody tr:nth-child(even) {
    background-color: #f9f9f9;
}
</style>
""", unsafe_allow_html=True)

tabla_html = "<table class='pn-tabla-resumen'><thead><tr><th>Tipo de Política</th>"
for col in resumen_estado.columns:
    tabla_html += f"<th>{col}</th>"
tabla_html += "</tr></thead><tbody>"

for idx, row in resumen_estado.iterrows():
    tabla_html += f"<tr><td><b>{idx}</b></td>"
    for val in row:
        tabla_html += f"<td>{val}</td>"
    tabla_html += "</tr>"
tabla_html += "</tbody></table>"

st.markdown(tabla_html, unsafe_allow_html=True)



df_sorted = df.loc[natsorted(df.index, key=lambda i: df.loc[i, "__nro_str"])]
opciones = ["-- Selecciona una política --"] + df_sorted["__opcion_combo"].drop_duplicates().tolist() 

with st.container():
    col1, col2 = st.columns([9, 1])
    with col1:
        st.markdown("""
        <div style='
            font-size: 20px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 6px;
        '>    
        📁 Consulta una Política Nacional del Perú :"
        </div>
        """, unsafe_allow_html=True)

        # Mostrar el selectbox sin su label original
        seleccion = st.selectbox(
            label=" ",  # ← no texto
            options=opciones,
            key="combo_pn",
            label_visibility="collapsed"  # ← oculta el label original
        )       
                   



    with col2:
       #with st.container():
            st.markdown(
                """
                <style>
                div.stButton > button {
                    width: 100px;
                    white-space: nowrap;
                    font-size: 14px;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            if st.button("Limpiar", key="limpiar_btn_pn"):
                if "combo_pn" in st.session_state:
                    del st.session_state["combo_pn"]
                st.rerun()








def _si(campo):
    val = campo if not isinstance(campo, str) else campo
    if pd.isna(val) or str(val).strip() == "": return "No registrado"
    return val

if seleccion != "-- Selecciona una política --":
    nro = seleccion.split(" - ")[0].strip()
    resultados = df_sorted[df_sorted["__nro_str"].astype(str) == nro]

    if not resultados.empty:
        c = COLS
        nombre_politica = resultados.iloc[0][c["pn"]]
        tipo = str(resultados.iloc[0].get(c["tipo"], "—"))

        st.subheader(f"💡 {nombre_politica}")

        colA, colB = st.columns(2)
        with colA:
            st.markdown(f"**Número:** {_si(resultados.iloc[0].get(c['nro']))}")
           # Estado con color
            estado_valor = _si(resultados.iloc[0].get(c['estado']))
            color_estado = "#198754" if "aprobada" in estado_valor.lower() else "#dc3545"
            estado_html = f"<b>Estado:</b> <span style='background-color:{color_estado};color:white;padding:4px 12px;border-radius:6px;font-size:14px;'>● {estado_valor}</span>"
            st.markdown(estado_html, unsafe_allow_html=True)


            st.markdown(f"**Periodo:** {_si(resultados.iloc[0].get(c['periodo']))}")
            st.markdown(f"**Marco legal:** {_si(resultados.iloc[0].get(c['marco_legal']))}")
            st.markdown(f"**Problema Público:** {_si(resultados.iloc[0].get(c['problema_publico']))}")
        with colB:
            #st.markdown(f"**Tipo:** {tipo}")
            color_tipo = "#0d6efd" if "sectorial" in tipo.lower() else "#fd7e14"
            tipo_html = f"<b>Tipo:</b> <span style='background-color:{color_tipo};color:white;padding:4px 10px;border-radius:6px;font-size:14px'>{tipo}</span>"
            st.markdown(tipo_html, unsafe_allow_html=True)

            st.markdown(f"**Conductor:** {_si(resultados.iloc[0].get(c['conductor']))}")
            st.markdown(f"**Interviniente:** {_si(resultados.iloc[0].get(c['intervinientes']))}")
            st.markdown(f"**Informe Técnico CEPLAN:** {_si(resultados.iloc[0].get(c['informe']))}")
            st.markdown(f"**Aprobación Decreto Supremo:** {_si(resultados.iloc[0].get(c['ds']))}")

        st.markdown("### 🎯 Objetivos Prioritarios, Lineamientos, Servicios, Proveedores y Receptores")

        needed_cols = [c["op"], c["lin"], c["servicios"], c["proveedores"], c["receptor"]]
        sub = resultados[needed_cols].dropna(subset=[c["lin"]])

        if sub.empty:
            st.info("No se encontraron columnas de OP/Lineamientos en la selección.")
        else:
            ops = [op for op in sub[c["op"]].dropna().unique()]
            for op in ops:
                st.markdown(f"**🔶 {op}**")
                lin_rows = sub[sub[c["op"]] == op]
                lineamientos = list(dict.fromkeys(lin_rows[c["lin"]].tolist()))

                for lin in lineamientos:
                    rlin = lin_rows[lin_rows[c["lin"]] == lin]

                    #with st.expander(f"➤ {lin}", expanded=False):
                    with st.expander(f" {lin}", expanded=False):    
                        rows = rlin[[c["servicios"], c["proveedores"], c["receptor"]]].dropna(how="all")

                        # Detectar si un servicio se repite con distintos proveedores/receptores
                        if rows[c["servicios"]].duplicated().any():
                            rows = (
                                rows.groupby(c["servicios"], as_index=False)
                                .agg({
                                    c["proveedores"]: lambda x: ", ".join(sorted(set(x.dropna()))),
                                    c["receptor"]: lambda x: ", ".join(sorted(set(x.dropna())))
                                })
                                .reset_index(drop=True)
                            )
                        else:
                            rows = rows.drop_duplicates()

                        if not rows.empty:
                            table_html = """<table style='width:100%; border-collapse: collapse;'>
                            <tr style='background:#f0f0f0;'><th style='border:1px solid #ddd;padding:8px;'>Servicio</th><th style='border:1px solid #ddd;padding:8px;'>Proveedor(es)</th><th style='border:1px solid #ddd;padding:8px;'>Receptor(es)</th></tr>"""
                            for _, row in rows.iterrows():
                                srv = row[c["servicios"]] or "—"
                                prv = row[c["proveedores"]] or "—"
                                rec = row[c["receptor"]] or "—"
                                table_html += f"<tr><td style='border:1px solid #ddd;padding:8px;'>{srv}</td><td style='border:1px solid #ddd;padding:8px;'>{prv}</td><td style='border:1px solid #ddd;padding:8px;'>{rec}</td></tr>"
                            table_html += "</table>"
                            st.markdown(table_html, unsafe_allow_html=True)
                        else:
                            st.markdown("_Sin servicios, proveedores ni receptores registrados_")


        # ========== Descargas ==========
        st.markdown("---")
        st.markdown("### 📥 Formato de descarga:")
        formato = st.radio("Selecciona el formato:", ["Excel", "PDF"], index=0, horizontal=False, label_visibility="collapsed")

        if formato == "Excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                resultados.to_excel(writer, index=False, sheet_name='Datos')
            output.seek(0)
            st.download_button(
                "📄 Descargar archivo Excel",
                data=output.getvalue(),
                file_name='politica_nacional.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                key="descargar_excel"
            )
        else:
            pdf = FPDF()
            pdf.add_page()
            # Intentar insertar los logos si existen
            try:
                pdf.image("pages/assets/logopcm_fpdf.jpg", x=15, y=8, w=75)
                pdf.image("pages/assets/ceplan_fpdf.jpg", x=160, y=8, w=35)
            except Exception as e:
                st.warning(f"⚠️ No se pudieron cargar los logos en el PDF: {e}")

            pdf.set_font("Arial", style='B', size=12)
            pdf.ln(30)
            pdf.multi_cell(0, 10, f"Política Nacional: {nombre_politica}")
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, f"Número: {_si(resultados.iloc[0].get(c['nro']))}")
            pdf.multi_cell(0, 10, f"Estado: {_si(resultados.iloc[0].get(c['estado']))}")
            pdf.multi_cell(0, 10, f"Periodo: {_si(resultados.iloc[0].get(c['periodo']))}")
            pdf.multi_cell(0, 10, f"Tipo: {tipo}")
            pdf.multi_cell(0, 10, f"Conductor: {_si(resultados.iloc[0].get(c['conductor']))}")
            pdf.multi_cell(0, 10, f"Intervinientes: {_si(resultados.iloc[0].get(c['intervinientes']))}")
            pdf.multi_cell(0, 10, f"Problema Público: {_si(resultados.iloc[0].get(c['problema_publico']))}")
            pdf.multi_cell(0, 10, f"Marco Legal: {_si(resultados.iloc[0].get(c['marco_legal']))}")
            pdf.multi_cell(0, 10, f"Informe Técnico CEPLAN: {_si(resultados.iloc[0].get(c['informe']))}")
            pdf.multi_cell(0, 10, f"Decreto Supremo de Aprobación: {_si(resultados.iloc[0].get(c['ds']))}")

            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                "📄 Descargar archivo PDF",
                data=pdf_output,
                file_name='politica_nacional.pdf',
                mime='application/pdf',
                key="descargar_pdf"
            )






# Pie institucional
st.markdown("<center><small>App elaborada por la Dirección Nacional de Coordinación y Planeamiento (DNCP) - CEPLAN</small></center>", unsafe_allow_html=True)







 
