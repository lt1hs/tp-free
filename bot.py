import telebot
import os
from flask import Flask, request
import threading

# Load Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Debugging: Check if environment variables are set
if not TOKEN:
    raise ValueError("BOT_TOKEN is missing. Check your Railway environment variables.")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID is missing. Check your Railway environment variables.")

print("BOT_TOKEN:", TOKEN[:10] + "********")  # Hide most of the token for security
print("CHANNEL_ID:", CHANNEL_ID)

# Initialize Bot and Flask
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

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

# Function to Start Flask
def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Function to Keep Bot Alive
def run_bot():
    bot.infinity_polling()  # Keeps bot running

# Run Flask and Bot in Parallel
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()  # Start Flask server
    run_bot()  # Start the Telegram bot