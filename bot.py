import telebot
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from PIL import Image, ImageDraw, ImageFont
import os, json, random, time
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler

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
awaiting_birth_date_change = set()

# ---------- СПИСКИ ----------
quotes = [
    "Наша жизнь — цепочка дней, таких как сегодня.",
    "Каждая неделя — ещё один штрих твоей истории.",
    "Прошлая неделя уже история. Новая — в твоих руках.",
    "Жизнь измеряется не годами, а моментами, которые нас меняют.",
    "Пока ты читаешь это, ты уже прожил ещё несколько секунд.",
    "Каждый день — это чистый лист, который мы часто заполняем спешкой.",
    "Даже когда ничего не происходит — идёт жизнь.",
]

birthday_messages = [
    "🎉 С днём рождения!\nПобольше солнца, свободы и людей, рядом с которыми по-настоящему спокойно ✌️",
    "🥳 С днём рождения!\nЖелаю, чтобы музыка звучала, идеи рождались, и всё складывалось естественно 😌",
    "🌅 С днём рождения!\nПусть этот год принесёт ощущение, что всё идёт как надо, даже если пока непонятно куда 🙂",
    "🎈 Пусть будет светло, спокойно и по-своему красиво.\nА всё ненужное — просто отвалится само собой 💫",
    "🎉 Ещё один виток вокруг солнца 🌍\nПусть впереди будет больше тёплых недель, чем позади ✨",
]

newyear_messages = [
    "🎇 С Новым годом! Пусть всё плохое останется в прошлом, а впереди будет место для лёгкости, вдохновения и уютных вечеров ✨",
    "🥂 С праздником! Пусть этот год будет без суеты — с правильными людьми, вкусной едой и настоящими моментами ❤️",
    "🌟 С Новым годом! Желаю, чтобы мечты не просто сбывались, а сами находили дорогу к тебе ✌️",
    "🌟 С Новым годом! Пусть в сердце будет светло, даже если за окном темно 💫",
    "✨ Пусть в этом году каждый день будет как маленький подарок, который хочется открыть снова и снова 😌",
]

weekly_phrases = [
    "Ещё одна неделя прошла ✌️",
    "Прошла неделя — и это уже что-то.",
    "Небольшой отчёт: прошла ещё одна неделя твоей жизни.",
    "Надёжный чек: неделя прошла — время идёт.",
]

# ---------- КАРТИНКА ----------
def _load_font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

