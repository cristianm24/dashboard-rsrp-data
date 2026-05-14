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
            <div class="compact-context-sub">Mediana {fmt_dBm(best_operator["RSRP_mediana"])}</div>
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
            cuota_low  = territorial_cross["Cuota_mercado"].quantile(0.40)
            # Risk: bad signal + high market share (at risk of losing market due to signal)
            risk = territorial_cross[
                (territorial_cross["RSRP_mediana"] < -100) &
                (territorial_cross["Cuota_mercado"] >= cuota_high)
            ].copy()
            # Opportunity: relatively better signal + low market share (room to grow)
            # Use relative threshold — top 40% of signal in dataset, not absolute -80
            rsrp_good_threshold = territorial_cross["RSRP_mediana"].quantile(0.60)
            opp = territorial_cross[
                (territorial_cross["RSRP_mediana"] >= rsrp_good_threshold) &
                (territorial_cross["Cuota_mercado"] <= cuota_low)
            ].copy()
            result["risk_table"]        = risk.sort_values(["Cuota_mercado","RSRP_mediana"], ascending=[False,True]).head(25)
            result["opportunity_table"] = opp.sort_values(["RSRP_mediana","Cuota_mercado"], ascending=[False,True]).head(25)

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
# =========================================================
# Columnas críticas y opcionales para validación
# =========================================================
CLARO_FILE_CANDIDATES = [
    os.path.join(BASE_DIR, "Plan_actualizado_CORTE_30_FINAL.xlsx"),
    os.path.join(BASE_DIR, "Plan_actualizado_CORTE_28_FINAL.xlsx"),
    os.path.join(BASE_DIR, "Plan_actualizado_CORTE_28_FINAL(1).xlsx"),
]

COLUMNAS_REQUERIDAS = [
    "AGENTE", "ID", "META ALTA NAT (>$2000)", "EJEC ALTA NAT",
    "EJE ALTA TOTAL", "CATEGORIA", "ASESOR",
]
COLUMNAS_OPCIONALES = {
    "META ALTA INDU (=< $2.000)": 0,
    "EJEC ALTA INDU": 0,
    "CUOTA DE ALTA": np.nan,
    "CUOTA DE MERCADO": np.nan,
    "RSRP": np.nan,
    "S1": 0, "S2": 0, "S3": 0, "S4": 0,
    "S1.1": 0, "S2.1": 0, "S3.1": 0, "S4.1": 0,
    "VR_M-1": np.nan, "VR_M-1.1": np.nan, "VR_M-12": np.nan, "VR_M-12.1": np.nan,
    "BARRIO": None, "ZONA": None, "RUTA": None, "CIRCUITO": None,
    "TIPOLOGIA": None, "CLASIFICACION": None,
    "META INGRESOS M0": np.nan, "EJEC INGRESOS M0": np.nan,
}

def _find_detail_sheet(xl):
    """
    Detecta automáticamente la hoja principal de datos buscando por contenido,
    no por nombre. Busca la hoja que tenga al menos 3 columnas requeridas.
    Retorna (sheet_name, None) si encuentra, (None, mensaje_error) si no.
    """
    available = xl.sheet_names
    best_sheet = None
    best_score = 0

    for sheet in available:
        try:
            # Read only headers — fast
            preview = pd.read_excel(xl, sheet_name=sheet, header=0, nrows=0)
            cols = [str(c).strip() for c in preview.columns]
            score = sum(1 for c in COLUMNAS_REQUERIDAS if c in cols)
            if score > best_score:
                best_score = score
                best_sheet = sheet
        except Exception:
            continue

    if best_sheet is None or best_score < 3:
        return None, (
            f"No se encontró ninguna hoja con las columnas del plan de trabajo. "
            f"Hojas disponibles: {', '.join(available)}. "
            f"La hoja principal debe tener columnas como: {', '.join(COLUMNAS_REQUERIDAS[:4])}..."
        )
    return best_sheet, None
    """Limpia y coerciona tipos. Retorna (df_limpio, columnas_faltantes, columnas_nuevas)."""
    df_det.columns = [str(c).strip() for c in df_det.columns]
    cols_excel = set(df_det.columns)

    # Columnas requeridas faltantes
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in cols_excel]

    # Columnas opcionales faltantes → rellenar con valor por defecto
    for c, default in COLUMNAS_OPCIONALES.items():
        if c not in df_det.columns:
            df_det[c] = default

    # Columnas nuevas no reconocidas
    conocidas = set(COLUMNAS_REQUERIDAS) | set(COLUMNAS_OPCIONALES.keys()) | {
        "TOTAL META ALTA", "% CUMPLI", "META ARPU", "EJEC ARPU",
        "VR_M-1.2", "VR_M-12.2", "TIPO", "CODIGO POSTAL",
    }
    nuevas = sorted(cols_excel - conocidas - {"AGENTE","ID","ASESOR","CATEGORIA",
                     "TIPOLOGIA","CLASIFICACION","BARRIO","ZONA","RUTA","CIRCUITO"})

    # Coerción numérica
    num_cols = list(COLUMNAS_OPCIONALES.keys()) + [
        "TOTAL META ALTA", "EJE ALTA TOTAL", "META ALTA NAT (>$2000)", "EJEC ALTA NAT",
        "% CUMPLI", "META ARPU", "EJEC ARPU", "META INGRESOS M0", "EJEC INGRESOS M0",
    ]
    for c in num_cols:
        if c in df_det.columns:
            df_det[c] = pd.to_numeric(df_det[c], errors="coerce")

    # Coerción string
    for c in ["AGENTE","CATEGORIA","TIPOLOGIA","CLASIFICACION","ZONA","TIPO","ASESOR","RUTA","CIRCUITO","BARRIO"]:
        if c in df_det.columns:
            df_det[c] = df_det[c].astype(str).str.strip().replace("nan", pd.NA)

    return df_det, faltantes, nuevas


def load_claro_data_from_path(path):
    """Carga desde ruta en disco. Nunca lanza excepciones — siempre retorna estado."""
    try:
        xl = pd.ExcelFile(path)
        available_sheets = xl.sheet_names
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
            "found": False, "message": f"No se pudo abrir el archivo: {e}"
        }

    # Hoja principal — detección automática por contenido
    sheet_name, err = _find_detail_sheet(xl)
    if err:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
            "found": False, "message": err
        }
    try:
        df_det = pd.read_excel(xl, sheet_name=sheet_name, header=0)
        df_det, faltantes, nuevas = _process_claro_df(df_det)
        if faltantes:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
                "found": False,
                "message": f"Faltan columnas requeridas en '{sheet_name}': {', '.join(faltantes)}"
            }
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
            "found": False, "message": f"Error leyendo hoja '{sheet_name}': {e}"
        }

    # Hoja Cierre — opcional
    df_cierre = pd.DataFrame()
    for sheet_name in ["Cierre marzo", "Cierre abril", "Cierre mayo", "Cierre junio",
                        "Cierre julio", "Cierre agosto", "Cierre septiembre",
                        "Cierre octubre", "Cierre noviembre", "Cierre diciembre"]:
        if sheet_name in available_sheets:
            try:
                df_cierre = pd.read_excel(xl, sheet_name=sheet_name, header=0)
                df_cierre.columns = [str(c).strip() for c in df_cierre.columns]
                if len(df_cierre.columns) >= 3:
                    df_cierre = df_cierre.iloc[:, :3]
                    df_cierre.columns = ["ID_POS", "MAR_ALTAS", "MAR_INGRESOS"]
                    df_cierre["MAR_ALTAS"]    = pd.to_numeric(df_cierre["MAR_ALTAS"],    errors="coerce")
                    df_cierre["MAR_INGRESOS"] = pd.to_numeric(df_cierre["MAR_INGRESOS"], errors="coerce")
            except Exception:
                df_cierre = pd.DataFrame()
            break

    # Hoja plan agente — opcional
    df_plan = pd.DataFrame()
    for sheet_name in [s for s in available_sheets if s not in ["plan_trabajo"] and
                        not s.lower().startswith("cierre")]:
        try:
            df_plan = pd.read_excel(xl, sheet_name=sheet_name, header=5)
            df_plan.columns = [str(c).strip() for c in df_plan.columns]
            break
        except Exception:
            continue

    return df_det, df_cierre, df_plan, {
        "found": True, "message": None, "path": str(path),
        "columnas_nuevas": nuevas,
        "hojas_disponibles": available_sheets,
    }


def load_claro_data_from_upload(uploaded_file):
    """Carga desde archivo subido. Nunca lanza excepciones — siempre retorna estado."""
    try:
        xl = pd.ExcelFile(uploaded_file)
        available_sheets = xl.sheet_names
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
            "found": False, "message": f"No se pudo abrir el archivo: {e}"
        }

    sheet_name, err = _find_detail_sheet(xl)
    if err:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
            "found": False, "message": err
        }
    try:
        df_det = pd.read_excel(xl, sheet_name=sheet_name, header=0)
        df_det, faltantes, nuevas = _process_claro_df(df_det)
        if faltantes:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
                "found": False,
                "message": f"Faltan columnas requeridas en '{sheet_name}': {', '.join(faltantes)}"
            }
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
            "found": False, "message": f"Error leyendo hoja '{sheet_name}': {e}"
        }

    df_cierre = pd.DataFrame()
    for sheet_name in ["Cierre marzo", "Cierre abril", "Cierre mayo", "Cierre junio",
                        "Cierre julio", "Cierre agosto", "Cierre septiembre",
                        "Cierre octubre", "Cierre noviembre", "Cierre diciembre"]:
        if sheet_name in available_sheets:
            try:
                df_cierre = pd.read_excel(xl, sheet_name=sheet_name, header=0)
                df_cierre.columns = [str(c).strip() for c in df_cierre.columns]
                if len(df_cierre.columns) >= 3:
                    df_cierre = df_cierre.iloc[:, :3]
                    df_cierre.columns = ["ID_POS", "MAR_ALTAS", "MAR_INGRESOS"]
                    df_cierre["MAR_ALTAS"]    = pd.to_numeric(df_cierre["MAR_ALTAS"],    errors="coerce")
                    df_cierre["MAR_INGRESOS"] = pd.to_numeric(df_cierre["MAR_INGRESOS"], errors="coerce")
            except Exception:
                df_cierre = pd.DataFrame()
            break

    df_plan = pd.DataFrame()
    for sheet_name in [s for s in available_sheets if s not in ["plan_trabajo"] and
                        not s.lower().startswith("cierre")]:
        try:
            df_plan = pd.read_excel(xl, sheet_name=sheet_name, header=5)
            df_plan.columns = [str(c).strip() for c in df_plan.columns]
            break
        except Exception:
            continue

    return df_det, df_cierre, df_plan, {
        "found": True, "message": None, "path": uploaded_file.name,
        "columnas_nuevas": nuevas,
        "hojas_disponibles": available_sheets,
    }


