import streamlit as st

"""
UI Theme — complete CSS injection for Streamlit with real custom styling.
Uses hardcoded hex colors (not CSS vars) for Streamlit compatibility,
and targets Streamlit's actual rendered DOM selectors.
"""

# Poppins from Google Fonts — loaded via <link> inside the style block works
# reliably in Streamlit's markdown renderer.
GOOGLE_FONT_LINK = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
"""

# ── Color palettes (hardcoded so CSS vars don't need :root to propagate) ──────
LIGHT = {
    "bg":           "#f0f2f8",
    "sidebar_bg":   "#ffffff",
    "surface":      "#ffffff",
    "surface2":     "#f4f6fb",
    "border":       "#e2e8f0",
    "text":         "#1a1d2e",
    "text_muted":   "#64748b",
    "primary":      "#6c63ff",
    "primary_dark": "#4f46e5",
    "primary_glow": "rgba(108,99,255,0.25)",
    "accent":       "#06b6d4",
    "success":      "#10b981",
    "warning":      "#f59e0b",
    "danger":       "#ef4444",
    "card_bg":      "#ffffff",
    "card_border":  "#e8eaf6",
}

DARK = {
    "bg":           "#0d1117",
    "sidebar_bg":   "#161b27",
    "surface":      "#1c2333",
    "surface2":     "#252d3d",
    "border":       "#30384d",
    "text":         "#e8eaf6",
    "text_muted":   "#8b95a8",
    "primary":      "#7c6fff",
    "primary_dark": "#6c63ff",
    "primary_glow": "rgba(124,111,255,0.30)",
    "accent":       "#22d3ee",
    "success":      "#34d399",
    "warning":      "#fbbf24",
    "danger":       "#f87171",
    "card_bg":      "#1c2333",
    "card_border":  "#30384d",
}


def _build_css(c: dict) -> str:
    """Build the full CSS string using hardcoded values from palette dict."""
    return f"""
/* ── Google Font application ── */
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"],
[data-testid="stMain"], .stApp, .main, .block-container,
[data-testid="stSidebar"], .css-1d391kg, section[data-testid="stSidebar"] {{
  font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}}

/* ── App background ── */
[data-testid="stApp"], [data-testid="stAppViewContainer"],
.stApp, body {{
  background-color: {c['bg']} !important;
}}

/* Main content area */
[data-testid="stMain"] > div, .block-container {{
  background-color: {c['bg']} !important;
  padding-top: 1.5rem !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div:first-child {{
  background-color: {c['sidebar_bg']} !important;
  border-right: 1px solid {c['border']} !important;
}}

/* ── Text colors ── */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{
  color: {c['text']} !important;
  font-family: 'Poppins', sans-serif !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em !important;
}}

p, .stMarkdown p {{
  color: {c['text']} !important;
  font-family: 'Poppins', sans-serif !important;
}}
/* IMPORTANT: Do not style every div/span/label globally.
   Streamlit uses those elements internally for uploaders, buttons,
   menus and inputs. Broad rules can make text overlap or disappear. */
.stMarkdown,
[data-testid="stMarkdownContainer"] {{
  font-family: 'Poppins', sans-serif !important;
  color: {c['text']} !important;
}}

.stMarkdown p,
.stMarkdown li,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {{
  font-family: 'Poppins', sans-serif !important;
  color: {c['text']} !important;
  line-height: 1.55 !important;
}}

/* ── Hide Streamlit default nav & branding ── */
#MainMenu, footer, header[data-testid="stHeader"] {{
  display: none !important;
}}

/* ── NORMAL STREAMLIT BUTTONS ── */
.stButton > button {{
  font-family: 'Poppins', sans-serif !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  letter-spacing: 0.02em !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 0.55rem 1.2rem !important;
  cursor: pointer !important;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
  background: linear-gradient(135deg, {c['primary']} 0%, {c['primary_dark']} 100%) !important;
  color: #ffffff !important;
  box-shadow: 0 2px 12px {c['primary_glow']} !important;
  width: 100% !important;
}}

