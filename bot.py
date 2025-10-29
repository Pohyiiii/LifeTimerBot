import telebot
from datetime import date
from PIL import Image, ImageDraw

BOT_TOKEN = "8312401636:AAGfQXDN5v5in2d4jUHMZZdTJYt29TfF3I8"
bot = telebot.TeleBot(BOT_TOKEN)

# Функция для генерации изображения с неделями
def generate_life_weeks_image(birth_date, current_date):
    life_expectancy_years = 90
    total_weeks = life_expectancy_years * 52
    lived_weeks = (current_date - birth_date).days // 7

    cols = 52
    rows = life_expectancy_years
    size = 10
    margin = 2

    img_width = cols * (size + margin) + margin
    img_height = rows * (size + margin) + margin
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    for i in range(total_weeks):
        x = margin + (i % cols) * (size + margin)
        y = margin + (i // cols) * (size + margin)
        color = (220, 20, 60) if i < lived_weeks else (230, 230, 230)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    return img

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Привет! Я помогу тебе увидеть, как проходит твоя жизнь по неделям.\n"
        "Отправь мне дату своего рождения в формате: ДД.ММ.ГГГГ"
    )

@bot.message_handler(func=lambda message: True)
def send_life_image(message):
    try:
        birth_date = date.fromisoformat(
            "-".join(reversed(message.text.split('.')))
        )
        current_date = date.today()
        img = generate_life_weeks_image(birth_date, current_date)
        img.save("life.png")
        with open("life.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption="Вот твоя жизнь в неделях 🕰")
    except Exception:
        bot.reply_to(message, "⚠️ Пожалуйста, введи дату в формате ДД.ММ.ГГГГ")

bot.polling()
