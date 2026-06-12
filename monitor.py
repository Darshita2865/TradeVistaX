import time
import json
import requests
import yfinance as yf
from datetime import datetime
import os
from dotenv import load_dotenv

# Load the secret from the .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")  # This reads from .env

CHECK_INTERVAL = 60  # seconds

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALERTS_FILE = os.path.join(BASE_DIR, "alerts.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

def load_json(filename):
    """Load JSON data from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filename, data):
    """Save JSON data to file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def send_telegram_message(chat_id, message):
    """Send message via Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        response = requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False

def check_alert_condition(condition, current_price, target):
    """Check if alert condition is met"""
    if condition == ">":
        return current_price >= target
    elif condition == "<":
        return current_price <= target
    return False

def get_current_price(symbol):
    """Get current price for a symbol"""
    try:
        # Try to get 5m interval data for more current price
        data = yf.download(symbol, period="1d", interval="5m", progress=False)
        
        if data.empty:
            # Fallback to 1d interval
            data = yf.download(symbol, period="1d", interval="1d", progress=False)
            
        if data.empty:
            return None
            
        current_price = float(data['Close'].iloc[-1])
        return current_price
    except Exception as e:
        print(f"❌ Error fetching price for {symbol}: {e}")
        return None

def monitor():
    """Main monitoring loop"""
    print("=" * 50)
    print("🚀 TradeVistaX Monitoring Engine Started")
    print("=" * 50)
    print(f"📁 Alerts file: {ALERTS_FILE}")
    print(f"📁 History file: {HISTORY_FILE}")
    print(f"⏱️  Checking every {CHECK_INTERVAL} seconds")
    print(f"🤖 Telegram Bot Token: {'✓ Loaded' if TOKEN else '✗ Missing'}")
    print("=" * 50)
    
    if not TOKEN:
        print("❌ ERROR: TELEGRAM_TOKEN not found in .env file!")
        print("Please add your Telegram bot token to the .env file")
        return
    
    loop_count = 0
    
    while True:
        try:
            loop_count += 1
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Load alerts and history
            alerts = load_json(ALERTS_FILE)
            history = load_json(HISTORY_FILE)
            updated = False

            active_alerts = {k: v for k, v in alerts.items() if v.get('status') == 'active'}
            
            if active_alerts:
                print(f"\n[{current_time}] 📊 Checking {len(active_alerts)} active alerts (Loop #{loop_count})")
            else:
                print(f"[{current_time}] 💤 No active alerts. Waiting...", end="\r")

            for alert_id, info in list(alerts.items()):
                if info.get("status") != "active":
                    continue

                symbol = info.get("symbol")
                condition = info.get("condition")
                target = info.get("target")
                chat_id = info.get("chat_id")
                user = info.get("user", "Unknown")

                if not all([symbol, condition, target, chat_id]):
                    print(f"⚠️ Invalid alert {alert_id}: missing required fields")
                    continue

                # Get current price
                current_price = get_current_price(symbol)
                
                if current_price is None:
                    print(f"⚠️ Could not fetch price for {symbol}")
                    continue

                # Check if alert condition is met
                if check_alert_condition(condition, current_price, target):
                    print(f"\n🎯 ALERT TRIGGERED for {symbol}!")
                    print(f"   Condition: Price {condition} {target}")
                    print(f"   Current Price: ₹{current_price:.2f}")
                    print(f"   User: {user}")
                    print(f"   Chat ID: {chat_id}")
                    
                    # Prepare message
                    message = f"""🔔 *TRADEVISTAX ALERT TRIGGERED* 🔔

📊 *Symbol:* {symbol}
📈 *Condition:* Price {condition} ₹{target}
💰 *Current Price:* ₹{current_price:.2f}
📅 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👤 *User:* {user}

⚠️ This is an automated alert from TradeVistaX."""
                    
                    # Send Telegram notification
                    if send_telegram_message(chat_id, message):
                        print(f"   ✅ Telegram notification sent successfully!")
                    else:
                        print(f"   ❌ Failed to send Telegram notification")
                    
                    # Move to history
                    info["triggered_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    info["triggered_price"] = round(current_price, 2)
                    info["status"] = "triggered"
                    
                    history[alert_id] = info
                    del alerts[alert_id]
                    updated = True
                    print(f"   📝 Alert moved to history")

            # Save updated files
            if updated:
                save_json(ALERTS_FILE, alerts)
                save_json(HISTORY_FILE, history)
                print(f"💾 Files saved successfully")
                print("-" * 50)

        except Exception as e:
            print(f"❌ Error in monitoring loop: {e}")
            import traceback
            traceback.print_exc()

        # Wait before next check
        time.sleep(CHECK_INTERVAL)

def test_telegram_connection():
    """Test Telegram bot connection"""
    print("\n📱 Testing Telegram Bot Connection...")
    
    if not TOKEN:
        print("❌ TELEGRAM_TOKEN not found in .env file")
        print("Please create a .env file with: TELEGRAM_TOKEN=your_token_here")
        return False
    
    # Get bot info
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Bot connected successfully!")
            print(f"   Bot Name: {bot_info['result']['first_name']}")
            print(f"   Bot Username: @{bot_info['result']['username']}")
            return True
        else:
            print(f"❌ Failed to connect to bot. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing bot connection: {e}")
        return False

def show_active_alerts():
    """Display currently active alerts"""
    alerts = load_json(ALERTS_FILE)
    active = {k: v for k, v in alerts.items() if v.get('status') == 'active'}
    
    if active:
        print("\n📋 Current Active Alerts:")
        print("-" * 50)
        for alert_id, info in active.items():
            print(f"   ID: {alert_id}")
            print(f"   User: {info.get('user', 'Unknown')}")
            print(f"   Symbol: {info.get('symbol')}")
            print(f"   Condition: {info.get('condition')} {info.get('target')}")
            print(f"   Set at: {info.get('set_at', 'Unknown')}")
            print("-" * 50)
    else:
        print("\n📋 No active alerts found")

def show_recent_history(limit=10):
    """Display recent triggered alerts"""
    history = load_json(HISTORY_FILE)
    
    if history:
        print(f"\n📜 Recent Triggered Alerts (Last {limit}):")
        print("-" * 60)
        
        # Sort by triggered time (newest first)
        sorted_history = sorted(history.items(), 
                              key=lambda x: x[1].get('triggered_at', ''), 
                              reverse=True)[:limit]
        
        for alert_id, info in sorted_history:
            print(f"   Symbol: {info.get('symbol')}")
            print(f"   Condition: {info.get('condition')} {info.get('target')}")
            print(f"   Triggered at: ₹{info.get('triggered_price')}")
            print(f"   Time: {info.get('triggered_at', 'Unknown')}")
            print("-" * 60)
    else:
        print("\n📜 No triggered alerts in history")

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # Test Telegram connection
            test_telegram_connection()
            sys.exit(0)
        elif sys.argv[1] == "--show-alerts":
            # Show active alerts
            show_active_alerts()
            sys.exit(0)
        elif sys.argv[1] == "--show-history":
            # Show recent history
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_recent_history(limit)
            sys.exit(0)
        elif sys.argv[1] == "--help":
            print("""
TradeVistaX Monitor - Usage:
    python monitor.py              # Start monitoring
    python monitor.py --test       # Test Telegram connection
    python monitor.py --show-alerts # Show active alerts
    python monitor.py --show-history [limit] # Show triggered history
            """)
            sys.exit(0)
    
    # Start monitoring
    try:
        # Test connection first
        test_telegram_connection()
        
        # Show active alerts before starting
        show_active_alerts()
        
        print("\n" + "=" * 50)
        print("Starting monitoring loop... Press Ctrl+C to stop")
        print("=" * 50 + "\n")
        
        monitor()
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
