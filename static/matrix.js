(() => {
  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const $ = id => document.getElementById(id);
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
      $('matrix-message').textContent = data.message || '';
      $('matrix-install').disabled = data.phase === 'ready' || data.phase === 'installing';
      if (data.phase === 'ready') {
        $('matrix-install').textContent = 'Installeret';
        $('matrix-domain').disabled = true;
      }
      if (data.phase === 'error') message(data.message || 'Installationen fejlede.', true);
    } catch (_) { /* Remain usable when offline. */ }
  };
  $('matrix-install-form').addEventListener('submit', async e => {
    e.preventDefault();
    $('matrix-install').disabled = true;
    try {
      const data = await post('/api/matrix/install', {domain: $('matrix-domain').value});
      message(data.message);
    } catch (err) {
      message(err.message, true);
      $('matrix-install').disabled = false;
    }
    refresh();
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
      copy.className = 'btn-open';
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
    button.className = 'btn-open';
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
