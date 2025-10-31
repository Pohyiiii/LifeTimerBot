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

# ---------- НАСТРОЙКИ ----------
BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
DATA_FILE = "users.json"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

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
quotes = [
    "Жизнь не загадка, а процесс.",
    "Просто живи.",
    "Каждый день — шанс начать с нуля.",
    "Сегодня — начало остальной части твоей жизни.",
    "Не спеши. Успеешь."
]

# ---------- ПОЗДРАВЛЕНИЯ ----------
birthday_wishes = [
    "🎉 С днём рождения!\nПобольше солнца, свободы и людей, рядом с которыми по-настоящему спокойно ✌️",
    "🥳 С днём рождения!\nЖелаю, чтобы музыка звучала, идеи рождались, и всё складывалось естественно 😌",
    "😎 С днём рождения!\nПусть вдохновение приходит тогда, когда совсем не ждёшь, а рядом будут только те, кто заряжает ✨",
    "🫶 Ещё один год позади — но это только начало.\nПусть впереди будет много света, тишины и приятных случайностей 🍀",
    "🌅 С днём рождения!\nПусть этот год принесёт ощущение, что всё идёт как надо, даже если пока непонятно куда 🙂",
    "🎈 Пусть будет светло, спокойно и по-своему красиво.\nА всё ненужное — просто отвалится само собой 💫",
    "🌙 С днём рождения!\nЖелаю тебе меньше спешки, больше глубины и побольше тех вечеров, где просто хорошо быть 🌌",
    "🔆 Пусть этот год научит радоваться простому, верить в своё и не искать подтверждения снаружи.\nС днём рождения, человек с огнём внутри ❤️",
    "🎉 С днём рождения!\nЕщё один виток вокруг солнца 🌍 Пусть впереди будет больше тёплых недель, чем позади ✨"
]

new_year_wishes = [
    "🎇 С Новым годом! Пусть всё плохое останется в прошлом, а впереди будет место для лёгкости, вдохновения и уютных вечеров ✨",
    "🥂 С праздником! Пусть этот год будет без суеты — с правильными людьми, вкусной едой и настоящими моментами ❤️",
    "🌟 С Новым годом! Желаю, чтобы мечты не просто сбывались, а сами находили дорогу к тебе ✌️",
    "🎆 Пусть этот год будет как свежий воздух — чистый, бодрящий и полный новых идей 💡 🥂 С праздником!",
    "🌟 С Новым годом! Пусть в сердце будет светло, даже если за окном темно 💫",
    "🕯 Пусть в этом году будет больше света в доме и в душе, мгновений, которые хочется запомнить, и людей, рядом с которыми спокойно 🌿 С Новым годом!🎆",
    "🥂 Пусть каждый месяц нового года приносит что-то своё, свою радость, своё открытие и маленькую победу 💛 С Новым годом!🎆",
    "🔔 С праздником! Пусть в новом году будет больше смеха, светлых идей и уютных вечеров с теми, кто дорог ❤️",
    "🎇 С Новым годом! Желаю лёгкости, приятных сюрпризов и людей, с которыми тепло и спокойно 🌅",
    "✨ Пусть в этом году каждый день будет как маленький подарок, который хочется открыть снова и снова 😌"
]

# ---------- КАРТИНКИ ----------
def generate_life_weeks_image(birth_date, current_date, life_expectancy_years=80):
    total_weeks = life_expectancy_years * 52
    lived_weeks = (current_date - birth_date).days // 7

    cols, rows = 52, life_expectancy_years
    size, margin = 10, 2
    left_space, top_space = 35, 90

    img = Image.new("RGB", (cols * (size + margin) + left_space + 20, rows * (size + margin) + top_space + 20), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((10, 10), f"Прожито: {lived_weeks} недель", fill="black", font=font)

    for i in range(total_weeks):
        x = left_space + (i % cols) * (size + margin)
        y = top_space + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_weeks else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)
    return img

# ---------- ОСНОВНЫЕ ХЕНДЛЕРЫ ----------
def main_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Изменить дату рождения", "Посмотреть жизнь по месяцам", "Изменить продолжительность жизни")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup_inline = types.InlineKeyboardMarkup()
    for y in [70, 80, 90]:
        markup_inline.add(types.InlineKeyboardButton(f"{y} лет", callback_data=f"years_{y}"))
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я помогу тебе увидеть, как проходит твоя жизнь по неделям.\n\nВыбери предполагаемую продолжительность жизни:",
        reply_markup=markup_inline
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("years_"))
def set_life_expectancy(call):
    years = int(call.data.split("_")[1])
    user_id = str(call.from_user.id)
    users.setdefault(user_id, {})
    users[user_id]["life_expectancy"] = years
    save_users(users)

    if "birth_date" in users[user_id]:
        birth_date = datetime.fromisoformat(users[user_id]["birth_date"]).date()
        img = generate_life_weeks_image(birth_date, date.today(), years)
        img.save("life.png")
        quote = random.choice(quotes)
        with open("life.png", "rb") as photo:
            bot.send_photo(call.message.chat.id, photo, caption=f"{quote}\n\nВот твоя жизнь в неделях 🕰", reply_markup=main_reply_keyboard())
    else:
        bot.send_message(call.message.chat.id, "Отлично! Теперь отправь дату рождения в формате: ДД.MM.ГГГГ")

# ---------- ПЛАНИРОВЩИК ----------
def check_weekly_updates():
    today = date.today()
    for user_id, info in users.items():
        if "birth_date" not in info: continue
        birth_date = datetime.fromisoformat(info["birth_date"]).date()
        weeks_lived = (today - birth_date).days // 7
        last_sent = info.get("last_sent_week", -1)

        # Проверка на день рождения
        if today.day == birth_date.day and today.month == birth_date.month:
            bot.send_message(user_id, random.choice(birthday_wishes))
            info["last_sent_week"] = weeks_lived
            continue

        # Проверка на Новый год
        if today.day == 1 and today.month == 1:
            bot.send_message(user_id, random.choice(new_year_wishes))
            info["last_sent_week"] = weeks_lived
            continue

        # Новая неделя
        if weeks_lived > last_sent:
            img = generate_life_weeks_image(birth_date, today, info.get("life_expectancy", 80))
            img.save("life.png")
            with open("life.png", "rb") as photo:
                bot.send_photo(user_id, photo, caption=f"Ещё одна неделя прошла ✌️\n\n{random.choice(quotes)}")
            info["last_sent_week"] = weeks_lived

    save_users(users)

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

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    WEBHOOK_URL = f"https://lifetimerbot.onrender.com/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_weekly_updates, "interval", days=1)
    scheduler.start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
