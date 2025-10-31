import telebot
from datetime import date, timedelta, datetime
from PIL import Image, ImageDraw, ImageFont
import os
import json
from flask import Flask, request
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler

# ---------- НАСТРОЙКИ ----------
BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
DATA_FILE = "users.json"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ---------- ЗАГРУЗКА / СОХРАНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ ----------
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_users()

# ---------- СОЗДАНИЕ КАРТИНКИ ----------
def generate_life_weeks_image(birth_date, current_date, life_expectancy_years=80):
    total_weeks = life_expectancy_years * 52
    lived_weeks = (current_date - birth_date).days // 7
    lived_days = (current_date - birth_date).days
    remaining_weeks = total_weeks - lived_weeks
    remaining_days = remaining_weeks * 7

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

    # Шрифт
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 14)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 18)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # Текст сверху
    draw.text((10, 10), f"Прожито: {lived_weeks} недель ({lived_days} дней)", fill="black", font=title_font)
    draw.text((10, 40), f"Осталось: {remaining_weeks} недель ({remaining_days} дней)", fill="gray", font=font)

    # Подписи недель сверху (4, 8, 12, ...)
    for w in range(4, cols + 1, 4):
        x_pos = left_space + (w - 1) * (size + margin)
        draw.text((x_pos, top_space - 18), str(w), fill="gray", font=font)

    # Подписи лет слева
    for y in range(rows):
        y_pos = top_space + y * (size + margin) - 5
        draw.text((10, y_pos), str(y + 1), fill="gray", font=font)

    # Сетка
    for i in range(total_weeks):
        x = left_space + (i % cols) * (size + margin)
        y = top_space + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_weeks else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    return img

# ---------- ОСНОВНАЯ ЛОГИКА ----------
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
    user_id = str(call.from_user.id)
    if user_id not in users:
        users[user_id] = {}
    users[user_id]["life_expectancy"] = years
    save_users(users)
    bot.answer_callback_query(call.id, f"Выбрано: {years} лет")
    bot.send_message(call.message.chat.id, f"Отлично! Теперь отправь дату рождения в формате: ДД.ММ.ГГГГ")

@bot.message_handler(func=lambda message: True)
def send_life_image(message):
    user_id = str(message.from_user.id)
    try:
        birth_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        current_date = date.today()
        years = users.get(user_id, {}).get("life_expectancy", 80)

        users[user_id]["birth_date"] = birth_date.isoformat()
        save_users(users)

        img = generate_life_weeks_image(birth_date, current_date, years)
        img.save("life.png")
        with open("life.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f"Вот твоя жизнь до {years} лет 🕰")

    except ValueError:
        bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.ММ.ГГГГ")

# ---------- ПЛАНИРОВЩИК (еженедельное обновление) ----------
def send_weekly_updates():
    today = date.today()
    for user_id, info in users.items():
        try:
            if "birth_date" in info:
                birth_date = date.fromisoformat(info["birth_date"])
                years = info.get("life_expectancy", 80)
                img = generate_life_weeks_image(birth_date, today, years)
                img.save("life.png")
                with open("life.png", "rb") as photo:
                    bot.send_photo(user_id, photo, caption=f"Обновлённая таблица на {today.strftime('%d.%m.%Y')} ✨")
        except Exception as e:
            print(f"Ошибка при обновлении для {user_id}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(send_weekly_updates, 'cron', day_of_week='mon', hour=10, minute=0)
scheduler.start()

# ---------- FLASK ----------
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "✅ Bot is running and Flask server is alive!"

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