.stButton > button:hover {{
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 0 6px 20px {c['primary_glow']} !important;
  background: linear-gradient(135deg, {c['primary_dark']} 0%, {c['primary']} 100%) !important;
}}

.stButton > button:active {{
  transform: translateY(0) scale(0.99) !important;
  box-shadow: 0 1px 6px {c['primary_glow']} !important;
}}

/* Sidebar nav buttons — these are overridden by custom HTML nav, but keep as fallback */
[data-testid="stSidebar"] .stButton > button {{
  background: transparent !important;
  color: {c['text_muted']} !important;
  box-shadow: none !important;
  text-align: left !important;
  border-radius: 10px !important;
  padding: 0.6rem 1rem !important;
  font-weight: 500 !important;
}}

[data-testid="stSidebar"] .stButton > button:hover {{
  background: {c['surface2']} !important;
  color: {c['primary']} !important;
  transform: translateX(4px) !important;
  box-shadow: none !important;
}}

/* ── Form inputs — explicit color+bg on every element to prevent invisible text ── */

/* Text inputs */
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] input:not([disabled]),
.stTextInput input {{
  background-color: {c['surface']} !important;
  color: {c['text']} !important;
  caret-color: {c['primary']} !important;
  border: 1.5px solid {c['border']} !important;
  border-radius: 10px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  padding: 10px 14px !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}}
[data-testid="stTextInput"] input::placeholder {{
  color: {c['text_muted']} !important;
  opacity: 1 !important;
}}

/* Number inputs */
[data-testid="stNumberInput"] input,
[data-testid="stNumberInput"] input:not([disabled]),
.stNumberInput input {{
  background-color: {c['surface']} !important;
  color: {c['text']} !important;
  caret-color: {c['primary']} !important;
  border: 1.5px solid {c['border']} !important;
  border-radius: 10px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  padding: 10px 14px !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}}

/* Textarea */
[data-testid="stTextArea"] textarea,
[data-testid="stTextArea"] textarea:not([disabled]),
.stTextArea textarea {{
  background-color: {c['surface']} !important;
  color: {c['text']} !important;
  caret-color: {c['primary']} !important;
  border: 1.5px solid {c['border']} !important;
  border-radius: 10px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  padding: 10px 14px !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}}
[data-testid="stTextArea"] textarea::placeholder {{
  color: {c['text_muted']} !important;
  opacity: 1 !important;
}}

/* Focus states */
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
  border-color: {c['primary']} !important;
  box-shadow: 0 0 0 3px {c['primary_glow']} !important;
  outline: none !important;
  background-color: {c['surface']} !important;
  color: {c['text']} !important;
}}

