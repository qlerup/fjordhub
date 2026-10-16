# FjordCode (mobile Codex MVP)

This is an **admin-only FjordHub page** backed by a separate, low-privilege Docker service. It is **not** VS Code running inside FjordHub. The execution service can later be relocated to its own LXC while retaining the browser UI.

## Usage

1. Rebuild/restart the full Compose project once to provision the new worker:
   \`docker compose up -d --build\`
2. Sign in to FjordHub as an administrator, choose **FjordCode** in the sidebar.
3. Choose **Start ChatGPT-login**, open the device-login URL shown, and enter the one-time code on your phone.
4. Clone a **public** GitHub project by entering \`qlerup/fjordflix\` (or another \`owner/repository\`).
5. Select the project and send prompts. History is persisted in a named Docker volume. A running turn can be stopped and prior sessions resumed after the turn completes.

### Security and limitations

- Codex runs in the \`fjordcode\` service, not in the privileged FjordHub app. No Docker socket, Proxmox API or other installed apps are mounted in the worker.
- Workspaces and Codex credentials live in separate named volumes. Never mount server secrets or other apps' private directories into the worker.
- Only authenticated hub administrators can reach the proxy. All mutations use the existing CSRF protection. The worker has no published host port and authenticates requests from the hub using a private-volume token.
- **Codex CLI's workspace-write sandbox must function correctly** on the Docker/LXC host. Inspect errors before granting additional Docker privileges; do not switch to \`danger-full-access\`.
- First release: public repository clone, prompt/continue, agent activity, changed-file status, stop. It does **not** automatically push to GitHub or handle private repos, editable model presets, multiple simultaneous Codex turns or approval prompts.
- The worker needs outbound HTTPS to GitHub and OpenAI. The isolated bridge should be additionally restricted by host firewall rules where possible.
- Device auth may need enabling in your ChatGPT account's security settings; no tokens or pairing codes belong in a GitHub commit.
- This implementation has not been live-tested against your Proxmox host or ChatGPT session. If the worker cannot initialize in your LXC, review Docker security policies and logs without weakening isolation.
