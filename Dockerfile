FROM python:3.11-slim

# Set working directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Salin seluruh isi project ke dalam container
COPY . .

# Install dependencies Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Jalankan collectstatic (jika pakai staticfiles)
RUN python manage.py collectstatic --noinput

# Jalankan Daphne (ASGI server untuk WebSocket + HTTP)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "core.asgi:application"]
