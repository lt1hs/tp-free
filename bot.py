import telebot
import os
from flask import Flask, request

# Load Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Use Railway-provided domain

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

# Set Webhook
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    """Receive Telegram updates via webhook"""
    update = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "OK", 200

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
    data = request.json
    signal = format_signal(
        data["asset"],
        data["direction"],
        data["entry"],
        data["target"],
        data["stop_loss"],
        data["timeframe"]
    )
    bot.send_message(CHANNEL_ID, signal)
    return "Signal sent!", 200

# Start Flask
if __name__ == "__main__":
    # Remove previous webhook before setting a new one
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")  # Set webhook
    app.run(host="0.0.0.0", port=5000)