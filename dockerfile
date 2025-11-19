FROM python:3.9-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка Python пакетов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование ВСЕХ Python файлов
COPY *.py ./

# Создание директорий
RUN mkdir -p input output uploads processed

# Команда по умолчанию
CMD ["python", "web_app.py"]