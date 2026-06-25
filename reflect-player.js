// Reflect background player — frame-by-frame ImageBitmap on canvas
// Scroll in #messages drives frame index. Typing freezes frame.
// Idle: auto-advances at 25fps loop.

(function() {
  const TOTAL   = 300;
  const FPS     = 25;
  const CHUNK   = 8;
  const BASE    = '/_frames_reflect/';

  const canvas  = document.getElementById('bg-canvas');
  const ctx     = canvas.getContext('2d', { alpha: false });
  const msgsEl  = document.getElementById('messages');
  const inputEl = document.getElementById('user-input');

  function setSize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  setSize();
  window.addEventListener('resize', () => { setSize(); draw(currentIdx); }, { passive: true });

  const bitmaps  = new Array(TOTAL).fill(null);
  let loaded     = 0;
  let ready      = false;
  let currentIdx = 0;
  let targetIdx  = 0;

  // Loading bar
  const loadBar  = document.getElementById('reflect-load-bar');
  const loadPct  = document.getElementById('reflect-load-pct');

  function draw(idx) {
    const bmp = bitmaps[idx];
    if (!bmp) return;
    const scale = Math.max(canvas.width / bmp.width, canvas.height / bmp.height);
    const dw = bmp.width * scale, dh = bmp.height * scale;
    ctx.drawImage(bmp, (canvas.width - dw) / 2, (canvas.height - dh) / 2, dw, dh);
    currentIdx = idx;
  }

  // ── IDLE auto-play loop ────────────────────────────────────────────────────
  let isTyping   = false;
  let isScrolling = false;
  let lastTime   = 0;
  let playHead   = 0;

  function idleLoop(ts) {
    requestAnimationFrame(idleLoop);
    if (!ready || isTyping || isScrolling) return;
    const dt = ts - lastTime;
    if (dt < 1000 / FPS) return;
    lastTime = ts;
    playHead = (playHead + 1) % TOTAL;
    draw(playHead);
  }
  requestAnimationFrame(idleLoop);

  // ── TYPING: freeze ─────────────────────────────────────────────────────────
  let typingTimer = null;
  inputEl.addEventListener('input', () => {
    isTyping = true;
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => { isTyping = false; }, 1200);
  });
  inputEl.addEventListener('blur', () => {
    clearTimeout(typingTimer);
    isTyping = false;
  });

  // ── SCROLL: drive frame from messages scroll position ──────────────────────
  let scrollTimer = null;
  let rafPending  = false;

  msgsEl.addEventListener('scroll', () => {
    if (!ready) return;
    isScrolling = true;
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => { isScrolling = false; }, 700);

    const maxScroll = msgsEl.scrollHeight - msgsEl.clientHeight;
    if (maxScroll <= 0) return;
    const pct = Math.min(Math.max(msgsEl.scrollTop / maxScroll, 0), 1);
    targetIdx = Math.round(pct * (TOTAL - 1));

    if (!rafPending) {
      rafPending = true;
      requestAnimationFrame(() => {
        rafPending = false;
        draw(targetIdx);
        playHead = targetIdx;
      });
    }
  }, { passive: true });

  // ── Frame loading ──────────────────────────────────────────────────────────
  function loadChunk(start) {
    const end = Math.min(start + CHUNK, TOTAL);
    for (let i = start; i < end; i++) {
      const img = new Image();
      img.src = BASE + 'f' + String(i + 1).padStart(4, '0') + '.jpg';
      img.onload = () => {
        createImageBitmap(img).then(bmp => {
          bitmaps[i] = bmp;
          loaded++;
          const pct = Math.round((loaded / TOTAL) * 100);
          if (loadBar) loadBar.style.width = pct + '%';
          if (loadPct) loadPct.textContent = pct + '%';
          if (loaded === 1) draw(0);
          if (loaded === TOTAL) {
            ready = true;
            const overlay = document.getElementById('reflect-load-overlay');
            if (overlay) {
              overlay.style.transition = 'opacity 0.4s';
              overlay.style.opacity = '0';
              setTimeout(() => overlay.remove(), 400);
            }
          }
          if (i === end - 1 && end < TOTAL) loadChunk(end);
        });
      };
      img.onerror = () => {
        loaded++;
        if (i === end - 1 && end < TOTAL) loadChunk(end);
        if (loaded === TOTAL) { ready = true; }
      };
    }
  }

  loadChunk(0);
})();
