#!/bin/bash
# LinuxServer custom init hook: best-effort install the official Codex extension.
# Runs locally as abc, persists in /config. Never fail VS Code startup if the
# Marketplace is temporarily unavailable.
set +e
if command -v code >/dev/null 2>&1; then
  timeout 120s s6-setuidgid abc code --no-sandbox --install-extension OpenAI.chatgpt --force
  if [ $? -ne 0 ]; then
    echo "[FjordCode] Codex extension auto-install failed; install OpenAI.chatgpt from VS Code Extensions."
  fi
else
  echo "[FjordCode] VS Code CLI not found at startup; install OpenAI.chatgpt from Extensions."
fi
exit 0
