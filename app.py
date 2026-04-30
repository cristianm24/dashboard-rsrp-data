import os
import io
import re
import unicodedata
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

# =========================================================
# ORGANIZACION DEL ARCHIVO
# 1. Imports y configuracion
# 2. Constantes, estilos y helpers UI
# 3. Funciones de carga, limpieza y calculo
# 4. Filtros y agregados
# 5. Render del dashboard
# =========================================================


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
DASHBOARD_TITLE = "Panel Ejecutivo de Desempeño de Red y Mercado - Prototipo"

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

MARKET_FILE_CANDIDATES = [
    os.path.join(BASE_DIR, "Cuota_mercado_completo.xlsx"),
    os.path.join(BASE_DIR, "Cuota_mercado_completo(1).xlsx"),
    os.path.join(BASE_DIR, "Cuota_mercado_completo(2).xlsx"),
]

ALTAS_FILE_CANDIDATES = [
    os.path.join(BASE_DIR, "Cuota_alta_completo.xlsx"),
    os.path.join(BASE_DIR, "Cuota_alta_completo(1).xlsx"),
    os.path.join(BASE_DIR, "Cuota_alta_completo(2).xlsx"),
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
    "Others": "#64748B",
    "Virgin Mobile": "#14B8A6",
}

QUALITY_COLORS = {
    "Excelente": "#22C55E",
    "Buena": "#84CC16",
    "Aceptable": "#F59E0B",
    "Crítica": "#EF4444",
    "Sin medición": "#64748B",
}

# =========================================================
# ESTILOS
# =========================================================
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: radial-gradient(circle at 12% 18%, rgba(225,6,0,0.10), transparent 22%), radial-gradient(circle at 88% 82%, rgba(56,189,248,0.10), transparent 24%), linear-gradient(135deg, #020817 0%, #041225 44%, #03111d 100%) !important;
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
    max-width: 1620px;
    padding-top: 1.0rem !important;
    padding-bottom: 3rem !important;
}
div[data-testid="stHorizontalBlock"] {
    gap: 1rem !important;
    align-items: stretch !important;
    margin-bottom: 0.35rem !important;
}
div[data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 0.9rem !important;
}
div[data-testid="column"] > div {
    height: auto !important;
    width: 100% !important;
}
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="column"]) {
    gap: 0.9rem !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(11,19,35,0.98) 0%, rgba(8,16,29,0.98) 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] * { color: #E5E7EB !important; }
.header-shell, .kpi-strip, .section-card, .card, .mini-card, .insight-card, .territory-card, .alert-card, .rule-card, .business-hero, .business-kpi {
    border-radius: 20px;
    padding: 16px 16px 14px 16px;
    min-height: 132px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: linear-gradient(180deg, rgba(17,24,39,0.96) 0%, rgba(15,23,42,0.96) 100%) !important;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 12px 28px rgba(0,0,0,0.18);
    transition: transform .20s ease, box-shadow .20s ease, border-color .20s ease;
}
.card:hover, .mini-card:hover, .section-card:hover, .insight-card:hover, .territory-card:hover, .alert-card:hover, .rule-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 40px rgba(0,0,0,0.24);
    border-color: rgba(255,255,255,0.14);
}
.header-shell {
    position: relative;
    overflow: hidden;
    border-radius: 30px;
    padding: 26px 28px 22px 28px;
    margin-bottom: 14px;
    background:
        radial-gradient(circle at top left, rgba(225,6,0,0.18), transparent 34%),
        radial-gradient(circle at bottom right, rgba(56,189,248,0.14), transparent 34%),
        linear-gradient(135deg, rgba(17,24,39,0.99) 0%, rgba(10,17,31,0.99) 55%, rgba(18,32,58,0.99) 100%) !important;
}
.header-shell::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, rgba(255,255,255,0.05), transparent 28%, transparent 72%, rgba(255,255,255,0.03));
    pointer-events: none;
}
.header-shell::after {
    content: "";
    position: absolute;
    left: 28px;
    right: 28px;
    bottom: 0;
    height: 3px;
    border-radius: 999px;
    background: linear-gradient(90deg, #E10600 0%, #38BDF8 100%);
    opacity: 0.95;
}
.kpi-strip {
    position: relative;
    overflow: hidden;
    border-radius: 22px;
    padding: 12px 14px 10px 14px;
    margin-bottom: 16px;
    background:
        linear-gradient(180deg, rgba(14,22,40,0.98) 0%, rgba(10,18,34,0.98) 100%) !important;
}
.kpi-strip::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.035), transparent 36%, transparent 68%, rgba(255,255,255,0.02));
    pointer-events: none;
}
.section-card {
    border-radius: 24px;
    padding: 20px 20px 16px 20px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
}
.card {
    border-radius: 18px;
    padding: 16px 16px 14px 16px;
    min-height: 138px;
    margin-bottom: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.mini-card {
    border-radius: 18px;
    padding: 14px 15px 12px 15px;
    min-height: 116px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.insight-card, .territory-card, .alert-card, .rule-card {
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 14px;
    min-height: 130px;
}
.insight-card {
    background: linear-gradient(135deg, rgba(225,6,0,0.08), rgba(56,189,248,0.08), rgba(17,24,39,0.98));
    border: 1px solid rgba(255,255,255,0.10);
}
.insight-title {
    display:inline-flex;
    align-items:center;
    gap:8px;
}
.insight-title::before {
    content: "";
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: linear-gradient(180deg, #E10600, #38BDF8);
    box-shadow: 0 0 12px rgba(56,189,248,0.28);
}
.section-title { font-size: 1.05rem; font-weight: 800; margin-bottom: 0.32rem; letter-spacing: 0.1px; }
.section-subtitle { font-size: 0.84rem; color: #CBD5E1 !important; margin-bottom: 1rem; line-height: 1.55; max-width: 95%; }
.kpi-label { font-size: 0.79rem; color: #CBD5E1 !important; margin-bottom: 0.3rem; font-weight: 700; }
.kpi-value { font-size: 1.72rem; font-weight: 800; line-height: 1.08; }
.kpi-sub { font-size: 0.79rem; color: #94A3B8 !important; margin-top: 0.45rem; line-height: 1.45; }
.metric-operator { font-size: 1.16rem; font-weight: 800; line-height: 1.2; }
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
div[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}
div[data-testid="column"] > div {
    height: 100%;
}
div[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
    margin-top: 8px;
}
.small-caption { font-size: 0.76rem; color: #94A3B8 !important; }

.dashboard-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.16) 50%, transparent 100%);
    margin: 8px 0 14px 0;
}
.executive-note {
    border-radius: 20px;
    padding: 18px 18px 16px 18px;
    background: linear-gradient(135deg, rgba(17,24,39,0.98) 0%, rgba(15,23,42,0.96) 50%, rgba(9,18,35,0.96) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 12px 28px rgba(0,0,0,0.18);
    margin-bottom: 14px;
}
.executive-highlight {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(56,189,248,0.12);
    border: 1px solid rgba(56,189,248,0.22);
    color: #BAE6FD;
    font-size: 0.76rem;
    font-weight: 700;
    margin-bottom: 10px;
}

.alert-card { min-height: 132px; }
.section-card { height: auto; }
.business-hero {
    border-radius: 24px;
    padding: 20px 22px;
    margin-bottom: 10px;
    border-radius: 24px;
    padding: 18px 20px;
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
}
.business-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, rgba(225,6,0,0.10), rgba(56,189,248,0.08), rgba(168,85,247,0.10));
    pointer-events: none;
}
.business-kpi {
    border-radius: 18px;
    padding: 18px 18px 16px 18px;
    min-height: 154px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border-radius: 20px;
    padding: 20px;
    min-height: 160px;
    position: relative;
    overflow: hidden;
}
.business-kpi::after {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, #E10600, #38BDF8);
    opacity: 0.9;
}
.panel-divider {
    height: 1px;
    width: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.14), transparent);
    margin: 6px 0 18px 0;
}

[data-testid="stVegaLiteChart"] canvas,
[data-testid="stVegaLiteChart"] svg {
    background: transparent !important;
}


.section-card::before, .card::before, .mini-card::before, .business-hero::before, .business-kpi::before {
    content: "";
    position: absolute;
    top: 0;
    left: 18px;
    right: 18px;
    height: 1px;
    background: linear-gradient(90deg, rgba(225,6,0,0), rgba(225,6,0,0.50), rgba(56,189,248,0));
}
.section-card::after, .card::after, .mini-card::after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    right: -100px;
    top: -100px;
    background: radial-gradient(circle, rgba(56,189,248,0.08) 0%, transparent 72%);
    pointer-events: none;
}


