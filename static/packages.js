(() => {
  const toast = document.getElementById('package-toast');
  const showToast = (message, error = false) => {
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast show ${error ? 'err' : 'ok'}`;
    setTimeout(() => toast.classList.remove('show'), 2600);
  };

  document.querySelectorAll('.package-card').forEach(card => {
    const id = card.dataset.packageId;
    const install = card.querySelector('.package-install');
    const remove = card.querySelector('.package-remove');
    const setInstalled = value => {
      card.classList.toggle('is-installed', value);
      if (install) install.hidden = value;
      if (remove) remove.hidden = !value;
      card.querySelector('.package-open').hidden = !value;
      card.querySelector('.package-installed-label').hidden = !value;
    };
    install?.addEventListener('click', async () => {
      install.disabled = true;
      install.textContent = 'Installerer…';
      try {
        const response = await fetch(`/api/packages/${id}/install`, {method: 'POST'});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Installationen fejlede');
        setInstalled(true);
        showToast('Pakken er installeret');
      } catch (error) { showToast(error.message, true); }
      finally { install.disabled = false; install.textContent = 'Installér'; }
    });
    remove?.addEventListener('click', async () => {
      if (!confirm('Vil du afinstallere pakken?')) return;
      try {
        const response = await fetch(`/api/packages/${id}/uninstall`, {method: 'POST'});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Afinstallationen fejlede');
        setInstalled(false);
        showToast('Pakken er afinstalleret');
      } catch (error) { showToast(error.message, true); }
    });
  });

  const noteContent = document.getElementById('note-content');
  const noteTitle = document.getElementById('note-title');
  if (noteContent && noteTitle) {
    noteTitle.value = localStorage.getItem('fjordhub-note-title') || '';
    noteContent.value = localStorage.getItem('fjordhub-note-content') || '';
    const save = () => {
      localStorage.setItem('fjordhub-note-title', noteTitle.value);
      localStorage.setItem('fjordhub-note-content', noteContent.value);
      document.getElementById('note-count').textContent = `${noteContent.value.length} tegn`;
      document.getElementById('note-status').textContent = 'Gemt lokalt';
    };
    [noteTitle, noteContent].forEach(field => field.addEventListener('input', save));
    save();
  }

  const calendarGrid = document.getElementById('calendar-grid');
  if (calendarGrid) {
    let view = new Date(); view.setDate(1);
    const names = ['januar','februar','marts','april','maj','juni','juli','august','september','oktober','november','december'];
    const render = () => {
      document.getElementById('cal-month').textContent = `${names[view.getMonth()]} ${view.getFullYear()}`;
      calendarGrid.innerHTML = '';
      const offset = (view.getDay() + 6) % 7;
      const days = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
      const today = new Date();
      for (let i = 0; i < offset; i++) calendarGrid.appendChild(document.createElement('span'));
      for (let day = 1; day <= days; day++) {
        const cell = document.createElement('button'); cell.textContent = day;
        if (day === today.getDate() && view.getMonth() === today.getMonth() && view.getFullYear() === today.getFullYear()) cell.className = 'today';
        calendarGrid.appendChild(cell);
      }
    };
    document.getElementById('cal-prev').onclick = () => { view.setMonth(view.getMonth() - 1); render(); };
    document.getElementById('cal-next').onclick = () => { view.setMonth(view.getMonth() + 1); render(); };
    render();
  }
})();
