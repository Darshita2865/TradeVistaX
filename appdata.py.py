import streamlit as st
import json
import base64
import os
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
import time
import requests
import mplfinance as mpf
from streamlit_autorefresh import st_autorefresh
import datetime
from sklearn.metrics import mean_absolute_percentage_error

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

# --- FILE PATH LOGIC ---
# This looks "up" one level from the /application folder to find the JSON files in the root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERTS_FILE = os.path.join(BASE_DIR, "..", "alerts.json")
HISTORY_FILE = os.path.join(BASE_DIR, "..", "history.json")

# Helper function to read JSON safely
def load_json_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Helper function to save JSON safely
def save_json_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def get_nifty_data():
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

# Helper: encode image
def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_path = os.path.join(os.path.dirname(__file__), "..", "assets", "bg.png")
bg_b64 = get_base64(bg_path)

# Session State
if "page" not in st.session_state:
    st.session_state.page = "home"
if "market_open" not in st.session_state:
    st.session_state.market_open = False
    
#Login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# Helper functions
def set_page(page):
    st.session_state.page = page
    st.session_state.market_open = False

def toggle_market():
    st.session_state.market_open = not st.session_state.market_open

# CSS for navbar and dropdown
st.markdown(f"""
<style>

.block-container {{
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    background: transparent !important;
}}

/* Background image */
.bg-section {{
    background-image: url("data:image/png;base64,{bg_b64}");
    background-size: cover;
    background-position: center;
    height: 120vh;
    width: 99vw;
}}

/* Navbar - Original height restored */
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

/* Buttons styling */
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

/* Horizontal block spacing */
div[data-testid="stHorizontalBlock"] {{
    gap: 20px !important;
    justify-content: flex-start !important;
    align-items: center !important;
}}

/* Get Started button */
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

/* Market Data Container */
.market-data-container {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 10px;
    border-left: 1px solid rgba(255,255,255,0.1);
    border-right: 1px solid rgba(255,255,255,0.1);
    height: 40px;
}}

.market-item {{
    text-align: right;
}}

.market-label {{
    font-size: 10px;
    color: #a0a0a0;
    font-weight: 500;
    letter-spacing: 0.5px;
}}

.market-value {{
    font-size: 13px;
    font-weight: 700;
    color: white;
    margin: 2px 0;
}}

.market-change {{
    font-size: 10px;
    font-weight: 600;
}}

.positive {{
    color: #00ff88;
}}

.negative {{
    color: #ff4d4d;
}}

/* Dropdown */
.dropdown-menu {{
    position: fixed;
    top: 52px;
    left: 155px;
    background: #1e2430;
    border-radius: 8px;
    padding: 8px 0;
    width: 130px;
    z-index: 1000;
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}}

.dropdown-menu .stButton button {{
    width: 100%;
    background: transparent !important;
    border: none !important;
    color: #e0e0e0 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    height: auto !important;
    text-align: left !important;
    min-width: auto !important;
}}

.dropdown-menu .stButton button:hover {{
    background: rgba(0, 191, 166, 0.1) !important;
    color: #00bfa6 !important;
}}

/* Hide Streamlit UI */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* Content spacing */
.content {{
    padding-top: 65px;
}}

/* Fix spacing */
div[data-testid="column"] {{
    padding: 0 !important;
    display: flex;
    justify-content: center;
}}

.stVerticalBlock {{
    
    gap: 0 !important;
}}

/* Responsive design */
@media (max-width: 992px) {{
    .stButton button {{
        padding: 4px 12px !important;
        min-width: 80px !important;
        font-size: 12px !important;
    }}
    
    .market-data-container {{
        gap: 8px;
    }}
}}

</style>
""", unsafe_allow_html=True)


# Navbar implementation
st.markdown('<div class="navbar-container">', unsafe_allow_html=True)

# Create columns for navbar items - Adjusted ratios for better spacing
col_home, col_markets, col_signin, col_getstarted, col_spacer, col_market_container, col_right = st.columns([0.8, 0.9, 0.8, 0.9, 2.5, 2.2, 1.2])
# Home Button
with col_home:
    if st.button("🏠 Home", key="nav_home", use_container_width=True):
        set_page("home")
        st.rerun()

