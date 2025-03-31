import telebot
import os
import threading
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

# Load Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = "https://tp-bot-free.railway.app"  # Corrected Railway URL

# Make sure CHANNEL_ID is properly formatted
if CHANNEL_ID and not CHANNEL_ID.startswith('@') and not CHANNEL_ID.startswith('-'):
    CHANNEL_ID = '@' + CHANNEL_ID

# Debugging: Check if environment variables are set
if not TOKEN:
    raise ValueError("BOT_TOKEN is missing. Check your Railway environment variables.")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID is missing. Check your Railway environment variables.")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL is missing. Set it in Railway.")

print("BOT_TOKEN:", TOKEN[:10] + "********")  # Hide most of the token for security
print("CHANNEL_ID:", CHANNEL_ID)
print("WEBHOOK_URL:", WEBHOOK_URL)

# Initialize Bot and Flask
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Command handler for /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    print(f"User {username} (ID: {user_id}) started the bot")
    try:
        bot.reply_to(message, "Welcome to Trading Signal Bot! Use /sendsignal to send a new trading signal or /test to test the bot.")
        print(f"Start message sent to user {username}")
    except Exception as e:
        print(f"Error sending start message: {e}")

# Add a test command to verify bot functionality
@bot.message_handler(commands=['test'])
def handle_test(message):
    user_id = message.from_user.id
    username = message.from_user.username
    print(f"User {username} (ID: {user_id}) is testing the bot")
    
    try:
        # Test reply to user
        bot.reply_to(message, "✅ Bot is working! This is a test message.")
        print(f"Test message sent to user {username}")
        
        # Test channel message
        try:
            test_message = f"🔄 Test message from @{username} (ID: {user_id})"
            bot.send_message(CHANNEL_ID, test_message)
            bot.reply_to(message, f"✅ Test message sent to channel {CHANNEL_ID}")
            print(f"Test message sent to channel {CHANNEL_ID}")
        except Exception as channel_error:
            bot.reply_to(message, f"❌ Error sending to channel: {str(channel_error)}")
            print(f"Error sending to channel: {channel_error}")
    except Exception as e:
        print(f"Error in test command: {e}")

# Add authorized users (you can modify this list)
AUTHORIZED_USERS = []  # Add user IDs here, e.g. [123456789, 987654321]

# Command handler for /sendsignal with authorization check
@bot.message_handler(commands=['sendsignal'])
def handle_send_signal_command(message):
    user_id = message.from_user.id
    
    # Check if user is authorized (skip check if AUTHORIZED_USERS is empty)
    if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
        bot.reply_to(message, "You are not authorized to send signals.")
        return
        
    msg = bot.reply_to(message, """
Please send your signal data in the following format:

Asset: BTC/USDT
Direction: BUY
Entry: 42000
Target: 45000
Stop Loss: 40000
Timeframe: 4h
""")
    bot.register_next_step_handler(msg, process_asset_step)

# Signal creation steps
def process_asset_step(message):
    try:
        chat_id = message.chat.id
        asset = message.text
        user_data = {"asset": asset}
        msg = bot.reply_to(message, f"Asset: {asset}\nNow enter the direction (BUY/SELL):")
        bot.register_next_step_handler(msg, process_direction_step, user_data)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}\nPlease try again with /sendsignal")

def process_direction_step(message, user_data):
    try:
        chat_id = message.chat.id
        direction = message.text
        if direction.upper() not in ["BUY", "SELL"]:
            msg = bot.reply_to(message, "Please enter either BUY or SELL:")
            bot.register_next_step_handler(msg, process_direction_step, user_data)
            return
        
        user_data["direction"] = direction.upper()
        msg = bot.reply_to(message, f"Direction: {direction.upper()}\nNow enter the entry price:")
        bot.register_next_step_handler(msg, process_entry_step, user_data)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}\nPlease try again with /sendsignal")

def process_entry_step(message, user_data):
    try:
        chat_id = message.chat.id
        entry = message.text
        user_data["entry"] = entry
        msg = bot.reply_to(message, f"Entry: {entry}\nNow enter the target price:")
        bot.register_next_step_handler(msg, process_target_step, user_data)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}\nPlease try again with /sendsignal")

def process_target_step(message, user_data):
    try:
        chat_id = message.chat.id
        target = message.text
        user_data["target"] = target
        msg = bot.reply_to(message, f"Target: {target}\nNow enter the stop loss:")
        bot.register_next_step_handler(msg, process_stoploss_step, user_data)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}\nPlease try again with /sendsignal")

def process_stoploss_step(message, user_data):
    try:
        chat_id = message.chat.id
        stop_loss = message.text
        user_data["stop_loss"] = stop_loss
        msg = bot.reply_to(message, f"Stop Loss: {stop_loss}\nNow enter the timeframe (e.g., 4h, 1d):")
        bot.register_next_step_handler(msg, process_timeframe_step, user_data)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}\nPlease try again with /sendsignal")

def process_timeframe_step(message, user_data):
    try:
        chat_id = message.chat.id
        timeframe = message.text
        user_data["timeframe"] = timeframe
        
        # Format and send the signal
        signal = format_signal(
            user_data["asset"],
            user_data["direction"],
            user_data["entry"],
            user_data["target"],
            user_data["stop_loss"],
            user_data["timeframe"]
        )
        
        # Preview the signal
        bot.send_message(chat_id, "Signal Preview:\n" + signal)
        msg = bot.reply_to(message, "Do you want to send this signal? (yes/no)")
        bot.register_next_step_handler(msg, confirm_send_signal, user_data, signal)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}\nPlease try again with /sendsignal")