/* Selectbox — BaseUI / Streamlit selectbox container and value text */
[data-testid="stSelectbox"] > div > div,
[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div > div {{
  background-color: {c['surface']} !important;
  color: {c['text']} !important;
  border: 1.5px solid {c['border']} !important;
  border-radius: 10px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
}}
/* The actual selected value text inside selectbox */
[data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSelectbox"] [data-baseweb="select"] div span,
[data-testid="stSelectbox"] [class*="ValueContainer"] span,
[data-testid="stSelectbox"] [class*="singleValue"] {{
  color: {c['text']} !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
}}
/* Dropdown popover list */
[data-baseweb="popover"] ul,
[data-baseweb="popover"] li,
[data-baseweb="menu"] li {{
  background-color: {c['surface']} !important;
  color: {c['text']} !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
}}
[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover {{
  background-color: {c['surface2']} !important;
}}
/* Selectbox focus/hover border */
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"]:hover {{
  border-color: {c['primary']} !important;
}}

/* ── Expander — safe layout ── */
[data-testid="stExpander"] {{
  background: {c['surface']} !important;
  border: 1px solid {c['border']} !important;
  border-radius: 12px !important;
  overflow: visible !important;
}}

[data-testid="stExpander"] summary {{
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
  min-height: 48px !important;
  box-sizing: border-box !important;
  padding: 12px 16px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  line-height: 1.4 !important;
  color: {c['text']} !important;
  white-space: normal !important;
  overflow: visible !important;
}}

[data-testid="stExpander"] summary > div {{
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
  min-width: 0 !important;
  gap: 8px !important;
}}

[data-testid="stExpander"] summary span {{
  font-family: 'Poppins', sans-serif !important;
  font-size: 14px !important;
  line-height: 1.4 !important;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
}}

/* ── File uploader — do not inherit normal button styling ── */
[data-testid="stFileUploader"] {{
  width: 100% !important;
  box-sizing: border-box !important;
  overflow: visible !important;
  background: {c['surface2']} !important;
  border: 2px dashed {c['border']} !important;
  border-radius: 14px !important;
  padding: 1rem !important;
  transition: border-color 0.2s ease !important;
}}

[data-testid="stFileUploader"]:hover {{
  border-color: {c['primary']} !important;
}}

[data-testid="stFileUploaderDropzone"] {{
  width: 100% !important;
  min-height: 78px !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  overflow: visible !important;
}}

[data-testid="stFileUploader"] button {{
  width: auto !important;
  min-width: 120px !important;
  max-width: 240px !important;
  min-height: 42px !important;
  height: auto !important;
  margin: 0 !important;
  padding: 9px 18px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  box-sizing: border-box !important;
  border-radius: 9px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  line-height: 1.3 !important;
  white-space: nowrap !important;
  overflow: visible !important;
  text-overflow: clip !important;
  transform: none !important;
}}

[data-testid="stFileUploader"] button span {{
  display: inline-block !important;
  width: auto !important;
  max-width: none !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  line-height: 1.3 !important;
  white-space: nowrap !important;
  overflow: visible !important;
  text-overflow: clip !important;
}}

[data-testid="stFileUploader"] svg {{
  flex-shrink: 0 !important;
  width: 18px !important;
  height: 18px !important;
}}

/* Date input */
[data-testid="stDateInput"] input {{
  background-color: {c['surface']} !important;
  color: {c['text']} !important;
  border: 1.5px solid {c['border']} !important;
  border-radius: 10px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  padding: 10px 14px !important;
}}

/* Chat input */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInputTextArea"] textarea {{
  background-color: {c['surface']} !important;
  color: {c['text']} !important;
  caret-color: {c['primary']} !important;
  border: 1.5px solid {c['border']} !important;
  border-radius: 10px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
}}

/* Number input stepper buttons */
[data-testid="stNumberInput"] button {{
  background-color: {c['surface2']} !important;
  color: {c['text']} !important;
  border: none !important;
  border-radius: 6px !important;
}}

/* Form label text */
[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
[data-testid="stDateInput"] label {{
  color: {c['text']} !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  margin-bottom: 4px !important;
}}

/* ── Tabs — pill switcher with smooth active highlight ── */
[data-testid="stTabs"] {{
  margin-bottom: 8px !important;
}}
[data-testid="stTabs"] [role="tablist"] {{
  background: {c['surface2']} !important;
  border-radius: 14px !important;
  padding: 5px 6px !important;
  border: 1px solid {c['border']} !important;
  gap: 4px !important;
  display: flex !important;
}}
[data-testid="stTabs"] button[role="tab"] {{
  font-family: 'Poppins', sans-serif !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  color: {c['text_muted']} !important;
  border-radius: 10px !important;
  border: none !important;
  padding: 8px 20px !important;
  transition: all 0.18s ease !important;
  background: transparent !important;
  box-shadow: none !important;
  transform: none !important;
  flex: 1 !important;
  white-space: nowrap !important;
}}
[data-testid="stTabs"] button[role="tab"]:hover {{
  background: {c['surface']} !important;
  color: {c['text']} !important;
  transform: none !important;
  box-shadow: none !important;
}}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
  color: #ffffff !important;
  background: linear-gradient(135deg, {c['primary']} 0%, {c['primary_dark']} 100%) !important;
  box-shadow: 0 2px 10px {c['primary_glow']} !important;
  font-weight: 600 !important;
  transform: none !important;
}}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]:hover {{
  background: linear-gradient(135deg, {c['primary_dark']} 0%, {c['primary']} 100%) !important;
  color: #ffffff !important;
}}
/* Remove Streamlit's default red tab underline */
[data-testid="stTabs"] button[role="tab"]::after,
[data-testid="stTabs"] button[role="tab"]::before {{
  display: none !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
  display: none !important;
}}

  line-height: 1.4 !important;
}}

