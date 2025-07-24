import os
import re
import requests
import threading
import time
import http.server
import socketserver
import telebot  # <--- THIS was missing
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


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
@bot.message_handler(commands=['weather'])
def handle_weather(message):
    try:
        parts = message.text.split(" ", 1)
        if len(parts) != 2:
            bot.reply_to(message, "⚠️ Please provide a city name.\nExample: /weather Addis Ababa")
            return

        input_city = parts[1].strip()
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={input_city}&limit=1&appid={WEATHER_API_KEY}"
        geo_response = requests.get(geo_url)
        geo_data = geo_response.json()

        if not geo_data:
            bot.reply_to(message, "❌ Couldn't find a matching city. Please check the spelling.")
            return

        # Extract corrected city name and coordinates
        city_name = geo_data[0]['name']
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        country = geo_data[0].get('country', '')

        # Now fetch weather data using lat/lon
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        weather_response = requests.get(weather_url)
        data = weather_response.json()

        if data.get("cod") != 200:
            bot.reply_to(message, f"❌ Weather not found for {city_name}")
            return

        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]

        reply = (
            f"🌍 Weather in {city_name}, {country}\n"
            f"🌡 Temperature: {temp}°C\n"
            f"🌤 Description: {desc}\n"
            f"💧 Humidity: {humidity}%\n"
            f"🌬 Wind Speed: {wind} m/s"
        )

        bot.reply_to(message, reply)

    except Exception as e:
        print("Error:", e)
        bot.reply_to(message, "❗ An error occurred. Please try again later.")

    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="🔮 5-Day Forecast", callback_data=f"forecast:{city}")
    keyboard.add(button)
    bot.send_message(message.chat.id, "Do you want the 5-day forecast?", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("forecast:"))
def handle_forecast_callback(call):
    city = call.data.split(":", 1)[1]
    try:
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(forecast_url)
        data = response.json()

        if data.get("cod") != "200":
            bot.send_message(call.message.chat.id, f"❌ Forecast not available for {city}.")
            return

        message_lines = [f"🔮 5-Day Forecast for *{city.title()}*:"]
        for i in range(0, 40, 8):  # Every 8th = roughly 1 forecast per day (3-hour intervals × 8 = 24h)
            entry = data["list"][i]
            date = entry["dt_txt"].split(" ")[0]
            desc = entry["weather"][0]["description"].title()
            temp = entry["main"]["temp"]
            message_lines.append(f"📅 {date}: {temp}°C, {desc}")

        forecast_msg = "\n".join(message_lines)
        bot.send_message(call.message.chat.id, forecast_msg, parse_mode="Markdown")

    except Exception as e:
        print("Forecast error:", e)
        bot.send_message(call.message.chat.id, "⚠️ Failed to get the forecast.")

# === Fallback for unknown input ===
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.reply_to(message, "❓ Try /weather <city> or /location to get the weather.")

# === Start polling ===
print("Bot is running...")
bot.infinity_polling()
