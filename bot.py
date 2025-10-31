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
import pytz

# ---------- НАСТРОЙКИ ----------
BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
DATA_FILE = "users.json"
TIMEZONE = "Europe/Moscow"  # используем для APScheduler
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
"Каждый прожитый день уходит навсегда.", 
"Не откладывай жизнь на завтра", 
"Мгновения уходят, и их нельзя вернуть.", 
"Смерть — лучший учитель ценить жизнь.", 
"Жизнь короче, чем кажется, и длиннее, чем думаешь.", 
"Каждая прожитая неделя — невозвратимая.", 
"Смерть — это напоминание жить.", 
"Каждый момент жизни уникален и неповторим.", 
"Не считай дни, делай дни значимыми.", 
"Жизнь — это сумма мгновений, которые ты осознаешь.", 
"Не бойся смерти, бойся прожить жизнь напрасно.", 
"Не жди идеального момента, он не придёт.", 
"Смерть — зеркало, показывающее цену каждого дня.", 
"Мы уходим раньше, чем понимаем это.", 
"Каждое утро — подарок, который невозможно вернуть.", 
"Прошлое не вернуть, будущее не предугадать.", 
"Жизнь — миг, и он пролетает быстро.", 
"Человеческая жизнь слишком коротка, чтобы тратить её впустую.", 
"Мы часто забываем, что конец ближе, чем кажется.", 
"Жизнь ускользает, пока мы ищем смысл.", 
"Смерть делает каждый день драгоценным.", 
"Мы не вечны, и это делает нас свободными."
"Счастливая жизнь — цепочка счастливых дней.", 
"Прими то, что есть, и найди радость в простом.", 
"Прямо сейчас — всё, что у тебя есть.", 
"Не держись за прошлое, оно ускользает.", 
"Не бойся остановки, она часть пути.", 
"Смотри на жизнь как на процесс, а не на результат.", 
"Малые радости делают жизнь большой.", 
"Не спеши, каждый шаг имеет значение.", 
"Замедление открывает глаза на красоту мира.", 
"Не нужно делать всё идеально, достаточно быть.", 
"В каждом дне есть место для света.", 
"Не каждый день нужно спешить, чтобы он был ценным.", 
"Твоя жизнь — это твой путь, а не чужие ожидания.", 
"Не ищи цель, иногда достаточно движения.", 
"Счастье — не пункт назначения, а путешествие.", 
"Сейчас — лучшее время быть живым.", 
"Прими неопределённость как часть жизни.", 
"Только момент здесь и сейчас реален.", 
"Счастье — это наблюдать, а не владеть.", 
"Не нужно торопиться, чтобы жизнь имела смысл.", 
"День за днём создаются годы, не пропускай их.", 
"Прими несовершенство как часть красоты.", 
"Настоящий момент — самое ценное.", 
"Малые шаги — часть великого пути.", 
"Мы лишь мгновение во вселенной.", 
"То, что потеряно, придаёт ценность тому, что есть.", 
"Всё проходит, и это прекрасно.", 
"Страх перед концом учит ценить начало.", 
"Ничто не длится вечно, и это делает жизнь драгоценной.", 
"То, что кажется мелким, может быть самым значимым.", 
"Жизнь — это мгновение, которое ты наблюдаешь.", 
"Прими смерть как часть жизни, и она станет яснее.", 
"Жизнь слишком коротка для пустых ссор.", 
"Не бойся быть уязвимым — это делает мгновения настоящими.", 
"Смерть — самая сильная мотивация жить.", 
"Каждая прожитая боль учит ценить радость.", 
"Все дороги ведут к концу, но каждый шаг — твой.", 
"Жизнь — цепочка мгновений, которые ты выбираешь видеть."
]