def generate_life_weeks_image(birth_date, current_date, life_expectancy_years=80):
    total_weeks = life_expectancy_years * 52
    lived_weeks = (current_date - birth_date).days // 7
    lived_days = (current_date - birth_date).days

    cols, rows = 52, life_expectancy_years
    size, margin, left, top = 10, 2, 35, 90
    img_width = cols * (size + margin) + margin + left + 20
    img_height = rows * (size + margin) + margin + top + 20
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    font, title_font = _load_font(14), _load_font(18)
    draw.text((10, 10), f"Прожито: {lived_weeks} недель ({lived_days} дней)", fill="black", font=title_font)
    remaining_weeks = max(total_weeks - lived_weeks, 0)
    remaining_days = (birth_date + relativedelta(weeks=total_weeks) - current_date).days
    draw.text((10, 36), f"Осталось: {remaining_weeks} недель ({remaining_days} дней)", fill="gray", font=font)

    for w in range(4, cols + 1, 4):
        draw.text((left + (w - 1) * (size + margin), top - 18), str(w), fill="gray", font=font)
    for y in range(rows):
        draw.text((10, top + y * (size + margin) + (size//2 - 6)), str(y + 1), fill="gray", font=font)
    for i in range(total_weeks):
        x = left + (i % cols) * (size + margin)
        y = top + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_weeks else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)
    return img

# ---------- КЛАВИАТУРА ----------
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Изменить дату рождения", "Жизнь в месяцах", "Изменить продолжительность жизни")
    return markup

# ---------- /START ----------
@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    for y in [70, 80, 90]:
        markup.add(types.InlineKeyboardButton(f"{y} лет", callback_data=f"years_{y}"))
    bot.send_message(message.chat.id, "👋 Привет! Выбери предполагаемую продолжительность жизни:", reply_markup=markup)

# ---------- CALLBACK ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("years_"))
def set_years(call):
    years = int(call.data.split("_")[1])
    uid = str(call.from_user.id)
    users.setdefault(uid, {})["life_expectancy"] = years
    save_users(users)
    bot.answer_callback_query(call.id, f"Выбрано: {years} лет")

    if "birth_date" in users[uid]:
        birth_date = datetime.fromisoformat(users[uid]["birth_date"]).date()
        img = generate_life_weeks_image(birth_date, date.today(), years)
        img.save("life.png")
        quote = random.choice(quotes)
        with open("life.png", "rb") as photo:
            bot.send_photo(call.message.chat.id, photo, caption=f"{quote}\n\nВот твоя жизнь в неделях 🕰", reply_markup=main_keyboard())
    else:
        bot.send_message(call.message.chat.id, "Отправь дату рождения в формате: ДД.MM.ГГГГ")

# ---------- СООБЩЕНИЯ ----------
@bot.message_handler(func=lambda m: True)
def messages(m):
    uid, text = str(m.from_user.id), m.text.strip()

    if uid in awaiting_birth_date_change:
        try:
            new_date = datetime.strptime(text, "%d.%m.%Y").date()
            users.setdefault(uid, {})["birth_date"] = new_date.isoformat()
            lived_weeks = (date.today() - new_date).days // 7
            users[uid]["last_sent_week"] = lived_weeks
            save_users(users)
            awaiting_birth_date_change.remove(uid)
            img = generate_life_weeks_image(new_date, date.today(), users[uid].get("life_expectancy", 80))
            img.save("life.png")
            quote = random.choice(quotes)
            with open("life.png", "rb") as photo:
                bot.send_photo(m.chat.id, photo, caption=f"{quote}\n\nВот твоя жизнь в неделях 🕰", reply_markup=main_keyboard())
        except ValueError:
            bot.reply_to(m, "⚠️ Введи дату в формате ДД.MM.ГГГГ")
        return

    if text == "Изменить дату рождения":
        awaiting_birth_date_change.add(uid)
        bot.send_message(m.chat.id, "Отправь новую дату рождения в формате: ДД.MM.ГГГГ")
        return

    if text == "Изменить продолжительность жизни":
        markup = types.InlineKeyboardMarkup()
        for y in [70, 80, 90]:
            markup.add(types.InlineKeyboardButton(f"{y} лет", callback_data=f"years_{y}"))
        bot.send_message(m.chat.id, "Выбери продолжительность:", reply_markup=markup)
        return

    # первая регистрация
    try:
        birth = datetime.strptime(text, "%d.%m.%Y").date()
        users.setdefault(uid, {})["birth_date"] = birth.isoformat()
        lived_weeks = (date.today() - birth).days // 7
        users[uid]["last_sent_week"] = lived_weeks
        save_users(users)
        img = generate_life_weeks_image(birth, date.today(), users[uid].get("life_expectancy", 80))
        img.save("life.png")
        quote = random.choice(quotes)
        with open("life.png", "rb") as photo:
            bot.send_photo(m.chat.id, photo, caption=f"{quote}\n\nВот твоя жизнь в неделях 🕰", reply_markup=main_keyboard())
    except ValueError:
        bot.reply_to(m, "⚠️ Введи дату в формате ДД.MM.ГГГГ")

# ---------- ПЛАНИРОВЩИК ----------
def check_and_send_updates():
    today = date.today()
    for uid, info in list(users.items()):
        try:
            if "birth_date" not in info: continue
            bdate = datetime.fromisoformat(info["birth_date"]).date()
            years = info.get("life_expectancy", 80)

            # День рождения
            if bdate.month == today.month and bdate.day == today.day:
                bot.send_message(int(uid), random.choice(birthday_messages))
                continue

            # Новый год
            if today.month == 1 and today.day == 1:
                bot.send_message(int(uid), random.choice(newyear_messages))
                continue

            # Еженедельная проверка
            lived_weeks = (today - bdate).days // 7
            last = info.get("last_sent_week", lived_weeks)
            if lived_weeks > last:
                img = generate_life_weeks_image(bdate, today, years)
                img.save("life.png")
                caption = f"{random.choice(weekly_phrases)}\n\n{random.choice(quotes)}"
                with open("life.png", "rb") as photo:
                    bot.send_photo(int(uid), photo, caption=caption)
                users[uid]["last_sent_week"] = lived_weeks
                save_users(users)
        except Exception as e:
            print(f"Ошибка для {uid}: {e}")

# ---------- ЗАПУСК ----------
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_updates, "cron", hour=0, minute=0)
scheduler.start()

print("✅ Бот запущен (polling + scheduler)")
bot.polling(none_stop=True, interval=1)
