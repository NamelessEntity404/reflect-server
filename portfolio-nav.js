(() => {
  const pages = [
    'index.html','page2.html','page3.html','page4.html','page5.html',
    'page6.html','page7.html','page8.html','page9.html','page10.html',
    'page11.html','page12.html','page13.html','page14.html','page15.html','page16.html'
  ];
  const titles = [
    'Holograph','Round Holograph','Futuristic Spaceship','Future Technology',
    'Platform Floating','Cyberpunk Slideshow','Main Sequence','Render Composition',
    'Test Sequence','Futuristic Slideshow','Game Carousels','Game HUD',
    'Holograph — Product Designer','Sci-Fi City','Scifi Energy Logo','The Big Final'
  ];

  const current = window.location.pathname.split('/').pop() || 'index.html';
  const idx = pages.indexOf(current);
  if (idx === -1) return;

  const prev = idx > 0 ? pages[idx - 1] : null;
  const next = idx < pages.length - 1 ? pages[idx + 1] : null;

  const bar = document.createElement('div');
  bar.style.cssText = [
    'position:fixed','bottom:0','left:0','right:0','z-index:99998',
    'display:flex','align-items:center','justify-content:space-between',
    'padding:0 24px','height:48px',
    'background:rgba(5,6,10,0.88)',
    'backdrop-filter:blur(20px)',
    '-webkit-backdrop-filter:blur(20px)',
    'border-top:0.5px solid rgba(200,240,0,0.12)',
  ].join(';');

  const linkStyle = "font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:0.12em;text-transform:uppercase;text-decoration:none;padding:6px 14px;border-radius:3px;transition:background 0.2s;";

  const prevEl = document.createElement('a');
  prevEl.href = prev || 'work.html';
  prevEl.textContent = prev ? '← Prev' : '← All Work';
  prevEl.style.cssText = linkStyle + 'color:#A8A89A;border:0.5px solid rgba(168,168,154,0.2);';
  prevEl.onmouseover = () => prevEl.style.color = '#C8F000';
  prevEl.onmouseout  = () => prevEl.style.color = '#A8A89A';

  const counter = document.createElement('span');
  counter.style.cssText = "font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:rgba(168,168,154,0.5);";
  counter.textContent = `${String(idx + 1).padStart(2,'0')} / ${pages.length}  —  ${titles[idx]}`;

  const nextEl = document.createElement('a');
  nextEl.href = next || 'work.html';
  nextEl.textContent = next ? 'Next →' : 'All Work →';
  nextEl.style.cssText = linkStyle + 'color:#05060a;background:#C8F000;';
  nextEl.onmouseover = () => nextEl.style.opacity = '0.85';
  nextEl.onmouseout  = () => nextEl.style.opacity = '1';

  bar.appendChild(prevEl);
  bar.appendChild(counter);
  bar.appendChild(nextEl);
  document.body.appendChild(bar);

  // Add bottom padding so scroll hint isn't hidden behind bar
  document.body.style.paddingBottom = '48px';
})();
