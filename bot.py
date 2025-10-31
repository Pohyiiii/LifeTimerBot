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
import time

# ---------- НАСТРОЙКИ ----------
BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"  # <-- твой токен
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
awaiting_birth_date_change = set()  # user_id (str) — ждём новую дату

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
    "Прошла неделя — и это уже что-то.",
    "Небольшой отчёт: прошла ещё одна неделя твоей жизни.",
    "Надёжный чек: неделя прошла — время идёт.",
]

# ---------- ФУНКЦИИ ДЛЯ КАРТИНОК ----------
def _load_font(size):
    # пробуем NotoSans, иначе дефолт
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", size)
    except:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except:
            return ImageFont.load_default()

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

    font = _load_font(14)
    title_font = _load_font(18)

    # текст — поднят, чтобы не заходил на таблицу
    draw.text((10, 10), f"Прожито: {lived_weeks} недель ({lived_days} дней)", fill="black", font=title_font)
    remaining_weeks = max(total_weeks - lived_weeks, 0)
    remaining_days = (birth_date + relativedelta(weeks=total_weeks) - current_date).days
    draw.text((10, 36), f"Осталось: {remaining_weeks} недель ({remaining_days} дней)", fill="gray", font=font)

    # подписи сверху — по 4 недели: 4,8,12...
    for w in range(4, cols + 1, 4):
        x_pos = left_space + (w - 1) * (size + margin)
        draw.text((x_pos, top_space - 18), str(w), fill="gray", font=font)

    # подписи лет слева (выравнивание по вертикали аккуратно)
    for y in range(rows):
        y_pos = top_space + y * (size + margin) + (size//2 - 6)  # небольшая коррекция по вертикали
        draw.text((10, y_pos), str(y + 1), fill="gray", font=font)

    # сетка
    for i in range(total_weeks):
        x = left_space + (i % cols) * (size + margin)
        y = top_space + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_weeks else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    return img

def generate_life_months_image(birth_date, current_date, life_expectancy_years=80):
    total_months = life_expectancy_years * 12
    lived_months = (current_date.year - birth_date.year) * 12 + (current_date.month - birth_date.month)
    lived_months = max(lived_months, 0)

    cols = 12
    rows = life_expectancy_years
    size = 20
    margin = 2
    left_space = 35
    top_space = 70  # поднято для надписей

    img_width = cols * (size + margin) + margin + left_space + 20
    img_height = rows * (size + margin) + margin + top_space + 20
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    font = _load_font(12)
    title_font = _load_font(16)

    # текст
    draw.text((10, 10), f"Прожито: {lived_months} месяцев", fill="black", font=title_font)
    remaining_months = max(total_months - lived_months, 0)
    draw.text((10, 32), f"Осталось: {remaining_months} месяцев", fill="gray", font=font)

    # цифры месяцев сверху 1..12
    for m in range(1, 13):
        x_pos = left_space + (m - 1) * (size + margin)
        draw.text((x_pos + 5, top_space - 18), str(m), fill="gray", font=font)

    # цифры лет слева
    for y in range(rows):
        y_pos = top_space + y * (size + margin) + (size//2 - 6)
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
    markup.add("Изменить дату рождения", "Жизнь в месяцах", "Изменить продолжительность жизни")
    return markup

# ---------- START ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # inline выбор 70/80/90
    markup_inline = types.InlineKeyboardMarkup()
    for y in [70, 80, 90]:
        markup_inline.add(types.InlineKeyboardButton(f"{y} лет", callback_data=f"years_{y}"))
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я помогу тебе увидеть, как проходит твоя жизнь по неделям.\n\n"
        "Выбери предполагаемую продолжительность жизни:",
        reply_markup=markup_inline
    )

# ---------- CALLBACK ДЛЯ INLINE-КНОПОК ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("years_"))
def set_life_expectancy(call):
    years = int(call.data.split("_")[1])
    user_id = str(call.from_user.id)
    users.setdefault(user_id, {})
    users[user_id]["life_expectancy"] = years
    save_users(users)
    bot.answer_callback_query(call.id, f"Выбрано: {years} лет")

    # если дата есть — просто обновляем таблицу и не просим дату снова
    if "birth_date" in users[user_id]:
        try:
            birth_date = datetime.fromisoformat(users[user_id]["birth_date"]).date()
            img = generate_life_weeks_image(birth_date, date.today(), years)
            img.save("life.png")
            quote = random.choice(quotes)
            with open("life.png", "rb") as photo:
                bot.send_photo(call.message.chat.id, photo,
                               caption=f"{quote}\n\nВот твоя жизнь в неделях (до {years} лет) 🕰",
                               reply_markup=main_reply_keyboard())
        except Exception as e:
            bot.send_message(call.message.chat.id, "Произошла ошибка при обновлении таблицы.")
            print("Ошибка при обновлении после выбора лет:", e)
    else:
        bot.send_message(call.message.chat.id, "Отлично! Теперь отправь дату рождения в формате: ДД.MM.ГГГГ")

# ---------- ОБРАБОТКА СООБЩЕНИЙ ----------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    text = (message.text or "").strip()

    # пользователей в ожидании смены даты (меню -> Изменить дату)
    if user_id in awaiting_birth_date_change:
        try:
            new_birth_date = datetime.strptime(text, "%d.%m.%Y").date()
            users.setdefault(user_id, {})
            users[user_id]["birth_date"] = new_birth_date.isoformat()
            # если не было last_sent_week — установим текущую, чтобы не слать старые недели
            lived_weeks = (date.today() - new_birth_date).days // 7
            users[user_id].setdefault("last_sent_week", lived_weeks)
            save_users(users)
            awaiting_birth_date_change.remove(user_id)

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

    # Кнопки в ReplyKeyboard:
    if text == "Изменить дату рождения" or text == "Изменить дату":
        awaiting_birth_date_change.add(user_id)
        bot.send_message(message.chat.id, "Отправь новую дату рождения в формате: ДД.MM.ГГГГ")
        return

    if text == "Жизнь в месяцах" or text == "Жизнь по месяцам":
        info = users.get(user_id, {})
        if "birth_date" not in info:
            bot.send_message(message.chat.id, "Сначала установи дату рождения через кнопку 'Изменить дату рождения'.")
            return
        birth_date = datetime.fromisoformat(info["birth_date"]).date()
        years = info.get("life_expectancy", 80)
        img = generate_life_months_image(birth_date, date.today(), years)
        img.save("life_months.png")
        quote = random.choice(quotes)
        with open("life_months.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f"{quote}\n\nВот твоя жизнь в месяцах 📆")
        return

    if text == "Изменить продолжительность жизни" or text == "Выбрать продолжительность жизни":
        markup_inline = types.InlineKeyboardMarkup()
        for y in [70, 80, 90]:
            markup_inline.add(types.InlineKeyboardButton(f"{y} лет", callback_data=f"years_{y}"))
        bot.send_message(message.chat.id, "Выбери предполагаемую продолжительность жизни:", reply_markup=markup_inline)
        return

    # Если пользователь просто прислал дату впервые
    try:
        birth_date = datetime.strptime(text, "%d.%m.%Y").date()
        users.setdefault(user_id, {})
        users[user_id]["birth_date"] = birth_date.isoformat()
        # при первоначальном вводе — устанавливаем last_sent_week = текущий lived_weeks,
        # чтобы бот не считал предыдущие недели как "пропущенные" и не шлёт сразу еженедельную рассылку.
        lived_weeks = (date.today() - birth_date).days // 7
        users[user_id]["last_sent_week"] = lived_weeks
        years = users[user_id].get("life_expectancy", 80)
        save_users(users)

        img = generate_life_weeks_image(birth_date, date.today(), years)
        img.save("life.png")
        quote = random.choice(quotes)
        with open("life.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo,
                           caption=f"{quote}\n\nВот твоя жизнь в неделях (до {years} лет) 🕰",
                           reply_markup=main_reply_keyboard())
    except ValueError:
        # не дата — игнорируем / можно добавить реакцию
        bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.MM.ГГГГ или используй кнопки меню.")

# ---------- ПЛАНИРОВЩИК (ежедневная проверка) ----------
def check_and_send_updates():
    today = date.today()
    print(f"Планировщик: проверка {today} — {datetime.now().isoformat()}")
    for user_id, info in list(users.items()):
        try:
            if "birth_date" not in info:
                continue
            birth_date = datetime.fromisoformat(info["birth_date"]).date()
            years = info.get("life_expectancy", 80)

            # --- День рождения ---
            if birth_date.month == today.month and birth_date.day == today.day:
                # отправляем только поздравление (без цитаты)
                msg = random.choice(birthday_messages)
                try:
                    bot.send_message(int(user_id), msg)
                except Exception as e:
                    print(f"Не удалось отправить ДР {user_id}: {e}")
                # не идём дальше для этого пользователя (чтобы не дублировать с еженедельными)
                # *если нужно отправлять ещё и таблицу — можно включить*
                # Обновлять last_sent_week не требуется
                continue

            # --- Новый год (1 января) ---
            if today.month == 1 and today.day == 1:
                msg = random.choice(newyear_messages)
                try:
                    bot.send_message(int(user_id), msg)
                except Exception as e:
                    print(f"Не удалось отправить НГ {user_id}: {e}")
                # отправляем поздравление всем и пропускаем остальные проверки
                continue

            # --- Еженедельные обновления (когда вырос lived_weeks больше чем last_sent_week) ---
            lived_weeks = (today - birth_date).days // 7
            last_week = info.get("last_sent_week", None)
            if last_week is None:
                # если нет — инициализируем, чтобы не отправлять старые недели
                users[user_id]["last_sent_week"] = lived_weeks
                save_users(users)
                continue

            if lived_weeks > last_week:
                # отправить обновлённую таблицу + фразу + цитата
                img = generate_life_weeks_image(birth_date, today, years)
                img.save("life.png")
                phrase = random.choice(weekly_phrases)
                quote = random.choice(quotes)
                caption = f"{phrase}\n\n{quote}\n\nОбновлённая таблица на {today.strftime('%d.%m.%Y')}"
                try:
                    with open("life.png", "rb") as photo:
                        bot.send_photo(int(user_id), photo, caption=caption)
                except Exception as e:
                    print(f"Не удалось отправить еженедельную таблицу {user_id}: {e}")
                # обновляем маркер
                users[user_id]["last_sent_week"] = lived_weeks
                save_users(users)

        except Exception as e:
            print(f"Ошибка при планировщике для {user_id}: {e}")

# создаём и запускаем планировщик
scheduler = BackgroundScheduler()
# запускаем проверку каждый день в 00:00 сервера
scheduler.add_job(check_and_send_updates, 'cron', hour=0, minute=0)
scheduler.start()

# ---------- FLASK / WEBHOOK или POLLING ----------
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "✅ Bot is running!"

# webhook receiver (если используешь webhook)
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

if __name__ == "__main__":
    # Если у тебя есть публичный URL (Render / Heroku) — задай его в окружении как WEBHOOK_URL
    # пример: export WEBHOOK_URL="https://your-app.onrender.com"
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    if WEBHOOK_URL:
        full_url = f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}"
        try:
            bot.remove_webhook()
            bot.set_webhook(url=full_url)
            print("Webhook установлен:", full_url)
            # Запускаем Flask (webhook mode)
            port = int(os.environ.get("PORT", 8080))
            app.run(host="0.0.0.0", port=port)
        except Exception as e:
            print("Не удалось установить webhook, падаем в polling:", e)
            bot.remove_webhook()
            print("Запускаю polling...")
            bot.polling(none_stop=True, interval=1)
    else:
        # fallback: polling (локально удобно)
        print("WEBHOOK_URL не задан — запускаю polling (удобно для локального запуска).")
        bot.polling(none_stop=True, interval=1)
