
import streamlit as st
import base64
import os
import json
import time
import datetime
import requests
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_percentage_error
import tensorflow as tf
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv

load_dotenv()

# ==================== CONFIGURATION ====================//

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

if not TELEGRAM_TOKEN:
    st.warning("⚠️ TELEGRAM_TOKEN not found in .env file. Alert features will not work.")
if not FINNHUB_API_KEY:
    st.warning("⚠️ FINNHUB_API_KEY not found in .env file. News features may not work.")

ALERTS_FILE = "alerts.json"
HISTORY_FILE = "history.json"

# ==================== HELPER FUNCTIONS ====================

def load_json_data(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json_data(file_path, data):
    """Save JSON data to file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def add_new_alert(user, symbol, cond, target, chat_id):
    """Add a new price alert"""
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
    """Get NIFTY 50 current data"""
    try:
        df = yf.download("^NSEI", period="1d", interval="1m", progress=False)
        if df.empty:
            return None, None
        current = float(df["Close"].iloc[-1])
        open_price = float(df["Open"].iloc[0])
        change_pct = ((current - open_price) / open_price) * 100
        return current, float(change_pct)
    except:
        return None, None

def get_top_news():
    """Fetch top financial news using Finnhub API"""
    if not FINNHUB_API_KEY:
        return []
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url)
        news_list = response.json()
        return news_list[:5]  # Top 5 news
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

def get_base64(file_path):
    """Encode image to base64"""
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""

# ==================== SESSION STATE INITIALIZATION ====================

if "page" not in st.session_state:
    st.session_state.page = "home"
if "market_open" not in st.session_state:
    st.session_state.market_open = False
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ==================== HELPER FUNCTIONS FOR NAVIGATION ====================

def set_page(page):
    st.session_state.page = page
    st.session_state.market_open = False

def toggle_market():
    st.session_state.market_open = not st.session_state.market_open

# ==================== BACKGROUND IMAGE ====================

bg_path = os.path.join(os.path.dirname(__file__), "assets", "bg.png")
bg_b64 = get_base64(bg_path)

# ==================== CSS STYLES ====================

st.markdown(f"""
<style>
.block-container {{
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    background: transparent !important;
}}
.stApp {{
    background-image: url("data:image/png;base64,{bg_b64}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

.navbar-container {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    background: rgba(15,17,22,0.95);
    z-index: 999;
    padding: 0;
}}

div[data-testid="column"] {{
    display: flex;
    align-items: center;
    justify-content: center;
}}

.stButton button {{
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #e0e0e0 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 6px 20px !important;
    border-radius: 20px !important;
    min-width: 100px !important;
    height: 36px !important;
    line-height: 1 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
    margin: 0 !important;
    letter-spacing: 0.3px !important;
    white-space: nowrap !important;
    cursor: pointer !important;
}}

.stButton button:hover {{
    background: rgba(0, 191, 166, 0.15) !important;
    border-color: #00bfa6 !important;
    color: #00bfa6 !important;
    transform: translateY(-1px);
}}

div[data-testid="stHorizontalBlock"] {{
    gap: 20px !important;
    justify-content: flex-start !important;
    align-items: center !important;
}}

.get-started-btn button {{
    background: linear-gradient(135deg, #00bfa6, #00a88f) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
}}

.get-started-btn button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,191,166,0.3);
}}

.positive {{
    color: #00ff88;
}}

.negative {{
    color: #ff4d4d;
}}

/* Hide Streamlit UI */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

.content {{
    padding-top: 65px;
}}

@media (max-width: 992px) {{
    .stButton button {{
        padding: 4px 12px !important;
        min-width: 80px !important;
        font-size: 12px !important;
    }}
}}
</style>
""", unsafe_allow_html=True)

# ==================== NAVIGATION BAR ====================

st.markdown('<div class="navbar-container">', unsafe_allow_html=True)

col_home, col_markets, col_signin, col_getstarted, col_spacer, col_market_container, col_right = st.columns([0.8, 0.9, 0.8, 0.9, 2.5, 2.2, 1.2])

with col_home:
    if st.button("🏠 Home", key="nav_home", use_container_width=True):
        set_page("home")
        st.rerun()

with col_markets:
    if st.button("📊 Markets ▼", key="nav_markets", use_container_width=True):
        toggle_market()
        st.rerun()

with col_signin:
    if st.button("🔐 Sign In", key="nav_signin", use_container_width=True):
        set_page("signin")
        st.rerun()

with col_getstarted:
    st.markdown('<div class="get-started-btn">', unsafe_allow_html=True)
    if st.button("🚀 Get Started", key="nav_getstarted", use_container_width=True):
        set_page("signup")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Market Data Display
with col_market_container:
    nifty_price, nifty_change = get_nifty_data()
    sensex_df = yf.download("^BSESN", period="1d", interval="1m", progress=False)
    col_nifty, col_profile = st.columns([5, 1])
    if nifty_price is not None and not sensex_df.empty:
        sensex_price = float(sensex_df["Close"].iloc[-1])
        sensex_open = float(sensex_df["Open"].iloc[0])
        sensex_change = ((sensex_price - sensex_open) / sensex_open) * 100

        nifty_color = "#00ff88" if nifty_change >= 0 else "#ff4d4d"
        nifty_arrow = "▲" if nifty_change >= 0 else "▼"
        sensex_color = "#00ff88" if sensex_change >= 0 else "#ff4d4d"
        sensex_arrow = "▲" if sensex_change >= 0 else "▼"

        

        with col_nifty:
            st.markdown(f"""
            <div style="text-align:right; font-weight:700; font-size:14px; line-height:1.4; padding-right:10px;">
                📊 NIFTY {nifty_price:,.0f}
                <span style="color:{nifty_color}; margin-left:6px;">{nifty_arrow} {nifty_change:.2f}%</span>
                <br>
                📊 SENSEX {sensex_price:,.0f}
                <span style="color:{sensex_color}; margin-left:6px;">{sensex_arrow} {sensex_change:.2f}%</span>
            </div>
            """, unsafe_allow_html=True)

# Profile Dropdown
with col_profile:
    first_letter = "👤"
    if st.session_state.logged_in and st.session_state.username:
        first_letter = st.session_state.username[0].upper()

    with st.popover(first_letter):
        st.write(f"👋 {st.session_state.username if st.session_state.logged_in else 'Guest'}")
        if st.button("⚙️ Profile Settings", key="profile_settings_btn"):
            st.info("Profile settings page coming soon...")
        if st.button("❓ Help", key="help_btn"):
            st.info("Help section coming soon...")
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.success("Logged out successfully!")
            time.sleep(1)
            set_page("home")
            st.rerun()

# ==================== PAGE CONTENT ====================

# Home Page
if st.session_state.page == "home":
    st.markdown(f"""
    <div class="bg-section" style="position: relative; display: flex; align-items: center; justify-content: center; text-align: center;">
        <h1 style="color: white; font-size: 48px; font-weight: bold; text-align: center; text-shadow: 2px 2px 8px rgba(0,0,0,0.7); max-width: 900px; margin: 0 auto; line-height: 1.3;">
            Empower Your Financial Decisions with<br>Real-Time Stock Insights
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # News Section
    st.subheader("📰 Top Stories")
    news_items = get_top_news()
    if news_items:
        for news in news_items:
            published_time = datetime.datetime.fromtimestamp(news['datetime']).strftime('%Y-%m-%d %H:%M')
            st.markdown(f"""
            <div style="background-color: #161b22; padding: 15px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                <a href="{news['url']}" target="_blank" style="text-decoration:none; color:#00bfa6; font-size:16px; font-weight:bold;">
                    {news['headline']}
                </a>
                <p style="color:#c9d1d9; font-size:13px; margin:5px 0 0 0;">
                    Source: {news['source']} | Published: {published_time}
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No news available at the moment.")
    
    # Candlestick Chart Section
    st.title("📊 Live Candlestick Chart")
    symbol = st.text_input("Enter Stock Symbol (e.g. RELIANCE.NS or AAPL):", "RELIANCE.NS").upper().strip()
    interval = st.selectbox("Select Interval:", ["5m", "15m", "1h", "1d"], index=3)
    period = st.selectbox("Select Period:", ["5d", "1mo", "3mo", "6mo", "1y"], index=1)
    refresh_sec = st.slider("Auto-refresh every (seconds):", 30, 300, 60)
    st_autorefresh(interval=refresh_sec * 1000, limit=None, key="auto_refresh")
    
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            st.warning("⚠️ No data available for this stock or selected interval.")
        else:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = np.nan
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
            df.index = pd.to_datetime(df.index, errors='coerce')
            df = df[~df.index.duplicated(keep='first')].sort_index()
            
            if len(df) < 2:
                st.warning("⚠️ Not enough valid data to plot candlestick chart.")
            else:
                st.success(f"✅ Showing {symbol} | Interval: {interval} | Period: {period}")
                fig, ax = mpf.plot(df, type='candle', style='yahoo', volume=True, figsize=(12, 6), ylabel='Price', title=f"{symbol} Candlestick Chart", returnfig=True)
                st.pyplot(fig)
    except Exception as e:
        st.error(f"Error fetching candlestick data: {e}")
    
    # Stock Analysis Section
    st.subheader("🏠 Stock Analysis")
    stocks = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "WIPRO.NS", "HDFCBANK.NS"]
    selected_stock = st.selectbox("🔎 Select Stock Symbol", stocks)
    
    if st.button("Show Analysis"):
        st.session_state.selected_stock = selected_stock
    
    if "selected_stock" in st.session_state:
        stock_symbol = st.session_state.selected_stock
        st.subheader(f"📈 {stock_symbol} Analysis")
        
        try:
            start_date = '2018-01-01'
            end_date = datetime.datetime.today().strftime('%Y-%m-%d')
            data = yf.download(stock_symbol, start=start_date, end=end_date)
            
            if data.empty:
                st.warning(f"No data found for {stock_symbol}.")
            else:
                st.subheader("Historical Prices (Last 100 Days)")
                st.dataframe(data.tail(100))
                
                st.subheader("📊 Summary Statistics")
                summary = data.describe().drop(["25%", "50%", "75%"], errors="ignore")
                st.table(summary)
                
                st.subheader("📈 Closing Price")
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(data.index, data["Close"], color="blue", label="Closing Price")
                ax.set_xlabel("Date")
                ax.set_ylabel("Price")
                ax.legend()
                st.pyplot(fig)
                
                st.subheader("📉 Moving Averages (10, 20, 50 days)")
                data["MA10"] = data["Close"].rolling(10).mean()
                data["MA20"] = data["Close"].rolling(20).mean()
                data["MA50"] = data["Close"].rolling(50).mean()
                
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(data.index, data["Close"], label="Close", color="blue")
                ax.plot(data.index, data["MA10"], label="MA10", color="red")
                ax.plot(data.index, data["MA20"], label="MA20", color="green")
                ax.plot(data.index, data["MA50"], label="MA50", color="purple")
                ax.set_xlabel("Date")
                ax.set_ylabel("Price")
                ax.legend()
                st.pyplot(fig)
                
                # LSTM Prediction
                close_prices = data['Close'].values.reshape(-1, 1)
                scaler = MinMaxScaler(feature_range=(0, 1))
                scaled_data = scaler.fit_transform(close_prices)
                
                time_step = 60
                if len(scaled_data) <= time_step:
                    st.warning(f"Not enough historical data for LSTM prediction of {stock_symbol}.")
                else:
                    X, y = [], []
                    for i in range(time_step, len(scaled_data)):
                        X.append(scaled_data[i-time_step:i, 0])
                        y.append(scaled_data[i, 0])
                    
                    X = np.array(X)
                    y = np.array(y)
                    X = X.reshape(X.shape[0], X.shape[1], 1)
                    
                    model = tf.keras.Sequential()
                    model.add(tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
                    model.add(tf.keras.layers.LSTM(50))
                    model.add(tf.keras.layers.Dense(25))
                    model.add(tf.keras.layers.Dense(1))
                    model.compile(optimizer='adam', loss='mean_squared_error')
                    model.fit(X, y, batch_size=32, epochs=5, verbose=0)
                    
                    predicted = model.predict(X)
                    predicted_prices = scaler.inverse_transform(predicted)
                    actual_prices = scaler.inverse_transform(y.reshape(-1, 1))
                    mape = mean_absolute_percentage_error(actual_prices, predicted_prices) * 100
                    
                    hist_close = close_prices.flatten()
                    pred_plot = np.full_like(hist_close, fill_value=np.nan)
                    pred_plot[time_step:] = predicted_prices.flatten()
                    
                    st.subheader(f"{stock_symbol} Close Price & LSTM Predicted Price")
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(data.index, hist_close, color='blue', label='Historical Close')
                    ax.plot(data.index, pred_plot, color='red', label='Predicted Price')
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Price")
                    ax.legend()
                    st.pyplot(fig)
                    
                    latest_price = hist_close[-1]
                    next_input = scaled_data[-time_step:].reshape(1, time_step, 1)
                    next_pred = model.predict(next_input)
                    next_price = scaler.inverse_transform(next_pred)[0, 0]
                    
                    st.write(f"**Latest Price:** ₹ {latest_price:.2f}")
                    st.write(f"**Predicted Next Price:** ₹ {next_price:.2f}")
                    st.write(f"📉 Model MAPE: {mape:.2f}%")
                    st.write(f"✅ Approximate Accuracy: {100 - mape:.2f}%")
                    
                    # Alert System (only if logged in and token exists)
                    if st.session_state.logged_in and TELEGRAM_TOKEN:
                        st.markdown("---")
                        st.header("🔔 Live Alert Manager")
                        
                        with st.expander(f"➕ Set Quick Alert for {stock_symbol}", expanded=True):
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                alert_cond = st.selectbox("Condition", ["Price >=", "Price <="], key="cond")
                            with col_b:
                                alert_val = st.number_input("Target Price (₹)", value=float(next_price))
                            with col_c:
                                user_chat_id = st.text_input("Telegram Chat ID", value=st.session_state.get('chat_id', ""), type="password")
                            
                            if st.button("🚀 Schedule Alert"):
                                if user_chat_id:
                                    add_new_alert(st.session_state.username, stock_symbol, ">" if ">=" in alert_cond else "<", alert_val, user_chat_id)
                                    st.success(f"Alert for {stock_symbol} saved!")
                                else:
                                    st.error("Please enter a valid Telegram Chat ID.")
                        
                        st.subheader("📝 Active Alerts")
                        all_alerts = load_json_data(ALERTS_FILE)
                        user_alerts = {k: v for k, v in all_alerts.items() if v.get('user') == st.session_state.username}
                        
                        if user_alerts:
                            for aid, ainfo in user_alerts.items():
                                col_info, col_btn = st.columns([3, 1])
                                status_color = "🟢" if ainfo.get('status') == 'active' else "🟡"
                                col_info.write(f"{status_color} **{ainfo['symbol']}** {ainfo['condition']} {ainfo['target']}")
                                btn_label = "⏸️ Pause" if ainfo['status'] == 'active' else "▶️ Resume"
                                if col_btn.button(btn_label, key=aid):
                                    all_alerts[aid]['status'] = 'paused' if ainfo['status'] == 'active' else 'active'
                                    save_json_data(ALERTS_FILE, all_alerts)
                                    st.rerun()
                        else:
                            st.info("No active alerts.")
                        
                        st.subheader("📜 Triggered History")
                        hist_data = load_json_data(HISTORY_FILE)
                        u_hist = [v for v in hist_data.values() if v.get('user') == st.session_state.username]
                        if u_hist:
                            df_hist = pd.DataFrame(u_hist)
                            st.table(df_hist[['symbol', 'condition', 'target', 'triggered_price', 'triggered_at']])
                        else:
                            st.write("No alerts triggered yet.")
                    
                    st.info("⚠️ Disclaimer: Stock data and predictions are for informational purposes only and may not be 100% accurate. Trade at your own risk.")
        except Exception as e:
            st.error(f"Error: {e}")

# Indian Markets Page
elif st.session_state.page == "indian":
    st.markdown('</div>', unsafe_allow_html=True)
    st.title("📊 Indian Market")
    st.info("Example stocks: TCS, Reliance, Infosys, Wipro, HDFC")
    indian_stocks = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "WIPRO.NS", "HDFCBANK.NS"]
    selected_indian = st.selectbox("Select Indian Stock", indian_stocks)
    if st.button("View Analysis", key="view_indian"):
        st.session_state.stock = selected_indian
        set_page("home")
        st.rerun()

# Global Markets Page
elif st.session_state.page == "global":
    st.markdown('</div>', unsafe_allow_html=True)
    st.title("🌍 Global Market")
    st.info("Example stocks: AAPL, MSFT, TSLA, AMZN, GOOGL")
    global_stocks = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL"]
    selected_global = st.selectbox("Select Global Stock", global_stocks)
    if st.button("View Analysis", key="view_global"):
        st.session_state.stock = selected_global
        set_page("home")
        st.rerun()

# Sign In Page
elif st.session_state.page == "signin":
    st.markdown('</div>', unsafe_allow_html=True)
    st.title("🔐 Sign In")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("signin_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)
            if submit:
                if username and password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Welcome back, {username}!")
                    time.sleep(1)
                    set_page("home")
                    st.rerun()
                else:
                    st.error("Please enter both username and password")

# Sign Up Page
elif st.session_state.page == "signup":
    st.markdown('</div>', unsafe_allow_html=True)
    st.title("🚀 Get Started")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("signup_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            if st.form_submit_button("Sign Up", use_container_width=True):
                if email and password and confirm_password:
                    if password == confirm_password:
                        st.success(f"Account created for {email}!")
                        time.sleep(1)
                        set_page("home")
                        st.rerun()
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill all fields")
