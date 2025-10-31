import telebot
from datetime import date, datetime
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
    "Не пытайся остановить время — наполни его смыслом.",
    "Жизнь измеряется не годами, а моментами, которые нас меняют.",
    "Сегодня — начало остальной части твоей жизни.",
    "Прошлая неделя уже история. Новая — в твоих руках.",
    "Секунды превращаются в годы — не упусти мгновение.",
    "Иногда время летит, иногда тянется, но оно всегда твоё.",
    "Пока ты читаешь это, ты уже прожил ещё несколько секунд.",
    "Всё пройдёт — и это тоже.",
    "Мы не замечаем, как дни складываются в жизнь.",
    "Каждое утро — шанс начать заново.",
    "Тишина тоже течёт во времени.",
    "Никто не предупреждает, что «потом» наступает слишком быстро.",
    "Самое быстрое на свете — годы.",
    "Даже когда ничего не происходит — идёт жизнь.",
    "Вчерашние тревоги уже ничего не значат.",
    "Будущее приходит тихо, шаг за шагом.",
    "Каждый день — это чистый лист, который мы часто заполняем спешкой.",
    # можно добавить остальные цитаты из твоего списка...
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
awaiting_birth_date_change = set()  # пользователи, которые меняют дату

# ---------- СОЗДАНИЕ КАРТИНОК ----------
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

    draw.text((10, 10), f"Прожито: {lived_weeks} недель ({lived_days} дней)", fill="black", font=title_font)
    remaining_weeks = total_weeks - lived_weeks
    remaining_days = remaining_weeks * 7
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

def generate_life_months_image(birth_date, current_date, life_expectancy_years=80):
    total_months = life_expectancy_years * 12
    lived_months = (current_date.year - birth_date.year) * 12 + (current_date.month - birth_date.month)
    remaining_months = total_months - lived_months

    cols = 12
    rows = life_expectancy_years
    size = 20
    margin = 3
    left_space = 35
    top_space = 50

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

    draw.text((10, 10), f"Прожито: {lived_months} месяцев", fill="black", font=title_font)
    draw.text((10, 40), f"Осталось: {remaining_months} месяцев", fill="gray", font=font)

    for m in range(1, 13):
        x_pos = left_space + (m - 1) * (size + margin)
        draw.text((x_pos, top_space - 20), str(m), fill="gray", font=font)

    for y in range(rows):
        y_pos = top_space + y * (size + margin)
        draw.text((10, y_pos), str(y + 1), fill="gray", font=font)

    for i in range(total_months):
        x = left_space + (i % cols) * (size + margin)
        y = top_space + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_months else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    return img

# ---------- МЕНЮ И СТАРТ ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    markup = types.InlineKeyboardMarkup()
    # Если дата рождения у пользователя ещё нет, показываем только выбор продолжительности
    if user_id not in users or "birth_date" not in users[user_id]:
        for years in [70, 80, 90]:
            markup.add(types.InlineKeyboardButton(f"{years} лет", callback_data=f"years_{years}"))
        bot.send_message(message.chat.id, "👋 Привет! Выбери предполагаемую продолжительность жизни:", reply_markup=markup)
    else:
        # Если дата уже есть, показываем меню действий
        markup.add(types.InlineKeyboardButton("Изменить дату рождения", callback_data="change_date"))
        markup.add(types.InlineKeyboardButton("Посмотреть таблицу по месяцам", callback_data="months_table"))
        bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)


# ---------- ОБРАБОТКА КНОПОК ----------
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = str(call.from_user.id)

    if call.data.startswith("years_"):
        years = int(call.data.split("_")[1])
        if user_id not in users:
            users[user_id] = {}
        users[user_id]["life_expectancy"] = years
        save_users(users)
        bot.answer_callback_query(call.id, f"Выбрано: {years} лет")
        bot.send_message(call.message.chat.id, "Отлично! Теперь отправь дату рождения в формате: ДД.MM.ГГГГ")

    elif call.data == "change_date":
        awaiting_birth_date_change.add(user_id)
        bot.send_message(call.message.chat.id, "Отправь новую дату рождения в формате: ДД.MM.ГГГГ")

    elif call.data == "months_table":
        if user_id in users and "birth_date" in users[user_id]:
            birth_date = datetime.fromisoformat(users[user_id]["birth_date"]).date()
            years = users[user_id].get("life_expectancy", 80)
            img = generate_life_months_image(birth_date, date.today(), years)
            img.save("life_months.png")
            with open("life_months.png", "rb") as photo:
                bot.send_photo(call.message.chat.id, photo, caption=f"Вот твоя жизнь по месяцам (до {years} лет) 🕰")

# ---------- ОБРАБОТКА СООБЩЕНИЙ ----------
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

            years = users[user_id].get("life_expectancy", 80)
            img = generate_life_weeks_image(new_birth_date, date.today(), years)
            img.save("life.png")
            with open("life.png", "rb") as photo:
                bot.send_photo(message.chat.id, photo, caption=f"Вот твоя жизнь в неделях (до {years} лет) 🕰")
        except ValueError:
            bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.MM.ГГГГ")
    else:
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
                    caption=f"{quote}\n\nВот твоя жизнь в неделях (до {years} лет) 🕰"
                )
        except ValueError:
            bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.MM.ГГГГ")

# ---------- ПЛАНИРОВЩИК ----------
def send_weekly_updates():
    today = date.today()
    print("🔔 Еженедельная рассылка запущена", datetime.now())
    for user_id, info in users.items():
        try:
            if "birth_date" in info:
                birth_date = date.fromisoformat(info["birth_date"])
                years = info.get("life_expectancy", 80)
                img = generate_life_weeks_image(birth_date, today, years)
                img.save("life.png")
                quote = random.choice(quotes)
                try:
                    with open("life.png", "rb") as photo:
                        bot.send_photo(user_id, photo, caption=f"{quote}\n\nОбновлённая таблица на {today.strftime('%d.%m.%Y')} ✨")
                except Exception as e:
                    print(f"Не удалось отправить {user_id}: {e}")
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
