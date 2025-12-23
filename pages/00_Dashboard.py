
import streamlit as st
import plotly.express as px
import pandas as pd
import json
from pathlib import Path

@st.cache_data(ttl=3600)
def load_geojson():
    for path in [Path("pages/peru_departa.geojson"), Path("peru_departa.geojson")]:
        if path.exists():
            gj = json.loads(path.read_text(encoding="utf-8"))
            for ft in gj["features"]:
                name = str(ft["properties"].get("NOMBDEP") or ft["properties"].get("name"))
                ft["properties"]["dep_key"] = name.strip().upper()
            return gj
    return None

@st.cache_data(ttl=3600)
def load_resumen_departamental():
    departamentos = ["AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA",
                     "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN", "LA LIBERTAD",
                     "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO",
                     "PIURA", "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"]
    data = {
        "departamento": departamentos,
        "formulados": [60, 80, 45, 75, 30, 50, 85, 40, 55, 70, 90, 100, 35, 65, 95, 55, 60, 45, 70, 80, 90, 50, 60, 70, 80, 90],
        "pendientes": [40, 20, 55, 25, 70, 50, 15, 60, 45, 30, 10, 0, 65, 35, 5, 45, 40, 55, 30, 20, 10, 50, 40, 30, 20, 10]
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
