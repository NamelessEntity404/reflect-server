// SGI Carousel — 3D perspective card rotation, Tinder/Envato style
// Works on any set of cards in a container

(function() {
  'use strict';

  function initCarousel(container, cards) {
    if (!container || cards.length < 2) return;

    let current = 0;
    let touchStartX = 0;

    // Container setup
    container.style.cssText += ';position:relative;perspective:1200px;perspective-origin:50% 45%;overflow:visible;';

    function pos(offset) {
      const abs = Math.abs(offset);
      const sign = offset > 0 ? 1 : -1;
      if (abs === 0) return { x:0, z:0, ry:0, s:1, o:1, zi:20, pe:'all' };
      if (abs === 1) return { x:sign*55+'%', z:-90, ry:sign*-14, s:0.88, o:0.72, zi:10, pe:'all' };
      if (abs === 2) return { x:sign*90+'%', z:-180, ry:sign*-24, s:0.76, o:0.42, zi:5, pe:'all' };
      return          { x:sign*115+'%', z:-260, ry:sign*-32, s:0.64, o:0.15, zi:1, pe:'none' };
    }

    function render(animated) {
      cards.forEach(function(card, i) {
        const p = pos(i - current);
        const tr = 'translateX('+p.x+') translateZ('+p.z+'px) rotateY('+p.ry+'deg) scale('+p.s+')';
        card.style.position = 'absolute';
        card.style.left = '50%';
        card.style.top = '50%';
        card.style.marginLeft = '-' + (card.offsetWidth/2) + 'px';
        card.style.marginTop  = '-' + (card.offsetHeight/2) + 'px';
        card.style.transform  = tr;
        card.style.opacity    = p.o;
        card.style.zIndex     = p.zi;
        card.style.pointerEvents = p.pe;
        card.style.cursor     = Math.abs(i-current) > 0 ? 'pointer' : '';
        if (animated !== false) {
          card.style.transition = 'transform 0.55s cubic-bezier(0.16,1,0.3,1), opacity 0.55s ease';
        } else {
          card.style.transition = 'none';
        }
      });
    }

    function goTo(idx) {
      current = Math.max(0, Math.min(cards.length - 1, idx));
      render();
    }

    // Click: side card → bring forward; front card → follow href if it's a link
    cards.forEach(function(card, i) {
      card.addEventListener('click', function(e) {
        if (i !== current) {
          e.preventDefault();
          e.stopPropagation();
          goTo(i);
        }
        // If already current, let clicks through normally (link navigation etc)
      }, true);
    });

    // Swipe
    container.addEventListener('touchstart', function(e) {
      touchStartX = e.touches[0].clientX;
    }, { passive: true });
    container.addEventListener('touchend', function(e) {
      const dx = e.changedTouches[0].clientX - touchStartX;
      if (Math.abs(dx) > 50) goTo(current + (dx < 0 ? 1 : -1));
    }, { passive: true });

    // Arrow keys (only when container is focused or no input focused)
    document.addEventListener('keydown', function(e) {
      if (document.activeElement && document.activeElement.tagName === 'INPUT') return;
      if (document.activeElement && document.activeElement.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowRight') goTo(current + 1);
      if (e.key === 'ArrowLeft')  goTo(current - 1);
    });

    // Nav dots
    var dotsWrap = document.createElement('div');
    dotsWrap.style.cssText = 'position:absolute;bottom:-32px;left:50%;transform:translateX(-50%);display:flex;gap:6px;z-index:50;';
    cards.forEach(function(_, i) {
      var dot = document.createElement('div');
      dot.style.cssText = 'width:6px;height:6px;border-radius:50%;background:rgba(200,240,0,0.3);cursor:pointer;transition:background 0.2s,transform 0.2s;';
      dot.addEventListener('click', function() { goTo(i); });
      dotsWrap.appendChild(dot);
    });
    container.appendChild(dotsWrap);

    function updateDots() {
      Array.from(dotsWrap.children).forEach(function(d, i) {
        d.style.background = i === current ? '#C8F000' : 'rgba(200,240,0,0.25)';
        d.style.transform  = i === current ? 'scale(1.4)' : 'scale(1)';
      });
    }

    var origGoTo = goTo;
    goTo = function(idx) { origGoTo(idx); updateDots(); };

    // Initial render without animation
    render(false);
    // Then animate in after a frame
    requestAnimationFrame(function() { render(); updateDots(); });
  }

  // ── AUTO-DETECT AND INIT ────────────────────────────────────────────────

  function setup() {
    // About page cards
    var aboutGrid = document.querySelector('.about-grid');
    if (aboutGrid) {
      var aboutCards = Array.from(aboutGrid.querySelectorAll('.about-card'));
      if (aboutCards.length) {
        aboutGrid.style.cssText += ';min-height:420px;';
        initCarousel(aboutGrid, aboutCards);
      }
    }

    // Research page paper-cards
    var grid = document.querySelector('.grid');
    if (grid) {
      var paperCards = Array.from(grid.querySelectorAll('.paper-card'));
      if (paperCards.length) {
        grid.style.cssText += ';min-height:520px;';
        initCarousel(grid, paperCards);
      }
    }

    // Perspective chat card-pairs
    var msgs = document.getElementById('messages');
    if (msgs && typeof pairs !== 'undefined') {
      // Already handled by therapy-chat's own pair system
      // Enhance existing pair animations
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }

})();