# Markets Button
with col_markets:
    if st.button("📊 Markets ▼", key="nav_markets", use_container_width=True):
        toggle_market()
        st.rerun()

# Sign In Button
with col_signin:
    if st.button("🔐 Sign In", key="nav_signin", use_container_width=True):
        set_page("signin")
        st.rerun()

# Get Started Button
with col_getstarted:
    st.markdown('<div class="get-started-btn">', unsafe_allow_html=True)
    if st.button("🚀 Get Started", key="nav_getstarted", use_container_width=True):
        set_page("signup")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- NIFTY + SENSEX ----------------
with col_market_container:

    nifty_price, nifty_change = get_nifty_data()
    sensex_df = yf.download("^BSESN", period="1d", interval="1m", progress=False)

    if nifty_price is not None and not sensex_df.empty:

        sensex_price = float(sensex_df["Close"].iloc[-1])
        sensex_open = float(sensex_df["Open"].iloc[0])
        sensex_change = ((sensex_price - sensex_open) / sensex_open) * 100

        # Colors & arrows
        nifty_color = "#00ff88" if nifty_change >= 0 else "#ff4d4d"
        nifty_arrow = "▲" if nifty_change >= 0 else "▼"

        sensex_color = "#00ff88" if sensex_change >= 0 else "#ff4d4d"
        sensex_arrow = "▲" if sensex_change >= 0 else "▼"

        # Layout (NIFTY + Profile)
        col_nifty, col_profile = st.columns([5, 1])

        # ✅ ORIGINAL STYLE (YOUR FIRST DESIGN — CLEAN INLINE)
        with col_nifty:
            st.markdown(f"""
            <div style="
                text-align:right;
                font-weight:700;
                font-size:14px;
                line-height:1.4;
                padding-right:10px;
            ">
                📊 NIFTY {nifty_price:,.0f}
                <span style="color:{nifty_color}; margin-left:6px;">
                    {nifty_arrow} {nifty_change:.2f}%
                </span>
                <br>
                📊 SENSEX {sensex_price:,.0f}
                <span style="color:{sensex_color}; margin-left:6px;">
                    {sensex_arrow} {sensex_change:.2f}%
                </span>
            </div>
            """, unsafe_allow_html=True)

