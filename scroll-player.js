function initScrollPlayer(page, totalFrames) {
  const canvas = document.getElementById('c');
  const ctx    = canvas.getContext('2d', { alpha: false });

  canvas.style.willChange = 'contents';

  function setSize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  setSize();
  window.addEventListener('resize', () => { setSize(); renderFrame(Math.round(currentFloat)); }, { passive: true });

  // ── Loading overlay ────────────────────────────────────────────────────────
  const overlay = document.createElement('div');
  overlay.style.cssText = [
    'position:fixed','inset:0','z-index:9998',
    'display:flex','flex-direction:column',
    'align-items:center','justify-content:center',
    'background:#05060a',
    "font-family:'JetBrains Mono',monospace",
  ].join(';');
  overlay.innerHTML = `
    <div style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:#A8A89A;margin-bottom:20px;">
      Loading
    </div>
    <div style="width:200px;height:1px;background:rgba(200,240,0,0.15);border-radius:1px;overflow:hidden;">
      <div id="load-bar" style="height:100%;width:0%;background:#C8F000;transition:width 0.1s linear;"></div>
    </div>
    <div id="load-pct" style="font-size:10px;letter-spacing:0.14em;color:rgba(200,240,0,0.5);margin-top:12px;">0%</div>
  `;
  document.body.appendChild(overlay);

  const loadBar = overlay.querySelector('#load-bar');
  const loadPct = overlay.querySelector('#load-pct');

  // ── Frame storage ──────────────────────────────────────────────────────────
  const bitmaps  = new Array(totalFrames).fill(null);
  let loaded     = 0;
  let ready      = false;
  let currentIdx = 0;

  // Float position for lerp — kept separate from the integer currentIdx
  let currentFloat = 0;
  let targetFloat  = 0;

  // How fast to chase the target. 0.08 = smooth catch-up, no skipped frames.
  // Lower = slower/more cinematic. Higher = snappier but may skip at high velocity.
  const LERP = 0.08;

  function renderFrame(idx) {
    const bmp = bitmaps[idx];
    if (!bmp) return;
    const scale = Math.max(canvas.width / bmp.width, canvas.height / bmp.height);
    const dw = bmp.width  * scale, dh = bmp.height * scale;
    const dx = (canvas.width  - dw) / 2, dy = (canvas.height - dh) / 2;
    ctx.drawImage(bmp, dx, dy, dw, dh);
    currentIdx = idx;
  }

  // ── Continuous RAF loop — lerps currentFloat toward targetFloat each tick ──
  function tick() {
    requestAnimationFrame(tick);
    if (!ready) return;

    currentFloat += (targetFloat - currentFloat) * LERP;

    const newIdx = Math.min(Math.round(currentFloat), totalFrames - 1);
    if (newIdx !== currentIdx) renderFrame(newIdx);
  }
  requestAnimationFrame(tick);

  // ── Scroll handler — only sets targetFloat, never jumps directly ───────────
  function onScroll() {
    if (!ready) return;
    const maxScroll = document.body.scrollHeight - window.innerHeight;
    const pct = maxScroll > 0 ? Math.min(Math.max(window.scrollY / maxScroll, 0), 1) : 0;
    targetFloat = pct * (totalFrames - 1);
  }

  window.addEventListener('scroll', onScroll, { passive: true });

  // ── Preload all frames via Image ───────────────────────────────────────────
  const CHUNK = 8;

  function loadChunk(start) {
    const end = Math.min(start + CHUNK, totalFrames);
    for (let i = start; i < end; i++) {
      const img = new Image();
      const num = String(i + 1).padStart(4, '0');
      img.src = `./_frames/${page}/f${num}.jpg`;
      img.onload = () => {
        createImageBitmap(img).then(bmp => {
          bitmaps[i] = bmp;
          loaded++;
          const pct = Math.round((loaded / totalFrames) * 100);
          loadBar.style.width = pct + '%';
          loadPct.textContent = pct + '%';

          if (loaded === 1) renderFrame(0);

          if (loaded === totalFrames) {
            ready = true;
            overlay.style.transition = 'opacity 0.4s';
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 400);
            onScroll();
          }

          if (i === end - 1 && end < totalFrames) loadChunk(end);
        });
      };
      img.onerror = () => {
        loaded++;
        if (i === end - 1 && end < totalFrames) loadChunk(end);
        if (loaded === totalFrames) { ready = true; overlay.remove(); }
      };
    }
  }

  loadChunk(0);
}
