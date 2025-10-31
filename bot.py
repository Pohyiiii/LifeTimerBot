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

# ---------- СПИСОК ЦИТАТ ----------
quotes = [
    # --- О жизни и времени ---
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

    # --- Тёплые и мягкие ---
    "Сегодня — неплохой день, чтобы просто быть.",
    "Не всё нужно понимать, чтобы чувствовать.",
    "Некоторые дни просто хотят, чтобы ты отдохнул.",
    "Жизнь — не гонка, а прогулка с непредсказуемым маршрутом.",
    "Иногда счастье приходит в виде тишины и чашки чая.",
    "Будь там, где тебе спокойно.",
    "Иногда лучшее, что можно сделать — просто дышать.",
    "Мир становится тише, когда начинаешь слушать.",
    "Никто не знает, как правильно жить — и в этом есть свобода.",
    "Даже обычный день может стать важным, если его заметить.",

    # --- Ностальгия и воспоминания ---
    "Иногда целая жизнь умещается в одно лето.",
    "Детство не уходит — оно просто становится воспоминанием.",
    "Некоторые моменты не повторятся, и в этом их красота.",
    "Мы взрослеем в тот момент, когда начинаем скучать по себе прошлому.",
    "Прошлое живёт в запахах и песнях.",
    "Иногда хочется вернуться не во время, а в состояние.",
    "Память — это способ сердца сказать: «я всё ещё чувствую».",
    "Годы проходят, а ощущение юности всё равно где-то рядом.",
    "Иногда хочется просто побыть тем, кем был раньше.",
    "Некоторые места навсегда остаются внутри нас.",

    # --- Спокойная философия ---
    "Не бойся идти медленно, бойся стоять.",
    "Настоящее — это мгновение между уже и ещё.",
    "Мы не теряем годы — они просто становятся частью нас.",
    "Пока мы считаем недели, жизнь считает воспоминания.",
    "Время — лучший рассказчик, но ужасный собеседник.",
    "Не все пути должны куда-то вести.",
    "Иногда достаточно просто быть — и этого уже много.",
    "Тот, кто умеет ждать, живёт в ритме времени.",
    "Смысл часто приходит позже — когда уже не ищешь.",
    "Прожить день — уже искусство.",

    # --- О быстротечности ---
    "Никто не знает, сколько осталось, и в этом вся магия.",
    "Пока мы строим планы, время улыбается и идёт дальше.",
    "Каждый день становится вчера быстрее, чем кажется.",
    "Годы не проходят — они просто меняют нас.",
    "Некоторые мгновения длятся дольше, чем целый год.",
    "Чем дольше живёшь, тем короче становятся годы.",
    "Секунды незаметны, пока не становятся последними.",
    "Мы не замечаем, как проживаем мечты.",
    "Иногда жизнь проходит незаметно — просто между встречами и снами.",
    "Жизнь течёт тихо, если не спешить.",

    # --- Немного мотивации ---
    "Каждый день — шанс сделать хоть что-то по-другому.",
    "Сегодня можно начать с нуля, без объяснений.",
    "Если хочешь — успеешь. Просто начни.",
    "Не обязательно успевать всё. Главное — успеть пожить.",
    "Пусть твой день будет добрым, даже если никто не заметит.",
    "Счастье не громкое. Оно просто есть.",
    "Живи не спеша, но не стой на месте.",
    "Иногда достаточно просто не сдаваться сегодня.",
    "Не всё потеряно, пока ты всё ещё хочешь попробовать.",
    "Не обязательно знать путь, чтобы по нему идти.",

    # --- Про настоящее ---
    "Сегодня — то завтра, о котором ты думал вчера.",
    "Настоящее всегда происходит незаметно.",
    "Иногда просто посмотри в окно и вспомни, что всё ещё здесь.",
    "Мы так много думаем о будущем, что забываем дышать в настоящем.",
    "Иногда день кажется обычным, пока не станет воспоминанием.",
    "Сейчас — единственное, что по-настоящему твоё.",
    "Почувствуй, как живёт момент.",
    "Всё, что у нас есть — это сегодня.",
    "Не ищи особенных дней — сделай этот особенным.",
    "Иногда момент стоит больше, чем год ожидания.",

    # --- Лёгкая грусть и принятие ---
    "Всё проходит, но не всё забывается.",
    "Иногда нужно потеряться, чтобы снова найти себя.",
    "Боль тоже часть пути.",
    "Мы не можем вернуть время, но можем вернуть внимание.",
    "Некоторые вещи становятся понятны только с расстояния лет.",
    "Иногда молчание говорит больше слов.",
    "С каждым годом легче прощать, но труднее забывать.",
    "Жизнь не обязана быть лёгкой, чтобы быть красивой.",
    "Даже когда грустно — это тоже жизнь.",
    "Время не лечит, но делает боль мягче.",

    # --- О благодарности и тепле ---
    "Благодари за то, что было, даже если было сложно.",
    "Иногда счастье — это просто осознать, что всё ещё есть силы.",
    "Каждый прожитый день — уже подарок.",
    "Заметь хорошее, пока оно рядом.",
    "Даже если день был тяжёлым — он был твоим.",
    "Иногда просто поблагодари время за то, что оно идёт.",
    "Благодарность делает минуты дольше.",
    "Всё ценное обычно тихое.",
    "Не спеши. Хорошее всё равно приходит.",
    "Мир становится теплее, когда ты его замечаешь.",

    # --- О смысле и простоте ---
    "Смысл не ищут — его чувствуют.",
    "Иногда ответы приходят тогда, когда перестаёшь спрашивать.",
    "Простые вещи спасают чаще, чем великие.",
    "Иногда всё самое важное — уже рядом.",
    "Сложное становится простым, когда перестаёшь бояться.",
    "Не всё нужно понимать, чтобы ценить.",
    "Иногда тишина — самый честный ответ.",
    "Покой не приходит извне — он растёт внутри.",
    "Ничего страшного, если не знаешь, зачем — главное, что живёшь.",
    "Жизнь не загадка, а процесс.",

    # --- Короткие, как дыхание ---
    "Всё будет. Но не всё сразу.",
    "Просто живи.",
    "Тише — это тоже ответ.",
    "Главное — быть.",
    "Не спеши. Успеешь.",
    "Вдох. Выдох. День продолжается.",
    "Пусть будет как будет.",
    "Живи мягко.",
    "Каждое «сегодня» когда-то станет «вчера».",
    "Иди. Просто иди.",
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

# ---------- СОЗДАНИЕ КАРТИНКИ ----------
def generate_life_weeks_image(birth_date, current_date, life_expectancy_years=80):
    end_of_life = birth_date + relativedelta(years=life_expectancy_years)
    delta = relativedelta(end_of_life, current_date)
    remaining_days_total = (end_of_life - current_date).days
    lived_weeks = (current_date - birth_date).days // 7
    total_weeks = life_expectancy_years * 52

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

    draw.text((10, 10), f"Прожито: {lived_weeks} недель", fill="black", font=title_font)
    draw.text((10, 40), f"Осталось: {total_weeks - lived_weeks} недель ({remaining_days_total} дней)", fill="gray", font=font)

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

# ---------- МЕНЮ И СТАРТ ----------
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

# ---------- ИЗМЕНЕНИЕ ДАТЫ ----------
@bot.message_handler(commands=['change_date'])
def change_birth_date_command(message):
    user_id = str(message.from_user.id)
    awaiting_birth_date_change.add(user_id)
    bot.send_message(message.chat.id, "Отправь новую дату рождения в формате: ДД.MM.ГГГГ")

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
                bot.send_photo(message.chat.id, photo, caption=f"Вот твоя жизнь в неделях (расчёт до {years} лет) 🕰")
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
                    caption=f"{quote}\n\nВот твоя жизнь в неделях (расчёт до {years} лет) 🕰"
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
                        bot.send_photo(
                            user_id,
                            photo,
                            caption=f"{quote}\n\nОбновлённая таблица на {today.strftime('%d.%m.%Y')} ✨"
                        )
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
