// Reflect background player — frame-by-frame ImageBitmap on canvas
// Blocks on loading overlay until ALL 300 frames are GPU-resident.
// Scroll in #messages drives frame index. Typing freezes frame.
// Idle: auto-advances at 25fps loop.

(function() {
  var TOTAL   = 300;
  var FPS     = 25;
  var CHUNK   = 16; // larger chunks = faster parallel loading
  var BASE    = '/_frames_reflect/';

  var canvas  = document.getElementById('bg-canvas');
  var ctx     = canvas.getContext('2d', { alpha: false });
  var msgsEl  = document.getElementById('messages');
  var inputEl = document.getElementById('user-input');

  function setSize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  setSize();
  window.addEventListener('resize', function() { setSize(); draw(currentIdx); }, { passive: true });

  var bitmaps    = new Array(TOTAL).fill(null);
  var loaded     = 0;
  var ready      = false;
  var currentIdx = 0;
  var targetIdx  = 0;
  var playHead   = 0;
  var isTyping   = false;
  var isScrolling = false;
  var lastTime   = 0;
  var rafPending = false;
  var typingTimer, scrollTimer;

  var loadBar = document.getElementById('reflect-load-bar');
  var loadPct = document.getElementById('reflect-load-pct');
  var overlay = document.getElementById('reflect-load-overlay');

  function draw(idx) {
    var bmp = bitmaps[Math.min(Math.max(idx, 0), TOTAL - 1)];
    if (!bmp) return;
    var scale = Math.max(canvas.width / bmp.width, canvas.height / bmp.height);
    var dw = bmp.width * scale, dh = bmp.height * scale;
    ctx.drawImage(bmp, (canvas.width - dw) / 2, (canvas.height - dh) / 2, dw, dh);
    currentIdx = idx;
  }

  // Auto-play loop — only runs when ready, not typing, not scrolling
  function idleLoop(ts) {
    requestAnimationFrame(idleLoop);
    if (!ready || isTyping || isScrolling) return;
    if (ts - lastTime < 1000 / FPS) return;
    lastTime = ts;
    playHead = (playHead + 1) % TOTAL;
    draw(playHead);
  }
  requestAnimationFrame(idleLoop);

  // Typing: freeze on current frame
  inputEl.addEventListener('input', function() {
    isTyping = true;
    clearTimeout(typingTimer);
    typingTimer = setTimeout(function() { isTyping = false; }, 1200);
  });
  inputEl.addEventListener('blur', function() {
    clearTimeout(typingTimer);
    isTyping = false;
  });

  // Scroll: drive frame from messages scroll position
  msgsEl.addEventListener('scroll', function() {
    if (!ready) return;
    var maxScroll = msgsEl.scrollHeight - msgsEl.clientHeight;
    if (maxScroll <= 0) return;
    isScrolling = true;
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function() { isScrolling = false; }, 700);
    var pct = Math.min(Math.max(msgsEl.scrollTop / maxScroll, 0), 1);
    targetIdx = Math.round(pct * (TOTAL - 1));
    if (!rafPending) {
      rafPending = true;
      requestAnimationFrame(function() {
        rafPending = false;
        draw(targetIdx);
        playHead = targetIdx;
      });
    }
  }, { passive: true });

  // Load all frames in parallel chunks — don't unlock until everything is ready
  function loadChunk(start) {
    var end = Math.min(start + CHUNK, TOTAL);
    var pending = end - start;
    for (var i = start; i < end; i++) {
      (function(idx) {
        var img = new Image();
        img.src = BASE + 'f' + String(idx + 1).padStart(4, '0') + '.jpg';
        img.onload = function() {
          createImageBitmap(img).then(function(bmp) {
            bitmaps[idx] = bmp;
            loaded++;
            var pct = Math.round((loaded / TOTAL) * 100);
            if (loadBar) loadBar.style.width = pct + '%';
            if (loadPct) loadPct.textContent = pct + '%';
            pending--;
            if (loaded === TOTAL) {
              ready = true;
              if (overlay) {
                overlay.style.transition = 'opacity 0.5s';
                overlay.style.opacity = '0';
                setTimeout(function() { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); }, 500);
              }
            }
            if (pending === 0 && end < TOTAL) loadChunk(end);
          });
        };
        img.onerror = function() {
          loaded++;
          pending--;
          if (pending === 0 && end < TOTAL) loadChunk(end);
          if (loaded === TOTAL) { ready = true; if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay); }
        };
      })(i);
    }
  }

  // Kick off 4 parallel chunk streams for faster loading
  loadChunk(0);
  loadChunk(CHUNK);
  loadChunk(CHUNK * 2);
  loadChunk(CHUNK * 3);

})();
