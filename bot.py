import telebot
from datetime import date
from PIL import Image, ImageDraw, ImageFont
import os
from flask import Flask, request
from telebot import types

BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Хранение данных пользователей
user_life_expectancy = {}
user_state = {}  # состояние диалога

# ---------- ФУНКЦИЯ СОЗДАНИЯ ИЗОБРАЖЕНИЯ ----------
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
    top_space = 80
    left_space = 50

    img_width = cols * (size + margin) + margin + left_space + 10
    img_height = rows * (size + margin) + margin + top_space + 10
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Подключаем шрифт Noto Sans
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 13)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", 18)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # Текст сверху
    text1 = f"Прожито: {lived_weeks} недель ({lived_days} дней)"
    text2 = f"Осталось примерно: {remaining_weeks} недель ({remaining_days} дней)"
    draw.text((10, 10), text1, fill="black", font=title_font)
    draw.text((10, 40), text2, fill="gray", font=font)

    # Подписи месяцев сверху: 4,8,12,...,52 (ставим метки именно на 4-ю, 8-ю и т.д. клетки)
    for month_index in range(1, cols // 4 + 1):  # 1..13
        week_index = month_index * 4  # 4,8,...
        # вычисляем позицию центра соответствующей клетки (week_index - 1) — 0-based
        cell_x = left_space + (week_index - 1) * (size + margin)
        label = str(week_index)
        tw, th = font.getsize(label)
        x_text = cell_x + (size - tw) / 2
        y_text = top_space - 24  # чуть выше клетки
        draw.text((x_text, y_text), label, fill="gray", font=font)

    # Подписи лет слева (выровнены по центру квадрата и ближе к сетке)
    # выровняем вертикально по центру клетки и подвинем горизонтально ближе к клеткам
    sample_text = "0"
    try:
        _, sample_h = font.getsize(sample_text)
    except:
        sample_h = 12
    for y in range(rows):
        cell_y = top_space + y * (size + margin)
        y_pos = cell_y + (size - sample_h) / 2
        x_pos = left_space - 14
        draw.text((x_pos, y_pos), str(y + 1), fill="gray", font=font)

    # Сетка
    for i in range(total_weeks):
        x = left_space + (i % cols) * (size + margin)
        y = top_space + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_weeks else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    return img


# ---------- TELEGRAM ----------
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
    user_state[message.from_user.id] = "choosing_years"


@bot.callback_query_handler(func=lambda call: call.data.startswith("years_"))
def set_life_expectancy(call):
    years = int(call.data.split("_")[1])
    user_life_expectancy[call.from_user.id] = years
    user_state[call.from_user.id] = "waiting_for_date"

    bot.answer_callback_query(call.id, f"Выбрано: {years} лет")
    bot.send_message(
        call.message.chat.id,
        f"Отлично! Будем считать {years} лет.\nТеперь отправь дату рождения в формате: ДД.ММ.ГГГГ"
    )


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id

    if user_state.get(user_id) == "waiting_for_date":
        try:
            birth_date = date.fromisoformat("-".join(reversed(message.text.split('.'))))
            current_date = date.today()
            years = user_life_expectancy.get(user_id, 80)

            img = generate_life_weeks_image(birth_date, current_date, years)
            img.save("life.png")

            with open("life.png", "rb") as photo:
                bot.send_photo(
                    message.chat.id,
                    photo,
                    caption=f"Вот твоя жизнь в неделях (расчёт до {years} лет) 🕰"
                )

            user_state[user_id] = "ready"

        except Exception as e:
            print("Ошибка:", e)
            bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.ММ.ГГГГ")

    else:
        bot.send_message(
            message.chat.id,
            "Напиши /start, чтобы начать заново 👋"
        )


# ---------- FLASK / WEBHOOK ----------
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "✅ Bot is running and Flask server is alive!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200


if __name__ == "__main__":
    WEBHOOK_URL = f"https://lifetimerbot.onrender.com/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
