/* A harmless, opt-out mouse-stealing duck for one opted-in FjordHub username.
   It never moves the OS pointer, captures input, or changes application state. */
(() => {
  'use strict';

  if (!window.matchMedia('(pointer: fine)').matches ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const DISMISSED = 'fjordhub-duck-dismissed';
  try {
    if (window.sessionStorage.getItem(DISMISSED) === '1') return;
  } catch (_) { /* Private mode or blocked storage: Escape still works. */ }

  let stage, duck, cursor, notice, stopButton;
  let frameId = 0, timerId = 0, previousTime = 0, enteredAt = 0, grabbedAt = 0;
  let mode = 'waiting', duckX = -140, duckY = 0;
  let pointerX = innerWidth * 0.6, pointerY = innerHeight * 0.5;

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  function trackPointer(event) {
    if (event.pointerType && event.pointerType !== 'mouse') return;
    pointerX = event.clientX;
    pointerY = event.clientY;
  }

  function stopDuck() {
    if (mode === 'stopped') return;
    mode = 'stopped';
    clearTimeout(timerId);
    cancelAnimationFrame(frameId);
    document.body.classList.remove('fjord-duck-carrying');
    window.removeEventListener('pointermove', trackPointer);
    window.removeEventListener('keydown', onKeyDown, true);
    window.removeEventListener('pagehide', stopDuck);
    stage?.remove();
    notice?.remove();
    try { window.sessionStorage.setItem(DISMISSED, '1'); } catch (_) {}
  }

  function onKeyDown(event) {
    if (event.key === 'Escape') stopDuck();
  }

  function createDuck() {
    stage = document.createElement('div');
    stage.className = 'fjord-duck-stage';
    stage.setAttribute('aria-hidden', 'true');
    stage.innerHTML = `
      <div class="fjord-duck-bird">
        <svg viewBox="0 0 132 110" role="presentation" focusable="false">
          <path d="M46 80v13m24-13v13M46 92H31m39 0H55" stroke="#D77E1C" stroke-width="6" stroke-linecap="round" fill="none"/>
          <path d="M27 56 8 43l12 31 17-5" fill="#E9BB3E"/>
          <ellipse cx="60" cy="66" rx="45" ry="30" fill="#F6D35A"/>
          <path d="M36 65c12-15 28-13 43-4-9 15-28 23-43 4Z" fill="#E8B83A"/>
          <path d="M78 55c0-19 4-30 13-34 9-4 22 2 25 13 3 12-2 23-13 29Z" fill="#F6D35A"/>
          <circle cx="98" cy="29" r="3.8" fill="#243146"/>
          <path d="M112 37c8-3 15-2 20 5l-20 10-8-8Z" fill="#E88922"/>
          <path d="M115 44h12" stroke="#BC661A" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="fjord-duck-cursor">
        <svg viewBox="0 0 28 35" aria-hidden="true">
          <path d="M2 2v27l7.5-7.5L15 33l5-2.5-5.5-11.5 11-1Z"
                fill="#fff" stroke="#202a3a" stroke-width="2.5" stroke-linejoin="round"/>
        </svg>
      </div>`;
    document.body.appendChild(stage);
    duck = stage.querySelector('.fjord-duck-bird');
    cursor = stage.querySelector('.fjord-duck-cursor');

    notice = document.createElement('div');
    notice.className = 'fjord-duck-notice';
    const message = document.createElement('span');
    message.textContent = '🦆 Haps! Anden stjal din mus. Tryk Esc for at stoppe.';
    stopButton = document.createElement('button');
    stopButton.type = 'button';
    stopButton.className = 'fjord-duck-stop';
    stopButton.textContent = 'Stop anden';
    stopButton.addEventListener('click', stopDuck);
    notice.append(message, stopButton);
    document.body.appendChild(notice);
  }

  function showDuck() {
    if (mode === 'stopped') return;
    mode = 'chase';
    duckX = -135;
    duckY = clamp(pointerY - 40, 5, Math.max(5, innerHeight - 104));
    enteredAt = performance.now();
    previousTime = 0;
    cursor.classList.remove('visible');
    duck.style.visibility = 'visible';
    frameId = requestAnimationFrame(animate);
  }

  function grabCursor(time) {
    mode = 'carry';
    grabbedAt = time;
    cursor.classList.add('visible');
    document.body.classList.add('fjord-duck-carrying');
    notice.classList.add('visible');
  }

  function releaseCursor() {
    mode = 'waiting';
    document.body.classList.remove('fjord-duck-carrying');
    cursor.classList.remove('visible');
    duck.style.visibility = 'hidden';
    timerId = setTimeout(showDuck, 2800 + Math.random() * 2600);
  }

  function animate(time) {
    if (mode === 'stopped' || mode === 'waiting') return;
    const dt = previousTime ? clamp((time - previousTime) / 1000, 0, 0.05) : 0.016;
    previousTime = time;

    if (mode === 'chase') {
      const targetX = pointerX - 112;
      const targetY = pointerY - 40;
      const dx = targetX - duckX, dy = targetY - duckY;
      const distance = Math.hypot(dx, dy);
      const speed = 560 + Math.min(750, (time - enteredAt) * 0.22);
      if (distance > 2) {
        const move = Math.min(speed * dt, distance);
        duckX += dx / distance * move;
        duckY += dy / distance * move;
      }
      if (distance < 16) grabCursor(time);
    } else if (mode === 'carry') {
      const elapsed = (time - grabbedAt) / 1000;
      duckX += (670 + Math.min(170, elapsed * 55)) * dt;
      duckY = clamp(duckY + Math.sin(time / 150) * 42 * dt,
                    5, Math.max(5, innerHeight - 104));
      cursor.style.transform = `translate3d(${duckX + 111}px,${duckY + 38}px,0)`;
      if (duckX > innerWidth + 125 || elapsed > 3.6) {
        releaseCursor();
      }
    }

    duck.style.transform = `translate3d(${duckX}px,${duckY}px,0)`;
    if (mode !== 'waiting' && mode !== 'stopped') {
      frameId = requestAnimationFrame(animate);
    }
  }

  function onReady() {
    if (!document.body) return;
    createDuck();
    window.addEventListener('pointermove', trackPointer, { passive: true });
    window.addEventListener('keydown', onKeyDown, true);
    window.addEventListener('pagehide', stopDuck);
    timerId = setTimeout(showDuck, 750);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', onReady, { once: true });
  } else {
    onReady();
  }
})();
