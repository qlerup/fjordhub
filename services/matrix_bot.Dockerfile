FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libolm-dev libffi-dev libssl-dev pkg-config \
    && pip install --no-cache-dir 'matrix-nio[e2e]>=0.25,<0.27' 'requests>=2.31,<3' \
    && apt-get purge -y --auto-remove gcc pkg-config \
    && rm -rf /var/lib/apt/lists/*
COPY matrix_bot.py bot_queries.py /app/
WORKDIR /app
CMD ["python", "matrix_bot.py"]
