FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache \
    docker-cli \
    docker-cli-compose \
    curl

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "wsgi:application", \
     "--worker-class", "gthread", \
     "--workers", "1", \
     "--threads", "4", \
     "--bind", "0.0.0.0:8080", \
     "--timeout", "60", \
     "--access-logfile", "-"]
