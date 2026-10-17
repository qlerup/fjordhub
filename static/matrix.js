(() => {
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const $ = id => document.getElementById(id);
  const domainInput = $('matrix-domain');
  const configuredUrl = domainInput.dataset.hubPublicUrl || '';
  const externalOrigin = configuredUrl || (location.protocol === 'https:' ? location.origin : '');
  const previewDomain = (() => {
    try {
      const url = new URL(externalOrigin);
      if (url.protocol !== 'https:' || (url.port && url.port !== '443')) return '';
      return url.hostname.toLowerCase();
    } catch (_) { return ''; }
  })();
  if (!domainInput.value) domainInput.value = previewDomain || 'Åbn FjordHub via dit HTTPS-domæne først';
  const message = (text, isError = false) => {
    const node = $('matrix-feedback');
    node.textContent = text;
    node.style.color = isError ? '#ef6b6b' : 'var(--text-muted)';
  };
  const post = async (url, data) => {
    const response = await fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type':'application/json', 'X-CSRF-Token':csrf},
      body: JSON.stringify(data)
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'Handlingen mislykkedes');
    return payload;
  };
  const refresh = async () => {
    try {
      const response = await fetch('/api/matrix/status', {credentials:'same-origin',cache:'no-store'});
      if (!response.ok) return;
      const data = await response.json();
      if (data.domain) $('matrix-bot-id').textContent = '@fjordhub-bot:' + data.domain;
      $('matrix-phase').textContent = data.phase;
      $('matrix-server').textContent = data.server;
      $('matrix-bot').textContent = data.bot_ready ? 'Online' : data.bot;
      $('matrix-bot-update').hidden = data.phase !== 'ready';
      $('matrix-bot-update').disabled = data.bot_update === 'running';
      $('matrix-bot-update-message').textContent = data.bot_update_message || '';
      $('matrix-bot-identity').textContent = data.bot_identity?.message || '';
      $('matrix-message').textContent = data.message || '';
      $('matrix-install').disabled = data.phase === 'ready' || data.phase === 'installing' || !previewDomain;
      $('matrix-connectivity').hidden = data.phase !== 'ready';
      if (data.domain) domainInput.value = data.domain;
      if (data.phase === 'ready') {
        $('matrix-install').textContent = 'Installeret';
      }
      if (data.phase === 'error') message(data.message || 'Installationen fejlede.', true);
    } catch (_) { /* Remain usable when offline. */ }
  };
  $('matrix-install-form').addEventListener('submit', async e => {
    e.preventDefault();
    if (!previewDomain) {
      message('Åbn FjordHub via dens offentlige HTTPS-adresse for at installere.', true);
      return;
    }
    $('matrix-install').disabled = true;
    try {
      const data = await post('/api/matrix/install', {origin: externalOrigin});
      message(data.message);
    } catch (err) {
      message(err.message, true);
      $('matrix-install').disabled = !previewDomain;
    }
    refresh();
  });
  $('matrix-connectivity').addEventListener('click', async () => {
    const result = $('matrix-connectivity-result');
    result.textContent = 'Tester...';
    try {
      if (!externalOrigin) throw new Error('Åbn FjordHub via HTTPS først.');
      const response = await fetch(externalOrigin + '/_matrix/client/versions',
        {cache: 'no-store', mode: 'cors'});
      const body = await response.json();
      if (!response.ok || !Array.isArray(body.versions)) {
        throw new Error('Matrix API svarer ikke korrekt.');
      }
      result.textContent = '✅ Matrix API svarer gennem FjordHubs eksisterende adresse.';
    } catch (err) {
      result.textContent = '❌ Kunne ikke nå Matrix gennem domænet: ' + err.message;
    }
  });
  $('matrix-bot-update').addEventListener('click', async () => {
    $('matrix-bot-update').disabled = true;
    try {
      const result = await post('/api/matrix/bot/update', {});
      message(result.message);
    } catch (err) {
      message(err.message, true);
    }
    await refresh();
  });
  $('matrix-user-form').addEventListener('submit', async e => {
    e.preventDefault();
    const button = e.target.querySelector('button');
    button.disabled = true;
    try {
      const data = await post('/api/matrix/users', {username: $('matrix-username').value});
      const box = $('matrix-credentials');
      box.hidden = false;
      box.replaceChildren();
      const title = document.createElement('strong');
      title.textContent = 'Gem disse oplysninger – adgangskoden vises kun nu!';
      box.append(title);
      [['Server', data.url], ['Bruger', data.user_id], ['Adgangskode', data.password]].forEach(([label, value]) => {
        const p = document.createElement('p');
        p.textContent = label + ': ' + value;
        box.append(p);
      });
      const copy = document.createElement('button');
      copy.type = 'button';
      copy.className = 'btn btn-open';
      copy.textContent = 'Kopiér loginoplysninger';
      copy.addEventListener('click', () => navigator.clipboard?.writeText(
        'Server: ' + data.url + '\nBruger: ' + data.user_id + '\nAdgangskode: ' + data.password
      ));
      box.append(copy);
      addUser(data.user_id);
      message('Brugeren er oprettet. Åbn Element X og start en krypteret chat med botten.');
    } catch (err) { message(err.message, true); }
    finally { button.disabled = false; }
  });
  const addUser = (id) => {
    if (Array.from(document.querySelectorAll('[data-test-user]')).some(x => x.dataset.testUser === id)) return;
    const div = document.createElement('div');
    div.className = 'matrix-user';
    const span = document.createElement('span');
    span.textContent = id;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn btn-open';
    button.dataset.testUser = id;
    button.textContent = 'Send push-test';
    div.append(span,button);
    $('matrix-users').append(div);
  };
  $('matrix-users').addEventListener('click', async e => {
    const button = e.target.closest('[data-test-user]');
    if (!button) return;
    button.disabled = true;
    try {
      const data = await post('/api/matrix/test', {user_id:button.dataset.testUser});
      message(data.message);
    } catch (err) { message(err.message,true); }
    finally { button.disabled = false; }
  });
  window.setInterval(refresh, 10000);
})();
