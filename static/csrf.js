// Supply the session token only to same-origin state-changing requests.
(() => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  if (!token) return;
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    const request = input instanceof Request ? input : null;
    const url = new URL(request ? request.url : input, window.location.href);
    const method = String(init.method || request?.method || 'GET').toUpperCase();
    if (url.origin === window.location.origin && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
      const headers = new Headers(init.headers || request?.headers);
      if (!headers.has('X-CSRF-Token')) headers.set('X-CSRF-Token', token);
      init = {...init, headers};
    }
    return originalFetch(input, init);
  };
})();