# Profile Icon + Dropdown
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
if st.session_state.page == "home":
    st.markdown(f"""
    <div class="bg-section" style="position: relative; display: flex; align-items: center; justify-content: center; text-align: center;">
        <h1 style="
            color: white;
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.7);
            max-width: 900px;
            margin: 0 auto;
            line-height: 1.3;
        ">
            Empower Your Financial Decisions with<br>Real-Time Stock Insights
        </h1>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.page == "indian":
    st.title("📊 Indian Market")
    st.info("Example stocks: TCS, Reliance, Infosys, Wipro, HDFC")
    
    # Add some Indian market specific content
    indian_stocks = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "WIPRO.NS", "HDFCBANK.NS"]
    selected_indian = st.selectbox("Select Indian Stock", indian_stocks)
    
    if st.button("View Analysis", key="view_indian"):
        st.session_state.stock = selected_indian
        set_page("home")

elif st.session_state.page == "global":
    st.title("🌍 Global Market")
    st.info("Example stocks: AAPL, MSFT, TSLA, AMZN, GOOGL")
    
    # Add some global market specific content
    global_stocks = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL"]
    selected_global = st.selectbox("Select Global Stock", global_stocks)
    
    if st.button("View Analysis", key="view_global"):
        st.session_state.stock = selected_global
        set_page("home")

elif st.session_state.page == "signin":
    st.title("🔐 Sign In")
    
    col1, col2, col3 = st.columns([1,2,1])
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

elif st.session_state.page == "signup":
    st.title("🚀 Get Started")
    
    col1, col2, col3 = st.columns([1,2,1])
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

st.markdown('</div>', unsafe_allow_html=True)

#Top Stories Placeholder
st.subheader("📰 Top Stories")

FINNHUB_API_KEY = "d3ftkt1r01qqbh547q7gd3ftkt1r01qqbh547q80"

def get_top_news():
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url)
        news_list = response.json()
        return news_list[:5]  # Top 5 news
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

news_items = get_top_news()

if news_items:
    for news in news_items:
        published_time = datetime.datetime.fromtimestamp(news['datetime']).strftime('%Y-%m-%d %H:%M')
        # Styled news card
        st.markdown(f"""
        <div style="
            background-color: #161b22;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        ">
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

#Candlestick charts
#Page setup
st.set_page_config(page_title="Live Candlestick Chart", layout="wide")   #wrote in the browser UI or tab
st.title("📊 Live Candlestick Chart (Simulated Real-Time)")

#User Inputs
symbol = st.text_input("Enter Stock Symbol (e.g. RELIANCE.NS or AAPL):", "RELIANCE.NS").upper().strip()
interval = st.selectbox("Select Interval:", ["5m", "15m", "1h", "1d"], index=3)
period = st.selectbox("Select Period:", ["5d", "1mo", "3mo", "6mo", "1y"], index=1)

# Auto-refresh (simulates live updates)
refresh_sec = st.slider("Auto-refresh every (seconds):", 30, 300, 60)
st_autorefresh(interval=refresh_sec * 1000, limit=None, key="auto_refresh")

#Fetch Data
try:
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)

    if df.empty:
        st.warning("⚠️ No data available for this stock or selected interval.")
    else:
        # Handle MultiIndex columns (common in NSE intraday)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Ensure all required columns exist
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan

        # Convert numeric columns safely
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop rows with missing essential OHLC data
        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)

        # Fix index
        df.index = pd.to_datetime(df.index, errors='coerce')
        df = df[~df.index.duplicated(keep='first')].sort_index()

        # Plot if valid data exists
        if len(df) < 2:
            st.warning("⚠️ Not enough valid data to plot candlestick chart.")
        else:
            st.success(f"✅ Showing {symbol} | Interval: {interval} | Period: {period}")
            st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            #Plot Candlestick Chart
            fig, ax = mpf.plot(
                df,
                type='candle',
                style='yahoo',
                volume=True,
                figsize=(4,2),
                ylabel='Price',
                title=f"{symbol} Candlestick Chart",
                returnfig=True
            )
            st.pyplot(fig)

except Exception as e:
    st.error(f"Error fetching candlestick data: {e}")

#Stock Analysis
st.subheader("🏠 Stock Analysis")
stocks = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "WIPRO.NS", "HDFCBANK.NS"]
selected_stock = st.selectbox("🔎 Select Stock Symbol", stocks)

# Button to trigger showing analysis
if st.button("Show Analysis"):
    st.session_state.selected_stock = selected_stock

