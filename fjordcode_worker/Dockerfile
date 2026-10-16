FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @openai/codex \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin codex \
    && mkdir -p /workspaces /home/codex/.codex \
    && printf '[permissions.filesystem]\ndeny_read = ["/home/codex/.codex/auth.json", "/run/fjordcode-token"]\n' > /home/codex/.codex/config.toml \
    && chown -R 10001:10001 /workspaces /home/codex
WORKDIR /app
COPY fjordcode_worker/worker.py /app/worker.py
USER 10001:10001
ENV HOME=/home/codex CODEX_HOME=/home/codex/.codex PYTHONDONTWRITEBYTECODE=1
EXPOSE 8811
CMD ["python3", "/app/worker.py"]
