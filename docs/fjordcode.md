# Codex system integration (FjordHub)

Open **Integrationer → Codex / AI-kodeagent**, then **Installér Codex**, complete the official ChatGPT OAuth device-login, and choose **Åbn agentchat**.

Codex remains accessible at the current FjordHub origin on `/fjordcode` (for example, `https://fjordhub.gleruphub.dk/fjordcode`), without new domains or Cloudflare rules.

The install button starts an asynchronous Docker SDK installation; FjordHub builds an isolated worker image from the included source and creates `fjordhub-code`, with no Docker socket or host file mounts. Worker volumes are preserved between restarts. Legacy workers deployed via Compose are reused, if present.

Only FjordHub administrators can install, authenticate, and chat. All write endpoints use FjordHub CSRF checks. The worker is accessible only on the FjordHub-internal Codex Docker network and uses a shared private-volume token. Codex device credentials never go to GitHub or the browser.

The first release clones only public GitHub projects; it can modify and test them inside its isolated workspace, but **does not automatically push**. Element X bot integration, dedicated domains, private repository credentials, and a separate LXC are future work.

If the Codex worker is already running from an older Compose deployment, the installation page detects it without deleting workspaces. New installations are opt-in; the Codex service is in Compose profile `codex` so ordinary FjordHub updates do not auto-install it.

Device authorization must be enabled in the ChatGPT account's security settings. The installation requires outbound connectivity to GitHub, the Docker registry, and OpenAI. Confirm at runtime that Codex workspace-write sandboxing works in the selected LXC; do not grant privileged mode or disable sandbox checks to work around host restrictions.
