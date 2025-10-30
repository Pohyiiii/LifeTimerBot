import telebot
from datetime import date
from PIL import Image, ImageDraw

BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
bot = telebot.TeleBot(BOT_TOKEN)

# Функция для генерации изображения с неделями
def generate_life_weeks_image(birth_date, current_date):
    life_expectancy_years = 90
    total_weeks = life_expectancy_years * 52
    lived_weeks = (current_date - birth_date).days // 7
    lived_days = (current_date - birth_date).days

    cols = 52
    rows = life_expectancy_years
    size = 10
    margin = 2
    top_space = 80  # место для текста сверху

    img_width = cols * (size + margin) + margin + 60  # немного шире для подписей
    img_height = rows * (size + margin) + margin + top_space
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Шрифт
    try:
        font = ImageFont.truetype("arial.ttf", 14)
        title_font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # Заголовок
    text = f"Прожито: {lived_weeks} недель ({lived_days} дней)"
    draw.text((10, 10), text, fill="black", font=title_font)

    # Подписи недель сверху
    for w in range(0, cols, 5):
        draw.text((60 + w * (size + margin), top_space - 20), str(w + 1), fill="gray", font=font)

    # Подписи лет слева
    for y in range(rows):
        draw.text((10, top_space + y * (size + margin)), str(y + 1), fill="gray", font=font)

    # Сетка
    for i in range(total_weeks):
        x = 60 + (i % cols) * (size + margin)
        y = top_space + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_weeks else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    return img

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Привет! Я помогу тебе увидеть, как проходит твоя жизнь по неделям.\n"
        "Отправь мне дату своего рождения в формате: ДД.ММ.ГГГГ"
    )

@bot.message_handler(func=lambda message: True)
def send_life_image(message):
    try:
        birth_date = date.fromisoformat(
            "-".join(reversed(message.text.split('.')))
        )
        current_date = date.today()
        img = generate_life_weeks_image(birth_date, current_date)
        img.save("life.png")
        with open("life.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption="Вот твоя жизнь в неделях 🕰")
    except Exception:
        bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.ММ.ГГГГ")

bot.polling()
import os
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def run_bot():
    bot.polling(none_stop=True, interval=0)

threading.Thread(target=run_flask).start()

run_bot()
