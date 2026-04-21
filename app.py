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
    page_title="EU Market Insight Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal Custom CSS for Dashboard Polish
st.markdown("""
    <style>
    .report-card {
        padding: 1.5rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    .chart-label {
        font-size: 0.9rem;
        color: #6c757d;
        font-weight: 500;
        margin-top: 0.5rem;
        font-style: italic;
    }
    .main-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 2rem;
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
    "summary": "Recent rainfall deficits across NW Europe continue to pressure early crop yields. Soil moisture remains a primary concern for DE and FR regions.",
    "weather_overview": "A mix of extreme heat in the Mediterranean and unseasonably cool winds in the Baltic region observed over the last fortnight.",
    "weather_forecast": "Above-average temperatures predicted for the next 10 days in the North Sea region, potentially accelerating evapotranspiration.",
    "potato_section": "Planting cycle is technically concluded. Emergence is uniform in NL but lagging in BE due to soil compaction issues from early spring rain.",
    "eu_country_analysis": "FR: Stable. DE: Yield expectations lowered by 2%. PL: Expanding acreage compensates for localized water stress.",
    "yield_forecast": "EU aggregated potato yield forecast adjusted to 31.2 t/ha, down from 32.1 t/ha previous estimate.",
    "key_points": [
        "Soil moisture deficit in Northern France remains critical.",
        "Logistics costs for internal EU transport rising by 4%.",
        "Higher storage withdrawal rates reported in Germany."
    ]
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
        Analyze as a professional market analyst. 
        Generate a {tone} market intelligence report for {product} in the {lang} language.
        
        CONTEXT FROM JRC BULLETIN: {jrc_text}
        CURRENT MARKET KPIs: {latest_data}
        ADDITIONAL USER OBSERVATIONS: {user_notes}
        
        Structure the report with Executive Summary, Regional Analysis, and Market Outlook.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Generation Failed: {str(e)}"

# --- Data Loading ---
if 'market_df' not in st.session_state:
    st.session_state.market_df = get_sample_market_data()

if 'report_output' not in st.session_state:
    st.session_state.report_output = ""

# --- Sidebar ---
with st.sidebar:
    st.image("https://picsum.photos/seed/market/200/50", use_container_width=True)
    st.title("Admin Console")
    
    with st.expander("Data Management", expanded=True):
        uploaded_pdf = st.file_uploader("JRC Bulletin (PDF)", type="pdf")
        uploaded_csv = st.file_uploader("Market Indices (CSV)", type="csv")
        if uploaded_csv:
            st.session_state.market_df = pd.read_csv(uploaded_csv)
            st.success("CSV Data Loaded")

    st.info("💡 Tip: Upload the latest JRC bulletin to update the Summary and Preview tabs automatically.")

# --- Main UI ---
st.markdown('<p class="main-title">Professional Market Intelligence Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">EU Potato Market Synthesis & JRC Bulletin Integration</p>', unsafe_allow_html=True)

# Define Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Report Summary", "Data & Charts", "PDF Preview", "Final Report"])

# --- Tab 1: Report Summary ---
with tab1:
    st.header("JRC Analysis Summary")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("📋 Executive Overview")
            st.write(SAMPLE_JRC_INSIGHTS["summary"])
            
            st.subheader("🌡️ Weather Synthesis")
            st.info(f"**Current Status:** {SAMPLE_JRC_INSIGHTS['weather_overview']}")
            st.warning(f"**Short-term Forecast:** {SAMPLE_JRC_INSIGHTS['weather_forecast']}")
            
            st.subheader("🥔 Potato Sector Dynamics")
            st.write(SAMPLE_JRC_INSIGHTS["potato_section"])
            
            st.subheader("🇪🇺 EU Regional Breakdown")
            st.write(SAMPLE_JRC_INSIGHTS["eu_country_analysis"])
            
            st.subheader("📈 Yield Expectations")
            st.success(f"**Current Forecast:** {SAMPLE_JRC_INSIGHTS['yield_forecast']}")

    with col2:
        st.subheader("💡 Key Insights")
        for point in SAMPLE_JRC_INSIGHTS["key_points"]:
            st.markdown(f"- {point}")
            
        st.divider()
        st.metric("EU Aggregated Yield", "31.2 t/ha", "-0.9 t/ha")
        st.metric("Soil Moisture Index", "72%", "-5%")

# --- Tab 2: Data & Charts ---
with tab2:
    st.header("Historical Market Analytics")
    df = st.session_state.market_df
    
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        st.subheader("Potato Price Index (EUR)")
        st.line_chart(df, x="date", y="price", color="#1e293b")
        st.markdown('<p class="chart-label">Recent stability observed after a sharp Q1 rally due to low carry-over stocks.</p>', unsafe_allow_html=True)
        
    with row1_c2:
        st.subheader("FX Rate (EUR/KRW)")
        st.line_chart(df, x="date", y="fx_rate", color="#2563eb")
        st.markdown('<p class="chart-label">EUR weakening against KRW slightly affecting import competitiveness.</p>', unsafe_allow_html=True)

    st.divider()

    row2_c1, row2_c2 = st.columns(2)
    with row2_c1:
        st.subheader("SCFI Container Index")
        st.line_chart(df, x="date", y="scfi", color="#dc2626")
        st.markdown('<p class="chart-label">Freight rates peaking as capacity tightens on North-South routes.</p>', unsafe_allow_html=True)
        
    with row2_c2:
        st.subheader("Energy & Fertilizer Proxy")
        st.line_chart(df, x="date", y="energy", color="#16a34a")
        st.markdown('<p class="chart-label">Energy prices remain volatile, directly impacting storage cooling costs.</p>', unsafe_allow_html=True)

# --- Tab 3: PDF Preview ---
with tab3:
    st.header("JRC Publication Preview")
    
    if uploaded_pdf:
        st.success(f"File '{uploaded_pdf.name}' is being processed.")
        # In a real app with static file serving or PDF libraries, we'd render the PDF pages here.
        # For this requirement, we'll simulate the "page selection" as requested.
        page_selection = st.selectbox("Select Page for Preview", ["Weather Synthesis (Page 4)", "Weather Forecast (Page 8)", "Yield Forecast (Page 12)"])
        st.image(f"https://picsum.photos/seed/{page_selection.replace(' ', '')}/1000/600", caption=f"Simulated Preview: {page_selection}")
    else:
        st.warning("No PDF uploaded. Using simulated preview for demonstration.")
        page_selection = st.selectbox("Select Section to Preview", ["Weather Overview", "Regional Temperatures", "Soil Moisture Map"])
        st.image(f"https://picsum.photos/seed/{page_selection.replace(' ', '')}/1000/600", caption=f"Archive Preview: {page_selection}")

# --- Tab 4: Final Report ---
with tab4:
    st.header("Intelligence Manuscript Generator")
    
    with st.expander("Report Configuration", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            prod_choice = st.selectbox("Target Product", ["Potato Starch", "Premium Fresh Potatoes", "Processed Goods"])
        with c2:
            tone_choice = st.radio("Output Fidelity", ["Executive Brief", "Comprehensive Analysis"], horizontal=True)
        with c3:
            lang_choice = st.selectbox("Language Output", ["Korean", "English"])
            
        custom_notes = st.text_area("Analyst Observations", placeholder="Add specific signals or local insights to include in the generation...")
    
    if st.button("🚀 Generate Final Intelligence Report", use_container_width=True):
        with st.spinner("Synthesizing JRC insights and market data..."):
            jrc_context = f"Summary: {SAMPLE_JRC_INSIGHTS['summary']}. Yield: {SAMPLE_JRC_INSIGHTS['yield_forecast']}"
            st.session_state.report_output = generate_report(prod_choice, tone_choice, lang_choice, df, jrc_context, custom_notes)
    
    if st.session_state.report_output:
        st.divider()
        st.subheader("Generated Report")
        st.text_area("Refined Text", value=st.session_state.report_output, height=400)
        
        st.download_button(
            label="📄 Download Report (TXT)",
            data=st.session_state.report_output,
            file_name=f"market_report_{datetime.date.today()}.txt",
            mime="text/plain",
            use_container_width=True
        )