def load_claro_data():
    """
    Punto de entrada principal.
    Prioridad: 1) archivo subido por usuario  2) archivo en disco (desarrollo)
    """
    uploaded = st.session_state.get("claro_uploaded_file")
    if uploaded is not None:
        return load_claro_data_from_upload(uploaded)
    # Fallback disco
    path = find_existing_file(CLARO_FILE_CANDIDATES)
    if path:
        return load_claro_data_from_path(path)
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {
        "found": False,
        "message": "No se encontró archivo. Usa el cargador del sidebar para subir el Excel del mes."
    }
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
        df_det = pd.read_excel(path, sheet_name="plan_trabajo", header=0)
        df_det.columns = [str(c).strip() for c in df_det.columns]
        # Numeric coercion
        num_cols = [
            "META ALTA NAT (>$2000)", "EJEC ALTA NAT", "META ALTA INDU (=< $2.000)", "EJEC ALTA INDU",
            "TOTAL META ALTA", "EJE ALTA TOTAL", "% CUMPLI", "META ARPU", "EJEC ARPU",
            "META INGRESOS M0", "EJEC INGRESOS M0", "CUOTA DE MERCADO", "CUOTA DE ALTA",
            "RSRP", "S1", "S2", "S3", "S4", "S1.1", "S2.1", "S3.1", "S4.1",
            "VR_M-1", "VR_M-1.1", "VR_M-1.2", "VR_M-12", "VR_M-12.1", "VR_M-12.2",
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
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:40px;text-align:center;margin:40px 0;">
            <div style="font-size:2rem;margin-bottom:12px;">📂</div>
            <div style="font-size:1.1rem;font-weight:800;color:#F8FAFC;margin-bottom:8px;">Sin datos cargados</div>
            <div style="font-size:.84rem;color:#94A3B8;">{info.get('message', 'Sube el archivo Excel del mes usando el cargador del sidebar.')}</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # =========================================================
    # SIDEBAR CLARO: Filtros propios
    # =========================================================
    st.sidebar.markdown("---")
    # Date range from actual data
    _fecha_label = ""
    if "FECHA" in df_det.columns or any("FECHA" in c.upper() for c in df_det.columns):
        _fc = next((c for c in df_det.columns if "FECHA" in c.upper()), None)
        if _fc:
            _fmin = pd.to_datetime(df_det[_fc], errors="coerce").min()
            _fmax = pd.to_datetime(df_det[_fc], errors="coerce").max()
            if pd.notna(_fmin):
                _fecha_label = f'<div style="margin-top:8px;padding:8px 10px;background:rgba(225,6,0,0.10);border:1px solid rgba(225,6,0,0.22);border-radius:12px;font-size:0.73rem;color:#FCA5A5;font-weight:700;">📅 {_fmin.strftime("%d/%m/%Y")} – {_fmax.strftime("%d/%m/%Y")}</div>'
    _n_pdvs = len(df_det)
    _n_ags  = df_det["AGENTE"].nunique() if "AGENTE" in df_det.columns else 0
    _archivo_label = f'<div style="margin-top:6px;font-size:.68rem;color:#64748B;">{os.path.basename(str(info.get("path","")))} · {_n_pdvs:,} PDVs · {_n_ags} agentes</div>'
    st.sidebar.markdown(f'<div class="sidebar-block"><div class="sidebar-kicker">{icon_svg("spark",12)} Vista Claro · Filtros</div><div class="sidebar-title">Personaliza la vista</div><div class="sidebar-sub">Filtra el universo de PDVs por agente, categoría, zona, circuito, ruta, barrio y más.</div>{_fecha_label}{_archivo_label}', unsafe_allow_html=True)

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
    meta_indu_total   = df["META ALTA INDU (=< $2.000)"].sum() if "META ALTA INDU (=< $2.000)" in df.columns else 0
    ejec_indu_total   = df["EJEC ALTA INDU"].sum() if "EJEC ALTA INDU" in df.columns else 0
    # Meta total real = orgánicas + inducidas (TOTAL META ALTA en el archivo es otra métrica)
    meta_total_real   = meta_nat_total + meta_indu_total
    ejec_total_alta   = df["EJE ALTA TOTAL"].sum()
    meta_total_alta   = meta_total_real   # alias para compatibilidad
    meta_ingresos     = df["META INGRESOS M0"].sum()
    ejec_ingresos     = df["EJEC INGRESOS M0"].sum()
    cuota_mkt_media   = df["CUOTA DE MERCADO"].mean()
    cuota_alta_media  = df["CUOTA DE ALTA"].mean()
    rsrp_media        = df["RSRP"].mean()

    cumplimiento_nat  = (ejec_nat_total  / meta_nat_total  * 100) if meta_nat_total  > 0 else np.nan
    cumplimiento_tot  = (ejec_total_alta / meta_total_real * 100) if meta_total_real > 0 else np.nan

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
            <div class="hero-title">Agentes Claro · Abril 2026</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Cálculos previos necesarios para el nav guide ─────────────────────────
    _DIA_CORTE_NAV = 30; _DIAS_MES_NAV = 30; _FACTOR_NAV = 1.0  # mes completo
    _proy_global   = ((ejec_nat_total + ejec_indu_total) / (meta_nat_total + meta_indu_total) * 100) if (meta_nat_total + meta_indu_total) > 0 else 0
    _cumpl_nav     = (ejec_nat_total / meta_nat_total * 100) if meta_nat_total > 0 else 0
    _pdvs_riesgo   = int(((df["META ALTA NAT (>$2000)"] > 0) &
                          ((df["EJEC ALTA NAT"] / df["META ALTA NAT (>$2000)"].replace(0,np.nan)*100).fillna(0) < 70)).sum())
    _by_ag_nav     = df.groupby("AGENTE").agg(ejec_nat=("EJEC ALTA NAT","sum"), meta_nat=("META ALTA NAT (>$2000)","sum")).reset_index()
    _by_ag_nav["proy"] = (_by_ag_nav["ejec_nat"] / _by_ag_nav["meta_nat"].replace(0,np.nan) * 100).fillna(0)
    _ag_riesgo     = (_by_ag_nav["proy"] < 70).sum()
    _s_vals_nav    = {s: float(df[s].sum()) if s in df.columns else 0.0 for s in ["S1","S2","S3","S4"]}
    _s_list        = [_s_vals_nav["S1"],_s_vals_nav["S2"],_s_vals_nav["S3"],_s_vals_nav["S4"]]
    _tendencia_ok  = _s_list[2] >= _s_list[1] >= _s_list[0]
    _sem_c         = lambda v: "#22C55E" if v>=100 else "#F59E0B" if v>=70 else "#EF4444"
    _dot           = lambda v: f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{_sem_c(v)};margin-right:5px;flex-shrink:0;"></span>'

    # SVG icons — professional, no emojis
    def _nav_icon(name):
        icons = {
            "chart": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
            "users": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
            "map":   '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>',
            "trend": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
            "target":'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
        }
        return icons.get(name, "")

    # ── Franja de navegación visual ───────────────────────────────────────────
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:12px 0 4px 0;">
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
            <div style="margin-bottom:6px;">{_nav_icon("chart")}</div>
            <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:3px;line-height:1.3;">¿Cómo vamos?</div>
            <div style="font-size:.66rem;color:#64748B;margin-bottom:6px;line-height:1.3;">Estado del mes y proyección</div>
            <div style="display:flex;align-items:center;gap:4px;font-size:.70rem;font-weight:800;color:{_sem_c(_proy_global)};">{_dot(_proy_global)}Cumpl. {_proy_global:.0f}%</div>
        </div>
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
            <div style="margin-bottom:6px;">{_nav_icon("users")}</div>
            <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:3px;line-height:1.3;">¿Quién cumple?</div>
            <div style="font-size:.66rem;color:#64748B;margin-bottom:6px;line-height:1.3;">Agentes vs su meta</div>
            <div style="display:flex;align-items:center;gap:4px;font-size:.70rem;font-weight:800;color:{_sem_c(100 if _ag_riesgo==0 else 70 if _ag_riesgo<=2 else 0)};">{_dot(100 if _ag_riesgo==0 else 70 if _ag_riesgo<=2 else 0)}{_ag_riesgo} en riesgo</div>
        </div>
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
            <div style="margin-bottom:6px;">{_nav_icon("map")}</div>
            <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:3px;line-height:1.3;">Brecha</div>
            <div style="font-size:.66rem;color:#64748B;margin-bottom:6px;line-height:1.3;">PDVs y circuitos críticos</div>
            <div style="display:flex;align-items:center;gap:4px;font-size:.70rem;font-weight:800;color:{_sem_c(0 if _pdvs_riesgo>5000 else 70 if _pdvs_riesgo>2000 else 100)};">{_dot(0 if _pdvs_riesgo>5000 else 70 if _pdvs_riesgo>2000 else 100)}{_pdvs_riesgo:,} PDVs</div>
        </div>
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
            <div style="margin-bottom:6px;">{_nav_icon("trend")}</div>
            <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:3px;line-height:1.3;">¿Sube el ritmo?</div>
            <div style="font-size:.66rem;color:#64748B;margin-bottom:6px;line-height:1.3;">Curva semanal de ventas</div>
            <div style="font-size:.70rem;font-weight:800;color:{'#22C55E' if _tendencia_ok else '#EF4444'};">{'▲ Positiva' if _tendencia_ok else '▼ A la baja'}</div>
        </div>
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
            <div style="margin-bottom:6px;">{_nav_icon("target")}</div>
            <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:3px;line-height:1.3;">¿Dónde ganar más?</div>
            <div style="font-size:.66rem;color:#64748B;margin-bottom:6px;line-height:1.3;">Cuota de altas y señal</div>
            <div style="font-size:.70rem;font-weight:800;color:#38BDF8;">Ver oportunidades →</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================
    # TABS
    # =========================================================
    tc1, tc2, tc3, tc4, tc5 = st.tabs([
        "↗  ¿Cómo vamos?",
        "◈  ¿Quién cumple?",
        "◎  La brecha",
        "∿  El ritmo",
        "◉  Oportunidades",
    ])

    # -------------------------------------------------------
    # TAB C1 — ¿CÓMO VAMOS?
    # -------------------------------------------------------
    with tc1:
        # Sistema dinámico: si día corte = días del mes → mes cerrado (resultado final)
        # Si día corte < días del mes → mes en curso (mostrar proyección)
        _DIA_CORTE = 30; _DIAS_MES = 30
        _MES_CERRADO_BANNER = (_DIA_CORTE >= _DIAS_MES)
        _FACTOR_BANNER = 1.0 if _MES_CERRADO_BANNER else _DIAS_MES / _DIA_CORTE

        _meta_total     = meta_nat_total + meta_indu_total
        _ejec_total     = ejec_total_alta
        _cumpl_total    = (_ejec_total / _meta_total * 100) if _meta_total > 0 else 0
        _proy_total     = (_ejec_total * _FACTOR_BANNER / _meta_total * 100) if _meta_total > 0 else 0
        _valor_banner   = _cumpl_total if _MES_CERRADO_BANNER else _proy_total
        _cumpl_nat_tc1  = (ejec_nat_total  / meta_nat_total  * 100) if meta_nat_total  > 0 else 0
        _cumpl_indu_tc1 = (ejec_indu_total / meta_indu_total * 100) if meta_indu_total > 0 else 0
        _proy_nat_tc1   = (_cumpl_nat_tc1  * _FACTOR_BANNER) if not _MES_CERRADO_BANNER else _cumpl_nat_tc1
        _proy_indu_tc1  = (_cumpl_indu_tc1 * _FACTOR_BANNER) if not _MES_CERRADO_BANNER else _cumpl_indu_tc1
        _pdvs_con_meta  = int((df["META ALTA NAT (>$2000)"] > 0).sum())
        _cumpl_pdv_ser  = (df["EJEC ALTA NAT"] / df["META ALTA NAT (>$2000)"].replace(0, np.nan) * 100).fillna(0)
        _pdvs_bajo70    = int(((df["META ALTA NAT (>$2000)"] > 0) & (_cumpl_pdv_ser < 70)).sum())
        _pct_bajo70     = (_pdvs_bajo70 / _pdvs_con_meta * 100) if _pdvs_con_meta > 0 else 0

        def _sc(v): return "#22C55E" if v >= 100 else "#F59E0B" if v >= 70 else "#EF4444"
        def _bar(pct, color):
            w = min(max(pct, 0), 100)
            return f'<div style="width:100%;height:6px;background:rgba(255,255,255,0.08);border-radius:99px;margin-top:6px;overflow:hidden;"><div style="width:{w}%;height:100%;background:{color};border-radius:99px;"></div></div>'

        _c_banner  = _sc(_valor_banner)
        _titulo_banner = "Resultado final · Mes completo" if _MES_CERRADO_BANNER else f"Proyección al cierre · Día {_DIA_CORTE} de {_DIAS_MES}"
        _lbl_nat   = "Orgánicas (final)" if _MES_CERRADO_BANNER else f"Orgánicas (proy.)"
        _lbl_indu  = "Inducidas (final)" if _MES_CERRADO_BANNER else f"Inducidas (proy.)"
        _val_nat   = _cumpl_nat_tc1 if _MES_CERRADO_BANNER else _proy_nat_tc1
        _val_indu  = _cumpl_indu_tc1 if _MES_CERRADO_BANNER else _proy_indu_tc1

        if _MES_CERRADO_BANNER:
            _estado_txt = "✅ Meta total cumplida — cierre exitoso" if _valor_banner >= 100 else ("🟡 Cierre por encima del 70%" if _valor_banner >= 70 else "🔴 Meta total no alcanzada al cierre del mes")
        else:
            _estado_txt = "✅ En camino a cumplir la meta" if _valor_banner >= 100 else ("⚠️ Recuperable con esfuerzo" if _valor_banner >= 85 else "🔴 Meta en riesgo — se necesita acción")

        # ── Protagonista ──────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.96),rgba(10,18,34,0.98));border:1px solid rgba(255,255,255,0.10);border-radius:24px;padding:24px 28px;margin-bottom:16px;display:flex;align-items:center;gap:32px;">
            <div style="flex:0 0 auto;">
                <div style="font-size:.72rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;">{_titulo_banner}</div>
                <div style="font-size:3.8rem;font-weight:950;color:{_c_banner};line-height:1;">{_valor_banner:.1f}%</div>
                <div style="font-size:.84rem;color:#CBD5E1;margin-top:6px;">{_estado_txt}</div>
                {_bar(_valor_banner, _c_banner)}
                <div style="font-size:.70rem;color:#64748B;margin-top:4px;">Total: <b style="color:#F8FAFC;">{fmt_int(_ejec_total)}</b> de <b>{fmt_int(_meta_total)}</b> altas (orgánicas + inducidas)</div>
            </div>
            <div style="width:1px;height:100px;background:rgba(255,255,255,0.08);flex-shrink:0;"></div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;flex:1;">
                <div>
                    <div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.3px;margin-bottom:2px;">{_lbl_nat}</div>
                    <div style="font-size:1.55rem;font-weight:900;color:{_sc(_val_nat)};">{_val_nat:.1f}%</div>
                    <div style="font-size:.70rem;color:#64748B;">{fmt_int(ejec_nat_total)} de {fmt_int(meta_nat_total)}</div>
                    {_bar(_val_nat, _sc(_val_nat))}
                </div>
                <div>
                    <div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.3px;margin-bottom:2px;">{_lbl_indu}</div>
                    <div style="font-size:1.55rem;font-weight:900;color:{_sc(_val_indu)};">{_val_indu:.1f}%</div>
                    <div style="font-size:.70rem;color:#64748B;">{fmt_int(ejec_indu_total)} de {fmt_int(meta_indu_total)}</div>
                    {_bar(_val_indu, _sc(_val_indu))}
                </div>
                <div>
                    <div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.3px;margin-bottom:2px;">PDVs bajo 70%</div>
                    <div style="font-size:1.55rem;font-weight:900;color:{_sc(100-_pct_bajo70)};">{fmt_int(_pdvs_bajo70)}</div>
                    <div style="font-size:.70rem;color:#64748B;">{_pct_bajo70:.0f}% del portafolio activo</div>
                    {_bar(100-_pct_bajo70, _sc(100-_pct_bajo70))}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Tarjetas de agente — dinámicas según corte ───────────────────────
        # Si _DIA_CORTE == _DIAS_MES: mes cerrado → mostrar cumplimiento real
        # Si _DIA_CORTE < _DIAS_MES: mes en curso → mostrar proyección al cierre
        _MES_CERRADO = (_DIA_CORTE >= _DIAS_MES)
        _FACTOR = 1.0 if _MES_CERRADO else _DIAS_MES / _DIA_CORTE

        _label_principal = "Resultado final del mes" if _MES_CERRADO else "Proyección al cierre del mes"
        st.markdown(f'<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:8px;">{_label_principal} por agente</div>', unsafe_allow_html=True)

        by_agente = df.groupby("AGENTE").agg(
            pdvs=("ID","count"),
            meta_nat=("META ALTA NAT (>$2000)","sum"),
            ejec_nat=("EJEC ALTA NAT","sum"),
            meta_indu=("META ALTA INDU (=< $2.000)","sum") if "META ALTA INDU (=< $2.000)" in df.columns else ("EJEC ALTA NAT","count"),
            ejec_indu=("EJEC ALTA INDU","sum") if "EJEC ALTA INDU" in df.columns else ("EJEC ALTA NAT","count"),
            ejec_total=("EJE ALTA TOTAL","sum"),
            cuota_alta=("CUOTA DE ALTA","mean"),
            var_alta=("VR_M-1.1","mean") if "VR_M-1.1" in df.columns else ("EJEC ALTA NAT","count"),
        ).reset_index()
        by_agente["meta_total"]  = by_agente["meta_nat"] + by_agente.get("meta_indu", 0)
        by_agente["cumpl_total"] = (by_agente["ejec_total"] / by_agente["meta_total"].replace(0,np.nan)*100).fillna(0)
        by_agente["cumpl_nat"]   = (by_agente["ejec_nat"]   / by_agente["meta_nat"].replace(0,np.nan)*100).fillna(0)
        by_agente["proy_total"]  = (by_agente["ejec_total"] * _FACTOR / by_agente["meta_total"].replace(0,np.nan)*100).fillna(0)
        by_agente["brecha"]      = by_agente["meta_total"] - by_agente["ejec_total"]
        # Valor que se usa como protagonista en la tarjeta
        by_agente["valor_principal"] = by_agente["cumpl_total"] if _MES_CERRADO else by_agente["proy_total"]
        _max_p = by_agente["valor_principal"].max()
        _min_p = by_agente["valor_principal"].min()

        n_ag = min(len(by_agente), 4)
        ag_cols = st.columns(n_ag, gap="small")
        for i, row in by_agente.sort_values("valor_principal", ascending=False).reset_index(drop=True).iterrows():
            ag_c  = AGENTE_COLORS.get(row["AGENTE"], AGENTE_COLORS.get(str(row["AGENTE"]).strip(), "#64748B"))
            p     = row["valor_principal"]; cp = _sc(p)
            badge = "🏆" if p == _max_p else ("⚠️" if p == _min_p else "")
            _var_a = row.get("var_alta", np.nan)
            _vt   = (f"{'↓' if pd.notna(_var_a) and _var_a < 0 else '↑'}{abs(_var_a):.1f}pp" if pd.notna(_var_a) and "VR_M-1.1" in df.columns else "")
            _vc   = "#EF4444" if pd.notna(_var_a) and _var_a < 0 else "#22C55E"
            _sub  = "cumplimiento total del mes" if _MES_CERRADO else f"proyección al día {_DIAS_MES}"
            # Segunda línea: si mes cerrado muestra cumpl orgánicas; si en curso muestra cumpl al corte
            _linea2_lbl = "Orgánicas:" if _MES_CERRADO else f"Al corte (d{_DIA_CORTE}):"
            _linea2_val = f"{row['cumpl_nat']:.1f}%"
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
                    <div style="font-size:.68rem;color:#64748B;margin-top:1px;">{_sub}</div>
                    {_bar(p, cp)}
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:8px;">
                        <div style="font-size:.70rem;color:#94A3B8;">{_linea2_lbl} <span style="color:#F8FAFC;font-weight:800;">{_linea2_val}</span></div>
                        <div style="font-size:.70rem;color:#94A3B8;">Brecha: <span style="color:#F8FAFC;font-weight:800;">{fmt_int(row["brecha"])}</span></div>
                        <div style="font-size:.70rem;color:#94A3B8;">Ejec. total: <span style="color:#F8FAFC;font-weight:800;">{fmt_int(row["ejec_total"])}</span></div>
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
        # Mes cerrado — no hay proyección, cumplimiento = resultado final
        cat_order = ["DIAMANTE","PLATINO","ORO","PLATA","BRONCE"]
        by_cat["CATEGORIA"] = pd.Categorical(by_cat["CATEGORIA"], categories=cat_order, ordered=True)
        by_cat = by_cat.sort_values("CATEGORIA")

        c1a, c1b = st.columns(2, gap="large")
        with c1a:
            st.markdown('<div class="section-card"><div class="section-title">Cumplimiento final por categoría</div><div class="section-subtitle">Resultado final del mes por categoría · línea verde = 100% de meta</div>', unsafe_allow_html=True)
            if not by_cat.empty:
                _mc = by_cat[["CATEGORIA","cumpl"]].copy()
                ch = alt.Chart(_mc).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                    x=alt.X("CATEGORIA:N",sort=cat_order,title=None),
                    y=alt.Y("cumpl:Q",title="Cumplimiento final (%)"),
                    color=alt.Color("CATEGORIA:N",scale=alt.Scale(domain=cat_order,range=[CATEGORIA_COLORS.get(c,"#64748B") for c in cat_order]),legend=None),
                    tooltip=[alt.Tooltip("CATEGORIA:N"),alt.Tooltip("cumpl:Q",format=".1f",title="Cumpl. %"),alt.Tooltip("pdvs:Q",title="PDVs")]
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
        by_ag_full["meta_total_ag"] = by_ag_full["meta_nat"] + by_ag_full.get("meta_indu",0)
        by_ag_full["proy_nat"]  = (by_ag_full["ejec_total"]/by_ag_full["meta_total_ag"].replace(0,np.nan)*100).fillna(0)
        by_ag_full["part_ejec"] = (by_ag_full["ejec_nat"]/by_ag_full["ejec_nat"].sum()*100).fillna(0)
        by_ag_full["brecha"]    = by_ag_full["meta_total_ag"] - by_ag_full["ejec_total"]

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
        by_ag_full["cumpl_indu"] = (by_ag_full["ejec_indu"]/by_ag_full["meta_indu"].replace(0,np.nan)*100).fillna(0)

        a2_l, a2_r = st.columns(2, gap="large")
        with a2_l:
            # Brecha waterfall — cuánto le falta a cada agente y de dónde viene
            by_ag_full["gap_pct"] = (100 - by_ag_full["cumpl_nat"]).clip(lower=0)
            st.markdown('<div class="section-card"><div class="section-title">Brecha real vs meta por agente</div><div class="section-subtitle">🔴 Altas ejecutadas · punto blanco = meta · número = altas que faltan para cerrar</div>', unsafe_allow_html=True)
            _base = alt.Chart(by_ag_full).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5,color="#E10600").encode(
                x=alt.X("AGENTE:N",title=None,axis=alt.Axis(labelAngle=-20)),
                y=alt.Y("ejec_nat:Q",title="Altas orgánicas"),
                tooltip=[alt.Tooltip("AGENTE:N"),alt.Tooltip("ejec_nat:Q",format=",.0f",title="Ejecutado"),alt.Tooltip("meta_nat:Q",format=",.0f",title="Meta"),alt.Tooltip("brecha:Q",format=",.0f",title="Faltan")]
            ).properties(height=280)
            _meta_rule = alt.Chart(by_ag_full).mark_tick(color="white",thickness=3,size=28).encode(
                x=alt.X("AGENTE:N"),
                y=alt.Y("meta_nat:Q"),
                tooltip=[alt.Tooltip("AGENTE:N"),alt.Tooltip("meta_nat:Q",format=",.0f",title="Meta")]
            )
            _brecha_txt = alt.Chart(by_ag_full).mark_text(dy=-14,fontSize=11,fontWeight="bold",color="#FCA5A5").encode(
                x=alt.X("AGENTE:N"),
                y=alt.Y("ejec_nat:Q"),
                text=alt.Text("brecha:Q",format=",.0f")
            )
            st.altair_chart(style_chart(_base+_meta_rule+_brecha_txt), use_container_width=True, theme=None)
            st.markdown('<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">Barra roja = ejecutado · guion blanco = meta · número en rojo encima = altas que aún faltan</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with a2_r:
            # Cumplimiento nat vs inducidas — dos frentes del plan
            _indu_melt = by_ag_full[["AGENTE","cumpl_nat","cumpl_indu"]].melt("AGENTE",var_name="Frente",value_name="Cumpl")
            _indu_melt["Frente"] = _indu_melt["Frente"].map({"cumpl_nat":"Orgánicas (>$2.000)","cumpl_indu":"Inducidas (≤$2.000)"})
            st.markdown('<div class="section-card"><div class="section-title">Cumplimiento: orgánicas vs inducidas</div><div class="section-subtitle">Cada agente tiene dos frentes. 🔴 Orgánicas = plan principal · 🔵 Inducidas = captación de bajo valor. La línea verde = 100%</div>', unsafe_allow_html=True)
            chart_dual2 = alt.Chart(_indu_melt).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                y=alt.Y("AGENTE:N",title=None,sort="-x"),
                x=alt.X("Cumpl:Q",title="Cumplimiento %"),
                color=alt.Color("Frente:N",scale=alt.Scale(domain=["Orgánicas (>$2.000)","Inducidas (≤$2.000)"],range=["#E10600","#38BDF8"]),legend=alt.Legend(title="",orient="bottom")),
                yOffset="Frente:N",
                tooltip=[alt.Tooltip("AGENTE:N"),alt.Tooltip("Frente:N"),alt.Tooltip("Cumpl:Q",format=".1f",title="Cumpl. %")]
            ).properties(height=280)
            r100_indu = alt.Chart(pd.DataFrame({"x":[100]})).mark_rule(color="#22C55E",strokeDash=[5,3],strokeWidth=1.5).encode(x="x:Q")
            st.altair_chart(style_chart(chart_dual2+r100_indu), use_container_width=True, theme=None)
            st.markdown('<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">Si la barra azul es muy corta, el frente inducido está siendo descuidado — oportunidad de captación de volumen.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Tabla resumen compacta ────────────────────────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:12px 0 6px 0;">Detalle completo por agente</div>', unsafe_allow_html=True)
        show_ag = safe_round_columns(by_ag_full[["AGENTE","pdvs","meta_nat","ejec_nat","cumpl_nat","proy_nat","brecha","cuota_alta"]].copy(),
            ["meta_nat","ejec_nat","cumpl_nat","proy_nat","brecha","cuota_alta"])
        show_ag.columns = ["Agente","PDVs","Meta","Ejecutado","Cumpl. %","Cumpl. total %","Brecha","Cuota Alta %"]
        st.dataframe(show_ag, use_container_width=True, height=240)


    # -------------------------------------------------------
    # TAB C3 — ¿DÓNDE ESTÁ LA BRECHA?
    # -------------------------------------------------------
    with tc3:
        # ── Cálculos protagonistas ────────────────────────────────────────────
        df_opp_c3 = df[df["META ALTA NAT (>$2000)"] > 0].copy()
        df_opp_c3["cumpl_pdv"] = (df_opp_c3["EJEC ALTA NAT"] / df_opp_c3["META ALTA NAT (>$2000)"] * 100).fillna(0)
        _n_pdvs_brecha   = int((df_opp_c3["cumpl_pdv"] < 70).sum())
        _n_pdvs_total_c3 = len(df_opp_c3)
        _pct_brecha_c3   = (_n_pdvs_brecha / _n_pdvs_total_c3 * 100) if _n_pdvs_total_c3 > 0 else 0
        _brecha_altas_c3 = int((df_opp_c3["META ALTA NAT (>$2000)"] - df_opp_c3["EJEC ALTA NAT"]).clip(lower=0).sum())
        _df_bajo70       = df_opp_c3[df_opp_c3["cumpl_pdv"] < 70]
        _agente_mas_brecha = (_df_bajo70.groupby("AGENTE").size().idxmax() if not _df_bajo70.empty else "N/D")
        _top_asesor_c3s  = df.groupby("ASESOR")["EJE ALTA TOTAL"].sum()
        _top_asesor_c3   = _top_asesor_c3s.idxmax() if not _top_asesor_c3s.empty else "N/D"
        _top_asesor_c3v  = int(_top_asesor_c3s.max()) if not _top_asesor_c3s.empty else 0

        def _sc3(v): return "#22C55E" if v >= 100 else "#F59E0B" if v >= 70 else "#EF4444"
        def _bar3(pct, color):
            w = min(max(pct, 0), 100)
            return f'<div style="width:100%;height:5px;background:rgba(255,255,255,0.07);border-radius:99px;margin-top:5px;overflow:hidden;"><div style="width:{w}%;height:100%;background:{color};border-radius:99px;"></div></div>'

        # ── 4 KPIs protagonistas ──────────────────────────────────────────────
        h1c3, h2c3, h3c3, h4c3 = st.columns(4, gap="medium")
        with h1c3:
            _cc = _sc3(100 - _pct_brecha_c3)
            st.markdown(f"""
            <div class="card" style="min-height:0;">
                <div class="kpi-label">PDVs con brecha activa</div>
                <div class="kpi-value" style="color:{_cc};">{fmt_int(_n_pdvs_brecha)}</div>
                <div class="kpi-sub">{_pct_brecha_c3:.0f}% del portafolio · cumplimiento &lt;70%</div>
                {_bar3(100-_pct_brecha_c3, _cc)}
            </div>""", unsafe_allow_html=True)
        with h2c3:
            st.markdown(f"""
            <div class="card" style="min-height:0;">
                <div class="kpi-label">Altas en juego</div>
                <div class="kpi-value" style="color:#F59E0B;">{fmt_int(_brecha_altas_c3)}</div>
                <div class="kpi-sub">Total de altas pendientes en PDVs con brecha</div>
            </div>""", unsafe_allow_html=True)
        with h3c3:
            st.markdown(f"""
            <div class="card" style="min-height:0;">
                <div class="kpi-label">Agente con más PDVs en riesgo</div>
                <div class="kpi-value" style="font-size:1.1rem;color:#EF4444;">{_agente_mas_brecha}</div>
                <div class="kpi-sub">Mayor concentración de PDVs &lt;70%</div>
            </div>""", unsafe_allow_html=True)
        with h4c3:
            st.markdown(f"""
            <div class="card" style="min-height:0;">
                <div class="kpi-label">Asesor líder</div>
                <div class="kpi-value" style="font-size:1.1rem;color:#22C55E;">{_top_asesor_c3}</div>
                <div class="kpi-sub">{fmt_int(_top_asesor_c3v)} altas totales vendidas</div>
            </div>""", unsafe_allow_html=True)

        # ── Sección 1: Top asesores + Top barrios ─────────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:16px 0 8px 0;">¿Quién vende más y dónde?</div>', unsafe_allow_html=True)
        c3a, c3b = st.columns(2, gap="large")

        by_asesor = df.groupby(["ASESOR","AGENTE"]).agg(
            pdvs=("ID","count"), meta_nat=("META ALTA NAT (>$2000)","sum"),
            ejec_nat=("EJEC ALTA NAT","sum"), ejec_total=("EJE ALTA TOTAL","sum"),
        ).reset_index()
        by_asesor["cumpl"] = (by_asesor["ejec_nat"]/by_asesor["meta_nat"].replace(0,np.nan)*100).fillna(0)
        by_asesor = by_asesor.sort_values("ejec_total", ascending=False).head(20)

        with c3a:
            st.markdown('<div class="section-card"><div class="section-title">Top 15 asesores por altas vendidas</div><div class="section-subtitle">Color = agente al que pertenece · barra = altas totales (orgánicas + inducidas)</div>', unsafe_allow_html=True)
            chart_asesor = alt.Chart(by_asesor.head(15)).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                x=alt.X("ejec_total:Q",title="Altas totales"),
                y=alt.Y("ASESOR:N",sort="-x",title=None,axis=alt.Axis(labelLimit=200)),
                color=alt.Color("AGENTE:N",scale=alt.Scale(domain=list(AGENTE_COLORS.keys()),range=list(AGENTE_COLORS.values())),legend=alt.Legend(title="Agente")),
                tooltip=[alt.Tooltip("ASESOR:N"),alt.Tooltip("AGENTE:N"),alt.Tooltip("ejec_total:Q",format=",.0f",title="Altas totales"),alt.Tooltip("ejec_nat:Q",format=",.0f",title="Altas orgánicas"),alt.Tooltip("cumpl:Q",format=".1f",title="Cumpl. %"),alt.Tooltip("pdvs:Q",title="PDVs")]
            ).properties(height=360)
            st.altair_chart(style_chart(chart_asesor), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with c3b:
            barrio_col_exists   = "BARRIO"   in df.columns
            circuito_col_exists = "CIRCUITO" in df.columns
            group_cols_circ = [c for c in ["BARRIO","CIRCUITO"] if c in df.columns] or ["AGENTE"]
            by_barrio = df.groupby(group_cols_circ).agg(
                pdvs=("ID","count"), meta_nat=("META ALTA NAT (>$2000)","sum"),
                ejec_nat=("EJEC ALTA NAT","sum"), ejec_total=("EJE ALTA TOTAL","sum"),
                cuota_alta=("CUOTA DE ALTA","mean"),
            ).reset_index()
            by_barrio["cumpl"] = (by_barrio["ejec_nat"]/by_barrio["meta_nat"].replace(0,np.nan)*100).fillna(0)

            if barrio_col_exists:
                by_barrio_top = by_barrio.groupby("BARRIO").agg(
                    ejec_total=("ejec_total","sum"), meta_nat=("meta_nat","sum"),
                    ejec_nat=("ejec_nat","sum"), pdvs=("pdvs","sum"), cuota_alta=("cuota_alta","mean"),
                ).reset_index()
                by_barrio_top["cumpl"] = (by_barrio_top["ejec_nat"]/by_barrio_top["meta_nat"].replace(0,np.nan)*100).fillna(0)
                if circuito_col_exists:
                    cpb = by_barrio.groupby("BARRIO")["CIRCUITO"].apply(lambda x: ", ".join(sorted(x.dropna().unique()))).reset_index()
                    cpb.columns = ["BARRIO","circuitos_lista"]
                    by_barrio_top = by_barrio_top.merge(cpb, on="BARRIO", how="left")
                else:
                    by_barrio_top["circuitos_lista"] = ""
                by_barrio_top = by_barrio_top.sort_values("ejec_total", ascending=False).head(15)
                y_col = "BARRIO"; tooltip_extra = [alt.Tooltip("circuitos_lista:N",title="Circuitos")]
            else:
                by_barrio_top = by_barrio.sort_values("ejec_total", ascending=False).head(15)
                y_col = "CIRCUITO"; tooltip_extra = []

            st.markdown('<div class="section-card"><div class="section-title">Top barrios por ejecución</div><div class="section-subtitle">🟢 ≥100% meta · 🟡 70–99% · 🔴 &lt;70% · pasa el mouse para ver circuitos</div>', unsafe_allow_html=True)
            chart_circ = alt.Chart(by_barrio_top).transform_calculate(
                color_semaforo="datum.cumpl >= 100 ? '#22C55E' : datum.cumpl >= 70 ? '#F59E0B' : '#EF4444'"
            ).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                x=alt.X("ejec_total:Q",title="Altas totales"),
                y=alt.Y(f"{y_col}:N",sort="-x",title=None,axis=alt.Axis(labelLimit=220)),
                color=alt.Color("color_semaforo:N",scale=None,legend=None),
                tooltip=[alt.Tooltip(f"{y_col}:N",title="Barrio" if y_col=="BARRIO" else "Circuito"),alt.Tooltip("pdvs:Q",title="PDVs"),alt.Tooltip("ejec_total:Q",format=",.0f",title="Ejec. total"),alt.Tooltip("cumpl:Q",format=".1f",title="Cumpl. %"),alt.Tooltip("cuota_alta:Q",format=".1f",title="Cuota alta %")]+tooltip_extra
            ).properties(height=360)
            st.altair_chart(style_chart(chart_circ), use_container_width=True, theme=None)
            if barrio_col_exists and circuito_col_exists and not by_barrio_top.empty:
                for _, row_b in by_barrio_top.head(6).iterrows():
                    circs = row_b.get("circuitos_lista","")
                    st.markdown(f'<div style="font-size:.72rem;color:#F8FAFC;margin-bottom:2px;"><b>{row_b["BARRIO"]}</b> <span style="color:#64748B;">— {circs}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Sección 5: Capacidad de mejora — asesores, barrios, cuota alta ───
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:20px 0 8px 0;">Capacidad de mejora — ¿dónde hay más potencial sin aprovechar?</div>', unsafe_allow_html=True)

        _DIA_C3=28; _MES_C3=30; _F_C3=_MES_C3/_DIA_C3

        # Asesores con menor cumplimiento (meta > umbral mínimo para que sea relevante)
        by_as_c3 = df.groupby(["ASESOR","AGENTE"]).agg(
            pdvs=("ID","count"), meta_nat=("META ALTA NAT (>$2000)","sum"),
            ejec_nat=("EJEC ALTA NAT","sum"), ejec_total=("EJE ALTA TOTAL","sum"),
            cuota_alta=("CUOTA DE ALTA","mean"),
        ).reset_index()
        by_as_c3["cumpl"]  = (by_as_c3["ejec_nat"]/by_as_c3["meta_nat"].replace(0,np.nan)*100).fillna(0)
        by_as_c3["brecha"] = by_as_c3["meta_nat"] - by_as_c3["ejec_nat"]
        by_as_c3["proy"]   = by_as_c3["cumpl"]  # mes cerrado — proyección = cumplimiento real
        # Umbral mínimo de meta para que sea relevante (median de meta para filtrar los muy pequeños)
        _meta_min_threshold = by_as_c3[by_as_c3["meta_nat"]>0]["meta_nat"].quantile(0.40)
        # Bottom performers = menor cumplimiento entre los que tienen meta significativa
        _bottom_as = (by_as_c3[by_as_c3["meta_nat"] >= _meta_min_threshold]
                      .sort_values("cumpl").head(15))

        # Barrios con mayor brecha
        by_bar_c3 = df.groupby("BARRIO").agg(
            pdvs=("ID","count"), meta_nat=("META ALTA NAT (>$2000)","sum"),
            ejec_nat=("EJEC ALTA NAT","sum"), cuota_alta=("CUOTA DE ALTA","mean"),
        ).reset_index()
        by_bar_c3["cumpl"]  = (by_bar_c3["ejec_nat"]/by_bar_c3["meta_nat"].replace(0,np.nan)*100).fillna(0)
        by_bar_c3["brecha"] = by_bar_c3["meta_nat"] - by_bar_c3["ejec_nat"]
        _bottom_bar = by_bar_c3[by_bar_c3["meta_nat"]>0].sort_values("brecha",ascending=False).head(20)

        # Barrios con menor cuota de alta (potencial competitivo)
        _baja_cuota_bar = by_bar_c3[by_bar_c3["pdvs"]>=5].sort_values("cuota_alta").head(20)

        cm1, cm2 = st.columns(2, gap="large")
        with cm1:
            st.markdown('<div class="section-card"><div class="section-title">Asesores con menor cumplimiento de meta</div><div class="section-subtitle">Los que más necesitan intervención — menor % de cumplimiento entre asesores con meta significativa · color = agente al que pertenecen</div>', unsafe_allow_html=True)
            chart_as_brecha = alt.Chart(_bottom_as).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                x=alt.X("cumpl:Q", title="Cumplimiento de meta (%)"),
                y=alt.Y("ASESOR:N", sort="x", title=None, axis=alt.Axis(labelLimit=200)),
                color=alt.Color("AGENTE:N",scale=alt.Scale(domain=list(AGENTE_COLORS.keys()),range=list(AGENTE_COLORS.values())),legend=alt.Legend(title="Agente")),
                tooltip=[
                    alt.Tooltip("ASESOR:N",       title="Asesor"),
                    alt.Tooltip("AGENTE:N",        title="Agente"),
                    alt.Tooltip("cumpl:Q",         format=".1f", title="Cumpl. %"),
                    alt.Tooltip("brecha:Q",        format=",.0f", title="Altas pendientes"),
                    alt.Tooltip("proy_nat:Q",       format=".1f", title="Cumpl. total %"),
                    alt.Tooltip("ejec_total:Q",    format=",.0f", title="Altas ejecutadas"),
                    alt.Tooltip("cuota_alta:Q",    format=".1f", title="Cuota alta %"),
                    alt.Tooltip("pdvs:Q",          title="PDVs"),
                ]
            ).properties(height=340)
            _rule_70 = alt.Chart(pd.DataFrame({"x":[70]})).mark_rule(color="#EF4444",strokeDash=[5,3],strokeWidth=1.5).encode(x="x:Q")
            st.altair_chart(style_chart(chart_as_brecha + _rule_70), use_container_width=True, theme=None)
            st.markdown('<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">Línea 🔴 = 70% de cumplimiento (umbral de alerta) · los asesores a la izquierda de la línea necesitan intervención inmediata</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with cm2:
            st.markdown('<div class="section-card"><div class="section-title">Barrios con mayor brecha de altas</div><div class="section-subtitle">Los barrios donde más altas se pierden vs la meta. No necesariamente los de menor cumplimiento — sino los de mayor volumen de oportunidad sin capturar.</div>', unsafe_allow_html=True)
            chart_bar_brecha = alt.Chart(_bottom_bar).transform_calculate(
                color_c="datum.cumpl >= 70 ? '#F59E0B' : '#EF4444'"
            ).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                x=alt.X("brecha:Q",title="Altas pendientes"),
                y=alt.Y("BARRIO:N",sort="-x",title=None,axis=alt.Axis(labelLimit=200)),
                color=alt.Color("color_c:N",scale=None,legend=None),
                tooltip=[
                    alt.Tooltip("BARRIO:N",title="Barrio"),
                    alt.Tooltip("pdvs:Q",title="PDVs"),
                    alt.Tooltip("brecha:Q",format=",.0f",title="Brecha altas"),
                    alt.Tooltip("cumpl:Q",format=".1f",title="Cumpl. %"),
                    alt.Tooltip("cuota_alta:Q",format=".1f",title="Cuota alta %"),
                ]
            ).properties(height=340)
            st.altair_chart(style_chart(chart_bar_brecha), use_container_width=True, theme=None)
            st.markdown('<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">🟡 Amarillo = cumpl 70-99% (recuperable) · 🔴 Rojo = &lt;70% (crítico)</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Barrios con menor cuota de alta — oportunidad competitiva
        st.markdown('<div class="section-card" style="margin-top:8px;"><div class="section-title">Barrios con menor cuota de altas Claro — mayor potencial competitivo</div><div class="section-subtitle">Barrios donde Claro tiene menor participación en ventas nuevas vs la competencia. Bajo porcentaje = mucho espacio para crecer sin necesidad de más PDVs · mínimo 5 PDVs por barrio</div>', unsafe_allow_html=True)
        chart_baja_cuota = alt.Chart(_baja_cuota_bar).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5,color="#38BDF8").encode(
            x=alt.X("cuota_alta:Q",title="Cuota de altas Claro (%)"),
            y=alt.Y("BARRIO:N",sort="x",title=None,axis=alt.Axis(labelLimit=220)),
            tooltip=[
                alt.Tooltip("BARRIO:N",title="Barrio"),
                alt.Tooltip("pdvs:Q",title="PDVs"),
                alt.Tooltip("cuota_alta:Q",format=".1f",title="Cuota alta %"),
                alt.Tooltip("cumpl:Q",format=".1f",title="Cumpl. meta %"),
                alt.Tooltip("brecha:Q",format=",.0f",title="Brecha altas"),
            ]
        ).properties(height=340)
        r50_bq = alt.Chart(pd.DataFrame({"x":[50]})).mark_rule(color="#22C55E",strokeDash=[5,3],strokeWidth=1.5).encode(x="x:Q")
        st.altair_chart(style_chart(chart_baja_cuota+r50_bq), use_container_width=True, theme=None)
        st.markdown('<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">Ordenado de menor a mayor cuota · línea verde = 50% (paridad con competencia) · barrios a la izquierda de la línea son los de mayor oportunidad</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------


        # ── Sección 2: Clasificación + Tipología ─────────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:16px 0 8px 0;">¿En qué tipo de PDV está la brecha?</div>', unsafe_allow_html=True)
        c3c, c3d = st.columns(2, gap="large")
        with c3c:
            by_clasif = df.groupby("CLASIFICACION").agg(
                pdvs=("ID","count"), ejec_nat=("EJEC ALTA NAT","sum"), meta_nat=("META ALTA NAT (>$2000)","sum"),
            ).reset_index().sort_values("ejec_nat", ascending=False).head(12)
            st.markdown('<div class="section-card"><div class="section-title">Altas por clasificación de PDV</div><div class="section-subtitle">Tiendas, cigarrerías, papelerías, etc. · ordenadas por volumen de altas</div>', unsafe_allow_html=True)
            if not by_clasif.empty:
                chart_cl = alt.Chart(by_clasif).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                    x=alt.X("ejec_nat:Q",title="Altas nat."),
                    y=alt.Y("CLASIFICACION:N",sort="-x",title=None,axis=alt.Axis(labelLimit=200)),
                    color=alt.value("#38BDF8"),
                    tooltip=[alt.Tooltip("CLASIFICACION:N"),alt.Tooltip("pdvs:Q",title="PDVs"),alt.Tooltip("ejec_nat:Q",format=",.0f")]
                ).properties(height=280)
                st.altair_chart(style_chart(chart_cl), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)
        with c3d:
            by_tipo = df.groupby("TIPOLOGIA").agg(
                pdvs=("ID","count"), ejec_nat=("EJEC ALTA NAT","sum"), meta_nat=("META ALTA NAT (>$2000)","sum"),
            ).reset_index()
            by_tipo["cumpl"] = (by_tipo["ejec_nat"]/by_tipo["meta_nat"].replace(0,np.nan)*100).fillna(0)
            st.markdown('<div class="section-card"><div class="section-title">Cumplimiento por tipología de PDV</div><div class="section-subtitle">A = mayor potencial · D = menor · color = semáforo de cumplimiento</div>', unsafe_allow_html=True)
            if not by_tipo.empty:
                chart_tip = alt.Chart(by_tipo).transform_calculate(
                    color_semaforo="datum.cumpl >= 100 ? '#22C55E' : datum.cumpl >= 70 ? '#F59E0B' : '#EF4444'"
                ).mark_bar(cornerRadiusTopLeft=6,cornerRadiusTopRight=6).encode(
                    x=alt.X("TIPOLOGIA:N",title=None),
                    y=alt.Y("ejec_nat:Q",title="Altas nat."),
                    color=alt.Color("color_semaforo:N",scale=None,legend=None),
                    tooltip=[alt.Tooltip("TIPOLOGIA:N"),alt.Tooltip("pdvs:Q",title="PDVs"),alt.Tooltip("ejec_nat:Q",format=",.0f"),alt.Tooltip("cumpl:Q",format=".1f",title="Cumpl. %")]
                ).properties(height=280)
                st.altair_chart(style_chart(chart_tip), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Sección 3: Rutas críticas ─────────────────────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:16px 0 8px 0;">Rutas que necesitan intervención inmediata</div>', unsafe_allow_html=True)
        if "RUTA" in df.columns:
            df_ruta_opp = df[df["META ALTA NAT (>$2000)"] > 0].copy()
            df_ruta_opp["cumpl_pdv"] = (df_ruta_opp["EJEC ALTA NAT"] / df_ruta_opp["META ALTA NAT (>$2000)"] * 100).fillna(0)
            ruta_group_cols = [c for c in ["RUTA","AGENTE","BARRIO"] if c in df_ruta_opp.columns]
            ruta_opp = df_ruta_opp.groupby(ruta_group_cols).agg(
                pdvs_totales=("ID","count"), pdvs_criticos=("cumpl_pdv", lambda x: (x < 70).sum()),
                meta_total=("META ALTA NAT (>$2000)","sum"), ejec_total=("EJEC ALTA NAT","sum"),
            ).reset_index()
            ruta_opp["cumpl_ruta"]        = (ruta_opp["ejec_total"]/ruta_opp["meta_total"].replace(0,np.nan)*100).fillna(0)
            ruta_opp["brecha"]            = ruta_opp["meta_total"] - ruta_opp["ejec_total"]
            ruta_opp["pct_pdvs_criticos"] = (ruta_opp["pdvs_criticos"]/ruta_opp["pdvs_totales"].replace(0,np.nan)*100).fillna(0)
            ruta_opp = ruta_opp[ruta_opp["cumpl_ruta"] < 70].sort_values("brecha", ascending=False).head(20)
            if not ruta_opp.empty:
                ruta_rename = {"RUTA":"Ruta","AGENTE":"Agente","BARRIO":"Barrio","pdvs_totales":"PDVs","pdvs_criticos":"PDVs críticos","meta_total":"Meta","ejec_total":"Ejecutado","cumpl_ruta":"Cumpl. %","brecha":"Brecha","pct_pdvs_criticos":"% críticos"}
                show_ruta_cols = [c for c in ruta_rename.keys() if c in ruta_opp.columns]
                show_ruta = safe_round_columns(ruta_opp[show_ruta_cols].copy(), ["meta_total","ejec_total","cumpl_ruta","brecha","pct_pdvs_criticos"])
                show_ruta = show_ruta.rename(columns={k:v for k,v in ruta_rename.items() if k in show_ruta.columns})
                st.dataframe(show_ruta, use_container_width=True, height=280)
                st.markdown(f'<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">{len(ruta_opp)} rutas con cumplimiento &lt;70% · ordenadas por mayor brecha</div>', unsafe_allow_html=True)
            else:
                st.success("✅ No hay rutas con cumplimiento por debajo del 70%.")
        else:
            st.info("No se encontró la columna RUTA en los datos.")

        # ── Sección 4: PDVs individuales ──────────────────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:16px 0 8px 0;">Los 30 PDVs con mayor meta y menor cumplimiento</div>', unsafe_allow_html=True)
        df_opp2 = df[df["META ALTA NAT (>$2000)"] > 0].copy()
        df_opp2["cumpl_pdv"] = (df_opp2["EJEC ALTA NAT"] / df_opp2["META ALTA NAT (>$2000)"] * 100).fillna(0)
        df_opp_show2 = df_opp2[df_opp2["cumpl_pdv"] < 70].sort_values("META ALTA NAT (>$2000)", ascending=False).head(30)
        if not df_opp_show2.empty:
            extra_cols2 = [c for c in ["BARRIO","ZONA","RUTA"] if c in df_opp_show2.columns]
            cols_show2 = [c for c in ["ID","AGENTE","ASESOR","CIRCUITO"]+extra_cols2+["CLASIFICACION","CATEGORIA","META ALTA NAT (>$2000)","EJEC ALTA NAT","cumpl_pdv"] if c in df_opp_show2.columns]
            show_opp2 = df_opp_show2[cols_show2].copy()
            show_opp2 = safe_round_columns(show_opp2, ["META ALTA NAT (>$2000)","EJEC ALTA NAT","cumpl_pdv"])
            rename_opp2 = {"META ALTA NAT (>$2000)":"Meta","EJEC ALTA NAT":"Ejecutado","cumpl_pdv":"Cumpl. %","ID":"ID PDV","AGENTE":"Agente","ASESOR":"Asesor","CIRCUITO":"Circuito","CLASIFICACION":"Clasificación","CATEGORIA":"Categoría","BARRIO":"Barrio","ZONA":"Zona","RUTA":"Ruta"}
            show_opp2 = show_opp2.rename(columns={k:v for k,v in rename_opp2.items() if k in show_opp2.columns})
            st.dataframe(show_opp2, use_container_width=True, height=300)
            st.markdown(f'<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">{len(df_opp_show2)} PDVs · ordenados por mayor meta · usa filtros del sidebar para enfocar</div>', unsafe_allow_html=True)
        else:
            st.success("✅ No hay PDVs con cumplimiento por debajo del 70%.")


    # -------------------------------------------------------
    # TAB C4 — ¿SUBE EL RITMO?
    # -------------------------------------------------------
    with tc4:
        semanas      = ["S1","S2","S3","S4"]
        semanas_indu = ["S1.1","S2.1","S3.1","S4.1"]
        s_totals      = {s: float(df[s].sum()) if s in df.columns else 0.0 for s in semanas}
        s_indu_totals = {s: float(df[s].sum()) if s in df.columns else 0.0 for s in semanas_indu}
        _s_list       = [s_totals["S1"],s_totals["S2"],s_totals["S3"],s_totals["S4"]]
        _mejor_s      = max(semanas, key=lambda s: s_totals[s])
        _peor_s       = min(semanas, key=lambda s: s_totals[s])
        _tendencia_c4 = _s_list[2] >= _s_list[1] >= _s_list[0]
        _var_s2s1     = ((s_totals["S2"]-s_totals["S1"])/s_totals["S1"]*100) if s_totals["S1"]>0 else 0
        _var_s3s2     = ((s_totals["S3"]-s_totals["S2"])/s_totals["S2"]*100) if s_totals["S2"]>0 else 0
        _var_s4s3     = ((s_totals["S4"]-s_totals["S3"])/s_totals["S3"]*100) if s_totals["S3"]>0 else 0

        def _sc4(v): return "#22C55E" if v >= 0 else "#EF4444"
        def _arrow(v): return "↑" if v >= 0 else "↓"

        # ── Headline: semana a semana ─────────────────────────────────────────
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.96),rgba(10,18,34,0.98));border:1px solid rgba(255,255,255,0.10);border-radius:24px;padding:20px 28px;margin-bottom:16px;">
            <div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:14px;">Evolución semanal · 1–27 Abril 2026</div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;">
                <div style="text-align:center;padding:0 12px;border-right:1px solid rgba(255,255,255,0.07);">
                    <div style="font-size:.68rem;font-weight:900;color:#94A3B8;margin-bottom:4px;">SEMANA 1</div>
                    <div style="font-size:2rem;font-weight:950;color:#F8FAFC;">{fmt_int(s_totals["S1"])}</div>
                    <div style="font-size:.72rem;color:#64748B;margin-top:2px;">altas</div>
                </div>
                <div style="text-align:center;padding:0 12px;border-right:1px solid rgba(255,255,255,0.07);">
                    <div style="font-size:.68rem;font-weight:900;color:#94A3B8;margin-bottom:4px;">SEMANA 2</div>
                    <div style="font-size:2rem;font-weight:950;color:#F8FAFC;">{fmt_int(s_totals["S2"])}</div>
                    <div style="font-size:.72rem;color:{_sc4(_var_s2s1)};margin-top:2px;">{_arrow(_var_s2s1)} {abs(_var_s2s1):.0f}% vs S1</div>
                </div>
                <div style="text-align:center;padding:0 12px;border-right:1px solid rgba(255,255,255,0.07);">
                    <div style="font-size:.68rem;font-weight:900;color:#94A3B8;margin-bottom:4px;">SEMANA 3</div>
                    <div style="font-size:2rem;font-weight:950;color:#F8FAFC;">{fmt_int(s_totals["S3"])}</div>
                    <div style="font-size:.72rem;color:{_sc4(_var_s3s2)};margin-top:2px;">{_arrow(_var_s3s2)} {abs(_var_s3s2):.0f}% vs S2</div>
                </div>
                <div style="text-align:center;padding:0 12px;">
                    <div style="font-size:.68rem;font-weight:900;color:#94A3B8;margin-bottom:4px;">SEMANA 4</div>
                    <div style="font-size:2rem;font-weight:950;color:#F8FAFC;">{fmt_int(s_totals["S4"])}</div>
                    <div style="font-size:.72rem;color:{_sc4(_var_s4s3)};margin-top:2px;">{_arrow(_var_s4s3)} {abs(_var_s4s3):.0f}% vs S3</div>
                </div>
            </div>
            <div style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:10px;">
                <span style="font-size:.82rem;font-weight:800;color:{"#22C55E" if _tendencia_c4 else "#EF4444"};"> {"▲ Tendencia positiva — el ritmo crece semana a semana" if _tendencia_c4 else f"▼ Tendencia a la baja — {_mejor_s} fue el pico, {_peor_s} el punto más bajo"}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Gráficas ──────────────────────────────────────────────────────────
        c4a, c4b = st.columns(2, gap="large")
        df_semana = pd.DataFrame({"Semana": semanas, "Total": [s_totals[s] for s in semanas]})

        with c4a:
            st.markdown('<div class="section-card"><div class="section-title">Curva de ejecución semanal</div><div class="section-subtitle">↑ subida = aceleración · ↓ bajada = desaceleración · área rellena = volumen acumulado</div>', unsafe_allow_html=True)
            chart_sem = alt.Chart(df_semana).mark_line(point=True,strokeWidth=3,color="#E10600").encode(
                x=alt.X("Semana:N",title=None,sort=semanas),
                y=alt.Y("Total:Q",title="Altas"),
                tooltip=[alt.Tooltip("Semana:N"),alt.Tooltip("Total:Q",format=",.0f")]
            ).properties(height=260)
            area_sem = alt.Chart(df_semana).mark_area(opacity=0.12,color="#E10600").encode(
                x=alt.X("Semana:N",sort=semanas), y=alt.Y("Total:Q")
            )
            st.altair_chart(style_chart(area_sem+chart_sem), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with c4b:
            sem_by_ag = []
            for s in semanas:
                if s in df.columns:
                    grp = df.groupby("AGENTE")[s].sum().reset_index()
                    grp["Semana"] = s; grp = grp.rename(columns={s:"Altas"})
                    sem_by_ag.append(grp)
            df_sem_ag = pd.concat(sem_by_ag, ignore_index=True) if sem_by_ag else pd.DataFrame()
            st.markdown('<div class="section-card"><div class="section-title">Ritmo semanal por agente</div><div class="section-subtitle">Cada línea = un agente · línea que sube = aceleró · línea que baja = perdió ritmo</div>', unsafe_allow_html=True)
            if not df_sem_ag.empty:
                chart_sem_ag = alt.Chart(df_sem_ag).mark_line(point=True,strokeWidth=2).encode(
                    x=alt.X("Semana:N",sort=semanas,title=None),
                    y=alt.Y("Altas:Q",title="Altas orgánicas"),
                    color=alt.Color("AGENTE:N",scale=alt.Scale(domain=list(AGENTE_COLORS.keys()),range=list(AGENTE_COLORS.values())),legend=alt.Legend(title="Agente")),
                    tooltip=[alt.Tooltip("Semana:N"),alt.Tooltip("AGENTE:N"),alt.Tooltip("Altas:Q",format=",.0f")]
                ).properties(height=260)
                st.altair_chart(style_chart(chart_sem_ag), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Orgánicas vs Inducidas ────────────────────────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:16px 0 8px 0;">Orgánicas vs inducidas — composición semanal</div>', unsafe_allow_html=True)
        df_sem_indu = pd.DataFrame({
            "Semana": ["S1","S2","S3","S4"],
            "Inducidas": [s_indu_totals[s] for s in semanas_indu],
            "Orgánicas": [s_totals[s2] for s2 in semanas],
        })
        df_sem_indu["Acum_org"]  = df_sem_indu["Orgánicas"].cumsum()
        df_sem_indu["Acum_indu"] = df_sem_indu["Inducidas"].cumsum()
        df_sem_indu_long = df_sem_indu.melt("Semana", var_name="Tipo", value_name="Altas",
                                             value_vars=["Orgánicas","Inducidas"])
        df_acum = df_sem_indu[["Semana","Acum_org","Acum_indu"]].melt("Semana",var_name="Tipo",value_name="Acumulado")
        df_acum["Tipo"] = df_acum["Tipo"].map({"Acum_org":"Orgánicas","Acum_indu":"Inducidas"})

        c4c, c4d = st.columns(2, gap="large")
        with c4c:
            st.markdown('<div class="section-card"><div class="section-title">Orgánicas vs inducidas por semana</div><div class="section-subtitle">🔴 Orgánicas = planes &gt;$2.000 (mayor valor) · 🔵 Inducidas = planes ≤$2.000</div>', unsafe_allow_html=True)
            chart_comp = alt.Chart(df_sem_indu_long).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                x=alt.X("Semana:N",sort=["S1","S2","S3","S4"],title=None),
                y=alt.Y("Altas:Q",title="Altas"),
                color=alt.Color("Tipo:N",scale=alt.Scale(domain=["Orgánicas","Inducidas"],range=["#E10600","#38BDF8"]),legend=alt.Legend(title="")),
                xOffset="Tipo:N",
                tooltip=[alt.Tooltip("Semana:N"),alt.Tooltip("Tipo:N"),alt.Tooltip("Altas:Q",format=",.0f")]
            ).properties(height=240)
            st.altair_chart(style_chart(chart_comp), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)
        with c4d:
            st.markdown('<div class="section-card"><div class="section-title">Avance acumulado</div><div class="section-subtitle">Si la línea 🔴 crece más rápido que la 🔵, la captación de calidad va bien</div>', unsafe_allow_html=True)
            chart_acum = alt.Chart(df_acum).mark_line(point=True,strokeWidth=3).encode(
                x=alt.X("Semana:N",sort=["S1","S2","S3","S4"],title=None),
                y=alt.Y("Acumulado:Q",title="Altas acumuladas"),
                color=alt.Color("Tipo:N",scale=alt.Scale(domain=["Orgánicas","Inducidas"],range=["#E10600","#38BDF8"]),legend=alt.Legend(title="")),
                tooltip=[alt.Tooltip("Semana:N"),alt.Tooltip("Tipo:N"),alt.Tooltip("Acumulado:Q",format=",.0f")]
            ).properties(height=240)
            st.altair_chart(style_chart(chart_acum), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)


    # -------------------------------------------------------
    # TAB C5 — ¿DÓNDE GANAR MÁS?
    # -------------------------------------------------------
    with tc5:
        # ── Cálculos globales ─────────────────────────────────────────────────
        _cuota_alta_50    = (pd.to_numeric(df["CUOTA DE ALTA"],errors="coerce")>50).sum()
        _cuota_alta_50_pct= (_cuota_alta_50/len(df)*100) if len(df)>0 else 0
        _var_alta_m1      = pd.to_numeric(df["VR_M-1.1"],errors="coerce").mean() if "VR_M-1.1" in df.columns else np.nan
        def _vc5(v): return "#EF4444" if pd.notna(v) and v<0 else "#22C55E"
        def _sc5(v): return "#22C55E" if v>=50 else "#F59E0B" if v>=40 else "#EF4444"

        # ── BLOQUE 1: ¿Cómo está Claro en el mercado? — 4 KPIs ───────────────
        # KPIs con valores reales y conclusión clara
        _pdvs_cuota_baja  = int((pd.to_numeric(df["CUOTA DE ALTA"],errors="coerce")<30).sum())
        _pct_cuota_baja   = (_pdvs_cuota_baja/len(df)*100) if len(df)>0 else 0
        _pdvs_cuota_dom   = int((pd.to_numeric(df["CUOTA DE ALTA"],errors="coerce")>=60).sum())
        _pct_cuota_dom    = (_pdvs_cuota_dom/len(df)*100) if len(df)>0 else 0
        _rsrp_criticos_n  = int((pd.to_numeric(df["RSRP"],errors="coerce")<-100).sum())
        _pct_rsrp_crit    = (_rsrp_criticos_n/len(df)*100) if len(df)>0 else 0

        k5a,k5b,k5c,k5d = st.columns(4,gap="medium")
        with k5a:
            _c_alta5 = "#22C55E" if cuota_alta_media>=50 else "#F59E0B" if cuota_alta_media>=40 else "#EF4444"
            _vt_a5   = (f'{"↓" if pd.notna(_var_alta_m1) and _var_alta_m1<0 else "↑"}{abs(_var_alta_m1):.1f}pp vs mes ant.'
                        if pd.notna(_var_alta_m1) else "")
            _vcolor5 = "#EF4444" if pd.notna(_var_alta_m1) and _var_alta_m1<0 else "#22C55E"
            _concl_alta = ("✅ Claro domina la captación" if cuota_alta_media>=50
                           else "🟡 La competencia capta más en promedio")
            st.markdown(f"""
            <div class="card" style="min-height:0;">
                <div class="kpi-label">Cuota de altas media</div>
                <div class="kpi-value" style="color:{_c_alta5};">{fmt_pct_c(cuota_alta_media)}</div>
                <div class="kpi-sub">{_concl_alta}<br><span style="color:{_vcolor5};">{_vt_a5}</span></div>
            </div>""", unsafe_allow_html=True)
        with k5b:
            _c_mkt5  = "#22C55E" if cuota_mkt_media>=60 else "#F59E0B" if cuota_mkt_media>=50 else "#EF4444"
            _concl_mkt = ("✅ Base instalada sólida" if cuota_mkt_media>=60
                          else "🟡 Liderazgo estrecho en mercado" if cuota_mkt_media>=50
                          else "🔴 Competencia domina la base")
            st.markdown(f"""
            <div class="card" style="min-height:0;">
                <div class="kpi-label">Cuota de mercado media</div>
                <div class="kpi-value" style="color:{_c_mkt5};">{fmt_pct_c(cuota_mkt_media)}</div>
                <div class="kpi-sub">{_concl_mkt} · {fmt_int(_pdvs_cuota_dom)} PDVs con cuota &gt;60%</div>
            </div>""", unsafe_allow_html=True)
        with k5c:
            _c_baja5 = "#EF4444" if _pct_cuota_baja>40 else "#F59E0B" if _pct_cuota_baja>20 else "#22C55E"
            _concl_baja = (f"🔴 {_pct_cuota_baja:.0f}% del portafolio con cuota &lt;30% — alta oportunidad"
                           if _pct_cuota_baja>20 else f"✅ Pocos PDVs con cuota baja")
            st.markdown(f"""
            <div class="card" style="min-height:0;">
                <div class="kpi-label">PDVs con cuota de altas &lt;30%</div>
                <div class="kpi-value" style="color:{_c_baja5};">{fmt_int(_pdvs_cuota_baja)}</div>
                <div class="kpi-sub">{_concl_baja}</div>
            </div>""", unsafe_allow_html=True)
        with k5d:
            _c_rsrp5 = "#EF4444" if _pct_rsrp_crit>10 else "#F59E0B"
            st.markdown(f"""
            <div class="card" style="min-height:0;">
                <div class="kpi-label">PDVs con señal crítica</div>
                <div class="kpi-value" style="color:{_c_rsrp5};">{fmt_int(_rsrp_criticos_n)}</div>
                <div class="kpi-sub">{_pct_rsrp_crit:.1f}% del portafolio bajo -100 dBm · afecta captación</div>
            </div>""", unsafe_allow_html=True)

        # ── BLOQUE 2: ¿Qué posición tiene cada agente? ───────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:18px 0 8px 0;">Posición competitiva por agente</div>', unsafe_allow_html=True)
        cuota_by_ag = df.groupby("AGENTE").agg(
            cuota_mkt=("CUOTA DE MERCADO","mean"), cuota_alta=("CUOTA DE ALTA","mean"), n=("ID","count"),
        ).reset_index()
        b2a, b2b = st.columns(2, gap="large")
        with b2a:
            st.markdown('<div class="section-card"><div class="section-title">Cuota de altas vs cuota de mercado por agente</div><div class="section-subtitle">🔵 Cuota altas = ventas nuevas que son Claro · 🔴 Cuota mercado = base instalada · si azul supera al rojo, el agente gana participación activamente</div>', unsafe_allow_html=True)
            cuota_melt = cuota_by_ag[["AGENTE","cuota_mkt","cuota_alta"]].melt("AGENTE",var_name="Indicador",value_name="Valor")
            cuota_melt["Indicador"] = cuota_melt["Indicador"].map({"cuota_mkt":"Cuota Mercado","cuota_alta":"Cuota Altas"})
            chart_cuota = alt.Chart(cuota_melt).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                x=alt.X("AGENTE:N",title=None,axis=alt.Axis(labelAngle=-20)),
                y=alt.Y("Valor:Q",title="Cuota (%)"),
                color=alt.Color("Indicador:N",scale=alt.Scale(domain=["Cuota Mercado","Cuota Altas"],range=["#E10600","#38BDF8"]),legend=alt.Legend(title="")),
                xOffset="Indicador:N",
                tooltip=[alt.Tooltip("AGENTE:N"),alt.Tooltip("Indicador:N"),alt.Tooltip("Valor:Q",format=".1f",title="Cuota %")]
            ).properties(height=280)
            st.altair_chart(style_chart(chart_cuota), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)
        with b2b:
            cuota_vals = pd.to_numeric(df["CUOTA DE MERCADO"],errors="coerce").dropna()
            df_hist = pd.DataFrame({"Cuota": cuota_vals})
            st.markdown('<div class="section-card"><div class="section-title">¿Cómo se distribuye la cuota de mercado Claro?</div><div class="section-subtitle">Cada barra = cuántos PDVs tienen ese % de cuota · masa a la derecha = Claro domina en esos puntos · masa a la izquierda = oportunidad de crecimiento</div>', unsafe_allow_html=True)
            if not df_hist.empty:
                chart_hist = alt.Chart(df_hist).mark_bar(color="#E10600",opacity=0.82).encode(
                    x=alt.X("Cuota:Q",bin=alt.Bin(maxbins=20),title="Cuota mercado Claro (%)"),
                    y=alt.Y("count():Q",title="PDVs"),
                    tooltip=[alt.Tooltip("Cuota:Q",bin=True),alt.Tooltip("count():Q",title="PDVs")]
                ).properties(height=280)
                st.altair_chart(style_chart(chart_hist), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── BLOQUE 3: ¿Cómo es la señal de cada agente? ──────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:18px 0 8px 0;">Calidad de señal RSRP por agente</div>', unsafe_allow_html=True)

        _df_rsrp = df.copy()
        _df_rsrp["RSRP_n"]      = pd.to_numeric(_df_rsrp["RSRP"],errors="coerce")
        _df_rsrp["CUOTA_ALTA_n"]= pd.to_numeric(_df_rsrp["CUOTA DE ALTA"],errors="coerce")
        def _rband(v):
            if pd.isna(v): return "Sin datos"
            if v>=-70: return "Excelente"
            if v>=-90: return "Buena"
            if v>=-100: return "Aceptable"
            return "Crítica"
        _df_rsrp["banda"] = _df_rsrp["RSRP_n"].apply(_rband)

        _rsrp_ag = _df_rsrp.groupby("AGENTE").agg(
            rsrp_medio=("RSRP_n","mean"), rsrp_min=("RSRP_n","min"), rsrp_max=("RSRP_n","max"),
            pdvs_total=("RSRP_n","count"),
            criticos=("banda", lambda x: (x=="Crítica").sum()),
            aceptables=("banda", lambda x: (x=="Aceptable").sum()),
            buenos=("banda", lambda x: (x=="Buena").sum()),
            excelentes=("banda", lambda x: (x=="Excelente").sum()),
            cuota_alta=("CUOTA_ALTA_n","mean"),
        ).reset_index()
        _rsrp_ag["pct_criticos"]  = (_rsrp_ag["criticos"]/_rsrp_ag["pdvs_total"].replace(0,np.nan)*100).fillna(0)
        _rsrp_ag["pct_aceptable"] = (_rsrp_ag["aceptables"]/_rsrp_ag["pdvs_total"].replace(0,np.nan)*100).fillna(0)
        _rsrp_ag["color_rsrp"]    = _rsrp_ag["rsrp_medio"].apply(
            lambda v: "#22C55E" if pd.notna(v) and v>=-90 else "#F59E0B" if pd.notna(v) and v>=-100 else "#EF4444"
        )

        b3a, b3b = st.columns(2, gap="large")
        with b3a:
            _rsrp_plot = _rsrp_ag[["AGENTE","rsrp_medio","pct_criticos","pdvs_total","rsrp_min","rsrp_max"]].copy()
            _rsrp_plot = _rsrp_plot.sort_values("rsrp_medio", ascending=False).reset_index(drop=True)
            # Build pure HTML bar chart — no Altair dependency
            _rsrp_abs_min = float(_rsrp_plot["rsrp_medio"].abs().min())
            _rsrp_abs_max = float(_rsrp_plot["rsrp_medio"].abs().max())
            _rsrp_range   = max(_rsrp_abs_max - _rsrp_abs_min, 1)

            rows_html = ""
            for _, rr in _rsrp_plot.iterrows():
                _v      = float(rr["rsrp_medio"])
                _abs_v  = abs(_v)
                _bar_w  = int((_abs_v - _rsrp_abs_min) / _rsrp_range * 100)  # 0-100%
                _color  = "#EF4444" if _v < -100 else "#F59E0B" if _v < -90 else "#22C55E"
                _band   = "Crítica" if _v < -100 else "Aceptable" if _v < -90 else "Buena"
                _crit_p = float(rr["pct_criticos"])
                _pdvs   = int(rr["pdvs_total"])
                rows_html += f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                        <span style="font-size:.78rem;font-weight:800;color:#E2E8F0;">{rr["AGENTE"]}</span>
                        <span style="font-size:.78rem;font-weight:900;color:{_color};">{_v:.1f} dBm &nbsp;
                            <span style="font-size:.66rem;background:{_color}22;border:1px solid {_color}44;border-radius:6px;padding:1px 6px;color:{_color};">{_band}</span>
                        </span>
                    </div>
                    <div style="width:100%;height:10px;background:rgba(255,255,255,0.07);border-radius:99px;overflow:hidden;">
                        <div style="width:{_bar_w}%;height:100%;background:{_color};border-radius:99px;"></div>
                    </div>
                    <div style="font-size:.67rem;color:#64748B;margin-top:2px;">{_pdvs:,} PDVs medidos · {_crit_p:.1f}% en señal crítica</div>
                </div>"""

            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">RSRP medio por agente</div>
                <div class="section-subtitle">Barra más larga = peor señal · 🟡 Aceptable (-90 a -100 dBm) · 🔴 Crítica (&lt;-100 dBm)</div>
                <div style="margin-top:12px;">{rows_html}</div>
                <div style="font-size:.68rem;color:#64748B;margin-top:8px;border-top:1px solid rgba(255,255,255,0.06);padding-top:6px;">
                    La barra representa la posición relativa entre agentes — no el valor absoluto.
                    El número a la derecha es el RSRP real en dBm.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with b3b:
            _band_long_ag = _rsrp_ag[["AGENTE","criticos","aceptables","buenos","excelentes","pdvs_total"]].copy()
            for col,lbl in [("criticos","Crítica"),("aceptables","Aceptable"),("buenos","Buena"),("excelentes","Excelente")]:
                _band_long_ag[lbl] = (_band_long_ag[col]/_band_long_ag["pdvs_total"].replace(0,np.nan)*100).fillna(0)
            _band_melt = _band_long_ag[["AGENTE","Crítica","Aceptable","Buena","Excelente"]].melt("AGENTE",var_name="Banda",value_name="Pct")
            st.markdown('<div class="section-card"><div class="section-title">Composición de señal por agente</div><div class="section-subtitle">Qué porcentaje del portafolio de cada agente está en cada banda de señal · más rojo = más PDVs en zona crítica</div>', unsafe_allow_html=True)
            _ch_dist = alt.Chart(_band_melt).mark_bar().encode(
                x=alt.X("Pct:Q",title="% del portafolio",stack="normalize",axis=alt.Axis(format="%")),
                y=alt.Y("AGENTE:N",title=None),
                color=alt.Color("Banda:N",
                    scale=alt.Scale(domain=["Excelente","Buena","Aceptable","Crítica"],
                                    range=["#22C55E","#84CC16","#F59E0B","#EF4444"]),
                    legend=alt.Legend(title="",orient="bottom")),
                order=alt.Order("Banda:N",sort="descending"),
                tooltip=[alt.Tooltip("AGENTE:N"),alt.Tooltip("Banda:N"),alt.Tooltip("Pct:Q",format=".1f",title="%")]
            ).properties(height=280)
            st.altair_chart(style_chart(_ch_dist), use_container_width=True, theme=None)
            st.markdown('<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">El agente con mayor porción roja tiene más PDVs en señal crítica — afecta directamente la cuota de altas</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── BLOQUE 4: ¿La señal afecta la captación? ─────────────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:18px 0 8px 0;">¿La señal afecta la captación de altas?</div>', unsafe_allow_html=True)
        b4a, b4b = st.columns(2, gap="large")

        with b4a:
            # Señal crítica por agente + cuota de altas superpuesta (doble eje)
            st.markdown('<div class="section-card"><div class="section-title">PDVs con señal crítica vs cuota de altas por agente</div><div class="section-subtitle">Barra = % PDVs con señal crítica · línea azul = cuota de altas · si barra alta y línea baja, la señal está frenando la captación</div>', unsafe_allow_html=True)
            _ch_crit = alt.Chart(_rsrp_ag).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                x=alt.X("AGENTE:N",title=None,axis=alt.Axis(labelAngle=-20)),
                y=alt.Y("pct_criticos:Q",title="% PDVs señal crítica"),
                color=alt.Color("AGENTE:N",scale=alt.Scale(domain=list(AGENTE_COLORS.keys()),range=list(AGENTE_COLORS.values())),legend=None),
                tooltip=[alt.Tooltip("AGENTE:N"),alt.Tooltip("pct_criticos:Q",format=".1f",title="% críticos"),alt.Tooltip("pct_aceptable:Q",format=".1f",title="% aceptable"),alt.Tooltip("cuota_alta:Q",format=".1f",title="Cuota alta %")]
            )
            _ch_cuota_line = alt.Chart(_rsrp_ag).mark_line(point=True,strokeWidth=2.5,color="#38BDF8").encode(
                x=alt.X("AGENTE:N",axis=alt.Axis(labelAngle=-20)),
                y=alt.Y("cuota_alta:Q",title="Cuota altas %",axis=alt.Axis(titleColor="#38BDF8")),
                tooltip=[alt.Tooltip("AGENTE:N"),alt.Tooltip("cuota_alta:Q",format=".1f",title="Cuota alta %")]
            )
            _dual_c = alt.layer(_ch_crit,_ch_cuota_line).resolve_scale(y="independent").properties(height=280)
            st.altair_chart(style_chart(_dual_c), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with b4b:
            # Señal por banda vs cuota de altas (las bandas reales del portafolio)
            df_sc5 = df[["CUOTA DE ALTA","CUOTA DE MERCADO","RSRP","AGENTE","CATEGORIA","ID"]].copy()
            df_sc5["RSRP_n"]    = pd.to_numeric(df_sc5["RSRP"],errors="coerce")
            df_sc5["CUOTA_A"]   = pd.to_numeric(df_sc5["CUOTA DE ALTA"],errors="coerce")
            df_sc5 = df_sc5.dropna(subset=["RSRP_n","CUOTA_A"]).copy()
            def rsrp_band_v2(v):
                if v>=-70:  return "Excelente (≥-70)"
                if v>=-90:  return "Buena (-70 a -90)"
                if v>=-100: return "Aceptable (-90 a -100)"
                return "Crítica (<-100)"
            _bo2 = ["Excelente (≥-70)","Buena (-70 a -90)","Aceptable (-90 a -100)","Crítica (<-100)"]
            _bc2 = ["#22C55E","#84CC16","#F59E0B","#EF4444"]
            df_sc5["Banda"] = df_sc5["RSRP_n"].apply(rsrp_band_v2)
            df_sc5["Banda"] = pd.Categorical(df_sc5["Banda"],categories=_bo2,ordered=True)
            by_band5 = df_sc5.groupby("Banda",observed=True).agg(
                cuota_alta_media=("CUOTA_A","mean"), pdvs=("CUOTA_A","count"), rsrp_m=("RSRP_n","mean"),
            ).reset_index()
            by_band5["Banda"] = by_band5["Banda"].astype(str)
            _ausentes = [b for b in _bo2 if b not in by_band5["Banda"].tolist()]
            st.markdown(f'<div class="section-card"><div class="section-title">Cuota de altas por banda de señal</div><div class="section-subtitle">{"⚠️ Sin PDVs en Excelente ni Buena — red opera solo en Aceptable y Crítica · " if _ausentes else ""}¿Los PDVs con mejor señal captan más? · línea azul = referencia 50%</div>', unsafe_allow_html=True)
            if not by_band5.empty:
                _ym = max(by_band5["cuota_alta_media"].max()*1.3,60)
                _ch_band = alt.Chart(by_band5).mark_bar(cornerRadiusTopLeft=7,cornerRadiusTopRight=7).encode(
                    x=alt.X("Banda:N",sort=_bo2,title=None,axis=alt.Axis(labelAngle=-12,labelLimit=220)),
                    y=alt.Y("cuota_alta_media:Q",title="Cuota altas (%)",scale=alt.Scale(domain=[0,_ym])),
                    color=alt.Color("Banda:N",scale=alt.Scale(domain=_bo2,range=_bc2),legend=None),
                    tooltip=[alt.Tooltip("Banda:N"),alt.Tooltip("pdvs:Q",title="PDVs"),alt.Tooltip("rsrp_m:Q",format=".1f",title="RSRP medio"),alt.Tooltip("cuota_alta_media:Q",format=".1f",title="Cuota alta %")]
                ).properties(height=280)
                _r50b = alt.Chart(pd.DataFrame({"y":[50]})).mark_rule(color="#38BDF8",strokeDash=[5,3],strokeWidth=1.5).encode(y="y:Q")
                _txt_b = alt.Chart(by_band5).mark_text(dy=-14,fontSize=12,fontWeight="bold",color="#F8FAFC").encode(
                    x=alt.X("Banda:N",sort=_bo2), y=alt.Y("cuota_alta_media:Q"),
                    text=alt.Text("cuota_alta_media:Q",format=".1f")
                )
                st.altair_chart(style_chart(_ch_band+_r50b+_txt_b), use_container_width=True, theme=None)
                if _ausentes:
                    st.markdown(f'<div style="font-size:.72rem;color:#FCA5A5;background:rgba(239,68,68,0.10);border-radius:10px;padding:5px 10px;margin-top:4px;">⚠️ Sin PDVs en banda: <b>{", ".join(_ausentes)}</b></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── BLOQUE 5: Cuota de altas por categoría + tabla zona de mejora ─────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:18px 0 8px 0;">¿En qué tipo de PDV y agente hay más para ganar?</div>', unsafe_allow_html=True)
        b5a, b5b = st.columns(2, gap="large")
        with b5a:
            cuota_cat5 = df.groupby("CATEGORIA").agg(
                cuota_mkt=("CUOTA DE MERCADO","mean"), cuota_alta=("CUOTA DE ALTA","mean"), n=("ID","count"),
            ).reset_index()
            cuota_cat5["CATEGORIA"] = pd.Categorical(cuota_cat5["CATEGORIA"],categories=["DIAMANTE","PLATINO","ORO","PLATA","BRONCE"],ordered=True)
            cuota_cat5 = cuota_cat5.sort_values("CATEGORIA")
            st.markdown('<div class="section-card"><div class="section-title">Cuota de altas por categoría de PDV</div><div class="section-subtitle">¿En qué nivel de PDV capta más Claro? · línea azul = paridad 50% · por debajo = la competencia gana más en esa categoría</div>', unsafe_allow_html=True)
            _ch_cat5 = alt.Chart(cuota_cat5).mark_bar(cornerRadiusTopLeft=6,cornerRadiusTopRight=6).encode(
                x=alt.X("CATEGORIA:N",sort=["DIAMANTE","PLATINO","ORO","PLATA","BRONCE"],title=None),
                y=alt.Y("cuota_alta:Q",title="Cuota alta Claro (%)"),
                color=alt.Color("CATEGORIA:N",scale=alt.Scale(domain=list(CATEGORIA_COLORS.keys()),range=list(CATEGORIA_COLORS.values())),legend=None),
                tooltip=[alt.Tooltip("CATEGORIA:N"),alt.Tooltip("cuota_alta:Q",format=".1f",title="Cuota alta %"),alt.Tooltip("cuota_mkt:Q",format=".1f",title="Cuota mkt %"),alt.Tooltip("n:Q",title="PDVs")]
            ).properties(height=280)
            _r50c5 = alt.Chart(pd.DataFrame({"y":[50]})).mark_rule(color="#38BDF8",strokeDash=[5,3],strokeWidth=1.5).encode(y="y:Q")
            st.altair_chart(style_chart(_ch_cat5+_r50c5), use_container_width=True, theme=None)
            st.markdown('</div>', unsafe_allow_html=True)

        with b5b:
            # Tabla de zona de mejora por agente — métricas reales validadas, sin score
            _ag_mejora = df.groupby("AGENTE").agg(
                pdvs=("ID","count"),
                rsrp_medio=("RSRP","mean"),
                pct_criticos=("RSRP", lambda x: (pd.to_numeric(x,errors="coerce")<-100).mean()*100),
                cuota_alta=("CUOTA DE ALTA","mean"),
                cuota_mkt=("CUOTA DE MERCADO","mean"),
                ejec_nat=("EJEC ALTA NAT","sum"),
                meta_nat=("META ALTA NAT (>$2000)","sum"),
            ).reset_index()
            _ag_mejora["cumpl"] = (_ag_mejora["ejec_nat"]/_ag_mejora["meta_nat"].replace(0,np.nan)*100).fillna(0)
            _ag_mejora["proy"]  = (_ag_mejora["ejec_nat"]/_ag_mejora["meta_nat"].replace(0,np.nan)*100).fillna(0)  # mes cerrado
            _ag_mejora["brecha"]= _ag_mejora["meta_nat"] - _ag_mejora["ejec_nat"]
            _ag_mejora = _ag_mejora.sort_values("cuota_alta")
            st.markdown('<div class="section-card"><div class="section-title">Zona de mejora por agente</div><div class="section-subtitle">Ordenado por menor cuota de altas · muestra señal, captación y cumplimiento en una sola vista para identificar dónde actuar</div>', unsafe_allow_html=True)
            _show_mej = safe_round_columns(
                _ag_mejora[["AGENTE","pdvs","rsrp_medio","pct_criticos","cuota_alta","cuota_mkt","cumpl","proy","brecha"]].copy(),
                ["rsrp_medio","pct_criticos","cuota_alta","cuota_mkt","cumpl","proy","brecha"]
            )
            _show_mej.columns = ["Agente","PDVs","RSRP medio","% PDVs críticos","Cuota alta %","Cuota mkt %","Cumpl. %","Cumpl. total %","Brecha"]
            st.dataframe(_show_mej, use_container_width=True, height=260)
            st.markdown('<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">El agente arriba de la tabla tiene menor cuota de altas — es donde hay más potencial de captación por ganar · combina con la señal para priorizar</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── BLOQUE 6: Tabla circuitos+barrios por oportunidad ─────────────────
        st.markdown('<div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:18px 0 8px 0;">Circuitos y barrios con mayor oportunidad de mejora</div>', unsafe_allow_html=True)
        if "CIRCUITO" in df.columns:
            _df_opp5b = df.copy()
            _df_opp5b["RSRP_n5"]      = pd.to_numeric(_df_opp5b["RSRP"],errors="coerce")
            _df_opp5b["CUOTA_ALTA_n5"]= pd.to_numeric(_df_opp5b["CUOTA DE ALTA"],errors="coerce")
            _df_opp5b["META_n5"]      = pd.to_numeric(_df_opp5b["META ALTA NAT (>$2000)"],errors="coerce")
            _df_opp5b["EJEC_n5"]      = pd.to_numeric(_df_opp5b["EJEC ALTA NAT"],errors="coerce")
            _df_opp5b["cumpl_5"]      = (_df_opp5b["EJEC_n5"]/_df_opp5b["META_n5"].replace(0,np.nan)*100).fillna(0)
            _df_opp5b["banda5"]       = _df_opp5b["RSRP_n5"].apply(lambda v: rsrp_band_v2(v) if pd.notna(v) else "Sin datos")
            _group5b = [c for c in ["BARRIO","CIRCUITO","AGENTE"] if c in _df_opp5b.columns]
            _circ5b = _df_opp5b[_df_opp5b["META_n5"]>0].groupby(_group5b).agg(
                pdvs=("ID","count"), rsrp_medio=("RSRP_n5","mean"),
                cuota_alta=("CUOTA_ALTA_n5","mean"), cumpl=("cumpl_5","mean"),
                pdvs_criticos=("banda5", lambda x: (x=="Crítica (<-100)").sum()),
                meta=("META_n5","sum"), ejec=("EJEC_n5","sum"),
            ).reset_index()
            _circ5b["brecha"] = _circ5b["meta"] - _circ5b["ejec"]
            _circ5b = _circ5b[(_circ5b["cuota_alta"]<50) | (_circ5b["cumpl"]<70)].sort_values(["pdvs_criticos","brecha"],ascending=[False,False]).head(20)
            _rn5b = {"BARRIO":"Barrio","CIRCUITO":"Circuito","AGENTE":"Agente","pdvs":"PDVs","rsrp_medio":"RSRP medio","cuota_alta":"Cuota alta %","cumpl":"Cumpl. %","pdvs_criticos":"PDVs críticos","meta":"Meta","ejec":"Ejecutado","brecha":"Brecha"}
            _sc5b = [c for c in _rn5b.keys() if c in _circ5b.columns]
            _show5b = safe_round_columns(_circ5b[_sc5b].copy(),["rsrp_medio","cuota_alta","cumpl","brecha"])
            _show5b = _show5b.rename(columns={k:v for k,v in _rn5b.items() if k in _show5b.columns})
            st.dataframe(_show5b, use_container_width=True, height=300)
            st.markdown('<div style="font-size:.72rem;color:#94A3B8;margin-top:4px;">Filtrados por cuota &lt;50% o cumplimiento &lt;70% · ordenados por PDVs críticos y brecha · incluye barrio para gestión en campo</div>', unsafe_allow_html=True)


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
    st.info("Recarga la página o contacta al administrador si el problema persiste.")
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
# PANTALLA DE BIENVENIDA — se muestra solo si no hay datos cargados aún
# =========================================================
_has_claro_file = (
    st.session_state.get("claro_uploaded_file") is not None or
    find_existing_file(CLARO_FILE_CANDIDATES) is not None
)
_has_rsrp_file = find_existing_file(DATA_FILE_CANDIDATES) is not None if 'DATA_FILE_CANDIDATES' in dir() else False

_show_welcome = not _has_claro_file and not _has_rsrp_file
if _show_welcome:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:32px;">
        <div style="width:52px;height:52px;background:#E10600;border-radius:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
        </div>
        <div>
            <div style="font-size:1.6rem;font-weight:950;color:#F8FAFC;line-height:1.1;">Dashboard de Inteligencia Comercial</div>
            <div style="font-size:.84rem;color:#64748B;margin-top:3px;">Claro Colombia · Red y Mercado · Gestión de Agentes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_w1, col_w2 = st.columns(2, gap="large")

    with col_w1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.95),rgba(10,18,34,0.98));border:1px solid rgba(255,255,255,0.09);border-radius:20px;padding:24px 26px;height:100%;">
            <div style="font-size:.68rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:12px;">Vista de Red y Mercado</div>
            <div style="font-size:.84rem;color:#E2E8F0;line-height:1.7;margin-bottom:14px;">
                Analiza la calidad de señal RSRP por operador, territorio y variación temporal.
                Incluye análisis competitivo de cuota de mercado y captación de altas.
            </div>
            <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;">
                <div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;margin-bottom:8px;">Cómo activar</div>
                <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                    <span style="background:#38BDF8;color:#0F172A;font-size:.64rem;font-weight:900;padding:2px 7px;border-radius:99px;flex-shrink:0;margin-top:1px;">1</span>
                    <span style="font-size:.76rem;color:#CBD5E1;">El archivo CSV de señal debe estar en la misma carpeta del proyecto en el servidor.</span>
                </div>
                <div style="display:flex;align-items:flex-start;gap:8px;">
                    <span style="background:#38BDF8;color:#0F172A;font-size:.64rem;font-weight:900;padding:2px 7px;border-radius:99px;flex-shrink:0;margin-top:1px;">2</span>
                    <span style="font-size:.76rem;color:#CBD5E1;">Selecciona "Red y Mercado · Operadores" en el selector del sidebar.</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_w2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.95),rgba(10,18,34,0.98));border:1px solid rgba(225,6,0,0.20);border-radius:20px;padding:24px 26px;height:100%;">
            <div style="font-size:.68rem;font-weight:900;color:#FCA5A5;text-transform:uppercase;letter-spacing:.4px;margin-bottom:12px;">Vista de Agentes Claro</div>
            <div style="font-size:.84rem;color:#E2E8F0;line-height:1.7;margin-bottom:14px;">
                Seguimiento comercial de metas, altas orgánicas e inducidas, PDVs, asesores,
                cuota de altas y señal RSRP por agente y circuito.
            </div>
            <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;">
                <div style="font-size:.70rem;font-weight:900;color:#94A3B8;text-transform:uppercase;margin-bottom:8px;">Cómo activar</div>
                <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                    <span style="background:#E10600;color:white;font-size:.64rem;font-weight:900;padding:2px 7px;border-radius:99px;flex-shrink:0;margin-top:1px;">1</span>
                    <span style="font-size:.76rem;color:#CBD5E1;">En el sidebar, haz clic en <b style="color:#F8FAFC;">"Cargar archivo Excel"</b> y selecciona el archivo del mes.</span>
                </div>
                <div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">
                    <span style="background:#E10600;color:white;font-size:.64rem;font-weight:900;padding:2px 7px;border-radius:99px;flex-shrink:0;margin-top:1px;">2</span>
                    <span style="font-size:.76rem;color:#CBD5E1;">El archivo puede tener cualquier nombre de hoja — el sistema detecta automáticamente la hoja que contiene el plan de trabajo por sus columnas.</span>
                </div>
                <div style="display:flex;align-items:flex-start;gap:8px;">
                    <span style="background:#E10600;color:white;font-size:.64rem;font-weight:900;padding:2px 7px;border-radius:99px;flex-shrink:0;margin-top:1px;">3</span>
                    <span style="font-size:.76rem;color:#CBD5E1;">Selecciona <b style="color:#F8FAFC;">"Agentes Claro · PDVs"</b> en el selector del sidebar.</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:18px 22px;margin-top:16px;">
        <div style="font-size:.68rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:10px;">Tabs disponibles en cada vista</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div>
                <div style="font-size:.72rem;font-weight:800;color:#38BDF8;margin-bottom:5px;">Red y Mercado</div>
                <div style="font-size:.74rem;color:#94A3B8;line-height:1.8;">
                    Resumen · Estado global de señal<br>
                    Operadores · Ranking competitivo<br>
                    Territorio · Zonas críticas por CP<br>
                    Variación · Cambio de señal en el tiempo<br>
                    Mercado · Cuota y captación vs competencia
                </div>
            </div>
            <div>
                <div style="font-size:.72rem;font-weight:800;color:#E10600;margin-bottom:5px;">Agentes Claro</div>
                <div style="font-size:.74rem;color:#94A3B8;line-height:1.8;">
                    ↗ ¿Cómo vamos? · Resultado del mes<br>
                    ◈ ¿Quién cumple? · Ranking de agentes<br>
                    ◎ La brecha · PDVs y capacidad de mejora<br>
                    ∿ El ritmo · Curva semanal de ventas<br>
                    ◉ Oportunidades · Cuota, señal y mercado
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:.70rem;color:#475569;text-align:center;margin-top:20px;">Los datos procesados en este dashboard no se almacenan en ningún servidor. Todo se procesa localmente en tu sesión.</div>', unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## Centro de control")
st.sidebar.markdown(f"""<div class="sidebar-guide-row"><span class="sidebar-guide-pill">{icon_svg("filter",12)} Ajusta universo</span><span class="sidebar-guide-pill">{icon_svg("users",12)} Define operadores</span><span class="sidebar-guide-pill">{icon_svg("target",12)} Enfoca lectura</span></div>""", unsafe_allow_html=True)

# ---- CARGADOR DE ARCHIVO ----
st.sidebar.markdown(f'<div class="sidebar-block"><div class="sidebar-kicker">{icon_svg("spark",12)} Datos del mes</div><div class="sidebar-title">Cargar archivo Excel</div><div class="sidebar-sub">Sube el archivo del mes para actualizar el dashboard. El archivo no se guarda en ningún servidor — se procesa solo en tu sesión.</div>', unsafe_allow_html=True)

_uploaded = st.sidebar.file_uploader(
    "Seleccionar archivo (.xlsx)",
    type=["xlsx"],
    key="claro_file_upload",
    label_visibility="collapsed",
    help="El dashboard detecta automáticamente la hoja correcta. Nombre sugerido: Plan_actualizado_CORTE_XX_FINAL.xlsx"
)

if _uploaded is not None:
    # Store in session state so load_claro_data() picks it up
    st.session_state["claro_uploaded_file"] = _uploaded
    # Quick validation preview
    try:
        _xl_prev = pd.ExcelFile(_uploaded)
        _sheet_prev, _err_prev = _find_detail_sheet(_xl_prev)
        _uploaded.seek(0)
        if _err_prev:
            st.sidebar.error(f"⚠️ {_err_prev}")
        else:
            _preview = pd.read_excel(_xl_prev, sheet_name=_sheet_prev, header=0, nrows=3)
            _preview.columns = [str(c).strip() for c in _preview.columns]
            _uploaded.seek(0)
            _faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in _preview.columns]
            _nuevas    = [c for c in _preview.columns
                          if c not in set(COLUMNAS_REQUERIDAS) | set(COLUMNAS_OPCIONALES.keys())
                          | {"TOTAL META ALTA","% CUMPLI","META ARPU","EJEC ARPU","TIPO","CODIGO POSTAL",
                             "VR_M-1.2","VR_M-12.2","AGENTE","ID","ASESOR","CATEGORIA","TIPOLOGIA",
                             "CLASIFICACION","BARRIO","ZONA","RUTA","CIRCUITO"}]
            if _faltantes:
                st.sidebar.error(f"⚠️ Faltan columnas requeridas:\n{', '.join(_faltantes)}")
            else:
                st.sidebar.success(f"✅ {_uploaded.name} · hoja: '{_sheet_prev}'")
                if _nuevas:
                    st.sidebar.info(f"ℹ️ Columnas nuevas detectadas:\n{', '.join(_nuevas)}")
    except Exception as _e:
        st.sidebar.error(f"Error leyendo el archivo: {_e}")
else:
    # Check if there's a file on disk as fallback
    _disk_path = find_existing_file(CLARO_FILE_CANDIDATES)
    if _disk_path:
        st.sidebar.info(f"Usando archivo del servidor: {os.path.basename(_disk_path)}")
    else:
        st.sidebar.warning("Sin archivo cargado. Sube el Excel del mes para ver la vista de Agentes.")

st.sidebar.markdown('</div>', unsafe_allow_html=True)

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
    fecha_min = pd.Timestamp("2024-01-01")
    fecha_max = pd.Timestamp.now()

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

    st.sidebar.markdown(f'<div class="sidebar-block"><div class="sidebar-kicker">{icon_svg("users",12)} Paso 3 · Define la competencia</div><div class="sidebar-title">Operadores visibles</div><div class="sidebar-sub">Selecciona los operadores a comparar. Impacta todos los tabs.</div>', unsafe_allow_html=True)
    btn1, btn2 = st.sidebar.columns(2)
    with btn1:
        if st.button("Todos", use_container_width=True):
            for op in operator_cols:
                st.session_state[f"op_{op}"] = True
    with btn2:
        if st.button("Ninguno", use_container_width=True):
            for op in operator_cols:
                st.session_state[f"op_{op}"] = False
    for op in operator_cols:
        op_color = OPERATOR_COLORS.get(op, "#64748B")
        col_left, col_right = st.sidebar.columns([0.12, 0.88])
        with col_left:
            st.markdown(f'<div style="width:10px;height:10px;border-radius:50%;background:{op_color};margin-top:10px;"></div>', unsafe_allow_html=True)
        with col_right:
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

best_operator = summary_operator.sort_values("RSRP_mediana", ascending=False).iloc[0]
worst_operator = summary_operator.sort_values("RSRP_mediana", ascending=True).iloc[0]
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
territorial_cross = business_metrics.get("territorial_cross", pd.DataFrame())
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
        best_operator["RSRP_mediana"] - worst_operator["RSRP_mediana"]
        if best_operator is not None and worst_operator is not None
        and pd.notna(best_operator.get("RSRP_mediana", np.nan))
        and pd.notna(worst_operator.get("RSRP_mediana", np.nan))
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
    _gap_text = fmt_dBm(score_gap) if pd.notna(score_gap) else "N/D"
    tab2_insight_body = f"{_best_op_name} lidera en señal con mediana {fmt_dBm(best_operator['RSRP_mediana'])}; la brecha de señal frente al operador más débil es de {_gap_text} dBm."
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

if not _show_welcome:
    if _vista_claro:
        render_claro_view()
        st.stop()

# =========================================================
# HEADER (VISTA RED/MERCADO)
# =========================================================
if _show_welcome:
    st.stop()

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

# ── Franja de navegación — ENCIMA de los tabs ────────────────────────────────
def _op_nav_icon(name):
    icons = {
        "eye":   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
        "users": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        "map":   '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>',
        "trend": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
        "brief": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>',
    }
    return icons.get(name, "")

_t1_color = "#22C55E" if (global_median or 0) >= -90 else "#F59E0B" if (global_median or 0) >= -100 else "#EF4444"
_t3_color = "#EF4444" if worst_zone is not None and worst_zone.get("Pct_critica", 0) > 30 else "#F59E0B"

st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:10px 0 10px 0;">
    <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
        <div style="margin-bottom:5px;">{_op_nav_icon("eye")}</div>
        <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:2px;">Resumen</div>
        <div style="font-size:.66rem;color:#64748B;margin-bottom:5px;">Estado global de señal</div>
        <div style="display:flex;align-items:center;gap:4px;font-size:.70rem;font-weight:800;color:{_t1_color};"><span style="width:7px;height:7px;border-radius:50%;background:{_t1_color};display:inline-block;flex-shrink:0;"></span>{fmt_dBm(global_median)}</div>
    </div>
    <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
        <div style="margin-bottom:5px;">{_op_nav_icon("users")}</div>
        <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:2px;">Operadores</div>
        <div style="font-size:.66rem;color:#64748B;margin-bottom:5px;">Ranking competitivo</div>
        <div style="font-size:.70rem;font-weight:800;color:{OPERATOR_COLORS.get(best_operator["Operador"],"#F8FAFC")};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">Líder: {best_operator["Operador"]}</div>
    </div>
    <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
        <div style="margin-bottom:5px;">{_op_nav_icon("map")}</div>
        <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:2px;">Territorio</div>
        <div style="font-size:.66rem;color:#64748B;margin-bottom:5px;">Zonas críticas</div>
        <div style="display:flex;align-items:center;gap:4px;font-size:.70rem;font-weight:800;color:{_t3_color};"><span style="width:7px;height:7px;border-radius:50%;background:{_t3_color};display:inline-block;flex-shrink:0;"></span>{fmt_int(cp_critical_count)} CP críticos</div>
    </div>
    <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
        <div style="margin-bottom:5px;">{_op_nav_icon("trend")}</div>
        <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:2px;">Variación</div>
        <div style="font-size:.66rem;color:#64748B;margin-bottom:5px;">Cambio de señal</div>
        <div style="font-size:.70rem;font-weight:800;color:{"#22C55E" if variation_result.get("variacion_global",0)>=0 else "#EF4444"};">{"▲" if variation_result.get("variacion_global",0)>=0 else "▼"} {fmt_var_dBm(variation_result.get("variacion_global",0))}</div>
    </div>
    <div style="background:linear-gradient(135deg,rgba(17,24,39,0.92),rgba(10,18,34,0.96));border:1px solid rgba(255,255,255,0.09);border-radius:16px;padding:11px 12px;box-sizing:border-box;overflow:hidden;min-width:0;">
        <div style="margin-bottom:5px;">{_op_nav_icon("brief")}</div>
        <div style="font-size:.76rem;font-weight:900;color:#F8FAFC;margin-bottom:2px;">Mercado</div>
        <div style="font-size:.66rem;color:#64748B;margin-bottom:5px;">Cuota y captación</div>
        <div style="font-size:.70rem;font-weight:800;color:{OPERATOR_COLORS.get(leader_market["Operador"],"#38BDF8") if leader_market is not None else "#38BDF8"};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{leader_market["Operador"] if leader_market is not None else "N/D"} lidera</div>
    </div>
</div>
""", unsafe_allow_html=True)