# ---------- ПРАЗДНИЧНЫЕ ПОЗДРАВЛЕНИЯ ----------
birthday_messages = [
    "🎉 С днём рождения!\nПобольше солнца, свободы и людей, рядом с которыми по-настоящему спокойно ✌️",
    "🥳 С днём рождения!\nЖелаю, чтобы музыка звучала, идеи рождались, и всё складывалось естественно 😌",
    "😎 С днём рождения!\nПусть вдохновение приходит тогда, когда совсем не ждёшь,\nа рядом будут только те, кто заряжает ✨",
    "🫶 Ещё один год позади — но это только начало.\nПусть впереди будет много света, тишины и приятных случайностей 🍀",
    "🌅 С днём рождения!\nПусть этот год принесёт ощущение, что всё идёт как надо,\nдаже если пока непонятно куда 🙂",
    "🎈 Пусть будет светло, спокойно и по-своему красиво.\nА всё ненужное — просто отвалится само собой 💫",
    "🌙 С днём рождения!\nЖелаю тебе меньше спешки, больше глубины\nи побольше тех вечеров, где просто хорошо быть 🌌",
    "🔆 Пусть этот год научит радоваться простому,\nверить в своё и не искать подтверждения снаружи.\nС днём рождения, человек с огнём внутри ❤️",
    "🎉 Ещё один виток вокруг солнца 🌍\nПусть впереди будет больше тёплых недель, чем позади ✨"
]

newyear_messages = [
    "🎇 С Новым годом! Пусть всё плохое останется в прошлом, а впереди будет место для лёгкости, вдохновения и уютных вечеров ✨",
    "🥂 С праздником! Пусть этот год будет без суеты — с правильными людьми, вкусной едой и настоящими моментами ❤️",
    "🌟 С Новым годом! Желаю, чтобы мечты не просто сбывались, а сами находили дорогу к тебе ✌️",
    "🎆 Пусть этот год будет как свежий воздух — чистый, бодрящий и полный новых идей. С праздником! 🥂",
    "🌟 С Новым годом! Пусть в сердце будет светло, даже если за окном темно 💫",
    "🕯 Пусть в этом году будет больше света в доме и в душе, мгновений, которые хочется запомнить, и людей, рядом с которыми спокойно 🌿",
    "🥂 Пусть каждый месяц нового года приносит что-то своё, свою радость, своё открытие и маленькую победу 💛",
    "🔔 С праздником! Пусть в новом году будет больше смеха, светлых идей и уютных вечеров с теми, кто дорог ❤️",
    "🎇 С Новым годом! Желаю лёгкости, приятных сюрпризов и людей, с которыми тепло и спокойно 🌅",
    "✨ Пусть в этом году каждый день будет как маленький подарок, который хочется открыть снова и снова 😌"
]

weekly_phrases = [
    "Ещё одна неделя прошла ✌️",
    "Вот и неделя пролетела",
    "Прошла ещё одна неделя твоей жизни.",
    "Неделя прошла",
    "Ещё одна неделя позади",
    "Прошла неделя",
    "А вот и я, снова напоминаю тебе как быстро летит время"
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
    top_space = 70

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

    draw.text((10, 10), f"Прожито: {lived_months} месяцев", fill="black", font=title_font)
    remaining_months = total_months - lived_months
    draw.text((10, 30), f"Осталось: {remaining_months} месяцев", fill="gray", font=font)

    for m in range(1, 13):
        x_pos = left_space + (m - 1) * (size + margin)
        draw.text((x_pos + 5, top_space - 18), str(m), fill="gray", font=font)

    for y in range(rows):
        y_pos = top_space + y * (size + margin) - 2
        draw.text((10, y_pos), str(y + 1), fill="gray", font=font)

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

# ---------- START ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup_inline = types.InlineKeyboardMarkup()
    for y in [70, 80, 90]:
        markup_inline.add(types.InlineKeyboardButton(f"{y} лет", callback_data=f"years_{y}"))
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я помогу тебе увидеть, как проходит твоя жизнь по неделям.\n\n"
        "Выбери предполагаемую продолжительность жизни:",
        reply_markup=markup_inline
    )

# ---------- CALLBACK ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("years_"))
def set_life_expectancy(call):
    years = int(call.data.split("_")[1])
    user_id = str(call.from_user.id)

    users.setdefault(user_id, {})
    users[user_id]["life_expectancy"] = years
    save_users(users)

    bot.answer_callback_query(call.id, f"Выбрано: {years} лет")

    if "birth_date" in users[user_id]:
        birth_date = datetime.fromisoformat(users[user_id]["birth_date"]).date()
        img = generate_life_weeks_image(birth_date, date.today(), years)
        img.save("life.png")
        quote = random.choice(quotes)
        with open("life.png", "rb") as photo:
            bot.send_photo(call.message.chat.id, photo,
                           caption=f"{quote}\n\nВот твоя жизнь в неделях (до {years} лет) 🕰",
                           reply_markup=main_reply_keyboard())
    else:
        bot.send_message(call.message.chat.id, "Отлично! Теперь отправь дату рождения в формате: ДД.MM.ГГГГ")

