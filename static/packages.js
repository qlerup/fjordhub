(() => {
  const toast = document.getElementById('package-toast');
  const showToast = (message, error = false) => {
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast show ${error ? 'err' : 'ok'}`;
    setTimeout(() => toast.classList.remove('show'), 2600);
  };

  // Rammer både butikkens .package-card og launcher-rækkerne på "Installerede apps"
  document.querySelectorAll('[data-package-id]').forEach(card => {
    const id = card.dataset.packageId;
    const install = card.querySelector('.package-install');
    const remove = card.querySelector('.package-remove');
    const setInstalled = value => {
      card.classList.toggle('is-installed', value);
      if (install) install.hidden = value;
      if (remove) remove.hidden = !value;
      const open = card.querySelector('.package-open');
      const label = card.querySelector('.package-installed-label');
      if (open) open.hidden = !value;
      if (label) label.hidden = !value;
    };
    const update = card.querySelector('.package-update');
    update?.addEventListener('click', async () => {
      update.disabled = true;
      update.textContent = 'Opdaterer…';
      try {
        const response = await fetch(`/api/packages/${id}/install`, {method: 'POST'});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Opdateringen fejlede');
        update.hidden = true;
        const hint = card.querySelector('.package-update-hint');
        if (hint) hint.textContent = hint.textContent.split('→').pop().trim();
        showToast('Appen er opdateret');
      } catch (error) { showToast(error.message, true); }
      finally { update.disabled = false; update.textContent = 'Opdatér'; }
    });
    install?.addEventListener('click', async () => {
      install.disabled = true;
      install.textContent = 'Installerer…';
      try {
        const response = await fetch(`/api/packages/${id}/install`, {method: 'POST'});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Installationen fejlede');
        setInstalled(true);
        showToast('Appen er installeret');
      } catch (error) { showToast(error.message, true); }
      finally { install.disabled = false; install.textContent = 'Installér'; }
    });
    remove?.addEventListener('click', async () => {
      if (!confirm('Vil du afinstallere appen og fjerne dens filer?')) return;
      try {
        const response = await fetch(`/api/packages/${id}/uninstall`, {method: 'POST'});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Afinstallationen fejlede');
        if (document.body.querySelector('.package-page [data-package-id]') && location.pathname === '/packages') {
          card.remove();
          if (!document.querySelector('[data-package-id]')) location.reload();
        } else {
          setInstalled(false);
        }
        showToast('Appen er afinstalleret');
      } catch (error) { showToast(error.message, true); }
    });
  });

})();
