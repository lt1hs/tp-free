import telebot
import os
from flask import Flask, request, jsonify

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

# Remove any existing webhook before setting a new one
bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Receive Telegram updates via webhook"""
    try:
        update = request.get_json()
        if update:
            bot.process_new_updates([telebot.types.Update.de_json(update)])
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

# Start Flask
if __name__ == "__main__":
    print("Starting Flask server...")
    port = int(os.getenv("PORT", 5000))  # Use Railway's PORT env var or default to 5000
    app.run(host="0.0.0.0", port=port)