# ---------- ОБРАБОТКА СООБЩЕНИЙ (ДРУЖЕЛЮБНАЯ) ----------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    # Если пользователь меняет дату
    if user_id in awaiting_birth_date_change or "birth_date" not in users.get(user_id, {}):
        try:
            new_birth_date = datetime.strptime(text, "%d.%m.%Y").date()
            users.setdefault(user_id, {})
            users[user_id]["birth_date"] = new_birth_date.isoformat()
            save_users(users)
            awaiting_birth_date_change.discard(user_id)

            years = users[user_id].get("life_expectancy", 80)
            img = generate_life_weeks_image(new_birth_date, date.today(), years)
            img.save("life.png")
            quote = random.choice(quotes)
            with open("life.png", "rb") as photo:
                bot.send_photo(message.chat.id, photo,
                               caption=f"{quote}\n\nВот твоя жизнь в неделях (до {years} лет) 🕰",
                               reply_markup=main_reply_keyboard())
        except ValueError:
            bot.reply_to(message, "⚠️ Введи дату в формате ДД.MM.ГГГГ")
        return

    # Обработка кнопок
    if text == "Изменить дату рождения":
        awaiting_birth_date_change.add(user_id)
        bot.send_message(message.chat.id, "Отправь новую дату рождения в формате: ДД.MM.ГГГГ")
    elif text == "Посмотреть жизнь по месяцам":
        info = users.get(user_id, {})
        if "birth_date" not in info:
            bot.send_message(message.chat.id, "Сначала установи дату рождения через 'Изменить дату рождения'.")
            return
        birth_date = datetime.fromisoformat(info["birth_date"]).date()
        years = info.get("life_expectancy", 80)
        img = generate_life_months_image(birth_date, date.today(), years)
        img.save("life_months.png")
        quote = random.choice(quotes)
        with open("life_months.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo,
                           caption=f"{quote}\n\nВот твоя жизнь по месяцам 📆")
    elif text == "Изменить продолжительность жизни":
        markup_inline = types.InlineKeyboardMarkup()
        for y in [70, 80, 90]:
            markup_inline.add(types.InlineKeyboardButton(f"{y} лет", callback_data=f"years_{y}"))
        bot.send_message(message.chat.id, "Выбери предполагаемую продолжительность жизни:", reply_markup=markup_inline)


# ---------- FLASK ----------
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "✅ Bot is running!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# ---------- ПЛАНИРОВЩИК ----------
scheduler = BackgroundScheduler(timezone=pytz.timezone(TIMEZONE))

def daily_update():
    today = date.today()
    for user_id, info in users.items():
        if "birth_date" not in info:
            continue
        birth_date = datetime.fromisoformat(info["birth_date"]).date()
        years = info.get("life_expectancy", 80)

        img = generate_life_weeks_image(birth_date, today, years)
        filename = f"life_{user_id}.png"
        img.save(filename)

        # ДР
        if birth_date.day == today.day and birth_date.month == today.month:
            message = random.choice(birthday_messages)
            with open(filename, "rb") as photo:
                bot.send_photo(user_id, photo, caption=message)

        # Новый год
        if today.month == 1 and today.day == 1:
            message = random.choice(new_year_messages)
            with open(filename, "rb") as photo:
                bot.send_photo(user_id, photo, caption=message)

scheduler.add_job(daily_update, 'cron', hour=9, minute=0)  # каждый день в 9:00
scheduler.start()

# ---------- ВЕБХУК НА RENDER ----------
bot.remove_webhook()
WEBHOOK_URL = "https://lifetimerbot.onrender.com/8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
bot.set_webhook(url=WEBHOOK_URL)


# ---------- ЗАПУСК FLASK ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
