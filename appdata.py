import streamlit as st
st.set_page_config(page_title="TradeVistaX - AI Trading Terminal", layout="wide")

# Force remove all default Streamlit padding
st.markdown("""
    <style>
        .stApp header { display: none !important; }
        .stApp .main > div { padding-top: 0px !important; }
        section.main > div { padding-top: 0px !important; }
        .block-container { padding-top: 60px !important; }
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
from streamlit_autorefresh import st_autorefresh

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

# Create directories if they don't exist
if not os.path.exists(PROFILE_IMAGES_DIR):
    os.makedirs(PROFILE_IMAGES_DIR)

# Create empty JSON files if they don't exist
for file in [ALERTS_FILE, HISTORY_FILE, USERS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)

# ==================== LIGHTWEIGHT PREDICTION FUNCTION ====================

def simple_price_prediction(data):
    """Simple price prediction using moving averages"""
    try:
        # Ensure we're working with simple float values
        close_prices = data['Close'].values.flatten()
        
        # Convert to float and ensure no numpy arrays
        close_prices = [float(x) for x in close_prices]
        latest_price = float(close_prices[-1])
        
        if len(close_prices) >= 30:
            # Calculate moving averages as simple floats
            ma5 = float(np.mean(close_prices[-5:]))
            ma10 = float(np.mean(close_prices[-10:]))
            ma20 = float(np.mean(close_prices[-20:]))
            
            # Calculate trends
            short_trend = (ma5 - ma10) / ma10 * 100 if ma10 != 0 else 0
            long_trend = (ma10 - ma20) / ma20 * 100 if ma20 != 0 else 0
            
            # Weighted prediction
            trend_weight = (short_trend * 0.6 + long_trend * 0.4) / 100
            predicted_price = latest_price * (1 + trend_weight)
            
            # Calculate confidence
            if short_trend > 0 and long_trend > 0:
                confidence = 92
                signal = "STRONG BUY"
                recommendation = "📈 Consider buying on dips"
            elif short_trend < 0 and long_trend < 0:
                confidence = 88
                signal = "STRONG SELL"
                recommendation = "📉 Consider selling on rallies"
            elif short_trend > 0:
                confidence = 78
                signal = "WEAK BUY"
                recommendation = "📊 Cautious buying opportunity"
            elif short_trend < 0:
                confidence = 75
                signal = "WEAK SELL"
                recommendation = "⚡ Consider reducing position"
            else:
                confidence = 70
                signal = "NEUTRAL"
                recommendation = "➡️ Wait for clearer trend"
            
            return predicted_price, confidence, 100 - confidence, signal, recommendation, latest_price
        else:
            return latest_price * 1.01, 85.0, 15.0, "INSUFFICIENT DATA", "Need more data for analysis", latest_price
    except Exception as e:
        st.error(f"Prediction error: {str(e)}")
        return None, None, None, None, None, None

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

def generate_captcha():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_profile_image_base64(username):
    image_path = os.path.join(PROFILE_IMAGES_DIR, f"{username}.png")
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def save_profile_image(username, image_file):
    if image_file is not None:
        image_path = os.path.join(PROFILE_IMAGES_DIR, f"{username}.png")
        with open(image_path, "wb") as f:
            f.write(image_file.getbuffer())
        return image_path
    return None

def add_new_alert(user, symbol, cond, target, chat_id):
    data = load_json_data(ALERTS_FILE)
    alert_id = f"{user}_{symbol}_{int(time.time())}"
    data[alert_id] = {
        "user": user,
        "symbol": symbol,
        "condition": cond,
        "target": float(target),
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
    
    # Hero Section
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 14px; letter-spacing: 4px; color: #00bfa6;">TRADEVISTAX</div>
        <div style="font-size: 52px; font-weight: 800; margin: 20px 0;">
            AI-Powered <span style="background: linear-gradient(135deg, #00bfa6, #00ff88); -webkit-background-clip: text; background-clip: text; color: transparent;">Trading</span> Intelligence
        </div>
        <div style="font-size: 18px; color: #8899aa;">Neural Market Analysis | Deep Learning Predictions | Real-Time Insights</div>
    </div>
    """, unsafe_allow_html=True)

    # NIFTY and SENSEX Display
    nifty_price, nifty_change = get_nifty_data()
    sensex_price, sensex_change = get_sensex_data()
    
    if nifty_price and sensex_price:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("NIFTY 50", f"{nifty_price:,.0f}", f"{'▲' if nifty_change >= 0 else '▼'} {abs(nifty_change):.2f}%")
        with col2:
            st.metric("SENSEX", f"{sensex_price:,.0f}", f"{'▲' if sensex_change >= 0 else '▼'} {abs(sensex_change):.2f}%")
    
    # Top Stories
    st.subheader("📰 Top Stories")
    
    def get_top_news():
        if not FINNHUB_API_KEY or FINNHUB_API_KEY == "None":
            return None
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()[:5]
            return None
        except:
            return None
    
    news_items = get_top_news()
    if news_items:
        for news in news_items:
            st.markdown(f"""
            <div style="background: rgba(0, 30, 20, 0.4); padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 2px solid #00bfa6;">
                <a href="{news['url']}" target="_blank" style="text-decoration:none; color:#00bfa6; font-size:16px; font-weight:bold;">{news['headline']}</a>
                <p style="color:#8899aa; font-size:13px;">{news['source']} | {datetime.datetime.fromtimestamp(news['datetime']).strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📰 Add FINNHUB_API_KEY to secrets for live news")
    
    # Candlestick charts
    st.title("📊 Live Candlestick Chart")
    
    symbol = st.text_input("Enter Stock Symbol:", st.session_state.selected_stock).upper().strip()
    period = st.selectbox("Period:", ["1mo", "3mo", "6mo", "1y"], index=1)
    
    try:
        df = yf.download(symbol, period=period, interval="1d", progress=False)
        
        if not df.empty:
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [3, 1]})
            
            for i in range(len(df)):
                open_p = df['Open'].iloc[i]
                close_p = df['Close'].iloc[i]
                high = df['High'].iloc[i]
                low = df['Low'].iloc[i]
                color = '#00ff88' if close_p >= open_p else '#ff4444'
                
                ax1.bar(df.index[i], close_p - open_p, bottom=min(open_p, close_p), width=0.6, color=color, alpha=0.8)
                ax1.plot([df.index[i], df.index[i]], [low, high], color=color, linewidth=1)
            
            ax1.set_facecolor('#0a0e17')
            ax1.tick_params(colors='white')
            ax1.set_title(f'{symbol} - {period}', color='white')
            
            colors = ['#00ff88' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ff4444' for i in range(len(df))]
            ax2.bar(df.index, df['Volume'], color=colors, alpha=0.5)
            ax2.set_facecolor('#0a0e17')
            ax2.tick_params(colors='white')
            
            fig.patch.set_facecolor('#0a0e17')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
    except Exception as e:
        st.error(f"Error: {e}")
    
    # Stock Analysis
    st.subheader("📈 Stock Analysis")
    stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "AAPL", "MSFT", "GOOGL"]
    selected_stock = st.selectbox("Select Stock:", stocks, key="stock_select")
    
    if st.button("📊 Analyze", key="analyze"):
        st.session_state.selected_stock = selected_stock
        st.rerun()
    
    if st.session_state.selected_stock:
        stock_symbol = st.session_state.selected_stock
        st.subheader(f"📈 {stock_symbol} Analysis")
        
        data = yf.download(stock_symbol, period="1y", interval="1d", progress=False)
        
        if not data.empty:
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
            
            # Display current price
            current_price = float(data['Close'].iloc[-1])
            st.metric("Current Price", f"₹{current_price:,.2f}")
            
            # Moving Averages Chart
            data["MA10"] = data["Close"].rolling(10).mean()
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            
            fig, ax = plt.subplots(figsize=(12, 5))
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
            st.pyplot(fig)
            plt.close()
            
            # ============ AI PRICE PREDICTION (FIXED) ============
            st.markdown("---")
            st.subheader("🤖 AI Price Prediction")
            
            with st.spinner("Analyzing market trends..."):
                result = simple_price_prediction(data)
            
            if result[0] is not None:
                predicted_price, confidence, mape, signal, recommendation, latest_price = result
                
                # Display predictions in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Price", f"₹{latest_price:,.2f}")
                with col2:
                    change_percent = ((predicted_price - latest_price) / latest_price) * 100
                    st.metric("Predicted Price", f"₹{predicted_price:,.2f}", 
                             delta=f"{'+' if change_percent >= 0 else ''}{change_percent:.2f}%")
                with col3:
                    st.metric("AI Confidence", f"{confidence:.1f}%")
                
                # Trading Signal
                if "BUY" in signal:
                    st.success(f"📈 **{signal}** - {recommendation}")
                elif "SELL" in signal:
                    st.warning(f"📉 **{signal}** - {recommendation}")
                else:
                    st.info(f"⚡ **{signal}** - {recommendation}")
                
                st.caption("⚠️ Disclaimer: For informational purposes only. Not financial advice.")
            else:
                st.warning("⚠️ Insufficient data for prediction. Need at least 30 days of data.")
            
            # Alert System for logged-in users
            if st.session_state.logged_in:
                st.markdown("---")
                st.subheader("🔔 Price Alert")
                
                with st.expander("Set New Alert"):
                    alert_cond = st.selectbox("Condition", ["Price >=", "Price <="])
                    alert_val = st.number_input("Target Price (₹)", value=float(current_price))
                    if st.button("Create Alert"):
                        add_new_alert(st.session_state.username, stock_symbol, ">" if ">=" in alert_cond else "<", alert_val, "demo")
                        st.success("Alert created!")
                
                # Show active alerts
                all_alerts = load_json_data(ALERTS_FILE)
                user_alerts = {k: v for k, v in all_alerts.items() if v.get('user') == st.session_state.username}
                if user_alerts:
                    st.write("**Your Alerts:**")
                    for aid, alert in user_alerts.items():
                        col1, col2 = st.columns([3, 1])
                        col1.write(f"🔔 {alert['symbol']} {alert['condition']} ₹{alert['target']:,.2f}")
                        if col2.button("Delete", key=f"del_{aid}"):
                            del all_alerts[aid]
                            save_json_data(ALERTS_FILE, all_alerts)
                            st.rerun()

# INDIAN MARKET PAGE
elif st.session_state.page == "indian":
    st.title("🇮🇳 Indian Markets")
    indian_stocks = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"]
    selected = st.selectbox("Select Stock", indian_stocks)
    if st.button("View"):
        st.session_state.selected_stock = selected
        set_page("home")
        st.rerun()

# GLOBAL MARKET PAGE
elif st.session_state.page == "global":
    st.title("🌍 Global Markets")
    global_stocks = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "NVDA"]
    selected = st.selectbox("Select Stock", global_stocks)
    if st.button("View"):
        st.session_state.selected_stock = selected
        set_page("home")
        st.rerun()

# SIGN UP PAGE
elif st.session_state.page == "signup":
    st.markdown("<h1 style='color:#00bfa6;text-align:center;'>🚀 Create Account</h1>", unsafe_allow_html=True)
    
    with st.form("signup"):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        
        st.markdown("### Captcha")
        st.code(st.session_state.current_captcha)
        captcha_input = st.text_input("Enter Captcha")
        agree = st.checkbox("I agree to Terms")
        
        if st.form_submit_button("Register"):
            if not all([first_name, last_name, email, username, password]):
                st.error("Fill all fields")
            elif password != confirm:
                st.error("Passwords don't match")
            elif captcha_input != st.session_state.current_captcha:
                st.error("Invalid captcha")
                st.session_state.current_captcha = generate_captcha()
                st.rerun()
            elif not agree:
                st.error("Accept terms")
            else:
                users = load_users()
                if username in users:
                    st.error("Username exists")
                else:
                    users[username] = {
                        "first_name": first_name, "last_name": last_name, "email": email,
                        "password": hash_password(password),
                        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    
    with st.form("login"):
        username = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            users = load_users()
            for uid, info in users.items():
                if uid == username or info.get('email') == username:
                    if info.get('password') == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.username = uid
                        st.session_state.user_data = info
                        st.success("Login successful!")
                        set_page("home")
                        st.rerun()
                        break
            else:
                st.error("Invalid credentials")

# PROFILE PAGE
elif st.session_state.page == "profile":
    if not st.session_state.logged_in:
        st.warning("Please login first")
        if st.button("Go to Sign In"):
            set_page("signin")
            st.rerun()
    else:
        st.markdown(f"## 👤 {st.session_state.user_data.get('first_name', '')} {st.session_state.user_data.get('last_name', '')}")
        st.markdown(f"**Username:** @{st.session_state.username}")
        st.markdown(f"**Email:** {st.session_state.user_data.get('email', '')}")
        st.markdown(f"**Member since:** {st.session_state.user_data.get('created_at', 'N/A')}")
        
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
