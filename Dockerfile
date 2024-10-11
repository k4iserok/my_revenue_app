# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir flask pandas matplotlib openpyxl seaborn

# Создаем папку для загрузки файлов
RUN mkdir -p /app/uploads

# Запускаем скрипт для генерации миниатюр графиков
RUN python generate_thumbnails.py

# Задаем переменные окружения для Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Запускаем Flask-приложение
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
