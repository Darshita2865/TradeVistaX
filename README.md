# 📈 TradeVistaX

TradeVistaX is a real-time financial analytics dashboard built using Streamlit that provides interactive stock market insights, live index tracking, candlestick charting, stock analysis, machine-learning-based predictions, alerts, and financial news — all within a modern web interface.

### LIVE DEMO LINK:
https://tradevistax-hgikrwdxaln4z4mtmwdphr.streamlit.app/


# 🚀 Features

## 📊 Live Market Summary
- Real-time NIFTY and SENSEX tracking
- Percentage gain/loss indicators
- Dynamic market updates

---

## 📈 Interactive Candlestick Charts
- Real-time stock visualization
- Multiple intervals:
  - 5m
  - 15m
  - 1h
  - 1d
- Adjustable periods:
  - 5 Days
  - 1 Month
  - 3 Months
  - 6 Months
  - 1 Year

---

## 🧠 AI-Based Stock Prediction
- LSTM neural network forecasting
- Predicted next-day stock prices
- Historical vs predicted comparison
- Accuracy estimation using MAPE

---

## 📉 Historical Stock Analysis
- Historical closing prices
- Moving averages:
  - MA10
  - MA20
  - MA50
- Summary statistics
- Interactive charts

---

## 📰 Top Financial News
- Live financial headlines using Finnhub API
- Market-related news updates
- Clickable article links

---

## 🔔 Price Alert System
- Custom stock price alerts
- Telegram integration support
- Active alerts management
- Trigger history tracking

---

## 🔐 Authentication UI
- Sign In interface
- Sign Up interface
- Session-based user management

---

# 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Streamlit | Web dashboard UI |
| yfinance | Live stock market data |
| pandas | Data manipulation |
| numpy | Numerical computations |
| matplotlib | Data visualization |
| mplfinance | Candlestick chart plotting |
| scikit-learn | ML preprocessing & metrics |
| TensorFlow | LSTM prediction model |
| requests | API communication |
| python-dotenv | Environment variable management |

---

# 📂 Project Structure

```bash
TradeVistaX/
│
├── assets/                    # Images & UI assets
├── app.py                     # Main Streamlit application
├── alerts.json                # Active alerts storage
├── history.json               # Triggered alerts history
├── requirements.txt           # Python dependencies
├── .gitignore
│
├── appdata.py                 # Utility/data functions
├── monitor.py                 # Monitoring utilities
├── config.toml                # Streamlit configuration
│
└── README.md
```

---

# ⚙️ Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/Darshita2865/TradeVistaX.git
cd TradeVistaX
```

---

## 2️⃣ Create Virtual Environment (Recommended)

### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables (Optional)

Create a `.env` file in the root directory:

```env
TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
FINNHUB_API_KEY=YOUR_FINNHUB_API_KEY
```

### APIs Used
- Finnhub API → Financial News
- Telegram Bot API → Alert Notifications

---

# ▶️ Run the Application

```bash
streamlit run app.py
```

---

# 📊 How It Works

Users can:

- View live market summaries
- Search stock symbols
- Analyze historical trends
- Visualize candlestick charts
- Generate stock predictions
- Track moving averages
- Read financial news
- Set price alerts
- Manage alerts history

---

# 🌐 Deployment

TradeVistaX can be deployed easily on:

- Streamlit Community Cloud
- Render
- Hugging Face Spaces

---

## Streamlit Cloud Deployment

1. Push code to GitHub
2. Visit:
   https://share.streamlit.io/
3. Select:
   - Repository
   - Branch
   - `app.py`
4. Deploy

---

# ⚠️ Important Notes

- Predictions are for educational purposes only.
- Stock market investments involve risk.
- Data accuracy depends on external APIs.
- Alert system currently uses local JSON storage.
- TensorFlow deployment may require Python 3.10/3.11.

---

# 🔮 Future Improvements

- Database integration
- User authentication backend
- Portfolio tracking
- Real-time websocket updates
- Advanced AI prediction models
- Dark/Light theme toggle
- Watchlist support

---

# 👩‍💻 Author

## Darshita

GitHub:
https://github.com/Darshita2865

---

# ⭐ Support

If you like this project:

- Star the repository ⭐
- Fork the project 🍴
- Contribute improvements 🚀

---

# 📜 License

This project is licensed under the MIT License.
