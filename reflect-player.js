// Reflect background player — frame-by-frame ImageBitmap on canvas
// Scroll VELOCITY drives tunnel speed — fast scroll = fast tunnel, slow scroll = slow tunnel
// Typing freezes frame. Idle auto-plays at 25fps.

(function() {
  var TOTAL   = 300;
  var FPS     = 25;
  var CHUNK   = 16;
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
  window.addEventListener('resize', function() { setSize(); draw(playHead); }, { passive: true });

  var bitmaps    = new Array(TOTAL).fill(null);
  var loaded     = 0;
  var ready      = false;
  var currentIdx = 0;
  var playHead   = 0;      // float — current frame position
  var velocity   = 0;      // frames per tick from scroll
  var isTyping   = false;
  var isScrolling = false;
  var lastScrollY = 0;
  var lastScrollTime = 0;
  var typingTimer, scrollTimer;
  var rafPending = false;

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
    currentIdx = i;
  }

  // Main RAF loop
  var lastTs = 0;
  function loop(ts) {
    requestAnimationFrame(loop);
    if (!ready) return;
    var dt = Math.min(ts - lastTs, 50); // cap at 50ms to avoid jumps
    lastTs = ts;

    if (isTyping) return; // frozen while typing

    if (isScrolling) {
      // Scroll mode: velocity drives playHead
      playHead += velocity;
      // Wrap around
      if (playHead >= TOTAL) playHead -= TOTAL;
      if (playHead < 0) playHead += TOTAL;
      // Decay velocity smoothly
      velocity *= 0.88;
      draw(playHead);
    } else {
      // Idle: auto-advance at FPS
      if (dt >= 1000 / FPS) {
        playHead = (playHead + 1) % TOTAL;
        draw(playHead);
        lastTs = ts;
      }
    }
  }
  requestAnimationFrame(loop);

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

  // Scroll: velocity from scroll delta
  msgsEl.addEventListener('scroll', function() {
    if (!ready) return;
    var now = performance.now();
    var dy = msgsEl.scrollTop - lastScrollY;
    var dt = now - lastScrollTime || 16;
    lastScrollY = msgsEl.scrollTop;
    lastScrollTime = now;

    // Convert scroll pixels/ms to frames — scale factor controls sensitivity
    // ~0.15 frames per pixel scrolled feels natural
    velocity = (dy / dt) * 2.5;

    isScrolling = true;
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function() {
      isScrolling = false;
      velocity = 0;
    }, 150);
  }, { passive: true });

  // Parallel frame loading — 4 streams simultaneously
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
            // Show first frame as soon as it's ready
            if (loaded === 1) { draw(0); }
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

  // 4 parallel streams
  loadChunk(0);
  loadChunk(CHUNK);
  loadChunk(CHUNK * 2);
  loadChunk(CHUNK * 3);

})();
