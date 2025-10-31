import telebot
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from PIL import Image, ImageDraw, ImageFont
import os
import json
import random
from telebot import types

# ---------- НАСТРОЙКИ ----------
BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
DATA_FILE = "users.json"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ---------- СПИСОК ЦИТАТ ----------
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

# ---------- СОСТОЯНИЯ ----------
awaiting_birth_date_change = set()  # пользователи, которые меняют дату

# ---------- СОЗДАНИЕ ТАБЛИЦЫ ПО НЕДЕЛЯМ ----------
def generate_life_weeks_image(birth_date, current_date, life_expectancy_years=80):
    total_weeks = life_expectancy_years * 52
    lived_weeks = (current_date - birth_date).days // 7
    lived_days = (current_date - birth_date).days
    remaining_days = (birth_date + relativedelta(years=life_expectancy_years) - current_date).days

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
    draw.text((10, 40), f"Осталось: {total_weeks - lived_weeks} недель ({remaining_days} дней)", fill="gray", font=font)

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

# ---------- СОЗДАНИЕ ТАБЛИЦЫ ПО МЕСЯЦАМ ----------
def generate_life_months_image(birth_date, current_date, life_expectancy_years=80):
    total_months = life_expectancy_years * 12
    lived_months = relativedelta(current_date, birth_date).years * 12 + relativedelta(current_date, birth_date).months
    remaining_months = total_months - lived_months

    cols = 12
    rows = life_expectancy_years
    size = 15
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

    draw.text((10, 10), f"Прожито: {lived_months} месяцев", fill="black", font=title_font)
    draw.text((10, 40), f"Осталось: {remaining_months} месяцев", fill="gray", font=font)

    for y in range(rows):
        y_pos = top_space + y * (size + margin) - 2
        draw.text((10, y_pos), str(y + 1), fill="gray", font=font)

    for i in range(total_months):
        x = left_space + (i % cols) * (size + margin)
        y = top_space + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_months else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    return img

# ---------- МЕНЮ И СТАРТ ----------
def main_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Изменить дату рождения", "Посмотреть жизнь по месяцам", "Выбрать продолжительность жизни")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup_inline = types.InlineKeyboardMarkup()
    for years in [70, 80, 90]:
        markup_inline.add(types.InlineKeyboardButton(f"{years} лет", callback_data=f"years_{years}"))

    bot.send_message(
        message.chat.id,
        "👋 Привет! Я помогу тебе увидеть, как проходит твоя жизнь по неделям.\n\n"
        "Выбери предполагаемую продолжительность жизни:",
        reply_markup=markup_inline
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

# ---------- ИЗМЕНЕНИЕ ДАТЫ ----------
@bot.message_handler(func=lambda message: message.text == "Изменить дату рождения")
def change_birth_date_request(message):
    user_id = str(message.from_user.id)
    awaiting_birth_date_change.add(user_id)
    bot.send_message(message.chat.id, "Отправь новую дату рождения в формате: ДД.MM.ГГГГ")

@bot.message_handler(func=lambda message: message.text == "Посмотреть жизнь по месяцам")
def show_life_months(message):
    user_id = str(message.from_user.id)
    if user_id not in users or "birth_date" not in users[user_id]:
        bot.send_message(message.chat.id, "Сначала установите дату рождения!")
        return
    birth_date = date.fromisoformat(users[user_id]["birth_date"])
    years = users[user_id].get("life_expectancy", 80)
    img = generate_life_months_image(birth_date, date.today(), years)
    img.save("life_months.png")
    with open("life_months.png", "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption=f"Вот твоя жизнь по месяцам до {years} лет 🕰")

@bot.message_handler(func=lambda message: message.text == "Выбрать продолжительность жизни")
def change_life_expectancy_request(message):
    markup_inline = types.InlineKeyboardMarkup()
    for years in [70, 80, 90]:
        markup_inline.add(types.InlineKeyboardButton(f"{years} лет", callback_data=f"years_{years}"))
    bot.send_message(message.chat.id, "Выбери продолжительность жизни:", reply_markup=markup_inline)

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

            years = users[user_id].get("life_expectancy", 80)
            img = generate_life_weeks_image(new_birth_date, date.today(), years)
            img.save("life.png")
            quote = random.choice(quotes)
            with open("life.png", "rb") as photo:
                bot.send_photo(message.chat.id, photo, caption=f"{quote}\n\nВот твоя жизнь в неделях (расчёт до {years} лет) 🕰", reply_markup=main_reply_keyboard())
        except ValueError:
            bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.MM.ГГГГ")

# ---------- ЗАПУСК БОТА ----------
print("Бот запущен ✌️")
bot.infinity_polling()
