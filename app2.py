import os
import io
import re
import unicodedata
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(
    page_title="Panel Ejecutivo de Desempeño de Red y Mercado",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# RUTAS Y CONFIGURACION
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AREA_NAME = "GERENCIA R4 PREPAGO"
DASHBOARD_TITLE = "Panel Ejecutivo de Desempeño de Red y Mercado"
DATA_FILE_CANDIDATES = [
    os.path.join(BASE_DIR, "RSRP_COMPLETO.csv"),
    os.path.join(BASE_DIR, "RSRP_COMPLETO(1).csv"),
    os.path.join(BASE_DIR, "RSRP_COMPLETO(2).csv"),
]
TERRITORIAL_FILE_CANDIDATES = [
    os.path.join(BASE_DIR, "RUTAS Y CODIGO POSTAL R4.xlsx"),
    os.path.join(BASE_DIR, "RUTAS Y CODIGO POSTAL R4(1).xlsx"),
    os.path.join(BASE_DIR, "RUTAS Y CODIGO POSTAL R4(2).xlsx"),
]
TERRITORIAL_STANDARD_COLS = ["LOCALIDAD", "BARRIO", "RUTA", "CIRCUITO"]
BUSINESS_EXCLUDED_CP = {"112011", "111981", "112041", "251201", "251628"}

OPERATOR_COLORS = {
    "Claro": "#E10600",
    "Tigo": "#1D4ED8",
    "Movistar Colombia": "#06B6D4",
    "ETB": "#8B5CF6",
    "WOM Colombia": "#A855F7",
    "Avantel": "#F59E0B",
}
QUALITY_COLORS = {
    "Excelente": "#22C55E",
    "Buena": "#84CC16",
    "Aceptable": "#F59E0B",
    "Crítica": "#EF4444",
    "Sin medición": "#64748B",
}
OPERATOR_ALIASES = {
    "Claro": ["CLARO"],
    "Tigo": ["TIGO"],
    "Movistar Colombia": ["MOVISTAR COLOMBIA", "MOVISTAR"],
    "ETB": ["ETB"],
    "WOM Colombia": ["WOM COLOMBIA", "WOM"],
    "Avantel": ["AVANTEL"],
}

# =========================================================
# ESTILOS
# =========================================================
st.markdown(
    """
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #07101d !important;
    color: #F8FAFC !important;
}
* { box-sizing: border-box; }
p, span, label, div, h1, h2, h3, h4, h5, h6 { color: #F8FAFC; }
body::before {
    content: "";
    position: fixed;
    width: 760px;
    height: 760px;
    top: -180px;
    left: -120px;
    background: radial-gradient(circle, rgba(225,6,0,0.20) 0%, transparent 68%);
    filter: blur(135px);
    z-index: 0;
    pointer-events: none;
}
body::after {
    content: "";
    position: fixed;
    width: 680px;
    height: 680px;
    bottom: -170px;
    right: -120px;
    background: radial-gradient(circle, rgba(56,189,248,0.12) 0%, transparent 70%);
    filter: blur(150px);
    z-index: 0;
    pointer-events: none;
}
.block-container {
    position: relative;
    z-index: 2;
    max-width: 1560px;
    padding-top: 1.25rem !important;
    padding-bottom: 3rem !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(11,19,35,0.98) 0%, rgba(8,16,29,0.98) 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] * { color: #E5E7EB !important; }
.header-shell, .kpi-strip, .section-card, .card, .insight-card, .territory-card, .alert-card, .rule-card {
    background: linear-gradient(180deg, rgba(17,24,39,0.96) 0%, rgba(15,23,42,0.96) 100%) !important;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 12px 28px rgba(0,0,0,0.18);
}
.header-shell {
    border-radius: 24px;
    padding: 20px 24px;
    margin-bottom: 18px;
}
.kpi-strip {
    border-radius: 22px;
    padding: 14px 16px;
    margin-bottom: 18px;
}
.section-card {
    border-radius: 22px;
    padding: 22px 22px 18px 22px;
    margin-bottom: 20px;
}
.card {
    border-radius: 18px;
    padding: 18px;
    min-height: 148px;
    margin-bottom: 14px;
}
.insight-card, .territory-card, .alert-card, .rule-card {
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
}
.section-title { font-size: 1.02rem; font-weight: 800; margin-bottom: 0.30rem; }
.section-subtitle { font-size: 0.84rem; color: #CBD5E1 !important; margin-bottom: 0.95rem; line-height: 1.5; }
.kpi-label { font-size: 0.79rem; color: #CBD5E1 !important; margin-bottom: 0.3rem; font-weight: 700; }
.kpi-value { font-size: 1.62rem; font-weight: 800; line-height: 1.08; }
.kpi-sub { font-size: 0.79rem; color: #94A3B8 !important; margin-top: 0.45rem; line-height: 1.45; }
.metric-operator { font-size: 1.08rem; font-weight: 800; line-height: 1.2; }
.note { font-size: 0.82rem; color: #CBD5E1 !important; line-height: 1.6; }
.insight-title { font-size: 0.80rem; font-weight: 800; color: #94A3B8 !important; margin-bottom: 0.45rem; text-transform: uppercase; }
.insight-body { font-size: 0.91rem; color: #F8FAFC !important; line-height: 1.56; }
.territory-label { font-size: 0.79rem; text-transform: uppercase; color: #94A3B8; font-weight: 700; margin-bottom: 6px; }
.territory-value { font-size: 1.42rem; font-weight: 800; line-height: 1.12; margin-top: 4px; margin-bottom: 8px; }
.territory-sub { font-size: 0.86rem; line-height: 1.52; color: #CBD5E1; }
.operator-box { background: rgba(17,24,39,0.90); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 10px 12px; margin-bottom: 8px; }
.operator-chip { display: inline-block; padding: 6px 10px; border-radius: 999px; margin-right: 6px; margin-bottom: 6px; font-size: 0.76rem; font-weight: 700; color: white; }
.badge-good, .badge-warn, .badge-bad, .badge-info {
    display: inline-block; border-radius: 999px; padding: 6px 11px; font-size: 0.78rem; font-weight: 800; margin-bottom: 12px;
}
.badge-good { background: rgba(34,197,94,0.16); color: #86EFAC; border: 1px solid rgba(34,197,94,0.35); }
.badge-warn { background: rgba(245,158,11,0.16); color: #FCD34D; border: 1px solid rgba(245,158,11,0.35); }
.badge-bad { background: rgba(239,68,68,0.16); color: #FCA5A5; border: 1px solid rgba(239,68,68,0.35); }
.badge-info { background: rgba(56,189,248,0.16); color: #7DD3FC; border: 1px solid rgba(56,189,248,0.35); }
button[data-baseweb="tab"] {
    background: rgba(17,24,39,0.96) !important;
    border-radius: 12px !important;
    color: #E5E7EB !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    padding: 10px 16px !important;
}
button[aria-selected="true"][data-baseweb="tab"] {
    background: rgba(30,41,59,0.96) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    color: #FFFFFF !important;
    box-shadow: inset 0 -2px 0 #E10600;
}
div[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
    margin-top: 8px;
}
.small-caption { font-size: 0.76rem; color: #94A3B8 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# FUNCIONES UTILITARIAS
# =========================================================
def normalize_text(value):
    if pd.isna(value):
        return ""
    value = str(value).replace("\ufeff", "").replace('"', "").strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.upper()
    value = re.sub(r"[^A-Z0-9]+", " ", value).strip()
    return value

def clean_columns(cols):
    return [str(c).replace("\ufeff", "").replace('"', "").strip() for c in cols]

def make_unique_columns(columns):
    seen = {}
    result = []
    for col in columns:
        col = str(col).strip()
        if col not in seen:
            seen[col] = 0
            result.append(col)
        else:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
    return result

def find_existing_file(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def find_col_by_aliases(df, aliases):
    if df is None or df.empty:
        return None
    normalized_map = {normalize_text(c): c for c in df.columns}
    for alias in aliases:
        alias_norm = normalize_text(alias)
        if alias_norm in normalized_map:
            return normalized_map[alias_norm]
    for alias in aliases:
        alias_norm = normalize_text(alias)
        for norm_col, real_col in normalized_map.items():
            if alias_norm == norm_col or alias_norm in norm_col:
                return real_col
    return None

def safe_to_str_series(series):
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()

def first_not_null(series):
    s = series.dropna()
    if s.empty:
        return None
    return s.iloc[0]

def fmt_dBm(x):
    return f"{x:.1f} dBm" if pd.notna(x) else "N/D"

def fmt_pct(x):
    return f"{x:.1f}%" if pd.notna(x) else "N/D"

def fmt_var_dBm(x):
    if pd.isna(x):
        return "N/D"
    sign = "+" if x > 0 else ""
    return f"{sign}{x:.1f} dBm"

def fmt_int(x):
    if pd.isna(x):
        return "N/D"
    return f"{int(round(x)):,}".replace(",", ".")

def safe_round_columns(df_in, cols, decimals=1):
    df_out = df_in.copy()
    for col in cols:
        if col in df_out.columns:
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce").round(decimals)
    return df_out

def classify_rsrp(x):
    if pd.isna(x):
        return "Sin medición"
    if x >= -70:
        return "Excelente"
    elif x >= -80:
        return "Buena"
    elif x >= -90:
        return "Aceptable"
    return "Crítica"

def executive_status(value):
    if pd.isna(value):
        return ("Sin dato", "badge-warn")
    if value >= -70:
        return ("Excelente", "badge-good")
    if value >= -80:
        return ("Buena", "badge-good")
    if value >= -90:
        return ("Aceptable", "badge-warn")
    return ("Crítica", "badge-bad")

def variation_status(value):
    if pd.isna(value):
        return ("Sin dato", "badge-warn")
    if value > 0:
        return ("Mejora", "badge-good")
    if value < 0:
        return ("Deterioro", "badge-bad")
    return ("Estable", "badge-info")

def quality_status(value):
    if pd.isna(value):
        return "Sin dato", "#64748B"
    if value >= 70:
        return "Verde", "#22C55E"
    if value >= 40:
        return "Amarillo", "#F59E0B"
    return "Rojo", "#EF4444"

def zone_semaphore(pct_critica, rsrp_mediana):
    if pd.isna(pct_critica) or pd.isna(rsrp_mediana):
        return "Sin dato"
    if pct_critica >= 70 or rsrp_mediana < -90:
        return "Rojo"
    if pct_critica >= 35 or rsrp_mediana < -80:
        return "Amarillo"
    return "Verde"

def compute_operator_score(row):
    med_norm = min(max((row["RSRP_mediana"] + 110) / 40, 0), 1) * 100
    good_norm = row["Buena_o_mejor"]
    weak_penalty = 100 - row["Critica"]
    score = (med_norm * 0.45) + (good_norm * 0.35) + (weak_penalty * 0.20)
    return round(score, 1)

def score_label(score):
    if pd.isna(score):
        return "Sin dato", "#64748B"
    if score >= 75:
        return "Sobresaliente", "#22C55E"
    elif score >= 60:
        return "Competitivo", "#84CC16"
    elif score >= 45:
        return "Vigilancia", "#F59E0B"
    return "Crítico", "#EF4444"

def build_territory_label(row):
    parts = []
    for col in TERRITORIAL_STANDARD_COLS:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            parts.append(str(row[col]))
    return " | ".join(parts)

def add_temporal_fields(df_in):
    df_out = df_in.copy()
    date_col = "Fecha de inicio" if "Fecha de inicio" in df_out.columns else None
    if date_col is None:
        df_out["Periodo_Dia"] = pd.NaT
        df_out["Periodo_Semana"] = pd.NaT
        df_out["Periodo_Mes"] = pd.NaT
        return df_out
    dt = pd.to_datetime(df_out[date_col], errors="coerce")
    df_out["Periodo_Dia"] = dt.dt.floor("D")
    df_out["Periodo_Semana"] = dt.dt.to_period("W-SUN").apply(lambda p: p.start_time if pd.notna(p) else pd.NaT)
    df_out["Periodo_Mes"] = dt.dt.to_period("M").dt.to_timestamp()
    return df_out

def period_columns(nivel_temporal):
    if nivel_temporal == "Mes":
        return "Periodo_Mes", "%b %Y"
    if nivel_temporal == "Semana":
        return "Periodo_Semana", "%d/%m/%Y"
    return "Periodo_Dia", "%d/%m/%Y"

def robust_read_csv(file_path):
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error = None
    for enc in encodings:
        for sep in [";", ","]:
            try:
                df = pd.read_csv(file_path, sep=sep, encoding=enc)
                if df is not None and df.shape[1] > 1:
                    return df, enc, sep
            except Exception as e:
                last_error = e
        try:
            df = pd.read_csv(file_path, sep=None, engine="python", encoding=enc)
            if df is not None and df.shape[1] > 1:
                return df, enc, "auto"
        except Exception as e:
            last_error = e
    raise ValueError(f"No fue posible leer el CSV con los encodings soportados. Detalle: {last_error}")

def robust_read_excel(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                if df is not None and not df.empty and df.shape[1] >= 1:
                    return df, sheet_name
            except Exception:
                continue
        return pd.read_excel(file_path), None
    except Exception:
        return pd.read_excel(file_path), None

# =========================================================
# TERRITORIO
# =========================================================
def load_territorial_data():
    territorial_path = find_existing_file(TERRITORIAL_FILE_CANDIDATES)
    if territorial_path is None:
        return pd.DataFrame(columns=["Codigo_postal"]), {
            "found": False,
            "message": "No se encontró el archivo territorial RUTAS Y CODIGO POSTAL R4.xlsx en la carpeta del proyecto.",
            "available_cols": [],
        }
    try:
        terr_df, _sheet_name = robust_read_excel(territorial_path)
        terr_df.columns = make_unique_columns(clean_columns(terr_df.columns))
        codigo_col = find_col_by_aliases(terr_df, ["COD. POSTAL", "COD POSTAL", "CODIGO POSTAL", "CÓDIGO POSTAL", "CODIGO_POSTAL", "Codigo_postal"])
        localidad_col = find_col_by_aliases(terr_df, ["LOCALIDAD"])
        barrio_col = find_col_by_aliases(terr_df, ["BARRIO"])
        ruta_col = find_col_by_aliases(terr_df, ["RUTA"])
        circuito_col = find_col_by_aliases(terr_df, ["CIRCUITO"])
        rename_map = {}
        if codigo_col: rename_map[codigo_col] = "Codigo_postal"
        if localidad_col: rename_map[localidad_col] = "LOCALIDAD"
        if barrio_col: rename_map[barrio_col] = "BARRIO"
        if ruta_col: rename_map[ruta_col] = "RUTA"
        if circuito_col: rename_map[circuito_col] = "CIRCUITO"
        terr_df = terr_df.rename(columns=rename_map)
        if "Codigo_postal" not in terr_df.columns:
            return pd.DataFrame(columns=["Codigo_postal"]), {
                "found": False,
                "message": "El archivo territorial no contiene una columna reconocible de código postal.",
                "available_cols": [],
            }
        cols_keep = ["Codigo_postal"] + [c for c in TERRITORIAL_STANDARD_COLS if c in terr_df.columns]
        terr_df = terr_df[cols_keep].copy()
        terr_df["Codigo_postal"] = safe_to_str_series(terr_df["Codigo_postal"])
        for col in TERRITORIAL_STANDARD_COLS:
            if col in terr_df.columns:
                terr_df[col] = terr_df[col].astype(str).str.strip()
                terr_df.loc[terr_df[col].isin(["", "nan", "None", "NaN"]), col] = pd.NA
        terr_df = terr_df.dropna(subset=["Codigo_postal"])
        terr_df = terr_df[terr_df["Codigo_postal"] != ""].copy()
        agg_map = {col: first_not_null for col in cols_keep if col != "Codigo_postal"}
        terr_df = terr_df.groupby("Codigo_postal", as_index=False).agg(agg_map)
        return terr_df, {
            "found": True,
            "message": None,
            "available_cols": [c for c in TERRITORIAL_STANDARD_COLS if c in terr_df.columns],
        }
    except Exception as e:
        return pd.DataFrame(columns=["Codigo_postal"]), {
            "found": False,
            "message": f"No fue posible leer el archivo territorial: {e}",
            "available_cols": [],
        }

def safe_merge_territorial(base_df, territorial_df):
    if base_df is None or base_df.empty:
        return base_df.copy()
    if territorial_df is None or territorial_df.empty or "Codigo_postal" not in territorial_df.columns:
        return base_df.copy()
    df_out = base_df.copy()
    if "Codigo_postal" in df_out.columns:
        df_out["Codigo_postal"] = safe_to_str_series(df_out["Codigo_postal"])
    merge_cols = ["Codigo_postal"] + [c for c in TERRITORIAL_STANDARD_COLS if c in territorial_df.columns]
    terr_use = territorial_df[merge_cols].copy()
    overlap_cols = [c for c in merge_cols if c != "Codigo_postal" and c in df_out.columns]
    if overlap_cols:
        df_out = df_out.drop(columns=overlap_cols, errors="ignore")
    df_out = df_out.merge(terr_use, on="Codigo_postal", how="left")
    return df_out.loc[:, ~df_out.columns.duplicated()].copy()

def filter_territorial_scope(territorial_df, localidad_sel=None, barrio_sel=None, ruta_sel=None, circuito_sel=None):
    if territorial_df is None or territorial_df.empty or "Codigo_postal" not in territorial_df.columns:
        return pd.DataFrame(columns=["Codigo_postal"])
    scope = territorial_df.copy()
    if localidad_sel and "LOCALIDAD" in scope.columns:
        scope = scope[scope["LOCALIDAD"].isin(localidad_sel)]
    if barrio_sel and "BARRIO" in scope.columns:
        scope = scope[scope["BARRIO"].isin(barrio_sel)]
    if ruta_sel and "RUTA" in scope.columns:
        scope = scope[scope["RUTA"].isin(ruta_sel)]
    if circuito_sel and "CIRCUITO" in scope.columns:
        scope = scope[scope["CIRCUITO"].isin(circuito_sel)]
    return scope.copy()

def get_dynamic_territorial_options(territorial_df, localidad_sel, barrio_sel, ruta_sel):
    if territorial_df is None or territorial_df.empty:
        return [], [], [], []
    localidad_options = sorted(territorial_df["LOCALIDAD"].dropna().astype(str).str.strip().loc[lambda s: s != ""].unique().tolist()) if "LOCALIDAD" in territorial_df.columns else []
    barrio_scope = filter_territorial_scope(territorial_df, localidad_sel=localidad_sel)
    barrio_options = sorted(barrio_scope["BARRIO"].dropna().astype(str).str.strip().loc[lambda s: s != ""].unique().tolist()) if "BARRIO" in barrio_scope.columns else []
    ruta_scope = filter_territorial_scope(territorial_df, localidad_sel=localidad_sel, barrio_sel=barrio_sel)
    ruta_options = sorted(ruta_scope["RUTA"].dropna().astype(str).str.strip().loc[lambda s: s != ""].unique().tolist()) if "RUTA" in ruta_scope.columns else []
    circuito_scope = filter_territorial_scope(territorial_df, localidad_sel=localidad_sel, barrio_sel=barrio_sel, ruta_sel=ruta_sel)
    circuito_options = sorted(circuito_scope["CIRCUITO"].dropna().astype(str).str.strip().loc[lambda s: s != ""].unique().tolist()) if "CIRCUITO" in circuito_scope.columns else []
    return localidad_options, barrio_options, ruta_options, circuito_options

# =========================================================
# NEGOCIO
# =========================================================
def detect_operator_metric_columns(df, metric_terms, forbidden_terms=None):
    forbidden_terms = forbidden_terms or []
    detected = {}
    for col in df.columns:
        norm_col = normalize_text(col)
        if any(term in norm_col for term in forbidden_terms):
            continue
        if not any(term in norm_col for term in metric_terms):
            continue
        if "RSRP" in norm_col:
            continue
        for operator, aliases in OPERATOR_ALIASES.items():
            if operator in detected:
                continue
            if any(normalize_text(alias) in norm_col for alias in aliases):
                detected[operator] = col
                break
    return detected

def build_business_long(df_source):
    if df_source is None or df_source.empty:
        return pd.DataFrame()
    data = df_source.copy()
    data.columns = make_unique_columns(clean_columns(data.columns))
    cp_col = find_col_by_aliases(data, ["Codigo_postal", "CODIGO POSTAL", "CÓDIGO POSTAL", "COD POSTAL", "COD. POSTAL"])
    fecha_col = find_col_by_aliases(data, ["Fecha de inicio", "FECHA DE INICIO", "Inicio", "Fecha inicio", "FECHA"])
    operador_col = find_col_by_aliases(data, ["Operador", "OPERADOR"])
    mercado_col = find_col_by_aliases(data, ["Cuota mercado", "CUOTA MERCADO", "Mercado", "MERCADO", "Market share", "Participacion mercado"])
    altas_col = find_col_by_aliases(data, ["Altas", "ALTAS", "Captacion", "CAPTACION", "CAPTACIÓN", "Adiciones", "ADICIONES"])
    rename_map = {}
    if cp_col: rename_map[cp_col] = "Codigo_postal"
    if fecha_col: rename_map[fecha_col] = "Fecha de inicio"
    if operador_col: rename_map[operador_col] = "Operador"
    if mercado_col: rename_map[mercado_col] = "Mercado"
    if altas_col: rename_map[altas_col] = "Altas"
    data = data.rename(columns=rename_map)
    if "Codigo_postal" in data.columns:
        data["Codigo_postal"] = safe_to_str_series(data["Codigo_postal"])
    if "Fecha de inicio" in data.columns:
        data["Fecha de inicio"] = pd.to_datetime(data["Fecha de inicio"], dayfirst=True, errors="coerce")
    base_keep = [c for c in ["Codigo_postal", "Fecha de inicio"] + TERRITORIAL_STANDARD_COLS if c in data.columns]

    if "Operador" in data.columns and ("Mercado" in data.columns or "Altas" in data.columns):
        keep_cols = base_keep + ["Operador"] + [c for c in ["Mercado", "Altas"] if c in data.columns]
        business = data[keep_cols].copy()
    else:
        market_terms = [normalize_text(x) for x in ["CUOTA MERCADO", "MERCADO", "MARKET SHARE", "PARTICIPACION"]]
        altas_terms = [normalize_text(x) for x in ["ALTAS", "CAPTACION", "ADICIONES", "ALTA"]]
        market_map = detect_operator_metric_columns(data, market_terms, forbidden_terms=altas_terms)
        altas_map = detect_operator_metric_columns(data, altas_terms, forbidden_terms=market_terms)
        if not market_map and not altas_map:
            return pd.DataFrame()
        market_long = pd.DataFrame()
        altas_long = pd.DataFrame()
        if market_map:
            market_df = pd.concat([data[base_keep].copy(), data[list(market_map.values())].copy()], axis=1)
            market_long = market_df.melt(id_vars=base_keep, value_vars=list(market_map.values()), var_name="col_origen_mercado", value_name="Mercado")
            market_long["Operador"] = market_long["col_origen_mercado"].map({v: k for k, v in market_map.items()})
            market_long = market_long.drop(columns=["col_origen_mercado"])
        if altas_map:
            altas_df = pd.concat([data[base_keep].copy(), data[list(altas_map.values())].copy()], axis=1)
            altas_long = altas_df.melt(id_vars=base_keep, value_vars=list(altas_map.values()), var_name="col_origen_altas", value_name="Altas")
            altas_long["Operador"] = altas_long["col_origen_altas"].map({v: k for k, v in altas_map.items()})
            altas_long = altas_long.drop(columns=["col_origen_altas"])
        join_cols = [c for c in base_keep + ["Operador"] if c in set(market_long.columns).union(set(altas_long.columns))]
        if not market_long.empty and not altas_long.empty:
            business = market_long.merge(altas_long, on=join_cols, how="outer")
        elif not market_long.empty:
            business = market_long.copy()
            business["Altas"] = np.nan
        else:
            business = altas_long.copy()
            business["Mercado"] = np.nan

    if business.empty:
        return business
    if "Operador" not in business.columns:
        return pd.DataFrame()
    business["Operador"] = business["Operador"].astype(str).str.strip()
    business = business[business["Operador"].isin(list(OPERATOR_ALIASES.keys()))].copy()
    if "Mercado" not in business.columns:
        business["Mercado"] = np.nan
    if "Altas" not in business.columns:
        business["Altas"] = np.nan
    business["Mercado"] = pd.to_numeric(business["Mercado"], errors="coerce")
    business["Altas"] = pd.to_numeric(business["Altas"], errors="coerce")
    if "Codigo_postal" in business.columns:
        business["Codigo_postal"] = safe_to_str_series(business["Codigo_postal"])
    if "Fecha de inicio" in business.columns:
        business["Fecha de inicio"] = pd.to_datetime(business["Fecha de inicio"], errors="coerce")
    group_keys = [c for c in ["Fecha de inicio", "Codigo_postal"] if c in business.columns]
    if group_keys and business["Mercado"].notna().any():
        mt = business.groupby(group_keys, dropna=False)["Mercado"].transform("sum")
        business["Cuota_mercado"] = np.where(mt > 0, business["Mercado"] / mt * 100, np.nan)
    else:
        total_m = business["Mercado"].sum(skipna=True)
        business["Cuota_mercado"] = np.where(total_m > 0, business["Mercado"] / total_m * 100, np.nan)
    if group_keys and business["Altas"].notna().any():
        at = business.groupby(group_keys, dropna=False)["Altas"].transform("sum")
        business["Participacion_altas"] = np.where(at > 0, business["Altas"] / at * 100, np.nan)
    else:
        total_a = business["Altas"].sum(skipna=True)
        business["Participacion_altas"] = np.where(total_a > 0, business["Altas"] / total_a * 100, np.nan)
    return business

def compute_business_metrics(business_df, rsrp_df):
    result = {
        "available": False,
        "message": "No se identificaron columnas de mercado o altas en el dataset.",
        "market_operator": pd.DataFrame(),
        "altas_operator": pd.DataFrame(),
        "market_time": pd.DataFrame(),
        "altas_time": pd.DataFrame(),
        "cross_operator": pd.DataFrame(),
        "risk_table": pd.DataFrame(),
        "opportunity_table": pd.DataFrame(),
        "scatter_df": pd.DataFrame(),
        "leader_market": None,
        "leader_altas": None,
        "variation_market": np.nan,
        "variation_altas": np.nan,
    }
    if business_df is None or business_df.empty:
        return result
    business_df = add_temporal_fields(business_df.copy())
    has_market = business_df["Mercado"].notna().any() if "Mercado" in business_df.columns else False
    has_altas = business_df["Altas"].notna().any() if "Altas" in business_df.columns else False
    if not has_market and not has_altas:
        result["message"] = "No se encontraron valores válidos de mercado o altas para el universo filtrado."
        return result
    if has_market:
        m = business_df.groupby("Operador", as_index=False).agg(Mercado_total=("Mercado", "sum"), Cuota_mercado=("Cuota_mercado", "mean"))
        total = m["Mercado_total"].sum()
        m["Cuota_mercado_global"] = np.where(total > 0, m["Mercado_total"] / total * 100, np.nan)
        m = m.sort_values("Cuota_mercado_global", ascending=False).reset_index(drop=True)
        result["market_operator"] = m
        if not m.empty:
            result["leader_market"] = m.iloc[0]
        mt = business_df.dropna(subset=["Periodo_Mes"]).groupby(["Periodo_Mes", "Operador"], as_index=False).agg(Mercado_total=("Mercado", "sum"))
        if not mt.empty:
            totals = mt.groupby("Periodo_Mes", as_index=False)["Mercado_total"].sum().rename(columns={"Mercado_total": "Total_mes"})
            mt = mt.merge(totals, on="Periodo_Mes", how="left")
            mt["Cuota_mercado"] = np.where(mt["Total_mes"] > 0, mt["Mercado_total"] / mt["Total_mes"] * 100, np.nan)
            result["market_time"] = mt
            pts = mt.groupby("Periodo_Mes", as_index=False).agg(Cuota_promedio=("Cuota_mercado", "mean")).sort_values("Periodo_Mes")
            if pts.shape[0] >= 2:
                result["variation_market"] = pts.iloc[-1]["Cuota_promedio"] - pts.iloc[0]["Cuota_promedio"]
    if has_altas:
        a = business_df.groupby("Operador", as_index=False).agg(Altas_total=("Altas", "sum"), Participacion_altas=("Participacion_altas", "mean"))
        total = a["Altas_total"].sum()
        a["Participacion_altas_global"] = np.where(total > 0, a["Altas_total"] / total * 100, np.nan)
        a = a.sort_values("Participacion_altas_global", ascending=False).reset_index(drop=True)
        result["altas_operator"] = a
        if not a.empty:
            result["leader_altas"] = a.iloc[0]
        at = business_df.dropna(subset=["Periodo_Mes"]).groupby(["Periodo_Mes", "Operador"], as_index=False).agg(Altas_total=("Altas", "sum"))
        if not at.empty:
            totals = at.groupby("Periodo_Mes", as_index=False)["Altas_total"].sum().rename(columns={"Altas_total": "Total_mes"})
            at = at.merge(totals, on="Periodo_Mes", how="left")
            at["Participacion_altas"] = np.where(at["Total_mes"] > 0, at["Altas_total"] / at["Total_mes"] * 100, np.nan)
            result["altas_time"] = at
            pts = at.groupby("Periodo_Mes", as_index=False).agg(Participacion_promedio=("Participacion_altas", "mean")).sort_values("Periodo_Mes")
            if pts.shape[0] >= 2:
                result["variation_altas"] = pts.iloc[-1]["Participacion_promedio"] - pts.iloc[0]["Participacion_promedio"]
    rsrp_operator = pd.DataFrame()
    if rsrp_df is not None and not rsrp_df.empty:
        rsrp_operator = rsrp_df.groupby("Operador", as_index=False).agg(
            RSRP_mediana=("RSRP_valido", "median"),
            Buena_o_mejor=("Categoria_RSRP", lambda s: s.isin(["Excelente", "Buena"]).mean() * 100),
            Critica=("Categoria_RSRP", lambda s: (s == "Crítica").mean() * 100),
        )
    cross = rsrp_operator.copy()
    if not result["market_operator"].empty:
        cross = cross.merge(result["market_operator"][["Operador", "Cuota_mercado_global"]], on="Operador", how="outer")
    if not result["altas_operator"].empty:
        cross = cross.merge(result["altas_operator"][["Operador", "Participacion_altas_global"]], on="Operador", how="outer")
    if not cross.empty:
        cross["Gap_red_vs_mercado"] = cross["Buena_o_mejor"] - cross["Cuota_mercado_global"]
        cross["Gap_red_vs_captacion"] = cross["Buena_o_mejor"] - cross["Participacion_altas_global"]
        result["cross_operator"] = cross
        result["scatter_df"] = cross.dropna(subset=["RSRP_mediana", "Cuota_mercado_global"]).copy()
    if rsrp_df is not None and not rsrp_df.empty and "Codigo_postal" in rsrp_df.columns and "Codigo_postal" in business_df.columns:
        rsrp_t = rsrp_df.groupby(["Codigo_postal", "Operador"], as_index=False).agg(
            RSRP_mediana=("RSRP_valido", "median"),
            Buena_o_mejor=("Categoria_RSRP", lambda s: s.isin(["Excelente", "Buena"]).mean() * 100),
        )
        biz_t = business_df.groupby([c for c in ["Codigo_postal"] + TERRITORIAL_STANDARD_COLS + ["Operador"] if c in business_df.columns], as_index=False).agg(
            Cuota_mercado=("Cuota_mercado", "mean"), Participacion_altas=("Participacion_altas", "mean")
        )
        terr = biz_t.merge(rsrp_t, on=["Codigo_postal", "Operador"], how="left")
        if not terr.empty:
            cuota_high = terr["Cuota_mercado"].quantile(0.60) if terr["Cuota_mercado"].notna().any() else np.nan
            cuota_low = terr["Cuota_mercado"].quantile(0.40) if terr["Cuota_mercado"].notna().any() else np.nan
            risk = terr[(terr["RSRP_mediana"] < -90) & (terr["Cuota_mercado"] >= cuota_high)].copy()
            opp = terr[(terr["RSRP_mediana"] >= -80) & (terr["Cuota_mercado"] <= cuota_low)].copy()
            result["risk_table"] = risk.sort_values(["Cuota_mercado", "RSRP_mediana"], ascending=[False, True]).head(25)
            result["opportunity_table"] = opp.sort_values(["RSRP_mediana", "Cuota_mercado"], ascending=[False, True]).head(25)
    result["available"] = True
    result["message"] = None
    return result

# =========================================================
# CARGA
# =========================================================
@st.cache_data
def load_data():
    data_path = find_existing_file(DATA_FILE_CANDIDATES)
    if data_path is None:
        raise FileNotFoundError("No se encontró el archivo RSRP_COMPLETO.csv en la carpeta del proyecto.")
    df, csv_encoding, csv_sep = robust_read_csv(data_path)
    df.columns = make_unique_columns(clean_columns(df.columns))
    codigo_col = find_col_by_aliases(df, ["Codigo_postal", "CODIGO POSTAL", "CÓDIGO POSTAL", "COD POSTAL", "COD. POSTAL"])
    fecha_inicio_col = find_col_by_aliases(df, ["Fecha de inicio", "FECHA DE INICIO", "Inicio", "Fecha inicio"])
    fecha_final_col = find_col_by_aliases(df, ["Fecha de finalización", "FECHA DE FINALIZACION", "FECHA DE FINALIZACIÓN", "Fecha finalizacion", "Fecha de finalizacion", "Fecha fin"])
    rename_map = {}
    if codigo_col: rename_map[codigo_col] = "Codigo_postal"
    if fecha_inicio_col: rename_map[fecha_inicio_col] = "Fecha de inicio"
    if fecha_final_col: rename_map[fecha_final_col] = "Fecha de finalización"
    df = df.rename(columns=rename_map)
    if "Codigo_postal" not in df.columns:
        raise KeyError("No se encontró una columna reconocible para código postal en el CSV principal.")
    if "Fecha de inicio" not in df.columns:
        raise KeyError("No se encontró una columna reconocible para fecha de inicio en el CSV principal.")
    if "Fecha de finalización" not in df.columns:
        df["Fecha de finalización"] = pd.NaT
    df["Codigo_postal"] = safe_to_str_series(df["Codigo_postal"])
    df["Fecha de inicio"] = pd.to_datetime(df["Fecha de inicio"], dayfirst=True, errors="coerce")
    df["Fecha de finalización"] = pd.to_datetime(df["Fecha de finalización"], dayfirst=True, errors="coerce")
    operator_cols_base = ["Claro", "Tigo", "Movistar Colombia", "ETB", "WOM Colombia", "Avantel"]
    operator_cols = [col for col in operator_cols_base if col in df.columns]
    if not operator_cols:
        raise KeyError("No se encontraron columnas de operadores esperadas en el CSV principal.")
    for col in operator_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df_long = df.melt(
        id_vars=["Codigo_postal", "Fecha de inicio", "Fecha de finalización"],
        value_vars=operator_cols,
        var_name="Operador",
        value_name="RSRP",
    )
    df_long["RSRP_valido"] = df_long["RSRP"].where(df_long["RSRP"] < 0)
    df_long["Con_medicion"] = df_long["RSRP_valido"].notna()
    df_long["Categoria_RSRP"] = df_long["RSRP_valido"].apply(classify_rsrp)
    territorial_df, territorial_info = load_territorial_data()
    df_long = safe_merge_territorial(df_long, territorial_df)
    df_base = safe_merge_territorial(df.copy(), territorial_df)
    business_long = build_business_long(df_base)
    return df, df_long, operator_cols, territorial_df, territorial_info, business_long, {"csv_encoding": csv_encoding, "csv_sep": csv_sep}

def compute_variation_tables(df_source, nivel_temporal):
    result = {
        "periodo_inicial": None,
        "periodo_final": None,
        "variacion_global": pd.NA,
        "variation_operator": pd.DataFrame(),
        "variation_route": pd.DataFrame(),
        "variation_circuit": pd.DataFrame(),
        "variation_cp": pd.DataFrame(),
        "variation_localidad": pd.DataFrame(),
        "variation_period": pd.DataFrame(),
        "tiene_variacion": False,
        "message": None,
    }
    if df_source is None or df_source.empty:
        result["message"] = "No hay datos para calcular variación."
        return result
    df_var = add_temporal_fields(df_source.copy())
    period_col, _fmt = period_columns(nivel_temporal)
    df_var = df_var[df_var["RSRP_valido"].notna()].copy()
    df_var = df_var[df_var[period_col].notna()].copy()
    if df_var.empty:
        result["message"] = "No hay datos válidos para calcular variación."
        return result
    variation_period = df_var.groupby(period_col, as_index=False).agg(RSRP_mediana=("RSRP_valido", "median")).sort_values(period_col)
    result["variation_period"] = variation_period.copy()
    if variation_period.shape[0] < 2:
        result["message"] = "Se requiere al menos dos periodos con datos válidos para calcular variación."
        return result
    periodo_inicial = variation_period.iloc[0][period_col]
    periodo_final = variation_period.iloc[-1][period_col]
    result["periodo_inicial"] = periodo_inicial
    result["periodo_final"] = periodo_final
    result["variacion_global"] = variation_period.iloc[-1]["RSRP_mediana"] - variation_period.iloc[0]["RSRP_mediana"]
    result["tiene_variacion"] = True
    def build_variation_table(group_cols):
        valid_group_cols = [c for c in group_cols if c in df_var.columns]
        if not valid_group_cols:
            return pd.DataFrame()
        base = df_var.groupby(valid_group_cols + [period_col], as_index=False).agg(RSRP_mediana=("RSRP_valido", "median"))
        initial = base[base[period_col] == periodo_inicial].drop(columns=[period_col]).rename(columns={"RSRP_mediana": "RSRP_inicial"})
        final = base[base[period_col] == periodo_final].drop(columns=[period_col]).rename(columns={"RSRP_mediana": "RSRP_final"})
        merged = initial.merge(final, on=valid_group_cols, how="outer")
        merged["Variacion_RSRP"] = merged["RSRP_final"] - merged["RSRP_inicial"]
        count_base = df_var.groupby(valid_group_cols, as_index=False).agg(Registros=("RSRP_valido", "count"))
        merged = merged.merge(count_base, on=valid_group_cols, how="left")
        return merged.sort_values("Variacion_RSRP", ascending=False).reset_index(drop=True)
    result["variation_operator"] = build_variation_table(["Operador"])
    result["variation_route"] = build_variation_table(["RUTA"]) if "RUTA" in df_var.columns else pd.DataFrame()
    result["variation_circuit"] = build_variation_table(["CIRCUITO"]) if "CIRCUITO" in df_var.columns else pd.DataFrame()
    result["variation_localidad"] = build_variation_table(["LOCALIDAD"]) if "LOCALIDAD" in df_var.columns else pd.DataFrame()
    result["variation_cp"] = build_variation_table(["Codigo_postal", "LOCALIDAD", "BARRIO", "RUTA", "CIRCUITO"])
    return result

def build_alerts(summary_operator, zone_summary, variation_result, business_metrics):
    alerts = []
    if not summary_operator.empty:
        op_crit = summary_operator.sort_values("Critica", ascending=False).iloc[0]
        alerts.append({"titulo": "Mayor exposición crítica", "detalle": f"{op_crit['Operador']} concentra {op_crit['Critica']:.1f}% de registros en categoría crítica."})
        op_best = summary_operator.sort_values("Score_operador", ascending=False).iloc[0]
        alerts.append({"titulo": "Mejor balance competitivo", "detalle": f"{op_best['Operador']} lidera con score {op_best['Score_operador']:.1f} y mediana {op_best['RSRP_mediana']:.1f} dBm."})
    if not zone_summary.empty:
        zona_crit = zone_summary.sort_values(["Pct_critica", "RSRP_mediana"], ascending=[False, True]).iloc[0]
        terr_lbl = build_territory_label(zona_crit)
        terr_txt = f" | {terr_lbl}" if terr_lbl else ""
        alerts.append({"titulo": "Zona con mayor urgencia", "detalle": f"CP {zona_crit['Codigo_postal']} presenta {zona_crit['Pct_critica']:.1f}% crítica y mediana {zona_crit['RSRP_mediana']:.1f} dBm{terr_txt}."})
    if variation_result.get("tiene_variacion", False):
        var_op = variation_result.get("variation_operator", pd.DataFrame())
        if not var_op.empty:
            op_det = var_op.sort_values("Variacion_RSRP", ascending=True).iloc[0]
            op_mej = var_op.sort_values("Variacion_RSRP", ascending=False).iloc[0]
            alerts.append({"titulo": "Mayor deterioro por operador", "detalle": f"{op_det['Operador']} registra variación {fmt_var_dBm(op_det['Variacion_RSRP'])}."})
            alerts.append({"titulo": "Mayor mejora por operador", "detalle": f"{op_mej['Operador']} registra variación {fmt_var_dBm(op_mej['Variacion_RSRP'])}."})
    if business_metrics.get("available", False):
        lm = business_metrics.get("leader_market")
        la = business_metrics.get("leader_altas")
        risk = business_metrics.get("risk_table", pd.DataFrame())
        if lm is not None:
            alerts.append({"titulo": "Líder de mercado", "detalle": f"{lm['Operador']} lidera mercado con {lm['Cuota_mercado_global']:.1f}% del total visible."})
        if la is not None:
            alerts.append({"titulo": "Líder de captación", "detalle": f"{la['Operador']} lidera altas con {la['Participacion_altas_global']:.1f}% del total visible."})
        if not risk.empty:
            r0 = risk.iloc[0]
            alerts.append({"titulo": "Riesgo comercial prioritario", "detalle": f"CP {r0['Codigo_postal']} | {r0['Operador']} combina red {fmt_dBm(r0['RSRP_mediana'])} y cuota {fmt_pct(r0['Cuota_mercado'])}."})
    return alerts[:8]

def build_exec_narrative(global_median, pct_good, pct_critica, best_operator, worst_zone, variation_result, business_metrics):
    parts = []
    if pd.notna(global_median):
        if global_median >= -70:
            parts.append("El desempeño agregado de señal se ubica en nivel excelente.")
        elif global_median >= -80:
            parts.append("El desempeño agregado de señal se mantiene en nivel bueno.")
        elif global_median >= -90:
            parts.append("El desempeño agregado de señal se mantiene en nivel aceptable.")
        else:
            parts.append("El desempeño agregado de señal se encuentra en condición crítica.")
    parts.append(f"La cobertura buena o mejor alcanza {pct_good:.1f}%, mientras la criticidad concentra {pct_critica:.1f}%.")
    if best_operator is not None:
        parts.append(f"El liderazgo competitivo corresponde a {best_operator['Operador']} con mediana {best_operator['RSRP_mediana']:.1f} dBm.")
    if worst_zone is not None:
        terr = build_territory_label(worst_zone)
        parts.append(f"La prioridad territorial principal es el código postal {worst_zone['Codigo_postal']}{' (' + terr + ')' if terr else ''}.")
    if variation_result.get("tiene_variacion", False):
        var_global = variation_result.get("variacion_global")
        if pd.notna(var_global):
            if var_global > 0:
                parts.append(f"Frente al primer periodo disponible, la señal mejora {var_global:.1f} dBm.")
            elif var_global < 0:
                parts.append(f"Frente al primer periodo disponible, la señal se deteriora {abs(var_global):.1f} dBm.")
            else:
                parts.append("Frente al primer periodo disponible, la señal se mantiene estable.")
    if business_metrics.get("available", False):
        lm = business_metrics.get("leader_market")
        la = business_metrics.get("leader_altas")
        if lm is not None:
            parts.append(f"En mercado, el liderazgo visible corresponde a {lm['Operador']} con {lm['Cuota_mercado_global']:.1f}%.")
        if la is not None:
            parts.append(f"En captación, {la['Operador']} lidera con {la['Participacion_altas_global']:.1f}% de altas.")
    return " ".join(parts)

def build_excel(summary_operator_df, zone_exec_df, variation_operator_df, variation_route_df, variation_circuit_df, market_df, altas_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        (summary_operator_df if summary_operator_df is not None and not summary_operator_df.empty else pd.DataFrame({"Mensaje": ["No hay datos para resumen por operador."]})).to_excel(writer, sheet_name="Resumen operador", index=False)
        (zone_exec_df if zone_exec_df is not None and not zone_exec_df.empty else pd.DataFrame({"Mensaje": ["No hay datos para zonas críticas."]})).to_excel(writer, sheet_name="Zonas críticas", index=False)
        (variation_operator_df if variation_operator_df is not None and not variation_operator_df.empty else pd.DataFrame({"Mensaje": ["No hay datos suficientes para variación por operador."]})).to_excel(writer, sheet_name="Variación operador", index=False)
        (variation_route_df if variation_route_df is not None and not variation_route_df.empty else pd.DataFrame({"Mensaje": ["No hay datos suficientes para variación por ruta."]})).to_excel(writer, sheet_name="Variación ruta", index=False)
        (variation_circuit_df if variation_circuit_df is not None and not variation_circuit_df.empty else pd.DataFrame({"Mensaje": ["No hay datos suficientes para variación por circuito."]})).to_excel(writer, sheet_name="Variación circuito", index=False)
        (market_df if market_df is not None and not market_df.empty else pd.DataFrame({"Mensaje": ["No se encontraron datos de mercado en el dataset."]})).to_excel(writer, sheet_name="Mercado", index=False)
        (altas_df if altas_df is not None and not altas_df.empty else pd.DataFrame({"Mensaje": ["No se encontraron datos de altas en el dataset."]})).to_excel(writer, sheet_name="Altas", index=False)
    output.seek(0)
    return output.getvalue()

# =========================================================
# CARGA BASE
# =========================================================
try:
    df, df_long, operator_cols, territorial_df, territorial_info, business_long, load_info = load_data()
except Exception as e:
    st.error(f"La aplicación no pudo cargarse correctamente: {e}")
    st.stop()

for op in operator_cols:
    if f"op_{op}" not in st.session_state:
        st.session_state[f"op_{op}"] = True
for key in ["localidad_sel", "barrio_sel", "ruta_sel", "circuito_sel"]:
    if key not in st.session_state:
        st.session_state[key] = []

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## Parámetros de análisis")
fecha_min = df["Fecha de inicio"].min()
fecha_max = df["Fecha de inicio"].max()
if pd.isna(fecha_min) or pd.isna(fecha_max):
    st.error("No se encontraron fechas válidas en el archivo principal.")
    st.stop()
rango_fechas = st.sidebar.date_input(
    "Ventana temporal",
    value=(fecha_min.date(), fecha_max.date()),
    min_value=fecha_min.date(),
    max_value=fecha_max.date(),
)
nivel_temporal_variacion = st.sidebar.selectbox("Nivel temporal de variación", options=["Mes", "Semana", "Día"], index=0)

st.sidebar.markdown("### Operadores incluidos")
btn1, btn2 = st.sidebar.columns(2)
with btn1:
    if st.button("Seleccionar todos", use_container_width=True):
        for op in operator_cols:
            st.session_state[f"op_{op}"] = True
with btn2:
    if st.button("Limpiar", use_container_width=True):
        for op in operator_cols:
            st.session_state[f"op_{op}"] = False
cols_ops = st.sidebar.columns(2)
for i, op in enumerate(operator_cols):
    with cols_ops[i % 2]:
        st.markdown('<div class="operator-box">', unsafe_allow_html=True)
        st.checkbox(op, key=f"op_{op}")
        st.markdown('</div>', unsafe_allow_html=True)
operadores_sel = [op for op in operator_cols if st.session_state.get(f"op_{op}", False)]
if not operadores_sel:
    st.warning("Debes seleccionar al menos un operador.")
    st.stop()

territorial_available_cols = territorial_info.get("available_cols", []) if territorial_info else []
territorial_filters_enabled = territorial_info.get("found", False) and "Codigo_postal" in territorial_df.columns
localidad_options, barrio_options, ruta_options, circuito_options = get_dynamic_territorial_options(
    territorial_df=territorial_df if territorial_filters_enabled else pd.DataFrame(),
    localidad_sel=st.session_state.get("localidad_sel", []),
    barrio_sel=st.session_state.get("barrio_sel", []),
    ruta_sel=st.session_state.get("ruta_sel", []),
)

st.sidebar.markdown("### Relación territorial")
localidad_sel = st.sidebar.multiselect("Localidad", options=localidad_options, default=[x for x in st.session_state.get("localidad_sel", []) if x in localidad_options], key="localidad_sel", disabled=not ("LOCALIDAD" in territorial_available_cols))
_, barrio_options, ruta_options, circuito_options = get_dynamic_territorial_options(territorial_df if territorial_filters_enabled else pd.DataFrame(), localidad_sel, st.session_state.get("barrio_sel", []), st.session_state.get("ruta_sel", []))
barrio_sel = st.sidebar.multiselect("Barrio", options=barrio_options, default=[x for x in st.session_state.get("barrio_sel", []) if x in barrio_options], key="barrio_sel", disabled=not ("BARRIO" in territorial_available_cols))
_, _, ruta_options, circuito_options = get_dynamic_territorial_options(territorial_df if territorial_filters_enabled else pd.DataFrame(), localidad_sel, barrio_sel, st.session_state.get("ruta_sel", []))
ruta_sel = st.sidebar.multiselect("Ruta", options=ruta_options, default=[x for x in st.session_state.get("ruta_sel", []) if x in ruta_options], key="ruta_sel", disabled=not ("RUTA" in territorial_available_cols))
_, _, _, circuito_options = get_dynamic_territorial_options(territorial_df if territorial_filters_enabled else pd.DataFrame(), localidad_sel, barrio_sel, ruta_sel)
circuito_sel = st.sidebar.multiselect("Circuito", options=circuito_options, default=[x for x in st.session_state.get("circuito_sel", []) if x in circuito_options], key="circuito_sel", disabled=not ("CIRCUITO" in territorial_available_cols))
territorial_scope = filter_territorial_scope(territorial_df if territorial_filters_enabled else pd.DataFrame(columns=["Codigo_postal"]), localidad_sel=localidad_sel, barrio_sel=barrio_sel, ruta_sel=ruta_sel, circuito_sel=circuito_sel)
codigos_disponibles_por_territorio = sorted(territorial_scope["Codigo_postal"].dropna().astype(str).unique().tolist()) if not territorial_scope.empty else []

codigos = sorted(df["Codigo_postal"].dropna().astype(str).unique().tolist())
if territorial_filters_enabled and (localidad_sel or barrio_sel or ruta_sel or circuito_sel):
    codigos_options_sidebar = sorted(set(codigos).intersection(set(codigos_disponibles_por_territorio)))
else:
    codigos_options_sidebar = codigos
codigos_sel = st.sidebar.multiselect("Códigos postales", options=codigos_options_sidebar, default=[])
solo_validos = st.sidebar.checkbox("Excluir registros sin medición válida", value=True)

if territorial_filters_enabled:
    st.sidebar.markdown(
        f"""
        <div class="note">
            Territorio activo: <b>{len(codigos_disponibles_por_territorio):,}</b> códigos postales
            {"| <b>" + str(len(localidad_sel)) + "</b> localidades" if localidad_sel else ""}
            {"| <b>" + str(len(ruta_sel)) + "</b> rutas" if ruta_sel else ""}
            {"| <b>" + str(len(circuito_sel)) + "</b> circuitos" if circuito_sel else ""}
        </div>
        """.replace(",", "."),
        unsafe_allow_html=True,
    )
if not territorial_filters_enabled and territorial_info.get("message"):
    st.sidebar.info(territorial_info["message"])

st.sidebar.markdown("---")
st.sidebar.markdown("### Referencia visual")
chips = []
for op in operadores_sel:
    color = OPERATOR_COLORS.get(op, "#64748B")
    chips.append(f'<span class="operator-chip" style="background:{color};">{op}</span>')
st.sidebar.markdown("".join(chips), unsafe_allow_html=True)

# =========================================================
# FILTROS
# =========================================================
fecha_ini, fecha_fin = rango_fechas
mask = (
    (df_long["Fecha de inicio"].dt.date >= fecha_ini)
    & (df_long["Fecha de inicio"].dt.date <= fecha_fin)
    & (df_long["Operador"].isin(operadores_sel))
)
codigos_por_territorio = set(codigos_disponibles_por_territorio) if (territorial_filters_enabled and (localidad_sel or barrio_sel or ruta_sel or circuito_sel)) else set()
codigos_manuales = set([str(x) for x in codigos_sel]) if codigos_sel else set()
codigos_filtrados_finales = None
if codigos_por_territorio and codigos_manuales:
    codigos_filtrados_finales = sorted(codigos_por_territorio.intersection(codigos_manuales))
elif codigos_por_territorio:
    codigos_filtrados_finales = sorted(codigos_por_territorio)
elif codigos_manuales:
    codigos_filtrados_finales = sorted(codigos_manuales)
if codigos_filtrados_finales is not None:
    mask &= df_long["Codigo_postal"].astype(str).isin(codigos_filtrados_finales)
df_f = df_long.loc[mask].copy()
if solo_validos:
    df_f = df_f[df_f["Con_medicion"]].copy()
if df_f.empty:
    st.error("No hay registros para la combinación de filtros seleccionada.")
    st.stop()

business_f = business_long.copy() if business_long is not None else pd.DataFrame()
if not business_f.empty:
    if "Fecha de inicio" in business_f.columns:
        business_f = business_f[(business_f["Fecha de inicio"].dt.date >= fecha_ini) & (business_f["Fecha de inicio"].dt.date <= fecha_fin)].copy()
    if "Operador" in business_f.columns:
        business_f = business_f[business_f["Operador"].isin(operadores_sel)].copy()
    if codigos_filtrados_finales is not None and "Codigo_postal" in business_f.columns:
        business_f = business_f[business_f["Codigo_postal"].astype(str).isin(codigos_filtrados_finales)].copy()
    if "Codigo_postal" in business_f.columns:
        business_f = business_f[~business_f["Codigo_postal"].astype(str).isin(BUSINESS_EXCLUDED_CP)].copy()

# =========================================================
# AGREGADOS RSRP
# =========================================================
summary_operator = (
    df_f.groupby("Operador", as_index=False)
    .agg(
        RSRP_promedio=("RSRP_valido", "mean"),
        RSRP_mediana=("RSRP_valido", "median"),
        Observaciones=("RSRP_valido", "count"),
        Codigos=("Codigo_postal", "nunique"),
        Excelente=("Categoria_RSRP", lambda s: (s == "Excelente").mean() * 100),
        Buena=("Categoria_RSRP", lambda s: (s == "Buena").mean() * 100),
        Aceptable=("Categoria_RSRP", lambda s: (s == "Aceptable").mean() * 100),
        Critica=("Categoria_RSRP", lambda s: (s == "Crítica").mean() * 100),
        Buena_o_mejor=("Categoria_RSRP", lambda s: s.isin(["Excelente", "Buena"]).mean() * 100),
    )
    .sort_values("RSRP_mediana", ascending=False)
)
summary_operator["Score_operador"] = summary_operator.apply(compute_operator_score, axis=1)
summary_operator["Clasificacion_score"] = summary_operator["Score_operador"].apply(lambda x: score_label(x)[0])
summary_operator["Semaforo_operador"] = summary_operator["Buena_o_mejor"].apply(lambda x: quality_status(x)[0])

best_operator = summary_operator.sort_values("Score_operador", ascending=False).iloc[0]
worst_operator = summary_operator.sort_values("Score_operador", ascending=True).iloc[0]
worst_operator_crit = summary_operator.sort_values("Critica", ascending=False).iloc[0]
global_median = df_f["RSRP_valido"].median()
global_mean = df_f["RSRP_valido"].mean()
pct_good = df_f["Categoria_RSRP"].isin(["Excelente", "Buena"]).mean() * 100
pct_acceptable = (df_f["Categoria_RSRP"] == "Aceptable").mean() * 100
pct_critical = (df_f["Categoria_RSRP"] == "Crítica").mean() * 100
status_text, status_class = executive_status(global_median)

zone_summary = (
    df_f.groupby("Codigo_postal", as_index=False)
    .agg(
        RSRP_promedio=("RSRP_valido", "mean"),
        RSRP_mediana=("RSRP_valido", "median"),
        Registros=("RSRP_valido", "count"),
        Operadores_presentes=("Operador", "nunique"),
        Pct_critica=("Categoria_RSRP", lambda s: (s == "Crítica").mean() * 100),
        Pct_buena_o_mejor=("Categoria_RSRP", lambda s: s.isin(["Excelente", "Buena"]).mean() * 100),
        Pct_aceptable=("Categoria_RSRP", lambda s: (s == "Aceptable").mean() * 100),
    )
)
territory_group_cols = [col for col in TERRITORIAL_STANDARD_COLS if col in df_f.columns]
if territory_group_cols:
    territory_agg = df_f.groupby("Codigo_postal", as_index=False)[territory_group_cols].agg(lambda s: first_not_null(s))
    zone_summary = zone_summary.merge(territory_agg, on="Codigo_postal", how="left")
zone_worst_operator = (
    df_f.groupby(["Codigo_postal", "Operador"], as_index=False)
    .agg(RSRP_mediana=("RSRP_valido", "median"))
    .sort_values(["Codigo_postal", "RSRP_mediana"], ascending=[True, True])
    .groupby("Codigo_postal", as_index=False)
    .first()
    .rename(columns={"Operador": "Operador_mas_debil", "RSRP_mediana": "RSRP_mas_debil"})
)
zone_best_operator = (
    df_f.groupby(["Codigo_postal", "Operador"], as_index=False)
    .agg(RSRP_mediana=("RSRP_valido", "median"))
    .sort_values(["Codigo_postal", "RSRP_mediana"], ascending=[True, False])
    .groupby("Codigo_postal", as_index=False)
    .first()
    .rename(columns={"Operador": "Operador_lider", "RSRP_mediana": "RSRP_lider"})
)
zone_summary = zone_summary.merge(zone_worst_operator, on="Codigo_postal", how="left")
zone_summary = zone_summary.merge(zone_best_operator, on="Codigo_postal", how="left")
zone_summary["Indice_prioridad"] = (((-1 * zone_summary["RSRP_mediana"]) * 0.40) + (zone_summary["Pct_critica"] * 0.35) - (zone_summary["Pct_buena_o_mejor"] * 0.15) + (zone_summary["Pct_aceptable"] * 0.10))
zone_summary["Semaforo"] = zone_summary.apply(lambda r: zone_semaphore(r["Pct_critica"], r["RSRP_mediana"]), axis=1)
zone_summary = zone_summary.sort_values(["Pct_critica", "RSRP_mediana"], ascending=[False, True])

top_zones = zone_summary.head(15).copy()
worst_zone = top_zones.iloc[0] if not top_zones.empty else None
best_zones = zone_summary.sort_values(["Pct_buena_o_mejor", "RSRP_mediana"], ascending=[False, False]).head(15).copy()
best_zone = best_zones.iloc[0] if not best_zones.empty else None
trend = df_f.groupby(["Fecha de inicio", "Operador"], as_index=False).agg(RSRP_mediana=("RSRP_valido", "median"))
quality = df_f.groupby(["Operador", "Categoria_RSRP"], as_index=False).size().rename(columns={"size": "Cantidad"})
quality_pct = quality.copy()
quality_totals = quality_pct.groupby("Operador", as_index=False)["Cantidad"].sum().rename(columns={"Cantidad": "Total"})
quality_pct = quality_pct.merge(quality_totals, on="Operador", how="left")
quality_pct["Porcentaje"] = np.where(quality_pct["Total"] > 0, quality_pct["Cantidad"] / quality_pct["Total"] * 100, np.nan)
matrix_source = (df_f[df_f["Codigo_postal"].isin(top_zones["Codigo_postal"])] if not top_zones.empty else df_f.iloc[0:0]).groupby(["Codigo_postal", "Operador"], as_index=False).agg(RSRP_mediana=("RSRP_valido", "median"))
trend_min = float(trend["RSRP_mediana"].min()) if not trend.empty else -125.0
trend_max = float(trend["RSRP_mediana"].max()) if not trend.empty else -60.0
y_min = max(-125, trend_min - 2)
y_max = min(-60, trend_max + 2)

variation_result = compute_variation_tables(df_f, nivel_temporal_variacion)
variation_operator = variation_result["variation_operator"].copy()
variation_route = variation_result["variation_route"].copy()
variation_circuit = variation_result["variation_circuit"].copy()
variation_cp = variation_result["variation_cp"].copy()
variation_localidad = variation_result["variation_localidad"].copy()
variation_period = variation_result["variation_period"].copy()
if variation_result["tiene_variacion"] and not variation_cp.empty:
    mayor_mejora = variation_cp.sort_values("Variacion_RSRP", ascending=False).iloc[0]
    mayor_deterioro = variation_cp.sort_values("Variacion_RSRP", ascending=True).iloc[0]
else:
    mayor_mejora = None
    mayor_deterioro = None

zone_exec_cols = ["Codigo_postal", "Semaforo", "RSRP_mediana", "Pct_critica", "Pct_aceptable", "Pct_buena_o_mejor", "Operador_mas_debil", "RSRP_mas_debil", "Operador_lider", "RSRP_lider", "Operadores_presentes", "Registros"] + [c for c in TERRITORIAL_STANDARD_COLS if c in top_zones.columns]
zone_exec_export = top_zones[zone_exec_cols].copy() if not top_zones.empty else pd.DataFrame(columns=zone_exec_cols)

business_metrics = compute_business_metrics(business_f, df_f)
market_operator = business_metrics.get("market_operator", pd.DataFrame())
altas_operator = business_metrics.get("altas_operator", pd.DataFrame())
cross_operator = business_metrics.get("cross_operator", pd.DataFrame())
market_time = business_metrics.get("market_time", pd.DataFrame())
altas_time = business_metrics.get("altas_time", pd.DataFrame())
scatter_df = business_metrics.get("scatter_df", pd.DataFrame())
risk_table = business_metrics.get("risk_table", pd.DataFrame())
opportunity_table = business_metrics.get("opportunity_table", pd.DataFrame())
leader_market = business_metrics.get("leader_market")
leader_altas = business_metrics.get("leader_altas")

excel_bytes = build_excel(
    summary_operator_df=safe_round_columns(summary_operator, ["RSRP_promedio", "RSRP_mediana", "Excelente", "Buena", "Aceptable", "Critica", "Buena_o_mejor", "Score_operador"]),
    zone_exec_df=safe_round_columns(zone_exec_export, ["RSRP_mediana", "Pct_critica", "Pct_aceptable", "Pct_buena_o_mejor", "RSRP_mas_debil", "RSRP_lider"]),
    variation_operator_df=safe_round_columns(variation_operator, ["RSRP_inicial", "RSRP_final", "Variacion_RSRP"]),
    variation_route_df=safe_round_columns(variation_route, ["RSRP_inicial", "RSRP_final", "Variacion_RSRP"]),
    variation_circuit_df=safe_round_columns(variation_circuit, ["RSRP_inicial", "RSRP_final", "Variacion_RSRP"]),
    market_df=safe_round_columns(market_operator, ["Mercado_total", "Cuota_mercado", "Cuota_mercado_global"]),
    altas_df=safe_round_columns(altas_operator, ["Altas_total", "Participacion_altas", "Participacion_altas_global"]),
)
exec_narrative = build_exec_narrative(global_median, pct_good, pct_critical, best_operator, worst_zone, variation_result, business_metrics)
alerts = build_alerts(summary_operator, zone_summary, variation_result, business_metrics)

# =========================================================
# HEADER
# =========================================================
periodo_txt = f"{pd.to_datetime(fecha_ini).strftime('%d/%m/%Y')} a {pd.to_datetime(fecha_fin).strftime('%d/%m/%Y')}"
obs_validas = int(df_f["RSRP_valido"].count())
st.markdown('<div class="header-shell">', unsafe_allow_html=True)
h1, h2 = st.columns([5.2, 1.1], gap="large")
with h1:
    st.markdown(
        f"""
        <div style="padding-top: 4px;">
            <div style="font-size: 0.86rem; color: #94A3B8; font-weight: 800; letter-spacing: 0.5px;">{AREA_NAME}</div>
            <div style="font-size: 2.05rem; color: #FFFFFF; font-weight: 900; line-height: 1.1; margin-top: 6px;">{DASHBOARD_TITLE}</div>
            <div class="note" style="margin-top: 10px;">
                Periodo analizado: <b>{periodo_txt}</b> |
                Observaciones válidas: <b>{fmt_int(obs_validas)}</b> |
                Códigos postales visibles: <b>{fmt_int(df_f['Codigo_postal'].nunique())}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with h2:
    st.download_button(
        label="Exportar Excel",
        data=excel_bytes,
        file_name="dashboard_rsrp_mercado_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
st.markdown('</div>', unsafe_allow_html=True)
st.markdown(f'<div class="{status_class}">{status_text} agregado del periodo</div>', unsafe_allow_html=True)

# KPI STRIP
st.markdown('<div class="kpi-strip">', unsafe_allow_html=True)
s1, s2, s3, s4, s5, s6 = st.columns(6)
with s1:
    st.markdown(f'<div class="card"><div class="kpi-label">RSRP mediano</div><div class="kpi-value">{fmt_dBm(global_median)}</div><div class="kpi-sub">Indicador ejecutivo principal.</div></div>', unsafe_allow_html=True)
with s2:
    st.markdown(f'<div class="card"><div class="kpi-label">% cobertura buena</div><div class="kpi-value">{fmt_pct(pct_good)}</div><div class="kpi-sub">Excelente + Buena.</div></div>', unsafe_allow_html=True)
with s3:
    st.markdown(f'<div class="card"><div class="kpi-label">Operador líder</div><div class="metric-operator" style="color:{OPERATOR_COLORS.get(best_operator["Operador"], "#FFFFFF")};">{best_operator["Operador"]}</div><div class="kpi-sub">Score {best_operator["Score_operador"]:.1f}</div></div>', unsafe_allow_html=True)
with s4:
    st.markdown(f'<div class="card"><div class="kpi-label">Peor operador</div><div class="metric-operator" style="color:{OPERATOR_COLORS.get(worst_operator_crit["Operador"], "#FFFFFF")};">{worst_operator_crit["Operador"]}</div><div class="kpi-sub">Crítica {fmt_pct(worst_operator_crit["Critica"])}.</div></div>', unsafe_allow_html=True)
with s5:
    lm_name = leader_market["Operador"] if leader_market is not None else "N/D"
    lm_share = fmt_pct(leader_market["Cuota_mercado_global"]) if leader_market is not None else "Sin datos"
    st.markdown(f'<div class="card"><div class="kpi-label">Cuota mercado líder</div><div class="metric-operator" style="color:{OPERATOR_COLORS.get(lm_name, "#FFFFFF")};">{lm_name}</div><div class="kpi-sub">{lm_share}</div></div>', unsafe_allow_html=True)
with s6:
    st.markdown(f'<div class="card"><div class="kpi-label">Variación global</div><div class="kpi-value">{fmt_var_dBm(variation_result["variacion_global"])}</div><div class="kpi-sub">Nivel temporal: {nivel_temporal_variacion}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# CONTEXTO
r1, r2, r3 = st.columns((1.0, 1.1, 0.9), gap="large")
with r1:
    st.markdown("""
    <div class="section-card">
        <div class="section-title">Regla de clasificación RSRP</div>
        <div class="section-subtitle">Escala visible en el dashboard para interpretación ejecutiva consistente.</div>
        <div class="rule-card">
            <div class="territory-sub">
                <b style="color:#22C55E;">Excelente:</b> ≥ -70 dBm<br><br>
                <b style="color:#84CC16;">Buena:</b> -80 a -70 dBm<br><br>
                <b style="color:#F59E0B;">Aceptable:</b> -90 a -80 dBm<br><br>
                <b style="color:#EF4444;">Crítica:</b> &lt; -90 dBm
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with r2:
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">Lectura ejecutiva consolidada</div>
        <div class="section-subtitle">Resumen automático para presentación gerencial.</div>
        <div class="rule-card"><div class="territory-sub">{exec_narrative}</div></div>
    </div>
    """, unsafe_allow_html=True)
with r3:
    territorio_activo_txt = f"{len(codigos_disponibles_por_territorio):,} CP relacionados".replace(",", ".") if territorial_filters_enabled and (localidad_sel or barrio_sel or ruta_sel or circuito_sel) else f"{df_f['Codigo_postal'].nunique():,} CP en muestra".replace(",", ".")
    st.markdown(f"""
    <div class="section-card">
        <div class="section-title">Contexto de territorio activo</div>
        <div class="section-subtitle">Cantidad visible del universo filtrado.</div>
        <div class="rule-card">
            <div class="territory-label">Territorio</div>
            <div class="territory-value">{territorio_activo_txt}</div>
            <div class="territory-sub">
                Localidades visibles: <b>{df_f['LOCALIDAD'].dropna().nunique() if 'LOCALIDAD' in df_f.columns else 0}</b><br>
                Rutas visibles: <b>{df_f['RUTA'].dropna().nunique() if 'RUTA' in df_f.columns else 0}</b><br>
                Circuitos visibles: <b>{df_f['CIRCUITO'].dropna().nunique() if 'CIRCUITO' in df_f.columns else 0}</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# TABS
order_quality = ["Excelente", "Buena", "Aceptable", "Crítica", "Sin medición"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Resumen ejecutivo", "Comparativo de operadores", "Zonas prioritarias", "Variación ejecutiva", "Mercado y Captación"])

with tab1:
    a0, a00 = st.columns((1.05, 0.95), gap="large")
    with a0:
        st.markdown('<div class="section-card"><div class="section-title">Alertas ejecutivas automáticas</div><div class="section-subtitle">Hallazgos clave generados a partir de la muestra filtrada.</div>', unsafe_allow_html=True)
        if alerts:
            for alert in alerts:
                st.markdown(f'<div class="alert-card"><div class="insight-title">{alert["titulo"]}</div><div class="insight-body">{alert["detalle"]}</div></div>', unsafe_allow_html=True)
        else:
            st.info("No fue posible generar alertas ejecutivas con la muestra actual.")
        st.markdown('</div>', unsafe_allow_html=True)
    with a00:
        st.markdown('<div class="section-card"><div class="section-title">Distribución consolidada por categoría</div><div class="section-subtitle">Participación general por nivel de señal bajo la nueva regla de clasificación.</div>', unsafe_allow_html=True)
        quality_global = df_f.groupby("Categoria_RSRP", as_index=False).size().rename(columns={"size": "Cantidad"})
        total_global = quality_global["Cantidad"].sum()
        quality_global["Porcentaje"] = np.where(total_global > 0, quality_global["Cantidad"] / total_global * 100, np.nan)
        quality_global["Categoria_RSRP"] = pd.Categorical(quality_global["Categoria_RSRP"], categories=order_quality, ordered=True)
        quality_global = quality_global.sort_values("Categoria_RSRP")
        donut = alt.Chart(quality_global).mark_arc(innerRadius=70).encode(
            theta=alt.Theta("Cantidad:Q"),
            color=alt.Color("Categoria_RSRP:N", scale=alt.Scale(domain=list(QUALITY_COLORS.keys()), range=list(QUALITY_COLORS.values())), legend=alt.Legend(title="Categoría")),
            tooltip=[alt.Tooltip("Categoria_RSRP:N", title="Categoría"), alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"), alt.Tooltip("Porcentaje:Q", title="% participación", format=".1f")],
        ).properties(height=320)
        st.altair_chart(donut, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    a1, a2 = st.columns((1.08, 0.92), gap="large")
    with a1:
        st.markdown('<div class="section-card"><div class="section-title">Tendencia ejecutiva por operador</div><div class="section-subtitle">Evolución temporal de la mediana de RSRP.</div>', unsafe_allow_html=True)
        line = alt.Chart(trend).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X("Fecha de inicio:T", title="Fecha", axis=alt.Axis(format="%b %Y", labelAngle=0)),
            y=alt.Y("RSRP_mediana:Q", title="RSRP mediano (dBm)", scale=alt.Scale(domain=[y_min, y_max], nice=False)),
            color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=alt.Legend(title="Operador")),
            tooltip=[alt.Tooltip("Fecha de inicio:T", title="Fecha"), alt.Tooltip("Operador:N", title="Operador"), alt.Tooltip("RSRP_mediana:Q", title="RSRP mediano", format=".1f")],
        ).properties(height=390).interactive()
        st.altair_chart(line, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with a2:
        st.markdown('<div class="section-card"><div class="section-title">Lectura ejecutiva</div><div class="section-subtitle">Síntesis lista para presentar.</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-card"><div class="insight-title">Liderazgo del periodo</div><div class="insight-body">El mejor desempeño agregado corresponde a <b style="color:{OPERATOR_COLORS.get(best_operator["Operador"], "#FFFFFF")};">{best_operator["Operador"]}</b>, con mediana <b>{fmt_dBm(best_operator["RSRP_mediana"])}</b> y score <b>{best_operator["Score_operador"]:.1f}</b>.</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="insight-card"><div class="insight-title">Zona prioritaria</div><div class="insight-body">El código postal <b>{worst_zone["Codigo_postal"] if worst_zone is not None else "N/D"}</b> presenta <b>{fmt_pct(worst_zone["Pct_critica"]) if worst_zone is not None else "N/D"}</b> en condición crítica.</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    c0, c00 = st.columns((1, 1), gap="large")
    with c0:
        st.markdown('<div class="section-card"><div class="section-title">Distribución porcentual por categoría y operador</div><div class="section-subtitle">Permite ver concentración de criticidad y balance de señal.</div>', unsafe_allow_html=True)
        stacked_pct = alt.Chart(quality_pct[quality_pct["Categoria_RSRP"].isin(order_quality[:-1])]).mark_bar().encode(
            x=alt.X("Operador:N", title=None),
            y=alt.Y("Porcentaje:Q", title="% participación"),
            color=alt.Color("Categoria_RSRP:N", scale=alt.Scale(domain=list(QUALITY_COLORS.keys()), range=list(QUALITY_COLORS.values())), legend=alt.Legend(title="Categoría")),
            tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("Categoria_RSRP:N"), alt.Tooltip("Porcentaje:Q", format=".1f"), alt.Tooltip("Cantidad:Q", format=",.0f")],
        ).properties(height=390)
        st.altair_chart(stacked_pct, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c00:
        st.markdown('<div class="section-card"><div class="section-title">Score por operador</div><div class="section-subtitle">Índice compuesto basado en mediana RSRP, cobertura buena o mejor y menor proporción crítica.</div>', unsafe_allow_html=True)
        score_chart = alt.Chart(summary_operator.sort_values("Score_operador", ascending=False)).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("Operador:N", title=None, sort="-y"),
            y=alt.Y("Score_operador:Q", title="Score"),
            color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=None),
            tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("Score_operador:Q", format=".1f"), alt.Tooltip("RSRP_mediana:Q", format=".1f")],
        ).properties(height=390)
        st.altair_chart(score_chart, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    c1, c2 = st.columns((1, 1), gap="large")
    with c1:
        st.markdown('<div class="section-card"><div class="section-title">Distribución de calidad por operador</div><div class="section-subtitle">Volumen absoluto de registros por categoría.</div>', unsafe_allow_html=True)
        stacked = alt.Chart(quality).mark_bar().encode(
            x=alt.X("Operador:N", title=None),
            y=alt.Y("Cantidad:Q", title="Cantidad"),
            color=alt.Color("Categoria_RSRP:N", scale=alt.Scale(domain=list(QUALITY_COLORS.keys()), range=list(QUALITY_COLORS.values())), legend=alt.Legend(title="Calidad")),
            tooltip=["Operador", "Categoria_RSRP", "Cantidad"],
        ).properties(height=390)
        st.altair_chart(stacked, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-card"><div class="section-title">Resumen ejecutivo por operador</div><div class="section-subtitle">Incluye score, semáforo y composición por categoría.</div>', unsafe_allow_html=True)
        executive_table = safe_round_columns(summary_operator.copy(), ["RSRP_promedio", "RSRP_mediana", "Excelente", "Buena", "Aceptable", "Critica", "Buena_o_mejor", "Score_operador"])
        st.dataframe(executive_table, use_container_width=True, height=380)
        st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    z1, z2 = st.columns((1.05, 0.95), gap="large")
    with z1:
        st.markdown('<div class="section-card"><div class="section-title">Top zonas con mayor oportunidad de mejora</div><div class="section-subtitle">Se priorizan códigos postales con mayor criticidad y peor mediana.</div>', unsafe_allow_html=True)
        top_chart = top_zones.copy()
        if not top_chart.empty:
            top_chart["Codigo_postal"] = top_chart["Codigo_postal"].astype(str)
            bars = alt.Chart(top_chart).mark_bar(cornerRadiusTopLeft=6, cornerRadiusBottomLeft=6).encode(
                x=alt.X("Pct_critica:Q", title="% de registros en condición crítica"),
                y=alt.Y("Codigo_postal:N", sort="-x", title="Código postal"),
                color=alt.value("#EF4444"),
                tooltip=[alt.Tooltip("Codigo_postal:N"), alt.Tooltip("Pct_critica:Q", format=".1f"), alt.Tooltip("RSRP_mediana:Q", format=".1f"), alt.Tooltip("Operador_mas_debil:N")],
            ).properties(height=420)
            st.altair_chart(bars, use_container_width=True)
        else:
            st.info("No hay datos suficientes para mostrar zonas prioritarias.")
        st.markdown('</div>', unsafe_allow_html=True)
    with z2:
        st.markdown('<div class="section-card"><div class="section-title">Resumen claro de zonas a intervenir</div><div class="section-subtitle">Incluye semáforo ejecutivo y detalle territorial.</div>', unsafe_allow_html=True)
        zone_exec = top_zones[zone_exec_cols].copy() if not top_zones.empty else pd.DataFrame(columns=zone_exec_cols)
        if not zone_exec.empty:
            zone_exec["Codigo_postal"] = zone_exec["Codigo_postal"].astype(str)
            zone_exec = safe_round_columns(zone_exec, ["RSRP_mediana", "Pct_critica", "Pct_aceptable", "Pct_buena_o_mejor", "RSRP_mas_debil", "RSRP_lider"])
            st.dataframe(zone_exec, use_container_width=True, height=420)
        else:
            st.info("No hay datos de zonas críticas para mostrar.")
        st.markdown('</div>', unsafe_allow_html=True)
    z3, z4 = st.columns((1, 1), gap="large")
    with z3:
        st.markdown('<div class="section-card"><div class="section-title">Matriz de desempeño por zona y operador</div><div class="section-subtitle">Permite ubicar rápidamente dónde cada operador presenta peor nivel de señal.</div>', unsafe_allow_html=True)
        matrix_plot = matrix_source.copy()
        if not matrix_plot.empty:
            matrix_plot["Codigo_postal"] = matrix_plot["Codigo_postal"].astype(str)
            matrix = alt.Chart(matrix_plot).mark_rect().encode(
                x=alt.X("Operador:N", title=None),
                y=alt.Y("Codigo_postal:N", title="Código postal"),
                color=alt.Color("RSRP_mediana:Q", title="RSRP mediano", scale=alt.Scale(domain=[-110, -60], scheme="redyellowgreen")),
                tooltip=[alt.Tooltip("Codigo_postal:N"), alt.Tooltip("Operador:N"), alt.Tooltip("RSRP_mediana:Q", format=".1f")],
            ).properties(height=420)
            st.altair_chart(matrix, use_container_width=True)
        else:
            st.info("No hay datos suficientes para mostrar la matriz.")
        st.markdown('</div>', unsafe_allow_html=True)
    with z4:
        st.markdown('<div class="section-card"><div class="section-title">Conclusión territorial ejecutiva</div><div class="section-subtitle">Lectura visual e intuitiva para priorización inmediata.</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="territory-card"><div class="territory-label">Zona de mayor prioridad</div><div class="territory-value">{str(worst_zone["Codigo_postal"]) if worst_zone is not None else "N/D"}</div><div class="territory-sub">Semáforo: <b>{worst_zone["Semaforo"] if worst_zone is not None else "N/D"}</b><br>Crítica: <b>{fmt_pct(worst_zone["Pct_critica"]) if worst_zone is not None else "N/D"}</b></div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="territory-card"><div class="territory-label">Mejor zona del periodo</div><div class="territory-value">{str(best_zone["Codigo_postal"]) if best_zone is not None else "N/D"}</div><div class="territory-sub">Cobertura buena o mejor: <b>{fmt_pct(best_zone["Pct_buena_o_mejor"]) if best_zone is not None else "N/D"}</b></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="section-card"><div class="section-title">Variación ejecutiva de RSRP</div><div class="section-subtitle">Compara el primer periodo disponible contra el último periodo disponible según los filtros activos.</div>', unsafe_allow_html=True)
    if variation_result["tiene_variacion"]:
        var_badge_text, var_badge_class = variation_status(variation_result["variacion_global"])
        periodo_inicial = pd.to_datetime(variation_result["periodo_inicial"])
        periodo_final = pd.to_datetime(variation_result["periodo_final"])
        st.markdown(f'<div class="{var_badge_class}">Variación global {var_badge_text.lower()} | {fmt_var_dBm(variation_result["variacion_global"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="note" style="margin-bottom: 18px;">Periodo inicial: {periodo_inicial.strftime("%d/%m/%Y")} | Periodo final: {periodo_final.strftime("%d/%m/%Y")} | Nivel temporal: {nivel_temporal_variacion}</div>', unsafe_allow_html=True)
    else:
        st.warning(variation_result["message"] or "No hay suficiente información para calcular la variación ejecutiva.")
    st.markdown('</div>', unsafe_allow_html=True)
    v1, v2, v3, v4 = st.columns(4, gap="medium")
    with v1:
        st.markdown(f'<div class="card"><div class="kpi-label">KPI de variación global</div><div class="kpi-value">{fmt_var_dBm(variation_result["variacion_global"])}</div><div class="kpi-sub">Diferencia entre la mediana final y la inicial.</div></div>', unsafe_allow_html=True)
    with v2:
        if mayor_mejora is not None:
            st.markdown(f'<div class="card"><div class="kpi-label">Mayor mejora</div><div class="kpi-value">{fmt_var_dBm(mayor_mejora["Variacion_RSRP"])}</div><div class="kpi-sub">Código postal: {str(mayor_mejora["Codigo_postal"])}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><div class="kpi-label">Mayor mejora</div><div class="kpi-value">N/D</div><div class="kpi-sub">No hay datos suficientes.</div></div>', unsafe_allow_html=True)
    with v3:
        if mayor_deterioro is not None:
            st.markdown(f'<div class="card"><div class="kpi-label">Mayor deterioro</div><div class="kpi-value">{fmt_var_dBm(mayor_deterioro["Variacion_RSRP"])}</div><div class="kpi-sub">Código postal: {str(mayor_deterioro["Codigo_postal"])}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><div class="kpi-label">Mayor deterioro</div><div class="kpi-value">N/D</div><div class="kpi-sub">No hay datos suficientes.</div></div>', unsafe_allow_html=True)
    with v4:
        st.markdown(f'<div class="card"><div class="kpi-label">Cobertura territorial visible</div><div class="kpi-value">{fmt_int(df_f["Codigo_postal"].nunique())}</div><div class="kpi-sub">Rutas: {fmt_int(df_f["RUTA"].dropna().nunique() if "RUTA" in df_f.columns else 0)} | Circuitos: {fmt_int(df_f["CIRCUITO"].dropna().nunique() if "CIRCUITO" in df_f.columns else 0)}</div></div>', unsafe_allow_html=True)
    v5, v6 = st.columns((1, 1), gap="large")
    with v5:
        st.markdown('<div class="section-card"><div class="section-title">Gráfico de variación por operador</div><div class="section-subtitle">Comparación entre el primer y el último periodo disponible para cada operador.</div>', unsafe_allow_html=True)
        if not variation_operator.empty:
            operator_var_chart = alt.Chart(variation_operator).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Operador:N", title=None, sort="-y"),
                y=alt.Y("Variacion_RSRP:Q", title="Variación RSRP (dBm)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=None),
                tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("RSRP_inicial:Q", format=".1f"), alt.Tooltip("RSRP_final:Q", format=".1f"), alt.Tooltip("Variacion_RSRP:Q", format=".1f")],
            ).properties(height=360)
            st.altair_chart(operator_var_chart, use_container_width=True)
        else:
            st.info("No hay datos suficientes para mostrar la variación por operador.")
        st.markdown('</div>', unsafe_allow_html=True)
    with v6:
        st.markdown('<div class="section-card"><div class="section-title">Tendencia agregada por periodo</div><div class="section-subtitle">Trayectoria consolidada de la mediana RSRP.</div>', unsafe_allow_html=True)
        if not variation_period.empty:
            period_col, period_fmt = period_columns(nivel_temporal_variacion)
            line_period = alt.Chart(variation_period).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X(f"{period_col}:T", title="Periodo", axis=alt.Axis(format=period_fmt, labelAngle=0)),
                y=alt.Y("RSRP_mediana:Q", title="RSRP mediano (dBm)"),
                tooltip=[alt.Tooltip(f"{period_col}:T", title="Periodo"), alt.Tooltip("RSRP_mediana:Q", format=".1f")],
            ).properties(height=360).interactive()
            st.altair_chart(line_period, use_container_width=True)
        else:
            st.info("No hay datos suficientes para la trayectoria temporal.")
        st.markdown('</div>', unsafe_allow_html=True)
    v7, v8 = st.columns((1, 1), gap="large")
    with v7:
        st.markdown('<div class="section-card"><div class="section-title">Gráfico de variación por ruta</div><div class="section-subtitle">Lectura ejecutiva del comportamiento por ruta.</div>', unsafe_allow_html=True)
        if not variation_route.empty and "RUTA" in variation_route.columns:
            route_var_chart = alt.Chart(variation_route.dropna(subset=["RUTA"])).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Variacion_RSRP:Q", title="Variación RSRP (dBm)"),
                y=alt.Y("RUTA:N", sort="-x", title="Ruta"),
                color=alt.condition(alt.datum.Variacion_RSRP >= 0, alt.value("#22C55E"), alt.value("#EF4444")),
                tooltip=[alt.Tooltip("RUTA:N"), alt.Tooltip("RSRP_inicial:Q", format=".1f"), alt.Tooltip("RSRP_final:Q", format=".1f"), alt.Tooltip("Variacion_RSRP:Q", format=".1f")],
            ).properties(height=420)
            st.altair_chart(route_var_chart, use_container_width=True)
        else:
            st.info("No hay datos suficientes para calcular la variación por ruta.")
        st.markdown('</div>', unsafe_allow_html=True)
    with v8:
        st.markdown('<div class="section-card"><div class="section-title">Gráfico de variación por circuito</div><div class="section-subtitle">Lectura ejecutiva del comportamiento por circuito.</div>', unsafe_allow_html=True)
        if not variation_circuit.empty and "CIRCUITO" in variation_circuit.columns:
            circuit_var_chart = alt.Chart(variation_circuit.dropna(subset=["CIRCUITO"])).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Variacion_RSRP:Q", title="Variación RSRP (dBm)"),
                y=alt.Y("CIRCUITO:N", sort="-x", title="Circuito"),
                color=alt.condition(alt.datum.Variacion_RSRP >= 0, alt.value("#22C55E"), alt.value("#EF4444")),
                tooltip=[alt.Tooltip("CIRCUITO:N"), alt.Tooltip("RSRP_inicial:Q", format=".1f"), alt.Tooltip("RSRP_final:Q", format=".1f"), alt.Tooltip("Variacion_RSRP:Q", format=".1f")],
            ).properties(height=420)
            st.altair_chart(circuit_var_chart, use_container_width=True)
        else:
            st.info("No hay datos suficientes para calcular la variación por circuito.")
        st.markdown('</div>', unsafe_allow_html=True)
    v9, v10 = st.columns((1, 1), gap="large")
    with v9:
        st.markdown('<div class="section-card"><div class="section-title">Tabla de variación por código postal</div><div class="section-subtitle">Detalle territorial enriquecido.</div>', unsafe_allow_html=True)
        if not variation_cp.empty:
            variation_cp_show = safe_round_columns(variation_cp.copy(), ["RSRP_inicial", "RSRP_final", "Variacion_RSRP"])
            st.dataframe(variation_cp_show, use_container_width=True, height=360)
        else:
            st.info("No hay datos suficientes para mostrar la variación por código postal.")
        st.markdown('</div>', unsafe_allow_html=True)
    with v10:
        st.markdown('<div class="section-card"><div class="section-title">Variación por localidad</div><div class="section-subtitle">Lectura agregada del cambio por localidad.</div>', unsafe_allow_html=True)
        if not variation_localidad.empty and "LOCALIDAD" in variation_localidad.columns:
            variation_localidad_show = safe_round_columns(variation_localidad.copy(), ["RSRP_inicial", "RSRP_final", "Variacion_RSRP"])
            st.dataframe(variation_localidad_show, use_container_width=True, height=360)
        else:
            st.info("No hay datos suficientes para mostrar la variación por localidad.")
        st.markdown('</div>', unsafe_allow_html=True)

with tab5:
    st.markdown('<div class="section-card"><div class="section-title">Mercado y Captación</div><div class="section-subtitle">Cruce ejecutivo entre red, mercado y altas. Se excluyen los códigos 112011, 111981, 112041, 251201 y 251628.</div>', unsafe_allow_html=True)
    if not business_metrics.get("available", False):
        st.warning(business_metrics.get("message") or "No hay datos de negocio disponibles para la muestra actual.")
    st.markdown('</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5, m6 = st.columns(6, gap="medium")
    with m1:
        value = fmt_pct(leader_market["Cuota_mercado_global"]) if leader_market is not None else "N/D"
        st.markdown(f'<div class="card"><div class="kpi-label">Cuota de mercado líder</div><div class="metric-operator" style="color:{OPERATOR_COLORS.get(leader_market["Operador"], "#FFFFFF") if leader_market is not None else "#FFFFFF"};">{leader_market["Operador"] if leader_market is not None else "N/D"}</div><div class="kpi-sub">{value}</div></div>', unsafe_allow_html=True)
    with m2:
        value = fmt_pct(leader_altas["Participacion_altas_global"]) if leader_altas is not None else "N/D"
        st.markdown(f'<div class="card"><div class="kpi-label">Participación altas líder</div><div class="metric-operator" style="color:{OPERATOR_COLORS.get(leader_altas["Operador"], "#FFFFFF") if leader_altas is not None else "#FFFFFF"};">{leader_altas["Operador"] if leader_altas is not None else "N/D"}</div><div class="kpi-sub">{value}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="card"><div class="kpi-label">Variación mes 1 vs mes 12 mercado</div><div class="kpi-value">{fmt_pct(business_metrics.get("variation_market"))}</div><div class="kpi-sub">Promedio visible entre primer y último mes.</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="card"><div class="kpi-label">Variación mes 1 vs mes 12 altas</div><div class="kpi-value">{fmt_pct(business_metrics.get("variation_altas"))}</div><div class="kpi-sub">Promedio visible entre primer y último mes.</div></div>', unsafe_allow_html=True)
    with m5:
        st.markdown(f'<div class="card"><div class="kpi-label">RSRP mediano</div><div class="kpi-value">{fmt_dBm(global_median)}</div><div class="kpi-sub">Base técnica para el cruce comercial.</div></div>', unsafe_allow_html=True)
    with m6:
        st.markdown(f'<div class="card"><div class="kpi-label">Cobertura buena o mejor</div><div class="kpi-value">{fmt_pct(pct_good)}</div><div class="kpi-sub">Lectura de red sobre la muestra actual.</div></div>', unsafe_allow_html=True)

    mt1, mt2 = st.columns((1, 1), gap="large")
    with mt1:
        st.markdown('<div class="section-card"><div class="section-title">Mercado por operador</div><div class="section-subtitle">Barras de cuota de mercado visible por operador.</div>', unsafe_allow_html=True)
        if not market_operator.empty:
            market_chart = alt.Chart(market_operator).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Operador:N", sort="-y", title=None),
                y=alt.Y("Cuota_mercado_global:Q", title="Cuota mercado (%)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=None),
                tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("Mercado_total:Q", format=",.1f"), alt.Tooltip("Cuota_mercado_global:Q", format=".1f")],
            ).properties(height=340)
            st.altair_chart(market_chart, use_container_width=True)
        else:
            st.info("No se encontraron datos de mercado.")
        st.markdown('</div>', unsafe_allow_html=True)
    with mt2:
        st.markdown('<div class="section-card"><div class="section-title">Altas por operador</div><div class="section-subtitle">Barras de participación de altas visible por operador.</div>', unsafe_allow_html=True)
        if not altas_operator.empty:
            altas_chart = alt.Chart(altas_operator).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Operador:N", sort="-y", title=None),
                y=alt.Y("Participacion_altas_global:Q", title="Participación altas (%)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=None),
                tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("Altas_total:Q", format=",.1f"), alt.Tooltip("Participacion_altas_global:Q", format=".1f")],
            ).properties(height=340)
            st.altair_chart(altas_chart, use_container_width=True)
        else:
            st.info("No se encontraron datos de altas.")
        st.markdown('</div>', unsafe_allow_html=True)

    mt3, mt4 = st.columns((1, 1), gap="large")
    with mt3:
        st.markdown('<div class="section-card"><div class="section-title">Evolución temporal de mercado</div><div class="section-subtitle">Tendencia mensual por operador.</div>', unsafe_allow_html=True)
        if not market_time.empty:
            market_time_chart = alt.Chart(market_time).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X("Periodo_Mes:T", title="Mes", axis=alt.Axis(format="%b %Y", labelAngle=0)),
                y=alt.Y("Cuota_mercado:Q", title="Cuota mercado (%)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=alt.Legend(title="Operador")),
                tooltip=[alt.Tooltip("Periodo_Mes:T"), alt.Tooltip("Operador:N"), alt.Tooltip("Cuota_mercado:Q", format=".1f")],
            ).properties(height=340).interactive()
            st.altair_chart(market_time_chart, use_container_width=True)
        else:
            st.info("No se detectó evolución temporal de mercado.")
        st.markdown('</div>', unsafe_allow_html=True)
    with mt4:
        st.markdown('<div class="section-card"><div class="section-title">Evolución temporal de altas</div><div class="section-subtitle">Tendencia mensual por operador.</div>', unsafe_allow_html=True)
        if not altas_time.empty:
            altas_time_chart = alt.Chart(altas_time).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X("Periodo_Mes:T", title="Mes", axis=alt.Axis(format="%b %Y", labelAngle=0)),
                y=alt.Y("Participacion_altas:Q", title="Participación altas (%)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=alt.Legend(title="Operador")),
                tooltip=[alt.Tooltip("Periodo_Mes:T"), alt.Tooltip("Operador:N"), alt.Tooltip("Participacion_altas:Q", format=".1f")],
            ).properties(height=340).interactive()
            st.altair_chart(altas_time_chart, use_container_width=True)
        else:
            st.info("No se detectó evolución temporal de altas.")
        st.markdown('</div>', unsafe_allow_html=True)

    mt5, mt6 = st.columns((1, 1), gap="large")
    with mt5:
        st.markdown('<div class="section-card"><div class="section-title">Scatter red vs mercado</div><div class="section-subtitle">X = RSRP mediano | Y = cuota de mercado.</div>', unsafe_allow_html=True)
        if not scatter_df.empty:
            scatter = alt.Chart(scatter_df).mark_circle(size=180, opacity=0.85).encode(
                x=alt.X("RSRP_mediana:Q", title="RSRP mediano (dBm)"),
                y=alt.Y("Cuota_mercado_global:Q", title="Cuota mercado (%)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values()))),
                tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("RSRP_mediana:Q", format=".1f"), alt.Tooltip("Cuota_mercado_global:Q", format=".1f"), alt.Tooltip("Participacion_altas_global:Q", format=".1f")],
            ).properties(height=340)
            st.altair_chart(scatter, use_container_width=True)
        else:
            st.info("No hay datos suficientes para el scatter de red vs mercado.")
        st.markdown('</div>', unsafe_allow_html=True)
    with mt6:
        st.markdown('<div class="section-card"><div class="section-title">Cruce red vs negocio por operador</div><div class="section-subtitle">Incluye gaps frente a mercado y captación.</div>', unsafe_allow_html=True)
        if not cross_operator.empty:
            cross_show = safe_round_columns(cross_operator.copy(), ["RSRP_mediana", "Buena_o_mejor", "Critica", "Cuota_mercado_global", "Participacion_altas_global", "Gap_red_vs_mercado", "Gap_red_vs_captacion"])
            st.dataframe(cross_show, use_container_width=True, height=340)
        else:
            st.info("No hay datos suficientes para el cruce operador.")
        st.markdown('</div>', unsafe_allow_html=True)

    mt7, mt8 = st.columns((1, 1), gap="large")
    with mt7:
        st.markdown('<div class="section-card"><div class="section-title">Zonas de riesgo</div><div class="section-subtitle">Mala red + alta cuota de mercado.</div>', unsafe_allow_html=True)
        if not risk_table.empty:
            risk_show = safe_round_columns(risk_table.copy(), ["Cuota_mercado", "Participacion_altas", "RSRP_mediana", "Buena_o_mejor"])
            st.dataframe(risk_show, use_container_width=True, height=360)
        else:
            st.info("No se identificaron zonas de riesgo con los filtros actuales.")
        st.markdown('</div>', unsafe_allow_html=True)
    with mt8:
        st.markdown('<div class="section-card"><div class="section-title">Zonas de oportunidad</div><div class="section-subtitle">Buena red + baja cuota de mercado.</div>', unsafe_allow_html=True)
        if not opportunity_table.empty:
            opp_show = safe_round_columns(opportunity_table.copy(), ["Cuota_mercado", "Participacion_altas", "RSRP_mediana", "Buena_o_mejor"])
            st.dataframe(opp_show, use_container_width=True, height=360)
        else:
            st.info("No se identificaron zonas de oportunidad con los filtros actuales.")
        st.markdown('</div>', unsafe_allow_html=True)

# PIE
st.markdown(
    f"""
    <div class="small-caption">
        Nota metodológica: se consideran mediciones válidas únicamente valores negativos de RSRP. La clasificación aplicada es:
        Excelente (≥ -70 dBm), Buena (-80 a -70 dBm), Aceptable (-90 a -80 dBm) y Crítica (&lt; -90 dBm).
        La variación ejecutiva compara la mediana del primer y del último periodo disponible según el nivel temporal seleccionado ({nivel_temporal_variacion}).
        La lectura de Mercado y Captación se construye únicamente si el dataset contiene columnas detectables para estas métricas.
    </div>
    """,
    unsafe_allow_html=True,
)