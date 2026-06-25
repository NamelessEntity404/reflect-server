// Reflect background player — plays always, pauses only when typing

(function() {
  var TOTAL  = 300;
  var FPS    = 25;
  var CHUNK  = 16;
  var BASE   = '/_frames_reflect/';

  var canvas  = document.getElementById('bg-canvas');
  var ctx     = canvas.getContext('2d', { alpha: false });
  var inputEl = document.getElementById('user-input');

  function setSize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  setSize();
  window.addEventListener('resize', function() { setSize(); draw(playHead); }, { passive: true });

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
    var i = ((Math.round(idx) % TOTAL) + TOTAL) % TOTAL;
    var bmp = bitmaps[i];
    if (!bmp) return;
    var scale = Math.max(canvas.width / bmp.width, canvas.height / bmp.height);
    var dw = bmp.width * scale, dh = bmp.height * scale;
    ctx.drawImage(bmp, (canvas.width - dw) / 2, (canvas.height - dh) / 2, dw, dh);
    playHead = i;
  }

  // Loop — always plays, stops only when typing
  var lastTs = 0;
  function loop(ts) {
    requestAnimationFrame(loop);
    if (!ready || isTyping) return;
    if (ts - lastTs < 1000 / FPS) return;
    lastTs = ts;
    draw((playHead + 1) % TOTAL);
  }
  requestAnimationFrame(loop);

  // Only rule: pause while typing
  inputEl.addEventListener('input', function() {
    isTyping = true;
    clearTimeout(typingTimer);
    typingTimer = setTimeout(function() { isTyping = false; }, 1200);
  });
  inputEl.addEventListener('blur', function() {
    clearTimeout(typingTimer);
    isTyping = false;
  });

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
            var pct = Math.round(loaded / TOTAL * 100);
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
