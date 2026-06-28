// Scroll-driven video playback in work grid cards
// Each .work-card[data-vid] has a <canvas> that scrubs through its video
// as the card scrolls through the viewport. GPU-accelerated via ImageBitmap.

(() => {
'use strict';

const DPR = Math.min(window.devicePixelRatio || 1, 2);

// ── Frame cache + queue-based loader ─────────────────────────────────────────
let VIDS = [];
const cache = {};       // cache[vi][fi] = ImageBitmap
const q = [];           // {vi, fi, hi}
const flying = new Set();
const MAX = 8;

function enq(vi, fi, hi) {
  if (!VIDS[vi] || fi < 0 || fi >= VIDS[vi].frames) return;
  const k = vi * 100000 + fi;
  if (flying.has(k) || (cache[vi] && cache[vi][fi])) return;
  hi ? q.unshift({ vi, fi, k }) : q.push({ vi, fi, k });
  pump();
}

function pump() {
  while (flying.size < MAX && q.length) {
    const { vi, fi, k } = q.shift();
    if (flying.has(k) || (cache[vi] && cache[vi][fi])) { pump(); return; }
    flying.add(k);
    const img = new Image();
    img.onload = () => {
      createImageBitmap(img, { premultiplyAlpha: 'none' }).then(bmp => {
        if (!cache[vi]) cache[vi] = {};
        cache[vi][fi] = bmp;
        flying.delete(k);
        pump();
      });
      img.onload = null;
    };
    img.onerror = () => { flying.delete(k); pump(); };
    img.src = `./_frames/b/${VIDS[vi].id}/f${String(fi + 1).padStart(4, '0')}.jpg`;
  }
}

function preloadAround(vi, fi) {
  for (let d = 0; d <= 3; d++) enq(vi, fi + d, true);
  for (let d = 4; d <= 20; d++) enq(vi, fi + d, false);
  for (let d = 1; d <= 4; d++) enq(vi, fi - d, false);
}

function preloadVideo(vi) {
  if (!VIDS[vi]) return;
  for (let fi = 0; fi < VIDS[vi].frames; fi++) enq(vi, fi, false);
}

// ── Per-card draw ─────────────────────────────────────────────────────────────
// ctx cached per canvas element
const ctxMap = new WeakMap();

function drawFrame(canvas, bmp) {
  if (!bmp) return;
  let ctx = ctxMap.get(canvas);
  if (!ctx) {
    ctx = canvas.getContext('2d', { alpha: false, desynchronized: true });
    ctxMap.set(canvas, ctx);
  }
  // Cover fit — same as object-fit:cover
  const scale = Math.max(canvas.width / bmp.width, canvas.height / bmp.height);
  const dw = bmp.width * scale, dh = bmp.height * scale;
  const dx = (canvas.width - dw) / 2, dy = (canvas.height - dh) / 2;
  ctx.drawImage(bmp, dx, dy, dw, dh);
}

// ── Scroll → frame mapping ────────────────────────────────────────────────────
function getProgress(el) {
  const rect = el.getBoundingClientRect();
  const vh = window.innerHeight;
  // 0 = card center at viewport bottom, 1 = card center at viewport top
  const center = rect.top + rect.height / 2;
  return 1 - (center / vh);
}

let cards = [];
let rafPending = false;

function tick() {
  rafPending = false;
  const vh = window.innerHeight;
  cards.forEach(({ el, canvas, vi }) => {
    if (!VIDS[vi]) return;
    const rect = el.getBoundingClientRect();
    // Skip cards not near viewport
    if (rect.bottom < -100 || rect.top > vh + 100) return;

    const p = Math.max(0, Math.min(1, getProgress(el)));
    const fi = Math.round(p * (VIDS[vi].frames - 1));
    const bmp = cache[vi] && cache[vi][fi];
    if (bmp) drawFrame(canvas, bmp);
    preloadAround(vi, fi);
  });
}

function onScroll() {
  if (rafPending) return;
  rafPending = true;
  requestAnimationFrame(tick);
}

// ── Canvas sizing ─────────────────────────────────────────────────────────────
function sizeCanvas(canvas) {
  // Use parent card dimensions as fallback — canvas is position:absolute inside it
  const parent = canvas.parentElement;
  const w = canvas.offsetWidth || parent.offsetWidth || parent.getBoundingClientRect().width;
  const h = canvas.offsetHeight || parent.offsetHeight || parent.getBoundingClientRect().height;
  if (!w || !h) return;
  const pw = Math.round(w * DPR);
  const ph = Math.round(h * DPR);
  if (canvas.width === pw && canvas.height === ph) return;
  canvas.width  = pw;
  canvas.height = ph;
}

// ── Init ──────────────────────────────────────────────────────────────────────
fetch('./_frames/b/manifest.json')
  .then(r => r.json())
  .then(data => {
    VIDS = data;

    cards = Array.from(document.querySelectorAll('.work-card[data-vid]')).map(el => {
      const canvas = el.querySelector('canvas');
      const vi = parseInt(el.dataset.vid.replace('v', ''), 10);
      new ResizeObserver(() => { sizeCanvas(canvas); tick(); }).observe(el);
      return { el, canvas, vi };
    });

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', () => {
      cards.forEach(({ el, canvas }) => sizeCanvas(canvas));
      tick();
    }, { passive: true });

    // Preload all videos progressively — seed first 3 immediately
    preloadVideo(0);
    preloadVideo(1);
    preloadVideo(2);
    let seeded = 3;
    const seedNext = () => {
      if (seeded < VIDS.length) {
        preloadVideo(seeded++);
        setTimeout(seedNext, 800);
      }
    };
    setTimeout(seedNext, 2000);

    // Size all canvases and draw after layout settles
    cards.forEach(({ canvas }) => sizeCanvas(canvas));
    requestAnimationFrame(() => {
      cards.forEach(({ canvas }) => sizeCanvas(canvas));
      tick();
    });
  })
  .catch(e => console.warn('[work-video-gl]', e));

})();