/* ── DataFrames ── */
[data-testid="stDataFrame"] {{
  border-radius: 14px !important;
  overflow: hidden !important;
  border: 1px solid {c['border']} !important;
}}

/* ── Toggle/checkbox ── */
[data-testid="stToggle"] label {{
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  color: {c['text']} !important;
  font-weight: 500 !important;
}}

/* ── Metric widget — hidden because we use custom cards ── */
[data-testid="metric-container"] {{
  display: none !important;
}}

/* ── Alert boxes — styled, contained, readable ── */
[data-testid="stAlert"] {{
  border-radius: 12px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  padding: 14px 18px !important;
  max-width: 100% !important;
  word-break: break-word !important;
  overflow-wrap: break-word !important;
  line-height: 1.6 !important;
}}
/* Error alert */
[data-testid="stAlert"][data-baseweb="notification"][kind="error"],
[data-testid="stAlertContentError"],
div[data-testid="stAlert"].element-container {{
  border: 1px solid rgba(239,68,68,0.35) !important;
  border-left: 4px solid #ef4444 !important;
  background: rgba(239,68,68,0.06) !important;
}}
/* Success alert */
[data-testid="stAlertContentSuccess"] {{
  border: 1px solid rgba(16,185,129,0.35) !important;
  border-left: 4px solid #10b981 !important;
  background: rgba(16,185,129,0.06) !important;
}}
/* Info alert */
[data-testid="stAlertContentInfo"] {{
  border: 1px solid rgba(108,99,255,0.25) !important;
  border-left: 4px solid {c['primary']} !important;
  background: rgba(108,99,255,0.06) !important;
}}
/* Warning alert */
[data-testid="stAlertContentWarning"] {{
  border: 1px solid rgba(245,158,11,0.35) !important;
  border-left: 4px solid #f59e0b !important;
  background: rgba(245,158,11,0.06) !important;
}}
/* Alert text must be readable */
[data-testid="stAlert"] p,
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] {{
  color: {c['text']} !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  word-break: break-word !important;
  line-height: 1.6 !important;
}}

/* ── Scrollbars ── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {c['surface2']}; border-radius: 3px; }}
::-webkit-scrollbar-thumb {{ background: {c['border']}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {c['text_muted']}; }}

/* ── Dividers ── */
hr {{ border: none; border-top: 1px solid {c['border']}; margin: 1.5rem 0; }}

