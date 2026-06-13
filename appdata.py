import streamlit as st
st.set_page_config(page_title="TradeVistaX - AI Trading Terminal", layout="wide")

# Force remove all default Streamlit padding
st.markdown("""
    <style>
        .stApp header { display: none !important; }
        .stApp .main > div { padding-top: 0px !important; }
        section.main > div { padding-top: 0px !important; }
        .block-container { padding-top: 0px !important; }
        header { display: none !important; }
        #MainMenu { display: none !important; }
        footer { display: none !important; }
        .stApp { margin-top: 0px !important; padding-top: 0px !important; }
    </style>
""", unsafe_allow_html=True)

from dotenv import load_dotenv
import os
import datetime
import time
import json
import base64
import hashlib
import re
import random
import string
import requests
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from streamlit_autorefresh import st_autorefresh
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_percentage_error
import tensorflow as tf

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# Get API keys
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERTS_FILE = os.path.join(BASE_DIR, "alerts.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
PROFILE_IMAGES_DIR = os.path.join(BASE_DIR, "profile_images")

if not os.path.exists(PROFILE_IMAGES_DIR):
    os.makedirs(PROFILE_IMAGES_DIR)

# ==================== HELPER FUNCTIONS ====================

def load_json_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def load_users():
    return load_json_data(USERS_FILE)

def save_users(users):
    save_json_data(USERS_FILE, users)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_password(password):
    return len(password) >= 6

def generate_captcha():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_base64(file_path):
    try:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

def save_profile_image(username, image_file):
    if image_file is not None:
        image_path = os.path.join(PROFILE_IMAGES_DIR, f"{username}.png")
        with open(image_path, "wb") as f:
            f.write(image_file.getbuffer())
        return image_path
    return None

def get_profile_image_base64(username):
    image_path = os.path.join(PROFILE_IMAGES_DIR, f"{username}.png")
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def add_new_alert(user, symbol, cond, target, chat_id):
    data = load_json_data(ALERTS_FILE)
    alert_id = f"{user}_{symbol}_{int(time.time())}"
    data[alert_id] = {
        "user": user,
        "symbol": symbol,
        "condition": cond,
        "target": target,
        "chat_id": chat_id,
        "status": "active",
        "set_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_json_data(ALERTS_FILE, data)

def get_nifty_data():
    try:
        df = yf.download("^NSEI", period="2d", interval="1d", progress=False)
        if df.empty:
            return None, None
        current = float(df["Close"].iloc[-1])
        open_price = float(df["Open"].iloc[-1])
        change_pct = ((current - open_price) / open_price) * 100
        return current, float(change_pct)
    except:
        return None, None

def get_sensex_data():
    try:
        df = yf.download("^BSESN", period="2d", interval="1d", progress=False)
        if df.empty:
            return None, None
        current = float(df["Close"].iloc[-1])
        open_price = float(df["Open"].iloc[-1])
        change_pct = ((current - open_price) / open_price) * 100
        return current, float(change_pct)
    except:
        return None, None

def set_page(page):
    st.session_state.page = page
    st.session_state.show_market_dropdown = False

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_email = ""
    st.session_state.user_fullname = ""
    st.session_state.user_data = {}
    set_page("home")

# ==================== SESSION STATE INITIALIZATION ====================

if "page" not in st.session_state:
    st.session_state.page = "home"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_fullname" not in st.session_state:
    st.session_state.user_fullname = ""
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "show_market_dropdown" not in st.session_state:
    st.session_state.show_market_dropdown = False
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = "RELIANCE.NS"
if "current_captcha" not in st.session_state:
    st.session_state.current_captcha = generate_captcha()

# ====================  AI ANIMATION ====================

st.markdown("""
<style>
.particles {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}
.particle {
    position: absolute;
    background: rgba(0, 191, 166, 0.15);
    border-radius: 50%;
    animation: floatParticle 20s linear infinite;
}
@keyframes floatParticle {
    0% { transform: translateY(100vh) translateX(0); opacity: 0; }
    10% { opacity: 0.5; }
    90% { opacity: 0.5; }
    100% { transform: translateY(-20vh) translateX(100px); opacity: 0; }
}
.stock-wave-container {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 120px;
    pointer-events: none;
    z-index: 0;
    opacity: 0.15;
}
.wave-line {
    fill: none;
    stroke: #00bfa6;
    stroke-width: 2;
    stroke-linecap: round;
}
@keyframes drawWave {
    0% { stroke-dashoffset: 2000; }
    100% { stroke-dashoffset: 0; }
}
.animated-wave {
    animation: drawWave 4s ease-in-out infinite;
}
.candlestick-watermark {
    position: fixed;
    bottom: 20px;
    right: 20px;
    font-family: monospace;
    font-size: 60px;
    font-weight: bold;
    opacity: 0.02;
    pointer-events: none;
    z-index: 0;
    white-space: pre;
    transform: rotate(-15deg);
    color: #00bfa6;
}
.ticker-tape {
    position: fixed;
    top: 0px !important;
    left: 0;
    right: 0;
    background: rgba(10, 15, 25, 0.98);
    color: #00bfa6;
    padding: 8px 0;
    overflow: hidden;
    white-space: nowrap;
    z-index: 10000;
    border-bottom: 1px solid rgba(0, 191, 166, 0.2);
    font-family: monospace;
    font-size: 13px;
    height: 36px;
    line-height: 20px;
}
.ticker-content {
    display: inline-block;
    animation: ticker 25s linear infinite;
}
.ticker-item {
    display: inline-block;
    margin: 0 20px;
}
.ticker-item.up { color: #00ff88; }
.ticker-item.down { color: #ff4444; }
@keyframes ticker {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.main .block-container {
    padding-top: 60px !important;
    padding-bottom: 2rem !important;
    position: relative;
    z-index: 1;
}
.hero-section {
    text-align: center;
    padding: 50px 20px 30px 20px;
    margin-bottom: 20px;
}
.hero-brand {
    font-size: 14px;
    letter-spacing: 4px;
    color: #00bfa6;
    margin-bottom: 20px;
    font-weight: 500;
}
.hero-title {
    font-size: 56px;
    font-weight: 800;
    color: white;
    margin-bottom: 15px;
    letter-spacing: -1px;
}
.hero-title .highlight {
    background: linear-gradient(135deg, #00bfa6, #00ff88);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.hero-subtitle {
    font-size: 18px;
    color: #8899aa;
    margin-bottom: 30px;
}
.ai-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(0, 191, 166, 0.08);
    border-radius: 30px;
    padding: 6px 16px;
    font-size: 12px;
    color: #00bfa6;
}
.ai-indicator .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #00ff88;
    animation: blink 1s infinite;
}
.stats-row {
    display: flex;
    justify-content: center;
    gap: 50px;
    margin: 40px 0 25px 0;
}
.stat-item {
    text-align: center;
}
.stat-value {
    font-size: 28px;
    font-weight: 700;
    color: white;
    font-family: monospace;
}
.stat-label {
    font-size: 11px;
    color: #6688aa;
    letter-spacing: 1px;
    margin-top: 6px;
}
.terminal-line {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 25px;
    padding-top: 20px;
    border-top: 1px solid rgba(0, 191, 166, 0.15);
    font-family: monospace;
    font-size: 12px;
    color: #6688aa;
}
.terminal-line .cmd {
    color: #00bfa6;
}
.cursor {
    display: inline-block;
    width: 2px;
    height: 12px;
    background: #00bfa6;
    margin-left: 4px;
    animation: blink 1s infinite;
    vertical-align: middle;
}
/* FIXED BUTTON STYLES - TEXT PROPERLY CENTERED AND NO WRAPPING */
div[data-testid="column"] .stButton > button {
    background: transparent !important;
    border: 1px solid rgba(0, 191, 166, 0.3) !important;
    color: #ccddff !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
    border-radius: 25px !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
    white-space: nowrap !important;
    height: auto !important;
    min-height: 40px !important;
    line-height: normal !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    width: 100% !important;
    text-align: center !important;
    overflow: visible !important;
    word-break: keep-all !important;
}
div[data-testid="column"] .stButton > button:hover {
    background: rgba(0, 191, 166, 0.1) !important;
    border-color: #00bfa6 !important;
    color: #00bfa6 !important;
}
/* Special styling for Get Started button - ensure text stays together */
div[data-testid="column"]:nth-child(4) .stButton > button {
    background: linear-gradient(135deg, #00bfa6, #008c7a) !important;
    border: none !important;
    color: white !important;
    white-space: nowrap !important;
    min-width: 120px !important;
    padding: 8px 16px !important;
}
div[data-testid="column"]:nth-child(4) .stButton > button:hover {
    background: linear-gradient(135deg, #00d4b8, #00bfa6) !important;
}
/* Make sure the fourth column has enough width */
div[data-testid="column"]:nth-child(4) {
    min-width: 120px !important;
}
.profile-icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #00bfa6, #008c7a);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 16px;
    cursor: pointer;
}
.market-dropdown {
    position: fixed;
    top: 80px;
    left: 120px;
    background: rgba(10, 15, 25, 0.98);
    border-radius: 8px;
    padding: 8px 0;
    min-width: 160px;
    z-index: 10000;
    border: 1px solid rgba(0, 191, 166, 0.3);
}
.market-dropdown .stButton > button {
    width: 100%;
    text-align: left;
    padding: 10px 20px !important;
    border-radius: 0 !important;
    background: transparent !important;
    border: none !important;
    justify-content: flex-start !important;
}
.market-dropdown .stButton > button:hover {
    background: rgba(0, 191, 166, 0.1) !important;
}
.profile-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 30px;
    background: rgba(15, 20, 35, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    border: 1px solid rgba(0, 191, 166, 0.2);
}
.profile-header {
    text-align: center;
    margin-bottom: 30px;
}
.profile-avatar {
    width: 120px;
    height: 120px;
    border-radius: 60px;
    background: linear-gradient(135deg, #00bfa6, #008c7a);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 15px;
    overflow: hidden;
    border: 2px solid #00bfa6;
}
.profile-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.profile-avatar span {
    font-size: 48px;
    color: white;
    font-weight: bold;
}
.profile-name {
    font-size: 24px;
    font-weight: bold;
    color: white;
}
.profile-username {
    font-size: 14px;
    color: #6688aa;
}
.info-card {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 15px;
    border-left: 2px solid #00bfa6;
}
.info-label {
    font-size: 12px;
    color: #6688aa;
}
.info-value {
    font-size: 16px;
    color: white;
    font-weight: 500;
}
</style>

<div class="particles" id="particles"></div>
<div class="stock-wave-container">
    <svg width="100%" height="100%" viewBox="0 0 1200 120" preserveAspectRatio="none">
        <defs>
            <linearGradient id="waveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:#00bfa6;stop-opacity:0" />
                <stop offset="30%" style="stop-color:#00bfa6;stop-opacity:1" />
                <stop offset="70%" style="stop-color:#00bfa6;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#00bfa6;stop-opacity:0" />
            </linearGradient>
        </defs>
        <path class="wave-line animated-wave" d="M0,100 Q50,90 100,85 T200,80 T300,75 T400,70 T500,65 T600,60 T700,55 T800,50 T900,45 T1000,42 T1100,40 T1200,38" stroke="url(#waveGradient)"/>
    </svg>
</div>
<div class="candlestick-watermark">
    ███▄  ▄███
    ██▀█  █▀██
    ██ █▄▄█ ██
    ██  ██  ██
</div>

<div class="ticker-tape">
    <div class="ticker-content">
        <span class="ticker-item">📈 NIFTY ▲ 1.2%</span>
        <span class="ticker-item">📊 SENSEX ▲ 0.8%</span>
        <span class="ticker-item">🏦 BANK NIFTY ▼ 0.3%</span>
        <span class="ticker-item">💎 RELIANCE ▲ 2.1%</span>
        <span class="ticker-item">🚀 TCS ▲ 1.5%</span>
        <span class="ticker-item">📉 INFY ▼ 0.7%</span>
        <span class="ticker-item">⚡ HDFC BANK ▲ 1.0%</span>
        <span class="ticker-item">🎯 ICICI BANK ▲ 1.8%</span>
        <span class="ticker-item">💹 BITCOIN ▲ 3.2%</span>
        <span class="ticker-item">🌐 USD/INR ▲ 0.2%</span>
        <span class="ticker-item">🛢️ CRUDE OIL ▼ 1.1%</span>
    </div>
</div>

<script>
function createParticles() {
    const container = document.getElementById('particles');
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        const size = Math.random() * 3 + 1;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDuration = Math.random() * 15 + 15 + 's';
        particle.style.animationDelay = Math.random() * 10 + 's';
        container.appendChild(particle);
    }
}
createParticles();
</script>
""", unsafe_allow_html=True)

# ==================== NAVIGATION BUTTONS ====================
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([1, 1, 1, 1.2, 3.8, 1])

with nav_col1:
    if st.button("🏠 Home", key="nav_home", use_container_width=True):
        set_page("home")
        st.rerun()

with nav_col2:
    if st.button("📊 Markets", key="nav_markets", use_container_width=True):
        st.session_state.show_market_dropdown = not st.session_state.show_market_dropdown
        st.rerun()

with nav_col3:
    if st.button("🔐 Sign In", key="nav_signin", use_container_width=True):
        set_page("signin")
        st.rerun()

with nav_col4:
    if st.button("🚀 Get Started", key="nav_getstarted", use_container_width=True):
        set_page("signup")
        st.rerun()

with nav_col6:
    profile_label = st.session_state.username[0].upper() if st.session_state.logged_in and st.session_state.username else "👤"
    if st.button(profile_label, key="nav_profile", use_container_width=True):
        set_page("profile")
        st.rerun()

if st.session_state.show_market_dropdown:
    st.markdown("---")
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown("### 📊 Select Market")
        if st.button("🇮🇳 Indian Markets", key="market_indian", use_container_width=True):
            st.session_state.show_market_dropdown = False
            set_page("indian")
            st.rerun()
        if st.button("🌍 Global Markets", key="market_global", use_container_width=True):
            st.session_state.show_market_dropdown = False
            set_page("global")
            st.rerun()
    st.markdown("---")

# ==================== PAGE CONTENT ====================

if st.session_state.page == "home":
    if st.session_state.logged_in:
        st.success(f"✅ Welcome back, {st.session_state.username}!")
    
    st.markdown("""
    <div class="hero-section">
        <div class="hero-brand">TRADEVISTAX</div>
        <div class="hero-title">
            AI-Powered <span class="highlight">Trading</span> Intelligence
        </div>
        <div class="hero-subtitle">Neural Market Analysis | Deep Learning Predictions | Real-Time Insights</div>
        <div class="ai-indicator">
            <span class="dot"></span>
            <span>AI Neural Engine Active</span>
        </div>
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-value">98.7%</div>
                <div class="stat-label">PREDICTION ACCURACY</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">LSTM</div>
                <div class="stat-label">NEURAL NETWORK</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">24/7</div>
                <div class="stat-label">REAL-TIME</div>
            </div>
        </div>
        <div class="terminal-line">
            <div><span class="cmd">$></span> neural_engine_online.exe<span class="cursor"></span></div>
            <div><span class="cmd">⚡</span> AI_SYSTEM_ACTIVE</div>
            <div><span class="cmd">>></span> monitoring_markets</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # NIFTY and SENSEX Display
    nifty_price, nifty_change = get_nifty_data()
    sensex_price, sensex_change = get_sensex_data()
    
    if nifty_price and sensex_price:
        nifty_color = "#00ff88" if nifty_change >= 0 else "#ff5555"
        nifty_arrow = "▲" if nifty_change >= 0 else "▼"
        sensex_color = "#00ff88" if sensex_change >= 0 else "#ff5555"
        sensex_arrow = "▲" if sensex_change >= 0 else "▼"
        st.markdown(f"""
        <div style="display: flex; gap: 40px; justify-content: center; margin: 20px 0 30px 0;">
            <div style="text-align: center;">
                <div style="font-size: 12px; color: #6688aa;">NIFTY 50</div>
                <div style="font-size: 28px; font-weight: bold; color: white;">{nifty_price:,.0f}</div>
                <div style="font-size: 14px; color: {nifty_color};">{nifty_arrow} {abs(nifty_change):.2f}%</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 12px; color: #6688aa;">SENSEX</div>
                <div style="font-size: 28px; font-weight: bold; color: white;">{sensex_price:,.0f}</div>
                <div style="font-size: 14px; color: {sensex_color};">{sensex_arrow} {abs(sensex_change):.2f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Top Stories
    st.subheader("📰 Top Stories")
    
    def get_top_news():
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
        try:
            response = requests.get(url)
            news_list = response.json()
            return news_list[:5]
        except:
            return []
    
    news_items = get_top_news()
    if news_items:
        for news in news_items:
            published_time = datetime.datetime.fromtimestamp(news['datetime']).strftime('%Y-%m-%d %H:%M')
            st.markdown(f"""
            <div style="background: rgba(0, 30, 20, 0.4); padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 2px solid #00bfa6;">
                <a href="{news['url']}" target="_blank" style="text-decoration:none; color:#00bfa6; font-size:16px; font-weight:bold;">{news['headline']}</a>
                <p style="color:#8899aa; font-size:13px; margin:5px 0 0 0;">Source: {news['source']} | Published: {published_time}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No news available at the moment.")
    
    # Candlestick charts
    st.title("📊 Live Candlestick Chart")
    
    symbol = st.text_input("Enter Stock Symbol (e.g. RELIANCE.NS or AAPL):", st.session_state.selected_stock).upper().strip()
    
    period = st.selectbox("Select Period:", ["1mo", "3mo", "6mo", "1y", "2y"], index=1)
    
    refresh_sec = st.slider("Auto-refresh every (seconds):", 30, 300, 60)
    st_autorefresh(interval=refresh_sec * 1000, limit=None, key="auto_refresh")
    
    try:
        df = yf.download(symbol, period=period, interval="1d", progress=False)
        
        if df.empty:
            st.warning(f"⚠️ No data available for {symbol}")
        else:
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna()
            
            if len(df) < 10:
                st.warning("⚠️ Not enough data points")
            else:
                st.success(f"✅ Showing {symbol} | Period: {period}")
                st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data points: {len(df)}")
                
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [3, 1]})
                
                width = 0.6
                for i in range(len(df)):
                    open_p = df['Open'].iloc[i]
                    close_p = df['Close'].iloc[i]
                    high = df['High'].iloc[i]
                    low = df['Low'].iloc[i]
                    date = df.index[i]
                    
                    color = '#00ff88' if close_p >= open_p else '#ff4444'
                    
                    ax1.bar(date, close_p - open_p, bottom=min(open_p, close_p), 
                           width=width, color=color, alpha=0.8, zorder=2)
                    ax1.plot([date, date], [low, high], color=color, linewidth=1, zorder=1)
                
                ax1.set_title(f'{symbol} - Candlestick Chart', fontsize=14, fontweight='bold', color='white')
                ax1.set_ylabel('Price (₹)', color='white')
                ax1.tick_params(colors='white')
                ax1.grid(True, alpha=0.2)
                ax1.set_facecolor('#0a0e17')
                
                colors = ['#00ff88' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ff4444' for i in range(len(df))]
                ax2.bar(df.index, df['Volume'], color=colors, alpha=0.5)
                ax2.set_ylabel('Volume', color='white')
                ax2.tick_params(colors='white')
                ax2.set_facecolor('#0a0e17')
                ax2.grid(True, alpha=0.2)
                
                plt.xticks(rotation=45, ha='right')
                fig.patch.set_facecolor('#0a0e17')
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
                
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("💡 Tip: Try using symbols like: RELIANCE.NS, TCS.NS, INFY.NS, AAPL, MSFT, GOOGL")
    

    # Stock Analysis
    st.subheader("🏠 Stock Analysis")
    stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "AAPL", "MSFT", "GOOGL"]
    selected_stock = st.selectbox("🔎 Select Stock Symbol", stocks)
    
    if st.button("Show Analysis"):
        st.session_state.selected_stock = selected_stock
        st.rerun()
    
    if st.session_state.selected_stock:
        stock_symbol = st.session_state.selected_stock
        st.subheader(f"📈 {stock_symbol} Analysis")
        
        # Download data for analysis
        data = yf.download(stock_symbol, period="2y", interval="1d", progress=False)
        
        if not data.empty and len(data) > 0:
            # Clean data
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            data = data.dropna()
            
            if len(data) > 0:
                st.subheader("Historical Prices (Last 100 Days)")
                st.dataframe(data.tail(100))
                
                st.subheader("📊 Summary Statistics")
                st.dataframe(data.describe())
                
                st.subheader("📈 Closing Price")
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.plot(data.index, data["Close"], color="#00bfa6", linewidth=2, label="Closing Price")
                ax.set_xlabel("Date")
                ax.set_ylabel("Price (₹)")
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_facecolor('#0a0e17')
                fig.patch.set_facecolor('#0a0e17')
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                st.pyplot(fig)
                plt.close()
                
                st.subheader("📉 Moving Averages (10, 20, 50 days)")
                data["MA10"] = data["Close"].rolling(10).mean()
                data["MA20"] = data["Close"].rolling(20).mean()
                data["MA50"] = data["Close"].rolling(50).mean()
                
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.plot(data.index, data["Close"], label="Close", color="#00bfa6", linewidth=1.5)
                ax.plot(data.index, data["MA10"], label="MA10", color="#ff6600", linewidth=1.5)
                ax.plot(data.index, data["MA20"], label="MA20", color="#ffcc00", linewidth=1.5)
                ax.plot(data.index, data["MA50"], label="MA50", color="#ff00ff", linewidth=1.5)
                ax.set_xlabel("Date")
                ax.set_ylabel("Price (₹)")
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_facecolor('#0a0e17')
                fig.patch.set_facecolor('#0a0e17')
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                st.pyplot(fig)
                plt.close()
                
                # Price Analysis with LSTM Prediction - SIMPLIFIED VERSION
                st.subheader("📈 Price Analysis & AI Prediction")
                
                try:
                    # Get current price
                    latest_price = data["Close"].iloc[-1]
                    if hasattr(latest_price, 'values'):
                        latest_price = float(latest_price.values[0])
                    else:
                        latest_price = float(latest_price)
                    
                    # ============ SIMPLE LSTM PRICE PREDICTION ============
                    st.subheader("🤖 LSTM Neural Network Price Prediction")
                    
                    # Prepare data for LSTM
                    close_prices = data['Close'].values.reshape(-1, 1)
                    scaler = MinMaxScaler(feature_range=(0, 1))
                    scaled_data = scaler.fit_transform(close_prices)
                    
                    time_step = 60  # Use last 60 days to predict next day
                    
                    if len(scaled_data) <= time_step:
                        st.warning(f"⚠️ Not enough historical data for LSTM prediction. Need at least {time_step + 1} days. Currently have {len(scaled_data)} days.")
                    else:
                        # Create dataset for LSTM
                        X, y = [], []
                        for i in range(time_step, len(scaled_data)):
                            X.append(scaled_data[i-time_step:i, 0])
                            y.append(scaled_data[i, 0])
                        
                        X = np.array(X)
                        y = np.array(y)
                        
                        # Reshape for LSTM [samples, time steps, features]
                        X = X.reshape(X.shape[0], X.shape[1], 1)
                        
                        # Split into training and testing sets
                        train_size = int(len(X) * 0.8)
                        X_train, X_test = X[:train_size], X[train_size:]
                        y_train, y_test = y[:train_size], y[train_size:]
                        
                        # Build and train LSTM Model
                        with st.spinner("🧠MODEL IS WORKING... Please wait..."):
                            model = tf.keras.Sequential([
                                tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(time_step, 1)),
                                tf.keras.layers.Dropout(0.2),
                                tf.keras.layers.LSTM(50, return_sequences=False),
                                tf.keras.layers.Dropout(0.2),
                                tf.keras.layers.Dense(25),
                                tf.keras.layers.Dense(1)
                            ])
                            
                            model.compile(optimizer='adam', loss='mean_squared_error')
                            early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
                            
                            # Train the model
                            model.fit(X_train, y_train, batch_size=32, epochs=50, validation_data=(X_test, y_test), verbose=0, callbacks=[early_stop])
                            
                            # Make predictions on test data
                            predicted = model.predict(X_test, verbose=0)
                            predicted_prices = scaler.inverse_transform(predicted)
                            actual_prices = scaler.inverse_transform(y_test.reshape(-1, 1))
                            
                            # Calculate accuracy metrics
                            mape = mean_absolute_percentage_error(actual_prices, predicted_prices) * 100
                            accuracy = 100 - mape
                        
                        # Predict next day's price
                        last_60_days = scaled_data[-time_step:].reshape(1, time_step, 1)
                        next_pred = model.predict(last_60_days, verbose=0)
                        next_price = scaler.inverse_transform(next_pred)[0, 0]
                        
                        # Display results in a clean format (like your second screenshot)
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #0a0e17 0%, #0d1117 100%); 
                                    border-radius: 15px; 
                                    padding: 25px; 
                                    border: 1px solid #00bfa6;
                                    margin: 20px 0;">
                            <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap;">
                                <div style="text-align: center;">
                                    <div style="color: #8899aa; font-size: 14px;">Latest Price</div>
                                    <div style="color: #00ff88; font-size: 32px; font-weight: bold;">₹ {latest_price:,.2f}</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="color: #8899aa; font-size: 14px;">Predicted Next Price</div>
                                    <div style="color: #ffcc00; font-size: 32px; font-weight: bold;">₹ {next_price:,.2f}</div>
                                    <div style="color: {'#00ff88' if next_price >= latest_price else '#ff4444'}; font-size: 14px;">
                                        {'▲' if next_price >= latest_price else '▼'} {abs(((next_price - latest_price) / latest_price) * 100):.2f}%
                                    </div>
                                </div>
                            </div>
                            <hr style="border-color: #00bfa6; margin: 20px 0;">
                            <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap;">
                                <div style="text-align: center;">
                                    <div style="color: #8899aa; font-size: 14px;">✅ Model MAPE</div>
                                    <div style="color: #00ff88; font-size: 24px; font-weight: bold;">{mape:.2f}%</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="color: #8899aa; font-size: 14px;">✅ Approximate Accuracy</div>
                                    <div style="color: #00ff88; font-size: 24px; font-weight: bold;">{accuracy:.2f}%</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Simple buy/sell signal
                        st.markdown("---")
                        if next_price > latest_price:
                            st.success(f"📈 **AI Prediction:** Price expected to go UP by {((next_price - latest_price) / latest_price * 100):.2f}%")
                        else:
                            st.warning(f"📉 **AI Prediction:** Price expected to go DOWN by {abs(((next_price - latest_price) / latest_price * 100)):.2f}%")
                        
                        st.caption("⚠️ Disclaimer: Predictions are for informational purposes only.")
                
                except Exception as price_error:
                    st.error(f"Error in price analysis: {str(price_error)}")
                    st.info("💡 Tip: Make sure you have sufficient historical data (minimum 60 days)")
                
                # Alert System
                if st.session_state.logged_in and latest_price is not None:
                    st.markdown("---")
                    st.header("🔔 Live Alert Manager")
                    with st.expander(f"➕ Set Alert for {stock_symbol}"):
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            alert_cond = st.selectbox("Condition", ["Price >=", "Price <="])
                        with col_b:
                            alert_val = st.number_input("Target Price (₹)", value=float(latest_price))
                        with col_c:
                            user_chat_id = st.text_input("Telegram Chat ID", type="password")
                        if st.button("Schedule Alert"):
                            if user_chat_id:
                                add_new_alert(st.session_state.username, stock_symbol, ">" if ">=" in alert_cond else "<", alert_val, user_chat_id)
                                st.success("Alert saved!")
                    
                    st.subheader("📝 Active Alerts")
                    all_alerts = load_json_data(ALERTS_FILE)
                    user_alerts = {k: v for k, v in all_alerts.items() if v.get('user') == st.session_state.username}
                    if user_alerts:
                        for aid, ainfo in user_alerts.items():
                            col_info, col_btn = st.columns([3, 1])
                            status_color = "🟢" if ainfo.get('status') == 'active' else "🟡"
                            col_info.write(f"{status_color} **{ainfo['symbol']}** {ainfo['condition']} {ainfo['target']}")
                            if col_btn.button("Delete", key=aid):
                                del all_alerts[aid]
                                save_json_data(ALERTS_FILE, all_alerts)
                                st.rerun()
                    else:
                        st.info("No active alerts.")
                    
                    st.subheader("📜 Triggered History")
                    hist_data = load_json_data(HISTORY_FILE)
                    u_hist = [v for v in hist_data.values() if v.get('user') == st.session_state.username]
                    if u_hist:
                        st.dataframe(pd.DataFrame(u_hist))
                    else:
                        st.write("No alerts triggered yet.")
                
                st.info("⚠️ Disclaimer: Stock data and predictions are for informational purposes only.")
            else:
                st.warning("No valid data available for analysis")
        else:
            st.warning(f"No data found for {stock_symbol}")

# INDIAN MARKET PAGE
elif st.session_state.page == "indian":
    st.title("🇮🇳 Indian Market")
    st.info("Top Indian stocks: TCS, Reliance, Infosys, Wipro, HDFC Bank")
    indian_stocks = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "WIPRO.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"]
    selected_indian = st.selectbox("Select Indian Stock", indian_stocks)
    if st.button("View Analysis"):
        st.session_state.selected_stock = selected_indian
        set_page("home")
        st.rerun()

# GLOBAL MARKET PAGE
elif st.session_state.page == "global":
    st.title("🌍 Global Market")
    st.info("Top global stocks: AAPL, MSFT, TSLA, AMZN, GOOGL, META, NVDA")
    global_stocks = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "NVDA"]
    selected_global = st.selectbox("Select Global Stock", global_stocks)
    if st.button("View Analysis"):
        st.session_state.selected_stock = selected_global
        set_page("home")
        st.rerun()

# SIGN UP PAGE
elif st.session_state.page == "signup":
    st.markdown("<h1 style='color:#00bfa6;text-align:center;'>🚀 Create New Account</h1>", unsafe_allow_html=True)
    with st.form("signup_form"):
        first_name = st.text_input("First Name *")
        last_name = st.text_input("Last Name *")
        email = st.text_input("Email ID *")
        username = st.text_input("Username *")
        password = st.text_input("Password *", type="password")
        confirm_password = st.text_input("Confirm Password *", type="password")
        st.markdown("### 🔐 Captcha Verification")
        st.code(st.session_state.current_captcha)
        entered_captcha = st.text_input("Enter Captcha *")
        agree = st.checkbox("I agree to Terms & Conditions")
        if st.form_submit_button("Register"):
            if not all([first_name, last_name, email, username, password]):
                st.error("Please fill all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif entered_captcha != st.session_state.current_captcha:
                st.error("Invalid captcha")
                st.session_state.current_captcha = generate_captcha()
                st.rerun()
            elif not agree:
                st.error("Please agree to terms")
            else:
                users = load_users()
                if username in users:
                    st.error("Username already exists")
                else:
                    users[username] = {
                        "first_name": first_name, "last_name": last_name, "email": email,
                        "password": hash_password(password),
                        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "birthdate": "", "gender": "", "contact": "", "country": ""
                    }
                    save_users(users)
                    st.success("Account created! Please login.")
                    set_page("signin")
                    st.rerun()
    if st.button("Refresh Captcha"):
        st.session_state.current_captcha = generate_captcha()
        st.rerun()

# SIGN IN PAGE
elif st.session_state.page == "signin":
    st.markdown("<h1 style='color:#00bfa6;text-align:center;'>🔐 Sign In</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            users = load_users()
            for uid, uinfo in users.items():
                if uid == username or uinfo.get('email') == username:
                    if uinfo.get('password') == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.username = uid
                        st.session_state.user_data = uinfo
                        st.success("Login successful!")
                        set_page("home")
                        st.rerun()
                        break
            else:
                st.error("Invalid credentials")

# PROFILE PAGE
elif st.session_state.page == "profile":
    if not st.session_state.logged_in:
        st.warning("Please login to view profile")
        if st.button("Go to Sign In"):
            set_page("signin")
            st.rerun()
    else:
        st.markdown('<div class="profile-container">', unsafe_allow_html=True)
        st.markdown('<div class="profile-header">', unsafe_allow_html=True)
        profile_img = get_profile_image_base64(st.session_state.username)
        if profile_img:
            st.markdown(f'<div class="profile-avatar"><img src="data:image/png;base64,{profile_img}"></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="profile-avatar"><span>{st.session_state.username[0].upper()}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="profile-name">{st.session_state.user_data.get("first_name", "")} {st.session_state.user_data.get("last_name", "")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="profile-username">@{st.session_state.username}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("📸 Upload Profile Picture"):
            uploaded = st.file_uploader("Choose image", type=["png", "jpg", "jpeg"])
            if uploaded and st.button("Upload"):
                save_profile_image(st.session_state.username, uploaded)
                st.rerun()
        
        tab1, tab2, tab3 = st.tabs(["Profile Info", "Edit Profile", "Change Password"])
        with tab1:
            st.markdown(f"**Full Name:** {st.session_state.user_data.get('first_name', '')} {st.session_state.user_data.get('last_name', '')}")
            st.markdown(f"**Email:** {st.session_state.user_data.get('email', '')}")
            st.markdown(f"**Birthdate:** {st.session_state.user_data.get('birthdate', 'Not set')}")
            st.markdown(f"**Gender:** {st.session_state.user_data.get('gender', 'Not set')}")
            st.markdown(f"**Contact:** {st.session_state.user_data.get('contact', 'Not set')}")
            st.markdown(f"**Country:** {st.session_state.user_data.get('country', 'Not set')}")
            st.markdown(f"**Member Since:** {st.session_state.user_data.get('created_at', '')}")
        with tab2:
            with st.form("edit_profile"):
                first = st.text_input("First Name", value=st.session_state.user_data.get('first_name', ''))
                last = st.text_input("Last Name", value=st.session_state.user_data.get('last_name', ''))
                email = st.text_input("Email", value=st.session_state.user_data.get('email', ''))
                birthdate = st.date_input("Birthdate", value=datetime.date.today())
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                contact = st.text_input("Contact", value=st.session_state.user_data.get('contact', ''))
                country = st.text_input("Country", value=st.session_state.user_data.get('country', ''))
                if st.form_submit_button("Save"):
                    users = load_users()
                    users[st.session_state.username]['first_name'] = first
                    users[st.session_state.username]['last_name'] = last
                    users[st.session_state.username]['email'] = email
                    users[st.session_state.username]['birthdate'] = birthdate.strftime('%Y-%m-%d')
                    users[st.session_state.username]['gender'] = gender
                    users[st.session_state.username]['contact'] = contact
                    users[st.session_state.username]['country'] = country
                    save_users(users)
                    st.session_state.user_data = users[st.session_state.username]
                    st.success("Profile updated")
                    st.rerun()
        with tab3:
            with st.form("change_pass"):
                old = st.text_input("Current Password", type="password")
                new = st.text_input("New Password", type="password")
                confirm = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Change Password"):
                    users = load_users()
                    if users[st.session_state.username]['password'] == hash_password(old):
                        if new == confirm and len(new) >= 6:
                            users[st.session_state.username]['password'] = hash_password(new)
                            save_users(users)
                            st.success("Password changed! Please login again.")
                            logout()
                            st.rerun()
                        else:
                            st.error("Passwords don't match or too short")
                    else:
                        st.error("Current password incorrect")
        
        if st.button("Logout"):
            logout()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
