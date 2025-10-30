import telebot
from datetime import date, timedelta
from PIL import Image, ImageDraw, ImageFont
import os
from flask import Flask, request
from telebot import types

BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Словарь для хранения выбранной продолжительности жизни каждого пользователя
user_life_expectancy = {}

# ---------- ФУНКЦИЯ СОЗДАНИЯ ИЗОБРАЖЕНИЯ ----------
def generate_life_weeks_image(birth_date, current_date, life_expectancy_years=80):
    total_weeks = life_expectancy_years * 52
    lived_weeks = (current_date - birth_date).days // 7
    lived_days = (current_date - birth_date).days
    remaining_weeks = total_weeks - lived_weeks
    remaining_days = remaining_weeks * 7

    cols = 52  # 52 недели в году
    rows = life_expectancy_years
    size = 10
    margin = 2
    top_space = 100

    img_width = cols * (size + margin) + margin + 60
    img_height = rows * (size + margin) + margin + top_space
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Моноширинный шрифт
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 14)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 18)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # Текст сверху
    text1 = f"Прожито: {lived_weeks} недель ({lived_days} дней)"
    text2 = f"Осталось примерно: {remaining_weeks} недель ({remaining_days} дней)"
    draw.text((10, 10), text1, fill="black", font=title_font)
    draw.text((10, 40), text2, fill="gray", font=font)

    # Подписи недель сверху (по 4 недели = ~1 месяц)
    for w in range(0, cols, 4):
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


# ---------- TELEGRAM БОТ ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    for years in [70, 80, 90]:
        markup.add(types.InlineKeyboardButton(f"{years} лет", callback_data=f"years_{years}"))
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я помогу тебе увидеть, как проходит твоя жизнь по неделям.\n\n"
        "Выбери предполагаемую продолжительность жизни:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("years_"))
def set_life_expectancy(call):
    years = int(call.data.split("_")[1])
    user_life_expectancy[call.from_user.id] = years
    bot.answer_callback_query(call.id, f"Выбрано: {years} лет")
    bot.send_message(
        call.message.chat.id,
        f"Отлично! Будем считать {years} лет.\nТеперь отправь дату рождения в формате: ДД.ММ.ГГГГ"
    )


@bot.message_handler(func=lambda message: True)
def send_life_image(message):
    try:
        birth_date = date.fromisoformat("-".join(reversed(message.text.split('.'))))
        current_date = date.today()
        years = user_life_expectancy.get(message.from_user.id, 80)  # по умолчанию 80 лет

        img = generate_life_weeks_image(birth_date, current_date, years)
        img.save("life.png")

        with open("life.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f"Вот твоя жизнь в неделях (расчёт до {years} лет) 🕰")
    except Exception as e:
        print("Ошибка:", e)
        bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.ММ.ГГГГ")


# ---------- FLASK ДЛЯ WEBHOOK ----------
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "✅ Bot is running and Flask server is alive!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200


if __name__ == "__main__":
    # Настройка webhook
    WEBHOOK_URL = f"https://lifetimerbot.onrender.com/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
