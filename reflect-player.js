// Perspective background player
// Capped canvas resolution, fixed-interval RAF, typing pause only

(function() {
  var TOTAL  = 300;
  var FPS    = 25;
  var CHUNK  = 32; // bigger chunks = faster load
  var BASE   = '/_frames_reflect/';
  var DPR    = Math.min(window.devicePixelRatio || 1, 1.5); // cap at 1.5x

  var canvas  = document.getElementById('bg-canvas');
  var ctx     = canvas.getContext('2d', { alpha: false, desynchronized: true });
  var inputEl = document.getElementById('user-input');

  function setSize() {
    var w = window.innerWidth;
    var h = window.innerHeight;
    // Cap canvas at 1920px wide to prevent Retina overdraw killing performance
    var maxW = Math.min(w * DPR, 1920);
    var scale = maxW / (w * DPR);
    canvas.width  = Math.round(w * DPR * scale);
    canvas.height = Math.round(h * DPR * scale);
    canvas.style.width  = w + 'px';
    canvas.style.height = h + 'px';
  }
  setSize();
  window.addEventListener('resize', function() { setSize(); if(bitmaps[playHead]) draw(playHead); }, { passive: true });

  var bitmaps  = new Array(TOTAL).fill(null);
  var loaded   = 0;
  var ready    = false;
  var playHead = 0;
  var isTyping = false;
  var typingTimer;

  var loadBar = document.getElementById('reflect-load-bar');
  var loadPct = document.getElementById('reflect-load-pct');
  var overlay = document.getElementById('reflect-load-overlay');

  function draw(idx) {
    var i = ((idx % TOTAL) + TOTAL) % TOTAL;
    var bmp = bitmaps[i];
    if (!bmp) return;
    // Cover fill
    var sw = canvas.width, sh = canvas.height;
    var scale = Math.max(sw / bmp.width, sh / bmp.height);
    var dw = bmp.width * scale, dh = bmp.height * scale;
    ctx.drawImage(bmp, (sw - dw) / 2, (sh - dh) / 2, dw, dh);
    playHead = i;
  }

  // Fixed-interval RAF — avoids drift
  var interval = 1000 / FPS;
  var lastTs   = 0;
  function loop(ts) {
    requestAnimationFrame(loop);
    if (!ready || isTyping) return;
    var elapsed = ts - lastTs;
    if (elapsed < interval) return;
    // Use fixed steps to avoid drift
    lastTs = ts - (elapsed % interval);
    draw((playHead + 1) % TOTAL);
  }
  requestAnimationFrame(loop);

  // Pause while typing
  inputEl.addEventListener('input', function() {
    isTyping = true;
    clearTimeout(typingTimer);
    typingTimer = setTimeout(function() { isTyping = false; }, 1200);
  });
  inputEl.addEventListener('blur', function() {
    clearTimeout(typingTimer);
    isTyping = false;
  });

  // Load frames — large chunks in parallel
  var inFlight = 0;
  var MAX_STREAMS = 6;

  function loadChunk(start) {
    if (start >= TOTAL) return;
    var end = Math.min(start + CHUNK, TOTAL);
    inFlight++;
    var pending = end - start;
    for (var i = start; i < end; i++) {
      (function(idx) {
        var img = new Image();
        img.src = BASE + 'f' + String(idx + 1).padStart(4, '0') + '.jpg';
        img.onload = function() {
          createImageBitmap(img, { resizeWidth: 1280, resizeHeight: 720, resizeQuality: 'medium' }).then(function(bmp) {
            bitmaps[idx] = bmp;
            loaded++;
            var pct = Math.round(loaded / TOTAL * 100);
            if (loadBar) loadBar.style.width = pct + '%';
            if (loadPct) loadPct.textContent = pct + '%';
            if (loaded === 1) draw(0);
            pending--;
            if (pending === 0) {
              inFlight--;
              if (loaded === TOTAL) {
                ready = true;
                if (overlay) {
                  overlay.style.transition = 'opacity 0.4s';
                  overlay.style.opacity = '0';
                  setTimeout(function() { overlay && overlay.parentNode && overlay.parentNode.removeChild(overlay); }, 400);
                }
              }
            }
          });
        };
        img.onerror = function() {
          loaded++; pending--;
          if (pending === 0) { inFlight--; if (loaded === TOTAL) { ready = true; overlay && overlay.parentNode && overlay.parentNode.removeChild(overlay); } }
        };
      })(i);
    }
  }

  // 6 parallel streams
  for (var s = 0; s < MAX_STREAMS; s++) {
    loadChunk(s * CHUNK);
  }

})();
