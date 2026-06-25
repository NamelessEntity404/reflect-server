(() => {
  // cursor: OS default — no custom cursor

  // ── Page transition overlay ───────────────────────────────────────────────
  const overlay = document.createElement('div');
  overlay.style.cssText = [
    'position:fixed','inset:0','z-index:9999997',
    'background:#05060a',
    'opacity:0','pointer-events:none',
    'display:flex','flex-direction:column',
    'align-items:center','justify-content:center','gap:20px',
  ].join(';');

  const bar = document.createElement('div');
  bar.style.cssText = 'width:120px;height:1px;background:rgba(200,240,0,0.15);overflow:hidden;border-radius:1px;';
  const fill = document.createElement('div');
  fill.style.cssText = 'height:100%;width:0%;background:#C8F000;transition:width 0.3s ease;';
  bar.appendChild(fill);

  const label = document.createElement('div');
  label.style.cssText = "font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(200,240,0,0.4);";
  label.textContent = 'Loading';

  overlay.appendChild(label);
  overlay.appendChild(bar);
  document.body.appendChild(overlay);

  function showOverlay() {
    overlay.style.transition = 'opacity 0.15s ease';
    overlay.style.opacity    = '1';
    overlay.style.pointerEvents = 'all';
    fill.style.width = '0%';
    // Animate bar to 80% then wait for navigation
    requestAnimationFrame(() => {
      fill.style.transition = 'width 0.4s ease';
      fill.style.width = '80%';
    });
  }

  function hideOverlay() {
    fill.style.transition = 'width 0.1s ease';
    fill.style.width = '100%';
    setTimeout(() => {
      overlay.style.transition = 'opacity 0.25s ease';
      overlay.style.opacity = '0';
      overlay.style.pointerEvents = 'none';
    }, 100);
  }

  // Fade in from black on page load
  overlay.style.opacity = '1';
  overlay.style.pointerEvents = 'none';
  fill.style.transition = 'none';
  fill.style.width = '100%';
  setTimeout(hideOverlay, 50);

  // Intercept clicks — show overlay immediately on mousedown for fastest feel
  document.addEventListener('mousedown', e => {
    const a = e.target.closest('a');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('http') || href.startsWith('#') || href.startsWith('mailto') || href.startsWith('javascript')) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    // Flash cursor
    cursor.style.transform = 'translate(-50%,-50%) scale(3)';
    ring.style.borderColor = '#C8F000';
    showOverlay();
    setTimeout(() => { cursor.style.transform = 'translate(-50%,-50%) scale(1)'; }, 200);
  });

  document.addEventListener('click', e => {
    const a = e.target.closest('a');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('http') || href.startsWith('#') || href.startsWith('mailto') || href.startsWith('javascript')) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    setTimeout(() => { window.location.href = href; }, 300);
  });

  // Back/forward cache
  window.addEventListener('pageshow', e => {
    if (e.persisted) hideOverlay();
  });

  // ── Global button/link active states ─────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    a, button { cursor: auto !important; }
    a:active { opacity: 0.7 !important; transform: scale(0.97) !important; }
    .paper-card:active, .work-card:active { transform: scale(0.98) !important; }
    .paper-card { transition: background 0.2s, transform 0.15s !important; }
    .work-card  { transition: transform 0.15s, filter 0.2s !important; }
  `;
  document.head.appendChild(style);
})();