def _sc_op(v): return "#22C55E" if v>=100 else "#F59E0B" if v>=70 else "#EF4444"
def _bar_op(pct, color):
    w = min(max(float(pct),0),100)
    return f'<div style="width:100%;height:5px;background:rgba(255,255,255,0.07);border-radius:99px;margin-top:5px;overflow:hidden;"><div style="width:{w}%;height:100%;background:{color};border-radius:99px;"></div></div>'

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Resumen",
    "Operadores",
    "Territorio",
    "Variación",
    "Mercado",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — RESUMEN
# Señal mediana como protagonista absoluto. Datos de soporte subordinados.
# Bloque comercial separado visualmente. Cierre con conclusión ejecutiva.
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    _t1m  = global_median or 0
    _t1c  = "#22C55E" if _t1m>=-90 else "#F59E0B" if _t1m>=-100 else "#EF4444"
    _t1e  = "Buena" if _t1m>=-90 else "Aceptable" if _t1m>=-100 else "Crítica"
    _t1msg= "Red en buen estado" if _t1m>=-90 else "Atención requerida en el territorio" if _t1m>=-100 else "Intervención urgente requerida"
    _t1cp_c = "#EF4444" if cp_critical_share>=0.25 else "#F59E0B" if cp_critical_share>=0.10 else "#22C55E"
    _t1pb_c = "#22C55E" if pct_good>=50 else "#F59E0B" if pct_good>=30 else "#EF4444"
    _biz1   = business_metrics.get("available",False)
    _lm1    = leader_market["Operador"] if leader_market is not None else None
    _la1    = leader_altas["Operador"]  if leader_altas  is not None else None

    # ── PROTAGONISTA — señal mediana, todo lo demás subordinado ──────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(17,24,39,0.97),rgba(10,18,34,0.99));border:1px solid rgba(255,255,255,0.10);border-radius:24px;padding:28px 32px;margin-bottom:16px;">
        <div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">Señal RSRP mediana · {periodo_txt_corto} · {fmt_int(obs_validas)} mediciones</div>
        <div style="display:flex;align-items:flex-end;gap:20px;margin-bottom:16px;">
            <div style="font-size:5rem;font-weight:950;color:{_t1c};line-height:1;">{fmt_dBm(_t1m)}</div>
            <div style="padding-bottom:8px;">
                <div style="font-size:1.1rem;font-weight:800;color:{_t1c};">{_t1e}</div>
                <div style="font-size:.82rem;color:#94A3B8;">{_t1msg}</div>
            </div>
        </div>
        <div style="width:100%;height:6px;background:rgba(255,255,255,0.07);border-radius:99px;overflow:hidden;margin-bottom:20px;">
            <div style="width:{max(0,min(100,(110+_t1m)/20*100)):.1f}%;height:100%;background:{_t1c};border-radius:99px;"></div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.07);">
            <div>
                <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.3px;margin-bottom:4px;">Códigos postales críticos</div>
                <div style="font-size:1.8rem;font-weight:900;color:{_t1cp_c};">{fmt_int(cp_critical_count)}</div>
                <div style="font-size:.68rem;color:#64748B;">{fmt_pct(cp_critical_share)} del territorio · señal bajo -100 dBm</div>
                {_bar_op(cp_critical_share*100, _t1cp_c)}
            </div>
            <div>
                <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.3px;margin-bottom:4px;">Cobertura buena o mejor</div>
                <div style="font-size:1.8rem;font-weight:900;color:{_t1pb_c};">{fmt_pct(pct_good)}</div>
                <div style="font-size:.68rem;color:#64748B;">Excelente + Buena (≥ -90 dBm)</div>
                {_bar_op(pct_good, _t1pb_c)}
            </div>
            <div>
                <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.3px;margin-bottom:4px;">Operador con mejor señal</div>
                <div style="font-size:1.2rem;font-weight:900;color:{OPERATOR_COLORS.get(best_operator["Operador"],"#F8FAFC")};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{best_operator["Operador"]}</div>
                <div style="font-size:.68rem;color:#64748B;">Mediana {fmt_dBm(best_operator["RSRP_mediana"])} · {float(best_operator["Buena_o_mejor"]):.1f}% buena+</div>
                {_bar_op(float(best_operator["Buena_o_mejor"]), OPERATOR_COLORS.get(best_operator["Operador"],"#64748B"))}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Distribución de señal ─────────────────────────────────────────────────
    st.markdown('<div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:8px;">Distribución de señal en el territorio</div>', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns((1.15, 0.85), gap="large")
    with r1c1:
        dist = df_f.groupby("Categoria_RSRP",as_index=False).size().rename(columns={"size":"Cantidad","Categoria_RSRP":"Categoria"})
        orden_cat = ["Excelente","Buena","Aceptable","Crítica","Sin medición"]
        dist["Categoria"] = pd.Categorical(dist["Categoria"],categories=orden_cat,ordered=True)
        dist = dist.sort_values("Categoria")
        dist["Pct"] = (dist["Cantidad"]/dist["Cantidad"].sum()*100).round(1)
        st.markdown('<div class="section-card"><div class="section-title">Mediciones por banda de señal</div><div class="section-subtitle">Cada barra = cuántas mediciones caen en esa banda · verde = buena señal · rojo = crítica</div>', unsafe_allow_html=True)
        if not dist.empty:
            _dch = alt.Chart(dist).mark_bar(cornerRadiusTopLeft=6,cornerRadiusTopRight=6).encode(
                x=alt.X("Categoria:N",title=None,sort=orden_cat),
                y=alt.Y("Cantidad:Q",title="Mediciones"),
                color=alt.Color("Categoria:N",scale=alt.Scale(domain=["Excelente","Buena","Aceptable","Crítica","Sin medición"],range=["#22C55E","#84CC16","#F59E0B","#EF4444","#64748B"]),legend=None),
                tooltip=[alt.Tooltip("Categoria:N",title="Banda"),alt.Tooltip("Cantidad:Q",title="Mediciones",format=","),alt.Tooltip("Pct:Q",title="%",format=".1f")]
            ).properties(height=240)
            st.altair_chart(style_chart(_dch), use_container_width=True, theme=None)
        st.markdown('</div>', unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="section-card"><div class="section-title">Composición por banda</div><div class="section-subtitle">% y volumen de cada banda</div>', unsafe_allow_html=True)
        if not dist.empty:
            for _, rr in dist.iterrows():
                _cc = {"Excelente":"#22C55E","Buena":"#84CC16","Aceptable":"#F59E0B","Crítica":"#EF4444"}.get(rr["Categoria"],"#64748B")
                _ww = float(rr["Pct"])
                st.markdown(f"""
                <div style="margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px;">
                        <span style="font-size:.76rem;font-weight:800;color:#E2E8F0;">{rr["Categoria"]}</span>
                        <span style="font-size:.85rem;font-weight:900;color:{_cc};">{_ww:.1f}%</span>
                    </div>
                    <div style="width:100%;height:7px;background:rgba(255,255,255,0.07);border-radius:99px;overflow:hidden;">
                        <div style="width:{_ww:.1f}%;height:100%;background:{_cc};border-radius:99px;"></div>
                    </div>
                    <div style="font-size:.65rem;color:#64748B;margin-top:2px;">{int(rr["Cantidad"]):,} mediciones</div>
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Bloque comercial — separado visualmente ───────────────────────────────
    if _biz1:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin:20px 0 10px 0;">
            <div style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></div>
            <div style="font-size:.66rem;font-weight:900;color:#64748B;text-transform:uppercase;letter-spacing:.4px;white-space:nowrap;padding:0 12px;">Posición comercial</div>
            <div style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></div>
        </div>
        """, unsafe_allow_html=True)

        _lmp1 = float(leader_market["Cuota_mercado_global"])      if leader_market is not None else 0
        _lap1 = float(leader_altas["Participacion_altas_global"]) if leader_altas  is not None else 0
        _vm1  = business_metrics.get("variation_market",np.nan)
        _va1  = business_metrics.get("variation_altas",np.nan)
        _gm1  = float(market_lead_gap) if pd.notna(market_lead_gap) else 0

        bc1,bc2,bc3,bc4 = st.columns(4,gap="medium")
        with bc1:
            _lmc = OPERATOR_COLORS.get(_lm1,"#F8FAFC") if _lm1 else "#F8FAFC"
            st.markdown(f"""<div class="card" style="min-height:0;">
                <div class="kpi-label">Líder de mercado</div>
                <div class="kpi-value" style="font-size:1.1rem;color:{_lmc};">{_lm1 or "N/D"}</div>
                <div class="kpi-sub">{_lmp1:.1f}% cuota acumulada</div>
                {_bar_op(_lmp1,_lmc)}
            </div>""", unsafe_allow_html=True)
        with bc2:
            _lac = OPERATOR_COLORS.get(_la1,"#F8FAFC") if _la1 else "#F8FAFC"
            st.markdown(f"""<div class="card" style="min-height:0;">
                <div class="kpi-label">Líder de captación</div>
                <div class="kpi-value" style="font-size:1.1rem;color:{_lac};">{_la1 or "N/D"}</div>
                <div class="kpi-sub">{_lap1:.1f}% participación en altas</div>
                {_bar_op(_lap1,_lac)}
            </div>""", unsafe_allow_html=True)
        with bc3:
            _mvc = "#22C55E" if pd.notna(_vm1) and _vm1>=0 else "#EF4444"
            st.markdown(f"""<div class="card" style="min-height:0;">
                <div class="kpi-label">Tendencia de mercado</div>
                <div class="kpi-value" style="color:{_mvc};">{"▲" if pd.notna(_vm1) and _vm1>=0 else "▼"} {f"{abs(_vm1):.1f} pp" if pd.notna(_vm1) else "S/D"}</div>
                <div class="kpi-sub">{"Mercado en crecimiento" if pd.notna(_vm1) and _vm1>=0 else "Mercado en contracción"} vs periodo ant.</div>
            </div>""", unsafe_allow_html=True)
        with bc4:
            _gmc = "#22C55E" if _gm1>=15 else "#F59E0B" if _gm1>=5 else "#EF4444"
            st.markdown(f"""<div class="card" style="min-height:0;">
                <div class="kpi-label">Ventaja del líder</div>
                <div class="kpi-value" style="color:{_gmc};">{_gm1:.1f} pp</div>
                <div class="kpi-sub">{"Liderazgo sólido" if _gm1>=15 else "Liderazgo moderado" if _gm1>=5 else "Mercado muy disputado"}</div>
            </div>""", unsafe_allow_html=True)

    # ── Conclusión ejecutiva ──────────────────────────────────────────────────
    _n_ops_t1 = len(summary_operator)
    _worst_op = summary_operator.sort_values("RSRP_mediana").iloc[0]["Operador"] if not summary_operator.empty else "N/D"
    _concl_red = (
        f"La red opera en banda {_t1e.lower()} con mediana {fmt_dBm(_t1m)}. "
        f"{'El territorio no presenta alertas críticas.' if cp_critical_share<0.10 else f'{fmt_int(cp_critical_count)} CP ({fmt_pct(cp_critical_share)}) están en señal crítica — requieren intervención.'} "
        f"{best_operator['Operador']} lidera la señal con {fmt_dBm(best_operator['RSRP_mediana'])} de mediana; "
        f"{_worst_op} tiene la señal más débil del grupo de {_n_ops_t1} operadores."
    )
    _concl_biz = ""
    if _biz1 and _lm1 and _la1:
        _same = _lm1 == _la1
        _concl_biz = (
            f" Comercialmente, {_lm1} domina {'tanto en mercado como en captación' if _same else 'el mercado'} "
            f"con {_lmp1:.1f}% de cuota" +
            (f", mientras {_la1} lidera la captación con {_lap1:.1f}% de las altas." if not _same else f" y {_lap1:.1f}% de las altas nuevas.")
        )

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(14,165,233,0.06),rgba(99,102,241,0.06));border:1px solid rgba(99,102,241,0.18);border-radius:18px;padding:16px 20px;margin-top:14px;">
        <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px;">Conclusión ejecutiva del periodo</div>
        <div style="font-size:.84rem;color:#E2E8F0;line-height:1.7;">{_concl_red}{_concl_biz}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — OPERADORES
# Ranking sin redundancia + una gráfica que añade valor + cierre con conclusión
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    _ops = summary_operator.sort_values("RSRP_mediana",ascending=False).reset_index(drop=True)
    _lid = _ops.iloc[0]
    _rez = _ops.iloc[-1]
    _brecha = float(_lid["RSRP_mediana"] - _rez["RSRP_mediana"])

    # ── 3 KPIs ───────────────────────────────────────────────────────────────
    st.markdown('<div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:8px;">¿Qué tan diferente es la señal entre operadores?</div>', unsafe_allow_html=True)
    ok1,ok2,ok3 = st.columns(3,gap="medium")
    with ok1:
        _lc = OPERATOR_COLORS.get(_lid["Operador"],"#F8FAFC")
        st.markdown(f"""<div class="card" style="min-height:0;">
            <div class="kpi-label">Mejor señal</div>
            <div class="kpi-value" style="font-size:1.3rem;color:{_lc};">{_lid["Operador"]}</div>
            <div class="kpi-sub">Mediana <b>{fmt_dBm(_lid["RSRP_mediana"])}</b> · {float(_lid["Buena_o_mejor"]):.1f}% buena+</div>
            {_bar_op(float(_lid["Buena_o_mejor"]),_lc)}
        </div>""", unsafe_allow_html=True)
    with ok2:
        _rc = OPERATOR_COLORS.get(_rez["Operador"],"#64748B")
        st.markdown(f"""<div class="card" style="min-height:0;">
            <div class="kpi-label">Señal más débil</div>
            <div class="kpi-value" style="font-size:1.3rem;color:{_rc};">{_rez["Operador"]}</div>
            <div class="kpi-sub">Mediana <b>{fmt_dBm(_rez["RSRP_mediana"])}</b> · {float(_rez["Critica"]):.1f}% crítica</div>
            {_bar_op(float(_rez["Critica"]),"#EF4444")}
        </div>""", unsafe_allow_html=True)
    with ok3:
        _bc = "#22C55E" if abs(_brecha)<=5 else "#F59E0B" if abs(_brecha)<=15 else "#EF4444"
        st.markdown(f"""<div class="card" style="min-height:0;">
            <div class="kpi-label">Brecha de señal</div>
            <div class="kpi-value" style="color:{_bc};">{abs(_brecha):.1f} dBm</div>
            <div class="kpi-sub">{"Operadores similares" if abs(_brecha)<=5 else "Diferencia notable" if abs(_brecha)<=15 else "Diferencia significativa"} entre mejor y peor</div>
        </div>""", unsafe_allow_html=True)

    # ── Ranking — una fila completa por operador ──────────────────────────────
    st.markdown('<div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:14px 0 8px 0;">Ranking por señal mediana — de mejor a peor</div>', unsafe_allow_html=True)
    for idx_op, ro in _ops.iterrows():
        _oc  = OPERATOR_COLORS.get(ro["Operador"],"#64748B")
        _med = float(ro["RSRP_mediana"])
        _bun = float(ro["Buena_o_mejor"])
        _cri = float(ro["Critica"])
        _ace = float(ro["Aceptable"])
        _obs = int(ro["Observaciones"])
        _cod = int(ro["Codigos"])
        _mm  = float(_ops["RSRP_mediana"].min())
        _mx  = float(_ops["RSRP_mediana"].max())
        _ww  = int((_med-_mm)/max(_mx-_mm,1)*100)
        _mc  = "#22C55E" if _med>=-90 else "#F59E0B" if _med>=-100 else "#EF4444"
        _cc  = "#EF4444" if _cri>30 else "#F59E0B" if _cri>10 else "#22C55E"
        _pos = idx_op + 1
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:10px 14px;margin-bottom:6px;">
            <div style="width:24px;text-align:center;font-size:.80rem;font-weight:900;color:#64748B;flex-shrink:0;">#{_pos}</div>
            <div style="width:150px;flex-shrink:0;display:flex;align-items:center;gap:7px;">
                <span style="width:9px;height:9px;border-radius:50%;background:{_oc};display:inline-block;flex-shrink:0;"></span>
                <span style="font-size:.80rem;font-weight:800;color:#F8FAFC;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{ro["Operador"]}</span>
            </div>
            <div style="flex:1;min-width:0;"><div style="width:100%;height:8px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;"><div style="width:{_ww}%;height:100%;background:{_mc};border-radius:99px;opacity:.85;"></div></div></div>
            <div style="width:90px;text-align:right;font-size:.95rem;font-weight:900;color:{_mc};flex-shrink:0;">{_med:.1f} dBm</div>
            <div style="width:95px;text-align:right;font-size:.72rem;color:#94A3B8;flex-shrink:0;">Buena+: <b style="color:#22C55E;">{_bun:.1f}%</b></div>
            <div style="width:85px;text-align:right;font-size:.72rem;color:#94A3B8;flex-shrink:0;">Aceptable: <b>{_ace:.1f}%</b></div>
            <div style="width:85px;text-align:right;font-size:.72rem;color:#94A3B8;flex-shrink:0;">Crítica: <b style="color:{_cc};">{_cri:.1f}%</b></div>
            <div style="width:75px;text-align:right;font-size:.66rem;color:#64748B;flex-shrink:0;">{_obs:,} obs<br>{_cod} CP</div>
        </div>""", unsafe_allow_html=True)

    # ── Gráfica que AÑADE valor: composición interna normalizada ─────────────
    st.markdown('<div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:14px 0 8px 0;">Composición interna de señal — la estructura real de cada operador</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-card"><div class="section-title">% de señal por banda (normalizado al 100%)</div><div class="section-subtitle">El ranking muestra quién tiene mejor mediana. Esta gráfica muestra QUÉ TAN DISTINTA es la estructura interna de cada operador. Un operador puede tener buena mediana pero mucha señal crítica oculta.</div>', unsafe_allow_html=True)
    sp = alt.Chart(quality_pct[quality_pct["Categoria_RSRP"].isin(order_quality[:-1])]).mark_bar().encode(
        x=alt.X("Operador:N",title=None),
        y=alt.Y("Porcentaje:Q",title="% del portafolio",stack="normalize"),
        color=alt.Color("Categoria_RSRP:N",scale=alt.Scale(domain=list(QUALITY_COLORS.keys()),range=list(QUALITY_COLORS.values())),legend=alt.Legend(title="Banda",orient="bottom")),
        order=alt.Order("Categoria_RSRP:N",sort="descending"),
        tooltip=[alt.Tooltip("Operador:N"),alt.Tooltip("Categoria_RSRP:N",title="Banda"),alt.Tooltip("Porcentaje:Q",title="%",format=".1f"),alt.Tooltip("Cantidad:Q",title="Mediciones",format=",")]
    ).properties(height=280)
    st.altair_chart(style_chart(sp), use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Conclusión ejecutiva ──────────────────────────────────────────────────
    _op_count = len(_ops)
    _top3_crit = _ops.nlargest(1,"Critica").iloc[0]
    _concl_op = (
        f"Entre los {_op_count} operadores visibles, {_lid['Operador']} tiene la mejor señal con mediana {fmt_dBm(_lid['RSRP_mediana'])} "
        f"y {float(_lid['Buena_o_mejor']):.1f}% de cobertura buena o mejor. "
        f"{_rez['Operador']} tiene la señal más débil con mediana {fmt_dBm(_rez['RSRP_mediana'])}. "
        f"La brecha de {abs(_brecha):.1f} dBm entre el mejor y el peor es {'pequeña — el mercado está competitivamente equilibrado en señal' if abs(_brecha)<=5 else 'notable — hay diferencias claras de calidad de red entre operadores' if abs(_brecha)<=15 else 'muy amplia — existe una ventaja estructural de señal significativa'}. "
        f"{_top3_crit['Operador']} concentra el mayor % de señal crítica ({float(_top3_crit['Critica']):.1f}%)."
    )
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(14,165,233,0.06),rgba(99,102,241,0.06));border:1px solid rgba(99,102,241,0.18);border-radius:18px;padding:16px 20px;margin-top:14px;">
        <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px;">Conclusión ejecutiva</div>
        <div style="font-size:.84rem;color:#E2E8F0;line-height:1.7;">{_concl_op}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Ver tabla completa"):
        _et = safe_round_columns(_ops[["Operador","RSRP_mediana","RSRP_promedio","Excelente","Buena","Aceptable","Critica","Buena_o_mejor","Observaciones","Codigos"]].copy(),["RSRP_mediana","RSRP_promedio","Excelente","Buena","Aceptable","Critica","Buena_o_mejor"])
        _et.columns = ["Operador","Mediana (dBm)","Promedio (dBm)","% Excelente","% Buena","% Aceptable","% Crítica","% Buena+","Observaciones","CP cubiertos"]
        st.dataframe(_et, use_container_width=True, height=260)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — TERRITORIO
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    _wz_cp  = enrich_cp_label(worst_zone["Codigo_postal"],worst_zone) if worst_zone is not None else "N/D"
    _wz_pct = float(worst_zone["Pct_critica"]) if worst_zone is not None else 0
    _wz_op  = worst_zone["Operador_mas_debil"] if worst_zone is not None else "N/D"
    _wz_med = float(worst_zone["RSRP_mediana"]) if worst_zone is not None else 0
    _bz_cp  = enrich_cp_label(best_zone["Codigo_postal"],best_zone) if best_zone is not None else "N/D"
    _bz_pct = float(best_zone["Pct_buena_o_mejor"]) if best_zone is not None else 0
    _n_cp   = zone_summary["Codigo_postal"].nunique() if not zone_summary.empty else 0
    _wz_c   = "#EF4444" if _wz_pct>=50 else "#F59E0B" if _wz_pct>=30 else "#22C55E"

    # ── Headline ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(17,24,39,0.97),rgba(10,18,34,0.99));border:1px solid rgba(255,255,255,0.10);border-radius:24px;padding:22px 28px;margin-bottom:16px;">
        <div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">Análisis territorial · {fmt_int(_n_cp)} CP evaluados · {fmt_int(cp_critical_count)} críticos ({fmt_pct(cp_critical_share)})</div>
        <div style="display:grid;grid-template-columns:1fr 1px 1fr;gap:24px;align-items:center;">
            <div>
                <div style="font-size:.62rem;font-weight:900;color:#FCA5A5;text-transform:uppercase;letter-spacing:.3px;margin-bottom:4px;">Zona prioritaria de intervención</div>
                <div style="font-size:1.5rem;font-weight:900;color:{_wz_c};">{_wz_cp}</div>
                <div style="font-size:.76rem;color:#94A3B8;margin-top:3px;">{fmt_pct(_wz_pct)} señal crítica · Mediana {fmt_dBm(_wz_med)} · Op. débil: {_wz_op}</div>
                {_bar_op(_wz_pct,"#EF4444")}
            </div>
            <div style="height:60px;background:rgba(255,255,255,0.07);"></div>
            <div>
                <div style="font-size:.62rem;font-weight:900;color:#86EFAC;text-transform:uppercase;letter-spacing:.3px;margin-bottom:4px;">Zona de mayor solidez</div>
                <div style="font-size:1.5rem;font-weight:900;color:#22C55E;">{_bz_cp}</div>
                <div style="font-size:.76rem;color:#94A3B8;margin-top:3px;">{fmt_pct(_bz_pct)} buena o mejor · Op. líder: {best_zone["Operador_lider"] if best_zone is not None else "N/D"}</div>
                {_bar_op(_bz_pct,"#22C55E")}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CP críticos + distribución ────────────────────────────────────────────
    z1,z2 = st.columns((1.4,0.6),gap="large")
    with z1:
        st.markdown('<div class="section-card"><div class="section-title">Top 15 CP más críticos</div><div class="section-subtitle">Ordenados por % señal crítica · pasa el mouse para ver operador más débil y número de operadores presentes</div>', unsafe_allow_html=True)
        if not top_zones.empty:
            tc = top_zones.copy()
            tc["Codigo_postal"] = tc["Codigo_postal"].astype(str)
            def _el(row):
                p=[str(row["Codigo_postal"])]
                if "LOCALIDAD" in row.index and pd.notna(row.get("LOCALIDAD")) and str(row.get("LOCALIDAD","")).strip() not in ("","nan"):
                    p.append(str(row["LOCALIDAD"]).title())
                return " · ".join(p)
            tc["Zona_label"] = tc.apply(_el,axis=1)
            bars = alt.Chart(tc.head(15)).mark_bar(cornerRadiusTopLeft=6,cornerRadiusBottomLeft=6).encode(
                x=alt.X("Pct_critica:Q",title="% señal crítica",scale=alt.Scale(domain=[0,100])),
                y=alt.Y("Zona_label:N",sort="-x",title=None,axis=alt.Axis(labelLimit=280)),
                color=alt.value("#EF4444"),
                tooltip=[alt.Tooltip("Codigo_postal:N",title="CP"),alt.Tooltip("Pct_critica:Q",title="% crítica",format=".1f"),alt.Tooltip("RSRP_mediana:Q",title="Mediana (dBm)",format=".1f"),alt.Tooltip("Operador_mas_debil:N",title="Op. más débil"),alt.Tooltip("Operadores_presentes:Q",title="# Operadores")]
            ).properties(height=400)
            st.altair_chart(style_chart(bars), use_container_width=True, theme=None)
        else:
            st.info("Sin datos territoriales.")
        st.markdown('</div>', unsafe_allow_html=True)

    with z2:
        # Distribución por nivel
        if not zone_summary.empty and "Pct_critica" in zone_summary.columns:
            _bins=[0,10,30,50,100]; _lbls=["0–10%","10–30%","30–50%",">50%"]
            _zc = zone_summary.copy()
            _zc["rango"] = pd.cut(_zc["Pct_critica"],bins=_bins,labels=_lbls,right=True)
            _rc = _zc["rango"].value_counts().reindex(_lbls,fill_value=0).reset_index()
            _rc.columns = ["Rango","CP"]
            st.markdown('<div class="section-card"><div class="section-title">CP por nivel de criticidad</div><div class="section-subtitle">Cuántos CP hay en cada rango de % señal crítica</div>', unsafe_allow_html=True)
            _total_cp = int(_rc["CP"].sum())
            for _, rn in _rc.iterrows():
                _rcc = "#EF4444" if rn["Rango"]==">50%" else "#F59E0B" if rn["Rango"]=="30–50%" else "#84CC16" if rn["Rango"]=="0–10%" else "#64748B"
                _rpct = int(rn["CP"])/max(_total_cp,1)*100
                st.markdown(f"""
                <div style="margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px;">
                        <span style="font-size:.74rem;color:#E2E8F0;font-weight:700;">{rn["Rango"]} crítica</span>
                        <span style="font-size:.82rem;font-weight:900;color:{_rcc};">{int(rn["CP"])} CP</span>
                    </div>
                    <div style="width:100%;height:6px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;">
                        <div style="width:{_rpct:.1f}%;height:100%;background:{_rcc};border-radius:99px;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Tabla compacta
        st.markdown('<div class="section-card" style="margin-top:8px;"><div class="section-title">Top 10 — tabla accionable</div><div class="section-subtitle">Solo las columnas que importan para actuar</div>', unsafe_allow_html=True)
        if not top_zones.empty:
            _sc = [c for c in ["Codigo_postal","LOCALIDAD","RSRP_mediana","Pct_critica","Pct_buena_o_mejor","Operador_mas_debil"] if c in top_zones.columns]
            _tz = safe_round_columns(top_zones[_sc].head(10).copy(),["RSRP_mediana","Pct_critica","Pct_buena_o_mejor"])
            _tz.columns = [{"Codigo_postal":"CP","LOCALIDAD":"Localidad","RSRP_mediana":"Mediana","Pct_critica":"% Crit.","Pct_buena_o_mejor":"% Buena+","Operador_mas_debil":"Op. débil"}.get(c,c) for c in _tz.columns]
            st.dataframe(_tz, use_container_width=True, height=280)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Conclusión ────────────────────────────────────────────────────────────
    _n_muy_crit = int((zone_summary["Pct_critica"]>50).sum()) if not zone_summary.empty else 0
    _concl_ter = (
        f"De {fmt_int(_n_cp)} CP evaluados, {fmt_int(cp_critical_count)} ({fmt_pct(cp_critical_share)}) están en señal crítica. "
        f"{fmt_int(_n_muy_crit)} CP superan el 50% de señal crítica — estos son la prioridad máxima de intervención. "
        f"La zona más urgente es {_wz_cp} con {fmt_pct(_wz_pct)} crítica y mediana {fmt_dBm(_wz_med)}. "
        f"En el otro extremo, {_bz_cp} es el referente del territorio con {fmt_pct(_bz_pct)} de señal buena o mejor."
    )
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(14,165,233,0.06),rgba(99,102,241,0.06));border:1px solid rgba(99,102,241,0.18);border-radius:18px;padding:16px 20px;margin-top:14px;">
        <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px;">Conclusión ejecutiva</div>
        <div style="font-size:.84rem;color:#E2E8F0;line-height:1.7;">{_concl_ter}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — VARIACIÓN
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    _vg4  = float(variation_result.get("variacion_global",0) or 0)
    _vc4  = "#22C55E" if _vg4>=0 else "#EF4444"
    _tie4 = variation_result.get("tiene_variacion",False)
    _pi4  = str(variation_result.get("periodo_inicial","N/D"))
    _pf4  = str(variation_result.get("periodo_final","N/D"))

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(17,24,39,0.97),rgba(10,18,34,0.99));border:1px solid rgba(255,255,255,0.10);border-radius:24px;padding:22px 28px;margin-bottom:16px;">
        <div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">Variación de señal RSRP · comparando <b style="color:#E2E8F0;">{_pi4}</b> vs <b style="color:#E2E8F0;">{_pf4}</b></div>
        <div style="display:flex;align-items:flex-end;gap:20px;margin-bottom:12px;">
            <div style="font-size:4rem;font-weight:950;color:{_vc4};line-height:1;">{"▲" if _vg4>=0 else "▼"} {fmt_var_dBm(_vg4)}</div>
            <div style="padding-bottom:6px;">
                <div style="font-size:1rem;font-weight:800;color:{_vc4};">{"Señal mejoró" if _vg4>=0 else "Señal se deterioró"} en el periodo</div>
                <div style="font-size:.76rem;color:#94A3B8;">{nivel_temporal_variacion} · {fmt_int(len(variation_cp)) if not variation_cp.empty else "N/D"} CP con datos en ambos periodos</div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:20px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.07);">
            <div>
                <div style="font-size:.62rem;font-weight:900;color:#86EFAC;text-transform:uppercase;margin-bottom:3px;">CP con mayor mejora</div>
                <div style="font-size:1.5rem;font-weight:900;color:#22C55E;">{fmt_var_dBm(mayor_mejora["Variacion_RSRP"]) if mayor_mejora is not None else "N/D"}</div>
                <div style="font-size:.68rem;color:#64748B;">CP {str(mayor_mejora["Codigo_postal"]) if mayor_mejora is not None else "N/D"}</div>
            </div>
            <div>
                <div style="font-size:.62rem;font-weight:900;color:#FCA5A5;text-transform:uppercase;margin-bottom:3px;">CP con mayor deterioro</div>
                <div style="font-size:1.5rem;font-weight:900;color:#EF4444;">{fmt_var_dBm(mayor_deterioro["Variacion_RSRP"]) if mayor_deterioro is not None else "N/D"}</div>
                <div style="font-size:.68rem;color:#64748B;">CP {str(mayor_deterioro["Codigo_postal"]) if mayor_deterioro is not None else "N/D"}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not _tie4:
        st.info(variation_result.get("message","Se necesitan al menos 2 periodos para calcular variación."))
    else:
        v1,v2 = st.columns(2,gap="large")
        with v1:
            st.markdown('<div class="section-card"><div class="section-title">Trayectoria de señal en el tiempo</div><div class="section-subtitle">Mediana RSRP por periodo · línea que sube = mejora de red · área = volumen de datos</div>', unsafe_allow_html=True)
            if not variation_period.empty:
                _pc = variation_period.columns[0]
                tj = alt.Chart(variation_period).mark_line(point=True,strokeWidth=2.5,color="#E10600").encode(
                    x=alt.X(f"{_pc}:T",title=None),
                    y=alt.Y("RSRP_mediana:Q",title="RSRP mediano (dBm)"),
                    tooltip=[alt.Tooltip(f"{_pc}:T",title="Periodo"),alt.Tooltip("RSRP_mediana:Q",title="Mediana (dBm)",format=".1f")]
                ).properties(height=280)
                ta = alt.Chart(variation_period).mark_area(opacity=0.10,color="#E10600").encode(x=alt.X(f"{_pc}:T"),y=alt.Y("RSRP_mediana:Q"))
                st.altair_chart(style_chart(ta+tj), use_container_width=True, theme=None)
            else:
                st.info("Sin datos de trayectoria.")
            st.markdown('</div>', unsafe_allow_html=True)

        with v2:
            st.markdown(f'<div class="section-card"><div class="section-title">Variación por operador</div><div class="section-subtitle">Cambio de señal entre {_pi4} y {_pf4} · verde = mejoró · rojo = empeoró</div>', unsafe_allow_html=True)
            if not variation_operator.empty:
                ov = alt.Chart(variation_operator).mark_bar(cornerRadiusTopLeft=6,cornerRadiusTopRight=6).encode(
                    x=alt.X("Operador:N",title=None,sort="-y"),
                    y=alt.Y("Variacion_RSRP:Q",title="Variación (dBm)"),
                    color=alt.Color("Operador:N",scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()),range=list(OPERATOR_COLORS.values())),legend=None),
                    tooltip=[alt.Tooltip("Operador:N"),alt.Tooltip("RSRP_inicial:Q",title=f"Señal {_pi4}",format=".1f"),alt.Tooltip("RSRP_final:Q",title=f"Señal {_pf4}",format=".1f"),alt.Tooltip("Variacion_RSRP:Q",title="Variación",format="+.1f")]
                ).properties(height=280)
                zl = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(color="rgba(255,255,255,0.2)",strokeDash=[4,3]).encode(y="y:Q")
                st.altair_chart(style_chart(ov+zl), use_container_width=True, theme=None)
            else:
                st.info("Sin datos de variación por operador.")
            st.markdown('</div>', unsafe_allow_html=True)

        vd1,vd2 = st.columns(2,gap="large")
        with vd1:
            st.markdown(f'<div class="section-card"><div class="section-title">Top 10 — mayor mejora</div><div class="section-subtitle">CP donde la señal mejoró más entre {_pi4} y {_pf4}</div>', unsafe_allow_html=True)
            if not variation_cp.empty:
                mj = safe_round_columns(variation_cp.sort_values("Variacion_RSRP",ascending=False).head(10).copy(),["RSRP_inicial","RSRP_final","Variacion_RSRP"])
                st.dataframe(mj, use_container_width=True, height=280)
            else:
                st.info("Sin datos.")
            st.markdown('</div>', unsafe_allow_html=True)
        with vd2:
            st.markdown(f'<div class="section-card"><div class="section-title">Top 10 — mayor deterioro</div><div class="section-subtitle">CP donde la señal empeoró más — prioridad de revisión de red</div>', unsafe_allow_html=True)
            if not variation_cp.empty:
                dt = safe_round_columns(variation_cp.sort_values("Variacion_RSRP",ascending=True).head(10).copy(),["RSRP_inicial","RSRP_final","Variacion_RSRP"])
                st.dataframe(dt, use_container_width=True, height=280)
            else:
                st.info("Sin datos.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Conclusión
        _op_mejor = variation_operator.sort_values("Variacion_RSRP",ascending=False).iloc[0] if not variation_operator.empty else None
        _op_peor  = variation_operator.sort_values("Variacion_RSRP",ascending=True).iloc[0]  if not variation_operator.empty else None
        _concl_var = (
            f"Comparando {_pi4} con {_pf4}, la señal {'mejoró' if _vg4>=0 else 'se deterioró'} {fmt_var_dBm(abs(_vg4))} a nivel global. "
            + (f"{_op_mejor['Operador']} fue el operador con mayor mejora ({fmt_var_dBm(_op_mejor['Variacion_RSRP'])}), "
               f"mientras {_op_peor['Operador']} tuvo el mayor deterioro ({fmt_var_dBm(_op_peor['Variacion_RSRP'])}). " if _op_mejor is not None else "")
            + (f"El CP con mayor mejora fue {mayor_mejora['Codigo_postal']} ({fmt_var_dBm(mayor_mejora['Variacion_RSRP'])}) "
               f"y el de mayor deterioro fue {mayor_deterioro['Codigo_postal']} ({fmt_var_dBm(mayor_deterioro['Variacion_RSRP'])})." if mayor_mejora is not None else "")
        )
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(14,165,233,0.06),rgba(99,102,241,0.06));border:1px solid rgba(99,102,241,0.18);border-radius:18px;padding:16px 20px;margin-top:14px;">
            <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px;">Conclusión ejecutiva</div>
            <div style="font-size:.84rem;color:#E2E8F0;line-height:1.7;">{_concl_var}</div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — MERCADO
