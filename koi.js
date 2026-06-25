/* ============================================================
   KOI POND — CSS segment fish + WebGL water
   Matches @thedesignely reference exactly
============================================================ */
(function () {
  'use strict';

  /* ── HIDE CURSOR ───────────────────────────────────────────── */
  document.documentElement.style.cursor = 'auto';

  /* ── VIDEO CURSOR ──────────────────────────────────────────── */
  const vidCursor = document.createElement('video');
  vidCursor.src        = './_cursor/cursor_trimmed.mp4';
  vidCursor.loop       = true;
  vidCursor.muted      = true;
  vidCursor.playsInline = true;
  vidCursor.autoplay   = true;
  const SIZE = 320; // px — tweak this to make it bigger/smaller
  Object.assign(vidCursor.style, {
    position:     'fixed',
    width:        SIZE + 'px',
    height:       SIZE + 'px',
    objectFit:    'cover',
    pointerEvents:'none',
    zIndex:       '2147483647',
    mixBlendMode: 'screen',   // black = transparent, effect stacks on top
    transform:    'translate(-50%, -50%)',
    top:          '0px',
    left:         '0px',
    willChange:   'transform',
    borderRadius: '50%',      // circular crop keeps it clean
  });
  document.body.appendChild(vidCursor);
  vidCursor.play().catch(() => {});

  window.addEventListener('mousemove', e => {
    vidCursor.style.top  = e.clientY + 'px';
    vidCursor.style.left = e.clientX + 'px';
  });

  /* ── STYLES ────────────────────────────────────────────────── */
  const S = document.createElement('style');
  S.textContent = `
    * { cursor: auto !important; }

    #pond-bg {
      position: fixed; inset: 0; z-index: 0;
      background: linear-gradient(160deg,
        #35c5f0 0%, #18a8dc 25%,
        #0d90c8 60%, #0a7ab0 100%
      );
    }

    #pond-webgl {
      position: absolute; inset: 0;
      width: 100%; height: 100%;
      mix-blend-mode: soft-light;
      opacity: 0.55;
    }

    #pond-canvas {
      position: fixed; inset: 0;
      width: 100vw; height: 100vh;
      pointer-events: none;
      z-index: 2;
    }

    .koi-fish {
      position: fixed;
      top: 0; left: 0;
      pointer-events: none;
      z-index: 3;
      filter: drop-shadow(0 8px 18px rgba(0,0,0,0.35));
      will-change: transform;
    }

    .koi-cell {
      position: absolute;
      top: 0; left: 0;
      border-radius: 50%;
      will-change: transform;
      transform-origin: center center;
    }

    /* Page content sits above water, below fish */
    body > *:not(#pond-bg):not(#pond-canvas):not(.koi-fish):not(style):not(script) {
      position: relative;
      z-index: 4;
    }
  `;
  document.head.appendChild(S);

  /* ── DOM ───────────────────────────────────────────────────── */
  const bg   = document.createElement('div');   bg.id = 'pond-bg';
  const glCv = document.createElement('canvas'); glCv.id = 'pond-webgl';
  const cv   = document.createElement('canvas'); cv.id  = 'pond-canvas';

  bg.appendChild(glCv);
  document.body.prepend(bg);
  document.body.appendChild(cv);

  const ctx = cv.getContext('2d');
  const DPR = Math.min(devicePixelRatio || 1, 2);

  function resize() {
    cv.width  = innerWidth  * DPR; cv.style.width  = innerWidth  + 'px';
    cv.height = innerHeight * DPR; cv.style.height = innerHeight + 'px';
    ctx.scale(DPR, DPR);
    glCv.width  = innerWidth;
    glCv.height = innerHeight;
    if (gl) gl.viewport(0, 0, glCv.width, glCv.height);
  }

  /* ── WEBGL CAUSTICS (bright, daylight-pool look) ────────────── */
  const gl = glCv.getContext('webgl', { alpha: true, premultipliedAlpha: false });
  let uTime, renderGL;

  if (gl) {
    const vs = `attribute vec2 p; void main(){gl_Position=vec4(p,0,1);}`;
    const fs = `
      precision highp float;
      uniform float t;
      uniform vec2  r;

      float caustic(vec2 uv, float tt) {
        float v = 0.0;
        for(int i=0;i<6;i++){
          float f = float(i);
          vec2 q = uv * (1.0 + f*0.15) + vec2(
            sin(tt*0.6+f*1.1)*0.35,
            cos(tt*0.5+f*0.8)*0.35
          );
          v += sin(q.x*8.0+tt)*cos(q.y*8.0-tt*0.7);
        }
        return clamp(v/6.0 + 0.5, 0.0, 1.0);
      }

      void main(){
        vec2 uv = gl_FragCoord.xy / r;
        uv.x   *= r.x/r.y;
        float c = caustic(uv, t);
        float b = pow(c, 1.8);
        vec3 col = mix(
          vec3(0.2, 0.65, 0.95),
          vec3(0.9, 0.97, 1.0),
          b * 0.6
        );
        gl_FragColor = vec4(col, b * 0.6);
      }
    `;
    function sh(type, src) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src); gl.compileShader(s); return s;
    }
    const prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER,   vs));
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(prog); gl.useProgram(prog);
    const vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
    const pLoc = gl.getAttribLocation(prog, 'p');
    gl.enableVertexAttribArray(pLoc);
    gl.vertexAttribPointer(pLoc, 2, gl.FLOAT, false, 0, 0);
    uTime = gl.getUniformLocation(prog, 't');
    const uRes = gl.getUniformLocation(prog, 'r');
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.uniform2f(uRes, glCv.width, glCv.height);
    renderGL = (t) => {
      gl.uniform1f(uTime, t);
      gl.uniform2f(uRes, glCv.width, glCv.height);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    };
  }

  resize();
  window.addEventListener('resize', resize);

  /* ── MOUSE ─────────────────────────────────────────────────── */
  let mx = innerWidth * 0.4, my = innerHeight * 0.5;
  window.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });

  /* ── RIPPLES ────────────────────────────────────────────────── */
  const ripples = [];
  let lastRx = -999, lastRy = -999;

  function addRipple(x, y, scale = 1) {
    const count = scale > 1 ? 4 : 1;
    for (let i = 0; i < count; i++)
      ripples.push({ x, y, r: i * 28, life: 1 - i * 0.18, speed: 1.8 + i * 0.4, thick: scale > 1 ? 2.2 : 1.4 });
  }
  window.addEventListener('click', e => addRipple(e.clientX, e.clientY, 2));

  /* ── KOI FISH CLASS (CSS segments) ─────────────────────────── */
  const CELLS   = 15;
  const SEG_LEN = 13;

  // Koi color patterns — [head→tail segment colors]
  const PATTERNS = [
    // Orange-red koi with white patches (like reference)
    (i) => {
      const t = i / (CELLS - 1);
      if (i <= 1)  return { bg: '#cc2200', border: '#991800' };  // red head
      if (i === 3 || i === 4)  return { bg: '#f5f0ee', border: '#ddd5d0' }; // white
      if (i >= 5 && i <= 9)  return { bg: '#dd2800', border: '#aa1500' };  // red body
      if (i === 10 || i === 11) return { bg: '#f8f3f0', border: '#e0d8d4' }; // white
      if (i >= 12) return { bg: `rgba(200,40,10,${1 - (i-12)*0.25})`, border: 'transparent' }; // tail fade
      return { bg: '#dd2800', border: '#aa1500' };
    },
    // White koi with red patches (mirrored / second fish)
    (i) => {
      if (i <= 2)  return { bg: '#f0ece8', border: '#d8d0cc' };  // white head
      if (i === 3) return { bg: '#cc2200', border: '#991800' };  // red spot
      if (i >= 4 && i <= 6) return { bg: '#f4efec', border: '#ddd5d0' }; // white
      if (i === 7 || i === 8) return { bg: '#cc2000', border: '#991500' }; // red
      if (i >= 9 && i <= 11) return { bg: '#f2eee9', border: '#dbd3ce' }; // white
      if (i >= 12) return { bg: `rgba(240,230,220,${1-(i-12)*0.28})`, border: 'transparent' };
      return { bg: '#f0ece8', border: '#d8d0cc' };
    },
  ];

  function bodyWidth(i) {
    const t = i / (CELLS - 1);
    // Torpedo: narrow head, wide middle, narrow tail
    const base = Math.sin(Math.pow(t, 0.6) * Math.PI);
    return Math.max(3, 46 * base * (1 - t * 0.45));
  }

  class KoiFish {
    constructor(patternIdx, autonomous) {
      this.autonomous = autonomous;
      this.pattern    = PATTERNS[patternIdx];

      // DOM
      this.wrap = document.createElement('div');
      this.wrap.className = 'koi-fish';
      this.cellEls = [];

      for (let i = 0; i < CELLS; i++) {
        const d   = document.createElement('div');
        d.className = 'koi-cell';
        const col   = this.pattern(i);
        const w     = bodyWidth(i);
        const h     = Math.max(2, w * 0.68);
        Object.assign(d.style, {
          width:           w + 'px',
          height:          h + 'px',
          background:      col.bg,
          border:          col.border !== 'transparent' ? `1px solid ${col.border}` : 'none',
          boxShadow:       i < 3 ? 'inset 0 -2px 4px rgba(0,0,0,0.2)' : 'none',
        });
        this.wrap.appendChild(d);
        this.cellEls.push({ el: d, w, h });
      }

      document.body.appendChild(this.wrap);

      // Spine
      const sx = autonomous ? innerWidth * 0.7 : innerWidth * 0.4;
      const sy = autonomous ? innerHeight * 0.6 : innerHeight * 0.5;
      this.spine = Array.from({ length: CELLS }, () => ({ x: sx, y: sy }));
      this.hx = sx; this.hy = sy;
      this.hvx = 0; this.hvy = 0;

      // Autonomous wandering
      this.tx = sx; this.ty = sy;
      this.timer = 0;
    }

    update(mx, my) {
      let tx, ty;
      if (this.autonomous) {
        this.timer--;
        if (this.timer <= 0) {
          this.tx = 80 + Math.random() * (innerWidth  - 160);
          this.ty = 80 + Math.random() * (innerHeight - 160);
          this.timer = 140 + Math.random() * 200;
        }
        tx = this.tx; ty = this.ty;
      } else {
        tx = mx; ty = my;
      }

      const spd = this.autonomous ? 0.045 : 0.08;
      const dmp = this.autonomous ? 0.82  : 0.76;
      this.hvx += (tx - this.hx) * spd;
      this.hvy += (ty - this.hy) * spd;
      this.hvx *= dmp; this.hvy *= dmp;
      this.hx  += this.hvx; this.hy  += this.hvy;

      this.spine[0].x = this.hx;
      this.spine[0].y = this.hy;

      for (let i = 1; i < CELLS; i++) {
        const p = this.spine[i-1], c = this.spine[i];
        const dx = c.x - p.x, dy = c.y - p.y;
        const d  = Math.sqrt(dx*dx + dy*dy) || 1;
        if (d > SEG_LEN) {
          c.x = p.x + dx/d * SEG_LEN;
          c.y = p.y + dy/d * SEG_LEN;
        }
      }
    }

    render() {
      for (let i = 0; i < CELLS; i++) {
        const curr  = this.spine[i];
        const next  = this.spine[Math.min(i+1, CELLS-1)];
        const angle = Math.atan2(next.y - curr.y, next.x - curr.x);
        const { el, w, h } = this.cellEls[i];
        el.style.transform = `translate(${curr.x - w/2}px,${curr.y - h/2}px) rotate(${angle}rad)`;
      }
    }

    // Returns head position for ripple spawning
    get head() { return this.spine[0]; }
    get speed() { return Math.sqrt(this.hvx*this.hvx + this.hvy*this.hvy); }
  }

  /* ── CREATE FISH ────────────────────────────────────────────── */
  const fish1 = new KoiFish(0, false); // cursor-following, red
  const fish2 = new KoiFish(1, true);  // autonomous, white

  /* ── RIPPLE FROM FISH MOVEMENT ──────────────────────────────── */
  let f1LastRx = -999, f1LastRy = -999;
  let f2LastRx = -999, f2LastRy = -999;

  function maybeRippleFromFish(fish, lx, ly) {
    const dx = fish.head.x - lx, dy = fish.head.y - ly;
    if (dx*dx + dy*dy > 1400 && fish.speed > 0.8) {
      addRipple(fish.head.x, fish.head.y, 1);
      return [fish.head.x, fish.head.y];
    }
    return [lx, ly];
  }

  /* ── DRAW RIPPLES ───────────────────────────────────────────── */
  function drawRipples() {
    ctx.save();
    for (let i = ripples.length-1; i >= 0; i--) {
      const rp = ripples[i];
      rp.r    += rp.speed;
      rp.life -= 0.016;
      if (rp.life <= 0) { ripples.splice(i,1); continue; }

      // Main ring
      ctx.beginPath();
      ctx.arc(rp.x, rp.y, rp.r, 0, Math.PI*2);
      ctx.strokeStyle = `rgba(255,255,255,${rp.life * 0.45})`;
      ctx.lineWidth   = rp.thick * rp.life;
      ctx.stroke();

      // Inner shimmer
      if (rp.r > 12) {
        ctx.beginPath();
        ctx.arc(rp.x, rp.y, rp.r * 0.72, 0, Math.PI*2);
        ctx.strokeStyle = `rgba(255,255,255,${rp.life * 0.2})`;
        ctx.lineWidth   = rp.thick * 0.5 * rp.life;
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  /* ── DRAW FISH SHADOWS ──────────────────────────────────────── */
  function drawFishShadow(fish) {
    const h = fish.spine[3];
    if (!h) return;
    ctx.save();
    ctx.globalAlpha = 0.18;
    ctx.filter = 'blur(10px)';
    const g = ctx.createRadialGradient(h.x+8, h.y+12, 0, h.x+8, h.y+12, 55);
    g.addColorStop(0,   'rgba(0,30,80,0.8)');
    g.addColorStop(1,   'rgba(0,0,0,0)');
    ctx.beginPath();
    ctx.ellipse(h.x+8, h.y+12, 55, 22, Math.atan2(
      fish.spine[1]?.y - fish.spine[0]?.y || 0,
      fish.spine[1]?.x - fish.spine[0]?.x || 1
    ), 0, Math.PI*2);
    ctx.fillStyle = g;
    ctx.fill();
    ctx.restore();
  }

  /* ── MOUSE RIPPLE ───────────────────────────────────────────── */
  function maybeMouse() {
    const dx = mx-lastRx, dy = my-lastRy;
    if (dx*dx+dy*dy > 900) { addRipple(mx,my,1); lastRx=mx; lastRy=my; }
  }

  /* ── MAIN LOOP ──────────────────────────────────────────────── */
  const T0 = performance.now();

  function loop() {
    requestAnimationFrame(loop);
    const t = (performance.now() - T0) * 0.001;

    // Caustics
    if (renderGL) renderGL(t * 0.4);

    // Canvas clear
    ctx.clearRect(0, 0, innerWidth, innerHeight);

    // Update fish
    fish1.update(mx, my);
    fish2.update(mx, my);

    // Ripples from fish movement
    [f1LastRx, f1LastRy] = maybeRippleFromFish(fish1, f1LastRx, f1LastRy);
    [f2LastRx, f2LastRy] = maybeRippleFromFish(fish2, f2LastRx, f2LastRy);
    maybeMouse();

    // Draw
    drawFishShadow(fish1);
    drawFishShadow(fish2);
    drawRipples();

    // Render CSS cells
    fish1.render();
    fish2.render();
  }

  loop();
})();