.sidebar-block {
    background: linear-gradient(180deg, rgba(17,24,39,0.80) 0%, rgba(15,23,42,0.88) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 14px 14px 12px 14px;
    margin-bottom: 12px;
    box-shadow: 0 8px 22px rgba(0,0,0,0.16);
}
.sidebar-title {
    font-size: 0.83rem;
    font-weight: 800;
    letter-spacing: 0.3px;
    color: #F8FAFC;
    margin-bottom: 4px;
}
.sidebar-sub {
    font-size: 0.74rem;
    color: #94A3B8;
    line-height: 1.45;
    margin-bottom: 10px;
}
.executive-ribbon {
    display:flex;
    flex-wrap:wrap;
    gap:8px;
    margin: 2px 0 16px 0;
}
.executive-ribbon .pill {
    background: rgba(255,255,255,0.05);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:999px;
    padding:6px 11px;
    font-size:0.77rem;
    color:#CBD5E1;
}
[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"],
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"],
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stDateInput input {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 10px !important;
}


.story-grid {
    display:grid;
    grid-template-columns: repeat(3, minmax(0,1fr));
    gap:12px;
    margin: 0 0 16px 0;
}
.story-mini {
    background: linear-gradient(180deg, rgba(19,29,47,0.98) 0%, rgba(15,23,42,0.98) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 14px 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.14);
}
.story-label {
    font-size: 0.73rem;
    color: #94A3B8;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .35px;
    margin-bottom: 5px;
}
.story-value {
    font-size: 1.08rem;
    color: #F8FAFC;
    font-weight: 800;
    line-height: 1.2;
}
.story-sub {
    font-size: 0.80rem;
    color: #CBD5E1;
    line-height: 1.45;
    margin-top: 6px;
}
.visual-note {
    background: linear-gradient(135deg, rgba(225,6,0,0.10), rgba(56,189,248,0.08));
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 16px;
}
.visual-note-title {
    font-size: .80rem;
    text-transform: uppercase;
    letter-spacing: .35px;
    font-weight: 800;
    color: #E2E8F0;
    margin-bottom: 8px;
}
.visual-note-body {
    font-size: .90rem;
    color: #F8FAFC;
    line-height: 1.58;
}
.legend-strip {
    display:flex;
    flex-wrap:wrap;
    gap:8px;
    margin: 0 0 14px 0;
}
.legend-pill {
    display:inline-flex;
    align-items:center;
    gap:8px;
    background: rgba(255,255,255,0.04);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:999px;
    padding:6px 10px;
    color:#CBD5E1;
    font-size:.75rem;
}
.legend-dot {
    width:10px;
    height:10px;
    border-radius:50%;
    display:inline-block;
}


.hero-badge {
    display:inline-flex;
    align-items:center;
    gap:8px;
    background: rgba(255,255,255,0.06);
    border:1px solid rgba(255,255,255,0.10);
    border-radius:999px;
    padding:7px 12px;
    font-size:.75rem;
    color:#E2E8F0;
    font-weight:800;
    margin-bottom:12px;
}
.hero-title {
    font-size:2.28rem;
    color:#FFFFFF;
    font-weight:950;
    line-height:1.02;
    letter-spacing:-0.03em;
    margin-top:8px;
}
.hero-subtitle {
    font-size:0.88rem;
    color:#CBD5E1;
    line-height:1.58;
    margin-top:10px;
    max-width:980px;
}
.hero-meta {
    display:flex;
    flex-wrap:wrap;
    gap:10px;
    margin-top:14px;
}
.hero-meta-pill {
    display:inline-flex;
    align-items:center;
    gap:8px;
    background: rgba(255,255,255,0.04);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:999px;
    padding:7px 11px;
    font-size:.76rem;
    color:#CBD5E1;
}
.header-status-card {
    border-radius:18px;
    padding:14px 14px 12px 14px;
    background: linear-gradient(180deg, rgba(17,24,39,0.94), rgba(15,23,42,0.94));
    border:1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 24px rgba(0,0,0,0.16);
    margin-bottom:10px;
}
.header-status-label {
    font-size:.72rem;
    text-transform:uppercase;
    letter-spacing:.4px;
    color:#94A3B8;
    font-weight:800;
    margin-bottom:6px;
}
.header-status-value {
    font-size:1.18rem;
    font-weight:900;
    color:#F8FAFC;
    line-height:1.15;
}
.header-status-sub {
    font-size:.78rem;
    color:#A8B3C7;
    margin-top:6px;
}
.kpi-strip-title {
    display:inline-flex;
    align-items:center;
    gap:8px;
    font-size:.72rem;
    font-weight:800;
    color:#E2E8F0;
    margin-bottom:10px;
    text-transform:uppercase;
    letter-spacing:.45px;
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 999px;
    padding: 6px 10px;
}
.kpi-strip-title::before {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: linear-gradient(180deg, #E10600, #38BDF8);
    box-shadow: 0 0 10px rgba(56,189,248,0.35);
}
.card {
    position: relative;
    border-radius: 20px;
}
.card::after {
    content: "";
    position: absolute;
    top: 0;
    left: 18px;
    right: 18px;
    height: 3px;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(225,6,0,0.95), rgba(56,189,248,0.75));
}
.mini-card {
    position: relative;
    border-radius: 20px;
}
.mini-card::after {
    content: "";
    position: absolute;
    top: 0;
    left: 16px;
    right: 16px;
    height: 2px;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(225,6,0,0.85), rgba(56,189,248,0.65));
}
.kpi-label { font-size: 0.72rem; color: #94A3B8 !important; margin-bottom: 0.36rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.42px; }
.kpi-value { font-size: 1.82rem; font-weight: 900; line-height: 1.03; letter-spacing: -0.02em; }
.metric-operator { font-size: 1.24rem; font-weight: 900; line-height: 1.12; letter-spacing: -0.01em; }
.kpi-sub { font-size: 0.78rem; color: #A8B3C7 !important; margin-top: 0.5rem; line-height: 1.48; }


.icon-inline { display:inline-flex; align-items:center; justify-content:center; color:#E2E8F0; vertical-align:middle; flex:0 0 auto; }
.icon-inline svg { width:100%; height:100%; }
.user-guide-band { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin: 0 0 14px 0; }
.guide-pill { display:inline-flex; align-items:center; gap:8px; padding:7px 11px; border-radius:999px; background: rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); color:#CBD5E1; font-size:.76rem; font-weight:700; }
.flow-guide { display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:10px; margin: 0 0 14px 0; }
.flow-step { background: linear-gradient(180deg, rgba(18,27,46,0.92) 0%, rgba(15,23,42,0.92) 100%); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:12px 13px; box-shadow: 0 8px 18px rgba(0,0,0,0.12); }
.flow-step-head { display:flex; align-items:center; gap:8px; font-size:.73rem; color:#E2E8F0; font-weight:800; text-transform:uppercase; letter-spacing:.35px; margin-bottom:6px; }
.flow-step-text { font-size:.80rem; color:#CBD5E1; line-height:1.46; }
.anchor-note { display:flex; align-items:flex-start; gap:10px; background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:12px 14px; margin-bottom: 12px; }
.anchor-note-body { font-size:.82rem; color:#CBD5E1; line-height:1.52; }
.mini-legend-grid { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:8px; margin: 0 0 12px 0; }
.mini-legend-card { background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:10px 11px; }
.mini-legend-title { font-size:.70rem; color:#94A3B8; font-weight:800; text-transform:uppercase; letter-spacing:.35px; margin-bottom:4px; }
.mini-legend-text { font-size:.78rem; color:#E2E8F0; line-height:1.42; }
.nav-chip-row { display:flex; flex-wrap:wrap; gap:8px; margin: 0 0 10px 0; }
.nav-chip { display:inline-flex; align-items:center; gap:8px; border-radius:999px; padding:6px 10px; font-size:.73rem; font-weight:700; color:#E2E8F0; background: rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); }

.sidebar-guide-row {
    display:flex;
    flex-wrap:wrap;
    gap:8px;
    margin: 0 0 12px 0;
}
.sidebar-guide-pill {
    display:inline-flex;
    align-items:center;
    gap:8px;
    padding:6px 10px;
    border-radius:999px;
    background: rgba(255,255,255,0.045);
    border:1px solid rgba(255,255,255,0.08);
    color:#CBD5E1;
    font-size:.73rem;
    font-weight:700;
}
.sidebar-kicker {
    display:inline-flex;
    align-items:center;
    gap:8px;
    padding:6px 10px;
    border-radius:999px;
    background: linear-gradient(90deg, rgba(225,6,0,0.14), rgba(56,189,248,0.10));
    border:1px solid rgba(255,255,255,0.10);
    color:#F8FAFC;
    font-size:.73rem;
    font-weight:800;
    margin-bottom:10px;
}
.sidebar-operator-card {
    background: linear-gradient(180deg, rgba(17,24,39,0.86) 0%, rgba(15,23,42,0.92) 100%);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:16px;
    padding:10px 12px 9px 12px;
    min-height:74px;
    box-shadow: 0 8px 18px rgba(0,0,0,0.12);
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
    margin-bottom: 6px;
}
.sidebar-operator-card:hover {
    transform: translateY(-1px);
    border-color: rgba(255,255,255,0.14);
    box-shadow: 0 12px 24px rgba(0,0,0,0.16);
}
.sidebar-operator-chip {
    display:inline-flex;
    align-items:center;
    gap:8px;
    padding:5px 9px;
    border-radius:999px;
    font-size:.70rem;
    font-weight:800;
    color:#F8FAFC;
    margin-bottom:8px;
    width: fit-content;
}
.sidebar-operator-label {
    font-size:.88rem;
    color:#F8FAFC;
    font-weight:800;
    line-height:1.28;
}
.sidebar-operator-sub {
    font-size:.72rem;
    color:#94A3B8;
    line-height:1.4;
    margin-top:4px;
}
.sidebar-soft-note {
    font-size:.73rem;
    color:#A8B3C7;
    line-height:1.48;
    margin: 8px 0 10px 0;
}
.filter-stage {
    display:grid;
    grid-template-columns: repeat(3, minmax(0,1fr));
    gap:8px;
    margin: 0 0 12px 0;
}
.filter-stage-card {
    background: rgba(255,255,255,0.04);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:14px;
    padding:9px 10px;
}
.filter-stage-title {
    font-size:.68rem;
    color:#94A3B8;
    font-weight:800;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin-bottom:4px;
}
.filter-stage-text {
    font-size:.76rem;
    color:#E2E8F0;
    line-height:1.4;
}
.filter-divider {
    height:1px;
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.14) 50%, transparent 100%);
    margin: 8px 0 12px 0;
}

.context-badge-row {
    display:flex;
    flex-wrap:wrap;
    gap:8px;
    margin:8px 0 12px 0;
}
.context-badge {
    display:inline-flex;
    align-items:center;
    gap:6px;
    padding:6px 10px;
    border-radius:999px;
    background:rgba(255,255,255,0.055);
    border:1px solid rgba(255,255,255,0.09);
    color:#CBD5E1;
    font-size:.74rem;
    font-weight:700;
}
.context-badge b { color:#F8FAFC; }
.sync-warning {
    display:flex;
    gap:10px;
    align-items:flex-start;
    background:linear-gradient(135deg, rgba(245,158,11,0.13), rgba(225,6,0,0.08));
    border:1px solid rgba(245,158,11,0.22);
    border-radius:18px;
    padding:13px 15px;
    margin:0 0 14px 0;
}
.sync-warning-title {
    font-size:.78rem;
    color:#FCD34D;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin-bottom:4px;
}
.sync-warning-body {
    color:#E2E8F0;
    font-size:.82rem;
    line-height:1.48;
}

/* ===== ORGANIZACION EJECUTIVA GLOBAL ===== */
[data-baseweb="tab-list"] {
    gap: 10px !important;
    background: linear-gradient(180deg, rgba(15,23,42,0.82), rgba(8,16,29,0.86)) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 24px !important;
    padding: 10px !important;
    margin: 18px 0 18px 0 !important;
    box-shadow: 0 14px 32px rgba(0,0,0,0.20);
    justify-content: center !important;
}
button[data-baseweb="tab"] {
    min-height: 44px !important;
    border-radius: 16px !important;
    transition: all .20s ease !important;
}
button[data-baseweb="tab"]:hover {
    transform: translateY(-1px);
    border-color: rgba(255,255,255,0.18) !important;
}
button[aria-selected="true"][data-baseweb="tab"] {
    background: linear-gradient(135deg, rgba(225,6,0,0.18), rgba(56,189,248,0.12)) !important;
    box-shadow: inset 0 -2px 0 #38BDF8, 0 8px 18px rgba(0,0,0,0.18) !important;
}
.exec-map {
    display:grid;
    grid-template-columns: repeat(5, minmax(0,1fr));
    gap:10px;
    margin: 10px 0 16px 0;
}
.exec-map-card {
    position:relative;
    overflow:hidden;
    border-radius:18px;
    padding:13px 13px 12px 13px;
    background: linear-gradient(180deg, rgba(17,24,39,0.88), rgba(15,23,42,0.94));
    border:1px solid rgba(255,255,255,0.08);
    min-height:92px;
    box-shadow: 0 10px 22px rgba(0,0,0,0.14);
}
.exec-map-card::before {
    content:"";
    position:absolute;
    left:12px;
    right:12px;
    top:0;
    height:2px;
    border-radius:999px;
    background: linear-gradient(90deg, rgba(225,6,0,0.9), rgba(56,189,248,0.7));
}
.exec-map-title {
    display:flex;
    align-items:center;
    gap:8px;
    font-size:.76rem;
    color:#F8FAFC;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.28px;
    margin-bottom:6px;
}
.exec-map-text {
    font-size:.76rem;
    color:#A8B3C7;
    line-height:1.45;
}
.stage-header {
    position:relative;
    overflow:hidden;
    border-radius:22px;
    padding:16px 18px;
    margin: 0 0 14px 0;
    background:
        radial-gradient(circle at top left, rgba(225,6,0,0.12), transparent 34%),
        linear-gradient(135deg, rgba(17,24,39,0.96), rgba(12,22,40,0.96));
    border:1px solid rgba(255,255,255,0.09);
    box-shadow: 0 12px 26px rgba(0,0,0,0.16);
}
.stage-kicker {
    display:inline-flex;
    align-items:center;
    gap:8px;
    color:#BAE6FD;
    background: rgba(56,189,248,0.10);
    border:1px solid rgba(56,189,248,0.18);
    border-radius:999px;
    padding:5px 10px;
    font-size:.72rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin-bottom:8px;
}
.stage-title {
    font-size:1.16rem;
    color:#F8FAFC;
    font-weight:950;
    letter-spacing:-.01em;
    line-height:1.18;
}
.stage-subtitle {
    margin-top:6px;
    font-size:.86rem;
    color:#CBD5E1;
    line-height:1.52;
    max-width:1050px;
}
.content-lane {
    border-radius:24px;
    padding:12px 12px 4px 12px;
    margin: 0 0 14px 0;
    background: rgba(255,255,255,0.018);
    border:1px solid rgba(255,255,255,0.045);
}
.lane-label {
    display:flex;
    align-items:center;
    gap:8px;
    color:#94A3B8;
    font-size:.72rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin: 0 0 10px 4px;
}
.decision-strip {
    display:grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap:10px;
    margin: 0 0 14px 0;
}
.decision-card {
    border-radius:16px;
    padding:12px 13px;
    background: linear-gradient(180deg, rgba(15,23,42,0.90), rgba(15,23,42,0.74));
    border:1px solid rgba(255,255,255,0.08);
}
.decision-label {
    font-size:.70rem;
    font-weight:900;
    color:#94A3B8;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin-bottom:5px;
}
.decision-text {
    color:#F8FAFC;
    font-size:.82rem;
    line-height:1.45;
}
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 18px !important;
    background: rgba(15,23,42,0.55) !important;
    overflow:hidden;
}
[data-testid="stExpander"] summary {
    color:#E2E8F0 !important;
    font-weight:800 !important;
}
@media (max-width: 1200px) {
    .exec-map { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .decision-strip { grid-template-columns: 1fr; }
}


/* =========================================================
   REDISEÑO VISUAL V31 - LENGUAJE EJECUTIVO MAS EVIDENTE
   ========================================================= */

:root {
    --glass: rgba(15,23,42,0.78);
    --glass-strong: rgba(15,23,42,0.94);
    --line: rgba(255,255,255,0.09);
    --muted: #94A3B8;
    --text: #F8FAFC;
    --cyan: #38BDF8;
    --red: #E10600;
}

.block-container {
    padding-top: 0.65rem !important;
}

.header-shell {
    min-height: auto !important;
    padding: 24px 28px !important;
    border-radius: 32px !important;
    background:
        radial-gradient(circle at 6% 10%, rgba(225,6,0,0.26), transparent 34%),
        radial-gradient(circle at 92% 75%, rgba(56,189,248,0.22), transparent 36%),
        linear-gradient(135deg, rgba(5,12,28,0.98), rgba(9,20,41,0.98) 52%, rgba(5,31,48,0.98)) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    box-shadow: 0 24px 70px rgba(0,0,0,0.36), inset 0 1px 0 rgba(255,255,255,0.06) !important;
}

.hero-title {
    font-size: 2.55rem !important;
    max-width: 980px;
}

.hero-badge {
    background: linear-gradient(90deg, rgba(225,6,0,0.22), rgba(56,189,248,0.12)) !important;
    border-color: rgba(255,255,255,0.14) !important;
}

.header-status-card {
    border-radius: 22px !important;
    min-height: 116px !important;
    background:
        radial-gradient(circle at top right, rgba(56,189,248,0.12), transparent 46%),
        linear-gradient(180deg, rgba(17,24,39,0.92), rgba(8,16,29,0.92)) !important;
}

.executive-ribbon {
    padding: 10px !important;
    border-radius: 22px !important;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
}

.executive-ribbon .pill {
    padding: 8px 12px !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.035)) !important;
}

.kpi-strip {
    padding: 16px !important;
    border-radius: 30px !important;
    background:
        radial-gradient(circle at 3% 0%, rgba(225,6,0,0.14), transparent 34%),
        radial-gradient(circle at 90% 100%, rgba(56,189,248,0.14), transparent 34%),
        linear-gradient(180deg, rgba(15,23,42,0.92), rgba(8,16,29,0.94)) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: 0 18px 48px rgba(0,0,0,0.30) !important;
}

.kpi-strip-title {
    margin-bottom: 14px !important;
}

.mini-card, .card {
    border-radius: 24px !important;
    background:
        radial-gradient(circle at top right, rgba(56,189,248,0.10), transparent 38%),
        linear-gradient(180deg, rgba(17,24,39,0.95), rgba(11,20,36,0.95)) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: 0 14px 34px rgba(0,0,0,0.22) !important;
}

.mini-card:hover, .card:hover, .section-card:hover {
    transform: translateY(-3px) !important;
    border-color: rgba(56,189,248,0.22) !important;
    box-shadow: 0 22px 54px rgba(0,0,0,0.32) !important;
}

.kpi-value {
    font-size: 1.95rem !important;
}

.metric-operator {
    font-size: 1.32rem !important;
}

.section-card, .business-hero, .executive-note, .visual-note {
    border-radius: 28px !important;
    background:
        radial-gradient(circle at top left, rgba(225,6,0,0.07), transparent 32%),
        radial-gradient(circle at bottom right, rgba(56,189,248,0.08), transparent 30%),
        linear-gradient(180deg, rgba(17,24,39,0.92), rgba(10,18,34,0.96)) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: 0 16px 42px rgba(0,0,0,0.24) !important;
}

.section-title {
    font-size: 1.15rem !important;
}

.section-subtitle {
    max-width: 100% !important;
}

.story-grid {
    gap: 14px !important;
}

.story-mini {
    border-radius: 22px !important;
    min-height: 130px;
    padding: 16px !important;
    background:
        linear-gradient(180deg, rgba(18,29,51,0.95), rgba(10,18,34,0.95)) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
}

.story-value {
    font-size: 1.26rem !important;
}

.visual-note {
    padding: 18px 20px !important;
    border-left: 4px solid rgba(56,189,248,0.65) !important;
}

[data-baseweb="tab-list"] {
    position: sticky !important;
    top: 0.45rem !important;
    z-index: 50 !important;
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    gap: 10px !important;
    background:
        linear-gradient(180deg, rgba(3,10,24,0.90), rgba(8,16,29,0.92)) !important;
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 28px !important;
    padding: 12px !important;
    margin: 18px 0 22px 0 !important;
    box-shadow: 0 18px 55px rgba(0,0,0,0.34) !important;
}

button[data-baseweb="tab"] {
    width: 100% !important;
    min-height: 58px !important;
    border-radius: 20px !important;
    background:
        radial-gradient(circle at top left, rgba(255,255,255,0.045), transparent 42%),
        linear-gradient(180deg, rgba(17,24,39,0.92), rgba(15,23,42,0.88)) !important;
    font-weight: 850 !important;
}

button[aria-selected="true"][data-baseweb="tab"] {
    background:
        radial-gradient(circle at top left, rgba(225,6,0,0.22), transparent 40%),
        radial-gradient(circle at bottom right, rgba(56,189,248,0.18), transparent 40%),
        linear-gradient(180deg, rgba(30,41,59,0.98), rgba(15,23,42,0.98)) !important;
    border-color: rgba(56,189,248,0.32) !important;
    box-shadow: inset 0 -3px 0 #38BDF8, 0 12px 26px rgba(0,0,0,0.25) !important;
}

.exec-map {
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    margin: 14px 0 20px 0 !important;
}

.exec-map-card {
    min-height: 118px !important;
    border-radius: 24px !important;
    padding: 16px !important;
    background:
        radial-gradient(circle at top right, rgba(56,189,248,0.12), transparent 40%),
        linear-gradient(180deg, rgba(17,24,39,0.94), rgba(10,18,34,0.96)) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
}

.exec-map-card:hover {
    transform: translateY(-4px);
    border-color: rgba(56,189,248,0.22);
    box-shadow: 0 20px 44px rgba(0,0,0,0.28);
}

.exec-map-title {
    font-size: .82rem !important;
}

.exec-map-text {
    font-size: .80rem !important;
}

.stage-header {
    padding: 22px 24px !important;
    border-radius: 30px !important;
    background:
        radial-gradient(circle at 0% 0%, rgba(225,6,0,0.18), transparent 36%),
        radial-gradient(circle at 100% 100%, rgba(56,189,248,0.15), transparent 36%),
        linear-gradient(135deg, rgba(15,23,42,0.95), rgba(8,22,39,0.96)) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    box-shadow: 0 18px 46px rgba(0,0,0,0.26) !important;
}

.stage-title {
    font-size: 1.45rem !important;
}

.stage-subtitle {
    font-size: .93rem !important;
}

.decision-strip {
    grid-template-columns: 1.15fr 1fr 1fr !important;
    gap: 14px !important;
    margin: 0 0 18px 0 !important;
}

.decision-card {
    min-height: 112px;
    border-radius: 22px !important;
    padding: 16px !important;
    background:
        linear-gradient(180deg, rgba(17,24,39,0.88), rgba(10,18,34,0.92)) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: 0 12px 28px rgba(0,0,0,0.18);
}

.decision-card:first-child {
    background:
        radial-gradient(circle at top right, rgba(56,189,248,0.14), transparent 42%),
        linear-gradient(180deg, rgba(20,34,57,0.92), rgba(10,18,34,0.95)) !important;
    border-color: rgba(56,189,248,0.18) !important;
}

.content-lane {
    border-radius: 28px !important;
    padding: 16px 16px 6px 16px !important;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.028), rgba(255,255,255,0.012)) !important;
    border: 1px solid rgba(255,255,255,0.065) !important;
}

.user-guide-band {
    margin: 2px 0 16px 0 !important;
}

.guide-pill {
    padding: 9px 13px !important;
    border-radius: 999px !important;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.075), rgba(255,255,255,0.035)) !important;
}

.anchor-note {
    border-radius: 20px !important;
    background:
        linear-gradient(135deg, rgba(56,189,248,0.08), rgba(255,255,255,0.035)) !important;
}

.context-badge {
    padding: 7px 11px !important;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.070), rgba(255,255,255,0.035)) !important;
}

.sidebar-block {
    border-radius: 24px !important;
    box-shadow: 0 16px 36px rgba(0,0,0,0.24) !important;
}

.sidebar-operator-card {
    border-radius: 20px !important;
    min-height: 86px !important;
    background:
        radial-gradient(circle at top right, rgba(56,189,248,0.10), transparent 36%),
        linear-gradient(180deg, rgba(17,24,39,0.92), rgba(10,18,34,0.96)) !important;
}

@keyframes breatheGlow {
    0%, 100% { box-shadow: 0 0 0 rgba(56,189,248,0); }
    50% { box-shadow: 0 0 24px rgba(56,189,248,0.12); }
}
.stage-header, .kpi-strip, .header-shell {
    animation: breatheGlow 6s ease-in-out infinite;
}


.reading-band {
    display:grid;
    grid-template-columns: 1.2fr 1fr 1fr;
    gap:12px;
    margin: 0 0 16px 0;
}
.reading-card {
    position:relative;
    overflow:hidden;
    border-radius:24px;
    padding:16px 17px;
    min-height:108px;
    background:
        radial-gradient(circle at top right, rgba(56,189,248,0.12), transparent 42%),
        linear-gradient(180deg, rgba(17,24,39,0.90), rgba(10,18,34,0.94));
    border:1px solid rgba(255,255,255,0.10);
    box-shadow: 0 12px 34px rgba(0,0,0,0.20);
}
.reading-card:first-child {
    background:
        radial-gradient(circle at top left, rgba(225,6,0,0.16), transparent 38%),
        radial-gradient(circle at bottom right, rgba(56,189,248,0.13), transparent 38%),
        linear-gradient(180deg, rgba(20,34,57,0.92), rgba(10,18,34,0.96));
}
.reading-title {
    display:flex;
    align-items:center;
    gap:8px;
    font-size:.80rem;
    color:#F8FAFC;
    font-weight:950;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin-bottom:7px;
}
.reading-text {
    color:#CBD5E1;
    font-size:.84rem;
    line-height:1.50;
}
@media (max-width: 1200px) {
    .reading-band { grid-template-columns: 1fr; }
}


/* =========================================================
   V32 - ORGANIZACION PROFESIONAL Y LECTURA PROGRESIVA
   ========================================================= */

.compact-context-bar {
    display:grid;
    grid-template-columns: 1.25fr repeat(4, minmax(0, 1fr));
    gap:10px;
    margin: 0 0 16px 0;
}
.compact-context-main,
.compact-context-item {
    position:relative;
    overflow:hidden;
    border-radius:18px;
    padding:12px 13px;
    background:
        radial-gradient(circle at top right, rgba(56,189,248,0.10), transparent 42%),
        linear-gradient(180deg, rgba(17,24,39,0.86), rgba(10,18,34,0.92));
    border:1px solid rgba(255,255,255,0.09);
    box-shadow: 0 10px 24px rgba(0,0,0,0.16);
    min-height:74px;
}
.compact-context-main {
    background:
        radial-gradient(circle at top left, rgba(225,6,0,0.14), transparent 38%),
        radial-gradient(circle at bottom right, rgba(56,189,248,0.12), transparent 38%),
        linear-gradient(180deg, rgba(20,34,57,0.92), rgba(10,18,34,0.96));
}
.compact-context-label {
    display:flex;
    align-items:center;
    gap:7px;
    font-size:.68rem;
    color:#94A3B8;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin-bottom:5px;
}
.compact-context-value {
    color:#F8FAFC;
    font-size:1.02rem;
    font-weight:950;
    line-height:1.16;
}
.compact-context-sub {
    color:#A8B3C7;
    font-size:.72rem;
    line-height:1.35;
    margin-top:4px;
}

.page-flow-note {
    border-radius:22px;
    padding:14px 16px;
    margin: 0 0 16px 0;
    background:
        linear-gradient(135deg, rgba(56,189,248,0.08), rgba(255,255,255,0.025));
    border:1px solid rgba(255,255,255,0.08);
}
.page-flow-title {
    display:flex;
    align-items:center;
    gap:8px;
    font-size:.78rem;
    font-weight:950;
    color:#E2E8F0;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin-bottom:5px;
}
.page-flow-text {
    font-size:.82rem;
    color:#CBD5E1;
    line-height:1.5;
}

.tab-layout {
    display:grid;
    grid-template-columns: 1fr;
    gap:14px;
}
.tab-section {
    border-radius:28px;
    padding:14px 14px 4px 14px;
    background: rgba(255,255,255,0.018);
    border:1px solid rgba(255,255,255,0.055);
    margin-bottom:14px;
}
.tab-section-header {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    margin:0 0 12px 4px;
}
.tab-section-title {
    display:flex;
    align-items:center;
    gap:8px;
    color:#E2E8F0;
    font-size:.78rem;
    font-weight:950;
    text-transform:uppercase;
    letter-spacing:.38px;
}
.tab-section-hint {
    color:#94A3B8;
    font-size:.74rem;
    line-height:1.35;
    text-align:right;
}
.decision-strip {
    margin-bottom: 16px !important;
}
.stage-header {
    margin-top: 2px !important;
}
.exec-map {
    margin-top: 0 !important;
}
.kpi-strip {
    display:none !important;
}
.reading-band {
    display:none !important;
}
@media (max-width: 1200px) {
    .compact-context-bar {
        grid-template-columns: repeat(2, minmax(0,1fr));
    }
    .compact-context-main {
        grid-column: span 2;
    }
    .tab-section-header {
        align-items:flex-start;
        flex-direction:column;
    }
    .tab-section-hint {
        text-align:left;
    }
}


/* =========================================================
   V33 - RESUMEN KPI SUPERIOR COMPACTO
   ========================================================= */

.compact-context-bar {
    display:flex !important;
    align-items:stretch !important;
    gap:8px !important;
    margin: 0 0 12px 0 !important;
    padding: 8px !important;
    border-radius: 18px !important;
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    box-shadow: 0 10px 26px rgba(0,0,0,0.16) !important;
}
.compact-context-main,
.compact-context-item {
    min-height: 54px !important;
    padding: 8px 10px !important;
    border-radius: 14px !important;
    flex: 1 1 0 !important;
    background:
        linear-gradient(180deg, rgba(17,24,39,0.74), rgba(10,18,34,0.78)) !important;
    box-shadow: none !important;
}
.compact-context-main {
    flex: 1.35 1 0 !important;
    background:
        linear-gradient(135deg, rgba(225,6,0,0.10), rgba(56,189,248,0.07), rgba(10,18,34,0.78)) !important;
}
.compact-context-label {
    font-size: .61rem !important;
    margin-bottom: 3px !important;
    letter-spacing: .3px !important;
}
.compact-context-label .icon-inline {
    width: 10px !important;
    height: 10px !important;
}
.compact-context-value {
    font-size: .88rem !important;
    line-height: 1.05 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.compact-context-sub {
    font-size: .64rem !important;
    margin-top: 3px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.page-flow-note {
    padding: 10px 12px !important;
    border-radius: 16px !important;
    margin: 0 0 12px 0 !important;
}
.page-flow-title {
    font-size: .68rem !important;
    margin-bottom: 3px !important;
}
.page-flow-text {
    font-size: .74rem !important;
    line-height: 1.38 !important;
}
@media (max-width: 1200px) {
    .compact-context-bar {
        display:grid !important;
        grid-template-columns: repeat(2, minmax(0,1fr)) !important;
    }
    .compact-context-main {
        grid-column: span 2 !important;
    }
}


/* =========================================================
   V34 - DIAGNOSTICO INICIAL COMPACTO
   ========================================================= */

.tab-section:first-of-type {
    padding: 10px 12px !important;
    border-radius: 18px !important;
    margin-bottom: 10px !important;
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
}

.tab-section:first-of-type .section-card {
    padding: 10px !important;
    border-radius: 16px !important;
    box-shadow: none !important;
}

.tab-section:first-of-type .anchor-note {
    padding: 10px !important;
    border-radius: 14px !important;
}

.tab-section:first-of-type .section-title {
    font-size: 0.9rem !important;
}

.tab-section:first-of-type .section-subtitle {
    font-size: 0.75rem !important;
    line-height: 1.35 !important;
}


/* =========================================================
   V35 - REFINAMIENTO EJECUTIVO SIN DOBLE VISTA
   ========================================================= */

/* Barra superior como estado compacto, no como seccion */
.compact-context-bar {
    min-height: 42px !important;
    padding: 5px 6px !important;
    gap: 6px !important;
    border-radius: 14px !important;
    margin-bottom: 10px !important;
}
.compact-context-main,
.compact-context-item {
    min-height: 34px !important;
    padding: 5px 8px !important;
    border-radius: 10px !important;
}
.compact-context-label {
    font-size: .54rem !important;
    margin-bottom: 1px !important;
    letter-spacing: .25px !important;
}
.compact-context-label .icon-inline {
    width: 9px !important;
    height: 9px !important;
}
.compact-context-value {
    font-size: .76rem !important;
    line-height: 1.02 !important;
}
.compact-context-sub {
    display: none !important;
}
.page-flow-note {
    padding: 7px 9px !important;
    border-radius: 12px !important;
    margin-bottom: 10px !important;
}
.page-flow-title {
    font-size: .62rem !important;
    margin-bottom: 2px !important;
}
.page-flow-text {
    font-size: .68rem !important;
    line-height: 1.28 !important;
}

/* Diagnostico inicial como micro estado */
.tab-section:first-of-type {
    padding: 6px 8px !important;
    margin-bottom: 8px !important;
    border-radius: 12px !important;
}
.tab-section:first-of-type .tab-section-header {
    margin-bottom: 6px !important;
}
.tab-section:first-of-type .tab-section-title {
    font-size: .68rem !important;
}
.tab-section:first-of-type .tab-section-hint {
    font-size: .66rem !important;
}
.tab-section:first-of-type .section-card {
    padding: 8px !important;
    border-radius: 12px !important;
    min-height: auto !important;
}
.tab-section:first-of-type .section-title {
    font-size: .78rem !important;
}
.tab-section:first-of-type .section-subtitle {
    font-size: .68rem !important;
    line-height: 1.22 !important;
}
.tab-section:first-of-type .anchor-note {
    display: none !important;
}

/* KPI contextual de tab */
.tab-kpi-context {
    display: grid;
    grid-template-columns: 1.15fr 1fr 1fr;
    gap: 10px;
    margin: 0 0 14px 0;
}
.tab-kpi-card {
    position: relative;
    overflow: hidden;
    border-radius: 18px;
    padding: 13px 14px;
    min-height: 92px;
    background:
        radial-gradient(circle at top right, rgba(56,189,248,0.12), transparent 42%),
        linear-gradient(180deg, rgba(17,24,39,0.88), rgba(10,18,34,0.94));
    border: 1px solid rgba(255,255,255,0.09);
    box-shadow: 0 10px 24px rgba(0,0,0,0.16);
}
.tab-kpi-card:first-child {
    background:
        radial-gradient(circle at top left, rgba(225,6,0,0.14), transparent 40%),
        radial-gradient(circle at bottom right, rgba(56,189,248,0.12), transparent 40%),
        linear-gradient(180deg, rgba(20,34,57,0.92), rgba(10,18,34,0.96));
    border-color: rgba(56,189,248,0.18);
}
.tab-kpi-label {
    display:flex;
    align-items:center;
    gap:7px;
    font-size:.68rem;
    color:#94A3B8;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin-bottom:5px;
}
.tab-kpi-value {
    color:#F8FAFC;
    font-size:1.22rem;
    font-weight:950;
    line-height:1.1;
}
.tab-kpi-sub {
    color:#A8B3C7;
    font-size:.74rem;
    line-height:1.38;
    margin-top:5px;
}

/* Insights por tab */
.tab-insight {
    position: relative;
    overflow: hidden;
    border-radius: 18px;
    padding: 14px 15px;
    margin: 0 0 14px 0;
    background:
        linear-gradient(135deg, rgba(56,189,248,0.09), rgba(225,6,0,0.06), rgba(255,255,255,0.025));
    border: 1px solid rgba(255,255,255,0.09);
}
.tab-insight-title {
    display:flex;
    align-items:center;
    gap:8px;
    color:#F8FAFC;
    font-size:.78rem;
    font-weight:950;
    text-transform:uppercase;
    letter-spacing:.35px;
    margin-bottom:6px;
}
.tab-insight-body {
    color:#CBD5E1;
    font-size:.84rem;
    line-height:1.48;
}

/* Etiquetas de riesgo mas claras */
.risk-badge-row {
    display:flex;
    flex-wrap:wrap;
    gap:8px;
    margin: 0 0 12px 0;
}
.risk-badge {
    display:inline-flex;
    align-items:center;
    gap:7px;
    border-radius:999px;
    padding:7px 10px;
    font-size:.72rem;
    font-weight:850;
    border:1px solid rgba(255,255,255,0.10);
}
.risk-high { background:rgba(239,68,68,0.13); color:#FCA5A5; }
.risk-watch { background:rgba(245,158,11,0.13); color:#FCD34D; }
.risk-stable { background:rgba(34,197,94,0.13); color:#86EFAC; }
.risk-opportunity { background:rgba(56,189,248,0.13); color:#7DD3FC; }

/* Tablas mas premium */
.table-shell {
    position: relative;
    border-radius: 20px;
    padding: 12px;
    background:
        radial-gradient(circle at top right, rgba(56,189,248,0.10), transparent 36%),
        linear-gradient(180deg, rgba(17,24,39,0.70), rgba(10,18,34,0.78));
    border: 1px solid rgba(255,255,255,0.09);
    box-shadow: 0 12px 30px rgba(0,0,0,0.18);
    margin-top: 8px;
}
.table-shell::before {
    content: "";
    position: absolute;
    left: 14px;
    right: 14px;
    top: 0;
    height: 2px;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(225,6,0,0.85), rgba(56,189,248,0.75));
}
.table-toolbar {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:10px;
    margin-bottom:10px;
}
.table-title-mini {
    display:flex;
    align-items:center;
    gap:8px;
    color:#E2E8F0;
    font-size:.74rem;
    font-weight:950;
    text-transform:uppercase;
    letter-spacing:.35px;
}
.table-hint-mini {
    color:#94A3B8;
    font-size:.70rem;
    text-align:right;
}
div[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}
div[data-testid="stDataFrame"] div[role="grid"] {
    background: rgba(15,23,42,0.70) !important;
}

/* Mejor ritmo */
.tab-section {
    margin-bottom: 12px !important;
}
.decision-strip {
    margin-bottom: 12px !important;
}
.section-card {
    margin-bottom: 10px !important;
}

@media (max-width: 1200px) {
    .tab-kpi-context {
        grid-template-columns: 1fr;
    }
}


/* =========================================================
   V37 - DIAGNOSTICO INICIAL BALANCEADO
   ========================================================= */

/* Insight ejecutivo + Contexto territorial: resumen compacto, no bloque grande */
.tab-section:first-of-type .section-card {
    min-height: 190px !important;
    max-height: 230px !important;
    padding: 18px 20px !important;
    border-radius: 22px !important;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
}

.tab-section:first-of-type .section-card .section-title {
    font-size: 1.05rem !important;
    margin-bottom: 6px !important;
}

.tab-section:first-of-type .section-card .section-subtitle {
    font-size: .80rem !important;
    line-height: 1.35 !important;
    margin-bottom: 10px !important;
}

.tab-section:first-of-type .insight-card {
    min-height: 104px !important;
    max-height: 132px !important;
    padding: 13px 15px !important;
    border-radius: 18px !important;
    overflow: hidden !important;
}

.tab-section:first-of-type .insight-title {
    font-size: .76rem !important;
    margin-bottom: 6px !important;
}

.tab-section:first-of-type .insight-body {
    font-size: .78rem !important;
    line-height: 1.38 !important;
}

.tab-section:first-of-type .insight-card .dashboard-divider {
    margin: 7px 0 !important;
}

.tab-section:first-of-type .territory-card {
    min-height: 104px !important;
    max-height: 132px !important;
    padding: 14px 16px !important;
    border-radius: 18px !important;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.tab-section:first-of-type .territory-value {
    font-size: 1.35rem !important;
    line-height: 1.05 !important;
}

.tab-section:first-of-type .territory-sub {
    font-size: .78rem !important;
    line-height: 1.35 !important;
    margin-top: 8px !important;
}

.tab-section:first-of-type .tab-section-header {
    margin-bottom: 8px !important;
}

.tab-section:first-of-type {
    padding: 10px 12px 8px 12px !important;
    border-radius: 18px !important;
}


/* ===== V38 FINAL AJUSTES ===== */
.insight-card{min-height:60px!important;max-height:75px!important;padding:6px 8px!important;}
.insight-title{font-size:.72rem!important;}
.insight-body{font-size:.72rem!important;line-height:1.2!important;}
.territory-card{min-height:60px!important;max-height:75px!important;padding:8px 10px!important;}
.territory-value{font-size:1rem!important;}
.territory-sub{font-size:.68rem!important;}
.compact-context-bar{height:52px!important;padding:6px 8px!important;}


/* =========================================================
   V39 - FIX TARJETAS TERRITORIALES SIN TEXTO ENCIMADO
   ========================================================= */

/* Ajuste global para las tarjetas de territorio */
.territory-card {
    min-height: 132px !important;
    max-height: none !important;
    height: auto !important;
    padding: 16px 18px !important;
    border-radius: 20px !important;
    overflow: visible !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    gap: 6px !important;
}

.territory-label {
    font-size: .72rem !important;
    line-height: 1.2 !important;
    margin-bottom: 2px !important;
    white-space: normal !important;
}

.territory-value {
    font-size: 1.35rem !important;
    line-height: 1.1 !important;
    margin-bottom: 2px !important;
    white-space: normal !important;
}

.territory-sub {
    font-size: .78rem !important;
    line-height: 1.42 !important;
    margin-top: 4px !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}

/* El bloque inicial compacto no debe forzar recorte en tarjetas de territorio */
.tab-section:first-of-type .territory-card {
    min-height: 118px !important;
    max-height: none !important;
    height: auto !important;
    padding: 14px 16px !important;
    overflow: visible !important;
}

.tab-section:first-of-type .territory-value {
    font-size: 1.18rem !important;
    line-height: 1.12 !important;
}

.tab-section:first-of-type .territory-sub {
    font-size: .74rem !important;
    line-height: 1.38 !important;
}

/* En la pestaña de zonas prioritarias, deja más aire entre tarjetas */


/* =========================================================
   V40 - DIAGNOSTICO INICIAL REALMENTE COMPACTO
   ========================================================= */

/* El bloque diagnóstico inicial debe funcionar como resumen, no como sección grande */
.tab-section:first-of-type {
    padding: 8px 10px !important;
    border-radius: 16px !important;
    margin-bottom: 10px !important;
}

.tab-section:first-of-type .tab-section-header {
    margin-bottom: 6px !important;
}

.tab-section:first-of-type .tab-section-title {
    font-size: .66rem !important;
}

.tab-section:first-of-type .tab-section-hint {
    font-size: .64rem !important;
}

/* Tarjetas Insight + Contexto territorial: más bajas y proporcionales */
.tab-section:first-of-type .section-card {
    min-height: 128px !important;
    max-height: 148px !important;
    height: 138px !important;
    padding: 12px 14px !important;
    border-radius: 20px !important;
    overflow: hidden !important;
}

.tab-section:first-of-type .section-card .section-title {
    font-size: .95rem !important;
    line-height: 1.1 !important;
    margin-bottom: 5px !important;
}

.tab-section:first-of-type .section-card .section-subtitle {
    font-size: .72rem !important;
    line-height: 1.25 !important;
    margin-bottom: 8px !important;
}

/* Insight interno: solo resumen corto */
.tab-section:first-of-type .insight-card {
    min-height: 62px !important;
    max-height: 72px !important;
    height: 68px !important;
    padding: 8px 10px !important;
    border-radius: 14px !important;
    overflow: hidden !important;
}

.tab-section:first-of-type .insight-title {
    font-size: .66rem !important;
    line-height: 1.05 !important;
    margin-bottom: 4px !important;
}

.tab-section:first-of-type .insight-body {
    font-size: .67rem !important;
    line-height: 1.18 !important;
    margin: 0 !important;
    display: -webkit-box !important;
    -webkit-line-clamp: 2 !important;
    -webkit-box-orient: vertical !important;
    overflow: hidden !important;
}

.tab-section:first-of-type .insight-card .dashboard-divider {
    display: none !important;
}

/* Oculta el segundo texto largo del insight inicial si existe */
.tab-section:first-of-type .insight-card .insight-body:nth-of-type(n+2) {
    display: none !important;
}

/* Contexto territorial compacto */
.tab-section:first-of-type .territory-card {
    min-height: 68px !important;
    max-height: 78px !important;
    height: 74px !important;
    padding: 10px 12px !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    justify-content: center !important;
}

.tab-section:first-of-type .territory-value {
    font-size: 1.05rem !important;
    line-height: 1.05 !important;
    margin-bottom: 6px !important;
}

.tab-section:first-of-type .territory-sub {
    font-size: .66rem !important;
    line-height: 1.18 !important;
    margin-top: 0 !important;
}

/* Reduce columnas del diagnóstico inicial para que no parezcan paneles enormes */
.tab-section:first-of-type + div,
.tab-section:first-of-type ~ div {
    --compact-diagnostic: 1;
}

</style>
""", unsafe_allow_html=True)

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

def fmt_num(value, decimals=1):
    try:
        if pd.isna(value):
            return "N/D"
        return f"{float(value):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "N/D"

def context_badges(scope="red"):
    periodo = f"{pd.to_datetime(fecha_ini).strftime('%d/%m/%Y')} - {pd.to_datetime(fecha_fin).strftime('%d/%m/%Y')}"
    ops = len(operadores_sel) if "operadores_sel" in globals() else "N/D"
    if scope == "negocio":
        registros = len(business_f) if "business_f" in globals() and business_f is not None else 0
        cps = business_f["Codigo_postal"].nunique() if "business_f" in globals() and business_f is not None and not business_f.empty and "Codigo_postal" in business_f.columns else 0
        label = "Periodo negocio"
        reg_label = "Registros negocio"
    else:
        registros = df_f["RSRP_valido"].count() if "df_f" in globals() and not df_f.empty and "RSRP_valido" in df_f.columns else 0
        cps = df_f["Codigo_postal"].nunique() if "df_f" in globals() and not df_f.empty and "Codigo_postal" in df_f.columns else 0
        label = "Periodo red"
        reg_label = "Mediciones red"
    return (
        f'<div class="context-badge-row">'
        f'<span class="context-badge">{label}: <b>{periodo}</b></span>'
        f'<span class="context-badge">Operadores: <b>{ops}</b></span>'
        f'<span class="context-badge">CP visibles: <b>{fmt_int(cps)}</b></span>'
        f'<span class="context-badge">{reg_label}: <b>{fmt_int(registros)}</b></span>'
        f'</div>'
    )

def stage_header(kicker, title, subtitle, icon="spark", scope="red", show_badges=True):
    badges = context_badges("negocio" if scope == "negocio" else "red") if show_badges else ""
    return (
        f'<div class="stage-header">'
        f'<div class="stage-kicker">{icon_svg(icon, 13)} {kicker}</div>'
        f'<div class="stage-title">{title}</div>'
        f'<div class="stage-subtitle">{subtitle}</div>'
        f'{badges}'
        f'</div>'
    )

def lane_label(text, icon="spark"):
    return f'<div class="lane-label">{icon_svg(icon, 13)} {text}</div>'

def compact_context_bar():
    return f'''
    <div class="compact-context-bar">
        <div class="compact-context-main">
            <div class="compact-context-label">{icon_svg("filter", 12)} Contexto activo</div>
            <div class="compact-context-value">{periodo_txt_corto}</div>
            <div class="compact-context-sub">{fmt_int(network_records_visible)} mediciones red · {fmt_int(business_records_visible)} registros negocio</div>
        </div>
        <div class="compact-context-item">
            <div class="compact-context-label">{icon_svg("signal", 12)} RSRP mediano</div>
            <div class="compact-context-value">{fmt_dBm(global_median)}</div>
            <div class="compact-context-sub">Intensidad agregada</div>
        </div>
        <div class="compact-context-item">
            <div class="compact-context-label">{icon_svg("target", 12)} CP críticos</div>
            <div class="compact-context-value">{fmt_int(cp_critical_count)}</div>
            <div class="compact-context-sub">{fmt_pct(cp_critical_share)} del territorio visible</div>
        </div>
        <div class="compact-context-item">
            <div class="compact-context-label">{icon_svg("users", 12)} Operador líder</div>
            <div class="compact-context-value">{best_operator["Operador"]}</div>
            <div class="compact-context-sub">Score {best_operator["Score_operador"]:.1f}</div>
        </div>
        <div class="compact-context-item">
            <div class="compact-context-label">{icon_svg("trend", 12)} Variación señal</div>
            <div class="compact-context-value">{fmt_var_dBm(variation_result["variacion_global"])}</div>
            <div class="compact-context-sub">Nivel {nivel_temporal_variacion}</div>
        </div>
    </div>
    '''

def page_flow_note():
    return f'''
    <div class="page-flow-note">
        <div class="page-flow-title">{icon_svg("eye", 12)} Guía rápida</div>
        <div class="page-flow-text">
            Usa esta barra solo como contexto. El análisis completo está organizado dentro de cada pestaña.
        </div>
    </div>
    '''

def tab_section(title, hint="", icon="spark"):
    return (
        f'<div class="tab-section">'
        f'<div class="tab-section-header">'
        f'<div class="tab-section-title">{icon_svg(icon, 13)} {title}</div>'
        f'<div class="tab-section-hint">{hint}</div>'
        f'</div>'
    )

def tab_kpi_context(items):
    cards = []
    for item in items:
        icon = item.get("icon", "spark")
        label = item.get("label", "")
        value = item.get("value", "N/D")
        sub = item.get("sub", "")
        cards.append(
            f'<div class="tab-kpi-card">'
            f'<div class="tab-kpi-label">{icon_svg(icon, 12)} {label}</div>'
            f'<div class="tab-kpi-value">{value}</div>'
            f'<div class="tab-kpi-sub">{sub}</div>'
            f'</div>'
        )
    return '<div class="tab-kpi-context">' + ''.join(cards) + '</div>'

def tab_insight(title, body, icon="eye"):
    return (
        f'<div class="tab-insight">'
        f'<div class="tab-insight-title">{icon_svg(icon, 13)} {title}</div>'
        f'<div class="tab-insight-body">{body}</div>'
        f'</div>'
    )

def risk_badges():
    if pct_critical >= 30:
        risk_class, risk_text = "risk-high", "Riesgo alto"
    elif pct_critical >= 15:
        risk_class, risk_text = "risk-watch", "Vigilancia"
    else:
        risk_class, risk_text = "risk-stable", "Estable"

    var_value = variation_result.get("variacion_global", np.nan)
    if pd.notna(var_value) and var_value < 0:
        var_class, var_text = "risk-high", "Deterioro de señal"
    elif pd.notna(var_value) and var_value > 0:
        var_class, var_text = "risk-stable", "Mejora de señal"
    else:
        var_class, var_text = "risk-watch", "Cambio estable"

    return (
        f'<div class="risk-badge-row">'
        f'<span class="risk-badge {risk_class}">{icon_svg("target", 12)} {risk_text}</span>'
        f'<span class="risk-badge {var_class}">{icon_svg("trend", 12)} {var_text}</span>'
        f'<span class="risk-badge risk-opportunity">{icon_svg("filter", 12)} {fmt_int(df_f["Codigo_postal"].nunique())} CP visibles</span>'
        f'</div>'
    )

def table_shell(title, hint="Detalle analítico disponible para validación."):
    return (
        f'<div class="table-shell">'
        f'<div class="table-toolbar">'
        f'<div class="table-title-mini">{icon_svg("table", 12)} {title}</div>'
        f'<div class="table-hint-mini">{hint}</div>'
        f'</div>'
    )

def executive_map():
    return f'''
    <div class="exec-map">
        <div class="exec-map-card"><div class="exec-map-title">{icon_svg("eye", 13)} Resumen</div><div class="exec-map-text">Estado general, insight y señal principal del periodo.</div></div>
        <div class="exec-map-card"><div class="exec-map-title">{icon_svg("users", 13)} Operadores</div><div class="exec-map-text">Comparación competitiva, score y composición de calidad.</div></div>
        <div class="exec-map-card"><div class="exec-map-title">{icon_svg("map", 13)} Territorio</div><div class="exec-map-text">Zonas prioritarias, operador débil y detalle por CP.</div></div>
        <div class="exec-map-card"><div class="exec-map-title">{icon_svg("trend", 13)} Variación</div><div class="exec-map-text">Cambio de intensidad de señal entre periodos.</div></div>
        <div class="exec-map-card"><div class="exec-map-title">{icon_svg("briefcase", 13)} Negocio</div><div class="exec-map-text">Mercado, altas, riesgo y oportunidad comercial.</div></div>
    </div>
    '''

def icon_svg(name="spark", size=14):
    icons = {
        "spark": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/></svg>',
        "signal": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M4 18h2"/><path d="M8 15h2"/><path d="M12 12h2"/><path d="M16 9h2"/><path d="M20 6h.01"/></svg>',
        "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v6c0 4.5-2.9 7.7-7 9-4.1-1.3-7-4.5-7-9V6l7-3z"/></svg>',
        "users": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9.5" cy="7" r="3"/><path d="M20 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 4.13a3 3 0 0 1 0 5.74"/></svg>',
        "map": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21 3 6"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>',
        "trend": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 7-8"/><path d="M14 7h6v6"/></svg>',
        "briefcase": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 12h18"/></svg>',
        "target": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="M2 12h2"/><path d="M20 12h2"/></svg>',
        "chart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="5"/><rect x="12" y="8" width="3" height="9"/><rect x="17" y="5" width="3" height="12"/></svg>',
        "filter": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>',
        "table": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18"/><path d="M9 4v16"/><path d="M15 4v16"/></svg>',
        "eye": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>'
    }
    svg = icons.get(name, icons["spark"])
    return f'<span class="icon-inline" style="width:{size}px;height:{size}px;">{svg}</span>'

# =========================================================
# INSIGHT EJECUTIVO / CEO
# =========================================================
def build_executive_insight(pct_critical, variation):
    try:
        if pct_critical >= 25:
            return {"icon": "alert", "color": "#ef4444", "title": "Riesgo alto en red", "text": "Alta criticidad detectada", "action": "Priorizar intervención inmediata"}
        elif variation < 0:
            return {"icon": "trend_down", "color": "#f59e0b", "title": "Deterioro de señal", "text": "La red está cayendo", "action": "Revisar zonas con caída"}
        else:
            return {"icon": "check", "color": "#22c55e", "title": "Red estable", "text": "Comportamiento controlado", "action": "Mantener monitoreo"}
    except Exception:
        return {"icon": "info", "color": "#94a3b8", "title": "Sin datos", "text": "No hay información suficiente", "action": "Revisar filtros"}


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
    elif x >= -90:
        return "Buena"
    elif x >= -100:
        return "Aceptable"
    return "Crítica"

def executive_status(value):
    if pd.isna(value):
        return ("Sin dato", "badge-warn")
    if value >= -70:
        return ("Excelente", "badge-good")
    if value >= -90:
        return ("Buena", "badge-good")
    if value >= -100:
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


def style_chart(chart):
    try:
        return (
            chart.properties(background="transparent")
            .configure_view(strokeOpacity=0)
            .configure_axis(
                domainColor="rgba(255,255,255,0.18)",
                tickColor="rgba(255,255,255,0.18)",
                gridColor="rgba(255,255,255,0.10)",
                labelColor="#CBD5E1",
                titleColor="#F8FAFC"
            )
            .configure_legend(
                titleColor="#CBD5E1",
                labelColor="#CBD5E1",
                symbolStrokeColor="rgba(255,255,255,0.15)"
            )
            .configure_title(color="#F8FAFC")
        )
    except Exception:
        return chart


def prepare_variation_display(df_in, label_col, top_n=24):
    if df_in is None or df_in.empty or label_col not in df_in.columns:
        return pd.DataFrame()
    df = df_in.dropna(subset=[label_col, "Variacion_RSRP"]).copy()
    if df.empty:
        return df
    half = max(6, top_n // 2)
    pos = df[df["Variacion_RSRP"] >= 0].nlargest(half, "Variacion_RSRP")
    neg = df[df["Variacion_RSRP"] < 0].nsmallest(half, "Variacion_RSRP")
    out = pd.concat([neg, pos], axis=0).drop_duplicates()
    out["label_short"] = out[label_col].astype(str).str.strip().str.slice(0, 26)
    out["label_short"] = np.where(out[label_col].astype(str).str.len() > 26, out["label_short"] + "…", out["label_short"])
    out = out.sort_values("Variacion_RSRP", ascending=True).reset_index(drop=True)
    return out

def build_territory_label(row):
    parts = []
    for col in TERRITORIAL_STANDARD_COLS:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            parts.append(str(row[col]))
    return " | ".join(parts)

def enrich_cp_label(cp_val, row=None):
    """Devuelve etiqueta enriquecida de un código postal: CP + Barrio/Localidad si disponibles."""
    label = str(cp_val) if pd.notna(cp_val) else "N/D"
    if row is not None:
        barrio = str(row.get("BARRIO", "")).strip() if "BARRIO" in row.index else ""
        localidad = str(row.get("LOCALIDAD", "")).strip() if "LOCALIDAD" in row.index else ""
        if barrio and barrio not in ("nan", ""):
            label = f"{barrio.title()} ({label})"
        elif localidad and localidad not in ("nan", ""):
            label = f"{localidad.title()} ({label})"
    return label

def add_temporal_fields(df_in, date_col="Fecha de inicio"):
    df_out = df_in.copy()
    if date_col not in df_out.columns:
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
# NEGOCIO: MERCADO + ALTAS DESDE EXCELS
# =========================================================
def map_business_operator(raw_col):
    n = normalize_text(raw_col)
    if "CLARO" in n:
        return "Claro"
    if "TIGO" in n:
        return "Tigo"
    if "MOVISTAR" in n:
        return "Movistar Colombia"
    if re.search(r"\bETB\b", n):
        return "ETB"
    if "WOM" in n:
        return "WOM Colombia"
    if "AVANTEL" in n:
        return "Avantel"
    if "VIRGIN" in n:
        return "Virgin Mobile"
    if "OTHERS" in n or "OTROS" in n:
        return "Others"
    return None

def load_business_excel_long(candidates, metric_name):
    path = find_existing_file(candidates)
    if path is None:
        return pd.DataFrame(), {"found": False, "message": f"No se encontró el archivo de {metric_name.lower()}."}

    try:
        df, sheet_name = robust_read_excel(path)
        if df is None or df.empty:
            return pd.DataFrame(), {"found": False, "message": f"El archivo de {metric_name.lower()} está vacío."}

        df.columns = make_unique_columns(clean_columns(df.columns))
        cp_col = find_col_by_aliases(df, ["Codigo_postal", "CODIGO POSTAL", "CÓDIGO POSTAL", "COD POSTAL", "COD. POSTAL"])
        fecha_col = find_col_by_aliases(df, ["Fecha", "FECHA", "Fecha de inicio", "FECHA DE INICIO"])
        if cp_col is None or fecha_col is None:
            return pd.DataFrame(), {"found": False, "message": f"El archivo de {metric_name.lower()} no contiene columnas válidas de código postal y fecha."}

        df = df.rename(columns={cp_col: "Codigo_postal", fecha_col: "Fecha"})
        df["Codigo_postal"] = safe_to_str_series(df["Codigo_postal"])
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

        operator_cols = []
        operator_map = {}
        for col in df.columns:
            if col in ["Codigo_postal", "Fecha"]:
                continue
            op = map_business_operator(col)
            if op is not None:
                operator_cols.append(col)
                operator_map[col] = op

        if not operator_cols:
            return pd.DataFrame(), {"found": False, "message": f"No se detectaron columnas de operadores en el archivo de {metric_name.lower()}."}

        long_df = df.melt(
            id_vars=["Codigo_postal", "Fecha"],
            value_vars=operator_cols,
            var_name="col_origen",
            value_name=metric_name
        )
        long_df["Operador"] = long_df["col_origen"].map(operator_map)
        long_df[metric_name] = pd.to_numeric(long_df[metric_name], errors="coerce")
        long_df = long_df.drop(columns=["col_origen"])
        long_df = long_df.dropna(subset=["Codigo_postal", "Fecha", "Operador"])
        return long_df, {
            "found": True,
            "message": None,
            "path": path,
            "sheet_name": sheet_name,
            "operators": sorted(long_df["Operador"].dropna().unique().tolist()),
        }
    except Exception as e:
        return pd.DataFrame(), {"found": False, "message": f"No fue posible leer el archivo de {metric_name.lower()}: {e}"}

def merge_business_sources(market_long, altas_long, territorial_df):
    join_cols = ["Codigo_postal", "Fecha", "Operador"]
    if market_long is None or market_long.empty:
        market_long = pd.DataFrame(columns=join_cols + ["Mercado"])
    if altas_long is None or altas_long.empty:
        altas_long = pd.DataFrame(columns=join_cols + ["Altas"])

    business = market_long.merge(altas_long, on=join_cols, how="outer")
    if business.empty:
        return business

    if "Mercado" not in business.columns:
        business["Mercado"] = np.nan
    if "Altas" not in business.columns:
        business["Altas"] = np.nan

    business = safe_merge_territorial(business, territorial_df)
    business = business.rename(columns={"Fecha": "Fecha de inicio"})
    business["Codigo_postal"] = safe_to_str_series(business["Codigo_postal"])

    grp = ["Codigo_postal", "Fecha de inicio"]
    market_total = business.groupby(grp, dropna=False)["Mercado"].transform("sum")
    altas_total = business.groupby(grp, dropna=False)["Altas"].transform("sum")
    business["Cuota_mercado"] = np.where(market_total > 0, business["Mercado"] / market_total * 100, np.nan)
    business["Participacion_altas"] = np.where(altas_total > 0, business["Altas"] / altas_total * 100, np.nan)
    business = business.loc[:, ~business.columns.duplicated()].copy()
    return business

def compute_business_metrics(business_df, rsrp_df):
    result = {
        "available": False,
        "message": "No hay datos de mercado o altas disponibles.",
        "market_operator": pd.DataFrame(),
        "altas_operator": pd.DataFrame(),
        "market_time": pd.DataFrame(),
        "altas_time": pd.DataFrame(),
        "cross_operator": pd.DataFrame(),
        "territorial_cross": pd.DataFrame(),
        "risk_table": pd.DataFrame(),
        "opportunity_table": pd.DataFrame(),
        "scatter_df": pd.DataFrame(),
        "leader_market": None,
        "leader_altas": None,
        "variation_market": np.nan,
        "variation_altas": np.nan,
        "market_month_initial_label": None,
        "market_month_final_label": None,
        "altas_month_initial_label": None,
        "altas_month_final_label": None,
        "market_month_initial_value": np.nan,
        "market_month_final_value": np.nan,
        "altas_month_initial_value": np.nan,
        "altas_month_final_value": np.nan,
        "market_month_initial_operator": None,
        "market_month_final_operator": None,
        "altas_month_initial_operator": None,
        "altas_month_final_operator": None,
    }
    if business_df is None or business_df.empty:
        return result

    biz = add_temporal_fields(business_df.copy(), date_col="Fecha de inicio")
    has_market = biz["Mercado"].notna().any() if "Mercado" in biz.columns else False
    has_altas = biz["Altas"].notna().any() if "Altas" in biz.columns else False
    if not has_market and not has_altas:
        return result

    if has_market:
        market_operator = (
            biz.groupby("Operador", as_index=False)
            .agg(
                Mercado_total=("Mercado", "sum"),
                Cuota_mercado=("Cuota_mercado", "mean"),
                Codigos=("Codigo_postal", "nunique"),
                Registros=("Mercado", "count")
            )
        )
        total_market = market_operator["Mercado_total"].sum()
        market_operator["Cuota_mercado_global"] = np.where(total_market > 0, market_operator["Mercado_total"] / total_market * 100, np.nan)
        market_operator = market_operator.sort_values("Cuota_mercado_global", ascending=False).reset_index(drop=True)
        result["market_operator"] = market_operator
        if not market_operator.empty:
            result["leader_market"] = market_operator.iloc[0]

        market_time = (
            biz.dropna(subset=["Periodo_Mes"])
            .groupby(["Periodo_Mes", "Operador"], as_index=False)
            .agg(Mercado_total=("Mercado", "sum"))
        )
        if not market_time.empty:
            totals = market_time.groupby("Periodo_Mes", as_index=False)["Mercado_total"].sum().rename(columns={"Mercado_total": "Total_mes"})
            market_time = market_time.merge(totals, on="Periodo_Mes", how="left")
            market_time["Cuota_mercado"] = np.where(market_time["Total_mes"] > 0, market_time["Mercado_total"] / market_time["Total_mes"] * 100, np.nan)
            result["market_time"] = market_time
            pts = market_time.sort_values(["Periodo_Mes", "Cuota_mercado"], ascending=[True, False]).copy()
            month_rank = pts.groupby("Periodo_Mes", as_index=False).first()
            month_rank = month_rank.sort_values("Periodo_Mes").reset_index(drop=True)
            if not month_rank.empty:
                result["market_month_initial_label"] = pd.to_datetime(month_rank.iloc[0]["Periodo_Mes"]).strftime("%b %Y")
                result["market_month_initial_value"] = month_rank.iloc[0]["Cuota_mercado"]
                result["market_month_initial_operator"] = month_rank.iloc[0]["Operador"]
                result["market_month_final_label"] = pd.to_datetime(month_rank.iloc[-1]["Periodo_Mes"]).strftime("%b %Y")
                result["market_month_final_value"] = month_rank.iloc[-1]["Cuota_mercado"]
                result["market_month_final_operator"] = month_rank.iloc[-1]["Operador"]
            if month_rank.shape[0] >= 2:
                result["variation_market"] = month_rank.iloc[-1]["Cuota_mercado"] - month_rank.iloc[0]["Cuota_mercado"]

    if has_altas:
        altas_operator = (
            biz.groupby("Operador", as_index=False)
            .agg(
                Altas_total=("Altas", "sum"),
                Participacion_altas=("Participacion_altas", "mean"),
                Codigos=("Codigo_postal", "nunique"),
                Registros=("Altas", "count")
            )
        )
        total_altas = altas_operator["Altas_total"].sum()
        altas_operator["Participacion_altas_global"] = np.where(total_altas > 0, altas_operator["Altas_total"] / total_altas * 100, np.nan)
        altas_operator = altas_operator.sort_values("Participacion_altas_global", ascending=False).reset_index(drop=True)
        result["altas_operator"] = altas_operator
        if not altas_operator.empty:
            result["leader_altas"] = altas_operator.iloc[0]

        altas_time = (
            biz.dropna(subset=["Periodo_Mes"])
            .groupby(["Periodo_Mes", "Operador"], as_index=False)
            .agg(Altas_total=("Altas", "sum"))
        )
        if not altas_time.empty:
            totals = altas_time.groupby("Periodo_Mes", as_index=False)["Altas_total"].sum().rename(columns={"Altas_total": "Total_mes"})
            altas_time = altas_time.merge(totals, on="Periodo_Mes", how="left")
            altas_time["Participacion_altas"] = np.where(altas_time["Total_mes"] > 0, altas_time["Altas_total"] / altas_time["Total_mes"] * 100, np.nan)
            result["altas_time"] = altas_time
            pts = altas_time.sort_values(["Periodo_Mes", "Participacion_altas"], ascending=[True, False]).copy()
            month_rank = pts.groupby("Periodo_Mes", as_index=False).first()
            month_rank = month_rank.sort_values("Periodo_Mes").reset_index(drop=True)
            if not month_rank.empty:
                result["altas_month_initial_label"] = pd.to_datetime(month_rank.iloc[0]["Periodo_Mes"]).strftime("%b %Y")
                result["altas_month_initial_value"] = month_rank.iloc[0]["Participacion_altas"]
                result["altas_month_initial_operator"] = month_rank.iloc[0]["Operador"]
                result["altas_month_final_label"] = pd.to_datetime(month_rank.iloc[-1]["Periodo_Mes"]).strftime("%b %Y")
                result["altas_month_final_value"] = month_rank.iloc[-1]["Participacion_altas"]
                result["altas_month_final_operator"] = month_rank.iloc[-1]["Operador"]
            if month_rank.shape[0] >= 2:
                result["variation_altas"] = month_rank.iloc[-1]["Participacion_altas"] - month_rank.iloc[0]["Participacion_altas"]

    rsrp_operator = pd.DataFrame()
    if rsrp_df is not None and not rsrp_df.empty:
        rsrp_operator = rsrp_df.groupby("Operador", as_index=False).agg(
            RSRP_mediana=("RSRP_valido", "median"),
            Buena_o_mejor=("Categoria_RSRP", lambda s: s.isin(["Excelente", "Buena"]).mean() * 100),
            Critica=("Categoria_RSRP", lambda s: (s == "Crítica").mean() * 100),
        )

    cross_operator = rsrp_operator.copy()
    if not result["market_operator"].empty:
        cross_operator = cross_operator.merge(result["market_operator"][["Operador", "Cuota_mercado_global"]], on="Operador", how="outer")
    if not result["altas_operator"].empty:
        cross_operator = cross_operator.merge(result["altas_operator"][["Operador", "Participacion_altas_global"]], on="Operador", how="outer")
    if not cross_operator.empty:
        cross_operator["Gap_red_vs_mercado"] = cross_operator["Buena_o_mejor"] - cross_operator["Cuota_mercado_global"]
        cross_operator["Gap_red_vs_captacion"] = cross_operator["Buena_o_mejor"] - cross_operator["Participacion_altas_global"]
        cross_operator = cross_operator.sort_values("RSRP_mediana", ascending=False).reset_index(drop=True)
        result["cross_operator"] = cross_operator
        result["scatter_df"] = cross_operator.dropna(subset=["RSRP_mediana", "Cuota_mercado_global"]).copy()

    if rsrp_df is not None and not rsrp_df.empty and "Codigo_postal" in rsrp_df.columns and "Codigo_postal" in biz.columns:
        rsrp_t = rsrp_df.groupby(["Codigo_postal", "Operador"], as_index=False).agg(
            RSRP_mediana=("RSRP_valido", "median"),
            Buena_o_mejor=("Categoria_RSRP", lambda s: s.isin(["Excelente", "Buena"]).mean() * 100),
            Critica=("Categoria_RSRP", lambda s: (s == "Crítica").mean() * 100),
        )
        biz_group_cols = [c for c in ["Codigo_postal"] + TERRITORIAL_STANDARD_COLS + ["Operador"] if c in biz.columns]
        biz_t = biz.groupby(biz_group_cols, as_index=False).agg(
            Cuota_mercado=("Cuota_mercado", "mean"),
            Participacion_altas=("Participacion_altas", "mean"),
            Mercado_total=("Mercado", "sum"),
            Altas_total=("Altas", "sum"),
        )
        territorial_cross = biz_t.merge(rsrp_t, on=["Codigo_postal", "Operador"], how="left")
        result["territorial_cross"] = territorial_cross

        if not territorial_cross.empty and territorial_cross["Cuota_mercado"].notna().any():
            cuota_high = territorial_cross["Cuota_mercado"].quantile(0.60)
            cuota_low = territorial_cross["Cuota_mercado"].quantile(0.40)
            risk = territorial_cross[(territorial_cross["RSRP_mediana"] < -90) & (territorial_cross["Cuota_mercado"] >= cuota_high)].copy()
            opp = territorial_cross[(territorial_cross["RSRP_mediana"] >= -80) & (territorial_cross["Cuota_mercado"] <= cuota_low)].copy()
            result["risk_table"] = risk.sort_values(["Cuota_mercado", "RSRP_mediana"], ascending=[False, True]).head(25)
            result["opportunity_table"] = opp.sort_values(["RSRP_mediana", "Cuota_mercado"], ascending=[False, True]).head(25)

    result["available"] = True
    result["message"] = None
    return result

# =========================================================
# CARGA PRINCIPAL
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
        value_name="RSRP"
    )
    df_long["RSRP_valido"] = df_long["RSRP"].where(df_long["RSRP"] < 0)
    df_long["Con_medicion"] = df_long["RSRP_valido"].notna()
    df_long["Categoria_RSRP"] = df_long["RSRP_valido"].apply(classify_rsrp)

    territorial_df, territorial_info = load_territorial_data()
    df_long = safe_merge_territorial(df_long, territorial_df)

    market_long, market_info = load_business_excel_long(MARKET_FILE_CANDIDATES, "Mercado")
    altas_long, altas_info = load_business_excel_long(ALTAS_FILE_CANDIDATES, "Altas")
    business_long = merge_business_sources(market_long, altas_long, territorial_df)

    return (
        df,
        df_long,
        operator_cols,
        territorial_df,
        territorial_info,
        business_long,
        market_info,
        altas_info,
        {"csv_encoding": csv_encoding, "csv_sep": csv_sep}
    )

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

    df_var = add_temporal_fields(df_source.copy(), date_col="Fecha de inicio")
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
        elif global_median >= -90:
            parts.append("El desempeño agregado de señal se mantiene en nivel bueno.")
        elif global_median >= -100:
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
        (market_df if market_df is not None and not market_df.empty else pd.DataFrame({"Mensaje": ["No se encontraron datos de mercado."]})).to_excel(writer, sheet_name="Mercado", index=False)
        (altas_df if altas_df is not None and not altas_df.empty else pd.DataFrame({"Mensaje": ["No se encontraron datos de altas."]})).to_excel(writer, sheet_name="Altas", index=False)
    output.seek(0)
    return output.getvalue()


# =========================================================
# MÓDULO: VISTA CLARO — PLAN Y EJECUCIÓN DE AGENTES
# Archivo de datos: Plan_actualizado_CORTE_28_FINAL.xlsx
# Hojas: Detalle (principal), LIKE SUR (resumen agente), Cierre marzo
# =========================================================

CLARO_FILE_CANDIDATES = [
    os.path.join(BASE_DIR, "Plan_actualizado_CORTE_28_FINAL.xlsx"),
    os.path.join(BASE_DIR, "Plan_actualizado_CORTE_28_FINAL(1).xlsx"),
    os.path.join(BASE_DIR, "Plan_actualizado_CORTE_28_FINAL(2).xlsx"),
]

AGENTE_COLORS = {
    "LIKE USME":       "#E10600",
    "MI RED MOVIL":    "#38BDF8",
    "ICELL R4":        "#22C55E",
    "MAX EVOLUCION BOG": "#F59E0B",
    "TEAM":            "#A855F7",
    "LIKE ZONA SUR":   "#EF4444",
    "MAX EVOLUCION ":  "#F97316",
    "MAX EVOLUCION":   "#F97316",
}

CATEGORIA_COLORS = {
    "DIAMANTE": "#38BDF8",
    "PLATINO":  "#A855F7",
    "ORO":      "#F59E0B",
    "PLATA":    "#94A3B8",
    "BRONCE":   "#92400E",
}

@st.cache_data(ttl=300)
def load_claro_data():
    path = find_existing_file(CLARO_FILE_CANDIDATES)
    if path is None:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {"found": False, "message": "No se encontró el archivo de agentes Claro."}
    try:
        df_det = pd.read_excel(path, sheet_name="Detalle", header=0)
        df_det.columns = [str(c).strip() for c in df_det.columns]
        # Numeric coercion
        num_cols = [
            "META ALTA NAT (>$2000)", "EJEC ALTA NAT", "META ALTA INDU (=< $2.000)", "EJEC ALTA INDU",
            "TOTAL META ALTA", "EJE ALTA TOTAL", "% CUMPLI", "META ARPU", "EJEC ARPU",
            "META INGRESOS M0", "EJEC INGRESOS M0", "CUOTA DE MERCADO", "CUOTA DE ALTA",
            "RSRP", "S1", "S2", "S3", "S4", "S1.1", "S2.1", "S3.1", "S4.1",
        ]
        for c in num_cols:
            if c in df_det.columns:
                df_det[c] = pd.to_numeric(df_det[c], errors="coerce")
        # String coercion
        for c in ["AGENTE", "CATEGORIA", "TIPOLOGIA", "CLASIFICACION", "ZONA", "TIPO", "ASESOR", "RUTA", "CIRCUITO", "BARRIO"]:
            if c in df_det.columns:
                df_det[c] = df_det[c].astype(str).str.strip().replace("nan", pd.NA)

        df_cierre = pd.read_excel(path, sheet_name="Cierre marzo", header=0)
        df_cierre.columns = [str(c).strip() for c in df_cierre.columns]
        df_cierre.columns = ["ID_POS", "MAR_ALTAS", "MAR_INGRESOS"]
        df_cierre["MAR_ALTAS"] = pd.to_numeric(df_cierre["MAR_ALTAS"], errors="coerce")
        df_cierre["MAR_INGRESOS"] = pd.to_numeric(df_cierre["MAR_INGRESOS"], errors="coerce")

        df_plan = pd.read_excel(path, sheet_name="LIKE SUR", header=5)
        df_plan.columns = [str(c).strip() for c in df_plan.columns]

        return df_det, df_cierre, df_plan, {"found": True, "message": None, "path": path}
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {"found": False, "message": str(e)}


def render_claro_view():
    """Renderiza la vista completa de Claro — Plan y Ejecución de Agentes."""

    df_det, df_cierre, df_plan, info = load_claro_data()

    if not info.get("found") or df_det.empty:
        st.error(f"No fue posible cargar los datos de Claro: {info.get('message', 'Archivo no encontrado.')}")
        return

    # =========================================================
    # SIDEBAR CLARO: Filtros propios
    # =========================================================
    st.sidebar.markdown("---")
    st.sidebar.markdown(f'<div class="sidebar-block"><div class="sidebar-kicker">{icon_svg("spark",12)} Vista Claro · Filtros</div><div class="sidebar-title">Personaliza la vista</div><div class="sidebar-sub">Filtra el universo de PDVs por agente, categoría, zona, circuito, ruta, barrio y más.</div><div style="margin-top:8px;padding:8px 10px;background:rgba(225,6,0,0.10);border:1px solid rgba(225,6,0,0.22);border-radius:12px;font-size:0.73rem;color:#FCA5A5;font-weight:700;">📅 Ventana de datos: 1 al 27 de Abril 2026</div>', unsafe_allow_html=True)

    def _opts(col): return sorted([x for x in df_det[col].dropna().unique() if str(x).strip() not in ("","nan")]) if col in df_det.columns else []

    agente_sel = st.sidebar.multiselect("Agente", options=_opts("AGENTE"), default=[], key="claro_agente_sel")
    cat_sel    = st.sidebar.multiselect("⭐ Categoría PDV", options=_opts("CATEGORIA"), default=[], key="claro_cat_sel",
                    help="DIAMANTE, PLATINO, ORO, PLATA, BRONCE — jerarquía comercial del PDV")
    zona_sel   = st.sidebar.multiselect("📍 Zona", options=_opts("ZONA"), default=[], key="claro_zona_sel")

    st.sidebar.markdown('<div style="font-size:0.72rem;color:#94A3B8;font-weight:700;letter-spacing:0.4px;margin:8px 0 2px;">FILTROS AVANZADOS</div>', unsafe_allow_html=True)
    tipo_sel    = st.sidebar.multiselect("🏪 Tipo de negocio", options=_opts("TIPO"), default=[], key="claro_tipo_sel")
    tipol_sel   = st.sidebar.multiselect("🔖 Tipología (A/B/C/D)", options=_opts("TIPOLOGIA"), default=[], key="claro_tipol_sel",
                    help="Clasificación interna del PDV por tamaño y potencial")
    clasif_sel  = st.sidebar.multiselect("🏷️ Clasificación comercial", options=_opts("CLASIFICACION"), default=[], key="claro_clasif_sel")
    asesor_sel  = st.sidebar.multiselect("👤 Asesor", options=_opts("ASESOR"), default=[], key="claro_asesor_sel")
    circuito_sel_c = st.sidebar.multiselect("🔁 Circuito", options=_opts("CIRCUITO"), default=[], key="claro_circuito_sel")
    ruta_sel_c  = st.sidebar.multiselect("🗺️ Ruta", options=_opts("RUTA"), default=[], key="claro_ruta_sel")
    barrio_sel_c = st.sidebar.multiselect("🏘️ Barrio", options=_opts("BARRIO"), default=[], key="claro_barrio_sel")

    cumpl_min = st.sidebar.slider("Cumplimiento mínimo (%)", 0, 100, 0, 5, key="claro_cumpl_min",
                    help="Muestra solo PDVs cuyo cumplimiento de meta nat. sea ≥ este valor")
    cumpl_max = st.sidebar.slider("Cumplimiento máximo (%)", 0, 200, 200, 5, key="claro_cumpl_max",
                    help="Útil para filtrar PDVs con sobre-ejecución o riesgo de saturación")

    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # =========================================================
    # FILTRADO
    # =========================================================
    df = df_det.copy()
    if agente_sel:     df = df[df["AGENTE"].isin(agente_sel)]
    if cat_sel:        df = df[df["CATEGORIA"].isin(cat_sel)]
    if zona_sel:       df = df[df["ZONA"].isin(zona_sel)]
    if tipo_sel:       df = df[df["TIPO"].isin(tipo_sel)]
    if tipol_sel:      df = df[df["TIPOLOGIA"].isin(tipol_sel)]
    if clasif_sel:     df = df[df["CLASIFICACION"].isin(clasif_sel)]
    if asesor_sel:     df = df[df["ASESOR"].isin(asesor_sel)]
    if circuito_sel_c: df = df[df["CIRCUITO"].isin(circuito_sel_c)]
    if ruta_sel_c:     df = df[df["RUTA"].isin(ruta_sel_c)]
    if barrio_sel_c:   df = df[df["BARRIO"].isin(barrio_sel_c)]
    # Cumplimiento filter (requires computing per-PDV cumpl)
    if "META ALTA NAT (>$2000)" in df.columns and "EJEC ALTA NAT" in df.columns and (cumpl_min > 0 or cumpl_max < 200):
        df["_cumpl_pdv"] = (df["EJEC ALTA NAT"] / df["META ALTA NAT (>$2000)"].replace(0, np.nan) * 100).fillna(0)
        df = df[(df["_cumpl_pdv"] >= cumpl_min) & (df["_cumpl_pdv"] <= cumpl_max)]
        df = df.drop(columns=["_cumpl_pdv"])

    if df.empty:
        st.warning("No hay PDVs con los filtros seleccionados.")
        return

    # =========================================================
    # MÉTRICAS GLOBALES
    # =========================================================
    total_pdvs        = int(df["ID"].nunique()) if "ID" in df.columns else int(len(df))
    meta_nat_total    = df["META ALTA NAT (>$2000)"].sum()
    ejec_nat_total    = df["EJEC ALTA NAT"].sum()
    meta_total_alta   = df["TOTAL META ALTA"].sum()
    ejec_total_alta   = df["EJE ALTA TOTAL"].sum()
    meta_ingresos     = df["META INGRESOS M0"].sum()
    ejec_ingresos     = df["EJEC INGRESOS M0"].sum()
    cuota_mkt_media   = df["CUOTA DE MERCADO"].mean()
    cuota_alta_media  = df["CUOTA DE ALTA"].mean()
    rsrp_media        = df["RSRP"].mean()

    cumplimiento_nat  = (ejec_nat_total / meta_nat_total * 100) if meta_nat_total > 0 else np.nan
    cumplimiento_tot  = (ejec_total_alta / meta_total_alta * 100) if meta_total_alta > 0 else np.nan

    s1_total = df["S1"].sum()
    s2_total = df["S2"].sum()
    s3_total = df["S3"].sum()
    s4_total = df["S4"].sum()

    cierre_altas    = df_cierre["MAR_ALTAS"].sum()
    cierre_ingresos = df_cierre["MAR_INGRESOS"].sum()

    def fmt_m(v):
        if pd.isna(v): return "N/D"
        if abs(v) >= 1_000_000_000: return f"${v/1_000_000_000:.2f}B"
        if abs(v) >= 1_000_000:     return f"${v/1_000_000:.1f}M"
        if abs(v) >= 1_000:         return f"${v/1_000:.0f}K"
        return f"${v:,.0f}"

    def fmt_pct_c(v):
        return f"{v:.1f}%" if pd.notna(v) else "N/D"

    def delta_badge(v, invert=False):
        if pd.isna(v): return ""
        ok = v >= 100 if not invert else v <= 100
        cls = "badge-good" if ok else "badge-warn" if v >= 70 else "badge-bad"
        return f'<span class="{cls}">{fmt_pct_c(v)}</span>'

    # =========================================================
    # TÍTULO COMPACTO CLARO
    # =========================================================
    filtros_txt = []
    if agente_sel:      filtros_txt.append(f"{len(agente_sel)} agente{'s' if len(agente_sel)>1 else ''}")
    if cat_sel:         filtros_txt.append(f"{len(cat_sel)} categoría{'s' if len(cat_sel)>1 else ''}")
    if zona_sel:        filtros_txt.append(f"{len(zona_sel)} zona{'s' if len(zona_sel)>1 else ''}")
    if tipo_sel:        filtros_txt.append(f"{len(tipo_sel)} tipo{'s' if len(tipo_sel)>1 else ''}")
    if tipol_sel:       filtros_txt.append(f"{len(tipol_sel)} tipología{'s' if len(tipol_sel)>1 else ''}")
    if clasif_sel:      filtros_txt.append(f"{len(clasif_sel)} clasificación{'es' if len(clasif_sel)>1 else ''}")
    if asesor_sel:      filtros_txt.append(f"{len(asesor_sel)} asesor{'es' if len(asesor_sel)>1 else ''}")
    if circuito_sel_c:  filtros_txt.append(f"{len(circuito_sel_c)} circuito{'s' if len(circuito_sel_c)>1 else ''}")
    if ruta_sel_c:      filtros_txt.append(f"{len(ruta_sel_c)} ruta{'s' if len(ruta_sel_c)>1 else ''}")
    if barrio_sel_c:    filtros_txt.append(f"{len(barrio_sel_c)} barrio{'s' if len(barrio_sel_c)>1 else ''}")
    if cumpl_min > 0 or cumpl_max < 200: filtros_txt.append(f"Cumpl. {cumpl_min}-{cumpl_max}%")
    filtros_str = " · ".join(filtros_txt) if filtros_txt else "Sin filtros adicionales — universo completo"

    top_agente = df.groupby("AGENTE")["EJEC ALTA NAT"].sum().idxmax() if df["EJEC ALTA NAT"].sum() > 0 else "N/D"
    top_asesor_s = df.groupby("ASESOR")["EJE ALTA TOTAL"].sum()
    top_asesor = top_asesor_s.idxmax() if not top_asesor_s.empty and top_asesor_s.sum() > 0 else "N/D"
    top_asesor_val = int(top_asesor_s.max()) if not top_asesor_s.empty else 0

    st.markdown(f"""
    <div class="header-shell">
        <div style="position:relative;z-index:2;">
            <div class="hero-badge">{icon_svg("spark",13)} Panel Claro · Agentes y PDVs</div>
            <div style="font-size:0.84rem;color:#94A3B8;font-weight:800;letter-spacing:0.55px;">GERENCIA R4 PREPAGO — SEGUIMIENTO COMERCIAL</div>
            <div class="hero-title">Agentes Claro · Abril 2026 - Prototipo</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Cálculos previos necesarios para el nav guide ─────────────────────────
    _DIA_CORTE_NAV = 28; _DIAS_MES_NAV = 30; _FACTOR_NAV = _DIAS_MES_NAV / _DIA_CORTE_NAV
    _proy_global   = (ejec_nat_total * _FACTOR_NAV / meta_nat_total * 100) if meta_nat_total > 0 else 0
    _cumpl_nav     = (ejec_nat_total / meta_nat_total * 100) if meta_nat_total > 0 else 0
    _pdvs_riesgo   = int(((df["META ALTA NAT (>$2000)"] > 0) &
                          ((df["EJEC ALTA NAT"] / df["META ALTA NAT (>$2000)"].replace(0,np.nan)*100).fillna(0) < 70)).sum())
    _by_ag_nav     = df.groupby("AGENTE").agg(ejec_nat=("EJEC ALTA NAT","sum"), meta_nat=("META ALTA NAT (>$2000)","sum")).reset_index()
    _by_ag_nav["proy"] = (_by_ag_nav["ejec_nat"] * _FACTOR_NAV / _by_ag_nav["meta_nat"].replace(0,np.nan) * 100).fillna(0)
    _ag_riesgo     = (_by_ag_nav["proy"] < 70).sum()
    _s_vals_nav    = {s: float(df[s].sum()) if s in df.columns else 0.0 for s in ["S1","S2","S3","S4"]}
    _s_list        = [_s_vals_nav["S1"],_s_vals_nav["S2"],_s_vals_nav["S3"],_s_vals_nav["S4"]]
    _tendencia_ok  = _s_list[2] >= _s_list[1] >= _s_list[0]
    _sem_c         = lambda v: "#22C55E" if v>=100 else "#F59E0B" if v>=70 else "#EF4444"
    _dot           = lambda v: f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{_sem_c(v)};margin-right:5px;flex-shrink:0;"></span>'

    # ── Franja de navegación visual ───────────────────────────────────────────
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:12px 0 4px 0;">
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:12px 14px;cursor:pointer;">
            <div style="font-size:1.1rem;margin-bottom:4px;">📊</div>
            <div style="font-size:.78rem;font-weight:900;color:#F8FAFC;margin-bottom:3px;">¿Cómo vamos?</div>
            <div style="font-size:.70rem;color:#94A3B8;margin-bottom:6px;">Estado del mes y proyección</div>
            <div style="display:flex;align-items:center;font-size:.72rem;font-weight:800;color:{_sem_c(_proy_global)};">{_dot(_proy_global)}Proyección {_proy_global:.0f}%</div>
        </div>
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:12px 14px;">
            <div style="font-size:1.1rem;margin-bottom:4px;">👥</div>
            <div style="font-size:.78rem;font-weight:900;color:#F8FAFC;margin-bottom:3px;">¿Quién cumple?</div>
            <div style="font-size:.70rem;color:#94A3B8;margin-bottom:6px;">Agentes vs su meta</div>
            <div style="display:flex;align-items:center;font-size:.72rem;font-weight:800;color:{_sem_c(100 if _ag_riesgo==0 else 70 if _ag_riesgo<=2 else 0)};">{_dot(100 if _ag_riesgo==0 else 70 if _ag_riesgo<=2 else 0)}{_ag_riesgo} agente{'s' if _ag_riesgo!=1 else ''} en riesgo</div>
        </div>
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:12px 14px;">
            <div style="font-size:1.1rem;margin-bottom:4px;">📍</div>
            <div style="font-size:.78rem;font-weight:800;color:#F8FAFC;margin-bottom:3px;">¿Dónde está la brecha?</div>
            <div style="font-size:.70rem;color:#94A3B8;margin-bottom:6px;">PDVs y circuitos críticos</div>
            <div style="display:flex;align-items:center;font-size:.72rem;font-weight:800;color:{_sem_c(0 if _pdvs_riesgo>5000 else 70 if _pdvs_riesgo>2000 else 100)};">{_dot(0 if _pdvs_riesgo>5000 else 70 if _pdvs_riesgo>2000 else 100)}{_pdvs_riesgo:,} PDVs con brecha</div>
        </div>
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:12px 14px;">
            <div style="font-size:1.1rem;margin-bottom:4px;">📈</div>
            <div style="font-size:.78rem;font-weight:900;color:#F8FAFC;margin-bottom:3px;">¿Sube el ritmo?</div>
            <div style="font-size:.70rem;color:#94A3B8;margin-bottom:6px;">Curva semanal de ventas</div>
            <div style="display:flex;align-items:center;font-size:.72rem;font-weight:800;color:{'#22C55E' if _tendencia_ok else '#EF4444'};">{'▲' if _tendencia_ok else '▼'} {'Tendencia positiva' if _tendencia_ok else 'Tendencia a la baja'}</div>
        </div>
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:12px 14px;">
            <div style="font-size:1.1rem;margin-bottom:4px;">🎯</div>
            <div style="font-size:.78rem;font-weight:900;color:#F8FAFC;margin-bottom:3px;">¿Dónde ganar más?</div>
            <div style="font-size:.70rem;color:#94A3B8;margin-bottom:6px;">Cuota de altas y señal</div>
            <div style="display:flex;align-items:center;font-size:.72rem;font-weight:800;color:#38BDF8;">→ Ver oportunidades</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================
    # TABS
    # =========================================================
    tc1, tc2, tc3, tc4, tc5 = st.tabs([
        "📊  ¿Cómo vamos?",
        "👥  ¿Quién cumple?",
        "📍  ¿Dónde está la brecha?",
        "📈  ¿Sube el ritmo?",
        "🎯  ¿Dónde ganar más?",
    ])

    # -------------------------------------------------------
    # TAB C1 — ¿CÓMO VAMOS?
    # -------------------------------------------------------
    with tc1:
        _DIA_CORTE = 28; _DIAS_MES = 30; _FACTOR = _DIAS_MES / _DIA_CORTE
        brecha_nat      = meta_nat_total - ejec_nat_total
        _proy_fin_mes   = ejec_nat_total * _FACTOR
        _proy_vs_meta   = (_proy_fin_mes / meta_nat_total * 100) if meta_nat_total > 0 else 0
        _altas_dia_real = ejec_nat_total / _DIA_CORTE
        _meta_dia       = meta_nat_total / _DIAS_MES
        _ritmo_pct      = (_altas_dia_real / _meta_dia * 100) if _meta_dia > 0 else 0
        _pdvs_con_meta  = int((df["META ALTA NAT (>$2000)"] > 0).sum())
        _cumpl_pdv_ser  = (df["EJEC ALTA NAT"] / df["META ALTA NAT (>$2000)"].replace(0, np.nan) * 100).fillna(0)
        _pdvs_bajo70    = int(((df["META ALTA NAT (>$2000)"] > 0) & (_cumpl_pdv_ser < 70)).sum())
        _pct_bajo70     = (_pdvs_bajo70 / _pdvs_con_meta * 100) if _pdvs_con_meta > 0 else 0
        _var_alta_media = pd.to_numeric(df["VR_M-1.1"], errors="coerce").mean() if "VR_M-1.1" in df.columns else np.nan

        def _sc(v): return "#22C55E" if v >= 100 else "#F59E0B" if v >= 70 else "#EF4444"
        def _bar(pct, color):
            w = min(max(pct, 0), 100)
            return f'<div style="width:100%;height:6px;background:rgba(255,255,255,0.08);border-radius:99px;margin-top:6px;overflow:hidden;"><div style="width:{w}%;height:100%;background:{color};border-radius:99px;transition:width .4s ease;"></div></div>'

        # ── Número protagonista ───────────────────────────────────────────────
        _c_proy = _sc(_proy_vs_meta)
        _estado_txt = "✅ La meta está en camino" if _proy_vs_meta >= 100 else ("⚠️ Recuperable con esfuerzo" if _proy_vs_meta >= 85 else "🔴 Meta en riesgo — se necesita acción")
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.96),rgba(10,18,34,0.98));border:1px solid rgba(255,255,255,0.10);border-radius:24px;padding:24px 28px;margin-bottom:16px;display:flex;align-items:center;gap:32px;">
            <div style="flex:0 0 auto;">
                <div style="font-size:.72rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;">Proyección al cierre del mes</div>
                <div style="font-size:3.8rem;font-weight:950;color:{_c_proy};line-height:1;">{_proy_vs_meta:.1f}%</div>
                <div style="font-size:.84rem;color:#CBD5E1;margin-top:6px;">{_estado_txt}</div>
                {_bar(_proy_vs_meta, _c_proy)}
            </div>
            <div style="width:1px;height:80px;background:rgba(255,255,255,0.08);flex-shrink:0;"></div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;flex:1;">
                <div>
                    <div style="font-size:.68rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.3px;margin-bottom:2px;">Cumplimiento hoy</div>
                    <div style="font-size:1.55rem;font-weight:900;color:{_sc(cumplimiento_nat if pd.notna(cumplimiento_nat) else 0)};">{fmt_pct_c(cumplimiento_nat)}</div>
                    <div style="font-size:.72rem;color:#64748B;">{fmt_int(ejec_nat_total)} de {fmt_int(meta_nat_total)}</div>
                    {_bar(cumplimiento_nat if pd.notna(cumplimiento_nat) else 0, _sc(cumplimiento_nat if pd.notna(cumplimiento_nat) else 0))}
                </div>
                <div>
                    <div style="font-size:.68rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.3px;margin-bottom:2px;">Ritmo diario</div>
                    <div style="font-size:1.55rem;font-weight:900;color:{_sc(_ritmo_pct)};">{fmt_int(_altas_dia_real)}<span style="font-size:.9rem;font-weight:600;"> /día</span></div>
                    <div style="font-size:.72rem;color:#64748B;">Meta: {fmt_int(_meta_dia)}/día</div>
                    {_bar(_ritmo_pct, _sc(_ritmo_pct))}
                </div>
                <div>
                    <div style="font-size:.68rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.3px;margin-bottom:2px;">PDVs con brecha</div>
                    <div style="font-size:1.55rem;font-weight:900;color:{_sc(100-_pct_bajo70)};">{fmt_int(_pdvs_bajo70)}</div>
                    <div style="font-size:.72rem;color:#64748B;">{_pct_bajo70:.0f}% del portafolio activo</div>
                    {_bar(100-_pct_bajo70, _sc(100-_pct_bajo70))}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Tarjetas de agente con barra de progreso ──────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:8px;">Proyección por agente al cierre del mes</div>', unsafe_allow_html=True)
        by_agente = df.groupby("AGENTE").agg(
            pdvs=("ID","count"), meta_nat=("META ALTA NAT (>$2000)","sum"),
            ejec_nat=("EJEC ALTA NAT","sum"), ejec_total=("EJE ALTA TOTAL","sum"),
            cuota_alta=("CUOTA DE ALTA","mean"),
            var_alta=("VR_M-1.1","mean") if "VR_M-1.1" in df.columns else ("EJEC ALTA NAT","count"),
        ).reset_index()
        by_agente["cumpl"]    = (by_agente["ejec_nat"] / by_agente["meta_nat"].replace(0,np.nan)*100).fillna(0)
        by_agente["brecha"]   = by_agente["meta_nat"] - by_agente["ejec_nat"]
        by_agente["proy_pct"] = (by_agente["ejec_nat"]*_FACTOR / by_agente["meta_nat"].replace(0,np.nan)*100).fillna(0)
        by_agente["alt_dia"]  = by_agente["ejec_nat"] / _DIA_CORTE
        _max_p = by_agente["proy_pct"].max(); _min_p = by_agente["proy_pct"].min()

        n_ag = min(len(by_agente), 4)
        ag_cols = st.columns(n_ag, gap="small")
        for i, row in by_agente.sort_values("proy_pct", ascending=False).reset_index(drop=True).iterrows():
            ag_c   = AGENTE_COLORS.get(row["AGENTE"], AGENTE_COLORS.get(str(row["AGENTE"]).strip(), "#64748B"))
            p      = row["proy_pct"]; cp = _sc(p)
            badge  = "🏆" if p == _max_p else ("⚠️" if p == _min_p else "")
            _var_a = row.get("var_alta", np.nan)
            _vt    = (f"{'↓' if pd.notna(_var_a) and _var_a < 0 else '↑'}{abs(_var_a):.1f}pp" if pd.notna(_var_a) and "VR_M-1.1" in df.columns else "")
            _vc    = "#EF4444" if pd.notna(_var_a) and _var_a < 0 else "#22C55E"
            with ag_cols[i % n_ag]:
                st.markdown(f"""
                <div class="card" style="min-height:0;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                        <div style="display:flex;align-items:center;gap:6px;">
                            <span style="width:9px;height:9px;border-radius:50%;background:{ag_c};display:inline-block;flex-shrink:0;"></span>
                            <span style="font-size:.74rem;font-weight:900;color:#E2E8F0;">{row["AGENTE"]}</span>
                        </div>
                        <span style="font-size:.80rem;">{badge}</span>
                    </div>
                    <div style="font-size:2rem;font-weight:950;color:{cp};line-height:1.05;">{p:.1f}%</div>
                    <div style="font-size:.68rem;color:#64748B;margin-top:1px;">proyección fin de mes</div>
                    {_bar(p, cp)}
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:8px;">
                        <div style="font-size:.70rem;color:#94A3B8;">Hoy: <span style="color:#F8FAFC;font-weight:800;">{fmt_pct_c(row["cumpl"])}</span></div>
                        <div style="font-size:.70rem;color:#94A3B8;">Brecha: <span style="color:#F8FAFC;font-weight:800;">{fmt_int(row["brecha"])}</span></div>
                        <div style="font-size:.70rem;color:#94A3B8;">Altas/día: <span style="color:#F8FAFC;font-weight:800;">{fmt_int(row["alt_dia"])}</span></div>
                        <div style="font-size:.70rem;color:#94A3B8;">Cuota alta: <span style="color:#F8FAFC;font-weight:800;">{fmt_pct_c(row["cuota_alta"])}</span> <span style="color:{_vc};font-size:.65rem;">{_vt}</span></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        # ── Gráfica de categorías ─────────────────────────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:16px 0 8px 0;">Cumplimiento por categoría de PDV</div>', unsafe_allow_html=True)
        by_cat = df.groupby("CATEGORIA").agg(
            pdvs=("ID","count"), ejec_nat=("EJEC ALTA NAT","sum"),
            meta_nat=("META ALTA NAT (>$2000)","sum"), cuota_alta=("CUOTA DE ALTA","mean"),
        ).reset_index()
        by_cat["cumpl"] = (by_cat["ejec_nat"]/by_cat["meta_nat"].replace(0,np.nan)*100).fillna(0)
        by_cat["proy"]  = (by_cat["ejec_nat"]*_FACTOR/by_cat["meta_nat"].replace(0,np.nan)*100).fillna(0)
        cat_order = ["DIAMANTE","PLATINO","ORO","PLATA","BRONCE"]
        by_cat["CATEGORIA"] = pd.Categorical(by_cat["CATEGORIA"], categories=cat_order, ordered=True)
        by_cat = by_cat.sort_values("CATEGORIA")

        c1a, c1b = st.columns(2, gap="large")
        with c1a:
            st.markdown('<div class="section-card"><div class="section-title">Cumplimiento vs proyección por categoría</div><div class="section-subtitle">🔴 Al corte · 🔸 Proyección fin de mes · línea verde = meta 100%</div>', unsafe_allow_html=True)
            if not by_cat.empty:
                _mc = by_cat[["CATEGORIA","cumpl","proy"]].melt("CATEGORIA", var_name="Tipo", value_name="Valor")
                _mc["Tipo"] = _mc["Tipo"].map({"cumpl":"Al corte (día 28)","proy":"Proyección fin mes"})
                ch = alt.Chart(_mc).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                    x=alt.X("CATEGORIA:N",sort=cat_order,title=None),
                    y=alt.Y("Valor:Q",title="% vs meta"),
                    color=alt.Color("Tipo:N",scale=alt.Scale(domain=["Al corte (día 28)","Proyección fin mes"],range=["#E10600","rgba(225,6,0,0.28)"]),legend=alt.Legend(title="",orient="bottom")),
                    xOffset="Tipo:N",
                    tooltip=[alt.Tooltip("CATEGORIA:N"),alt.Tooltip("Tipo:N"),alt.Tooltip("Valor:Q",format=".1f",title="%")]
                ).properties(height=260)
                r100 = alt.Chart(pd.DataFrame({"y":[100]})).mark_rule(color="#22C55E",strokeDash=[5,3],strokeWidth=2).encode(y="y:Q")
                st.altair_chart(style_chart(ch+r100), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with c1b:
            st.markdown('<div class="section-card"><div class="section-title">Cuota de altas Claro por categoría</div><div class="section-subtitle">% de las ventas nuevas que son de Claro · línea azul = 50% (paridad)</div>', unsafe_allow_html=True)
            if not by_cat.empty:
                ch2 = alt.Chart(by_cat).mark_bar(cornerRadiusTopLeft=6,cornerRadiusTopRight=6).encode(
                    x=alt.X("CATEGORIA:N",sort=cat_order,title=None),
                    y=alt.Y("cuota_alta:Q",title="Cuota altas (%)"),
                    color=alt.Color("CATEGORIA:N",scale=alt.Scale(domain=cat_order,range=[CATEGORIA_COLORS.get(c,"#64748B") for c in cat_order]),legend=None),
                    tooltip=[alt.Tooltip("CATEGORIA:N"),alt.Tooltip("cuota_alta:Q",format=".1f",title="Cuota alta %"),alt.Tooltip("cumpl:Q",format=".1f",title="Cumpl. %"),alt.Tooltip("pdvs:Q",title="PDVs")]
                ).properties(height=260)
                r50 = alt.Chart(pd.DataFrame({"y":[50]})).mark_rule(color="#38BDF8",strokeDash=[5,3],strokeWidth=1.5).encode(y="y:Q")
                st.altair_chart(style_chart(ch2+r50), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------
    # TAB C2 — ¿QUIÉN CUMPLE?
    # -------------------------------------------------------
    with tc2:
        _DIA_CORTE = 28; _DIAS_MES = 30
        by_ag_full = df.groupby("AGENTE").agg(
            pdvs=("ID","count"), meta_nat=("META ALTA NAT (>$2000)","sum"),
            ejec_nat=("EJEC ALTA NAT","sum"), meta_indu=("META ALTA INDU (=< $2.000)","sum"),
            ejec_indu=("EJEC ALTA INDU","sum"), ejec_total=("EJE ALTA TOTAL","sum"),
            cuota_alta=("CUOTA DE ALTA","mean"), rsrp=("RSRP","mean"),
        ).reset_index()
        by_ag_full["cumpl_nat"] = (by_ag_full["ejec_nat"]/by_ag_full["meta_nat"].replace(0,np.nan)*100).fillna(0)
        by_ag_full["proy_nat"]  = (by_ag_full["ejec_nat"]*(_DIAS_MES/_DIA_CORTE)/by_ag_full["meta_nat"].replace(0,np.nan)*100).fillna(0)
        by_ag_full["part_ejec"] = (by_ag_full["ejec_nat"]/by_ag_full["ejec_nat"].sum()*100).fillna(0)
        by_ag_full["brecha"]    = by_ag_full["meta_nat"] - by_ag_full["ejec_nat"]

        # ── Ranking visual de agentes ─────────────────────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:8px;">Ranking de agentes — de mejor a peor proyección</div>', unsafe_allow_html=True)
        for _, row in by_ag_full.sort_values("proy_nat", ascending=False).reset_index(drop=True).iterrows():
            ag_c  = AGENTE_COLORS.get(row["AGENTE"], "#64748B")
            p     = row["proy_nat"]; cp = _sc(p)
            w     = min(max(p, 0), 100)
            _brch = fmt_int(row["brecha"])
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:10px 14px;margin-bottom:6px;">
                <div style="display:flex;align-items:center;gap:8px;width:180px;flex-shrink:0;">
                    <span style="width:10px;height:10px;border-radius:50%;background:{ag_c};display:inline-block;flex-shrink:0;"></span>
                    <span style="font-size:.80rem;font-weight:800;color:#F8FAFC;">{row["AGENTE"]}</span>
                </div>
                <div style="flex:1;min-width:0;">
                    <div style="width:100%;height:8px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;">
                        <div style="width:{w}%;height:100%;background:{cp};border-radius:99px;"></div>
                    </div>
                </div>
                <div style="width:52px;text-align:right;font-size:1.05rem;font-weight:900;color:{cp};flex-shrink:0;">{p:.0f}%</div>
                <div style="width:110px;text-align:right;font-size:.72rem;color:#94A3B8;flex-shrink:0;">Hoy: <b style="color:#E2E8F0;">{fmt_pct_c(row["cumpl_nat"])}</b></div>
                <div style="width:130px;text-align:right;font-size:.72rem;color:#94A3B8;flex-shrink:0;">Brecha: <b style="color:#FCA5A5;">{_brch}</b></div>
                <div style="width:110px;text-align:right;font-size:.72rem;color:#94A3B8;flex-shrink:0;">Cuota alta: <b style="color:#E2E8F0;">{fmt_pct_c(row["cuota_alta"])}</b></div>
                <div style="width:80px;text-align:right;font-size:.72rem;color:#94A3B8;flex-shrink:0;">PDVs: <b style="color:#E2E8F0;">{fmt_int(row["pdvs"])}</b></div>
            </div>""", unsafe_allow_html=True)

        # ── Dos gráficas clave ────────────────────────────────────────────────
        a2_l, a2_r = st.columns(2, gap="large")
        with a2_l:
            st.markdown('<div class="section-card"><div class="section-title">Meta vs ejecución por agente</div><div class="section-subtitle">Barra blanca = meta · barra roja = ejecutado. Si la roja supera la blanca, cumplió.</div>', unsafe_allow_html=True)
            melt_ag = by_ag_full[["AGENTE","meta_nat","ejec_nat"]].melt(id_vars="AGENTE",var_name="Tipo",value_name="Valor")
            melt_ag["Tipo"] = melt_ag["Tipo"].map({"meta_nat":"Meta","ejec_nat":"Ejecutado"})
            chart_ag = alt.Chart(melt_ag).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                x=alt.X("AGENTE:N",title=None,axis=alt.Axis(labelAngle=-20)),
                y=alt.Y("Valor:Q",title="Altas orgánicas"),
                color=alt.Color("Tipo:N",scale=alt.Scale(domain=["Meta","Ejecutado"],range=["rgba(255,255,255,0.15)","#E10600"]),legend=alt.Legend(title="",orient="bottom")),
                xOffset="Tipo:N",
                tooltip=[alt.Tooltip("AGENTE:N"),alt.Tooltip("Tipo:N"),alt.Tooltip("Valor:Q",format=",.0f",title="Altas")]
            ).properties(height=280)
            st.altair_chart(style_chart(chart_ag), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with a2_r:
            st.markdown('<div class="section-card"><div class="section-title">Cumplimiento vs cuota de altas por agente</div><div class="section-subtitle">🔴 Cumplimiento meta nat. · 🔵 Cuota altas Claro · línea verde = 100%</div>', unsafe_allow_html=True)
            by_ag_dual = by_ag_full[["AGENTE","cumpl_nat","cuota_alta"]].melt("AGENTE",var_name="Indicador",value_name="Valor")
            by_ag_dual["Indicador"] = by_ag_dual["Indicador"].map({"cumpl_nat":"Cumplimiento %","cuota_alta":"Cuota altas %"})
            chart_dual = alt.Chart(by_ag_dual).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                y=alt.Y("AGENTE:N",title=None,sort="-x"),
                x=alt.X("Valor:Q",title="%"),
                color=alt.Color("Indicador:N",scale=alt.Scale(domain=["Cumplimiento %","Cuota altas %"],range=["#E10600","#38BDF8"]),legend=alt.Legend(title="",orient="bottom")),
                yOffset="Indicador:N",
                tooltip=[alt.Tooltip("AGENTE:N"),alt.Tooltip("Indicador:N"),alt.Tooltip("Valor:Q",format=".1f",title="%")]
            ).properties(height=280)
            r100h = alt.Chart(pd.DataFrame({"x":[100]})).mark_rule(color="#22C55E",strokeDash=[5,3],strokeWidth=1.5).encode(x="x:Q")
            st.altair_chart(style_chart(chart_dual+r100h), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Tabla resumen compacta ────────────────────────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:12px 0 6px 0;">Detalle completo por agente</div>', unsafe_allow_html=True)
        show_ag = safe_round_columns(by_ag_full[["AGENTE","pdvs","meta_nat","ejec_nat","cumpl_nat","proy_nat","brecha","cuota_alta"]].copy(),
            ["meta_nat","ejec_nat","cumpl_nat","proy_nat","brecha","cuota_alta"])
        show_ag.columns = ["Agente","PDVs","Meta","Ejecutado","Cumpl. %","Proy. %","Brecha","Cuota Alta %"]
        st.dataframe(show_ag, use_container_width=True, height=240)

    # -------------------------------------------------------
    # TAB C3 — PDVs Y CIRCUITOS
    # -------------------------------------------------------
    with tc3:
        st.markdown(stage_header(
            "03 · PDVs y Circuitos",
            "Granularidad territorial y comercial",
            "Desempeño por circuito, tipología de PDV, clasificación comercial y asesores con mayor aporte.",
            "map", "red", show_badges=False
        ), unsafe_allow_html=True)

        # Top asesores
        by_asesor = df.groupby(["ASESOR","AGENTE"]).agg(
            pdvs=("ID", "count"),
            meta_nat=("META ALTA NAT (>$2000)", "sum"),
            ejec_nat=("EJEC ALTA NAT", "sum"),
            ejec_total=("EJE ALTA TOTAL", "sum"),
        ).reset_index()
        by_asesor["cumpl"] = (by_asesor["ejec_nat"] / by_asesor["meta_nat"].replace(0, np.nan) * 100).fillna(0)
        by_asesor = by_asesor.sort_values("ejec_total", ascending=False).head(20)

        c3a, c3b = st.columns(2, gap="large")
        with c3a:
            st.markdown('<div class="section-card"><div class="section-title">Top 15 asesores por altas vendidas</div><div class="section-subtitle">Cada barra = un asesor. El color indica a qué agente pertenece. La longitud de la barra = altas totales vendidas (orgánicas + inducidas). Pasa el mouse para ver cumplimiento y PDVs a cargo.</div>', unsafe_allow_html=True)
            chart_asesor = alt.Chart(by_asesor.head(15)).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X("ejec_total:Q", title="Total altas vendidas (orgánicas + inducidas)"),
                y=alt.Y("ASESOR:N", sort="-x", title=None, axis=alt.Axis(labelLimit=200)),
                color=alt.Color("AGENTE:N",
                    scale=alt.Scale(domain=list(AGENTE_COLORS.keys()), range=list(AGENTE_COLORS.values())),
                    legend=alt.Legend(title="Agente al que pertenece")),
                tooltip=[
                    alt.Tooltip("ASESOR:N", title="Asesor"),
                    alt.Tooltip("AGENTE:N", title="Agente"),
                    alt.Tooltip("ejec_total:Q", format=",.0f", title="Altas totales ejecutadas"),
                    alt.Tooltip("ejec_nat:Q", format=",.0f", title="Altas orgánicas (>$2.000)"),
                    alt.Tooltip("cumpl:Q", format=".1f", title="Cumplimiento meta %"),
                    alt.Tooltip("pdvs:Q", title="PDVs a cargo"),
                ]
            ).properties(height=380)
            st.altair_chart(style_chart(chart_asesor), use_container_width=True, theme=None)
            st.markdown('<div style="font-size:0.74rem;color:#94A3B8;margin-top:4px;">El color de cada barra indica el agente supervisor. Los asesores de un mismo agente se ven del mismo color.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c3b:
            # Top barrios por ejecución (con circuitos como contexto)
            barrio_col_exists = "BARRIO" in df.columns
            circuito_col_exists = "CIRCUITO" in df.columns
            group_cols_circ = []
            if barrio_col_exists:
                group_cols_circ.append("BARRIO")
            if circuito_col_exists:
                group_cols_circ.append("CIRCUITO")
            if not group_cols_circ:
                group_cols_circ = ["CIRCUITO"] if circuito_col_exists else ["AGENTE"]

            by_barrio = df.groupby(group_cols_circ).agg(
                pdvs=("ID", "count"),
                meta_nat=("META ALTA NAT (>$2000)", "sum"),
                ejec_nat=("EJEC ALTA NAT", "sum"),
                ejec_total=("EJE ALTA TOTAL", "sum"),
                cuota_alta=("CUOTA DE ALTA", "mean"),
            ).reset_index()
            by_barrio["cumpl"] = (by_barrio["ejec_nat"] / by_barrio["meta_nat"].replace(0, np.nan) * 100).fillna(0)

            if barrio_col_exists:
                by_barrio_top = by_barrio.groupby("BARRIO").agg(
                    ejec_total=("ejec_total", "sum"),
                    meta_nat=("meta_nat", "sum"),
                    ejec_nat=("ejec_nat", "sum"),
                    pdvs=("pdvs", "sum"),
                    cuota_alta=("cuota_alta", "mean"),
                ).reset_index()
                by_barrio_top["cumpl"] = (by_barrio_top["ejec_nat"] / by_barrio_top["meta_nat"].replace(0, np.nan) * 100).fillna(0)
                # Attach list of circuitos per barrio
                if circuito_col_exists:
                    circ_per_barrio = by_barrio.groupby("BARRIO")["CIRCUITO"].apply(lambda x: ", ".join(sorted(x.dropna().unique()))).reset_index()
                    circ_per_barrio.columns = ["BARRIO", "circuitos_lista"]
                    by_barrio_top = by_barrio_top.merge(circ_per_barrio, on="BARRIO", how="left")
                else:
                    by_barrio_top["circuitos_lista"] = ""
                by_barrio_top = by_barrio_top.sort_values("ejec_total", ascending=False).head(15)
                y_col = "BARRIO"
                tooltip_extra = [alt.Tooltip("circuitos_lista:N", title="Circuitos")]
            else:
                by_barrio_top = by_barrio.sort_values("ejec_total", ascending=False).head(15)
                y_col = "CIRCUITO"
                tooltip_extra = []

            st.markdown('<div class="section-card"><div class="section-title">Top barrios por ejecución</div><div class="section-subtitle">Eje Y = barrio principal. Debajo del nombre aparecen los circuitos asociados. El color de semáforo indica si ese barrio cumplió su meta de altas: 🟢 ≥100% · 🟡 70–99% · 🔴 &lt;70%. La longitud de la barra refleja el total de altas ejecutadas.</div>', unsafe_allow_html=True)
            chart_circ = alt.Chart(by_barrio_top).transform_calculate(
                color_semaforo="datum.cumpl >= 100 ? '#22C55E' : datum.cumpl >= 70 ? '#F59E0B' : '#EF4444'"
            ).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X("ejec_total:Q", title="Altas totales"),
                y=alt.Y(f"{y_col}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
                color=alt.Color("color_semaforo:N", scale=None, legend=None),
                tooltip=[
                    alt.Tooltip(f"{y_col}:N", title="Barrio" if y_col == "BARRIO" else "Circuito"),
                    alt.Tooltip("pdvs:Q", title="PDVs"),
                    alt.Tooltip("ejec_total:Q", format=",.0f", title="Ejec. total"),
                    alt.Tooltip("cumpl:Q", format=".1f", title="Cumpl. %"),
                    alt.Tooltip("cuota_alta:Q", format=".1f", title="Cuota alta %"),
                ] + tooltip_extra
            ).properties(height=380)
            st.altair_chart(style_chart(chart_circ), use_container_width=True, theme=None)
            if barrio_col_exists and circuito_col_exists and not by_barrio_top.empty:
                # Show small table mapping barrio → circuitos below chart
                st.markdown('<div style="font-size:0.72rem;color:#94A3B8;margin-top:6px;margin-bottom:4px;font-weight:700;text-transform:uppercase;letter-spacing:0.3px;">Barrios y sus circuitos:</div>', unsafe_allow_html=True)
                for _, row_b in by_barrio_top.head(8).iterrows():
                    circs = row_b.get("circuitos_lista", "")
                    st.markdown(f'<div style="font-size:0.74rem;color:#F8FAFC;margin-bottom:3px;"><b>{row_b["BARRIO"]}</b> <span style="color:#94A3B8;font-size:0.68rem;">— {circs}</span></div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.74rem;color:#94A3B8;margin-top:6px;">🟢 Verde = meta cumplida · 🟡 Amarillo = 70-99% · 🔴 Rojo = &lt;70%. Pasa el mouse para ver cuota de altas y circuitos del barrio.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Clasificación comercial
        st.markdown(lane_label("Clasificación y tipología de PDVs", "map"), unsafe_allow_html=True)
        c3c, c3d = st.columns(2, gap="large")

        with c3c:
            by_clasif = df.groupby("CLASIFICACION").agg(
                pdvs=("ID", "count"),
                ejec_nat=("EJEC ALTA NAT", "sum"),
                meta_nat=("META ALTA NAT (>$2000)", "sum"),
            ).reset_index().sort_values("ejec_nat", ascending=False).head(12)

            st.markdown('<div class="section-card"><div class="section-title">Altas por clasificación de PDV</div><div class="section-subtitle">¿En qué tipo de punto de venta se generan más altas? Tiendas, cigarrerías, papelerías, etc. El eje muestra el total acumulado de altas orgánicas.</div>', unsafe_allow_html=True)
            if not by_clasif.empty:
                chart_cl = alt.Chart(by_clasif).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                    x=alt.X("ejec_nat:Q", title="Altas nat."),
                    y=alt.Y("CLASIFICACION:N", sort="-x", title=None, axis=alt.Axis(labelLimit=200)),
                    color=alt.value("#38BDF8"),
                    tooltip=[alt.Tooltip("CLASIFICACION:N"), alt.Tooltip("pdvs:Q", title="PDVs"), alt.Tooltip("ejec_nat:Q", format=",.0f")]
                ).properties(height=300)
                st.altair_chart(style_chart(chart_cl), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with c3d:
            by_tipo = df.groupby("TIPOLOGIA").agg(
                pdvs=("ID", "count"),
                ejec_nat=("EJEC ALTA NAT", "sum"),
                meta_nat=("META ALTA NAT (>$2000)", "sum"),
            ).reset_index()
            by_tipo["cumpl"] = (by_tipo["ejec_nat"] / by_tipo["meta_nat"].replace(0, np.nan) * 100).fillna(0)

            st.markdown('<div class="section-card"><div class="section-title">Ejecución por tipología de PDV</div><div class="section-subtitle">Tipología A = PDV más grande y de mayor potencial, D = más pequeño. El color de cada barra indica si ese tipo de PDV está cumpliendo su meta (🟢) o tiene brecha (🔴).</div>', unsafe_allow_html=True)
            if not by_tipo.empty:
                chart_tip = alt.Chart(by_tipo).transform_calculate(
                    color_semaforo="datum.cumpl >= 100 ? '#22C55E' : datum.cumpl >= 70 ? '#F59E0B' : '#EF4444'"
                ).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                    x=alt.X("TIPOLOGIA:N", title=None),
                    y=alt.Y("ejec_nat:Q", title="Altas nat."),
                    color=alt.Color("color_semaforo:N", scale=None, legend=None),
                    tooltip=[alt.Tooltip("TIPOLOGIA:N"), alt.Tooltip("pdvs:Q", title="PDVs"),
                             alt.Tooltip("ejec_nat:Q", format=",.0f"), alt.Tooltip("cumpl:Q", format=".1f", title="Cumpl. %")]
                ).properties(height=300)
                st.altair_chart(style_chart(chart_tip), use_container_width=True, theme=None)
                st.markdown('<div style="font-size:0.74rem;color:#94A3B8;margin-top:4px;">Pasa el mouse para ver cuántos PDVs hay en cada tipología y su % de cumplimiento.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Tabla de rutas con mayor oportunidad de mejora
        st.markdown(lane_label("Rutas con mayor oportunidad de mejora", "target"), unsafe_allow_html=True)
        ruta_col_exists_opp = "RUTA" in df.columns
        if ruta_col_exists_opp:
            df_ruta_opp = df[df["META ALTA NAT (>$2000)"] > 0].copy()
            df_ruta_opp["cumpl_pdv"] = (df_ruta_opp["EJEC ALTA NAT"] / df_ruta_opp["META ALTA NAT (>$2000)"] * 100).fillna(0)
            ruta_group_cols = ["RUTA"]
            if "AGENTE" in df_ruta_opp.columns:
                ruta_group_cols.append("AGENTE")
            if "BARRIO" in df_ruta_opp.columns:
                ruta_group_cols.append("BARRIO")
            ruta_opp = df_ruta_opp.groupby(ruta_group_cols).agg(
                pdvs_totales=("ID", "count"),
                pdvs_criticos=("cumpl_pdv", lambda x: (x < 70).sum()),
                meta_total=("META ALTA NAT (>$2000)", "sum"),
                ejec_total=("EJEC ALTA NAT", "sum"),
            ).reset_index()
            ruta_opp["cumpl_ruta"] = (ruta_opp["ejec_total"] / ruta_opp["meta_total"].replace(0, np.nan) * 100).fillna(0)
            ruta_opp["brecha"] = ruta_opp["meta_total"] - ruta_opp["ejec_total"]
            ruta_opp["pct_pdvs_criticos"] = (ruta_opp["pdvs_criticos"] / ruta_opp["pdvs_totales"].replace(0, np.nan) * 100).fillna(0)
            ruta_opp = ruta_opp[ruta_opp["cumpl_ruta"] < 70].sort_values("brecha", ascending=False).head(20)

            st.markdown(f"""
            <div class="section-card">
                <div class="anchor-note">
                    <div class="anchor-note-body">
                        <b>¿Para qué sirve esta tabla?</b> Identifica las <b>rutas más críticas</b> que necesitan intervención inmediata:
                        aquellas con mayor brecha absoluta entre meta y ejecución, con cumplimiento bajo el 70%.
                        Están ordenadas de mayor a menor brecha — las primeras son las que más impacto tendrían al intervenir.
                        El campo <b>PDVs críticos</b> indica cuántos puntos de venta en esa ruta también están por debajo del 70%.
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(table_shell(f"Rutas críticas con mayor oportunidad — {len(ruta_opp)} rutas identificadas"), unsafe_allow_html=True)
            if not ruta_opp.empty:
                ruta_rename = {"RUTA": "Ruta", "AGENTE": "Agente", "BARRIO": "Barrio",
                               "pdvs_totales": "PDVs totales", "pdvs_criticos": "PDVs críticos",
                               "meta_total": "Meta altas", "ejec_total": "Altas ejecutadas",
                               "cumpl_ruta": "Cumpl. %", "brecha": "Brecha",
                               "pct_pdvs_criticos": "% PDVs críticos"}
                show_ruta_cols = [c for c in ruta_rename.keys() if c in ruta_opp.columns]
                show_ruta = safe_round_columns(ruta_opp[show_ruta_cols].copy(), ["meta_total","ejec_total","cumpl_ruta","brecha","pct_pdvs_criticos"])
                show_ruta = show_ruta.rename(columns={k:v for k,v in ruta_rename.items() if k in show_ruta.columns})
                st.dataframe(show_ruta, use_container_width=True, height=300)
                st.markdown('<div style="font-size:0.74rem;color:#94A3B8;margin-top:4px;">Ordenado por mayor brecha (meta - ejecución). Las rutas arriba de la lista son las de intervención más urgente.</div>', unsafe_allow_html=True)
            else:
                st.success("✅ No hay rutas con cumplimiento por debajo del 70%.")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No se encontró la columna RUTA en los datos para calcular oportunidades por ruta.")

        # Tabla PDVs con bajo cumplimiento
        st.markdown(lane_label("PDVs con oportunidad de mejora", "target"), unsafe_allow_html=True)
        df_opp = df[df["META ALTA NAT (>$2000)"] > 0].copy()
        df_opp["cumpl_pdv"] = (df_opp["EJEC ALTA NAT"] / df_opp["META ALTA NAT (>$2000)"] * 100).fillna(0)
        df_opp_show = df_opp[df_opp["cumpl_pdv"] < 70].sort_values("META ALTA NAT (>$2000)", ascending=False).head(30)

        st.markdown(f'<div class="section-card"><div class="anchor-note"><div class="anchor-note-body"><b>¿Para qué sirve esta tabla?</b> Muestra los PDVs que tienen meta asignada pero aún están por debajo del 70% de cumplimiento. Son los puntos donde hay mayor oportunidad de recuperar ventas. Están ordenados por meta: los de mayor meta arriba.</div></div>', unsafe_allow_html=True)
        st.markdown(table_shell(f"PDVs con cumplimiento por debajo del 70% — {len(df_opp_show)} PDVs identificados"), unsafe_allow_html=True)
        if not df_opp_show.empty:
            extra_cols = [c for c in ["BARRIO", "ZONA", "RUTA"] if c in df_opp_show.columns]
            cols_show = [c for c in ["ID", "AGENTE", "ASESOR", "CIRCUITO"] + extra_cols + ["CLASIFICACION", "CATEGORIA",
                                     "META ALTA NAT (>$2000)", "EJEC ALTA NAT", "cumpl_pdv"] if c in df_opp_show.columns]
            show_opp = df_opp_show[cols_show].copy()
            show_opp = safe_round_columns(show_opp, ["META ALTA NAT (>$2000)", "EJEC ALTA NAT", "cumpl_pdv"])
            rename_opp = {"META ALTA NAT (>$2000)": "Meta altas", "EJEC ALTA NAT": "Altas ejecutadas",
                          "cumpl_pdv": "Cumpl. %", "ID": "ID PDV", "AGENTE": "Agente", "ASESOR": "Asesor",
                          "CIRCUITO": "Circuito", "CLASIFICACION": "Clasificación", "CATEGORIA": "Categoría",
                          "BARRIO": "Barrio", "ZONA": "Zona", "RUTA": "Ruta"}
            show_opp = show_opp.rename(columns={k:v for k,v in rename_opp.items() if k in show_opp.columns})
            st.dataframe(show_opp, use_container_width=True, height=320)
            st.markdown('<div style="font-size:0.74rem;color:#94A3B8;margin-top:4px;">Solo se muestran los 30 PDVs con mayor meta entre los que aún tienen brecha. Usa los filtros del sidebar para enfocar por agente, barrio o circuito.</div>', unsafe_allow_html=True)
        else:
            st.success("✅ No hay PDVs con cumplimiento por debajo del 70% en el universo visible.")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # -------------------------------------------------------
    # TAB C4 — CURVA SEMANAL
    # -------------------------------------------------------
    with tc4:
        st.markdown(stage_header(
            "04 · Curva semanal de ejecución",
            "Ritmo de captación por semana · 1–27 Abril 2026",
            "Evolución semanal de altas orgánicas e inducidas (S1–S4) por agente, categoría y zona. Ventana: 1 al 27 de Abril 2026. S4 puede estar incompleta al corte.",
            "trend", "red", show_badges=False
        ), unsafe_allow_html=True)

        semanas = ["S1", "S2", "S3", "S4"]
        s_totals = {s: df[s].sum() if s in df.columns else 0 for s in semanas}

        st.markdown(tab_kpi_context([
            {"icon": "trend", "label": "S1", "value": fmt_int(s_totals["S1"]), "sub": "Altas semana 1"},
            {"icon": "trend", "label": "S2", "value": fmt_int(s_totals["S2"]), "sub": "Altas semana 2"},
            {"icon": "trend", "label": "S3", "value": fmt_int(s_totals["S3"]), "sub": "Altas semana 3"},
            {"icon": "trend", "label": "S4", "value": fmt_int(s_totals["S4"]), "sub": "Altas semana 4"},
        ]), unsafe_allow_html=True)

        # Curva agregada por semana
        df_semana = pd.DataFrame({
            "Semana": semanas,
            "Total": [s_totals[s] for s in semanas],
        })

        c4a, c4b = st.columns(2, gap="large")
        with c4a:
            st.markdown('<div class="section-card"><div class="section-title">Curva de ejecución semanal</div><div class="section-subtitle">¿Cómo fue avanzando la venta semana a semana? S1 = primera semana del periodo, S4 = última. Una curva creciente indica buen ritmo de captación.</div>', unsafe_allow_html=True)
            chart_sem = alt.Chart(df_semana).mark_line(point=True, strokeWidth=3, color="#E10600").encode(
                x=alt.X("Semana:N", title=None, sort=semanas),
                y=alt.Y("Total:Q", title="Altas"),
                tooltip=[alt.Tooltip("Semana:N"), alt.Tooltip("Total:Q", format=",.0f")]
            ).properties(height=280)
            area_sem = alt.Chart(df_semana).mark_area(opacity=0.12, color="#E10600").encode(
                x=alt.X("Semana:N", sort=semanas),
                y=alt.Y("Total:Q")
            )
            st.altair_chart(style_chart(area_sem + chart_sem), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with c4b:
            # Curva por agente
            sem_by_ag = []
            for s in semanas:
                if s in df.columns:
                    grp = df.groupby("AGENTE")[s].sum().reset_index()
                    grp["Semana"] = s
                    grp = grp.rename(columns={s: "Altas"})
                    sem_by_ag.append(grp)
            df_sem_ag = pd.concat(sem_by_ag, ignore_index=True) if sem_by_ag else pd.DataFrame()

            st.markdown('<div class="section-card"><div class="section-title">Ritmo semanal por agente</div><div class="section-subtitle">Cada línea = un agente. Si la línea sube, ese agente aceleró esa semana. Si baja, tuvo menos ventas. Útil para detectar quién sostuvo el ritmo y quién lo perdió.</div>', unsafe_allow_html=True)
            if not df_sem_ag.empty:
                chart_sem_ag = alt.Chart(df_sem_ag).mark_line(point=True, strokeWidth=2).encode(
                    x=alt.X("Semana:N", sort=semanas, title=None),
                    y=alt.Y("Altas:Q", title="Altas orgánicas"),
                    color=alt.Color("AGENTE:N",
                        scale=alt.Scale(domain=list(AGENTE_COLORS.keys()), range=list(AGENTE_COLORS.values())),
                        legend=alt.Legend(title="Agente")),
                    tooltip=[alt.Tooltip("Semana:N"), alt.Tooltip("AGENTE:N"), alt.Tooltip("Altas:Q", format=",.0f")]
                ).properties(height=280)
                st.altair_chart(style_chart(chart_sem_ag), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        # Semanas inducidas
        semanas_indu = ["S1.1", "S2.1", "S3.1", "S4.1"]
        s_indu_totals = {s: df[s].sum() if s in df.columns else 0 for s in semanas_indu}
        df_sem_indu = pd.DataFrame({
            "Semana": ["S1", "S2", "S3", "S4"],
            "Inducidas": [s_indu_totals[s] for s in semanas_indu],
            "Orgánicas": [s_totals[s2] for s2 in semanas],
        })
        df_sem_indu_long = df_sem_indu.melt("Semana", var_name="Tipo", value_name="Altas")

        c4c, c4d = st.columns(2, gap="large")
        with c4c:
            st.markdown('<div class="section-card"><div class="section-title">Altas orgánicas vs inducidas por semana</div><div class="section-subtitle">Orgánicas = planes por encima de $2.000 (mayor valor). Inducidas = planes de hasta $2.000. Cada semana muestra cuántas ventas hubo de cada tipo.</div>', unsafe_allow_html=True)
            chart_comp = alt.Chart(df_sem_indu_long).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X("Semana:N", sort=["S1","S2","S3","S4"], title=None),
                y=alt.Y("Altas:Q", title="Altas"),
                color=alt.Color("Tipo:N",
                    scale=alt.Scale(domain=["Orgánicas","Inducidas"], range=["#E10600","#38BDF8"]),
                    legend=alt.Legend(title="")),
                xOffset="Tipo:N",
                tooltip=[alt.Tooltip("Semana:N"), alt.Tooltip("Tipo:N"), alt.Tooltip("Altas:Q", format=",.0f")]
            ).properties(height=260)
            st.altair_chart(style_chart(chart_comp), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with c4d:
            # Ritmo acumulado
            df_sem_indu["Acum_org"] = df_sem_indu["Orgánicas"].cumsum()
            df_sem_indu["Acum_indu"] = df_sem_indu["Inducidas"].cumsum()
            df_acum = df_sem_indu[["Semana","Acum_org","Acum_indu"]].melt("Semana", var_name="Tipo", value_name="Acumulado")
            df_acum["Tipo"] = df_acum["Tipo"].map({"Acum_org": "Orgánicas", "Acum_indu": "Inducidas"})

            st.markdown('<div class="section-card"><div class="section-title">Avance acumulado de ventas</div><div class="section-subtitle">La línea muestra el total acumulado al cierre de cada semana. Compara las dos líneas: si la roja (orgánicas) crece más rápido, la captación de calidad va bien.</div>', unsafe_allow_html=True)
            chart_acum = alt.Chart(df_acum).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X("Semana:N", sort=["S1","S2","S3","S4"], title=None),
                y=alt.Y("Acumulado:Q", title="Altas acumuladas"),
                color=alt.Color("Tipo:N",
                    scale=alt.Scale(domain=["Orgánicas","Inducidas"], range=["#E10600","#38BDF8"]),
                    legend=alt.Legend(title="")),
                tooltip=[alt.Tooltip("Semana:N"), alt.Tooltip("Tipo:N"), alt.Tooltip("Acumulado:Q", format=",.0f")]
            ).properties(height=260)
            st.altair_chart(style_chart(chart_acum), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        # Nota de contexto temporal — ventana 1–27 de Abril
        st.markdown(f"""
        <div class="executive-note" style="margin-top:10px;">
            <div class="executive-highlight">{icon_svg("trend",12)} Contexto de la curva semanal</div>
            <div class="insight-body">
                La información de esta curva corresponde a la <b>ventana del 1 al 27 de Abril 2026</b>.
                Las semanas S1–S4 reflejan el avance acumulado dentro de ese periodo. S4 puede estar incompleta
                dado que el corte es al 27 de abril. Compara la curva orgánica vs inducida para identificar
                dónde se concentró el esfuerzo de captación.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------
    # TAB C5 — MERCADO Y SEÑAL
    # -------------------------------------------------------
    with tc5:
        st.markdown(stage_header(
            "05 · Mercado y Señal en PDVs",
            "Cuota, presencia de mercado e intensidad de señal",
            "Distribución de cuota de mercado, cuota de altas y calidad de señal RSRP en el portafolio de PDVs visible.",
            "briefcase", "red", show_badges=False
        ), unsafe_allow_html=True)

        st.markdown(tab_kpi_context([
            {"icon": "target", "label": "Cuota de altas media",  "value": fmt_pct_c(cuota_alta_media), "sub": "% de ventas nuevas que son Claro"},
            {"icon": "signal", "label": "Cuota mercado media",   "value": fmt_pct_c(cuota_mkt_media),  "sub": "Promedio de PDVs visibles"},
            {"icon": "trend",  "label": "RSRP promedio",         "value": fmt_dBm(rsrp_media), "sub": "Intensidad señal media"},
            {"icon": "users",  "label": "PDVs cuota alta >50%",  "value": fmt_int((pd.to_numeric(df["CUOTA DE ALTA"],errors="coerce")>50).sum()), "sub": "Claro domina captación"},
        ]), unsafe_allow_html=True)

        c5a, c5b = st.columns(2, gap="large")
        with c5a:
            # Cuota de mercado por agente
            cuota_by_ag = df.groupby("AGENTE").agg(
                cuota_mkt=("CUOTA DE MERCADO", "mean"),
                cuota_alta=("CUOTA DE ALTA", "mean"),
                n=("ID", "count"),
            ).reset_index()

            st.markdown('<div class="section-card"><div class="section-title">Cuota de altas y mercado por agente</div><div class="section-subtitle"><b>Barra azul = cuota de altas</b> (% de ventas nuevas que son Claro — el indicador más relevante). Barra roja = cuota de mercado (base instalada). Si la azul supera la roja, el agente está ganando participación activamente.</div>', unsafe_allow_html=True)
            cuota_melt = cuota_by_ag[["AGENTE","cuota_mkt","cuota_alta"]].melt("AGENTE", var_name="Indicador", value_name="Valor")
            cuota_melt["Indicador"] = cuota_melt["Indicador"].map({"cuota_mkt": "Cuota Mercado (base)", "cuota_alta": "Cuota Altas (captación)"})
            chart_cuota = alt.Chart(cuota_melt).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X("AGENTE:N", title=None, axis=alt.Axis(labelAngle=-20)),
                y=alt.Y("Valor:Q", title="Cuota (%)"),
                color=alt.Color("Indicador:N",
                    scale=alt.Scale(domain=["Cuota Mercado (base)","Cuota Altas (captación)"], range=["#E10600","#38BDF8"]),
                    legend=alt.Legend(title="")),
                xOffset="Indicador:N",
                tooltip=[alt.Tooltip("AGENTE:N"), alt.Tooltip("Indicador:N"), alt.Tooltip("Valor:Q", format=".1f", title="Cuota %")]
            ).properties(height=300)
            st.altair_chart(style_chart(chart_cuota), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with c5b:
            # Distribución de cuota de mercado (histograma)
            cuota_vals = pd.to_numeric(df["CUOTA DE MERCADO"], errors="coerce").dropna()
            df_hist = pd.DataFrame({"Cuota": cuota_vals})

            st.markdown('<div class="section-card"><div class="section-title">Distribución de cuota de mercado Claro</div><div class="section-subtitle">Este histograma muestra <b>cuántos PDVs tienen cada nivel de cuota de mercado</b>. El eje X representa el porcentaje de cuota de Claro (0% a 100%) y el eje Y muestra cuántos puntos de venta caen en ese rango. Una barra alta en valores bajos indica muchos PDVs donde Claro tiene poca participación — oportunidad de mejora. Una barra alta cerca del 100% indica PDVs donde Claro domina. El objetivo es desplazar la distribución hacia la derecha.</div>', unsafe_allow_html=True)
            if not df_hist.empty:
                chart_hist = alt.Chart(df_hist).mark_bar(color="#E10600", opacity=0.82).encode(
                    x=alt.X("Cuota:Q", bin=alt.Bin(maxbins=20), title="Cuota mercado Claro (%)"),
                    y=alt.Y("count():Q", title="PDVs"),
                    tooltip=[alt.Tooltip("Cuota:Q", bin=True), alt.Tooltip("count():Q", title="PDVs")]
                ).properties(height=300)
                st.altair_chart(style_chart(chart_hist), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        c5c, c5d = st.columns(2, gap="large")
        with c5c:
            # Bandas RSRP correctas según el usuario:
            # >= -70 = Excelente | -70 a -90 = Buena | -90 a -100 = Aceptable | < -100 = Crítica
            df_sc = df[["CUOTA DE ALTA","CUOTA DE MERCADO","RSRP","AGENTE","CATEGORIA","ID"]].copy()
            df_sc["RSRP_num"]   = pd.to_numeric(df_sc["RSRP"], errors="coerce")
            df_sc["CUOTA_ALTA"] = pd.to_numeric(df_sc["CUOTA DE ALTA"], errors="coerce")
            df_sc = df_sc.dropna(subset=["RSRP_num","CUOTA_ALTA"]).copy()

            def rsrp_band_v2(v):
                if v >= -70:  return "Excelente (≥ -70 dBm)"
                if v >= -90:  return "Buena (-70 a -90 dBm)"
                if v >= -100: return "Aceptable (-90 a -100 dBm)"
                return "Crítica (< -100 dBm)"

            band_order_v2  = ["Excelente (≥ -70 dBm)", "Buena (-70 a -90 dBm)", "Aceptable (-90 a -100 dBm)", "Crítica (< -100 dBm)"]
            band_colors_v2 = ["#22C55E", "#84CC16", "#F59E0B", "#EF4444"]

            df_sc["Banda RSRP"] = df_sc["RSRP_num"].apply(rsrp_band_v2)
            df_sc["Banda RSRP"] = pd.Categorical(df_sc["Banda RSRP"], categories=band_order_v2, ordered=True)
            by_band_v2 = df_sc.groupby("Banda RSRP", observed=True).agg(
                cuota_alta_media=("CUOTA_ALTA", "mean"),
                pdvs=("CUOTA_ALTA", "count"),
                rsrp_media=("RSRP_num", "mean"),
            ).reset_index()
            by_band_v2["Banda RSRP"] = by_band_v2["Banda RSRP"].astype(str)

            # Detectar si faltan bandas (ej: sin excelente ni buena)
            _bandas_presentes = set(by_band_v2["Banda RSRP"].tolist())
            _bandas_ausentes  = [b for b in band_order_v2 if b not in _bandas_presentes]
            _alerta_señal = len(_bandas_ausentes) > 0

            _subtitle_band = (
                "Cuota de altas Claro promedio por banda de calidad de señal RSRP. "
                "Las bandas se definen así: <b>Excelente</b> ≥ -70 dBm · <b>Buena</b> -70 a -90 · "
                "<b>Aceptable</b> -90 a -100 · <b>Crítica</b> &lt; -100 dBm. "
                + (f"⚠️ <b>En este portafolio no hay PDVs con señal Excelente ni Buena</b> — toda la red opera en zona Aceptable o Crítica." if _alerta_señal else "")
            )

            st.markdown(f'<div class="section-card"><div class="section-title">Calidad de señal vs cuota de altas Claro</div><div class="section-subtitle">{_subtitle_band}</div>', unsafe_allow_html=True)
            if not by_band_v2.empty:
                _y_max = max(by_band_v2["cuota_alta_media"].max() * 1.25, 60)
                chart_band_v2 = alt.Chart(by_band_v2).mark_bar(cornerRadiusTopLeft=7, cornerRadiusTopRight=7).encode(
                    x=alt.X("Banda RSRP:N", sort=band_order_v2, title=None,
                            axis=alt.Axis(labelAngle=-12, labelLimit=220)),
                    y=alt.Y("cuota_alta_media:Q", title="Cuota de altas Claro (%)",
                            scale=alt.Scale(domain=[0, _y_max])),
                    color=alt.Color("Banda RSRP:N",
                        scale=alt.Scale(domain=band_order_v2, range=band_colors_v2),
                        legend=None),
                    tooltip=[
                        alt.Tooltip("Banda RSRP:N",        title="Banda de señal"),
                        alt.Tooltip("pdvs:Q",              title="PDVs en esta banda"),
                        alt.Tooltip("rsrp_media:Q",        title="RSRP medio (dBm)", format=".1f"),
                        alt.Tooltip("cuota_alta_media:Q",  title="Cuota altas media %", format=".1f"),
                    ]
                ).properties(height=290)
                rule50_b = alt.Chart(pd.DataFrame({"y":[50]})).mark_rule(
                    color="#38BDF8", strokeDash=[5,3], strokeWidth=1.5).encode(y="y:Q")
                text_b = alt.Chart(by_band_v2).mark_text(
                    dy=-14, fontSize=12, fontWeight="bold", color="#F8FAFC"
                ).encode(
                    x=alt.X("Banda RSRP:N", sort=band_order_v2),
                    y=alt.Y("cuota_alta_media:Q"),
                    text=alt.Text("cuota_alta_media:Q", format=".1f")
                )
                st.altair_chart(style_chart(chart_band_v2 + rule50_b + text_b), use_container_width=True, theme=None)
                # Mostrar advertencia si hay bandas vacías
                if _alerta_señal:
                    st.markdown(f'<div style="font-size:0.74rem;color:#FCA5A5;margin-top:4px;background:rgba(239,68,68,0.10);border:1px solid rgba(239,68,68,0.22);border-radius:10px;padding:7px 10px;">⚠️ Las bandas <b>{", ".join(_bandas_ausentes)}</b> no tienen PDVs — toda la señal del portafolio está en zona Aceptable o Crítica. Oportunidad de mejora de red.</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:0.74rem;color:#94A3B8;margin-top:6px;">Línea azul = 50% referencia. El número encima de cada barra = cuota de altas media en esa banda.</div>', unsafe_allow_html=True)
            else:
                st.info("No hay datos de señal disponibles.")
            st.markdown('</div>', unsafe_allow_html=True)

        with c5d:
            # Cuota de alta por categoría
            cuota_cat = df.groupby("CATEGORIA").agg(
                cuota_mkt=("CUOTA DE MERCADO", "mean"),
                cuota_alta=("CUOTA DE ALTA", "mean"),
                n=("ID", "count"),
            ).reset_index()
            cuota_cat["CATEGORIA"] = pd.Categorical(cuota_cat["CATEGORIA"], categories=["DIAMANTE","PLATINO","ORO","PLATA","BRONCE"], ordered=True)
            cuota_cat = cuota_cat.sort_values("CATEGORIA")

            st.markdown('<div class="section-card"><div class="section-title">¿En qué categoría de PDV capta más Claro?</div><div class="section-subtitle">Cuota de altas Claro por categoría (Diamante → Bronce). Un valor alto = Claro gana la mayoría de ventas nuevas en esos PDVs. La línea azul marca el 50%.</div>', unsafe_allow_html=True)
            if not cuota_cat.empty:
                chart_calt = alt.Chart(cuota_cat).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                    x=alt.X("CATEGORIA:N", sort=["DIAMANTE","PLATINO","ORO","PLATA","BRONCE"], title=None),
                    y=alt.Y("cuota_alta:Q", title="Cuota alta Claro (%)"),
                    color=alt.Color("CATEGORIA:N",
                        scale=alt.Scale(domain=list(CATEGORIA_COLORS.keys()), range=list(CATEGORIA_COLORS.values())),
                        legend=None),
                    tooltip=[alt.Tooltip("CATEGORIA:N"), alt.Tooltip("cuota_alta:Q", format=".1f", title="Cuota alta %"), alt.Tooltip("cuota_mkt:Q", format=".1f", title="Cuota mkt %"), alt.Tooltip("n:Q", title="PDVs")]
                ).properties(height=280)
                rule50_cat = alt.Chart(pd.DataFrame({"y":[50]})).mark_rule(color="#38BDF8", strokeDash=[5,3], strokeWidth=1.5).encode(y="y:Q")
                st.altair_chart(style_chart(chart_calt + rule50_cat), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── KPI de oportunidades de mejora (siempre visible) ──────────────────
        st.markdown(f'<div style="margin:18px 0 8px 0;font-size:.72rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;">Puntos de mejora identificados</div>', unsafe_allow_html=True)

        _df_opp = df.copy()
        _df_opp["RSRP_n"]      = pd.to_numeric(_df_opp["RSRP"], errors="coerce")
        _df_opp["CUOTA_ALTA_n"]= pd.to_numeric(_df_opp["CUOTA DE ALTA"], errors="coerce")
        _df_opp["CUOTA_MKT_n"] = pd.to_numeric(_df_opp["CUOTA DE MERCADO"], errors="coerce")
        _df_opp["EJEC_n"]      = pd.to_numeric(_df_opp["EJEC ALTA NAT"], errors="coerce")
        _df_opp["META_n"]      = pd.to_numeric(_df_opp["META ALTA NAT (>$2000)"], errors="coerce")
        _df_opp["cumpl_pdv"]   = (_df_opp["EJEC_n"] / _df_opp["META_n"].replace(0, np.nan) * 100).fillna(0)
        _df_opp["banda_rsrp"]  = _df_opp["RSRP_n"].apply(lambda v: rsrp_band_v2(v) if pd.notna(v) else "Sin datos")

        # Cuadrante 1: señal crítica + cuota alta baja → máxima prioridad
        _criticos_baja_cuota = _df_opp[
            (_df_opp["banda_rsrp"] == "Crítica (< -100 dBm)") &
            (_df_opp["CUOTA_ALTA_n"] < _df_opp["CUOTA_ALTA_n"].mean())
        ]
        # Cuadrante 2: señal aceptable + cumplimiento < 70% → oportunidad recuperable
        _acep_bajo_cumpl = _df_opp[
            (_df_opp["banda_rsrp"] == "Aceptable (-90 a -100 dBm)") &
            (_df_opp["META_n"] > 0) & (_df_opp["cumpl_pdv"] < 70)
        ]
        # Cuadrante 3: sin señal crítica pero cuota alta muy baja (< 30%) → potencial sin aprovechar
        _baja_cuota_pura = _df_opp[
            (_df_opp["CUOTA_ALTA_n"] < 30) & (_df_opp["META_n"] > 0)
        ]

        _n_crit_bc   = len(_criticos_baja_cuota)
        _n_acep_bc   = len(_acep_bajo_cumpl)
        _n_baja_c    = len(_baja_cuota_pura)
        _cuota_media = _df_opp["CUOTA_ALTA_n"].mean()
        _pct_criticos= len(_df_opp[_df_opp["banda_rsrp"]=="Crítica (< -100 dBm)"]) / max(len(_df_opp),1) * 100
        _pct_acept   = len(_df_opp[_df_opp["banda_rsrp"]=="Aceptable (-90 a -100 dBm)"]) / max(len(_df_opp),1) * 100

        op1, op2, op3, op4 = st.columns(4, gap="medium")
        with op1:
            _col1 = "#EF4444" if _pct_criticos > 10 else "#F59E0B"
            st.markdown(f"""
            <div class="card">
                <div class="kpi-label">PDVs señal crítica</div>
                <div class="kpi-value" style="color:{_col1};">{_pct_criticos:.1f}%</div>
                <div class="kpi-sub">{"🔴 Más del 10% del portafolio en señal crítica." if _pct_criticos > 10 else "🟡 Señal crítica presente."} {fmt_int(len(_df_opp[_df_opp["banda_rsrp"]=="Crítica (< -100 dBm)"]))} PDVs bajo -100 dBm — ningún PDV tiene señal Excelente o Buena en este portafolio.</div>
            </div>""", unsafe_allow_html=True)
        with op2:
            st.markdown(f"""
            <div class="card">
                <div class="kpi-label">Críticos + cuota baja</div>
                <div class="kpi-value" style="color:#EF4444;">{fmt_int(_n_crit_bc)}</div>
                <div class="kpi-sub">🔴 PDVs con señal crítica <b>y</b> cuota de altas bajo la media ({_cuota_media:.1f}%). Máxima prioridad: doble problema activo.</div>
            </div>""", unsafe_allow_html=True)
        with op3:
            st.markdown(f"""
            <div class="card">
                <div class="kpi-label">Aceptable + bajo 70% cumpl.</div>
                <div class="kpi-value" style="color:#F59E0B;">{fmt_int(_n_acep_bc)}</div>
                <div class="kpi-sub">🟡 PDVs con señal aceptable que además no cumplen la meta. Son recuperables si se interviene el PDV antes de que la señal empeore.</div>
            </div>""", unsafe_allow_html=True)
        with op4:
            st.markdown(f"""
            <div class="card">
                <div class="kpi-label">Cuota altas &lt; 30%</div>
                <div class="kpi-value" style="color:#F59E0B;">{fmt_int(_n_baja_c)}</div>
                <div class="kpi-sub">🟡 PDVs donde Claro tiene menos del 30% de las altas. Son puntos con competencia dominante — potencial de mejora comercial sin necesidad de inversión en red.</div>
            </div>""", unsafe_allow_html=True)

        # Tabla detalle oportunidades por circuito
        if "CIRCUITO" in _df_opp.columns:
            _circ_opp = _df_opp[_df_opp["META_n"] > 0].groupby(["CIRCUITO","AGENTE"]).agg(
                pdvs=("ID","count"),
                rsrp_medio=("RSRP_n","mean"),
                cuota_alta=("CUOTA_ALTA_n","mean"),
                cumpl=("cumpl_pdv","mean"),
                pdvs_criticos=("banda_rsrp", lambda x: (x == "Crítica (< -100 dBm)").sum()),
            ).reset_index()
            _circ_opp["score_opp"] = (
                (_circ_opp["pdvs_criticos"] / _circ_opp["pdvs"].replace(0, np.nan) * 40).fillna(0) +
                ((50 - _circ_opp["cuota_alta"].clip(0,50)) * 0.6) +
                ((70 - _circ_opp["cumpl"].clip(0,70)) * 0.4)
            )
            _circ_opp_show = _circ_opp.sort_values("score_opp", ascending=False).head(15)
            st.markdown(f'<div style="margin:16px 0 6px 0;font-size:.72rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;">Top circuitos con mayor oportunidad de mejora (señal + cuota + cumplimiento)</div>', unsafe_allow_html=True)
            _circ_display = safe_round_columns(
                _circ_opp_show[["CIRCUITO","AGENTE","pdvs","rsrp_medio","cuota_alta","cumpl","pdvs_criticos","score_opp"]].copy(),
                ["rsrp_medio","cuota_alta","cumpl","score_opp"]
            )
            _circ_display.columns = ["Circuito","Agente","PDVs","RSRP medio","Cuota alta %","Cumpl. %","PDVs críticos","Score oportunidad"]
            st.dataframe(_circ_display, use_container_width=True, height=320)
            st.markdown('<div style="font-size:0.74rem;color:#94A3B8;margin-top:4px;">Score oportunidad = combinación de % PDVs con señal crítica + baja cuota de altas + bajo cumplimiento. Mayor score = mayor prioridad de intervención.</div>', unsafe_allow_html=True)

        # Insight estratégico cierre
        cuota_alta_50_pct = (pd.to_numeric(df["CUOTA DE ALTA"], errors="coerce") > 50).mean() * 100
        cuota_50_pct = (pd.to_numeric(df["CUOTA DE MERCADO"], errors="coerce") > 50).mean() * 100
        st.markdown(f"""
        <div class="executive-note" style="margin-top:14px;">
            <div class="executive-highlight">{icon_svg("eye",12)} Conclusión ejecutiva de señal</div>
            <div class="insight-body">
                <b>Ningún PDV del portafolio tiene señal Excelente o Buena</b> — el {_pct_acept:.1f}% opera en zona Aceptable
                y el {_pct_criticos:.1f}% en zona Crítica. Claro supera el 50% de cuota de altas en el <b>{cuota_alta_50_pct:.1f}%</b> de los PDVs.
                Los <b>{fmt_int(_n_crit_bc)}</b> PDVs con señal crítica y cuota bajo la media son la prioridad número uno:
                concentran el peor estado de red <b>y</b> el menor desempeño comercial simultáneamente.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Cierre
    st.markdown("""
    <div class="section-card" style="margin-top:14px;">
        <div class="section-title">Cierre ejecutivo — Vista Claro</div>
        <div class="section-subtitle">Recomendación de uso del panel de agentes.</div>
        <div class="insight-body">
            Usa el sidebar para segmentar por agente, categoría, tipo de negocio o zona.
            Navega por las tabs para leer desde el estado global hasta el detalle de cada PDV,
            la curva semanal de captación y la relación entre señal y cuota de mercado Claro.
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# CARGA
# =========================================================
try:
    df, df_long, operator_cols, territorial_df, territorial_info, business_long, market_info, altas_info, load_info = load_data()
except Exception as e:
    st.error(f"La aplicación no pudo cargarse correctamente: {e}")
    st.stop()

for op in operator_cols:
    if f"op_{op}" not in st.session_state:
        st.session_state[f"op_{op}"] = True
for key in ["localidad_sel", "barrio_sel", "ruta_sel", "circuito_sel"]:
    if key not in st.session_state:
        st.session_state[key] = []
for key, default in {
    "metric_focus": "Comparado",
    "zone_focus": "Todas",
    "search_territory": "",
    "share_range": (0, 100),
    "temporal_mode": "Rango personalizado",
    "window_unit": "Mes",
    "window_value": 12,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## Centro de control")
st.sidebar.markdown(f"""<div class="sidebar-guide-row"><span class="sidebar-guide-pill">{icon_svg("filter",12)} Ajusta universo</span><span class="sidebar-guide-pill">{icon_svg("users",12)} Define operadores</span><span class="sidebar-guide-pill">{icon_svg("target",12)} Enfoca lectura</span></div>""", unsafe_allow_html=True)

# ---- SWITCH DE VISTA ----
st.sidebar.markdown(f'<div class="sidebar-block"><div class="sidebar-kicker">{icon_svg("spark",12)} Modo de visualización</div><div class="sidebar-title">Selecciona la vista</div><div class="sidebar-sub">Alterna entre el panel de red y mercado por operador, y la vista focalizada en el desempeño comercial de agentes Claro.</div>', unsafe_allow_html=True)
vista_activa = st.sidebar.radio(
    "Vista del dashboard",
    options=["Red y Mercado · Operadores", "Agentes Claro · PDVs"],
    key="vista_activa",
    horizontal=False,
)
st.sidebar.markdown('</div>', unsafe_allow_html=True)


_vista_claro_sidebar = st.session_state.get("vista_activa", "Red y Mercado · Operadores") == "Agentes Claro · PDVs"

fecha_min = df["Fecha de inicio"].min()
fecha_max = df["Fecha de inicio"].max()
if pd.isna(fecha_min) or pd.isna(fecha_max):
    if not _vista_claro_sidebar:
        st.error("No se encontraron fechas válidas en el archivo principal.")
        st.stop()

if not _vista_claro_sidebar:
    st.sidebar.markdown(f'<div class="sidebar-block"><div class="sidebar-kicker">{icon_svg("trend",12)} Paso 1 · Define el horizonte</div><div class="sidebar-title">Contexto temporal</div><div class="sidebar-sub">Define una ventana personalizada o una ventana móvil por mes, semana o día, y el nivel al que se calcula la variación.</div><div class="filter-stage"><div class="filter-stage-card"><div class="filter-stage-title">Ventana</div><div class="filter-stage-text">Rango o ventana móvil</div></div><div class="filter-stage-card"><div class="filter-stage-title">Unidad</div><div class="filter-stage-text">Mes, semana o día</div></div><div class="filter-stage-card"><div class="filter-stage-title">Lectura</div><div class="filter-stage-text">Cómo comparar periodos</div></div></div>', unsafe_allow_html=True)
if not _vista_claro_sidebar:
    temporal_mode = st.sidebar.radio(
        "Modo de ventana temporal",
        options=["Rango personalizado", "Ventana por periodo"],
        key="temporal_mode",
        horizontal=False
    )

    if temporal_mode == "Rango personalizado":
        col_f1, col_f2 = st.sidebar.columns(2)
        with col_f1:
            fecha_ini_input = st.date_input(
                "Desde",
                value=fecha_min.date(),
                min_value=fecha_min.date(),
                max_value=fecha_max.date(),
                key="fecha_ini_personalizada",
            )
        with col_f2:
            fecha_fin_input = st.date_input(
                "Hasta",
                value=fecha_max.date(),
                min_value=fecha_min.date(),
                max_value=fecha_max.date(),
                key="fecha_fin_personalizada",
            )
        if fecha_ini_input > fecha_fin_input:
            fecha_ini_input, fecha_fin_input = fecha_fin_input, fecha_ini_input
        fecha_ini = fecha_ini_input
        fecha_fin = fecha_fin_input
        st.sidebar.caption(f"Ventana activa: {fecha_ini.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")
    else:
        col_w1, col_w2 = st.sidebar.columns([1, 1])
        with col_w1:
            window_value = st.number_input(
                "Últimos",
                min_value=1,
                max_value=104,
                value=int(st.session_state.get("window_value", 12)),
                step=1,
                key="window_value"
            )
        with col_w2:
            window_unit = st.selectbox(
                "Periodo",
                options=["Mes", "Semana", "Día"],
                index=["Mes", "Semana", "Día"].index(st.session_state.get("window_unit", "Mes")),
                key="window_unit"
            )

        fecha_fin = fecha_max.date()
        fecha_fin_ts = pd.Timestamp(fecha_fin)
        if window_unit == "Mes":
            fecha_ini = (fecha_fin_ts - pd.DateOffset(months=int(window_value) - 1)).date()
        elif window_unit == "Semana":
            fecha_ini = (fecha_fin_ts - pd.Timedelta(weeks=int(window_value) - 1)).date()
        else:
            fecha_ini = (fecha_fin_ts - pd.Timedelta(days=int(window_value) - 1)).date()

        if fecha_ini < fecha_min.date():
            fecha_ini = fecha_min.date()

        st.sidebar.caption(
            f"Ventana activa: últimos {int(window_value)} {window_unit.lower()}{'' if int(window_value)==1 else 'es' if window_unit=='Mes' else 's'} | {fecha_ini.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
        )

    nivel_temporal_variacion = st.sidebar.selectbox("Nivel temporal de variación", options=["Mes", "Semana", "Día"], index=0)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    territorial_available_cols = territorial_info.get("available_cols", []) if territorial_info else []
    territorial_filters_enabled = territorial_info.get("found", False) and "Codigo_postal" in territorial_df.columns

    localidad_options, barrio_options, ruta_options, circuito_options = get_dynamic_territorial_options(
        territorial_df=territorial_df if territorial_filters_enabled else pd.DataFrame(),
        localidad_sel=st.session_state.get("localidad_sel", []),
        barrio_sel=st.session_state.get("barrio_sel", []),
        ruta_sel=st.session_state.get("ruta_sel", []),
    )

    # Fallback visual para evitar selectores vacíos cuando el Excel territorial no carga,
    # pero las columnas territoriales sí existen en el dataset ya unido.
    if not localidad_options and "LOCALIDAD" in df_long.columns:
        localidad_options = sorted(df_long["LOCALIDAD"].dropna().astype(str).loc[lambda s: s.str.strip() != ""].unique().tolist())
    if not barrio_options and "BARRIO" in df_long.columns:
        barrio_options = sorted(df_long["BARRIO"].dropna().astype(str).loc[lambda s: s.str.strip() != ""].unique().tolist())
    if not ruta_options and "RUTA" in df_long.columns:
        ruta_options = sorted(df_long["RUTA"].dropna().astype(str).loc[lambda s: s.str.strip() != ""].unique().tolist())
    if not circuito_options and "CIRCUITO" in df_long.columns:
        circuito_options = sorted(df_long["CIRCUITO"].dropna().astype(str).loc[lambda s: s.str.strip() != ""].unique().tolist())

    st.sidebar.markdown(f'<div class="sidebar-block"><div class="sidebar-kicker">{icon_svg("map",12)} Paso 2 · Acota el territorio</div><div class="sidebar-title">Segmentación principal</div><div class="sidebar-sub">Usa estos filtros para definir rápidamente el universo principal.</div><div class="filter-stage"><div class="filter-stage-card"><div class="filter-stage-title">Localidad</div><div class="filter-stage-text">Define el bloque geográfico</div></div><div class="filter-stage-card"><div class="filter-stage-title">Barrio</div><div class="filter-stage-text">Aterriza la búsqueda</div></div><div class="filter-stage-card"><div class="filter-stage-title">Avanzados</div><div class="filter-stage-text">Ruta, circuito y CP</div></div></div>', unsafe_allow_html=True)
    localidad_sel = st.sidebar.multiselect("Localidad", options=localidad_options, default=[x for x in st.session_state.get("localidad_sel", []) if x in localidad_options], key="localidad_sel", disabled=(not ("LOCALIDAD" in territorial_available_cols) and not localidad_options))
    _, barrio_options, ruta_options, circuito_options = get_dynamic_territorial_options(territorial_df if territorial_filters_enabled else pd.DataFrame(), localidad_sel, st.session_state.get("barrio_sel", []), st.session_state.get("ruta_sel", []))
    if not barrio_options and "BARRIO" in df_long.columns:
        barrio_scope_fallback = df_long.copy()
        if localidad_sel and "LOCALIDAD" in barrio_scope_fallback.columns:
            barrio_scope_fallback = barrio_scope_fallback[barrio_scope_fallback["LOCALIDAD"].isin(localidad_sel)]
        barrio_options = sorted(barrio_scope_fallback["BARRIO"].dropna().astype(str).loc[lambda s: s.str.strip() != ""].unique().tolist())
    barrio_sel = st.sidebar.multiselect("Barrio", options=barrio_options, default=[x for x in st.session_state.get("barrio_sel", []) if x in barrio_options], key="barrio_sel", disabled=(not ("BARRIO" in territorial_available_cols) and not barrio_options))
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    with st.sidebar.expander("Filtros avanzados", expanded=False):
        _, _, ruta_options, circuito_options = get_dynamic_territorial_options(territorial_df if territorial_filters_enabled else pd.DataFrame(), localidad_sel, barrio_sel, st.session_state.get("ruta_sel", []))
        if not ruta_options and "RUTA" in df_long.columns:
            ruta_scope_fallback = df_long.copy()
            if localidad_sel and "LOCALIDAD" in ruta_scope_fallback.columns:
                ruta_scope_fallback = ruta_scope_fallback[ruta_scope_fallback["LOCALIDAD"].isin(localidad_sel)]
            if barrio_sel and "BARRIO" in ruta_scope_fallback.columns:
                ruta_scope_fallback = ruta_scope_fallback[ruta_scope_fallback["BARRIO"].isin(barrio_sel)]
            ruta_options = sorted(ruta_scope_fallback["RUTA"].dropna().astype(str).loc[lambda s: s.str.strip() != ""].unique().tolist())
        ruta_sel = st.multiselect("Ruta", options=ruta_options, default=[x for x in st.session_state.get("ruta_sel", []) if x in ruta_options], key="ruta_sel", disabled=(not ("RUTA" in territorial_available_cols) and not ruta_options))
        _, _, _, circuito_options = get_dynamic_territorial_options(territorial_df if territorial_filters_enabled else pd.DataFrame(), localidad_sel, barrio_sel, ruta_sel)
        if not circuito_options and "CIRCUITO" in df_long.columns:
            circuito_scope_fallback = df_long.copy()
            if localidad_sel and "LOCALIDAD" in circuito_scope_fallback.columns:
                circuito_scope_fallback = circuito_scope_fallback[circuito_scope_fallback["LOCALIDAD"].isin(localidad_sel)]
            if barrio_sel and "BARRIO" in circuito_scope_fallback.columns:
                circuito_scope_fallback = circuito_scope_fallback[circuito_scope_fallback["BARRIO"].isin(barrio_sel)]
            if ruta_sel and "RUTA" in circuito_scope_fallback.columns:
                circuito_scope_fallback = circuito_scope_fallback[circuito_scope_fallback["RUTA"].isin(ruta_sel)]
            circuito_options = sorted(circuito_scope_fallback["CIRCUITO"].dropna().astype(str).loc[lambda s: s.str.strip() != ""].unique().tolist())
        circuito_sel = st.multiselect("Circuito", options=circuito_options, default=[x for x in st.session_state.get("circuito_sel", []) if x in circuito_options], key="circuito_sel", disabled=(not ("CIRCUITO" in territorial_available_cols) and not circuito_options))
        search_territory = st.text_input("Buscar CP / zona", key="search_territory", placeholder="Ej: 110111 o Suba")

        territorial_scope = filter_territorial_scope(
            territorial_df if territorial_filters_enabled else pd.DataFrame(columns=["Codigo_postal"]),
            localidad_sel=localidad_sel, barrio_sel=barrio_sel, ruta_sel=ruta_sel, circuito_sel=circuito_sel
        )
        codigos_disponibles_por_territorio = sorted(territorial_scope["Codigo_postal"].dropna().astype(str).unique().tolist()) if not territorial_scope.empty else []

        codigos = sorted(df["Codigo_postal"].dropna().astype(str).unique().tolist())
        if territorial_filters_enabled and (localidad_sel or barrio_sel or ruta_sel or circuito_sel):
            codigos_options_sidebar = sorted(set(codigos).intersection(set(codigos_disponibles_por_territorio)))
        else:
            codigos_options_sidebar = codigos
        codigos_sel = st.multiselect("Códigos postales", options=codigos_options_sidebar, default=[])

    st.sidebar.markdown(f'<div class="sidebar-block"><div class="sidebar-kicker">{icon_svg("users",12)} Paso 3 · Define la competencia</div><div class="sidebar-title">Operadores</div><div class="sidebar-sub">Selecciona el universo competitivo a comparar.</div><div class="sidebar-guide-row"><span class="sidebar-guide-pill">{icon_svg("eye",12)} Visible en análisis</span><span class="sidebar-guide-pill">{icon_svg("chart",12)} Impacta todas las tabs</span></div>', unsafe_allow_html=True)
    btn1, btn2 = st.sidebar.columns(2)
    with btn1:
        if st.button("Seleccionar todos", use_container_width=True):
            for op in operator_cols:
                st.session_state[f"op_{op}"] = True
    with btn2:
        if st.button("Limpiar", use_container_width=True):
            for op in operator_cols:
                st.session_state[f"op_{op}"] = False
    st.sidebar.markdown('<div class="sidebar-soft-note">Activa solo los operadores que quieras comparar. Si dejas uno solo, el tablero se comporta como una vista focalizada.</div>', unsafe_allow_html=True)
    cols_ops = st.sidebar.columns(2)
    for i, op in enumerate(operator_cols):
        with cols_ops[i % 2]:
            op_color = OPERATOR_COLORS.get(op, "#64748B")
            st.markdown(
                f'''<div class="sidebar-operator-card">
                    <div class="sidebar-operator-chip" style="background:{op_color};">{icon_svg("users", 11)} Operador</div>
                    <div class="sidebar-operator-label">{op}</div>
                    <div class="sidebar-operator-sub">Inclúyelo o exclúyelo del universo competitivo.</div>
                </div>''',
                unsafe_allow_html=True
            )
            st.checkbox(op, key=f"op_{op}")
    operadores_sel = [op for op in operator_cols if st.session_state.get(f"op_{op}", False)]
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    if not operadores_sel:
        st.warning("Debes seleccionar al menos un operador.")
        st.stop()

    with st.sidebar.expander("Negocio · configuración avanzada", expanded=False):
        st.markdown(f'<div class="sidebar-guide-row"><span class="sidebar-guide-pill">{icon_svg("briefcase",12)} Mercado y captación</span><span class="sidebar-guide-pill">{icon_svg("target",12)} Filtra focos</span></div>', unsafe_allow_html=True)
        metric_focus = st.selectbox("Vista de negocio", ["Comparado", "Mercado", "Altas"], key="metric_focus")
        share_range = st.slider("Rango de cuota / participación (%)", 0, 100, st.session_state.get("share_range", (0, 100)), key="share_range")
        zone_focus = st.selectbox("Tipo de zona", ["Todas", "Alta competencia", "Dominio claro", "Bajo desarrollo"], key="zone_focus")
        solo_validos = st.checkbox("Excluir registros sin medición válida", value=True)
        if st.button("Reset filtros", use_container_width=True):
            keep_ops = {k: v for k, v in st.session_state.items() if k.startswith("op_")}
            st.session_state.clear()
            for k, v in keep_ops.items():
                st.session_state[k] = v
            st.rerun()

    territorial_scope = filter_territorial_scope(
        territorial_df if territorial_filters_enabled else pd.DataFrame(columns=["Codigo_postal"]),
        localidad_sel=localidad_sel, barrio_sel=barrio_sel, ruta_sel=ruta_sel, circuito_sel=circuito_sel
    )
    codigos_disponibles_por_territorio = sorted(territorial_scope["Codigo_postal"].dropna().astype(str).unique().tolist()) if not territorial_scope.empty else []
    if territorial_filters_enabled:
        st.sidebar.markdown(
            f"""
            <div class="executive-ribbon">
                <span class="pill">{len(codigos_disponibles_por_territorio):,} CP territoriales</span>
                <span class="pill">{len(operadores_sel)} operadores activos</span>
                <span class="pill">Variación: {nivel_temporal_variacion}</span>
            </div>
            """.replace(",", "."),
            unsafe_allow_html=True,
        )
    if not territorial_filters_enabled and territorial_info.get("message"):
        st.sidebar.info(territorial_info["message"])
    if market_info.get("message"):
        st.sidebar.caption(f"Mercado: {market_info.get('message')}")
    if altas_info.get("message"):
        st.sidebar.caption(f"Altas: {altas_info.get('message')}")

    st.sidebar.markdown("### Referencia visual")
    st.sidebar.markdown('<div class="sidebar-soft-note">Esta leyenda te ayuda a reconocer rápidamente el color asociado a cada operador en tarjetas y gráficos.</div>', unsafe_allow_html=True)
    chips = []
    for op in operadores_sel:
        color = OPERATOR_COLORS.get(op, "#64748B")
        chips.append(f'<span class="operator-chip" style="background:{color};">{op}</span>')
    st.sidebar.markdown("".join(chips), unsafe_allow_html=True)
else:
    # Vista Claro: set defaults so downstream code that references these variables does not crash
    fecha_ini = fecha_min.date() if not pd.isna(fecha_min) else None
    fecha_fin = fecha_max.date() if not pd.isna(fecha_max) else None
    nivel_temporal_variacion = "Mes"
    operadores_sel = list(operator_cols) if operator_cols else []
    localidad_sel = []
    barrio_sel = []
    ruta_sel = []
    circuito_sel = []
    codigos_sel = []
    metric_focus = "Comparado"
    share_range = (0, 100)
    zone_focus = "Todas"
    solo_validos = True
    territorial_filters_enabled = False
    territorial_available_cols = []
    codigos_disponibles_por_territorio = []
    search_territory = ""
    territorial_scope = pd.DataFrame(columns=["Codigo_postal"])


# =========================================================
# FILTROS
# =========================================================
# fecha_ini y fecha_fin se definen desde el centro de control temporal
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

network_records_visible = int(df_f["RSRP_valido"].count()) if "RSRP_valido" in df_f.columns else int(len(df_f))

filtros_activos = []
if localidad_sel: filtros_activos.append(f"{len(localidad_sel)} localidades")
if barrio_sel: filtros_activos.append(f"{len(barrio_sel)} barrios")
if ruta_sel: filtros_activos.append(f"{len(ruta_sel)} rutas")
if circuito_sel: filtros_activos.append(f"{len(circuito_sel)} circuitos")
if codigos_sel: filtros_activos.append(f"{len(codigos_sel)} CP manuales")
if search_territory: filtros_activos.append(f'Búsqueda: "{search_territory}"')
if zone_focus != "Todas": filtros_activos.append(zone_focus)

business_all_f = business_long.copy() if business_long is not None else pd.DataFrame()
if not business_all_f.empty:
    business_all_f = business_all_f[
        (business_all_f["Fecha de inicio"].dt.date >= fecha_ini) &
        (business_all_f["Fecha de inicio"].dt.date <= fecha_fin)
    ].copy()
    if codigos_filtrados_finales is not None:
        business_all_f = business_all_f[business_all_f["Codigo_postal"].astype(str).isin(codigos_filtrados_finales)].copy()
    business_all_f = business_all_f[~business_all_f["Codigo_postal"].astype(str).isin(BUSINESS_EXCLUDED_CP)].copy()

business_f = business_all_f.copy()

if search_territory:
    search_norm = normalize_text(search_territory)
    rsrp_cols = [c for c in ["Codigo_postal", "LOCALIDAD", "BARRIO", "RUTA", "CIRCUITO"] if c in df_f.columns]
    if rsrp_cols:
        mask_search = pd.Series(False, index=df_f.index)
        for col in rsrp_cols:
            mask_search = mask_search | df_f[col].fillna("").astype(str).map(normalize_text).str.contains(search_norm, na=False)
        df_f = df_f[mask_search].copy()
    if not business_f.empty:
        biz_cols = [c for c in ["Codigo_postal", "LOCALIDAD", "BARRIO", "RUTA", "CIRCUITO"] if c in business_f.columns]
        if biz_cols:
            mask_biz = pd.Series(False, index=business_f.index)
            for col in biz_cols:
                mask_biz = mask_biz | business_f[col].fillna("").astype(str).map(normalize_text).str.contains(search_norm, na=False)
            business_f = business_f[mask_biz].copy()

if not business_f.empty:
    low, high = share_range
    mask_share = pd.Series(False, index=business_f.index)
    if "Cuota_mercado" in business_f.columns:
        mask_share = mask_share | business_f["Cuota_mercado"].between(low, high, inclusive="both")
    if "Participacion_altas" in business_f.columns:
        mask_share = mask_share | business_f["Participacion_altas"].between(low, high, inclusive="both")
    if mask_share.any():
        business_f = business_f[mask_share].copy()

    if zone_focus != "Todas":
        zone_base = business_f.groupby("Codigo_postal", as_index=False).agg(share_max=("Cuota_mercado", "max"), mercado_total=("Mercado", "sum"))
        if zone_focus == "Alta competencia":
            valid_cp = zone_base[zone_base["share_max"] < 40]["Codigo_postal"].astype(str).tolist()
        elif zone_focus == "Dominio claro":
            valid_cp = zone_base[zone_base["share_max"] >= 60]["Codigo_postal"].astype(str).tolist()
        else:
            cut = zone_base["mercado_total"].quantile(0.35) if zone_base["mercado_total"].notna().any() else 0
            valid_cp = zone_base[zone_base["mercado_total"] <= cut]["Codigo_postal"].astype(str).tolist()
        business_f = business_f[business_f["Codigo_postal"].astype(str).isin(valid_cp)].copy()

if not business_f.empty:
    business_f = business_f[business_f["Operador"].isin(operadores_sel)].copy()

business_records_visible = int(len(business_f)) if business_f is not None and not business_f.empty else 0

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
pct_critical = (df_f["Categoria_RSRP"] == "Crítica").mean() * 100
cp_critical_mask = df_f.groupby("Codigo_postal")["Categoria_RSRP"].apply(lambda s: (s == "Crítica").mean() >= 0.5)
cp_critical_count = int(cp_critical_mask.sum()) if not cp_critical_mask.empty else 0
cp_total_count = int(df_f["Codigo_postal"].nunique())
cp_critical_share = (cp_critical_count / cp_total_count * 100) if cp_total_count > 0 else np.nan
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

matrix_source = (
    df_f[df_f["Codigo_postal"].isin(top_zones["Codigo_postal"])] if not top_zones.empty else df_f.iloc[0:0]
).groupby(["Codigo_postal", "Operador"], as_index=False).agg(RSRP_mediana=("RSRP_valido", "median"))

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

business_metrics = compute_business_metrics(business_all_f, df_f)
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
market_month_initial_label = business_metrics.get("market_month_initial_label")
market_month_final_label = business_metrics.get("market_month_final_label")
altas_month_initial_label = business_metrics.get("altas_month_initial_label")
altas_month_final_label = business_metrics.get("altas_month_final_label")
market_month_initial_value = business_metrics.get("market_month_initial_value")
market_month_final_value = business_metrics.get("market_month_final_value")
altas_month_initial_value = business_metrics.get("altas_month_initial_value")
altas_month_final_value = business_metrics.get("altas_month_final_value")
market_month_initial_operator = business_metrics.get("market_month_initial_operator")
market_month_final_operator = business_metrics.get("market_month_final_operator")
altas_month_initial_operator = business_metrics.get("altas_month_initial_operator")
altas_month_final_operator = business_metrics.get("altas_month_final_operator")

market_total_visible = market_operator["Mercado_total"].sum() if not market_operator.empty and "Mercado_total" in market_operator.columns else np.nan
altas_total_visible = altas_operator["Altas_total"].sum() if not altas_operator.empty and "Altas_total" in altas_operator.columns else np.nan
market_follow_share = market_operator.iloc[1]["Cuota_mercado_global"] if len(market_operator) > 1 else np.nan
market_lead_gap = (leader_market["Cuota_mercado_global"] - market_follow_share) if leader_market is not None and pd.notna(market_follow_share) else np.nan
altas_follow_share = altas_operator.iloc[1]["Participacion_altas_global"] if len(altas_operator) > 1 else np.nan
altas_lead_gap = (leader_altas["Participacion_altas_global"] - altas_follow_share) if leader_altas is not None and pd.notna(altas_follow_share) else np.nan
risk_count = len(risk_table) if risk_table is not None else 0
opportunity_count = len(opportunity_table) if opportunity_table is not None else 0

market_top2_share = market_operator["Cuota_mercado_global"].head(2).sum() if not market_operator.empty and "Cuota_mercado_global" in market_operator.columns else np.nan
altas_top2_share = altas_operator["Participacion_altas_global"].head(2).sum() if not altas_operator.empty and "Participacion_altas_global" in altas_operator.columns else np.nan

def compute_period_operator_delta(df_in, period_col, value_col):
    if df_in is None or df_in.empty or period_col not in df_in.columns or value_col not in df_in.columns:
        return pd.DataFrame()
    base = df_in[[period_col, "Operador", value_col]].dropna().copy()
    if base.empty:
        return pd.DataFrame()
    base = base.sort_values([period_col, "Operador"])
    first_df = base.groupby("Operador", as_index=False).first().rename(columns={value_col: "Valor_inicial", period_col: "Periodo_inicial"})
    last_df = base.groupby("Operador", as_index=False).last().rename(columns={value_col: "Valor_final", period_col: "Periodo_final"})
    delta = first_df.merge(last_df, on="Operador", how="outer")
    delta["Variacion"] = delta["Valor_final"] - delta["Valor_inicial"]
    return delta.sort_values("Variacion", ascending=False).reset_index(drop=True)


def compute_total_growth(df_in, period_col, value_col):
    if df_in is None or df_in.empty or period_col not in df_in.columns or value_col not in df_in.columns:
        return np.nan, np.nan, np.nan, None, None
    base = df_in[[period_col, value_col]].dropna().copy()
    if base.empty:
        return np.nan, np.nan, np.nan, None, None
    total_by_period = base.groupby(period_col, as_index=False)[value_col].sum().sort_values(period_col)
    if total_by_period.shape[0] < 2:
        val = total_by_period.iloc[-1][value_col]
        per = total_by_period.iloc[-1][period_col]
        return np.nan, val, val, per, per
    initial_val = total_by_period.iloc[0][value_col]
    final_val = total_by_period.iloc[-1][value_col]
    if pd.notna(initial_val) and initial_val != 0:
        growth = ((final_val - initial_val) / initial_val) * 100
    else:
        growth = np.nan
    return growth, initial_val, final_val, total_by_period.iloc[0][period_col], total_by_period.iloc[-1][period_col]

def build_business_executive_summary(leader_market, leader_altas, market_best_gain, altas_best_gain, market_growth, altas_growth):
    fragments = []
    if leader_market is not None:
        fragments.append(f"El liderazgo de mercado lo conserva <b>{leader_market['Operador']}</b> con <b>{leader_market['Cuota_mercado_global']:.1f}%</b> de cuota visible.")
    if leader_altas is not None:
        fragments.append(f"En captación, el liderazgo corresponde a <b>{leader_altas['Operador']}</b> con <b>{leader_altas['Participacion_altas_global']:.1f}%</b> de participación en altas.")
    if market_best_gain is not None and pd.notna(market_best_gain.get('Variacion')):
        direction = "gana" if market_best_gain["Variacion"] >= 0 else "cede"
        fragments.append(f"<b>{market_best_gain['Operador']}</b> {direction} mayor participación de mercado en el periodo con una variación de <b>{market_best_gain['Variacion']:+.1f} pp</b>.")
    if altas_best_gain is not None and pd.notna(altas_best_gain.get('Variacion')):
        direction = "gana" if altas_best_gain["Variacion"] >= 0 else "cede"
        fragments.append(f"En altas, <b>{altas_best_gain['Operador']}</b> {direction} mayor participación con <b>{altas_best_gain['Variacion']:+.1f} pp</b>.")
    if pd.notna(market_growth):
        trend = "crece" if market_growth > 0 else "cae" if market_growth < 0 else "se mantiene"
        fragments.append(f"El volumen total de mercado visible <b>{trend}</b> <b>{market_growth:+.1f}%</b> entre el primer y el último mes disponible.")
    if pd.notna(altas_growth):
        trend = "crecen" if altas_growth > 0 else "caen" if altas_growth < 0 else "se mantienen"
        fragments.append(f"Las altas visibles <b>{trend}</b> <b>{altas_growth:+.1f}%</b> en ese mismo intervalo.")
    return " ".join(fragments)

market_operator_delta = compute_period_operator_delta(market_time, "Periodo_Mes", "Cuota_mercado")
altas_operator_delta = compute_period_operator_delta(altas_time, "Periodo_Mes", "Participacion_altas")

market_best_gain = market_operator_delta.iloc[0] if not market_operator_delta.empty else None
altas_best_gain = altas_operator_delta.iloc[0] if not altas_operator_delta.empty else None

cp_highest_market = None
cp_highest_altas = None
if business_f is not None and not business_f.empty:
    cp_market_df = business_f.groupby("Codigo_postal", as_index=False).agg(Mercado_total=("Mercado", "sum"))
    cp_altas_df = business_f.groupby("Codigo_postal", as_index=False).agg(Altas_total=("Altas", "sum"))
    if not cp_market_df.empty:
        cp_highest_market = cp_market_df.sort_values("Mercado_total", ascending=False).iloc[0]
    if not cp_altas_df.empty:
        cp_highest_altas = cp_altas_df.sort_values("Altas_total", ascending=False).iloc[0]

market_growth_pct, market_total_initial, market_total_final, market_period_initial, market_period_final = compute_total_growth(market_time, "Periodo_Mes", "Mercado_total")
altas_growth_pct, altas_total_initial, altas_total_final, altas_period_initial, altas_period_final = compute_total_growth(altas_time, "Periodo_Mes", "Altas_total")
business_executive_summary = build_business_executive_summary(
    leader_market=leader_market,
    leader_altas=leader_altas,
    market_best_gain=market_best_gain,
    altas_best_gain=altas_best_gain,
    market_growth=market_growth_pct,
    altas_growth=altas_growth_pct,
)

try:
    score_gap = (
        best_operator["Score_operador"] - worst_operator["Score_operador"]
        if best_operator is not None and worst_operator is not None
        and pd.notna(best_operator.get("Score_operador", np.nan))
        and pd.notna(worst_operator.get("Score_operador", np.nan))
        else np.nan
    )
except Exception:
    score_gap = np.nan

# Insights blindados: no dependen de que variables visuales previas existan en un orden específico.
try:
    _insight_title = locals().get("insight_title", None)
    _insight_action = locals().get("insight_action", None)
    if _insight_title and _insight_action:
        tab1_insight_body = f"{_insight_title}. {_insight_action}"
    elif pd.notna(global_median):
        tab1_insight_body = f"El periodo seleccionado presenta una mediana de intensidad de señal de {fmt_dBm(global_median)} y {fmt_int(cp_critical_count)} CP críticos visibles."
    else:
        tab1_insight_body = "No hay información suficiente para generar un insight del resumen."
except Exception:
    tab1_insight_body = "No hay información suficiente para generar un insight del resumen."

try:
    _best_op_name = best_operator["Operador"] if best_operator is not None and "Operador" in best_operator.index else "N/D"
    _gap_text = fmt_num(score_gap, 1) if pd.notna(score_gap) else "N/D"
    tab2_insight_body = f"{_best_op_name} lidera el score; la brecha frente al operador con menor score es de {_gap_text} puntos."
except Exception:
    tab2_insight_body = "No hay información suficiente para generar la lectura competitiva."

try:
    if worst_zone is not None:
        tab3_insight_body = (
            f"El foco territorial principal es el CP {worst_zone['Codigo_postal']}, "
            f"con {fmt_pct(worst_zone['Pct_critica'])} en condición crítica."
        )
    else:
        tab3_insight_body = "No se identifica un CP prioritario con los filtros seleccionados."
except Exception:
    tab3_insight_body = "No hay información suficiente para generar la lectura territorial."

try:
    _var_global = variation_result.get("variacion_global", np.nan) if isinstance(variation_result, dict) else np.nan
    tab4_insight_body = (
        f"La variación global de intensidad de señal es {fmt_var_dBm(_var_global)}; "
        f"revisa los extremos para separar mejora real de puntos aislados."
    )
except Exception:
    tab4_insight_body = "No hay información suficiente para generar la lectura de variación."

try:
    if business_executive_summary:
        tab5_insight_body = business_executive_summary
    elif leader_market is not None or leader_altas is not None:
        _lm = leader_market["Operador"] if leader_market is not None and "Operador" in leader_market.index else "N/D"
        _la = leader_altas["Operador"] if leader_altas is not None and "Operador" in leader_altas.index else "N/D"
        tab5_insight_body = f"Mercado liderado por {_lm}; captación liderada por {_la} en el universo visible."
    else:
        tab5_insight_body = "No hay suficientes datos de mercado o altas para generar una lectura comercial completa."
except Exception:
    tab5_insight_body = "No hay suficientes datos de mercado o altas para generar una lectura comercial completa."


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

if pct_critical >= 30:
    insight_title = "Riesgo alto de intensidad de señal"
    insight_body = f"La red muestra una presión crítica relevante: {fmt_pct(pct_critical)} de las mediciones y {cp_critical_count} códigos postales concentran condición crítica."
    insight_action = "Priorizar intervención en los CP con deterioro reciente y mayor exposición crítica."
elif pct_critical >= 15:
    insight_title = "Red bajo vigilancia"
    insight_body = f"El comportamiento agregado es mixto: {fmt_pct(pct_critical)} de criticidad y {cp_critical_count} códigos postales en condición crítica requieren monitoreo cercano."
    insight_action = "Enfocar optimización en zonas con deterioro y proteger las áreas que hoy se mantienen estables."
else:
    insight_title = "Desempeño estable de intensidad de señal"
    insight_body = f"La red mantiene baja criticidad visible: {fmt_pct(pct_critical)} de las mediciones y {cp_critical_count} códigos postales en condición crítica."
    insight_action = "Sostener la estabilidad y concentrar mejoras finas en territorios puntuales de menor señal."

# =========================================================
# SWITCH PRINCIPAL
# =========================================================
_vista_claro = st.session_state.get("vista_activa", "Red y Mercado · Operadores") == "Agentes Claro · PDVs"

if _vista_claro:
    render_claro_view()
    st.stop()

# =========================================================
# HEADER (VISTA RED/MERCADO)
# =========================================================
periodo_txt = f"{pd.to_datetime(fecha_ini).strftime('%d/%m/%Y')} a {pd.to_datetime(fecha_fin).strftime('%d/%m/%Y')}"
periodo_txt_corto = f"{pd.to_datetime(fecha_ini).strftime('%d/%m/%Y')} - {pd.to_datetime(fecha_fin).strftime('%d/%m/%Y')}"
obs_validas = int(df_f["RSRP_valido"].count())

if network_records_visible < 100:
    st.markdown(
        f'''
        <div class="sync-warning">
            <div>{icon_svg("target", 16) if "icon_svg" in globals() else ""}</div>
            <div>
                <div class="sync-warning-title">Muestra reducida de red</div>
                <div class="sync-warning-body">El rango seleccionado contiene <b>{fmt_int(network_records_visible)}</b> mediciones válidas. La lectura puede ser menos representativa.</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

if business_records_visible == 0:
    st.markdown(
        f'''
        <div class="sync-warning">
            <div>{icon_svg("briefcase", 16) if "icon_svg" in globals() else ""}</div>
            <div>
                <div class="sync-warning-title">Sin datos de negocio en el rango</div>
                <div class="sync-warning-body">Mercado y altas no tienen registros visibles para <b>{periodo_txt_corto}</b>. Revisa rango temporal, CP o filtros de negocio.</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )
elif business_records_visible < 20:
    st.markdown(
        f'''
        <div class="sync-warning">
            <div>{icon_svg("briefcase", 16) if "icon_svg" in globals() else ""}</div>
            <div>
                <div class="sync-warning-title">Muestra reducida de negocio</div>
                <div class="sync-warning-body">Mercado y altas tienen <b>{fmt_int(business_records_visible)}</b> registros visibles para <b>{periodo_txt_corto}</b>. La lectura puede ser parcial.</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

st.markdown(f"""
<div class="header-shell">
    <div style="position:relative;z-index:2;">
        <div class="hero-badge">Panel ejecutivo corporativo</div>
        <div style="font-size:0.84rem;color:#94A3B8;font-weight:800;letter-spacing:0.55px;">{AREA_NAME}</div>
        <div class="hero-title">{DASHBOARD_TITLE}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.download_button(
    label="⬇ Exportar Excel",
    data=excel_bytes,
    file_name="dashboard_rsrp_mercado_export.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=False,
)

order_quality = ["Excelente", "Buena", "Aceptable", "Crítica", "Sin medición"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(["01  Resumen ejecutivo", "02  Operadores", "03  Territorio", "04  Variación", "05  Mercado y Captación"])

# TAB 1
with tab1:
    st.markdown(stage_header("01 · Resumen ejecutivo", "Qué está pasando en la red", "Vista de entrada para entender el estado agregado, el insight principal y la distribución de señal antes de ir al detalle.", "eye", "red"), unsafe_allow_html=True)
    st.markdown(lane_label("Primero lee el diagnóstico y la señal principal", "spark"), unsafe_allow_html=True)
    st.markdown(risk_badges(), unsafe_allow_html=True)
    st.markdown(tab_kpi_context([
        {"icon": "signal", "label": "Estado de señal", "value": fmt_dBm(global_median), "sub": f"Mediana del periodo {periodo_txt_corto}"},
        {"icon": "target", "label": "CP críticos", "value": fmt_int(cp_critical_count), "sub": f"{fmt_pct(cp_critical_share)} del territorio visible"},
        {"icon": "users", "label": "Operador líder", "value": best_operator["Operador"], "sub": f"Score {best_operator['Score_operador']:.1f}"}
    ]), unsafe_allow_html=True)
    st.markdown(tab_insight("Insight del resumen", tab1_insight_body, "eye"), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="user-guide-band"><span class="guide-pill">{icon_svg("eye", 13)} Estado</span><span class="guide-pill">{icon_svg("users", 13)} Líder</span><span class="guide-pill">{icon_svg("target", 13)} Prioridad</span></div><div class="decision-strip"><div class="decision-card"><div class="decision-label">Qué decide esta pestaña</div><div class="decision-text">Si el periodo está sano, en vigilancia o requiere intervención.</div></div><div class="decision-card"><div class="decision-label">Dónde enfocar</div><div class="decision-text">En el CP prioritario y en la categoría crítica de señal.</div></div><div class="decision-card"><div class="decision-label">Qué validar</div><div class="decision-text">Que el insight coincida con la distribución de señal.</div></div></div>
        <div class="visual-note">
            <div class="visual-note-title">Cómo leer este resumen</div>
            <div class="visual-note-body">
                Esta pestaña concentra la <b>señal principal del periodo</b>: qué tan fuerte es la red, quién lidera y cuál es el código postal
                que debe entrar primero a intervención.
            </div>
        </div>
        <div class="story-grid">
            <div class="story-mini">
                <div class="story-label">Estado agregado</div>
                <div class="story-value">{status_text}</div>
                <div class="story-sub">Mediana global {fmt_dBm(global_median)}</div>
            </div>
            <div class="story-mini">
                <div class="story-label">Liderazgo actual</div>
                <div class="story-value">{best_operator["Operador"]}</div>
                <div class="story-sub">Score {best_operator["Score_operador"]:.1f} | Intensidad {fmt_dBm(best_operator["RSRP_mediana"])}</div>
            </div>
            <div class="story-mini">
                <div class="story-label">Prioridad territorial</div>
                <div class="story-value">{enrich_cp_label(worst_zone["Codigo_postal"], worst_zone) if worst_zone is not None else "N/D"}</div>
                <div class="story-sub">{fmt_pct(worst_zone["Pct_critica"]) if worst_zone is not None else "N/D"} crítica en la zona principal</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    distribucion = (
        df_f.groupby("Categoria_RSRP", as_index=False)
        .size()
        .rename(columns={"size": "Cantidad", "Categoria_RSRP": "Categoria"})
    )
    orden_categoria = ["Excelente", "Buena", "Aceptable", "Crítica", "Sin medición"]
    distribucion["Categoria"] = pd.Categorical(distribucion["Categoria"], categories=orden_categoria, ordered=True)
    distribucion = distribucion.sort_values("Categoria")

    st.markdown(
        f"""
        <div class="executive-ribbon">
            <span class="pill">Operador líder: {best_operator["Operador"]}</span>
            <span class="pill">RSRP mediano: {fmt_dBm(global_median)}</span>
            <span class="pill">CP críticos: {fmt_int(cp_critical_count)}</span>
            <span class="pill">CP prioritario: {enrich_cp_label(worst_zone["Codigo_postal"], worst_zone) if worst_zone is not None else "N/D"}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(tab_section("Señales principales", "KPIs solo dentro del resumen, no estorban la navegación global", "signal"), unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4, gap="medium")

    # Compute conclusions for each KPI
    if pd.notna(global_median):
        if global_median >= -70:
            _rsrp_conclusion = "✅ Señal excelente. La red está en condición óptima para este periodo."
        elif global_median >= -90:
            _rsrp_conclusion = "🟡 Señal buena. Desempeño estable, vigilar zonas en límite."
        elif global_median >= -100:
            _rsrp_conclusion = "🟠 Señal aceptable. Hay territorios que requieren atención prioritaria."
        else:
            _rsrp_conclusion = "🔴 Señal crítica. Se requiere intervención urgente en la red."
    else:
        _rsrp_conclusion = "Sin datos suficientes para emitir conclusión."

    if pd.notna(cp_critical_share):
        if cp_critical_share < 0.10:
            _cp_conclusion = "✅ Baja exposición crítica. Menos del 10% del territorio en riesgo."
        elif cp_critical_share < 0.25:
            _cp_conclusion = "🟡 Exposición moderada. Entre 10% y 25% del territorio con señal crítica."
        else:
            _cp_conclusion = "🔴 Alta concentración crítica. Más del 25% del territorio necesita intervención."
    else:
        _cp_conclusion = "Sin datos para evaluar criticidad territorial."

    _best_op_conclusion = f"Lidera con score {best_operator['Score_operador']:.1f} y mediana {fmt_dBm(best_operator['RSRP_mediana'])}. Es el referente de calidad en el periodo."

    if worst_zone is not None:
        _wz_pct = worst_zone['Pct_critica']
        if _wz_pct >= 50:
            _zone_conclusion = f"🔴 Zona de máxima urgencia: más del 50% de señal crítica. Intervención inmediata recomendada."
        elif _wz_pct >= 30:
            _zone_conclusion = f"🟠 Zona de alta prioridad con {fmt_pct(_wz_pct)} crítica. Debe entrar al próximo plan de mejora."
        else:
            _zone_conclusion = f"🟡 Zona prioritaria con {fmt_pct(_wz_pct)} crítica. Monitoreo cercano recomendado."
    else:
        _zone_conclusion = "No se identifica zona crítica principal con los filtros activos."

    with k1:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-label">RSRP mediano</div>
            <div class="kpi-value">{fmt_dBm(global_median)}</div>
            <div class="kpi-sub">{_rsrp_conclusion}</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-label">CP críticos</div>
            <div class="kpi-value">{fmt_int(cp_critical_count)}</div>
            <div class="kpi-sub">{_cp_conclusion}</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-label">Operador líder</div>
            <div class="metric-operator" style="color:{OPERATOR_COLORS.get(best_operator["Operador"], "#FFFFFF")};">
                {best_operator["Operador"]}
            </div>
            <div class="kpi-sub">{_best_op_conclusion}</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="card">
            <div class="kpi-label">Zona crítica</div>
            <div class="kpi-value" style="font-size:1.38rem;">{enrich_cp_label(worst_zone["Codigo_postal"], worst_zone) if worst_zone is not None else "N/D"}</div>
            <div class="kpi-sub">{_zone_conclusion}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(tab_section("Diagnóstico y evidencia", "Insight accionable a la izquierda; distribución visual a la derecha", "eye"), unsafe_allow_html=True)
    r1, r2 = st.columns((1.05, 0.95), gap="large")
    with r1:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Insight ejecutivo</div>
            <div class="section-subtitle">Lectura breve del estado actual de la red.</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">{insight_title}</div>
            <div class="insight-body"><b>{insight_title}</b> · {insight_action}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with r2:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">Distribución de señal</div>
            <div class="section-subtitle">Composición general por categoría RSRP dentro del periodo seleccionado.</div>
            <div class="mini-legend-grid"><div class="mini-legend-card"><div class="mini-legend-title">Excelente</div><div class="mini-legend-text">Señal muy sólida</div></div><div class="mini-legend-card"><div class="mini-legend-title">Buena</div><div class="mini-legend-text">Desempeño estable</div></div><div class="mini-legend-card"><div class="mini-legend-title">Aceptable</div><div class="mini-legend-text">Zona vigilable</div></div><div class="mini-legend-card"><div class="mini-legend-title">Crítica</div><div class="mini-legend-text">Requiere intervención</div></div></div>
        """, unsafe_allow_html=True)

        if not distribucion.empty:
            chart = alt.Chart(distribucion).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Categoria:N", title=None, sort=orden_categoria),
                y=alt.Y("Cantidad:Q", title="Cantidad"),
                color=alt.Color(
                    "Categoria:N",
                    scale=alt.Scale(
                        domain=["Excelente", "Buena", "Aceptable", "Crítica", "Sin medición"],
                        range=["#22C55E", "#84CC16", "#F59E0B", "#EF4444", "#64748B"]
                    ),
                    legend=None
                ),
                tooltip=[
                    alt.Tooltip("Categoria:N", title="Categoría"),
                    alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f")
                ]
            ).properties(height=320)
            st.altair_chart(style_chart(chart), use_container_width=True, theme=None)
        else:
            st.info("No hay datos suficientes para mostrar la distribución general.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# TAB 2
with tab2:
    st.markdown(stage_header("02 · Comparativo", "Cómo se comportan los operadores", "Ordena la lectura competitiva: liderazgo, composición de calidad, ranking y tabla de validación.", "users", "red"), unsafe_allow_html=True)
    st.markdown(lane_label("Primero compara liderazgo, luego valida el detalle", "chart"), unsafe_allow_html=True)
    st.markdown(tab_kpi_context([
        {"icon": "users", "label": "Líder por score", "value": best_operator["Operador"], "sub": f"Score {best_operator['Score_operador']:.1f}"},
        {"icon": "target", "label": "Mayor criticidad", "value": worst_operator_crit["Operador"], "sub": f"{fmt_pct(worst_operator_crit['Critica'])} crítica"},
        {"icon": "chart", "label": "Brecha competitiva", "value": fmt_num(score_gap, 1), "sub": "Puntos entre líder y rezago"}
    ]), unsafe_allow_html=True)
    st.markdown(tab_insight("Lectura competitiva", tab2_insight_body, "users"), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="user-guide-band"><span class="guide-pill">{icon_svg("users", 13)} Liderazgo</span><span class="guide-pill">{icon_svg("shield", 13)} Composición</span><span class="guide-pill">{icon_svg("table", 13)} Validación</span></div><div class="decision-strip"><div class="decision-card"><div class="decision-label">Qué decide esta pestaña</div><div class="decision-text">Quién lidera, quién está rezagado y qué tan grande es la brecha.</div></div><div class="decision-card"><div class="decision-label">Dónde mirar</div><div class="decision-text">Score, composición de calidad y criticidad por operador.</div></div><div class="decision-card"><div class="decision-label">Qué validar</div><div class="decision-text">Que el ranking coincida con la tabla ejecutiva.</div></div></div>
        <div class="visual-note">
            <div class="visual-note-title">Cómo leer este comparativo</div>
            <div class="visual-note-body">
                Primero ubica el <b>liderazgo</b>, luego la <b>composición de calidad</b> y finalmente valida el resultado en el ranking y la tabla ejecutiva.
            </div>
        </div>
        <div class="story-grid">
            <div class="story-mini">
                <div class="story-label">Líder competitivo</div>
                <div class="story-value">{best_operator["Operador"]}</div>
                <div class="story-sub">Score {best_operator["Score_operador"]:.1f} | Mediana {fmt_dBm(best_operator["RSRP_mediana"])}</div>
            </div>
            <div class="story-mini">
                <div class="story-label">Mayor presión crítica</div>
                <div class="story-value">{worst_operator_crit["Operador"]}</div>
                <div class="story-sub">{fmt_pct(worst_operator_crit["Critica"])} del total en categoría crítica</div>
            </div>
            <div class="story-mini">
                <div class="story-label">Brecha líder-rezago</div>
                <div class="story-value">{fmt_num(best_operator["Score_operador"] - worst_operator["Score_operador"], 1)}</div>
                <div class="story-sub">Puntos de diferencia entre el mejor y peor score</div>
            </div>
        </div>
        <div class="executive-note">
            <div class="executive-highlight">Comparativo de operadores</div>
            <div class="insight-body">
                Esta vista concentra la comparación competitiva entre operadores sin repetir visuales. 
                Primero muestra composición y score, y luego aterriza el ranking ejecutivo consolidado.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(tab_section("Evidencia visual principal", "Score y composición antes de revisar ranking o tabla", "chart"), unsafe_allow_html=True)
    c1, c2 = st.columns((1, 1), gap="large")
    with c1:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Score ejecutivo por operador</div><div class="section-subtitle">Índice compuesto con foco en desempeño agregado y menor exposición crítica.</div>{context_badges('red')}
        """, unsafe_allow_html=True)
        score_chart = alt.Chart(summary_operator.sort_values("Score_operador", ascending=False)).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("Operador:N", title=None, sort="-y"),
            y=alt.Y("Score_operador:Q", title="Score"),
            color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=None),
            tooltip=[
                alt.Tooltip("Operador:N", title="Operador"),
                alt.Tooltip("Score_operador:Q", title="Score", format=".1f"),
                alt.Tooltip("RSRP_mediana:Q", title="RSRP mediano", format=".1f"),
                alt.Tooltip("Buena_o_mejor:Q", title="% buena o mejor", format=".1f"),
                alt.Tooltip("Critica:Q", title="% crítica", format=".1f"),
            ],
        ).properties(height=350)
        st.altair_chart(style_chart(score_chart), use_container_width=True, theme=None)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Composición de calidad</div>
                <div class="section-subtitle">Distribución porcentual por categoría para cada operador dentro del periodo seleccionado.</div>
                <div class="legend-strip">
                    <span class="legend-pill"><span class="legend-dot" style="background:#22C55E;"></span>Excelente</span>
                    <span class="legend-pill"><span class="legend-dot" style="background:#84CC16;"></span>Buena</span>
                    <span class="legend-pill"><span class="legend-dot" style="background:#F59E0B;"></span>Aceptable</span>
                    <span class="legend-pill"><span class="legend-dot" style="background:#EF4444;"></span>Crítica</span>
                </div>
            """,
            unsafe_allow_html=True
        )
        stacked_pct = alt.Chart(quality_pct[quality_pct["Categoria_RSRP"].isin(order_quality[:-1])]).mark_bar().encode(
            x=alt.X("Operador:N", title=None),
            y=alt.Y("Porcentaje:Q", title="% participación"),
            color=alt.Color("Categoria_RSRP:N", scale=alt.Scale(domain=list(QUALITY_COLORS.keys()), range=list(QUALITY_COLORS.values())), legend=alt.Legend(title="Categoría")),
            tooltip=[
                alt.Tooltip("Operador:N", title="Operador"),
                alt.Tooltip("Categoria_RSRP:N", title="Categoría"),
                alt.Tooltip("Porcentaje:Q", title="% participación", format=".1f"),
                alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f")
            ],
        ).properties(height=350)
        st.altair_chart(style_chart(stacked_pct), use_container_width=True, theme=None)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(tab_section("Validación ejecutiva", "Ranking y tabla para confirmar la lectura competitiva", "table"), unsafe_allow_html=True)
    c3, c4 = st.columns((1.05, 0.95), gap="large")
    with c3:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Ranking ejecutivo</div><div class="section-subtitle">Ordenado por mediana de RSRP para lectura rápida de liderazgo y rezago.</div>{context_badges('red')}
        """, unsafe_allow_html=True)
        ranking = alt.Chart(summary_operator.sort_values("RSRP_mediana", ascending=False)).mark_bar(
            cornerRadiusTopLeft=6, cornerRadiusBottomLeft=6
        ).encode(
            x=alt.X("RSRP_mediana:Q", title="RSRP mediano (dBm)"),
            y=alt.Y("Operador:N", sort="-x", title=None),
            color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=None),
            tooltip=[
                alt.Tooltip("Operador:N", title="Operador"),
                alt.Tooltip("RSRP_mediana:Q", title="Mediana", format=".1f"),
                alt.Tooltip("Score_operador:Q", title="Score", format=".1f"),
                alt.Tooltip("Critica:Q", title="% crítica", format=".1f"),
            ],
        ).properties(height=320)
        st.altair_chart(style_chart(ranking), use_container_width=True, theme=None)
        st.markdown('</div>', unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="section-card"><div class="anchor-note"><div class="anchor-note-body"><b>Detalle progresivo:</b> esta tabla conserva el detalle para análisis, mientras la decisión principal se lee en los gráficos y tarjetas superiores.</div></div><div class="anchor-note"><div class="anchor-note-body"><b>Qué mirar aquí:</b> valida si score, mediana RSRP y criticidad cuentan la misma historia por operador.</div></div><div class="section-title">Tabla ejecutiva de operadores</div><div class="section-subtitle">Resumen compacto para revisión gerencial.</div>{context_badges('red')}
        """, unsafe_allow_html=True)
        executive_table = safe_round_columns(
            summary_operator[[
                "Operador", "RSRP_mediana", "Buena_o_mejor", "Critica", "Score_operador", "Clasificacion_score"
            ]].copy(),
            ["RSRP_mediana", "Buena_o_mejor", "Critica", "Score_operador"]
        )
        st.markdown(table_shell("Tabla ejecutiva de operadores"), unsafe_allow_html=True)

        st.dataframe(executive_table, use_container_width=True, height=320)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown(stage_header("03 · Territorio", "Dónde intervenir primero", "Prioriza códigos postales con mayor criticidad y cruza la lectura con operador más débil y referencia territorial.", "map", "red"), unsafe_allow_html=True)
    st.markdown(lane_label("Primero mira la prioridad, después el detalle territorial", "target"), unsafe_allow_html=True)
    st.markdown(tab_kpi_context([
        {"icon": "target", "label": "CP prioritario", "value": enrich_cp_label(worst_zone["Codigo_postal"], worst_zone) if worst_zone is not None else "N/D", "sub": f"{fmt_pct(worst_zone['Pct_critica']) if worst_zone is not None else 'N/D'} crítica"},
        {"icon": "users", "label": "Operador más débil", "value": worst_zone["Operador_mas_debil"] if worst_zone is not None else "N/D", "sub": "En zona prioritaria"},
        {"icon": "map", "label": "CP evaluados", "value": fmt_int(zone_summary["Codigo_postal"].nunique()) if not zone_summary.empty else "0", "sub": "Territorio visible"}
    ]), unsafe_allow_html=True)
    st.markdown(tab_insight("Lectura territorial", tab3_insight_body, "map"), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="user-guide-band"><span class="guide-pill">{icon_svg("target", 13)} Zona crítica</span><span class="guide-pill">{icon_svg("map", 13)} Territorio</span><span class="guide-pill">{icon_svg("table", 13)} Detalle</span></div><div class="decision-strip"><div class="decision-card"><div class="decision-label">Qué decide esta pestaña</div><div class="decision-text">Qué códigos postales deben entrar primero al plan de intervención.</div></div><div class="decision-card"><div class="decision-label">Dónde mirar</div><div class="decision-text">Porcentaje crítico, mediana RSRP y operador más débil.</div></div><div class="decision-card"><div class="decision-label">Qué validar</div><div class="decision-text">Que la prioridad territorial tenga suficiente volumen de registros.</div></div></div>
        <div class="visual-note">
            <div class="visual-note-title">Cómo leer la priorización territorial</div>
            <div class="visual-note-body">
                Esta vista sirve para responder tres preguntas: <b>qué zona atender primero</b>, <b>qué operador está más comprometido</b> y <b>qué referencia positiva existe dentro del territorio</b>.
            </div>
        </div>
        <div class="story-grid">
            <div class="story-mini">
                <div class="story-label">Zona prioritaria</div>
                <div class="story-value">{enrich_cp_label(worst_zone["Codigo_postal"], worst_zone) if worst_zone is not None else "N/D"}</div>
                <div class="story-sub">Crítica {fmt_pct(worst_zone["Pct_critica"]) if worst_zone is not None else "N/D"} | Mediana {fmt_dBm(worst_zone["RSRP_mediana"]) if worst_zone is not None else "N/D"}</div>
            </div>
            <div class="story-mini">
                <div class="story-label">Operador más débil</div>
                <div class="story-value">{worst_zone["Operador_mas_debil"] if worst_zone is not None else "N/D"}</div>
                <div class="story-sub">Principal presión competitiva en la zona prioritaria</div>
            </div>
            <div class="story-mini">
                <div class="story-label">Mejor zona visible</div>
                <div class="story-value">{enrich_cp_label(best_zone["Codigo_postal"], best_zone) if best_zone is not None else "N/D"}</div>
                <div class="story-sub">Cobertura buena o mejor {fmt_pct(best_zone["Pct_buena_o_mejor"]) if best_zone is not None else "N/D"}</div>
            </div>
        </div>
        <div class="executive-note">
            <div class="executive-highlight">Priorización territorial</div>
            <div class="insight-body">
                Esta pestaña concentra las zonas que deben entrar primero al plan de intervención. 
                Se elimina el ruido visual para destacar prioridad, contexto y detalle territorial.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(tab_section("Evidencia territorial principal", "Primero mira el ranking de CP y la lectura territorial", "map"), unsafe_allow_html=True)
    z1, z2 = st.columns((1.15, 0.85), gap="large")
    with z1:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Top zonas prioritarias</div><div class="section-subtitle">Códigos postales con mayor criticidad. La etiqueta incluye localidad y barrio para identificar la zona sin ambigüedad.</div>{context_badges('red')}
        """, unsafe_allow_html=True)
        top_chart = top_zones.copy()
        if not top_chart.empty:
            top_chart["Codigo_postal"] = top_chart["Codigo_postal"].astype(str)
            # Build enriched label: "110111 · Suba · Kennedy"
            def _enrich_cp(row):
                parts = [str(row["Codigo_postal"])]
                if "LOCALIDAD" in row.index and pd.notna(row.get("LOCALIDAD")) and str(row.get("LOCALIDAD","")).strip() not in ("","nan"):
                    parts.append(str(row["LOCALIDAD"]).title())
                if "BARRIO" in row.index and pd.notna(row.get("BARRIO")) and str(row.get("BARRIO","")).strip() not in ("","nan"):
                    parts.append(str(row["BARRIO"]).title())
                return " · ".join(parts)
            top_chart["Zona_label"] = top_chart.apply(_enrich_cp, axis=1)
            has_loc = "LOCALIDAD" in top_chart.columns and top_chart["LOCALIDAD"].notna().any()
            tt = [
                alt.Tooltip("Codigo_postal:N", title="Código postal"),
                alt.Tooltip("Pct_critica:Q", title="% señal crítica", format=".1f"),
                alt.Tooltip("RSRP_mediana:Q", title="Señal mediana (dBm)", format=".1f"),
                alt.Tooltip("Operador_mas_debil:N", title="Operador más débil"),
            ]
            if has_loc:
                tt.insert(1, alt.Tooltip("LOCALIDAD:N", title="Localidad"))
            if "BARRIO" in top_chart.columns and top_chart["BARRIO"].notna().any():
                tt.insert(2, alt.Tooltip("BARRIO:N", title="Barrio"))
            bars = alt.Chart(top_chart.head(12)).mark_bar(cornerRadiusTopLeft=6, cornerRadiusBottomLeft=6).encode(
                x=alt.X("Pct_critica:Q", title="% señal crítica (mayor = peor)"),
                y=alt.Y("Zona_label:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260)),
                color=alt.value("#EF4444"),
                tooltip=tt,
            ).properties(height=420)
            st.altair_chart(style_chart(bars), use_container_width=True, theme=None)
            st.markdown('<div style="font-size:0.75rem;color:#94A3B8;margin-top:4px;">Cada barra = un código postal. El nombre incluye localidad y barrio cuando están disponibles. Cuanto más larga la barra, mayor urgencia.</div>', unsafe_allow_html=True)
        else:
            st.info("No hay datos suficientes para mostrar zonas prioritarias.")
        st.markdown('</div>', unsafe_allow_html=True)

    with z2:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Lectura territorial</div><div class="section-subtitle">Síntesis corta de la mejor y peor zona del universo filtrado.</div>{context_badges('red')}
        """, unsafe_allow_html=True)
        if worst_zone is not None:
            wz_loc = str(worst_zone.get("LOCALIDAD","")).strip() if "LOCALIDAD" in worst_zone.index else ""
            wz_bar = str(worst_zone.get("BARRIO","")).strip() if "BARRIO" in worst_zone.index else ""
            wz_label = str(worst_zone["Codigo_postal"])
            if wz_loc and wz_loc != "nan": wz_label += f" · {wz_loc.title()}"
            if wz_bar and wz_bar != "nan": wz_label += f" · {wz_bar.title()}"
            st.markdown(f'<div class="territory-card"><div class="territory-label">Zona prioritaria</div><div class="territory-value">{wz_label}</div><div class="territory-sub">Señal crítica: <b>{fmt_pct(worst_zone["Pct_critica"])}</b> de las mediciones<br>Operador más débil: <b>{worst_zone["Operador_mas_debil"]}</b><br>Señal mediana: <b>{fmt_dBm(worst_zone["RSRP_mediana"])}</b></div></div>', unsafe_allow_html=True)
        if best_zone is not None:
            bz_loc = str(best_zone.get("LOCALIDAD","")).strip() if "LOCALIDAD" in best_zone.index else ""
            bz_label = str(best_zone["Codigo_postal"])
            if bz_loc and bz_loc != "nan": bz_label += f" · {bz_loc.title()}"
            st.markdown(f'<div class="territory-card"><div class="territory-label">Zona más sólida</div><div class="territory-value">{bz_label}</div><div class="territory-sub">Cobertura buena o mejor: <b>{fmt_pct(best_zone["Pct_buena_o_mejor"])}</b><br>Operador líder: <b>{best_zone["Operador_lider"]}</b></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="section-card"><div class="anchor-note"><div class="anchor-note-body"><b>Detalle progresivo:</b> esta tabla conserva el detalle para análisis, mientras la decisión principal se lee en los gráficos y tarjetas superiores.</div></div><div class="anchor-note"><div class="anchor-note-body"><b>Qué mirar aquí:</b> empieza por criticidad, revisa mediana RSRP y luego identifica el operador más débil de cada zona.</div></div><div class="section-title">Tabla priorizada</div><div class="section-subtitle">Top 12 códigos postales con mayor urgencia territorial dentro del periodo seleccionado.</div>{context_badges('red')}
    """, unsafe_allow_html=True)
    zone_exec = top_zones[zone_exec_cols].copy() if not top_zones.empty else pd.DataFrame(columns=zone_exec_cols)
    if not zone_exec.empty:
        zone_exec["Codigo_postal"] = zone_exec["Codigo_postal"].astype(str)
        # Enrich with locality/barrio label
        def _build_zona_label(row):
            parts = [str(row["Codigo_postal"])]
            if "LOCALIDAD" in row.index and pd.notna(row.get("LOCALIDAD")) and str(row.get("LOCALIDAD","")).strip() not in ("","nan"):
                parts.append(str(row["LOCALIDAD"]).title())
            if "BARRIO" in row.index and pd.notna(row.get("BARRIO")) and str(row.get("BARRIO","")).strip() not in ("","nan"):
                parts.append(str(row["BARRIO"]).title())
            return " · ".join(parts)
        zone_exec.insert(0, "Zona", zone_exec.apply(_build_zona_label, axis=1))
        zone_exec = safe_round_columns(zone_exec.head(12), ["RSRP_mediana", "Pct_critica", "Pct_aceptable", "Pct_buena_o_mejor", "RSRP_mas_debil", "RSRP_lider"])
        # Rename columns to readable Spanish names
        col_rename = {
            "Codigo_postal": "CP", "Semaforo": "Estado", "RSRP_mediana": "Señal mediana (dBm)",
            "Pct_critica": "% Crítica", "Pct_aceptable": "% Aceptable", "Pct_buena_o_mejor": "% Buena o mejor",
            "Operador_mas_debil": "Op. más débil", "RSRP_mas_debil": "Señal Op. débil",
            "Operador_lider": "Op. líder", "RSRP_lider": "Señal Op. líder",
            "Operadores_presentes": "# Operadores", "Registros": "Mediciones",
            "LOCALIDAD": "Localidad", "BARRIO": "Barrio", "RUTA": "Ruta", "CIRCUITO": "Circuito",
        }
        zone_exec = zone_exec.rename(columns={k: v for k, v in col_rename.items() if k in zone_exec.columns})
        st.markdown(table_shell("Tabla priorizada territorial · CP con localidad y barrio identificados"), unsafe_allow_html=True)
        st.dataframe(zone_exec, use_container_width=True, height=360)

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No hay datos de zonas críticas para mostrar.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown(stage_header("04 · Variación", "Cómo cambió la intensidad de señal", "Resume el cambio global, las mayores mejoras, los deterioros y la trayectoria del periodo filtrado.", "trend", "red"), unsafe_allow_html=True)
    st.markdown(lane_label("Primero lee el cambio global, luego revisa extremos", "trend"), unsafe_allow_html=True)
    st.markdown(tab_kpi_context([
        {"icon": "trend", "label": "Variación señal", "value": fmt_var_dBm(variation_result["variacion_global"]), "sub": f"Nivel {nivel_temporal_variacion}"},
        {"icon": "spark", "label": "Mayor mejora", "value": fmt_var_dBm(mayor_mejora["Variacion_RSRP"]) if mayor_mejora is not None else "N/D", "sub": f"CP {str(mayor_mejora['Codigo_postal']) if mayor_mejora is not None else 'N/D'}"},
        {"icon": "target", "label": "Mayor deterioro", "value": fmt_var_dBm(mayor_deterioro["Variacion_RSRP"]) if mayor_deterioro is not None else "N/D", "sub": f"CP {str(mayor_deterioro['Codigo_postal']) if mayor_deterioro is not None else 'N/D'}"}
    ]), unsafe_allow_html=True)
    st.markdown(tab_insight("Lectura de variación", tab4_insight_body, "trend"), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="user-guide-band"><span class="guide-pill">{icon_svg("trend", 13)} Cambio</span><span class="guide-pill">{icon_svg("users", 13)} Mejora</span><span class="guide-pill">{icon_svg("target", 13)} Deterioro</span></div><div class="decision-strip"><div class="decision-card"><div class="decision-label">Qué decide esta pestaña</div><div class="decision-text">Si la intensidad de señal mejora, se deteriora o permanece estable.</div></div><div class="decision-card"><div class="decision-label">Dónde mirar</div><div class="decision-text">Variación global, operador y CP con mayor cambio.</div></div><div class="decision-card"><div class="decision-label">Qué validar</div><div class="decision-text">Que el cambio no dependa de un único punto aislado.</div></div></div>
        <div class="visual-note">
            <div class="visual-note-title">Cómo leer la variación</div>
            <div class="visual-note-body">
                Esta pestaña resume el <b>cambio entre el inicio y el final del periodo</b>, y te ayuda a identificar dónde hubo mayor recuperación y dónde hubo mayor deterioro.
            </div>
        </div>
        <div class="story-grid">
            <div class="story-mini">
                <div class="story-label">Variación global de intensidad de señal</div>
                <div class="story-value">{fmt_var_dBm(variation_result["variacion_global"])}</div>
                <div class="story-sub">Cambio agregado del universo filtrado</div>
            </div>
            <div class="story-mini">
                <div class="story-label">Mayor mejora</div>
                <div class="story-value">{fmt_var_dBm(mayor_mejora["Variacion_RSRP"]) if mayor_mejora is not None else "N/D"}</div>
                <div class="story-sub">CP {str(mayor_mejora["Codigo_postal"]) if mayor_mejora is not None else "N/D"}</div>
            </div>
            <div class="story-mini">
                <div class="story-label">Mayor deterioro</div>
                <div class="story-value">{fmt_var_dBm(mayor_deterioro["Variacion_RSRP"]) if mayor_deterioro is not None else "N/D"}</div>
                <div class="story-sub">CP {str(mayor_deterioro["Codigo_postal"]) if mayor_deterioro is not None else "N/D"}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(f"""
    <div class="section-card"><div class="section-title">Variación ejecutiva de RSRP</div><div class="section-subtitle">Vista compacta del cambio entre el primer y el último periodo disponible.</div>{context_badges('red')}
    """, unsafe_allow_html=True)
    if variation_result["tiene_variacion"]:
        var_badge_text, var_badge_class = variation_status(variation_result["variacion_global"])
        periodo_inicial = pd.to_datetime(variation_result["periodo_inicial"])
        periodo_final = pd.to_datetime(variation_result["periodo_final"])
        st.markdown(f'<div class="{var_badge_class}">Variación global de intensidad de señal {var_badge_text.lower()} | {fmt_var_dBm(variation_result["variacion_global"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="note" style="margin-bottom: 18px;">Periodo inicial: {periodo_inicial.strftime("%d/%m/%Y")} | Periodo final: {periodo_final.strftime("%d/%m/%Y")} | Nivel temporal: {nivel_temporal_variacion}</div>', unsafe_allow_html=True)
    else:
        st.warning(variation_result["message"] or "No hay suficiente información para calcular la variación ejecutiva.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(tab_section("Señales de cambio", "Resume cambio global, mejora y deterioro antes de ver series", "trend"), unsafe_allow_html=True)
    v1, v2, v3 = st.columns(3, gap="medium")
    with v1:
        st.markdown(f'<div class="card"><div class="kpi-label">Variación global de intensidad de señal</div><div class="kpi-value">{fmt_var_dBm(variation_result["variacion_global"])}</div><div class="kpi-sub">Cambio entre mediana final e inicial.</div></div>', unsafe_allow_html=True)
    with v2:
        if mayor_mejora is not None:
            st.markdown(f'<div class="card"><div class="kpi-label">Mayor mejora</div><div class="kpi-value">{fmt_var_dBm(mayor_mejora["Variacion_RSRP"])}</div><div class="kpi-sub">CP {str(mayor_mejora["Codigo_postal"])}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><div class="kpi-label">Mayor mejora</div><div class="kpi-value">N/D</div><div class="kpi-sub">No hay datos suficientes.</div></div>', unsafe_allow_html=True)
    with v3:
        if mayor_deterioro is not None:
            st.markdown(f'<div class="card"><div class="kpi-label">Mayor deterioro</div><div class="kpi-value">{fmt_var_dBm(mayor_deterioro["Variacion_RSRP"])}</div><div class="kpi-sub">CP {str(mayor_deterioro["Codigo_postal"])}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><div class="kpi-label">Mayor deterioro</div><div class="kpi-value">N/D</div><div class="kpi-sub">No hay datos suficientes.</div></div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(tab_section("Evolución y comparación", "Operador y trayectoria para explicar el cambio", "trend"), unsafe_allow_html=True)
    v4, v5 = st.columns((1, 1), gap="large")
    with v4:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Variación por operador</div><div class="section-subtitle">Cambio entre el primer y el último periodo por operador dentro del rango seleccionado.</div>{context_badges('red')}
        """, unsafe_allow_html=True)
        if not variation_operator.empty:
            operator_var_chart = alt.Chart(variation_operator).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Operador:N", title=None, sort="-y"),
                y=alt.Y("Variacion_RSRP:Q", title="Variación RSRP (dBm)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=None),
                tooltip=[
                    alt.Tooltip("Operador:N", title="Operador"),
                    alt.Tooltip("RSRP_inicial:Q", title="RSRP inicial", format=".1f"),
                    alt.Tooltip("RSRP_final:Q", title="RSRP final", format=".1f"),
                    alt.Tooltip("Variacion_RSRP:Q", title="Variación", format=".1f"),
                ],
            ).properties(height=340)
            st.altair_chart(style_chart(operator_var_chart), use_container_width=True, theme=None)
        else:
            st.info("No hay datos suficientes para mostrar la variación por operador.")
        st.markdown('</div>', unsafe_allow_html=True)

    with v5:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Trayectoria agregada</div><div class="section-subtitle">Evolución consolidada de la mediana RSRP dentro del periodo seleccionado.</div>{context_badges('red')}
        """, unsafe_allow_html=True)
        if not variation_period.empty:
            period_col, period_fmt = period_columns(nivel_temporal_variacion)
            line_period = alt.Chart(variation_period).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X(f"{period_col}:T", title="Periodo", axis=alt.Axis(format=period_fmt, labelAngle=0)),
                y=alt.Y("RSRP_mediana:Q", title="RSRP mediano (dBm)"),
                tooltip=[alt.Tooltip(f"{period_col}:T", title="Periodo"), alt.Tooltip("RSRP_mediana:Q", title="RSRP mediano", format=".1f")],
            ).properties(height=340).interactive()
            st.altair_chart(style_chart(line_period), use_container_width=True, theme=None)
        else:
            st.info("No hay datos suficientes para la trayectoria temporal.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(tab_section("Detalle de extremos", "Listas cortas para identificar CP con mayor mejora y deterioro", "target"), unsafe_allow_html=True)
    vd1, vd2 = st.columns((1, 1), gap="large")
    with vd1:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Top mejoras</div><div class="section-subtitle">Primeros registros con mayor variación positiva.</div>{context_badges('red')}
        """, unsafe_allow_html=True)
        if not variation_cp.empty:
            mejora_tbl = safe_round_columns(variation_cp.sort_values("Variacion_RSRP", ascending=False).head(8).copy(), ["RSRP_inicial", "RSRP_final", "Variacion_RSRP"])
            st.markdown(table_shell("Top mejoras por código postal"), unsafe_allow_html=True)

            st.dataframe(mejora_tbl, use_container_width=True, height=260)

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No hay datos suficientes.")
        st.markdown('</div>', unsafe_allow_html=True)

    with vd2:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Top deterioros</div><div class="section-subtitle">Primeros registros con mayor variación negativa.</div>{context_badges('red')}
        """, unsafe_allow_html=True)
        if not variation_cp.empty:
            det_tbl = safe_round_columns(variation_cp.sort_values("Variacion_RSRP", ascending=True).head(8).copy(), ["RSRP_inicial", "RSRP_final", "Variacion_RSRP"])
            st.markdown(table_shell("Top deterioros por código postal"), unsafe_allow_html=True)

            st.dataframe(det_tbl, use_container_width=True, height=260)

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No hay datos suficientes.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with tab5:
    st.markdown(stage_header("05 · Mercado y captación", "Cómo se mueve el negocio", "Conecta mercado, altas, evolución mensual y focos comerciales sin perder el contexto del periodo filtrado.", "briefcase", "negocio"), unsafe_allow_html=True)
    st.markdown(lane_label("Primero identifica liderazgo comercial, luego riesgo y oportunidad", "briefcase"), unsafe_allow_html=True)
    st.markdown(tab_kpi_context([
        {"icon": "briefcase", "label": "Líder mercado", "value": leader_market["Operador"] if leader_market is not None else "N/D", "sub": fmt_pct(leader_market["Cuota_mercado_global"]) if leader_market is not None else "Sin dato"},
        {"icon": "users", "label": "Líder captación", "value": leader_altas["Operador"] if leader_altas is not None else "N/D", "sub": fmt_pct(leader_altas["Participacion_altas_global"]) if leader_altas is not None else "Sin dato"},
        {"icon": "target", "label": "Focos negocio", "value": fmt_int(risk_count + opportunity_count), "sub": f"{risk_count} riesgos · {opportunity_count} oportunidades"}
    ]), unsafe_allow_html=True)
    st.markdown(tab_insight("Lectura comercial", tab5_insight_body, "briefcase"), unsafe_allow_html=True)
    st.markdown("""<div class="decision-strip"><div class="decision-card"><div class="decision-label">Qué decide esta pestaña</div><div class="decision-text">Cómo se relacionan liderazgo comercial, altas y oportunidad territorial.</div></div><div class="decision-card"><div class="decision-label">Dónde mirar</div><div class="decision-text">Líder de mercado, líder de captación y evolución temporal.</div></div><div class="decision-card"><div class="decision-label">Qué validar</div><div class="decision-text">Que la lectura comercial responda al periodo filtrado y al universo visible.</div></div></div>""", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="visual-note">
            <div class="visual-note-title">Cómo leer mercado y captación</div>
            <div class="visual-note-body">
                Esta pestaña muestra <b>quién lidera</b>, <b>cómo se movió entre mes inicial y final</b> y <b>dónde están los focos comerciales prioritarios</b>, sin mezclar la lectura con RSRP en los KPIs de negocio.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div class="business-hero">
            <div class="section-title" style="font-size:1.10rem;">Mercado y Captación</div>
            <div class="section-subtitle" style="max-width:980px; margin-bottom:0;">
                Lectura comercial del territorio visible. Esta pestaña toma directamente los Excel de mercado y altas,
                excluye los códigos 112011, 111981, 112041, 251201 y 251628 y prioriza una síntesis ejecutiva de negocio sin mezclar RSRP.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not business_metrics.get("available", False):
        st.warning(business_metrics.get("message") or "No hay datos de negocio disponibles para la muestra actual.")

    show_market = metric_focus in ["Comparado", "Mercado"]
    show_altas = metric_focus in ["Comparado", "Altas"]

    if metric_focus == "Mercado":
        mk1, mk2, mk3 = st.columns(3, gap="medium")
        with mk1:
            value = fmt_pct(leader_market["Cuota_mercado_global"]) if leader_market is not None else "N/D"
            st.markdown(f'<div class="card"><div class="kpi-label">Líder de mercado</div><div class="metric-operator" style="color:{OPERATOR_COLORS.get(leader_market["Operador"], "#FFFFFF") if leader_market is not None else "#FFFFFF"};">{leader_market["Operador"] if leader_market is not None else "N/D"}</div><div class="kpi-sub">{value} del mercado total visible</div></div>', unsafe_allow_html=True)
        with mk2:
            st.markdown(f'<div class="card"><div class="kpi-label">Mes inicial</div><div class="kpi-value">{fmt_pct(market_month_initial_value)}</div><div class="kpi-sub">{market_month_initial_label or "N/D"} | {market_month_initial_operator or "Sin dato"}</div></div>', unsafe_allow_html=True)
        with mk3:
            st.markdown(f'<div class="card"><div class="kpi-label">Mes final</div><div class="kpi-value">{fmt_pct(market_month_final_value)}</div><div class="kpi-sub">{market_month_final_label or "N/D"} | Δ {fmt_pct(business_metrics.get("variation_market"))}</div></div>', unsafe_allow_html=True)
    elif metric_focus == "Altas":
        mk1, mk2, mk3 = st.columns(3, gap="medium")
        with mk1:
            value = fmt_pct(leader_altas["Participacion_altas_global"]) if leader_altas is not None else "N/D"
            st.markdown(f'<div class="card"><div class="kpi-label">Líder de captación</div><div class="metric-operator" style="color:{OPERATOR_COLORS.get(leader_altas["Operador"], "#FFFFFF") if leader_altas is not None else "#FFFFFF"};">{leader_altas["Operador"] if leader_altas is not None else "N/D"}</div><div class="kpi-sub">{value} de participación sobre el total real</div></div>', unsafe_allow_html=True)
        with mk2:
            st.markdown(f'<div class="card"><div class="kpi-label">Mes inicial</div><div class="kpi-value">{fmt_pct(altas_month_initial_value)}</div><div class="kpi-sub">{altas_month_initial_label or "N/D"} | {altas_month_initial_operator or "Sin dato"}</div></div>', unsafe_allow_html=True)
        with mk3:
            st.markdown(f'<div class="card"><div class="kpi-label">Mes final</div><div class="kpi-value">{fmt_pct(altas_month_final_value)}</div><div class="kpi-sub">{altas_month_final_label or "N/D"} | Δ {fmt_pct(business_metrics.get("variation_altas"))}</div></div>', unsafe_allow_html=True)
    else:
        mk1, mk2, mk3, mk4 = st.columns(4, gap="medium")
        with mk1:
            st.markdown(f'<div class="card"><div class="kpi-label">Mercado · mes inicial</div><div class="kpi-value">{fmt_pct(market_month_initial_value)}</div><div class="kpi-sub">{market_month_initial_label or "N/D"} | {market_month_initial_operator or "Sin dato"}</div></div>', unsafe_allow_html=True)
        with mk2:
            st.markdown(f'<div class="card"><div class="kpi-label">Mercado · mes final</div><div class="kpi-value">{fmt_pct(market_month_final_value)}</div><div class="kpi-sub">{market_month_final_label or "N/D"} | Δ {fmt_pct(business_metrics.get("variation_market"))}</div></div>', unsafe_allow_html=True)
        with mk3:
            st.markdown(f'<div class="card"><div class="kpi-label">Altas · mes inicial</div><div class="kpi-value">{fmt_pct(altas_month_initial_value)}</div><div class="kpi-sub">{altas_month_initial_label or "N/D"} | {altas_month_initial_operator or "Sin dato"}</div></div>', unsafe_allow_html=True)
        with mk4:
            st.markdown(f'<div class="card"><div class="kpi-label">Altas · mes final</div><div class="kpi-value">{fmt_pct(altas_month_final_value)}</div><div class="kpi-sub">{altas_month_final_label or "N/D"} | Δ {fmt_pct(business_metrics.get("variation_altas"))}</div></div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="executive-note">
            <div class="executive-highlight">Lectura estratégica</div>
            <div class="insight-body">
                {(
                    f"El foco principal está en mercado: {leader_market['Operador']} conserva el liderazgo visible con {leader_market['Cuota_mercado_global']:.1f}% y una variación de {business_metrics.get('variation_market'):.1f}% entre el primer y último mes visible."
                    if metric_focus == "Mercado" and leader_market is not None else
                    f"El foco principal está en captación: {leader_altas['Operador']} lidera las altas visibles con {leader_altas['Participacion_altas_global']:.1f}% y una variación de {business_metrics.get('variation_altas'):.1f}% entre el primer y último mes visible."
                    if metric_focus == "Altas" and leader_altas is not None else
                    f"{leader_market['Operador'] if leader_market is not None else 'N/D'} lidera mercado y {leader_altas['Operador'] if leader_altas is not None else 'N/D'} lidera captación, lo que permite evaluar si el liderazgo de base instalada coincide o no con el momentum comercial."
                )}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    mt1, mt2 = st.columns((1, 1), gap="large")
    with mt1:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Mercado por operador</div><div class="section-subtitle">Participación visible acumulada por operador en el periodo seleccionado. La visualización responde al rango de fechas, operadores, territorio y vista de negocio seleccionados.</div>{context_badges('negocio')}
        """, unsafe_allow_html=True)
        if not market_operator.empty:
            market_chart = alt.Chart(market_operator.head(6)).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Operador:N", sort="-y", title=None),
                y=alt.Y("Cuota_mercado_global:Q", title="Cuota mercado (%)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=None),
                tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("Mercado_total:Q", format=",.1f"), alt.Tooltip("Cuota_mercado_global:Q", format=".1f")]
            ).properties(height=320)
            st.altair_chart(style_chart(market_chart), use_container_width=True, theme=None)
        else:
            st.info("No se encontraron datos de mercado.")
        st.markdown('</div>', unsafe_allow_html=True)

    with mt2:
        st.markdown(f"""
        <div class="section-card"><div class="section-title">Altas por operador</div><div class="section-subtitle">Participación visible de captación por operador en el periodo filtrado.</div>{context_badges('negocio')}
        """, unsafe_allow_html=True)
        if not altas_operator.empty:
            altas_chart = alt.Chart(altas_operator.head(6)).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Operador:N", sort="-y", title=None),
                y=alt.Y("Participacion_altas_global:Q", title="Participación altas (%)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=None),
                tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("Altas_total:Q", format=",.1f"), alt.Tooltip("Participacion_altas_global:Q", format=".1f")]
            ).properties(height=320)
            st.altair_chart(style_chart(altas_chart), use_container_width=True, theme=None)
        else:
            st.info("No se encontraron datos de altas.")
        st.markdown('</div>', unsafe_allow_html=True)

    mt3, mt4 = st.columns((1, 1), gap="large")
    with mt3:
        st.markdown('<div class="section-card"><div class="section-title">Evolución mensual de share</div><div class="section-subtitle">Trayectoria de participación de mercado por operador.</div>', unsafe_allow_html=True)
        if not market_time.empty:
            market_time_chart = alt.Chart(market_time).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X("Periodo_Mes:T", title="Mes", axis=alt.Axis(format="%b %Y", labelAngle=0)),
                y=alt.Y("Cuota_mercado:Q", title="Share mercado (%)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=alt.Legend(title="Operador")),
                tooltip=[alt.Tooltip("Periodo_Mes:T"), alt.Tooltip("Operador:N"), alt.Tooltip("Cuota_mercado:Q", format=".1f")]
            ).properties(height=340).interactive()
            st.altair_chart(style_chart(market_time_chart), use_container_width=True, theme=None)
        else:
            st.info("No se detectó evolución temporal de mercado.")
        st.markdown('</div>', unsafe_allow_html=True)

    with mt4:
        st.markdown('<div class="section-card"><div class="section-title">Evolución mensual de captación</div><div class="section-subtitle">Trayectoria de participación de altas por operador.</div>', unsafe_allow_html=True)
        if not altas_time.empty:
            altas_time_chart = alt.Chart(altas_time).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X("Periodo_Mes:T", title="Mes", axis=alt.Axis(format="%b %Y", labelAngle=0)),
                y=alt.Y("Participacion_altas:Q", title="Share altas (%)"),
                color=alt.Color("Operador:N", scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()), range=list(OPERATOR_COLORS.values())), legend=alt.Legend(title="Operador")),
                tooltip=[alt.Tooltip("Periodo_Mes:T"), alt.Tooltip("Operador:N"), alt.Tooltip("Participacion_altas:Q", format=".1f")]
            ).properties(height=340).interactive()
            st.altair_chart(style_chart(altas_time_chart), use_container_width=True, theme=None)
        else:
            st.info("No se detectó evolución temporal de altas.")
        st.markdown('</div>', unsafe_allow_html=True)

    mt5, mt6 = st.columns((1, 1), gap="large")
    with mt5:
        st.markdown('<div class="section-card"><div class="section-title">Movimiento de share por operador</div><div class="section-subtitle">Cambio de participación entre el primer y el último mes visible.</div>', unsafe_allow_html=True)
        if not market_operator_delta.empty:
            delta_market_chart = alt.Chart(market_operator_delta).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Variacion:Q", title="Variación share (pp)"),
                y=alt.Y("Operador:N", sort="-x", title=None),
                color=alt.condition(alt.datum.Variacion >= 0, alt.value("#22C55E"), alt.value("#EF4444")),
                tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("Valor_inicial:Q", format=".1f"), alt.Tooltip("Valor_final:Q", format=".1f"), alt.Tooltip("Variacion:Q", format=".1f")]
            ).properties(height=300)
            st.altair_chart(style_chart(delta_market_chart), use_container_width=True, theme=None)
        else:
            st.info("No hay datos suficientes para medir movimiento de share.")
        st.markdown('</div>', unsafe_allow_html=True)

    with mt6:
        st.markdown('<div class="section-card"><div class="section-title">Movimiento de captación por operador</div><div class="section-subtitle">Cambio de participación en altas entre el primer y el último mes visible.</div>', unsafe_allow_html=True)
        if not altas_operator_delta.empty:
            delta_altas_chart = alt.Chart(altas_operator_delta).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Variacion:Q", title="Variación captación (pp)"),
                y=alt.Y("Operador:N", sort="-x", title=None),
                color=alt.condition(alt.datum.Variacion >= 0, alt.value("#22C55E"), alt.value("#EF4444")),
                tooltip=[alt.Tooltip("Operador:N"), alt.Tooltip("Valor_inicial:Q", format=".1f"), alt.Tooltip("Valor_final:Q", format=".1f"), alt.Tooltip("Variacion:Q", format=".1f")]
            ).properties(height=300)
            st.altair_chart(style_chart(delta_altas_chart), use_container_width=True, theme=None)
        else:
            st.info("No hay datos suficientes para medir movimiento de captación.")
        st.markdown('</div>', unsafe_allow_html=True)

    mt7, mt8 = st.columns((1, 1), gap="large")
    with mt7:
        st.markdown('<div class="section-card"><div class="section-title">Ranking ejecutivo de mercado</div><div class="section-subtitle">Resumen compacto del peso comercial por operador.</div>', unsafe_allow_html=True)
        if not market_operator.empty:
            market_show = safe_round_columns(market_operator[["Operador", "Mercado_total", "Cuota_mercado_global", "Codigos"]].copy(), ["Mercado_total", "Cuota_mercado_global"])
            st.dataframe(market_show, use_container_width=True, height=300)
        else:
            st.info("No hay datos de mercado para mostrar.")
        st.markdown('</div>', unsafe_allow_html=True)

    with mt8:
        st.markdown('<div class="section-card"><div class="section-title">Ranking ejecutivo de altas</div><div class="section-subtitle">Resumen compacto del desempeño de captación por operador.</div>', unsafe_allow_html=True)
        if not altas_operator.empty:
            altas_show = safe_round_columns(altas_operator[["Operador", "Altas_total", "Participacion_altas_global", "Codigos"]].copy(), ["Altas_total", "Participacion_altas_global"])
            st.dataframe(altas_show, use_container_width=True, height=300)
        else:
            st.info("No hay datos de altas para mostrar.")
        st.markdown('</div>', unsafe_allow_html=True)


st.markdown(
    """
    <div class="section-card" style="margin-top:14px;">
        <div class="section-title">Cierre ejecutivo</div>
        <div class="section-subtitle">Recomendación de uso del tablero.</div>
        <div class="insight-body">
            Usa el sidebar como centro de control premium para alternar foco entre Mercado, Altas o vista comparada,
            acotar por cuota y leer el tablero por zonas de alta competencia, dominio claro o territorios de bajo desarrollo.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="small-caption">
        Nota metodológica: se consideran mediciones válidas únicamente valores negativos de RSRP. La clasificación aplicada es:
        Excelente (hasta 70 dBm en valor absoluto), Buena (71 a 90 dBm), Aceptable (91 a 100 dBm) y Crítica (más de 100 dBm en valor absoluto).
        La variación ejecutiva compara la mediana del primer y del último periodo disponible según el nivel temporal seleccionado ({nivel_temporal_variacion}).
        La pestaña Mercado y Captación se alimenta desde los archivos Excel de cuota de mercado y cuota de altas, y resume liderazgo, momentum y variación de volumen sin mezclar métricas de RSRP.
    </div>
    """,
    unsafe_allow_html=True,
)
