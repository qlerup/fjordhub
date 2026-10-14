/* Check again when an existing Hub tab or homescreen app comes to the front. */
(() => {
  if (window.location.pathname === '/profile') return;
  let pending = false;
  async function check() {
    if (pending || document.hidden) return;
    pending = true;
    try {
      const response = await fetch('/api/auth/access', {cache:'no-store', credentials:'same-origin', signal:AbortSignal.timeout(8000)});
      if (response.status === 403 && (await response.json()).email_required === true)
        window.location.replace('/profile');
    } catch { /* An outage is retried without changing the user's session. */ }
    finally { pending = false; }
  }
  check();
  window.setInterval(check, 5000);
  window.addEventListener('focus', check);
  window.addEventListener('pageshow', check);
  document.addEventListener('visibilitychange', check);
})();
