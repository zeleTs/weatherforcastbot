import os
import telebot
import requests

# === Configuration ===
BOT_TOKEN = "7676117456:AAHoTyyxV8ILubH4qlgSMkoOOPPQ5yZCYVM"
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
bot = telebot.TeleBot(BOT_TOKEN)

# === /start command ===
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

# === /weather command ===
@bot.message_handler(commands=['weather'])
def handle_weather(message):
    try:
        parts = message.text.split(" ", 1)
        if len(parts) != 2:
            bot.reply_to(message, "⚠️ Please provide a city name.\nExample: /weather London")
            return

        city = parts[1]
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        print("API response:", data)

        if data.get("cod") != 200:
            bot.reply_to(message, f"❌ City not found: {city}")
            return

        weather = data['weather'][0]['description'].title()
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        wind = data['wind']['speed']

        reply = (
            f"🌍 Weather in *{city.title()}*\n"
            f"🌡 Temperature: {temp}°C\n"
            f"🌤 Description: {weather}\n"
            f"💧 Humidity: {humidity}%\n"
            f"🌬 Wind Speed: {wind} m/s"
        )
        bot.send_message(message.chat.id, reply, parse_mode="Markdown")

    except Exception as e:
        print("Error:", e)
        bot.reply_to(message, "⚠️ Something went wrong while fetching the weather.")

# === Unknown message fallback ===
@bot.message_handler(func=lambda message: True)
def fallback(message):
    bot.reply_to(message, "❓ Try /weather <city>")

# === Start polling ===
print("Bot is running...")
bot.infinity_polling()
