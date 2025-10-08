FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# copy and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

# Use Gunicorn with a threaded worker to handle moderate concurrency.
# We'll use the app factory `vms:create_app()`
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "4", "--timeout", "120", "--log-level", "info", "vms:create_app()"]
