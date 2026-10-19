import streamlit as st

AMBER, GREEN, RED, BLUE = "#FFB000", "#00D26A", "#FF4D4D", "#4FC3F7"
COLORWAY = [AMBER, BLUE, GREEN, "#E040FB", RED, "#B0BEC5"]
MONO = "IBM Plex Mono, Consolas, monospace"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');
.stApp { font-family: 'IBM Plex Mono', Consolas, monospace; background: #000; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { padding: 0.6rem 1.4rem 2rem 1.4rem; max-width: 100%; }

.topbar { display:flex; align-items:center; gap:18px; border-bottom:2px solid #FFB000;
          padding:6px 0 8px 0; margin-bottom:8px; font-family:'IBM Plex Mono',Consolas,monospace; }
.brand { background:#FFB000; color:#000; font-weight:700; padding:3px 10px; letter-spacing:2px; font-size:16px; }
.tag { color:#FFB000; font-size:12px; letter-spacing:1.5px; }
.src { margin-left:auto; color:#8a8a8a; font-size:11px; }

.strip { display:flex; align-items:baseline; gap:16px; padding:8px 12px; background:#0b0b0b;
         border:1px solid #262626; margin:6px 0 10px 0; font-family:'IBM Plex Mono',Consolas,monospace; }
.tk { color:#FFB000; font-weight:700; font-size:20px; }
.nm { color:#fff; font-size:16px; }
.fy { margin-left:auto; color:#8a8a8a; font-size:11px; }

.kpi-row { display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin-bottom:10px; }
.kpi { background:#0b0b0b; border:1px solid #262626; border-left:3px solid #FFB000; padding:8px 12px;
       font-family:'IBM Plex Mono',Consolas,monospace; }
.kpi-l { color:#8a8a8a; font-size:10px; letter-spacing:1px; text-transform:uppercase; }
.kpi-v { color:#fff; font-size:22px; font-weight:600; margin-top:2px; }
.kpi-d { font-size:11px; margin-top:2px; color:#8a8a8a; }
.up { color:#00D26A; }
.down { color:#FF4D4D; }

.bb-table { width:100%; border-collapse:collapse; font-size:12px; font-family:'IBM Plex Mono',Consolas,monospace; }
.bb-table th { background:#1a1300; color:#FFB000; text-align:right; padding:5px 10px;
               border-bottom:1px solid #FFB000; font-weight:600; }
.bb-table td { text-align:right; padding:4px 10px; border-bottom:1px solid #161616; color:#e6e6e6; }
.bb-table th:first-child, .bb-table td:first-child { text-align:left; }
.bb-table td.up { color:#00D26A; }
.bb-table td.down { color:#FF4D4D; }
.bb-table tr:hover td { background:#111; }
.bb-table tr.sec td { background:#0f0f0f; color:#FFB000; font-weight:600; letter-spacing:1px;
                      text-align:left; border-bottom:1px solid #333; padding-top:9px; }

.stTabs [data-baseweb="tab-list"] { gap:0; border-bottom:1px solid #333; }
.stTabs [data-baseweb="tab"] { background:transparent; color:#8a8a8a; letter-spacing:1.5px;
                               font-size:12px; padding:8px 18px; }
.stTabs [aria-selected="true"] { color:#000 !important; background:#FFB000 !important; }
.stTabs [data-baseweb="tab-highlight"] { background:transparent !important; }
"""


def apply_theme() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)