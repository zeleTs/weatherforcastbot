import os
import re
import threading
import time
import http.server
import socketserver
import telebot  # <--- THIS was missing
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def keep_alive():
    PORT = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving dummy HTTP on port {PORT}")
        httpd.serve_forever()

threading.Thread(target=keep_alive).start()

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# === Configuration ===
BOT_TOKEN =  os.environ.get("BOT_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
bot = telebot.TeleBot(BOT_TOKEN)

# === /start command ===
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message,
        "🌤️ Welcome to Weather Bot!\n"
        "Use /weather <city> to get weather info.\n"
        "Or /location to share your current location.")

# === /location command — asks for user location ===
@bot.message_handler(commands=['location'])
def ask_for_location(message):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = KeyboardButton(text="📍 Send Location", request_location=True)
    markup.add(button)
    bot.send_message(message.chat.id, "📍 Please share your location:", reply_markup=markup)

# === Handle user-shared location ===
@bot.message_handler(content_types=['location'])
def handle_location(message):
    try:
        lat = message.location.latitude
        lon = message.location.longitude
        
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        if data.get("cod") != 200:
            bot.reply_to(message, "❌ Could not fetch weather for this location.")
            return
        
        city = data.get('name', 'your location')
        weather = data['weather'][0]['description'].title()
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        wind = data['wind']['speed']
        
        reply = (
            f"🌍 Weather at *{city}*\n"
            f"🌡 Temperature: {temp}°C\n"
            f"🌤 Description: {weather}\n"
            f"💧 Humidity: {humidity}%\n"
            f"🌬 Wind Speed: {wind} m/s"
        )
        bot.send_message(message.chat.id, reply, parse_mode="Markdown")
    
    except Exception as e:
        print("Error:", e)
        bot.reply_to(message, "⚠️ Something went wrong while fetching the weather for your location.")

# === /weather command for city search ===
@bot.message_handler(commands=['weather'])
def handle_weather(message):
    try:
        parts = message.text.split(" ", 1)
        if len(parts) != 2 or not re.fullmatch(r"[A-Za-z\s]+", parts[1]):
            bot.reply_to(message, "⚠️ Please provide a valid city name (letters and spaces only).\nExample: /weather London")
            return

        city = parts[1]
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            bot.reply_to(message, f"❌ City not found: {city}")
            return

        # Example response message (you may have this already)
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"].capitalize()
        bot.reply_to(message, f"🌡️ {city} weather: {temp}°C, {desc}")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")
        
# === Fallback for unknown input ===
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.reply_to(message, "❓ Try /weather <city> or /location to get the weather.")

# === Start polling ===
print("Bot is running...")
bot.infinity_polling()