/* ── Plotly charts ── */
.js-plotly-plot, .js-plotly-plot .plotly, .js-plotly-plot .bg {{
  background: transparent !important;
}}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {{
  background: {c['surface']} !important;
  from {{ opacity: 0; }}
  to   {{ opacity: 1; }}
}}
@keyframes pulse {{
  0%, 100% {{ opacity: 1; transform: scale(1); }}
  50%       {{ opacity: 0.7; transform: scale(1.06); }}
}}
@keyframes spin {{
  from {{ transform: rotate(0deg); }}
  to   {{ transform: rotate(360deg); }}
}}
@keyframes popIn {{
  0%  {{ opacity: 0; transform: scale(0.6); }}
  70% {{ transform: scale(1.08); }}
  100%{{ opacity: 1; transform: scale(1); }}
}}
@keyframes glowPulse {{
  0%, 100% {{ box-shadow: 0 0 0 2px {c['primary_glow']}; }}
  50%       {{ box-shadow: 0 0 0 8px {c['primary_glow']}, 0 0 20px {c['primary_glow']}; }}
}}
@keyframes slideInLog {{
  from {{ opacity: 0; transform: translateX(-10px); }}
  to   {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes shimmer {{
  0%   {{ background-position: -400px 0; }}
  100% {{ background-position: 400px 0; }}
}}
@keyframes dotBounce {{
  0%, 80%, 100% {{ transform: translateY(0); opacity: 0.5; }}
  40%           {{ transform: translateY(-7px); opacity: 1; }}
}}

/* ── Metric cards (custom HTML) ── */
.xp-card {{
  background: {c['card_bg']};
  border: 1px solid {c['card_border']};
  border-radius: 18px;
  padding: 20px 22px 18px;
  box-shadow: 0 2px 16px rgba(108,99,255,0.07), 0 1px 4px rgba(0,0,0,0.05);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
  animation: fadeInUp 0.5s ease both;
  position: relative;
  overflow: hidden;
}}
.xp-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: 18px 18px 0 0;
}}
.xp-card:hover {{
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(108,99,255,0.14), 0 2px 8px rgba(0,0,0,0.08);
}}
.xp-card .xp-icon {{
  width: 44px; height: 44px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  margin-bottom: 14px;
}}
.xp-card .xp-label {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: {c['text_muted']};
  margin-bottom: 4px;
  font-family: 'Poppins', sans-serif;
}}
.xp-card .xp-value {{
  font-size: 28px;
  font-weight: 700;
  color: {c['text']};
  letter-spacing: -0.03em;
  line-height: 1.1;
  font-family: 'Poppins', sans-serif;
}}
.xp-card .xp-sub {{
  font-size: 12px;
  color: {c['text_muted']};
  margin-top: 5px;
  font-family: 'Poppins', sans-serif;
}}

/* ── Pipeline ── */
.xp-pipeline {{
  display: flex;
  align-items: center;
  padding: 18px 12px 10px;
  gap: 0;
  background: {c['surface']};
  border: 1px solid {c['border']};
  border-radius: 16px;
  margin: 12px 0;
  overflow-x: auto;
}}
.xp-node {{
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 100px;
  flex: 1;
}}
.xp-node-icon {{
  width: 54px; height: 54px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  font-weight: 700;
  transition: all 0.35s ease;
  position: relative;
}}
.xp-node-label {{
  margin-top: 8px;
  font-size: 10px;
  font-weight: 600;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: {c['text_muted']};
  font-family: 'Poppins', sans-serif;
}}
/* waiting */
.xp-waiting .xp-node-icon {{
  background: {c['surface2']};
  color: {c['text_muted']};
  border: 2px solid {c['border']};
}}
/* running */
.xp-running .xp-node-icon {{
  background: rgba(108,99,255,0.12);
  color: {c['primary']};
  border: 2px solid {c['primary']};
  animation: glowPulse 1.1s ease-in-out infinite;
}}
/* done */
.xp-done .xp-node-icon {{
  background: rgba(16,185,129,0.12);
  color: {c['success']};
  border: 2px solid {c['success']};
  animation: popIn 0.4s ease both;
}}
/* connector */
.xp-connector {{
  flex: 1;
  height: 3px;
  background: {c['border']};
  position: relative;
  overflow: hidden;
  min-width: 16px;
  margin-top: -28px;
}}
.xp-connector-fill {{
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, {c['success']}, {c['accent']});
  transition: width 0.7s ease;
  border-radius: 2px;
}}
.xp-connector-fill.done {{ width: 100%; }}
/* activity log */
.xp-log {{
  background: {c['surface2']};
  border: 1px solid {c['border']};
  border-radius: 12px;
  padding: 12px 16px;
  margin-top: 12px;
  max-height: 160px;
  overflow-y: auto;
  font-size: 12.5px;
  font-family: 'Poppins', monospace;
}}
.xp-log-line {{
  padding: 3px 0;
  animation: slideInLog 0.3s ease both;
  border-bottom: 1px solid {c['border']};
  color: {c['text_muted']};
}}
.xp-log-line:last-child {{ border-bottom: none; }}
.xp-log-line.success {{ color: {c['success']}; }}
.xp-log-line.warning {{ color: {c['warning']}; }}
.xp-log-line.running {{ color: {c['primary']}; }}

