(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
  let refreshing = false;
  async function api(action, post = false) {
    const result = await fetch("/api/fjordcode/" + action, {
      method: post ? "POST" : "GET",
      headers: post ? {"Content-Type":"application/json","X-CSRF-Token":csrf} : {},
      body: post ? "{}" : undefined,
      credentials:"same-origin", cache:"no-store"
    });
    const body = await result.json();
    if (!result.ok || !body.ok) throw new Error(body.error || "Forbindelsen fejlede");
    return body;
  }
  function feedback(error) { $("codex-feedback").textContent = error?.message || String(error); }
  function deviceLink(output) {
    const matches = output.match(/https:\/\/[^\s<>"']+/g) || [];
    for (const raw of matches) {
      try {
        const parsed = new URL(raw.replace(/[).,]+$/, ""));
        if (["auth.openai.com","chatgpt.com"].includes(parsed.hostname)) return parsed.href;
      } catch (_) {}
    }
    return "";
  }
  async function refresh() {
    if (refreshing) return;
    refreshing = true;
    try {
      const install = await api("install-status");
      const phase = install.phase || "not_installed";
      $("codex-phase").textContent = {
        ready:"Installeret", installing:"Installerer...", not_installed:"Ikke installeret", error:"Fejl"
      }[phase] || phase;
      $("codex-install-message").textContent = install.message || "";
      $("codex-install").disabled = phase === "installing" || phase === "ready";
      $("codex-install").textContent = phase === "installing" ? "Installerer..." :
        phase === "ready" ? "Installeret" : "Installér Codex";
      $("codex-auth-card").hidden = phase !== "ready";
      $("codex-chat-card").hidden = true;
      if (phase !== "ready") return;
      const auth = await api("status");
      $("codex-auth-state").textContent = auth.logged_in ? "Forbundet" :
        auth.auth_status === "running" ? "Afventer godkendelse..." : "Ikke forbundet";
      $("codex-auth-start").disabled = auth.logged_in || auth.auth_status === "running";
      $("codex-auth-start").hidden = !!auth.logged_in;
      $("codex-auth-output").textContent = auth.logged_in ? "" : (auth.auth_output || "");
      const link = auth.logged_in ? "" : deviceLink(auth.auth_output || "");
      $("codex-auth-link").hidden = !link;
      if (link) $("codex-auth-link").href = link;
      $("codex-chat-card").hidden = !auth.logged_in;
    } catch (error) { feedback(error); }
    finally { refreshing = false; }
  }
  $("codex-install").addEventListener("click", async () => {
    $("codex-install").disabled = true;
    try { feedback(""); await api("install",true); await refresh(); }
    catch(error) { feedback(error); $("codex-install").disabled = false; }
  });
  $("codex-auth-start").addEventListener("click", async () => {
    $("codex-auth-start").disabled = true;
    try { feedback(""); await api("auth/start",true); await refresh(); }
    catch(error) { feedback(error); $("codex-auth-start").disabled = false; }
  });
  refresh();
  setInterval(refresh, 4000);
})();
