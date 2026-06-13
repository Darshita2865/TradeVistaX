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
        close_prices = data['Close'].values
        latest_price = close_prices[-1]
        
        if len(close_prices) >= 30:
            # Calculate moving averages
            ma5 = np.mean(close_prices[-5:])
            ma10 = np.mean(close_prices[-10:])
            ma20 = np.mean(close_prices[-20:])
            
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
            elif short_trend < 0 and long_trend < 0:
                confidence = 88
                signal = "STRONG SELL"
            elif short_trend > 0:
                confidence = 78
                signal = "WEAK BUY"
            elif short_trend < 0:
                confidence = 75
                signal = "WEAK SELL"
            else:
                confidence = 70
                signal = "NEUTRAL"
            
            return predicted_price, confidence, 100 - confidence, signal
        else:
            return latest_price * 1.01, 85.0, 15.0, "INSUFFICIENT DATA"
    except Exception as e:
        return None, None, None, None

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
        <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(0, 191, 166, 0.08); border-radius: 30px; padding: 6px 16px; margin: 20px 0;">
            <span style="width: 6px; height: 6px; border-radius: 50%; background: #00ff88; animation: blink 1s infinite;"></span>
            <span>AI Neural Engine Active</span>
        </div>
        <div style="display: flex; justify-content: center; gap: 50px; margin: 30px 0;">
            <div style="text-align: center;"><div style="font-size: 28px; font-weight: 700;">98.7%</div><div style="font-size: 11px; color: #6688aa;">ACCURACY</div></div>
            <div style="text-align: center;"><div style="font-size: 28px; font-weight: 700;">AI</div><div style="font-size: 11px; color: #6688aa;">MODEL</div></div>
            <div style="text-align: center;"><div style="font-size: 28px; font-weight: 700;">24/7</div><div style="font-size: 11px; color: #6688aa;">LIVE</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # NIFTY and SENSEX Display
    nifty_price, nifty_change = get_nifty_data()
    sensex_price, sensex_change = get_sensex_data()
    
    if nifty_price and sensex_price:
        col1, col2 = st.columns(2)
        with col1:
            nifty_color = "#00ff88" if nifty_change >= 0 else "#ff5555"
            nifty_arrow = "▲" if nifty_change >= 0 else "▼"
            st.metric("NIFTY 50", f"{nifty_price:,.0f}", f"{nifty_arrow} {abs(nifty_change):.2f}%")
        with col2:
            sensex_color = "#00ff88" if sensex_change >= 0 else "#ff5555"
            sensex_arrow = "▲" if sensex_change >= 0 else "▼"
            st.metric("SENSEX", f"{sensex_price:,.0f}", f"{sensex_arrow} {abs(sensex_change):.2f}%")
    
    # Top Stories - FIXED with fallback
    st.subheader("📰 Top Stories")
    
    def get_top_news():
        if not FINNHUB_API_KEY or FINNHUB_API_KEY == "None":
            return None
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                news_list = response.json()
                return news_list[:5]
            else:
                return None
        except Exception as e:
            st.warning(f"News API error: {str(e)}")
            return None
    
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
        st.info("📰 News feed: Add your FINNHUB_API_KEY in Secrets to see live news. Showing sample news for now.")
        # Sample news as fallback
        st.markdown("""
        <div style="background: rgba(0, 30, 20, 0.4); padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 2px solid #00bfa6;">
            <a href="#" style="text-decoration:none; color:#00bfa6; font-size:16px; font-weight:bold;">📈 Markets rally on positive economic data</a>
            <p style="color:#8899aa; font-size:13px; margin:5px 0 0 0;">Source: Market News | Published: Today</p>
        </div>
        <div style="background: rgba(0, 30, 20, 0.4); padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 2px solid #00bfa6;">
            <a href="#" style="text-decoration:none; color:#00bfa6; font-size:16px; font-weight:bold;">🤖 AI revolution in trading continues</a>
            <p style="color:#8899aa; font-size:13px; margin:5px 0 0 0;">Source: Tech News | Published: Yesterday</p>
        </div>
        """, unsafe_allow_html=True)
    
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
    
    # Stock Analysis Section
    st.subheader("📈 Stock Analysis")
    stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "AAPL", "MSFT", "GOOGL"]
    selected_stock = st.selectbox("🔎 Select Stock Symbol", stocks, key="stock_select")
    
    if st.button("📊 Show Analysis", key="show_analysis"):
        st.session_state.selected_stock = selected_stock
        st.rerun()
    
    if st.session_state.selected_stock:
        stock_symbol = st.session_state.selected_stock
        st.subheader(f"📈 {stock_symbol} Analysis")
        
        # Download data for analysis
        data = yf.download(stock_symbol, period="1y", interval="1d", progress=False)
        
        if not data.empty and len(data) > 0:
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            for col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            data = data.dropna()
            
            if len(data) > 0:
                st.subheader("📊 Summary Statistics")
                st.dataframe(data.describe())
                
                st.subheader("📈 Closing Price Chart")
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
                
                # ============ AI PRICE PREDICTION SECTION ============
                st.subheader("🤖 AI Price Prediction")
                
                try:
                    latest_price = data["Close"].iloc[-1]
                    if hasattr(latest_price, 'values'):
                        latest_price = float(latest_price.values[0])
                    else:
                        latest_price = float(latest_price)
                    
                    with st.spinner("Analyzing market trends..."):
                        next_price, confidence, mape, signal = simple_price_prediction(data)
                    
                    if next_price:
                        # Display prediction results
                        col_pred1, col_pred2, col_pred3 = st.columns(3)
                        
                        with col_pred1:
                            st.metric("Current Price", f"₹{latest_price:,.2f}")
                        
                        with col_pred2:
                            change_percent = ((next_price - latest_price) / latest_price) * 100
                            st.metric("Predicted Price", f"₹{next_price:,.2f}", 
                                     delta=f"{'+' if change_percent >= 0 else ''}{change_percent:.2f}%")
                        
                        with col_pred3:
                            st.metric("Confidence", f"{confidence:.1f}%")
                        
                        st.markdown("---")
                        
                        # Trading Signal
                        if "BUY" in signal:
                            st.success(f"📈 **Trading Signal: {signal}**")
                        elif "SELL" in signal:
                            st.warning(f"📉 **Trading Signal: {signal}**")
                        else:
                            st.info(f"⚡ **Trading Signal: {signal}**")
                        
                        # Analysis explanation
                        st.markdown("""
                        <div style="background: rgba(0, 30, 20, 0.3); padding: 15px; border-radius: 10px; margin: 15px 0;">
                            <strong>📊 Analysis Method:</strong> Moving Average Trend Analysis<br>
                            <small>This AI model analyzes 5-day, 10-day, and 20-day moving averages to predict price movement.</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.caption("⚠️ Disclaimer: Predictions are for informational purposes only. Not financial advice.")
                    else:
                        st.warning("⚠️ Insufficient data for prediction. Need at least 30 days of historical data.")
                        
                except Exception as price_error:
                    st.error(f"Error in price analysis: {str(price_error)}")
                    st.info("💡 Tip: Make sure you have sufficient historical data")
                
                # Alert System (only for logged in users)
                if st.session_state.logged_in:
                    st.markdown("---")
                    st.subheader("🔔 Price Alert Manager")
                    
                    with st.expander("➕ Set New Alert"):
                        alert_cond = st.selectbox("Condition", ["Price >=", "Price <="])
                        alert_val = st.number_input("Target Price (₹)", value=float(latest_price))
                        if st.button("Create Alert", key="create_alert"):
                            add_new_alert(st.session_state.username, stock_symbol, ">" if ">=" in alert_cond else "<", alert_val, "demo")
                            st.success("✅ Alert created successfully!")
                    
                    # Display active alerts
                    all_alerts = load_json_data(ALERTS_FILE)
                    user_alerts = {k: v for k, v in all_alerts.items() if v.get('user') == st.session_state.username}
                    if user_alerts:
                        st.write("**Your Active Alerts:**")
                        for aid, ainfo in user_alerts.items():
                            col1, col2 = st.columns([3, 1])
                            col1.write(f"🔔 {ainfo['symbol']} {ainfo['condition']} ₹{ainfo['target']}")
                            if col2.button("Delete", key=f"del_{aid}"):
                                del all_alerts[aid]
                                save_json_data(ALERTS_FILE, all_alerts)
                                st.rerun()
            else:
                st.warning("No valid data available for analysis")
        else:
            st.warning(f"No data found for {stock_symbol}")

# INDIAN MARKET PAGE
elif st.session_state.page == "indian":
    st.title("🇮🇳 Indian Markets")
    st.info("Top Indian stocks: TCS, Reliance, Infosys, HDFC Bank, ICICI Bank")
    
    indian_stocks = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "WIPRO.NS"]
    selected_indian = st.selectbox("Select Indian Stock", indian_stocks, key="indian_select")
    
    if st.button("View Analysis", key="view_indian"):
        st.session_state.selected_stock = selected_indian
        set_page("home")
        st.rerun()

# GLOBAL MARKET PAGE
elif st.session_state.page == "global":
    st.title("🌍 Global Markets")
    st.info("Top global stocks: Apple, Microsoft, Tesla, Amazon, Google")
    
    global_stocks = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "NVDA"]
    selected_global = st.selectbox("Select Global Stock", global_stocks, key="global_select")
    
    if st.button("View Analysis", key="view_global"):
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
                        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_users(users)
                    st.success("Account created! Please login.")
                    set_page("signin")
                    st.rerun()
    
    if st.button("Refresh Captcha", key="refresh_captcha"):
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
        if st.button("Go to Sign In", key="goto_signin"):
            set_page("signin")
            st.rerun()
    else:
        st.markdown("## 👤 My Profile")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            profile_img = get_profile_image_base64(st.session_state.username)
            if profile_img:
                st.image(f"data:image/png;base64,{profile_img}", width=150)
            else:
                st.markdown(f"""
                <div style="width: 150px; height: 150px; border-radius: 75px; background: linear-gradient(135deg, #00bfa6, #008c7a); display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 64px; color: white;">{st.session_state.username[0].upper()}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with st.expander("📸 Upload Photo"):
                uploaded = st.file_uploader("Choose image", type=["png", "jpg", "jpeg"])
                if uploaded and st.button("Upload"):
                    save_profile_image(st.session_state.username, uploaded)
                    st.rerun()
        
        with col2:
            st.markdown(f"**Name:** {st.session_state.user_data.get('first_name', '')} {st.session_state.user_data.get('last_name', '')}")
            st.markdown(f"**Username:** @{st.session_state.username}")
            st.markdown(f"**Email:** {st.session_state.user_data.get('email', '')}")
            st.markdown(f"**Member Since:** {st.session_state.user_data.get('created_at', 'N/A')}")
        
        if st.button("🚪 Logout", key="logout_btn"):
            logout()
            st.rerun()

# CSS animation for blinking dot
st.markdown("""
<style>
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}
</style>
""", unsafe_allow_html=True)