# Display detailed analysis only after selection
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
            # Historical Prices
            st.subheader("Historical Prices (Last 100 Days)")
            st.dataframe(data.tail(100))

            # Summary stats
            st.subheader("📊 Summary Statistics")
            summary = data.describe().drop(["25%", "50%", "75%"], errors="ignore")
            st.table(summary)

            # Closing Price Chart
            st.subheader("📈 Closing Price")
            fig, ax = plt.subplots(figsize=(6,3))
            ax.plot(data.index, data["Close"],color = "blue", label="Closing Price")
            ax.set_xlabel("Date")
            ax.set_ylabel("Price")
            ax.legend()
            st.pyplot(fig)

            # Moving Averages
            st.subheader("📉 Moving Averages (10, 20, 50 days)")
            data["MA10"] = data["Close"].rolling(10).mean()
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()

            fig, ax = plt.subplots(figsize=(6,3))
            ax.plot(data.index, data["Close"], label="Close",color = "blue")
            ax.plot(data.index, data["MA10"], label="MA10", color = "red")
            ax.plot(data.index, data["MA20"], label="MA20",color = "green")
            ax.plot(data.index, data["MA50"], label="MA50",color = "purple")
            ax.set_xlabel("Date")
            ax.set_ylabel("Price")
            ax.legend() 
            st.pyplot(fig)

            # LSTM Prediction (FIXED)
            close_prices = data['Close'].values.reshape(-1,1)
            scaler = MinMaxScaler(feature_range=(0,1))
            scaled_data = scaler.fit_transform(close_prices)

            time_step = 60
            if len(scaled_data) <= time_step:
                st.warning(f"Not enough historical data for LSTM prediction of {stock_symbol}.")
            else:
                # STEP 1: create dataset (ONLY append here)
                X, y = [], []
                for i in range(time_step, len(scaled_data)):
                    X.append(scaled_data[i-time_step:i, 0])
                    y.append(scaled_data[i, 0])

                # STEP 2: convert after loop
                X = np.array(X)
                y = np.array(y)

                # reshape
                X = X.reshape(X.shape[0], X.shape[1], 1)

                # STEP 3: build model ONCE
                model = tf.keras.Sequential()
                model.add(tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
                model.add(tf.keras.layers.LSTM(50))
                model.add(tf.keras.layers.Dense(25))
                model.add(tf.keras.layers.Dense(1))

                model.compile(optimizer='adam', loss='mean_squared_error')
                model.fit(X, y, batch_size=32, epochs=5, verbose=0)

                # predictions
                predicted = model.predict(X)
                predicted_prices = scaler.inverse_transform(predicted)

                actual_prices = scaler.inverse_transform(y.reshape(-1, 1))
                mape = mean_absolute_percentage_error(actual_prices, predicted_prices) * 100

                hist_close = close_prices.flatten()
                pred_plot = np.full_like(hist_close, fill_value=np.nan)
                pred_plot[time_step:] = predicted_prices.flatten()

                # plot
                st.subheader(f"{stock_symbol} Close Price & LSTM Predicted Price")
                fig, ax = plt.subplots(figsize=(6,3))
                ax.plot(data.index, hist_close,color = 'blue', label='Historical Close')
                ax.plot(data.index, pred_plot,color = 'red', label='Predicted Price')
                ax.set_xlabel("Date")
                ax.set_ylabel("Price")
                ax.legend()
                st.pyplot(fig)

                # next prediction
                latest_price = hist_close[-1]
                next_input = scaled_data[-time_step:].reshape(1, time_step, 1)
                next_pred = model.predict(next_input)
                next_price = scaler.inverse_transform(next_pred)[0,0]

                st.write(f"**Latest Price:** ₹ {latest_price:.2f}")
                st.write(f"**Predicted Next Price:** ₹ {next_price:.2f}")
                st.write(f"📉 Model MAPE: {mape:.2f}%")
                st.write(f"✅ Approximate Accuracy: {100 - mape:.2f}%")

                # --- ALERT SYSTEM (Add this right after st.write(f"**Predicted Next Price...")) ---
                if st.session_state.logged_in:
                    st.markdown("---")
                    st.header("🔔 Live Alert Manager")

                # 1. Quick Set for Current Stock
                with st.expander(f"➕ Set Quick Alert for {stock_symbol}", expanded=True):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        alert_cond = st.selectbox("Condition", ["Price >=", "Price <="], key="cond")
                    with col_b:
                        alert_val = st.number_input("Target Price (₹)", value=float(next_price))
                    with col_c:
                        user_chat_id = st.text_input("Telegram Chat ID", value=st.session_state.get('chat_id', ""),type = "password")

                    if st.button("🚀 Schedule Alert"):
                        if user_chat_id:
                            # Use the helper function we added earlier to keep code clean
                            add_new_alert(st.session_state.username, stock_symbol, ">" if ">=" in alert_cond else "<", alert_val, user_chat_id)
                            st.success(f"Alert for {stock_symbol} saved!")
                        else:
                            st.error("Please enter a valid Telegram Chat ID.")

                # 2. Manage Active Alerts
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

                # 3. History Panel
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