# Hilo conductor: señal y mercado a nivel de CP por operador — datos reales accionables
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    _biz5 = business_metrics.get("available",False)
    _lm5  = leader_market["Operador"] if leader_market is not None else "N/D"
    _la5  = leader_altas["Operador"]  if leader_altas  is not None else "N/D"
    _lmp5 = float(leader_market["Cuota_mercado_global"])      if leader_market is not None else 0
    _lap5 = float(leader_altas["Participacion_altas_global"]) if leader_altas  is not None else 0
    _lmc5 = OPERATOR_COLORS.get(_lm5,"#F8FAFC")
    _lac5 = OPERATOR_COLORS.get(_la5,"#F8FAFC")
    _vm5  = business_metrics.get("variation_market",np.nan)
    _va5  = business_metrics.get("variation_altas",np.nan)
    _gm5  = float(market_lead_gap) if pd.notna(market_lead_gap) else 0
    _rsk5 = len(risk_table) if risk_table is not None and not risk_table.empty else 0
    _opp5 = len(opportunity_table) if opportunity_table is not None and not opportunity_table.empty else 0

    if not _biz5:
        st.warning(business_metrics.get("message") or "Sin datos de mercado y captación disponibles.")
    else:
        # ── BLOQUE 1: Headline ejecutivo ──────────────────────────────────────
        _same5 = _lm5==_la5
        _gmc5  = "#22C55E" if _gm5>=15 else "#F59E0B" if _gm5>=5 else "#EF4444"
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(17,24,39,0.97),rgba(10,18,34,0.99));border:1px solid rgba(255,255,255,0.10);border-radius:24px;padding:22px 28px;margin-bottom:16px;">
            <div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px;">Posición competitiva en mercado y captación</div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px;">
                <div>
                    <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;margin-bottom:4px;">Líder de mercado</div>
                    <div style="font-size:1.2rem;font-weight:900;color:{_lmc5};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{_lm5}</div>
                    <div style="font-size:.68rem;color:#64748B;">{_lmp5:.1f}% cuota acumulada</div>
                    {_bar_op(_lmp5,_lmc5)}
                </div>
                <div>
                    <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;margin-bottom:4px;">Líder de captación</div>
                    <div style="font-size:1.2rem;font-weight:900;color:{_lac5};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{_la5}</div>
                    <div style="font-size:.68rem;color:#64748B;">{_lap5:.1f}% de las altas nuevas</div>
                    {_bar_op(_lap5,_lac5)}
                </div>
                <div>
                    <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;margin-bottom:4px;">Ventaja del líder</div>
                    <div style="font-size:1.6rem;font-weight:900;color:{_gmc5};">{_gm5:.1f} pp</div>
                    <div style="font-size:.68rem;color:#64748B;">{"Liderazgo sólido" if _gm5>=15 else "Liderazgo moderado" if _gm5>=5 else "Mercado disputado"}</div>
                </div>
                <div>
                    <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;margin-bottom:4px;">Focos identificados</div>
                    <div style="font-size:1.6rem;font-weight:900;color:{"#EF4444" if _rsk5>3 else "#F59E0B" if _rsk5>0 else "#22C55E"};">{_rsk5+_opp5}</div>
                    <div style="font-size:.68rem;color:#64748B;">{_rsk5} riesgos · {_opp5} oportunidades</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── BLOQUE 2: Ranking doble mercado vs captación ──────────────────────
        st.markdown('<div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;">Mercado vs captación por operador</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.74rem;color:#64748B;margin-bottom:8px;">Mercado = cuota acumulada · Captación = % de clientes nuevos · si captación supera mercado, ese operador gana participación activa</div>', unsafe_allow_html=True)
        if not market_operator.empty and not altas_operator.empty:
            _mkt5 = market_operator[["Operador","Cuota_mercado_global"]].copy()
            _alt5 = altas_operator[["Operador","Participacion_altas_global"]].copy()
            _rk5  = _mkt5.merge(_alt5,on="Operador",how="outer").fillna(0).sort_values("Cuota_mercado_global",ascending=False).reset_index(drop=True)
            for _, rr in _rk5.iterrows():
                _oc5 = OPERATOR_COLORS.get(rr["Operador"],"#64748B")
                _mv5 = float(rr.get("Cuota_mercado_global",0))
                _av5 = float(rr.get("Participacion_altas_global",0))
                _df5 = _av5-_mv5
                _dc5 = "#22C55E" if _df5>=0 else "#EF4444"
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:12px;background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:9px 14px;margin-bottom:6px;">
                    <div style="width:150px;flex-shrink:0;display:flex;align-items:center;gap:7px;">
                        <span style="width:9px;height:9px;border-radius:50%;background:{_oc5};display:inline-block;flex-shrink:0;"></span>
                        <span style="font-size:.78rem;font-weight:800;color:#F8FAFC;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{rr["Operador"]}</span>
                    </div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:.60rem;color:#64748B;margin-bottom:1px;">Mercado</div>
                        <div style="width:100%;height:6px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;"><div style="width:{min(_mv5,100):.1f}%;height:100%;background:{_oc5};border-radius:99px;opacity:.65;"></div></div>
                    </div>
                    <div style="width:46px;text-align:right;font-size:.90rem;font-weight:900;color:{_oc5};flex-shrink:0;">{_mv5:.1f}%</div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:.60rem;color:#64748B;margin-bottom:1px;">Captación</div>
                        <div style="width:100%;height:6px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;"><div style="width:{min(_av5,100):.1f}%;height:100%;background:{_oc5};border-radius:99px;opacity:.92;"></div></div>
                    </div>
                    <div style="width:46px;text-align:right;font-size:.90rem;font-weight:900;color:{_oc5};flex-shrink:0;">{_av5:.1f}%</div>
                    <div style="width:120px;text-align:right;font-size:.72rem;color:{_dc5};flex-shrink:0;font-weight:800;">{"▲ ganando" if _df5>=0 else "▼ perdiendo"} {abs(_df5):.1f} pp</div>
                </div>""", unsafe_allow_html=True)

        # ── BLOQUE 3: Evolución temporal ──────────────────────────────────────
        st.markdown('<div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:14px 0 8px 0;">Evolución en el tiempo</div>', unsafe_allow_html=True)
        t5c1,t5c2 = st.columns(2,gap="large")
        with t5c1:
            st.markdown('<div class="section-card"><div class="section-title">Cuota de mercado por periodo</div><div class="section-subtitle">Línea que sube = ganando mercado · línea que baja = cediendo</div>', unsafe_allow_html=True)
            if not market_time.empty and "Periodo_Mes" in market_time.columns and "Cuota_mercado" in market_time.columns:
                mc = alt.Chart(market_time).mark_line(point=True,strokeWidth=2.5).encode(
                    x=alt.X("Periodo_Mes:T",title=None),
                    y=alt.Y("Cuota_mercado:Q",title="Cuota de mercado (%)"),
                    color=alt.Color("Operador:N",scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()),range=list(OPERATOR_COLORS.values())),legend=alt.Legend(title="")),
                    tooltip=[alt.Tooltip("Operador:N"),alt.Tooltip("Periodo_Mes:T",title="Periodo"),alt.Tooltip("Cuota_mercado:Q",title="Cuota %",format=".1f"),alt.Tooltip("Mercado_total:Q",title="Total mercado",format=",")]
                ).properties(height=260)
                st.altair_chart(style_chart(mc), use_container_width=True, theme=None)
                if pd.notna(market_growth_pct):
                    _mgc = "#22C55E" if market_growth_pct>=0 else "#EF4444"
                    st.markdown(f'<div style="font-size:.68rem;color:#94A3B8;margin-top:4px;">Volumen: <span style="color:{_mgc};font-weight:800;">{"▲" if market_growth_pct>=0 else "▼"} {abs(market_growth_pct):.1f}%</span> entre {market_period_initial} y {market_period_final}</div>', unsafe_allow_html=True)
            else:
                st.info("Sin datos temporales de mercado.")
            st.markdown('</div>', unsafe_allow_html=True)
        with t5c2:
            st.markdown('<div class="section-card"><div class="section-title">Captación de altas por periodo</div><div class="section-subtitle">Participación en clientes nuevos · quién capta más cada periodo</div>', unsafe_allow_html=True)
            if not altas_time.empty and "Periodo_Mes" in altas_time.columns and "Participacion_altas" in altas_time.columns:
                ac = alt.Chart(altas_time).mark_line(point=True,strokeWidth=2.5).encode(
                    x=alt.X("Periodo_Mes:T",title=None),
                    y=alt.Y("Participacion_altas:Q",title="Participación altas (%)"),
                    color=alt.Color("Operador:N",scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()),range=list(OPERATOR_COLORS.values())),legend=alt.Legend(title="")),
                    tooltip=[alt.Tooltip("Operador:N"),alt.Tooltip("Periodo_Mes:T",title="Periodo"),alt.Tooltip("Participacion_altas:Q",title="%",format=".1f"),alt.Tooltip("Altas_total:Q",title="Altas",format=",")]
                ).properties(height=260)
                st.altair_chart(style_chart(ac), use_container_width=True, theme=None)
                if pd.notna(altas_growth_pct):
                    _agc = "#22C55E" if altas_growth_pct>=0 else "#EF4444"
                    st.markdown(f'<div style="font-size:.68rem;color:#94A3B8;margin-top:4px;">Altas totales: <span style="color:{_agc};font-weight:800;">{"▲" if altas_growth_pct>=0 else "▼"} {abs(altas_growth_pct):.1f}%</span> entre {altas_period_initial} y {altas_period_final}</div>', unsafe_allow_html=True)
            else:
                st.info("Sin datos temporales de altas.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── BLOQUE 4: Inteligencia competitiva — comparativo entre dos operadores ─
        if not territorial_cross.empty:
            st.markdown("""
            <div style="display:flex;align-items:center;gap:10px;margin:20px 0 10px 0;">
                <div style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></div>
                <div style="font-size:.66rem;font-weight:900;color:#64748B;text-transform:uppercase;letter-spacing:.4px;white-space:nowrap;padding:0 12px;">Comparativo directo entre dos operadores — CP a CP</div>
                <div style="flex:1;height:1px;background:rgba(255,255,255,0.08);"></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div style="font-size:.74rem;color:#64748B;margin-bottom:10px;">Selecciona dos operadores para ver CP a CP en qué zonas el segundo le está ganando al primero en mercado, captación o señal — incluso si el primero es globalmente dominante.</div>', unsafe_allow_html=True)

            # Prep data
            tc = territorial_cross.copy()
            tc["RSRP_mediana"]        = pd.to_numeric(tc["RSRP_mediana"],        errors="coerce")
            tc["Cuota_mercado"]       = pd.to_numeric(tc["Cuota_mercado"],       errors="coerce")
            tc["Participacion_altas"] = pd.to_numeric(tc["Participacion_altas"], errors="coerce") if "Participacion_altas" in tc.columns else np.nan

            _ops_avail = sorted(tc["Operador"].dropna().unique().tolist())

            # Two operator selectors
            sel_col1, sel_col2 = st.columns(2, gap="large")
            with sel_col1:
                _op_a = st.selectbox(
                    "Operador principal (analizar sus oportunidades)",
                    options=_ops_avail,
                    index=_ops_avail.index("Claro") if "Claro" in _ops_avail else 0,
                    key="op_a_sel"
                )
            with sel_col2:
                _remaining = [o for o in _ops_avail if o != _op_a]
                _op_b = st.selectbox(
                    "Operador comparador (el que puede estarle ganando terreno)",
                    options=_remaining,
                    index=0,
                    key="op_b_sel"
                )

            tc_a = tc[tc["Operador"] == _op_a].copy()
            tc_b = tc[tc["Operador"] == _op_b].copy()

            if not tc_a.empty and not tc_b.empty:
                # Join both on CP
                merge_cols = ["Codigo_postal"] + [c for c in ["LOCALIDAD","BARRIO"] if c in tc_a.columns]
                cp_pair = tc_a[merge_cols + [c for c in ["Cuota_mercado","Participacion_altas","RSRP_mediana","Buena_o_mejor","Critica","Mercado_total","Altas_total"] if c in tc_a.columns]].merge(
                    tc_b[["Codigo_postal"] + [c for c in ["Cuota_mercado","Participacion_altas","RSRP_mediana","Buena_o_mejor","Critica"] if c in tc_b.columns]],
                    on="Codigo_postal",
                    how="inner",
                    suffixes=(f"_{_op_a.replace(' ','_')}", f"_{_op_b.replace(' ','_')}")
                )

                _col_a_cuota = f"Cuota_mercado_{_op_a.replace(' ','_')}"
                _col_b_cuota = f"Cuota_mercado_{_op_b.replace(' ','_')}"
                _col_a_rsrp  = f"RSRP_mediana_{_op_a.replace(' ','_')}"
                _col_b_rsrp  = f"RSRP_mediana_{_op_b.replace(' ','_')}"
                _col_a_altas = f"Participacion_altas_{_op_a.replace(' ','_')}"
                _col_b_altas = f"Participacion_altas_{_op_b.replace(' ','_')}"

                # Compute gaps: positive = B is winning over A
                if _col_a_cuota in cp_pair.columns and _col_b_cuota in cp_pair.columns:
                    cp_pair["gap_cuota"]  = cp_pair[_col_b_cuota] - cp_pair[_col_a_cuota]
                if _col_a_rsrp  in cp_pair.columns and _col_b_rsrp  in cp_pair.columns:
                    cp_pair["gap_rsrp"]   = cp_pair[_col_b_rsrp]  - cp_pair[_col_a_rsrp]
                if _col_a_altas in cp_pair.columns and _col_b_altas in cp_pair.columns:
                    cp_pair["gap_altas"]  = cp_pair[_col_b_altas] - cp_pair[_col_a_altas]

                # Zones where B beats A in each dimension
                opp_cuota = cp_pair[cp_pair.get("gap_cuota",pd.Series(dtype=float)) > 0].sort_values("gap_cuota", ascending=False) if "gap_cuota" in cp_pair.columns else pd.DataFrame()
                opp_rsrp  = cp_pair[cp_pair.get("gap_rsrp", pd.Series(dtype=float)) > 3].sort_values("gap_rsrp",  ascending=False) if "gap_rsrp"  in cp_pair.columns else pd.DataFrame()
                opp_altas = cp_pair[cp_pair.get("gap_altas",pd.Series(dtype=float)) > 0].sort_values("gap_altas", ascending=False) if "gap_altas" in cp_pair.columns else pd.DataFrame()

                _n_cuota = len(opp_cuota)
                _n_rsrp  = len(opp_rsrp)
                _n_altas = len(opp_altas)

                # 3 KPIs
                st.markdown(f'<div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:8px;">{_op_b} le gana a {_op_a} en...</div>', unsafe_allow_html=True)
                k4a,k4b,k4c = st.columns(3, gap="medium")
                with k4a:
                    _cc = "#EF4444" if _n_cuota > 20 else "#F59E0B" if _n_cuota > 5 else "#22C55E"
                    st.markdown(f"""<div class="card" style="min-height:0;border-color:rgba(239,68,68,0.20);">
                        <div class="kpi-label">CP donde {_op_b} tiene más cuota de mercado</div>
                        <div class="kpi-value" style="color:{_cc};">{_n_cuota}</div>
                        <div class="kpi-sub">Zonas donde {_op_b} domina el mercado frente a {_op_a} — {"alta exposición" if _n_cuota>20 else "exposición moderada" if _n_cuota>5 else "exposición baja"}</div>
                    </div>""", unsafe_allow_html=True)
                with k4b:
                    _rc = "#EF4444" if _n_rsrp > 20 else "#F59E0B" if _n_rsrp > 5 else "#22C55E"
                    st.markdown(f"""<div class="card" style="min-height:0;border-color:rgba(239,68,68,0.20);">
                        <div class="kpi-label">CP donde {_op_b} tiene mejor señal</div>
                        <div class="kpi-value" style="color:{_rc};">{_n_rsrp}</div>
                        <div class="kpi-sub">Ventaja de señal &gt;3 dBm de {_op_b} sobre {_op_a} — riesgo de pérdida futura</div>
                    </div>""", unsafe_allow_html=True)
                with k4c:
                    _ac = "#EF4444" if _n_altas > 20 else "#F59E0B" if _n_altas > 5 else "#22C55E"
                    st.markdown(f"""<div class="card" style="min-height:0;border-color:rgba(239,68,68,0.20);">
                        <div class="kpi-label">CP donde {_op_b} capta más altas</div>
                        <div class="kpi-value" style="color:{_ac};">{_n_altas}</div>
                        <div class="kpi-sub">{_op_b} gana más clientes nuevos en estas zonas</div>
                    </div>""", unsafe_allow_html=True)

                # 3 tabs for each dimension
                dim_tab1, dim_tab2, dim_tab3 = st.tabs([
                    f"Cuota de mercado ({_n_cuota} CP)",
                    f"Señal RSRP ({_n_rsrp} CP)",
                    f"Captación altas ({_n_altas} CP)",
                ])

                def _build_display_cols(df, col_a_cuota, col_b_cuota, col_a_rsrp, col_b_rsrp, gap_col, extra_cols=None):
                    base = ["Codigo_postal"] + [c for c in ["LOCALIDAD","BARRIO"] if c in df.columns]
                    data_cols = [c for c in [col_a_cuota, col_b_cuota, col_a_rsrp, col_b_rsrp, gap_col] + (extra_cols or []) if c and c in df.columns]
                    show = df[base + data_cols].copy()
                    rename = {
                        "Codigo_postal":"CP","LOCALIDAD":"Localidad","BARRIO":"Barrio",
                        col_a_cuota:f"Cuota {_op_a} %",
                        col_b_cuota:f"Cuota {_op_b} %",
                        col_a_rsrp:f"Señal {_op_a} (dBm)",
                        col_b_rsrp:f"Señal {_op_b} (dBm)",
                        "gap_cuota":f"Ventaja {_op_b} (cuota pp)",
                        "gap_rsrp":f"Ventaja {_op_b} (señal dBm)",
                        "gap_altas":f"Ventaja {_op_b} (altas pp)",
                    }
                    show = safe_round_columns(show, [c for c in data_cols if c in show.columns])
                    return show.rename(columns={k:v for k,v in rename.items() if k in show.columns})

                with dim_tab1:
                    if not opp_cuota.empty:
                        st.markdown(f'<div style="font-size:.74rem;color:#64748B;margin:8px 0;">Zonas donde {_op_b} tiene mayor cuota de mercado que {_op_a}. Ordenadas por mayor ventaja del competidor.</div>', unsafe_allow_html=True)
                        _d1 = _build_display_cols(opp_cuota.head(25), _col_a_cuota, _col_b_cuota, _col_a_rsrp, _col_b_rsrp, "gap_cuota")
                        st.dataframe(_d1, use_container_width=True, height=340)
                        st.markdown(f'<div style="font-size:.66rem;color:#94A3B8;margin-top:3px;">{_n_cuota} CP donde {_op_b} supera a {_op_a} en cuota de mercado</div>', unsafe_allow_html=True)
                    else:
                        st.success(f"✅ {_op_a} supera a {_op_b} en cuota de mercado en todos los CP compartidos.")

                with dim_tab2:
                    if not opp_rsrp.empty:
                        st.markdown(f'<div style="font-size:.74rem;color:#64748B;margin:8px 0;">Zonas donde {_op_b} tiene señal RSRP más de 3 dBm mejor que {_op_a}. Estas zonas son riesgo futuro aunque hoy {_op_a} tenga mercado.</div>', unsafe_allow_html=True)
                        _d2 = _build_display_cols(opp_rsrp.head(25), _col_a_cuota, _col_b_cuota, _col_a_rsrp, _col_b_rsrp, "gap_rsrp")
                        st.dataframe(_d2, use_container_width=True, height=340)
                        st.markdown(f'<div style="font-size:.66rem;color:#94A3B8;margin-top:3px;">{_n_rsrp} CP donde {_op_b} tiene ventaja de señal superior a 3 dBm</div>', unsafe_allow_html=True)
                    else:
                        st.success(f"✅ {_op_a} tiene igual o mejor señal que {_op_b} en todos los CP compartidos.")

                with dim_tab3:
                    if not opp_altas.empty:
                        st.markdown(f'<div style="font-size:.74rem;color:#64748B;margin:8px 0;">Zonas donde {_op_b} capta más altas que {_op_a}. Captación = clientes nuevos que se van con el competidor.</div>', unsafe_allow_html=True)
                        _d3 = _build_display_cols(opp_altas.head(25), _col_a_cuota, _col_b_cuota, _col_a_rsrp, _col_b_rsrp, "gap_altas", [_col_a_altas, _col_b_altas])
                        st.dataframe(_d3, use_container_width=True, height=340)
                        st.markdown(f'<div style="font-size:.66rem;color:#94A3B8;margin-top:3px;">{_n_altas} CP donde {_op_b} capta más clientes nuevos que {_op_a}</div>', unsafe_allow_html=True)
                    else:
                        st.success(f"✅ {_op_a} capta más altas que {_op_b} en todos los CP compartidos.")

                # CP donde B gana en TODO — máxima urgencia
                _all_gaps = [c for c in ["gap_cuota","gap_rsrp","gap_altas"] if c in cp_pair.columns]
                if len(_all_gaps) >= 2:
                    _worst = cp_pair.copy()
                    for _g in _all_gaps:
                        _worst = _worst[_worst[_g] > 0]
                    if not _worst.empty:
                        st.markdown(f'<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.20);border-radius:14px;padding:12px 16px;margin-top:10px;"><div style="font-size:.64rem;font-weight:900;color:#FCA5A5;text-transform:uppercase;margin-bottom:5px;">Máxima urgencia para {_op_a}</div><div style="font-size:.80rem;color:#E2E8F0;">{len(_worst)} CP donde {_op_b} supera a {_op_a} en todas las dimensiones disponibles ({", ".join([g.replace("gap_","") for g in _all_gaps])}) simultáneamente — intervención prioritaria.</div></div>', unsafe_allow_html=True)

            else:
                st.info(f"No hay CP compartidos entre {_op_a} y {_op_b} en los datos visibles.")

        # ── BLOQUE 5: Variación de operadores si hay histórico ────────────────
        if not market_operator_delta.empty or not altas_operator_delta.empty:
            st.markdown('<div style="font-size:.66rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin:14px 0 8px 0;">¿Quién ganó y quién perdió en el periodo?</div>', unsafe_allow_html=True)
            t5c3,t5c4 = st.columns(2,gap="large")
            with t5c3:
                st.markdown('<div class="section-card"><div class="section-title">Variación de cuota de mercado</div><div class="section-subtitle">Cambio entre inicio y fin · verde = ganó · rojo = cedió</div>', unsafe_allow_html=True)
                if not market_operator_delta.empty:
                    _moc = alt.Chart(market_operator_delta).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                        x=alt.X("Operador:N",title=None,sort="-y"),
                        y=alt.Y("Variacion:Q",title="Variación (pp)"),
                        color=alt.Color("Operador:N",scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()),range=list(OPERATOR_COLORS.values())),legend=None),
                        tooltip=[alt.Tooltip("Operador:N"),alt.Tooltip("Valor_inicial:Q",format=".1f",title="Inicial %"),alt.Tooltip("Valor_final:Q",format=".1f",title="Final %"),alt.Tooltip("Variacion:Q",format="+.1f",title="Variación pp")]
                    ).properties(height=240)
                    _z0m = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(color="rgba(255,255,255,0.2)",strokeDash=[4,3]).encode(y="y:Q")
                    st.altair_chart(style_chart(_moc+_z0m), use_container_width=True, theme=None)
                else:
                    st.info("Sin datos.")
                st.markdown('</div>', unsafe_allow_html=True)
            with t5c4:
                st.markdown('<div class="section-card"><div class="section-title">Variación de captación</div><div class="section-subtitle">Cambio en % de altas · verde = gana captación · rojo = cede</div>', unsafe_allow_html=True)
                if not altas_operator_delta.empty:
                    _aoc = alt.Chart(altas_operator_delta).mark_bar(cornerRadiusTopLeft=5,cornerRadiusTopRight=5).encode(
                        x=alt.X("Operador:N",title=None,sort="-y"),
                        y=alt.Y("Variacion:Q",title="Variación (pp)"),
                        color=alt.Color("Operador:N",scale=alt.Scale(domain=list(OPERATOR_COLORS.keys()),range=list(OPERATOR_COLORS.values())),legend=None),
                        tooltip=[alt.Tooltip("Operador:N"),alt.Tooltip("Valor_inicial:Q",format=".1f",title="Inicial %"),alt.Tooltip("Valor_final:Q",format=".1f",title="Final %"),alt.Tooltip("Variacion:Q",format="+.1f",title="Variación pp")]
                    ).properties(height=240)
                    _z0a = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(color="rgba(255,255,255,0.2)",strokeDash=[4,3]).encode(y="y:Q")
                    st.altair_chart(style_chart(_aoc+_z0a), use_container_width=True, theme=None)
                else:
                    st.info("Sin datos.")
                st.markdown('</div>', unsafe_allow_html=True)

        # ── BLOQUE 6: Conclusión ejecutiva ────────────────────────────────────
        _same_leader = _lm5==_la5
        _concl_mkt = (
            f"{_lm5} lidera el mercado con {_lmp5:.1f}% de cuota acumulada"
            + (f" y también lidera la captación con {_lap5:.1f}% de las altas nuevas — posición dominante en ambos frentes." if _same_leader
               else f", mientras {_la5} lidera la captación con {_lap5:.1f}% de las altas — operadores distintos ganan en cada frente.")
            + f" La ventaja del líder es de {_gm5:.1f} pp — {'posición consolidada' if _gm5>=15 else 'liderazgo moderado con competencia activa' if _gm5>=5 else 'mercado muy disputado'}."
        )
        if not territorial_cross.empty and "tc_focal" in dir() and not tc_focal.empty:
            _concl_mkt += (
                f" El análisis competitivo por CP identifica {_n_opp} zonas de oportunidad donde {_sel_op} puede disputar mercado a la competencia"
                f" y {_n_risk} zonas en riesgo donde puede perder clientes por señal."
            )

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(14,165,233,0.06),rgba(99,102,241,0.06));border:1px solid rgba(99,102,241,0.18);border-radius:18px;padding:16px 20px;margin-top:14px;">
            <div style="font-size:.62rem;font-weight:900;color:#94A3B8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px;">Conclusión ejecutiva</div>
            <div style="font-size:.84rem;color:#E2E8F0;line-height:1.7;">{_concl_mkt}</div>
        </div>
        """, unsafe_allow_html=True)
