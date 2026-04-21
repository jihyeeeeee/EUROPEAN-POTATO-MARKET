import streamlit as st
import pandas as pd
import numpy as np
import datetime
from typing import Optional, Dict
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# --- Config & Initialization ---
st.set_page_config(
    page_title="The Terroir Archive | Potato Market Dashboard",
    page_icon="🥔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for "The Terroir Archive" Editorial Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;700;800&family=Public_Sans:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #4A5D23;
        --background: #fff8f3;
        --surface: #f9f9f6;
        --on-surface: #1f1b16;
        --accent: #a73a13;
    }

    .stApp {
        background-color: var(--background);
        font-family: 'Public Sans', sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: var(--surface);
        border-right: 1px solid #e8e8e5;
    }

    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--primary) !important;
        font-family: 'Manrope', sans-serif;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Manrope', sans-serif !important;
        color: var(--on-surface) !important;
    }

    .editorial-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 1rem 0;
        margin-bottom: 2rem;
        border-bottom: 2px solid var(--on-surface);
    }

    .editorial-label {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        color: #817567;
        margin-bottom: 0.5rem;
    }

    .hero-price {
        font-size: 4rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1;
        margin-bottom: 1rem;
    }

    .market-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 12px 40px rgba(26,28,27,0.04);
        border: 1px solid rgba(198, 200, 184, 0.15);
        transition: transform 0.2s;
    }

    .market-card:hover {
        transform: translateY(-4px);
    }

    .sparkline-container {
        display: flex;
        align-items: flex-end;
        gap: 2px;
        height: 40px;
        margin-top: 1rem;
    }

    .sparkline-bar {
        flex: 1;
        background: #d2c4b3;
        border-radius: 1px 1px 0 0;
    }

    .sparkline-bar.active {
        background: var(--primary);
    }

    .sparkline-bar.error {
        background: #ba1a1a;
    }

    .bento-news {
        background: #f0e7de;
        border-radius: 16px;
        overflow: hidden;
        display: flex;
        min-height: 400px;
    }

    .news-image {
        width: 50%;
        background-image: url('https://images.unsplash.com/photo-1518977676601-b53f02bad67b?auto=format&fit=crop&q=80&w=2670&ixlib=rb-4.0.3');
        background-size: cover;
        background-position: center;
        position: relative;
    }

    .news-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 2rem;
        background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
        color: white;
    }

    .report-preview {
        background: white;
        border: 1px solid #e8e8e5;
        border-radius: 16px;
        padding: 2rem;
        font-family: 'Public Sans', sans-serif;
        font-size: 14px;
        line-height: 1.8;
        color: #4f4538;
        min-height: 500px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 32px;
        border-bottom: 1px solid #e8e8e5;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 60px;
        background-color: transparent !important;
        border-radius: 0px;
        border-bottom: 2px solid transparent;
        color: #817567;
        font-weight: 700;
        font-size: 1.25rem;
        font-family: 'Manrope', sans-serif;
        padding: 0 8px;
    }

    .stTabs [aria-selected="true"] {
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary) !important;
    }

    .stButton>button {
        background: linear-gradient(135deg, #004b0f 0%, #0f651d 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
        padding: 0.75rem 1.5rem !important;
        font-family: 'Public Sans', sans-serif;
        transition: all 0.2s !important;
    }

    .stButton>button:hover {
        opacity: 0.9;
        transform: scale(0.98);
    }
    
    /* Metrics override */
    [data-testid="stMetricValue"] {
        font-family: 'Manrope', sans-serif !important;
        font-weight: 800 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sample Data Fallbacks ---
def get_sample_market_data():
    dates = pd.date_range(start="2024-12-01", periods=6, freq="ME").strftime("%Y-%m")
    data = {
        "date": list(dates),
        "price": [810, 820, 828, 840, 860, 858],
        "fx_rate": [1445, 1455, 1472, 1488, 1495, 1502],
        "scfi": [1850, 1890, 2010, 2175, 2280, 2210],
        "energy": [90, 92, 88, 95, 101, 98]
    }
    return pd.DataFrame(data)

SAMPLE_JRC_INSIGHTS = {
    "summary": "Recent rainfall deficits across NW Europe (Benelux, FR, DE) are pressuring yields. Soil moisture is 15% below average.",
    "weather": "Heatwave in Southern EU; Northern regions remain dry but seasonally cool.",
    "potato": "Planting 100% complete. Early growth stable but water stress critical variable.",
    "forecast": "Yield expectations cluster adjusted -3% MoM."
}

# --- AI Helper ---
def generate_report(product, tone, lang, market_data, jrc_text, user_notes):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found. Please set it in AI Studio Secrets."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        latest_data = market_data.iloc[-1].to_dict()
        prompt = f"""
        Analyze as a European analyst. Generate a {tone} market report for {product} in {lang}.
        CONTEXT: {jrc_text or str(SAMPLE_JRC_INSIGHTS)}
        KPIs: {latest_data}
        NOTES: {user_notes}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Failed: {str(e)}"

# --- UI Sidebar ---
with st.sidebar:
    st.markdown("""
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 2rem;'>
            <h1 style='margin:0; font-size: 1.25rem;'>TERROIR ARCHIVE</h1>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("ANALYSIS")
    prod_opt = st.selectbox("Market Asset", ["Potato Starch", "Tapioca Starch", "Corn Starch"])
    tone_opt = st.radio("Intelligence Level", ["Brief", "Detailed Analysis"], horizontal=True)
    lang_opt = st.selectbox("Preferred Dialect", ["Korean", "English"])
    
    st.divider()
    st.subheader("DATA INTAKE")
    pdf_file = st.file_uploader("Upload JRC Bulletin", type="pdf")
    csv_file = st.file_uploader("Upload Market Data", type="csv")
    
    if csv_file:
        df_market = pd.read_csv(csv_file)
    else:
        df_market = get_sample_market_data()

    st.divider()
    if st.button("EXECUTE ANALYSIS", use_container_width=True):
        st.session_state.generate_clicked = True

# --- Main Dashboard ---
cur = df_market.iloc[-1]
prev = df_market.iloc[-2]

# Editorial Header
st.markdown(f"""
    <div class="editorial-header">
        <h1 style='font-size: 1.5rem; color: var(--primary) !important; letter-spacing: 0.1em;'>THE TERROIR ARCHIVE</h1>
    </div>
""", unsafe_allow_html=True)

tab_dash, tab_data, tab_editor = st.tabs(["Dashboard", "Market Data", "Draft Editor"])

with tab_dash:
    # Hero Section
    st.markdown('<p class="editorial-label">Global Market Index</p>', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown(f'<h2 class="hero-price">Potatoes: €{cur["price"]:.2f}<span style="font-size: 1.5rem; color: #817567; margin-left: 8px;">/cwt</span></h2>', unsafe_allow_html=True)
    with h_col2:
        diff = ((cur['price'] / prev['price']) - 1) * 100
        color = "#4A5D23" if diff >= 0 else "#ba1a1a"
        st.markdown(f"""
            <div style="background: rgba(74, 93, 35, 0.05); padding: 1rem; border-radius: 12px; display: flex; align-items: center; gap: 12px;">
                <div style="background: {color}; color: white; padding: 8px; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;">↑</div>
                <div>
                    <p style="margin:0; font-weight: 800; color: {color};">{diff:+.1f}% Today</p>
                    <p style="margin:0; font-size: 10px; color: #817567;">Last sync: Just now</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Market Grid
    g1, g2, g3 = st.columns(3)
    
    def render_card(title, sub, val, color_class, change):
        bars = "".join([f'<div class="sparkline-bar {"active" if i > 3 else ""}"></div>' for i in range(10)])
        st.markdown(f"""
            <div class="market-card">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <h3 style="margin:0; font-size: 1.25rem;">{title}</h3>
                        <p style="margin:0; font-size: 0.75rem; color: #817567;">{sub}</p>
                    </div>
                    <span style="font-size: 0.75rem; font-weight: 700; color: {("#4A5D23" if change > 0 else "#ba1a1a")}">{change:+.1f}%</span>
                </div>
                <div style="font-size: 2rem; font-weight: 800; margin-top: 1rem;">{val}</div>
                <div class="sparkline-container">{bars}</div>
            </div>
        """, unsafe_allow_html=True)

    with g1:
        render_card("Price Dynamics", "Premium Fresh Market", f"€{cur['price']:.1f}", "active", (cur['price']/prev['price']-1)*100)
    with g2:
        render_card("FX Volatility", "EUR/KRW Pair", f"{cur['fx_rate']:.0f}₩", "active", (cur['fx_rate']/prev['fx_rate']-1)*100)
    with g3:
        render_card("Logistics Index", "SCFI Global Route", f"{cur['scfi']:.0f} pts", "active", (cur['scfi']/prev['scfi']-1)*100)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Bento News / Insight List
    b_left, b_right = st.columns([8, 4])
    
    with b_left:
        st.markdown(f"""
            <div class="bento-news">
                <div class="news-image">
                    <div class="news-overlay">
                        <span style="background: var(--primary); padding: 4px 12px; font-size: 10px; font-weight: 800; text-transform: uppercase;">Harvest Report</span>
                        <h3 style="color: white !important; margin-top: 12px;">EU Yield Outlook Decouples from 5Y Avg</h3>
                    </div>
                </div>
                <div style="width: 50%; padding: 2rem;">
                    <p class="editorial-label">Market Intelligence</p>
                    <div style="margin-bottom: 1.5rem;">
                        <p style="font-size: 10px; font-weight: 800; color: var(--primary); margin:0;">CROP HEALTH</p>
                        <h5 style="margin: 4px 0 0 0;">{SAMPLE_JRC_INSIGHTS['summary']}</h5>
                    </div>
                    <div style="margin-bottom: 1.5rem;">
                        <p style="font-size: 10px; font-weight: 800; color: var(--primary); margin:0;">REGIONAL DYNAMICS</p>
                        <h5 style="margin: 4px 0 0 0;">{SAMPLE_JRC_INSIGHTS['potato']}</h5>
                    </div>
                    <div style="margin-bottom: 1.5rem;">
                        <p style="font-size: 10px; font-weight: 800; color: var(--primary); margin:0;">LOGISTICS</p>
                        <h5 style="margin: 4px 0 0 0;">Global shipping rates stabilize amid EU export pressure.</h5>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with b_right:
        with st.container(border=True):
            st.markdown('<p class="editorial-label">Stored Inventory</p>', unsafe_allow_html=True)
            st.markdown('<h3 style="margin:0; font-size: 2.5rem;">42.8M <span style="font-size:1rem; color:#817567;">lbs</span></h3>', unsafe_allow_html=True)
            st.markdown("""
                <div style="width:100%; height:12px; background:#f0e7de; border-radius: 6px; margin: 12px 0;">
                    <div style="width:65%; height:100%; background:var(--primary); border-radius: 6px;"></div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('<p style="font-size: 11px; color:#817567;">Capacity utilize at 65%. Dynamic shift detected in Poland storage.</p>', unsafe_allow_html=True)
            
            st.divider()
            st.markdown("<h4 style='font-size: 1.1rem;'>Draft Intelligence</h4>", unsafe_allow_html=True)
            if 'report_text' not in st.session_state:
                st.session_state.report_text = "Analysis pending..."
            
            if st.session_state.get('generate_clicked'):
                with st.spinner("Decoding Intelligence..."):
                    st.session_state.report_text = generate_report(prod_opt, tone_opt, lang_opt, df_market, "", "")
                st.session_state.generate_clicked = False
                st.rerun()

            st.markdown(f'<div style="font-size: 12px; color: #4f4538; line-height: 1.6; max-height: 200px; overflow:hidden; opacity: 0.8;">{st.session_state.report_text[:300]}...</div>', unsafe_allow_html=True)
            if st.button("Open Full Report", use_container_width=True):
                # We can't switch tabs via button easily, but we can instruct
                st.toast("Switch to Draft Editor tab for the full report")

# Tab 2: Market Data
with tab_data:
    st.markdown('<p class="editorial-label">Historical Analytics</p>', unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    with d1:
        st.line_chart(df_market, x="date", y="price", color="#4A5D23")
    with d2:
        st.area_chart(df_market, x="date", y="scfi", color="#a73a13")
    
    st.divider()
    st.dataframe(df_market, use_container_width=True)

# Tab 3: Editor
with tab_editor:
    st.markdown('<p class="editorial-label">Intelligence Refinement</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="report-preview">{st.session_state.report_text}</div>', unsafe_allow_html=True)
    
    st.divider()
    col_e1, col_e2 = st.columns([2, 1])
    with col_e1:
        st.text_area("Observations Input", placeholder="Add manual signals to influence report generation...", height=100)
    with col_e2:
        st.download_button("Export as Manuscript", st.session_state.report_text, file_name="terroir_archive_report.txt", use_container_width=True)
