import telebot
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from PIL import Image, ImageDraw, ImageFont
import os
import json
from flask import Flask, request
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler
import random

# ---------- НАСТРОЙКИ ----------
BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
DATA_FILE = "users.json"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ---------- СПИСОК ФРАЗ ----------
quotes = [
    "Наша жизнь — цепочка дней, таких как сегодня.",
    "Время не ждёт, но всегда идёт рядом.",
    "Каждая неделя — ещё один штрих твоей истории.",
    # ... добавьте остальные цитаты
]

# ---------- ЗАГРУЗКА / СОХРАНЕНИЕ ----------
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_users()
awaiting_birth_date_change = set()

# ---------- СОЗДАНИЕ ТАБЛИЦЫ ПО НЕДЕЛЯМ ----------
def generate_life_weeks_image(birth_date, current_date, life_expectancy_years=80):
    total_weeks = life_expectancy_years * 52
    lived_weeks = (current_date - birth_date).days // 7
    lived_days = (current_date - birth_date).days
    remaining_weeks = total_weeks - lived_weeks
    remaining_days = (total_weeks * 7) - lived_days

    cols = 52
    rows = life_expectancy_years
    size = 10
    margin = 2
    left_space = 35
    top_space = 90

    img_width = cols * (size + margin) + margin + left_space + 20
    img_height = rows * (size + margin) + margin + top_space + 20
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 14)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 18)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    draw.text((10, 10), f"Прожито: {lived_weeks} недель ({lived_days} дней)", fill="black", font=title_font)
    draw.text((10, 40), f"Осталось: {remaining_weeks} недель ({remaining_days} дней)", fill="gray", font=font)

    for w in range(4, cols + 1, 4):
        x_pos = left_space + (w - 1) * (size + margin)
        draw.text((x_pos, top_space - 18), str(w), fill="gray", font=font)

    for y in range(rows):
        y_pos = top_space + y * (size + margin) - 2
        draw.text((10, y_pos), str(y + 1), fill="gray", font=font)

    for i in range(total_weeks):
        x = left_space + (i % cols) * (size + margin)
        y = top_space + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_weeks else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    return img

# ---------- START ----------
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

# ---------- УСТАНОВКА ПРОДОЛЖИТЕЛЬНОСТИ ЖИЗНИ ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("years_"))
def set_life_expectancy(call):
    years = int(call.data.split("_")[1])
    user_id = str(call.from_user.id)
    if user_id not in users:
        users[user_id] = {}
    users[user_id]["life_expectancy"] = years
    save_users(users)
    bot.answer_callback_query(call.id, f"Выбрано: {years} лет")
    bot.send_message(call.message.chat.id, "Отлично! Теперь отправь дату рождения в формате: ДД.MM.ГГГГ")

# ---------- ОБРАБОТКА ДАТЫ ----------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)

    if user_id in awaiting_birth_date_change:
        try:
            new_birth_date = datetime.strptime(message.text, "%d.%m.%Y").date()
            if user_id not in users:
                users[user_id] = {}
            users[user_id]["birth_date"] = new_birth_date.isoformat()
            save_users(users)
            awaiting_birth_date_change.remove(user_id)
            bot.send_message(message.chat.id, f"Дата рождения обновлена: {message.text}")
        except ValueError:
            bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.MM.ГГГГ")
            return

    elif "birth_date" not in users.get(user_id, {}):
        try:
            birth_date = datetime.strptime(message.text, "%d.%m.%Y").date()
            years = users.get(user_id, {}).get("life_expectancy", 80)
            if user_id not in users:
                users[user_id] = {}
            users[user_id]["birth_date"] = birth_date.isoformat()
            save_users(users)

            img = generate_life_weeks_image(birth_date, date.today(), years)
            img.save("life.png")
            quote = random.choice(quotes)
            with open("life.png", "rb") as photo:
                bot.send_photo(
                    message.chat.id,
                    photo,
                    caption=f"{quote}\n\nВот твоя жизнь в неделях (расчёт до {years} лет) 🕰"
                )

            # Появление ReplyKeyboard после отправки таблицы
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("Изменить дату", "Посмотреть жизнь по месяцам", "Выбрать продолжительность жизни")
            bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)
        except ValueError:
            bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.MM.ГГГГ")

# ---------- ИЗМЕНЕНИЕ ДАТЫ ----------
@bot.message_handler(func=lambda message: message.text == "Изменить дату")
def change_birth_date(message):
    user_id = str(message.from_user.id)
    awaiting_birth_date_change.add(user_id)
    bot.send_message(message.chat.id, "Отправь новую дату рождения в формате: ДД.MM.ГГГГ")

# ---------- FLASK ----------
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "✅ Bot is running!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

if __name__ == "__main__":
    WEBHOOK_URL = f"https://YOUR_APP_URL/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