/* ── Budget bars ── */
.xp-budget-bar-track {{
  background: {c['surface2']};
  border-radius: 6px;
  height: 10px;
  overflow: hidden;
  margin: 5px 0;
}}
.xp-budget-bar-fill {{
  height: 100%;
  border-radius: 6px;
  transition: width 1.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}}

/* ── Anomaly card ── */
.xp-anomaly {{
  background: {c['surface']};
  border: 1px solid rgba(239,68,68,0.35);
  border-left: 4px solid #ef4444;
  border-radius: 14px;
  padding: 16px 20px;
  margin: 10px 0;
  animation: fadeInUp 0.4s ease both;
}}

/* ── Empty state ── */
.xp-empty {{
  background: {c['surface']};
  border: 1px solid {c['border']};
  border-radius: 20px;
  padding: 48px 40px;
  text-align: center;
  animation: fadeInUp 0.6s ease both;
}}
.xp-empty .xp-empty-icon {{
  font-size: 52px;
  margin-bottom: 16px;
  display: block;
}}
.xp-empty h3 {{
  font-size: 20px !important;
  font-weight: 700 !important;
  color: {c['text']} !important;
  margin: 0 0 8px !important;
}}
.xp-empty p {{
  font-size: 14px !important;
  color: {c['text_muted']} !important;
  margin: 0 0 28px !important;
  line-height: 1.6 !important;
}}
.xp-btn-primary {{
  display: inline-block;
  background: linear-gradient(135deg, {c['primary']} 0%, {c['primary_dark']} 100%);
  color: #fff !important;
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  font-weight: 600;
  padding: 12px 28px;
  border-radius: 12px;
  text-decoration: none;
  box-shadow: 0 4px 16px {c['primary_glow']};
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
  border: none;
  margin: 4px 6px;
}}
.xp-btn-primary:hover {{
  transform: translateY(-2px);
  box-shadow: 0 8px 24px {c['primary_glow']};
}}

/* ── Thinking dots ── */
.xp-thinking {{ display: inline-flex; gap: 5px; align-items: center; padding: 4px 0; }}
.xp-thinking span {{
  width: 7px; height: 7px;
  background: {c['primary']};
  border-radius: 50%;
  animation: dotBounce 1.4s ease infinite;
}}
.xp-thinking span:nth-child(2) {{ animation-delay: 0.2s; }}
.xp-thinking span:nth-child(3) {{ animation-delay: 0.4s; }}

/* ── Sidebar nav items (HTML-based) ── */
.xp-nav-item {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: {c['text_muted']};
  transition: all 0.18s ease;
  margin: 2px 0;
  border: none;
  background: transparent;
  text-decoration: none;
  width: 100%;
  border-left: 3px solid transparent;
}}
.xp-nav-item:hover {{
  background: {c['surface2']};
  color: {c['primary']};
  transform: translateX(3px);
}}
.xp-nav-item.active {{
  background: rgba(108,99,255,0.10);
  color: {c['primary']};
  border-left: 3px solid {c['primary']};
  font-weight: 600;
}}
.xp-nav-sep {{
  height: 1px;
  background: linear-gradient(90deg, transparent, {c['border']}, transparent);
  margin: 10px 0;
}}
.xp-sidebar-logo {{
  text-align: center;
  padding: 20px 16px 14px;
}}
.xp-sidebar-logo .logo-icon {{
  font-size: 38px;
  line-height: 1;
  margin-bottom: 6px;
}}
.xp-sidebar-logo .logo-title {{
  font-size: 15px;
  font-weight: 700;
  color: {c['text']};
  font-family: 'Poppins', sans-serif;
  letter-spacing: -0.01em;
}}
.xp-sidebar-logo .logo-sub {{
  font-size: 10px;
  font-weight: 500;
  color: {c['text_muted']};
  font-family: 'Poppins', sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 2px;
}}
.xp-sidebar-badge {{
  display: inline-block;
  background: linear-gradient(135deg, {c['primary']}, {c['accent']});
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 8px;
  margin-left: auto;
  letter-spacing: 0.05em;
}}

