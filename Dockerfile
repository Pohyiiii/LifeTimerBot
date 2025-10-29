# Берём официальный образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости для Pillow
RUN apt-get update && apt-get install -y \
    libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Создаём рабочую папку
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Команда запуска бота
CMD ["python", "bot.py"]
