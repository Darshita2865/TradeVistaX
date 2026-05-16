import time
import json
import requests
import yfinance as yf
from datetime import datetime
import os
from dotenv import load_dotenv

# Load the secret from the .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- CONFIG ---
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHECK_INTERVAL = 60  # seconds

def load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def monitor():
    print("🚀 Monitoring Engine Started...")
    while True:
        alerts = load_json('alerts.json')
        history = load_json('history.json')
        updated = False

        for alert_id, info in list(alerts.items()):
            if info.get("status") != "active":
                continue

            try:
                # --- MODIFIED SECTION: Safer Price Fetching ---
                # Fetching 1-minute data for the symbol
                data = yf.download(info["symbol"], period="1d", interval="1m", progress=False)
                
                if data.empty:
                    print(f"⚠️ No data found for {info['symbol']}, skipping...")
                    continue
                
                current_price = float(data['Close'].iloc[-1])

                condition = info["condition"]
                target = info["target"]

                triggered = False
                if condition == ">" and current_price >= target:
                    triggered = True
                elif condition == "<" and current_price <= target:
                    triggered = True

                if triggered:
                    msg = f"🔔 ALERT: {info['symbol']}\nPrice {condition} {target}\nCurrent: {current_price:.2f}"
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                  data={"chat_id": info["chat_id"], "text": msg})
                    
                    info["triggered_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    info["triggered_price"] = round(current_price, 2)
                    info["status"] = "triggered"
                    
                    history[alert_id] = info
                    del alerts[alert_id]
                    updated = True
                    print(f"✅ Alert triggered for {info['symbol']}")

            except Exception as e:
                print(f"Error checking {info['symbol']}: {e}")

        if updated:
            save_json('alerts.json', alerts)
            save_json('history.json', history)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()
