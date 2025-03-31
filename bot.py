import telebot
import os
from flask import Flask, request

# Bot Token from BotFather
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Signal Template Function
def format_signal(asset, direction, entry, target, stop_loss, timeframe):
    return f"""
🚀 **{asset} Signal**
📈 Direction: {direction}
🎯 Entry: {entry}
🎯 Target: {target}
🛑 Stop Loss: {stop_loss}
⏳ Timeframe: {timeframe}
"""

# Command to send a signal
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

# Start the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

    TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

print("BOT_TOKEN:", TOKEN)  # Debugging line
print("CHANNEL_ID:", CHANNEL_ID)  # Debugging line

if not TOKEN:
    raise ValueError("BOT_TOKEN is missing. Please check your environment variables.")

import telebot
bot = telebot.TeleBot(TOKEN)