/* Agent status dots */
.xp-dot {{
  display: inline-block;
  width: 9px; height: 9px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}}
.xp-dot.active {{
  background: {c['success']};
  box-shadow: 0 0 6px {c['success']};
  animation: pulse 2s ease-in-out infinite;
}}
.xp-dot.idle {{ background: {c['text_muted']}; opacity: 0.5; }}

/* Section header */
.xp-section-header {{
  animation: fadeInUp 0.5s ease both;
  margin-bottom: 22px;
  padding-bottom: 14px;
  border-bottom: 1px solid {c['border']};
}}
.xp-section-header h2 {{
  font-size: 22px !important;
  font-weight: 700 !important;
  color: {c['text']} !important;
  margin: 0 0 4px !important;
  letter-spacing: -0.02em !important;
}}
.xp-section-header p {{
  font-size: 13px !important;
  color: {c['text_muted']} !important;
  margin: 0 !important;
}}

/* Privacy notice */
.xp-privacy {{
  background: rgba(108,99,255,0.06);
  border: 1px solid rgba(108,99,255,0.18);
  border-radius: 10px;
  padding: 10px 14px;
  margin: 12px 0 6px;
  font-size: 11.5px;
  color: {c['text_muted']};
  font-family: 'Poppins', sans-serif;
  line-height: 1.5;
}}

/* Info/tip boxes */
.xp-tip {{
  background: {c['surface2']};
  border: 1px solid {c['border']};
  border-left: 3px solid {c['primary']};
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 13px;
  color: {c['text_muted']};
  margin: 12px 0;
  font-family: 'Poppins', sans-serif;
}}

/* Warning box */
.xp-warn {{
  background: rgba(245,158,11,0.06);
  border: 1px solid rgba(245,158,11,0.25);
  border-left: 3px solid {c['warning']};
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 13px;
  color: {c['text_muted']};
  margin: 12px 0;
  font-family: 'Poppins', sans-serif;
}}

/* AI insight box */
.xp-ai-box {{
  background: {c['surface']};
  border: 1px solid {c['border']};
  border-left: 4px solid {c['primary']};
  border-radius: 12px;
  padding: 18px 22px;
  font-size: 14px;
  line-height: 1.75;
  color: {c['text']};
  font-family: 'Poppins', sans-serif;
  margin: 8px 0;
}}

/* Tag badges */
.xp-tag-calc {{
  background: #e0f2fe;
  color: #0369a1;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
  margin-right: 4px;
  font-family: 'Poppins', sans-serif;
}}
.xp-tag-ai {{
  background: #f3e8ff;
  color: #7c3aed;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
  margin-right: 4px;
  font-family: 'Poppins', sans-serif;
}}
"""


def inject_theme(dark_mode: bool = False) -> str:
    """Return the full HTML+CSS injection string."""
    c = DARK if dark_mode else LIGHT
    css = _build_css(c)
    return f"""
{GOOGLE_FONT_LINK}
<style>
{css}
</style>
"""


CATEGORY_COLORS = {
    "Food":           "#f97316",
    "Travel":         "#3b82f6",
    "Shopping":       "#8b5cf6",
    "Utilities":      "#14b8a6",
    "Healthcare":     "#ef4444",
    "Education":      "#6366f1",
    "Entertainment":  "#ec4899",
    "Office":         "#64748b",
    "Rent":           "#f59e0b",
    "Transportation": "#0ea5e9",
    "Other":          "#94a3b8",
    "Uncategorized":  "#94a3b8",
}
