# VS Code + Codex integration

FjordHub > Integrationer > Codex / AI-kodeagent > Installér VS Code + Codex.

The installation creates a dedicated full VS Code Linux desktop from
[LinuxServer.io vscode](https://docs.linuxserver.io/images/docker-vscode/)
and retains the existing isolated Codex CLI worker. Both share project files
in the `<compose_project>_fjordcode-workspaces` Docker volume and Codex data
in `<compose_project>_fjordcode-home` (Codex skills under
`/home/codex/.codex/skills`). VS Code settings live separately in
`<compose_project>_fjordcode-vscode-config`.

The VS Code desktop is available only to signed-in FjordHub administrators,
using `/integrations/codex/desktop/` on the *existing* FjordHub origin
(including Cloudflare Tunnel). A backend HTTP/WebSocket gateway proxies to
the fixed Docker-internal address `fjordhub-vscode:3000`. No Docker host port
is published for the desktop; the VS Code container never mounts the Docker
socket, Proxmox API or other apps' directories.

Install or sign in to the official OpenAI Codex extension in the full editor.
The container image includes a best-effort extension installer, but if the
marketplace is not available on boot, use VS Code's Extensions tab.
Device login is offered in the integration page as a fallback.

### Limitations and follow-up

- Browser-streamed full VS Code is a desktop interface, not a mobile-native editor.
- The Selkies stream must be tested behind the user's actual Cloudflare Tunnel,
  especially HTTP upgrades and long-lived WebSockets.
- The first installation can take several minutes because the VS Code image is
  large. On a Proxmox LXC, ensure the Docker environment supports LinuxServer
  desktop processes without granting host/Proxmox privileges.
- SSH and private Git repositories can be configured in the isolated editor.
  Never place host or FjordHub credentials into the shared volume.
- Moving the desktop/worker to a dedicated LXC later requires migrating the
  named volumes but no public hostname change.
- Matrix/Element X bot control and independent domain management are future work.
