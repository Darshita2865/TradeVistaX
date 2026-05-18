TradeVistaX

TradeVistaX is a real-time financial analytics dashboard built with Streamlit that provides interactive stock market insights. It integrates live market data (via yfinance), offers NIFTY & SENSEX tracking, candlestick charting, basic analysis, machine-learning-based predictions, alerts, and top news features — all within a sleek web UI.

🚀 Features

📊 Live Market Summary
Displays real-time prices and changes for NIFTY and SENSEX indices. 


📈 Interactive Candlestick Charts
Visualize stock price movement using different intervals and periods. 

🧠 Prediction Module
LSTM-based price forecasting for selected stocks.

📰 Top Financial News
Shows recent headlines using a news API (if API key provided). 

📉 Historical Stock Analysis
Summary statistics, moving averages, and visualizations.

⏱️ Alerts System
Users can register and set price alerts stored in JSON.

🔐 Authentication UI
Basic sign-in and sign-up system simulated in the interface. 

🛠️ Tech Stack
The dashboard uses popular Python libraries for data fetching, visualization, and ML:
Streamlit – UI & layout
yfinance – Market data streaming
pandas, numpy – Data handling
matplotlib, mplfinance – Plotting
scikit-learn & TensorFlow – Prediction modeling
requests – External API calls
dotenv – Environment variable support 

📦 Installation
Clone the repo
Bash
git clone https://github.com/Darshita2865/TradeVistaX.git
cd TradeVistaX

Install dependencies
Bash
pip install -r requirements.txt
(Packages include: streamlit, yfinance, pandas, numpy, matplotlib, mplfinance, scikit-learn, requests)

Create .env file (optional)

TELEGRAM_TOKEN=YOUR_TOKEN
FINNHUB_API_KEY=YOUR_API_KEY
Run the app
Bash

streamlit run app.py

🧠 How It Works
Once launched, users can:
View live index data and charts
Search any stock ticker (e.g., RELIANCE.NS)
Toggle between intervals & periods for charts
See historical data and predictions
Set custom price alerts (if logged in)
(Note: some features like Telegram alerts require valid tokens) �
GitHub

🗂️ Project Structure

TradeVistaX/
├── assets/                  # UI graphics & background
├── app.py                   # Main Streamlit application
├── monitor.py.py            # (possibly monitoring utilities)
├── config.toml.toml         # App configuration
├── appdata.py.py            # Data utilities
├── alerts.json              # Stored price alerts
├── history.json             # Triggered alerts log
├── requirements.txt        # Dependencies
├── .gitignore
(Filenames reflect what’s visible in the repo) 

📊 Usage Notes
Predictions and historical analytics are informational only. Use at your own risk.
Data frequency and accuracy depend on external APIs.
The alert system stores local JSON files and does not use a real database.

📄 License
This repository currently does not show a license file on GitHub — if you intend to open-source or share, consider adding one (e.g., MIT LICENSE).
