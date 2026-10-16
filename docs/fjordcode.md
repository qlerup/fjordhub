# FjordHub Codex: isoleret VS Code-desktop

Integrationer → Codex / AI-kodeagent → Installér VS Code + Codex. Åbn derefter desktop under den eksisterende FjordHub-adresse på \`/fjordcode/desktop/\`.

## Architecture
- FjordHub's authenticated same-origin HTTP/WebSocket gateway proxies LinuxServer's **full Linux VS Code desktop**, rather than building another AI chat. Selkies runs at port 3000 **only on the isolated Docker network**, without publishing an external port. Browser access requires HTTPS for media streaming; the existing Cloudflare Tunnel to the FjordHub app port works with WebSockets enabled.
- Desktop install is opt-in through Docker SDK. Container image: \`lscr.io/linuxserver/vscode:latest\`. \`SUBFOLDER=/fjordcode/desktop/\` keeps browser asset and WebSocket URLs under FjordHub's current domain.
- Installation attempts \`code --install-extension OpenAI.chatgpt --force\` as the unprivileged \`abc\` account. If extension installation fails, the page reports that it must be installed from VS Code Extensions. Sign in to Codex in the **VS Code extension** (not the legacy Codex CLI chat).
- Persistent Docker named volume \`<compose-project>_fjordcode-vscode-config\` is mounted at \`/config\`. Existing Codex workspaces \`<project>_fjordcode-workspaces\` are mounted at \`/workspaces\`. Existing Codex CLI home \`<project>_fjordcode-home\` is mounted at \`/config/fjordcode-home\`, with \`CODEX_HOME=/config/fjordcode-home/.codex\`. This lets the editor reuse existing project files and skills.
- Clone projects from the VS Code terminal and import your personal skills to \`/config/fjordcode-home/.codex/skills\` (or clone skill repositories there). Nothing on your Windows PC is transferred automatically.
- Desktop container has **no Docker socket, no host filesystem bind mounts, and no published host ports**. UI is restricted to authenticated FjordHub administrators and an explicit same-origin check on WebSocket and mutating requests. Desktop has passwordless sudo **inside its own container**, so do not expose the upstream port directly.
- Proxmox LXC support and OpenAI extension login still require a **real smoke test on your installation**; failing WebSocket transport or Linux kernel sandbox restrictions must be diagnosed without disabling security protections.

The old Codex CLI worker remains installed if you already had it, and its data is not removed. The old FjordCode chat is no longer the primary UI. The Matrix/Element X bot and future domain management are out of scope.
