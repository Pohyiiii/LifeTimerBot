# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости + шрифт Noto Sans
RUN apt-get update && apt-get install -y \
    libjpeg-dev zlib1g-dev fonts-noto-core && \
    rm -rf /var/lib/apt/lists/*


# Создаём рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Устанавливаем переменную окружения, чтобы Flask слушал нужный порт
ENV PORT=8080

# Запускаем Flask и Telegram-бота
CMD ["python", "bot.py"]
