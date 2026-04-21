import streamlit as st
import pandas as pd
import numpy as np
import datetime
from typing import Optional, Dict
import google.generativeai as genai
import os
from dotenv import load_dotenv
from pypdf import PdfReader

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

# Initialize Session State
if 'market_df' not in st.session_state:
    dates = pd.date_range(start="2024-12-01", periods=6, freq="ME").strftime("%Y-%m")
    st.session_state.market_df = pd.DataFrame({
        "date": list(dates),
        "price": [810, 820, 828, 840, 860, 858],
        "fx_rate": [1445, 1455, 1472, 1488, 1495, 1502],
        "scfi": [1850, 1890, 2010, 2175, 2280, 2210],
        "energy": [90, 92, 88, 95, 101, 98]
    })

if 'jrc_data' not in st.session_state:
    st.session_state.jrc_data = {
        "summary": "Recent rainfall deficits across NW Europe continue to pressure early crop yields.",
        "weather_overview": "A mix of extreme heat in the Mediterranean and unseasonably cool winds in the Baltic region.",
        "weather_forecast": "Above-average temperatures predicted for the next 10 days.",
        "potato_section": "Planting cycle is technically concluded. Emergence is uniform in NL.",
        "eu_country_analysis": "FR: Stable. DE: Yield expectations lowered. PL: Expanding acreage.",
        "yield_forecast": "EU aggregated potato yield forecast adjusted to 31.2 t/ha.",
        "key_points": [
            "Soil moisture deficit in Northern France remains critical.",
            "Logistics costs for internal EU transport rising.",
            "Higher storage withdrawal rates reported in Germany."
        ]
    }

if 'report_output' not in st.session_state:
    st.session_state.report_output = ""

# --- AI Helper Functions ---
def extract_jrc_insights(pdf_file):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API Key missing.")
        return None
    
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages[:10]: # Process first 10 pages for cost/speed
            text += page.extract_text()
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Extract agricultural intelligence from this JRC JARS Bulletin text.
        Return ONLY a JSON object with these keys: 
        summary, weather_overview, weather_forecast, potato_section, eu_country_analysis, yield_forecast, key_points (list of strings).
        
        TEXT:
        {text[:10000]}
        """
        response = model.generate_content(prompt)
        # Attempt to parse json from response
        import json
        import re
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        st.error(f"Failed to process PDF: {str(e)}")
        return None

def generate_report(product, tone, lang, market_data, jrc_text, user_notes):
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    latest_data = market_data.iloc[-1].to_dict()
    prompt = f"""
    Analyze as a professional market analyst. 
    Generate a {tone} market intelligence report for {product} in the {lang} language.
    CONTEXT: {jrc_text}
    MARKET KPIs: {latest_data}
    NOTES: {user_notes}
    """
    response = model.generate_content(prompt)
    return response.text

# --- Sidebar UI ---
with st.sidebar:
    st.title("Admin Console")
    
    with st.expander("PDF Intelligence Update", expanded=True):
        uploaded_pdf = st.file_uploader("Upload JRC Bulletin", type="pdf")
        if uploaded_pdf:
            if st.button("Extract Intelligence from PDF", use_container_width=True):
                with st.spinner("Decoding Bulletin..."):
                    new_data = extract_jrc_insights(uploaded_pdf)
                    if new_data:
                        st.session_state.jrc_data = new_data
                        st.success("Dashboard Updated with PDF Insights!")
                        st.rerun()

    with st.expander("Market Indices Update", expanded=True):
        uploaded_csv = st.file_uploader("Upload CSV Data", type="csv")
        if uploaded_csv:
            try:
                for enc in ['utf-8', 'euc-kr', 'cp1252']:
                    try:
                        uploaded_csv.seek(0)
                        df = pd.read_csv(uploaded_csv, encoding=enc)
                        st.session_state.market_df = df
                        st.success(f"Market Data Updated ({enc.upper()})")
                        break
                    except: continue
            except Exception as e:
                st.error(f"CSV Error: {e}")

# --- Dashboard UI ---
st.markdown('<p class="main-title">Professional Market Intelligence Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">EU Potato Market Synthesis & JRC Bulletin Integration</p>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Report Summary", "Data & Charts", "PDF Preview", "Final Report"])

with tab1:
    data = st.session_state.jrc_data
    col1, col2 = st.columns([2, 1])
    with col1:
        with st.container(border=True):
            st.subheader("📋 Executive Overview")
            st.write(data["summary"])
            st.subheader("🌡️ Weather Synthesis")
            st.info(f"**Current:** {data['weather_overview']}")
            st.warning(f"**Forecast:** {data['weather_forecast']}")
            st.subheader("🥔 Potato Sector")
            st.write(data["potato_section"])
            st.subheader("🇪🇺 EU Regions")
            st.write(data["eu_country_analysis"])
    with col2:
        st.subheader("💡 Key Points")
        for p in data["key_points"]:
            st.markdown(f"- {p}")
        st.divider()
        st.metric("Yield Forecast", data["yield_forecast"])

with tab2:
    df = st.session_state.market_df
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Price Index")
        st.line_chart(df, x="date", y="price")
    with c2:
        st.subheader("FX Rate")
        st.line_chart(df, x="date", y="fx_rate")
    st.divider()
    st.dataframe(df, use_container_width=True)

with tab3:
    if uploaded_pdf:
        st.success(f"Previewing: {uploaded_pdf.name}")
        st.info("Actual PDF rendering requires specialized browser embedding. Viewing simulated metadata extraction below:")
        st.json(st.session_state.jrc_data)
    else:
        st.warning("Upload a PDF to see the preview metadata.")

with tab4:
    st.header("Manuscript Generator")
    c1, c2 = st.columns(2)
    with c1:
        prod = st.selectbox("Product", ["Potato Starch", "Premium Potatoes"])
        tone = st.radio("Style", ["Brief", "Analysis"], horizontal=True)
    with c2:
        lang = st.selectbox("Language", ["English", "Korean"])
        notes = st.text_area("Analyst Notes")
        
    if st.button("Generate Final Report", use_container_width=True):
        with st.spinner("Generating..."):
            ctx = str(st.session_state.jrc_data)
            st.session_state.report_output = generate_report(prod, tone, lang, st.session_state.market_df, ctx, notes)
    
    if st.session_state.report_output:
        st.text_area("Result", st.session_state.report_output, height=400)
        st.download_button("Download", st.session_state.report_output, file_name="report.txt")