def confirm_send_signal(message, user_data, signal):
    try:
        chat_id = message.chat.id
        answer = message.text.lower()
        
        if answer == "yes" or answer == "y":
            # Send to the channel
            bot.send_message(CHANNEL_ID, signal)
            bot.send_message(chat_id, "✅ Signal has been sent to the channel!")
        else:
            bot.send_message(chat_id, "❌ Signal sending cancelled.")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}\nPlease try again with /sendsignal")

# Remove any existing webhook before setting a new one
# Add delay and retry logic for webhook setup
def setup_webhook():
    try:
        print("Setting up webhook...")
        time.sleep(5)  # Wait 5 seconds before setting up webhook
        
        # First, get current webhook info
        current_webhook = bot.get_webhook_info()
        print(f"Current webhook URL: {current_webhook.url}")
        
        # Remove webhook if it exists
        if current_webhook.url:
            print("Removing existing webhook...")
            bot.remove_webhook()
            print("Existing webhook removed")
        
        time.sleep(2)  # Wait 2 seconds after removing webhook
        
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        print(f"Setting webhook to: {webhook_url}")
        
        # Set the webhook with max_connections parameter
        result = bot.set_webhook(url=webhook_url, max_connections=5)
        if result:
            print("Webhook setup successful")
        else:
            print("Webhook setup failed")
            
        # Verify webhook info
        webhook_info = bot.get_webhook_info()
        print(f"Webhook URL: {webhook_info.url}")
        print(f"Webhook has custom certificate: {webhook_info.has_custom_certificate}")
        print(f"Webhook pending updates: {webhook_info.pending_update_count}")
        print(f"Webhook max connections: {webhook_info.max_connections}")
        print(f"Webhook last error date: {webhook_info.last_error_date}")
        print(f"Webhook last error message: {webhook_info.last_error_message}")
        
    except telebot.apihelper.ApiTelegramException as e:
        if "Too Many Requests" in str(e):
            retry_after = int(str(e).split("retry after ")[1].split()[0])
            print(f"Rate limited by Telegram. Waiting {retry_after} seconds...")
            time.sleep(retry_after + 1)
            setup_webhook()  # Retry after waiting
        else:
            print(f"Telegram API error: {e}")
    except Exception as e:
        print(f"Error setting up webhook: {e}")

# Call the setup function instead of directly setting webhook
setup_webhook()

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Receive Telegram updates via webhook"""
    try:
        print("Webhook endpoint called!")
        update = request.get_json()
        print(f"Received update: {update}")
        
        if update:
            print("Processing update...")
            bot.process_new_updates([telebot.types.Update.de_json(update)])
            print("Update processed")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error in webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Signal Formatting Function
def format_signal(asset, direction, entry, target, stop_loss, timeframe):
    return f"""
🚀 **{asset} Signal**
📈 Direction: {direction}
🎯 Entry: {entry}
🎯 Target: {target}
🛑 Stop Loss: {stop_loss}
⏳ Timeframe: {timeframe}
"""

# Route to Send Signal
@app.route('/send_signal', methods=['POST'])
def send_signal():
    """Send trading signal to Telegram"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        required_fields = ["asset", "direction", "entry", "target", "stop_loss", "timeframe"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        signal = format_signal(
            data["asset"],
            data["direction"],
            data["entry"],
            data["target"],
            data["stop_loss"],
            data["timeframe"]
        )

        bot.send_message(CHANNEL_ID, signal)
        return jsonify({"message": "Signal sent successfully!"}), 200
    except Exception as e:
        print(f"Error sending signal: {e}")
        return jsonify({"error": str(e)}), 500

# Health check endpoint for Railway
@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    print("Health check received")
    return jsonify({
        "status": "Bot is running", 
        "timestamp": time.time(), 
        "uptime": "active",
        "service_name": "telegram-trading-bot"
    }), 200

# Improve keep-alive mechanism
def keep_alive():
    """Periodically ping the app to keep it running"""
    while True:
        try:
            # Sleep first to allow the server to fully start
            time.sleep(10)
            print("Keep-alive thread running...")
            
            # Ping our own health endpoint
            try:
                response = requests.get(f"{WEBHOOK_URL}")
                print(f"Keep-alive ping sent. Status: {response.status_code}")
            except Exception as ping_error:
                print(f"Error pinging health endpoint: {ping_error}")
            
            # Verify bot connection
            try:
                bot_info = bot.get_me()
                print(f"Bot connection verified: @{bot_info.username}")
            except Exception as bot_error:
                print(f"Error verifying bot connection: {bot_error}")
                
            # Sleep for the remainder of the interval
            time.sleep(50)  # Total 60 seconds interval
                
        except Exception as e:
            print(f"Keep-alive error: {e}")
            time.sleep(60)  # Wait a minute before trying again

# Start Flask
if __name__ == "__main__":
    print("Starting Flask server...")
    port = int(os.getenv("PORT", 8080))  # Use Railway's PORT env var or default to 8080
    print(f"Using port: {port}")
    
    # Start keep-alive thread
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=False)  # Changed to non-daemon
    keep_alive_thread.start()
    
    # Try to use polling as a fallback if webhook isn't working
    try:
        # Start a separate thread for polling
        def polling_thread():
            try:
                print("Starting polling as fallback...")
                bot.polling(none_stop=True, interval=0, timeout=20)
            except Exception as e:
                print(f"Polling error: {e}")
        
        # Start polling in a separate thread
        polling = threading.Thread(target=polling_thread)
        polling.daemon = True
        polling.start()
        
        # Start Flask server
        app.run(host="0.0.0.0", port=port, threaded=True)
    except Exception as e:
        print(f"Error starting Flask server: {e}")