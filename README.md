# 📈 TradeVistaX

TradeVistaX is a real-time financial analytics dashboard built using Streamlit that provides interactive stock market insights, live index tracking, candlestick charting, stock analysis, AI-based predictions using moving averages, alerts, and financial news — all within a modern web interface.

### LIVE DEMO LINK:
🔗 **[https://tradevistax-hgikrwdxaln4z4mtmwdphr.streamlit.app/](https://tradevistax-hgikrwdxaln4z4mtmwdphr.streamlit.app/)**

---

# 🚀 Features

## 📊 Live Market Summary
- Real-time NIFTY and SENSEX tracking
- Percentage gain/loss indicators
- Dynamic market updates

---

## 📈 Interactive Candlestick Charts
- Real-time stock visualization
- Multiple intervals:
  - 1m
  - 5m
  - 15m
  - 30m
  - 1h
  - 1d
- Adjustable periods:
  - 1 Month
  - 3 Months
  - 6 Months
  - 1 Year
  - 2 Years

---

## 🧠 AI-Based Stock Prediction
- **Moving Average Trend Analysis** (Lightweight & Fast)
- Predicted next-day stock prices
- Confidence score and accuracy metrics
- Trading signals (BUY/SELL/NEUTRAL)
- Works without heavy TensorFlow dependencies
- Instant predictions with 30+ days of historical data

---

## 📉 Historical Stock Analysis
- Historical closing prices
- Moving averages:
  - MA10 (10-day)
  - MA20 (20-day)
  - MA50 (50-day)
- Summary statistics (mean, min, max, etc.)
- Interactive price charts

---

## 📰 Top Financial News
- Live financial headlines using Finnhub API
- Market-related news updates
- Clickable article links
- Timestamp for each news article

---

## 🔔 Price Alert System
- Custom stock price alerts
- Telegram integration support
- Active alerts management
- Trigger history tracking
- Local JSON storage for alerts

---

## 🔐 Authentication UI
- Sign In interface
- Sign Up interface
- Password hashing (SHA256)
- Captcha verification
- Session-based user management
- Profile picture upload

---

## 👤 User Profile Management
- View profile information
- Edit profile details
- Change password
- Upload profile picture
- Account creation timestamp

---

# 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Streamlit** | Web dashboard UI |
| **yfinance** | Live stock market data |
| **pandas** | Data manipulation & analysis |
| **numpy** | Numerical computations |
| **matplotlib** | Data visualization |
| **mplfinance** | Candlestick chart plotting |
| **scikit-learn** | Data preprocessing |
| **requests** | API communication (Finnhub) |
| **python-dotenv** | Environment variable management |
| **streamlit-autorefresh** | Auto-refresh functionality |

> **Note:** This app uses a lightweight prediction model (Moving Average Trend Analysis) instead of TensorFlow LSTM for faster deployment and better cloud compatibility.

---

# 📂 Project Structure

```bash
TradeVistaX/
│
├── app.py                     # Main Streamlit application
├── appdata.py                 # Utility/data functions
├── monitor.py                 # Monitoring utilities
├── config.toml                # Streamlit configuration
│
├── alerts.json                # Active alerts storage
├── history.json               # Triggered alerts history
├── users.json                 # User authentication data
│
├── profile_images/            # User profile pictures
│
├── requirements.txt           # Python dependencies
├── .gitignore
├── .env.example               # Environment variables template
│
└── README.md
