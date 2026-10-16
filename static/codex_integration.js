(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
  let refreshing = false;
  const feedback = error => { $("codex-feedback").textContent = error?.message || String(error || ""); };
  async function api(action, post = false) {
    const response = await fetch("/api/fjordcode/desktop/" + action, {
      method: post ? "POST" : "GET",
      credentials:"same-origin", cache:"no-store",
      headers:post ? {"Content-Type":"application/json","X-CSRF-Token":csrf} : {},
      body: post ? "{}" : undefined,
    });
    const json = await response.json();
    if (!response.ok || !json.ok) throw new Error(json.error || "Forbindelsen fejlede.");
    return json;
  }
  async function refresh() {
    if (refreshing) return;
    refreshing = true;
    try {
      const data = await api("status");
      const phase = data.phase || "not_installed";
      const names = {ready:"Installeret",installing:"Installerer...",not_installed:"Ikke installeret",stopped:"Stoppet",error:"Fejl"};
      $("codex-phase").textContent = names[phase] || phase;
      $("codex-install-message").textContent = data.message || "";
      $("codex-install").disabled = phase === "ready" || phase === "installing";
      $("codex-install").textContent = phase === "ready" ? "Installeret" :
        phase === "installing" ? "Installerer..." :
        phase === "stopped" ? "Start VS Code" : "Installér VS Code + Codex";
      $("codex-chat-card").hidden = phase !== "ready";
      $("codex-extension-note").textContent = data.extension === "manual" ?
        "Codex-udvidelsen blev ikke installeret automatisk. I VS Code: Extensions → søg OpenAI Codex → Install." :
        data.extension === "installed" ? "OpenAI Codex-udvidelsen er installeret. Log ind i Codex-panelet." : "";
      feedback("");
    } catch (e) { feedback(e); }
    finally { refreshing = false; }
  }
  $("codex-install").addEventListener("click", async () => {
    $("codex-install").disabled = true;
    try { feedback(""); await api("install",true); await refresh(); }
    catch (e) { feedback(e); $("codex-install").disabled = false; }
  });
  refresh();
  setInterval(refresh, 4000);
})();
