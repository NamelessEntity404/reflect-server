// Reflect background player — frame-by-frame ImageBitmap on canvas
//
// STATES:
//   reading  (mouse still 2s+) → frozen
//   typing   (keyboard input)  → frozen
//   scrolling                  → velocity-driven tunnel speed
//   active   (mouse moving)    → auto-plays at 25fps
//
// Idle auto-play only runs when mouse is actively moving.
// Still mouse = reading = tunnel stops.

(function() {
  var TOTAL        = 300;
  var FPS          = 25;
  var CHUNK        = 16;
  var BASE         = '/_frames_reflect/';
  var READ_TIMEOUT = 6000; // ms of mouse stillness = reading

  var canvas  = document.getElementById('bg-canvas');
  var ctx     = canvas.getContext('2d', { alpha: false });
  var msgsEl  = document.getElementById('messages');
  var inputEl = document.getElementById('user-input');

  function setSize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  setSize();
  window.addEventListener('resize', function() { setSize(); draw(playHead); }, { passive: true });

  var bitmaps      = new Array(TOTAL).fill(null);
  var loaded       = 0;
  var ready        = false;
  var playHead     = 0;
  var velocity     = 0;
  var isTyping     = false;
  var isScrolling  = false;
  var isReading    = true;  // start as reading until mouse moves
  var lastScrollY  = 0;
  var lastScrollT  = 0;
  var typingTimer, scrollTimer, readTimer, rafPending;

  var loadBar = document.getElementById('reflect-load-bar');
  var loadPct = document.getElementById('reflect-load-pct');
  var overlay = document.getElementById('reflect-load-overlay');

  function draw(idx) {
    var i = Math.round(idx) % TOTAL;
    if (i < 0) i += TOTAL;
    var bmp = bitmaps[i];
    if (!bmp) return;
    var scale = Math.max(canvas.width / bmp.width, canvas.height / bmp.height);
    var dw = bmp.width * scale, dh = bmp.height * scale;
    ctx.drawImage(bmp, (canvas.width - dw) / 2, (canvas.height - dh) / 2, dw, dh);
    playHead = i;
  }

  // Main RAF loop
  var lastTs = 0;
  function loop(ts) {
    requestAnimationFrame(loop);
    if (!ready) return;

    // Frozen states
    if (isTyping || isReading) return;

    var dt = Math.min(ts - lastTs, 50);
    lastTs = ts;

    if (isScrolling) {
      // Velocity-driven
      playHead += velocity;
      if (playHead >= TOTAL) playHead -= TOTAL;
      if (playHead < 0) playHead += TOTAL;
      velocity *= 0.88;
      draw(playHead);
    } else {
      // Active (mouse moving): auto-play at FPS
      if (dt >= 1000 / FPS) {
        playHead = (playHead + 1) % TOTAL;
        draw(playHead);
        lastTs = ts;
      }
    }
  }
  requestAnimationFrame(loop);

  // Mouse movement = active, start reading timer
  document.addEventListener('mousemove', function() {
    isReading = false;
    clearTimeout(readTimer);
    readTimer = setTimeout(function() { isReading = true; }, READ_TIMEOUT);
  }, { passive: true });

  // Touch = active (mobile)
  document.addEventListener('touchstart', function() {
    isReading = false;
    clearTimeout(readTimer);
    readTimer = setTimeout(function() { isReading = true; }, READ_TIMEOUT);
  }, { passive: true });

  // Typing: freeze
  inputEl.addEventListener('input', function() {
    isTyping = true;
    clearTimeout(typingTimer);
    typingTimer = setTimeout(function() { isTyping = false; }, 1200);
  });
  inputEl.addEventListener('blur', function() {
    clearTimeout(typingTimer);
    isTyping = false;
  });

  // Scroll: velocity-driven
  msgsEl.addEventListener('scroll', function() {
    if (!ready) return;
    var now = performance.now();
    var dy  = msgsEl.scrollTop - lastScrollY;
    var dt  = now - lastScrollT || 16;
    lastScrollY = msgsEl.scrollTop;
    lastScrollT = now;
    velocity = (dy / dt) * 2.5;
    isScrolling = true;
    isReading = false;
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function() {
      isScrolling = false;
      velocity = 0;
    }, 150);
  }, { passive: true });

  // Frame loading — 4 parallel streams
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
            if (loaded === 1) draw(0);
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
          loaded++; pending--;
          if (pending === 0 && end < TOTAL) loadChunk(end);
          if (loaded === TOTAL) { ready = true; if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay); }
        };
      })(i);
    }
  }

  loadChunk(0);
  loadChunk(CHUNK);
  loadChunk(CHUNK * 2);
  loadChunk(CHUNK * 3);

})();
