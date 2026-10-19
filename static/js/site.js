(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const status = document.getElementById('action-status');
  const announce = text => { if (status) status.textContent = text; };
  const get = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const set = (key, value) => { try { localStorage.setItem(key, value); return true; } catch { return false; } };
  const root = document.documentElement;
  const stored = get('nexusup-theme');
  if (stored === 'dark' || stored === 'light') root.dataset.theme = stored;
  document.getElementById('theme-toggle')?.addEventListener('click', () => {
    const isDark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = isDark ? 'light' : 'dark'; set('nexusup-theme', root.dataset.theme);
  });
  const toggle = document.getElementById('menu-toggle');
  const nav = document.getElementById('primary-nav');
  toggle?.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open)); nav.classList.toggle('open', open);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle?.getAttribute('aria-expanded') === 'true') {
      nav.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus();
    }
  });
  document.querySelectorAll('[data-save]').forEach(button => {
    const key = 'nexusup-saved-' + button.dataset.save;
    const update = () => { const saved = get(key) === '1'; button.textContent = saved ? 'Saved ✓' : 'Save story'; button.setAttribute('aria-pressed', String(saved)); };
    update(); button.addEventListener('click', () => {
      const ok = set(key, get(key) === '1' ? '0' : '1'); update();
      announce(ok ? 'Reading preference saved in this browser only.' : 'Browser storage is unavailable.');
    });
  });
  document.getElementById('share-button')?.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(location.href); announce('Story link copied. This is a local demo URL.'); }
    catch { announce('Copy unavailable. Copy the URL from your address bar.'); }
  });
})();
