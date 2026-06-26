// SGI Section Carousels
// Each section of content = its own horizontal swipeable carousel
// Scroll UP/DOWN between sections, swipe LEFT/RIGHT within each section

(function() {
  'use strict';

  var EASE = 'transform 0.5s cubic-bezier(0.16,1,0.3,1), opacity 0.5s ease';

  function makeCarousel(cards, cardWidth) {
    if (!cards || cards.length === 0) return;
    var current = 0;

    // Wrap all cards in a carousel shell
    var parent = cards[0].parentNode;
    var shell = document.createElement('div');
    shell.className = 'sgi-carousel';
    shell.style.cssText = [
      'position:relative',
      'width:100%',
      'height:' + (cardWidth ? Math.round(cardWidth * 1.3) : 480) + 'px',
      'perspective:1100px',
      'perspective-origin:50% 50%',
      'overflow:visible',
    ].join(';');

    // Move cards into shell
    cards.forEach(function(c) { shell.appendChild(c); });
    parent.appendChild(shell);

    function getStyle(offset) {
      var abs = Math.abs(offset);
      var sign = offset > 0 ? 1 : -1;
      if (abs === 0) return { x:0,        z:0,    ry:0,          s:1,    o:1,    zi:20, pe:'all' };
      if (abs === 1) return { x:sign*52,   z:-70,  ry:sign*-12,   s:0.87, o:0.7,  zi:10, pe:'all' };
      if (abs === 2) return { x:sign*85,   z:-140, ry:sign*-22,   s:0.74, o:0.4,  zi:5,  pe:'all' };
      return               { x:sign*108,  z:-210, ry:sign*-30,   s:0.62, o:0.12, zi:1,  pe:'none' };
    }

    function render() {
      cards.forEach(function(card, i) {
        var p = getStyle(i - current);
        var w = card.offsetWidth || 380;
        var h = card.offsetHeight || 420;
        card.style.cssText += [
          ';position:absolute',
          'left:50%',
          'top:50%',
          'margin-left:-' + Math.round(w/2) + 'px',
          'margin-top:-' + Math.round(h/2) + 'px',
          'transform:translateX(' + p.x + '%) translateZ(' + p.z + 'px) rotateY(' + p.ry + 'deg) scale(' + p.s + ')',
          'opacity:' + p.o,
          'z-index:' + p.zi,
          'pointer-events:' + p.pe,
          'cursor:' + (Math.abs(i-current)>0 ? 'pointer' : 'default'),
          'transition:' + EASE,
        ].join(';');
      });
      updateDots();
    }

    function goTo(idx) {
      current = Math.max(0, Math.min(cards.length - 1, idx));
      render();
    }

    // Click side card = bring it forward; click front card = pass through (for links)
    cards.forEach(function(card, i) {
      card.addEventListener('click', function(e) {
        if (i !== current) {
          e.preventDefault();
          e.stopPropagation();
          goTo(i);
        }
      }, true);
    });

    // Touch swipe
    var tx0 = 0;
    shell.addEventListener('touchstart', function(e) { tx0 = e.touches[0].clientX; }, {passive:true});
    shell.addEventListener('touchend', function(e) {
      var dx = e.changedTouches[0].clientX - tx0;
      if (Math.abs(dx) > 50) goTo(current + (dx < 0 ? 1 : -1));
    }, {passive:true});

    // Mouse drag
    var mx0 = 0, dragging = false;
    shell.addEventListener('mousedown', function(e) { mx0 = e.clientX; dragging = true; });
    shell.addEventListener('mouseup', function(e) {
      if (!dragging) return;
      dragging = false;
      var dx = e.clientX - mx0;
      if (Math.abs(dx) > 40) goTo(current + (dx < 0 ? 1 : -1));
    });

    // Nav dots
    var dots = document.createElement('div');
    dots.style.cssText = 'position:absolute;bottom:-28px;left:50%;transform:translateX(-50%);display:flex;gap:7px;z-index:100';
    if (cards.length > 1) {
      cards.forEach(function(_, i) {
        var d = document.createElement('div');
        d.style.cssText = 'width:6px;height:6px;border-radius:50%;background:rgba(200,240,0,0.25);cursor:pointer;transition:all 0.25s';
        d.addEventListener('click', function() { goTo(i); });
        dots.appendChild(d);
      });
      shell.appendChild(dots);
    }

    function updateDots() {
      Array.from(dots.children).forEach(function(d, i) {
        d.style.background = i === current ? '#C8F000' : 'rgba(200,240,0,0.25)';
        d.style.transform  = i === current ? 'scale(1.5)' : 'scale(1)';
      });
    }

    // Arrow nav buttons
    if (cards.length > 1) {
      ['←','→'].forEach(function(arrow, dir) {
        var btn = document.createElement('button');
        btn.textContent = arrow;
        btn.style.cssText = [
          'position:absolute',
          dir === 0 ? 'left:8px' : 'right:8px',
          'top:50%',
          'transform:translateY(-50%)',
          'z-index:100',
          'background:rgba(200,240,0,0.08)',
          'border:0.5px solid rgba(200,240,0,0.25)',
          'color:rgba(200,240,0,0.7)',
          'font-size:18px',
          'width:36px',
          'height:36px',
          'border-radius:50%',
          'cursor:pointer',
          'display:flex',
          'align-items:center',
          'justify-content:center',
          'transition:background 0.2s',
        ].join(';');
        btn.addEventListener('click', function() { goTo(current + (dir === 0 ? -1 : 1)); });
        shell.appendChild(btn);
      });
    }

    // Initial draw (no animation)
    cards.forEach(function(c) { c.style.transition = 'none'; });
    requestAnimationFrame(function() { render(); });
  }

  function setup() {
    // ── ABOUT PAGE: about-grid ──────────────────────────────────────────────
    var aboutGrid = document.querySelector('.about-grid');
    if (aboutGrid) {
      var aboutCards = Array.from(aboutGrid.querySelectorAll('.about-card'));
      if (aboutCards.length > 1) makeCarousel(aboutCards, 340);
    }

    // ── RESEARCH PAGE: each grid-section separately ─────────────────────────
    // Group paper-cards by their section label
    var gridSections = document.querySelectorAll('.grid-section');
    gridSections.forEach(function(section) {
      var cards = Array.from(section.querySelectorAll('.paper-card'));
      if (cards.length > 1) makeCarousel(cards, 460);
    });

    // Fallback: if no grid-section, try the whole .grid
    if (!gridSections.length) {
      var grid = document.querySelector('.grid');
      if (grid) {
        var pCards = Array.from(grid.querySelectorAll('.paper-card'));
        if (pCards.length > 1) makeCarousel(pCards, 460);
      }
    }

    // ── SUBPAGES: any .pipe-step groups, .guardrail groups ──────────────────
    var pipeGroups = document.querySelectorAll('.pipeline, .guardrail-grid, .stat-row');
    pipeGroups.forEach(function(group) {
      var items = Array.from(group.children).filter(function(el) {
        return el.tagName !== 'STYLE' && el.tagName !== 'SCRIPT';
      });
      if (items.length > 2) makeCarousel(items, 260);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setTimeout(setup, 100);
  }

})();
