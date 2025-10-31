import telebot
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from PIL import Image, ImageDraw, ImageFont
import os
import json
from flask import Flask, request
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler
import random
import pytz

# ---------- НАСТРОЙКИ ----------
BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
DATA_FILE = "users.json"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
TIMEZONE = "Europe/Moscow"

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

# ---------- СОСТОЯНИЯ ----------
awaiting_birth_date_change = set()

# ---------- ЦИТАТЫ ----------
quotes = ["Жизнь не загадка, а процесс.", "Просто живи.", "Каждый день — шанс начать с нуля.", "Сегодня — начало остальной части твоей жизни.", "Не спеши. Успеешь."]

# ---------- ПОЗДРАВЛЕНИЯ ----------
birthday_msgs = [
    "🎉 С днём рождения! Ещё один виток вокруг солнца 🌍 Пусть впереди будет больше тёплых недель, чем позади ✨",
    "🥳 Поздравляю с днём рождения! Желаю много ярких и тёплых моментов в жизни ✌️",
    "🎈 С днём рождения! Пусть каждый день приносит радость и вдохновение 🌟"
]

new_year_msgs = [
    "🎇 С Новым годом! Пусть всё плохое останется в прошлом, а впереди будет место для лёгкости и вдохновения ✨",
    "🥂 С Новым годом! Пусть этот год будет без суеты — с правильными людьми и настоящими моментами ❤️",
    "🌟 С Новым годом! Желаю, чтобы мечты сами находили дорогу к тебе ✌️"
]

# ---------- ФУНКЦИИ ДЛЯ КАРТИНОК ----------
def generate_life_weeks_image(birth_date, current_date, life_expectancy_years=80):
    total_weeks = life_expectancy_years * 52
    lived_weeks = (current_date - birth_date).days // 7
    lived_days = (current_date - birth_date).days

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

    # перемещаем надписи выше, чтобы не пересекались
    draw.text((10, 10), f"Прожито: {lived_weeks} недель ({lived_days} дней)", fill="black", font=title_font)
    remaining_weeks = total_weeks - lived_weeks
    remaining_days = (birth_date + relativedelta(weeks=total_weeks) - current_date).days
    draw.text((10, 35), f"Осталось: {remaining_weeks} недель ({remaining_days} дней)", fill="gray", font=font)

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


def generate_life_months_image(birth_date, current_date, life_expectancy_years=80):
    total_months = life_expectancy_years * 12
    lived_months = (current_date.year - birth_date.year) * 12 + (current_date.month - birth_date.month)

    cols = 12
    rows = life_expectancy_years
    size = 20
    margin = 2
    left_space = 35
    top_space = 70  # подняли таблицу вниз, чтобы сверху поместились надписи

    img_width = cols * (size + margin) + margin + left_space + 20
    img_height = rows * (size + margin) + margin + top_space + 20
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 12)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 16)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # перенесли текст выше
    draw.text((10, 10), f"Прожито: {lived_months} месяцев", fill="black", font=title_font)
    remaining_months = total_months - lived_months
    draw.text((10, 30), f"Осталось: {remaining_months} месяцев", fill="gray", font=font)

    # цифры месяцев сверху
    for m in range(1, 13):
        x_pos = left_space + (m - 1) * (size + margin)
        draw.text((x_pos + 5, top_space - 18), str(m), fill="gray", font=font)

    # цифры лет слева
    for y in range(rows):
        y_pos = top_space + y * (size + margin) - 2
        draw.text((10, y_pos), str(y + 1), fill="gray", font=font)

    # прямоугольники
    for i in range(total_months):
        x = left_space + (i % cols) * (size + margin)
        y = top_space + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_months else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    return img

# ---------- КЛАВИАТУРА ----------
def main_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add("Изменить дату рождения", "Посмотреть жизнь по месяцам", "Изменить продолжительность жизни")
    return markup

# ---------- ФУНКЦИИ ОТПРАВКИ ----------
def send_life_image(user_id, include_quote=True):
    info = users.get(str(user_id), {})
    if "birth_date" not in info:
        return

    birth_date = datetime.fromisoformat(info["birth_date"]).date()
    years = info.get("life_expectancy", 80)
    img = generate_life_weeks_image(birth_date, date.today(), years)
    img.save("life.png")
    caption = ""
    if include_quote:
        caption = random.choice(quotes)
        caption += f"\n\nВот твоя жизнь в неделях (до {years} лет) 🕰"

    else:
        caption = f"Вот твоя жизнь в неделях (до {years} лет) 🕰"

    with open("life.png", "rb") as photo:
        bot.send_photo(user_id, photo, caption=caption, reply_markup=main_reply_keyboard())

def send_birthday(user_id):
    msg = random.choice(birthday_msgs)
    send_life_image(user_id, include_quote=False)
    bot.send_message(user_id, msg)

def send_new_year(user_id):
    msg = random.choice(new_year_msgs)
    send_life_image(user_id, include_quote=False)
    bot.send_message(user_id, msg)

# ---------- ПЛАНИРОВЩИК ----------
scheduler = BackgroundScheduler(timezone=TIMEZONE)

def daily_check():
    today = datetime.now(pytz.timezone(TIMEZONE)).date()
    for user_id_str, info in users.items():
        user_id = int(user_id_str)
        birth_date = datetime.fromisoformat(info.get("birth_date")).date()
        # Проверка ДР
        if birth_date.day == today.day and birth_date.month == today.month:
            send_birthday(user_id)
        else:
            # В обычные дни — обновляем таблицу с цитатой
            send_life_image(user_id, include_quote=True)

def new_year_check():
    today = datetime.now(pytz.timezone(TIMEZONE))
    if today.month == 1 and today.day == 1 and today.hour == 0:
        for user_id_str in users.keys():
            user_id = int(user_id_str)
            send_new_year(user_id)

scheduler.add_job(daily_check, "cron", hour=10, minute=0)  # каждый день в 10:00
scheduler.add_job(new_year_check, "cron", month=1, day=1, hour=0, minute=0)  # 1 января 00:00
scheduler.start()

# ---------- START, CALLBACK, MESSAGE HANDLER ----------
# (Тут вставляем весь твой код для /start, callback_query_handler и handle_message без изменений)

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
    WEBHOOK_URL = f"https://lifetimerbot.onrender.com/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
