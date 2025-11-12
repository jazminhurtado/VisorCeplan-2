# -*- coding: utf-8 -*-
"""
pages/00_Dashboard.py – Visor CEPLAN (Gerencial)

• PDC: Prioridad de fuentes para KPIs/Gráfico:
    1) Banderas por fila (col '¿SI tienen PDC?'): cuenta filas (TOTAL) y 'SI' (CON)
    2) Tabla de RESUMEN (Nivel | Total Pliegos | Entidades Con PDC | Entidades Sin PDC | Brecha)
    3) A/H (A=Total, H=Con PDC) numéricas
    4) Registros (respaldo)

• PEI/POI: igual que antes (universo por Q="S" + ACTIVO).
"""

# ---------------------- Imports ----------------------
import re
from typing import Optional, List
from urllib.parse import urlparse, parse_qs

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import unicodedata

# ---------------------- Config ----------------------
#st.set_page_config(page_title="Dashboard – CEPLAN (Gerencial)", page_icon=":bar_chart:", layout="wide")
# --------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------
st.set_page_config(
    page_title="Dashboard Detalle",
    page_icon="logo_icon.png",  # Asegúrate que el ícono esté en raíz
    layout="wide"
)

# --------------------------------------
# ESTILOS PERSONALIZADOS COMO INICIO.PY
# --------------------------------------
st.markdown("""
<style>
body, .stApp {
    background-color: #f0f4f8;
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


# Google Sheets
URL_PEI_POI_FILE_EDIT = "https://docs.google.com/spreadsheets/d/1pnoMXaLQpYugbR8dIlY8Vq8uPhX3GjykfXSoZrpbfOQ/edit"
GID_IT_PEI        = "1289302518"   # IT PEI
GID_DATA_UES      = "2130915882"   # Data_UEs
GID_REGISTRO_POI  = "879937350"    # Registro POI

URL_PDC_EDIT      = "https://docs.google.com/spreadsheets/d/1rSDhnTBKjqJfqfi-kxmx699IU375C39e/edit?gid=1778012106#gid=1778012106"
GID_PDC_ESTADO    = "1778012106"   # ESTADO_PDC

# Constantes
PENDING_LABEL = "Pendiente"
NIVEL_ORDER_UE  = ["GOBIERNO NACIONAL","GOBIERNO REGIONAL","MUNICIPALIDAD PROVINCIAL","MUNICIPALIDAD DISTRITAL"]
NIVEL_ORDER_PDC = ["GOBIERNO REGIONAL","GOBIERNO LOCAL"]

YES_SET  = {"S","SI","YES","TRUE","1"}
ACT_SET  = {"ACTIVO","ACTIVE","1","TRUE","SI","S"}
PLACEHOLDER_PAT = r'^\s*(\.\.\.|…|-|—|ND|N/?D|N\.D\.|N\.A\.|NA)?\s*$'

# ---------------------- Utils ----------------------
def _norm_txt(s: str) -> str:
    if s is None: return ""
    s = str(s).strip()
    for a,b in (("Á","A"),("É","E"),("Í","I"),("Ó","O"),("Ú","U"),("Ñ","N"),
                ("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")):
        s = s.replace(a,b)
    return s

def _norm_header(s: str) -> str:
    if s is None: return ""
    s = str(s).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 %]+"," ", s)
    s = re.sub(r"\s+"," ", s).strip()
    return s

def _norm_nivel_strict(v: str) -> str:
    v = _norm_header(v).upper()
    if "REGIONAL" in v: return "GOBIERNO REGIONAL"
    if "LOCAL" in v or "MUNICIPAL" in v: return "GOBIERNO LOCAL"
    return ""

def _norm_nivel_general(x: str) -> str:
    s = _norm_txt(x).upper()
    if "REGIONAL" in s: return "GOBIERNO REGIONAL"
    if "LOCAL" in s or "MUNI" in s: return "GOBIERNO LOCAL"
    if "NACIONAL" in s: return "GOBIERNO NACIONAL"
    if "PROVINC" in s: return "MUNICIPALIDAD PROVINCIAL"
    if "DISTRIT" in s: return "MUNICIPALIDAD DISTRITAL"
    return s

def _norm_key(s: str) -> str:
    s = _norm_txt(s).upper()
    s = re.sub(r"[^A-Z0-9 ]+"," ", s)
    s = re.sub(r"\s+"," ", s).strip()
    return s

def _to_upper_series(s: pd.Series) -> pd.Series:
    return pd.Series(["" if pd.isna(v) else str(v).strip().upper() for v in s])

def replace_placeholders(series: pd.Series, fill_label: Optional[str]=PENDING_LABEL) -> pd.Series:
    s = series.astype("object")
    s = s.replace({PLACEHOLDER_PAT: np.nan}, regex=True)
    if fill_label is not None:
        s = s.fillna(fill_label)
    return s

def _extract_id_gid(url_edit: str):
    try:
        file_id = url_edit.split("/d/")[1].split("/")[0]
    except Exception:
        file_id = ""
    gid = None
    parsed = urlparse(url_edit)
    if parsed.query:
        qs = parse_qs(parsed.query)
        if "gid" in qs: gid = qs["gid"][0]
    if (not gid) and parsed.fragment and "gid=" in parsed.fragment:
        gid = parsed.fragment.split("gid=")[1]
    return file_id, gid

def _edit_to_csv_url(file_edit: str, gid: Optional[str]) -> List[str]:
    file_id, _ = _extract_id_gid(file_edit)
    if file_id and gid:
        return [
            f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}",
            f"https://docs.google.com/spreadsheets/d/{file_id}/pub?gid={gid}&single=true&output=csv",
            f"https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&gid={gid}",
        ]
    if file_id:
        return [
            f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv",
            f"https://docs.google.com/spreadsheets/d/{file_id}/pub?output=csv",
        ]
    return [file_edit]

@st.cache_data(show_spinner="Leyendo Google Sheets…", ttl=600)
def _read_gs_csv_any(file_edit: str, gid: Optional[str], header_keywords=()) -> pd.DataFrame:
    if not header_keywords:
        header_keywords = ("id","unidad","ue","pliego","nivel","tipo_gobierno","estado","vigencia","activo","total","pdc","si","con")
    candidatas = _edit_to_csv_url(file_edit, gid)
    errores = []
    for url_csv in candidatas:
        try:
            raw = pd.read_csv(url_csv, header=None, dtype=str, keep_default_na=False)
            def clean(v):
                return re.sub(r'\s+','_',v.strip().lower()) if isinstance(v,str) else ""
            best_i, best_score = 0, -1
            keys = set(k.lower() for k in header_keywords)
            for i in range(min(10, len(raw))):
                row = [clean(x) for x in raw.iloc[i].tolist()]
                nonempty = sum(bool(x) for x in row)
                hits = sum(1 for x in row if x in keys or any(k in x for k in keys))
                score = hits*10 + nonempty
                if score > best_score:
                    best_i, best_score = i, score
            header = [clean(x) for x in raw.iloc[best_i].tolist()]
            df = raw.iloc[best_i+1:].copy()
            df.columns = header
            df = df.loc[:, [c for c in df.columns if c and c != 'nan']]
            if len(df.columns) == 0:
                raise ValueError("CSV leído, pero sin columnas (verifica hoja correcta y permisos).")
            return df
        except Exception as e:
            errores.append(f"{url_csv} -> {e}")
    st.error("No se pudo leer Google Sheets. Publica la hoja en CSV o comparte como 'Cualquiera con el enlace: lector'.")
    st.code("\n".join(errores))
    st.stop()

def pick(df: pd.DataFrame, *cands) -> Optional[str]:
    for c in cands:
        if c in df.columns: return c
    for cand in cands:
        pref = cand[:7]
        for col in df.columns:
            if col.startswith(pref):
                return col
    return None

# ---------------------- UNIVERSO / POI / PEI ----------------------
def _find_yes_flag_col(df: pd.DataFrame) -> Optional[str]:
    for c in df.columns:
        nm = str(c).lower()
        if any(k in nm for k in ["q", "flag", "incluye", "considerar", "cuenta", "habilitado", "habilitada"]):
            vals = set(_to_upper_series(df[c]).dropna().unique().tolist())
            if len(vals & (YES_SET)) >= 1:
                return c
    best_c, best_ratio = None, 0.0
    for c in df.columns:
        vals = _to_upper_series(df[c])
        total = float(len(vals)) or 1.0
        hits = float(vals.isin(YES_SET | {"N","NO"}).sum())
        ratio = hits/total
        if ratio > 0.6 and ratio > best_ratio:
            best_c, best_ratio = c, ratio
    return best_c

def _find_activo_col(df: pd.DataFrame) -> Optional[str]:
    for c in df.columns:
        if "activo" in str(c).lower() or "estado" in str(c).lower():
            vals = _to_upper_series(df[c])
            if len(set(vals.unique()) & ACT_SET) >= 1:
                return c
    best_c, best_ratio = None, 0.0
    for c in df.columns:
        vals = _to_upper_series(df[c])
        total = float(len(vals)) or 1.0
        hits = float(vals.isin(ACT_SET | {"INACTIVO"}).sum())
        ratio = hits/total
        if ratio > 0.6 and ratio > best_ratio:
            best_c, best_ratio = c, ratio
    return best_c

@st.cache_data(show_spinner="Cargando universo (Data_UEs)…", ttl=600)
def load_universo_ues() -> pd.DataFrame:
    df_raw = _read_gs_csv_any(URL_PEI_POI_FILE_EDIT, GID_DATA_UES,
                              header_keywords=("id","ue","pliego","unidad","nivel","departamento","tipo","activo"))
    c_nom  = pick(df_raw, "unidad_nombre","nombre_ue","entidad","organismo","nombre_pliego","pliego","nombre")
    c_niv  = pick(df_raw, "nivel_gobierno","nivel","ng","tipo_gobierno")
    c_dep  = pick(df_raw, "departamento","region","depa","nombre_departamento")
    c_id   = pick(df_raw, "unidad_id","id","id_ue","codigo_ue","ruc","pliego_id")

    col_yes = _find_yes_flag_col(df_raw)   # Q (S/N)
    col_act = _find_activo_col(df_raw)     # AH (ACTIVO)

    nom = df_raw[c_nom] if c_nom else pd.Series([""]*len(df_raw))
    niv = df_raw[c_niv] if c_niv else pd.Series([""]*len(df_raw))
    dep = df_raw[c_dep] if c_dep else pd.Series([""]*len(df_raw))
    uid = df_raw[c_id].astype(str) if c_id else pd.Series([""]*len(df_raw))

    yes = _to_upper_series(df_raw[col_yes]) if col_yes else pd.Series(["S"]*len(df_raw))
    act = _to_upper_series(df_raw[col_act]) if col_act else pd.Series(["ACTIVO"]*len(df_raw))

    df = pd.DataFrame({
        "unidad_id": uid,
        "unidad_nombre": nom,
        "nivel_gobierno": niv.apply(_norm_nivel_general),
        "departamento": dep.apply(lambda v: _norm_txt(v).upper()),
        "__yes": yes,
        "__act": act,
    })

    df = df[
        df["nivel_gobierno"].isin(NIVEL_ORDER_UE) &
        (df["__yes"].isin({"S","SI"})) &
        (df["__act"].isin({"ACTIVO","ACTIVE"}))
    ].copy()

    df["key_merge"] = np.where(df["unidad_id"].astype(str).str.strip()!="",
                               df["unidad_id"].astype(str),
                               df["unidad_nombre"].astype(str).map(_norm_key))
    return df[["unidad_id","unidad_nombre","nivel_gobierno","departamento","key_merge"]]

@st.cache_data(show_spinner="Cargando Registro POI…", ttl=600)
def load_poi_registro() -> pd.DataFrame:
    df = _read_gs_csv_any(URL_PEI_POI_FILE_EDIT, GID_REGISTRO_POI,
                          header_keywords=("id","unidad","ue","pliego","estado","poi","nombre"))
    c_id  = pick(df, "unidad_id","id","id_ue","codigo_ue","ruc","pliego_id")
    c_est = pick(df, "estado","estado_poi","situacion","etapa","situacion_poi")
    c_nom = pick(df, "unidad_nombre","nombre_unidad","unidad","nombre","pliego")

    uid = df[c_id].astype(str) if c_id else pd.Series([""]*len(df))
    nom = df[c_nom].astype(str) if c_nom else pd.Series([""]*len(df))
    estado_det = replace_placeholders(df[c_est] if c_est else pd.Series([""]*len(df)), fill_label="")
    s = estado_det.astype("object").apply(lambda v: "" if pd.isna(v) else str(v).lower())

    is_aprob = s.apply(lambda v: "aprob" in v)
    is_ajust = s.apply(lambda v: "ajust" in v)
    is_cons  = s.apply(lambda v: "consist" in v)
    is_segu  = s.apply(lambda v: "seguim" in v)
    is_elab  = s.apply(lambda v: "elab" in v)
    is_blank = s.apply(lambda v: v.strip()=="")

    estado_ui = np.select(
        [is_aprob, is_ajust, is_cons, is_segu, is_elab, is_blank],
        ["Aprobado", "Ajustado", "Consistenciado", "En Seguimiento", "En Elaboración", PENDING_LABEL],
        default="En Proceso"
    )
    tiene_poi = (is_aprob | is_ajust | is_cons | is_segu)

    out = pd.DataFrame({
        "unidad_id": uid,
        "unidad_nombre": nom,
        "estado_ui": estado_ui,
        "estado_simple": np.where(tiene_poi, "Emitido",
                                  np.where(is_elab | is_blank, PENDING_LABEL, "En Proceso")),
        "emitido_flag": tiene_poi.astype(int),
    })
    out["key_merge"] = np.where(out["unidad_id"].astype(str).str.strip()!="",
                                out["unidad_id"].astype(str),
                                out["unidad_nombre"].astype(str).map(_norm_key))
    return out

@st.cache_data(show_spinner="Cargando IT PEI…", ttl=600)
def load_it_pei() -> pd.DataFrame:
    df = _read_gs_csv_any(URL_PEI_POI_FILE_EDIT, GID_IT_PEI,
                          header_keywords=("id","unidad","ue","pliego","estado","vigencia","pei"))
    c_id   = pick(df, "unidad_id","id","id_ue","codigo_ue","ruc","pliego_id","codigo")
    cols_by_idx = list(df.columns)
    col_B = cols_by_idx[1] if len(cols_by_idx) > 1 else None
    col_F = cols_by_idx[5] if len(cols_by_idx) > 5 else None
    col_H = cols_by_idx[7] if len(cols_by_idx) > 7 else None

    c_est  = pick(df, "estado","estado_pei","situacion","etapa") or col_H
    c_vig  = pick(df, "vigencia","pei_vigente","esta_vigente","vigente") or col_F
    c_id   = c_id or col_B

    uid = df[c_id].astype(str) if c_id else pd.Series([""]*len(df))
    estado_det = replace_placeholders(df[c_est] if c_est else pd.Series([""]*len(df)), fill_label="")
    vig = replace_placeholders(df[c_vig] if c_vig else pd.Series([""]*len(df)), fill_label="")

    estado_ui = []
    for s in estado_det.astype("object").apply(lambda v: "" if pd.isna(v) else str(v).lower()):
        if not s:
            estado_ui.append(PENDING_LABEL)
        elif any(k in s for k in ["aprob","emit","ajust","public"]):
            estado_ui.append("Emitido")
        else:
            estado_ui.append("En Proceso")
    estado_ui = pd.Series(estado_ui)

    out = pd.DataFrame({
        "unidad_id": uid,
        "estado": estado_ui,
        "vigencia": vig.astype("object").apply(lambda v: "" if pd.isna(v) else str(v).replace("sí","Si").replace("si","Si").replace("no","No").title()),
    })
    out["key_merge"] = out["unidad_id"].astype(str)
    out["emitido_flag"] = (out["estado"]=="Emitido").astype(int)
    out["tiene_flag"]   = (out["estado"]!=PENDING_LABEL).astype(int)
    return out

def build_pei(universo: pd.DataFrame) -> pd.DataFrame:
    pei = load_it_pei()
    df = universo.merge(pei[["key_merge","estado","vigencia","emitido_flag","tiene_flag"]],
                        on="key_merge", how="left")
    df["estado"]       = df["estado"].fillna(PENDING_LABEL)
    df["vigencia"]     = df["vigencia"].fillna("")
    df["emitido_flag"] = df["emitido_flag"].fillna(0).astype(int)
    df["tiene_flag"]   = df["tiene_flag"].fillna(0).astype(int)
    df["plan"]         = "PEI"
    return df

def build_poi(universo: pd.DataFrame) -> pd.DataFrame:
    poi  = load_poi_registro()
    df = universo.merge(poi[["key_merge","estado_ui","estado_simple","emitido_flag"]],
                        on="key_merge", how="left")
    df["estado_ui"]     = df["estado_ui"].fillna(PENDING_LABEL)
    df["estado_simple"] = df["estado_simple"].fillna(PENDING_LABEL)
    df["emitido_flag"]  = df["emitido_flag"].fillna(0).astype(int)
    df["tiene_flag"]    = df["emitido_flag"]
    df["plan"]          = "POI"
    return df

# ---------------------- PDC (Banderas → Resumen → A/H → Registros) ----------------------
def _strong_yes(series: pd.Series) -> pd.Series:
    s = series.astype("object").fillna("").astype(str)
    s = s.str.strip()
    s = s.str.normalize("NFKD").str.encode("ascii","ignore").str.decode("utf-8","ignore")
    s = s.str.upper().str.replace(r"\s+","", regex=True)
    yes_values = {"SI","S","YES","TRUE","1"}
    return s.isin(yes_values)

@st.cache_data(show_spinner="Cargando PDC (banderas SI)…", ttl=600)
def load_pdc_flags() -> Optional[pd.DataFrame]:
    df = _read_gs_csv_any(
        URL_PDC_EDIT, GID_PDC_ESTADO,
        header_keywords=("nivel de gobierno","tipo_gobierno","nivel","si","pdc","tienen","¿si")
    )
    c_niv = pick(df, "nivel de gobierno","tipo_gobierno","nivel","ng")
    if not c_niv:
        return None
    nivel = df[c_niv].apply(_norm_nivel_general)

    c_yes = None
    for c in df.columns:
        h = _norm_header(c)
        if ("pdc" in h or "plan" in h) and ("si" in h or "tienen" in h):
            c_yes = c; break
    if c_yes is None and len(df.columns) >= 8:
        c_yes = list(df.columns)[7]  # Fallback: H

    if c_yes is None:
        return None

    si_mask = _strong_yes(df[c_yes])
    sub = pd.DataFrame({"nivel_gobierno": nivel, "yes": si_mask.astype(int)})
    sub = sub[sub["nivel_gobierno"].isin(NIVEL_ORDER_PDC)]
    sub = sub[sub["nivel_gobierno"] != ""]
    if sub.empty:
        return None

    agg = (sub.groupby("nivel_gobierno", as_index=False)
               .agg(total_entidades=("nivel_gobierno","size"),
                    con_pdc=("yes","sum")))
    agg["total_entidades"] = agg["total_entidades"].astype(int)
    agg["con_pdc"] = agg["con_pdc"].astype(int)
    return agg

@st.cache_data(show_spinner="Cargando PDC (RESUMEN)…", ttl=600)
def load_pdc_resumen() -> Optional[pd.DataFrame]:
    df = _read_gs_csv_any(
        URL_PDC_EDIT, GID_PDC_ESTADO,
        header_keywords=("nivel de gobierno","total pliegos","entidades con pdc","entidades sin pdc","brecha")
    )
    cols = list(df.columns)
    c_niv = c_total = c_con = None
    for c in cols:
        h = _norm_header(c)
        if c_niv is None and ("nivel" in h and "gobierno" in h): c_niv = c
        if c_total is None and ("total" in h and ("pliego" in h or "entidad" in h)): c_total = c
        if c_con   is None and ("con" in h and "pdc" in h): c_con = c
    if not (c_niv and c_total and c_con):
        return None

    nivel = df[c_niv].apply(_norm_nivel_strict)
    total = pd.to_numeric(df[c_total].astype(str).str.replace(",",""), errors="coerce")
    con   = pd.to_numeric(df[c_con].astype(str).str.replace(",",""), errors="coerce")
    sub = pd.DataFrame({"nivel_gobierno": nivel, "total_entidades": total, "con_pdc": con})
    sub = sub[sub["nivel_gobierno"].isin(NIVEL_ORDER_PDC)].dropna(subset=["total_entidades","con_pdc"])
    if sub.empty: return None

    agg = (sub.groupby("nivel_gobierno", as_index=False)
              .agg(total_entidades=("total_entidades","sum"),
                   con_pdc=("con_pdc","sum")))
    agg["total_entidades"] = agg["total_entidades"].round().astype(int)
    agg["con_pdc"] = agg["con_pdc"].round().astype(int)
    return agg

@st.cache_data(show_spinner="Cargando PDC (A/H)…", ttl=600)
def load_pdc_agregado_AH() -> Optional[pd.DataFrame]:
    df = _read_gs_csv_any(
        URL_PDC_EDIT, GID_PDC_ESTADO,
        header_keywords=("tipo de gobierno","tipo_gobierno","nivel","total","entidades","pdc","si","tienen")
    )
    cols = list(df.columns)
    if len(cols) < 8: return None
    col_A, col_H = cols[0], cols[7]
    c_niv = None
    for c in cols:
        h = _norm_header(c)
        if any(k in h for k in ["tipo de gobierno","tipo_gobierno","nivel","nivel de gobierno"]):
            c_niv = c; break
    if c_niv is None: return None

    nivel = df[c_niv].apply(_norm_nivel_strict)
    total = pd.to_numeric(df[col_A].astype(str).str.replace(",",""), errors="coerce")
    con   = pd.to_numeric(df[col_H].astype(str).str.replace(",",""), errors="coerce")

    sub = pd.DataFrame({"nivel_gobierno": nivel, "total_entidades": total, "con_pdc": con})
    sub = sub[sub["nivel_gobierno"].isin(NIVEL_ORDER_PDC)].dropna(subset=["total_entidades","con_pdc"])
    if sub.empty: return None

    agg = (sub.groupby("nivel_gobierno", as_index=False)
              .agg(total_entidades=("total_entidades","sum"),
                   con_pdc=("con_pdc","sum")))
    agg["total_entidades"] = agg["total_entidades"].round().astype(int)
    agg["con_pdc"] = agg["con_pdc"].round().astype(int)
    return agg

@st.cache_data(show_spinner="Cargando PDC (registros)…", ttl=600)
def load_pdc_registros() -> pd.DataFrame:
    df = _read_gs_csv_any(URL_PDC_EDIT, GID_PDC_ESTADO,
                          header_keywords=("id","pliego","tipo_gobierno","nivel","estado","vigencia"))
    c_niv = pick(df, "tipo_gobierno","nivel","ng")
    c_est = pick(df, "estado","estado_pdc")
    c_vig = pick(df, "vigencia","pdc_esta_vig")
    c_id  = pick(df, "id","unidad_id","pliego_id","ruc")

    nivel = df[c_niv] if c_niv else pd.Series([""]*len(df))
    est   = df[c_est] if c_est else pd.Series([""]*len(df))
    vig   = df[c_vig] if c_vig else pd.Series([""]*len(df))
    uid   = (df[c_id].astype(str) if c_id else pd.Series([str(i) for i in range(len(df))]))

    est = replace_placeholders(est, fill_label=PENDING_LABEL)
    vig = replace_placeholders(vig, fill_label="")

    est_ui = []
    for s in est.astype("object").apply(lambda v: "" if pd.isna(v) else str(v).lower()):
        if s == "" or s == PENDING_LABEL.lower():
            est_ui.append(PENDING_LABEL)
        elif any(k in s for k in ["emit","aprob","public"]):
            est_ui.append("Emitido")
        else:
            est_ui.append("En Proceso")
    est_ui = pd.Series(est_ui)

    out = pd.DataFrame({
        "unidad_id": uid,
        "nivel_gobierno": nivel.astype("object").apply(lambda v: _norm_nivel_general(v)),
        "estado": est_ui,
        "vigencia": vig.astype("object").apply(lambda v: "" if pd.isna(v) else str(v).replace("sí","Si").replace("si","Si").replace("no","No").title()),
    })
    out["emitido_flag"] = (out["estado"]=="Emitido").astype(int)
    out["tiene_flag"]   = (out["estado"]!=PENDING_LABEL).astype(int)
    return out

def pdc_compute_kpis(sel_levels: List[str]):
    """
    Prioridad:
      1) Banderas por fila (col H = 'SI') -> cuenta filas (TOTAL) y 'SI' (CON)
      2) Tabla RESUMEN (si existe)
      3) A/H (numéricas)
      4) Registros (respaldo)
    Devuelve dos dicts: totals_global, totals_filt (cada uno trae .agg_df)
    """
    # 1) Banderas SI/NO por fila
    flags = load_pdc_flags()
    if flags is not None and not flags.empty:
        g_total = int(flags["total_entidades"].sum())
        g_con   = int(flags["con_pdc"].sum())
        g_sin   = max(g_total - g_con, 0)
        g_br    = (g_sin / g_total * 100.0) if g_total else 0.0
        totals_global = dict(total=g_total, con=g_con, sin=g_sin, brecha=g_br, agg_df=flags)

        fdf = flags[flags["nivel_gobierno"].isin(sel_levels)].copy() if sel_levels else flags.copy()
        f_total = int(fdf["total_entidades"].sum())
        f_con   = int(fdf["con_pdc"].sum())
        f_sin   = max(f_total - f_con, 0)
        f_br    = (f_sin / f_total * 100.0) if f_total else 0.0
        totals_filt = dict(total=f_total, con=f_con, sin=f_sin, brecha=f_br, agg_df=fdf)
        return totals_global, totals_filt

    # 2) RESUMEN
    resumen = load_pdc_resumen()
    if resumen is not None and not resumen.empty:
        g_total = int(resumen["total_entidades"].sum())
        g_con   = int(resumen["con_pdc"].sum())
        g_sin   = max(g_total - g_con, 0)
        g_br    = (g_sin / g_total * 100.0) if g_total else 0.0
        totals_global = dict(total=g_total, con=g_con, sin=g_sin, brecha=g_br, agg_df=resumen)

        fdf = resumen[resumen["nivel_gobierno"].isin(sel_levels)].copy() if sel_levels else resumen.copy()
        f_total = int(fdf["total_entidades"].sum())
        f_con   = int(fdf["con_pdc"].sum())
        f_sin   = max(f_total - f_con, 0)
        f_br    = (f_sin / f_total * 100.0) if f_total else 0.0
        totals_filt = dict(total=f_total, con=f_con, sin=f_sin, brecha=f_br, agg_df=fdf)
        return totals_global, totals_filt

    # 3) A/H
    agg_ah = load_pdc_agregado_AH()
    if agg_ah is not None and not agg_ah.empty:
        g_total = int(agg_ah["total_entidades"].sum())
        g_con   = int(agg_ah["con_pdc"].sum())
        g_sin   = max(g_total - g_con, 0)
        g_br    = (g_sin / g_total * 100.0) if g_total else 0.0
        totals_global = dict(total=g_total, con=g_con, sin=g_sin, brecha=g_br, agg_df=agg_ah)

        fdf = agg_ah[agg_ah["nivel_gobierno"].isin(sel_levels)].copy() if sel_levels else agg_ah.copy()
        f_total = int(fdf["total_entidades"].sum())
        f_con   = int(fdf["con_pdc"].sum())
        f_sin   = max(f_total - f_con, 0)
        f_br    = (f_sin / f_total * 100.0) if f_total else 0.0
        totals_filt = dict(total=f_total, con=f_con, sin=f_sin, brecha=f_br, agg_df=fdf)
        return totals_global, totals_filt

    # 4) Registros
    regs = load_pdc_registros()
    g_total = int(len(regs))
    g_con   = int(regs["tiene_flag"].sum())
    g_sin   = max(g_total - g_con, 0)
    g_br    = (g_sin / g_total * 100.0) if g_total else 0.0
    agg = (regs.groupby("nivel_gobierno", as_index=False)
             .agg(total_entidades=("nivel_gobierno","size"),
                  con_pdc=("tiene_flag","sum")))
    totals_global = dict(total=g_total, con=g_con, sin=g_sin, brecha=g_br, agg_df=agg)

    regs_f = regs[regs["nivel_gobierno"].isin(sel_levels)] if sel_levels else regs
    f_total = int(len(regs_f))
    f_con   = int(regs_f["tiene_flag"].sum())
    f_sin   = max(f_total - f_con, 0)
    f_br    = (f_sin / f_total * 100.0) if f_total else 0.0
    fagg = (regs_f.groupby("nivel_gobierno", as_index=False)
              .agg(total_entidades=("nivel_gobierno","size"),
                   con_pdc=("tiene_flag","sum")))
    totals_filt = dict(total=f_total, con=f_con, sin=f_sin, brecha=f_br, agg_df=fagg)
    return totals_global, totals_filt

# ---------------------- UI principal ----------------------
st.markdown("## Dashboard General – Estado de Instrumentos (PEI – POI – PDC)")

if st.button("Refrescar (releer Google Sheets)"):
    try: st.cache_data.clear()
    except: pass
    st.rerun()

st.sidebar.markdown("### Planes")
plan_sel = st.sidebar.radio("Selecciona el Plan", ["PEI","POI","PDC"], index=2, horizontal=True)

# Carga base (PEI/POI)
universo = load_universo_ues()
pei = build_pei(universo)
poi = build_poi(universo)

# ---------------------- Filtros ----------------------
nivel_opts_full = NIVEL_ORDER_PDC if plan_sel == "PDC" else NIVEL_ORDER_UE
sel_nivel = st.sidebar.multiselect("Nivel de Gobierno", nivel_opts_full, default=nivel_opts_full)

# NUEVO: filtro por ¿Tiene PDC? (sólo PDC)
if plan_sel == "PDC":
    pdc_cond_map = {"Con PDC": "Con PDC", "Sin PDC": "Sin PDC"}
    sel_pdc_cond = st.sidebar.multiselect(
        "¿Tiene PDC?",
        options=list(pdc_cond_map.keys()),
        default=list(pdc_cond_map.keys())
    )
else:
    sel_pdc_cond = []

# ---------------------- Vista ----------------------
if plan_sel == "PDC":
    totals_global, totals_filt = pdc_compute_kpis(sel_nivel)

    aplicar_filtro_kpi = st.toggle(
        "Aplicar filtros a cabecera",
        value=True,
        help="Si está activado, la cabecera usa los niveles seleccionados."
    )
    sel = totals_filt if aplicar_filtro_kpi else totals_global

    # KPIs (respetando opcionalmente el filtro ¿Tiene PDC?)
    _total = int(sel["total"])
    _con   = int(sel["con"])
    _sin   = int(sel["sin"])

    picked = set(sel_pdc_cond)
    if picked == {"Con PDC"}:
        _total, _sin = _con, 0
    elif picked == {"Sin PDC"}:
        _total, _con = _sin, 0

    _brecha = (_sin / _total * 100.0) if _total else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Entidades", f"{_total:,}")
    c2.metric("Entidades con PDC", f"{_con:,}")
    c3.metric("Entidades sin PDC", f"{_sin:,}")
    c4.metric("Brecha %", f"{_brecha:.1f}%")

    # ----- Gráfico por nivel (MISMA FUENTE QUE KPI) -----
    st.markdown("#### Cobertura por Nivel de Gobierno (Con PDC vs Sin PDC)")
    niveles = NIVEL_ORDER_PDC
    base = pd.DataFrame({"nivel_gobierno": niveles})
    m = base.merge(sel["agg_df"], on="nivel_gobierno", how="left").fillna(0)
    m["total_entidades"] = m["total_entidades"].astype(int)
    m["con_pdc"]         = m["con_pdc"].astype(int)
    m["sin_pdc"]         = (m["total_entidades"] - m["con_pdc"]).clip(lower=0).astype(int)

    cov_long = pd.DataFrame({
        "nivel_gobierno": pd.concat([m["nivel_gobierno"], m["nivel_gobierno"]], ignore_index=True),
        "condicion":      ["Con PDC"]*len(m) + ["Sin PDC"]*len(m),
        "n":              pd.concat([m["con_pdc"], m["sin_pdc"]], ignore_index=True).astype(int)
    })

    # Filtrar por ¿Tiene PDC? para gráfico
    if picked:
        cov_long = cov_long[cov_long["condicion"].isin(picked)]

    fig = px.bar(
        cov_long, x="nivel_gobierno", y="n", color="condicion",
        barmode="stack", text_auto=True,
        category_orders={"nivel_gobierno": niveles}
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis_title="", yaxis_title="Entidades", legend_title="")
    st.plotly_chart(fig, use_container_width=True)

    # ----- Tabla -----
    st.markdown("#### Resumen por nivel")
    tabla = m.copy()
    if picked == {"Con PDC"}:
        tabla["sin_pdc"] = 0
        tabla["total_entidades"] = tabla["con_pdc"]
    elif picked == {"Sin PDC"}:
        tabla["con_pdc"] = 0
        tabla["total_entidades"] = tabla["sin_pdc"]

    st.dataframe(
        tabla[["nivel_gobierno","total_entidades","con_pdc","sin_pdc"]],
        use_container_width=True
    )

else:
    # ---- PEI/POI ----
    dfp = poi if plan_sel == "POI" else pei
    dfp = dfp[dfp["nivel_gobierno"].isin(sel_nivel)] if sel_nivel else dfp
    total = int(len(universo[universo["nivel_gobierno"].isin(sel_nivel)])) if sel_nivel else int(len(universo))
    emitidos = int(dfp["tiene_flag"].fillna(0).astype(int).sum())
    pendientes = max(total - emitidos, 0)
    avance = (emitidos/total*100.0) if total else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Emitidos", f"{emitidos:,}")
    c2.metric("Pendientes", f"{pendientes:,}")
    c3.metric("Total Entidades", f"{total:,}")
    c4.metric("% Avance", f"{avance:.1f}%")

    st.markdown("#### Cobertura por Nivel de Gobierno (Emitido vs Pendiente)")
    niveles = NIVEL_ORDER_UE
    dfp = dfp[dfp["nivel_gobierno"].isin(niveles)]
    universo_n = (universo[universo["nivel_gobierno"].isin(niveles)]
                  .groupby("nivel_gobierno").size().rename("total").reset_index())
    con_plan = (dfp.groupby("nivel_gobierno")["tiene_flag"].sum()
                .rename("emitidos").reset_index())
    m = (pd.DataFrame({"nivel_gobierno": niveles})
         .merge(universo_n, on="nivel_gobierno", how="left")
         .merge(con_plan, on="nivel_gobierno", how="left")
         .fillna(0))
    m["pendientes"] = (m["total"].astype(int) - m["emitidos"].astype(int)).clip(lower=0)
    cov_long = pd.DataFrame({
        "nivel_gobierno": pd.concat([m["nivel_gobierno"], m["nivel_gobierno"]], ignore_index=True),
        "estado_simple":  ["Emitido"]*len(m) + ["Pendiente"]*len(m),
        "n":              pd.concat([m["emitidos"], m["pendientes"]], ignore_index=True).astype(int)
    })
    fig = px.bar(cov_long, x="nivel_gobierno", y="n", color="estado_simple",
                 barmode="stack", text_auto=True, category_orders={"nivel_gobierno": niveles})
    fig.update_layout(height=380, margin=dict(l=10,r=10,t=10,b=10),
                      xaxis_title="", yaxis_title="Entidades", legend_title="")
    st.plotly_chart(fig, use_container_width=True)
