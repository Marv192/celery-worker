FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /celery_worker

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app .

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]