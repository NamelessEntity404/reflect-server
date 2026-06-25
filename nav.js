(() => {
  const current = window.location.pathname.split('/').pop() || 'index.html';
  const links = [
    { href: 'work.html', label: 'Work' },
    { href: 'research.html', label: 'Research' },
    { href: 'about.html', label: 'About' },
  ];

  const nav = document.createElement('nav');
  nav.style.cssText = [
    'position:fixed', 'top:0', 'left:0', 'right:0', 'z-index:99999',
    'display:flex', 'align-items:center', 'justify-content:space-between',
    'padding:0 32px', 'height:56px',
    'background:rgba(5,6,10,0.92)',
    'backdrop-filter:blur(20px)',
    '-webkit-backdrop-filter:blur(20px)',
    'border-bottom:0.5px solid rgba(200,240,0,0.12)',
    'transform:none',
    'transition:none',
    'border-radius:0',
    'max-width:none',
    'flex-wrap:nowrap',
    'gap:0',
    'justify-content:space-between',
  ].join(';');

  const logo = document.createElement('a');
  logo.href = 'index.html';
  logo.innerHTML = 'SHANE <span style="color:#C8F000;background:none;border:none;padding:0;border-radius:0;">GRAFFITI</span> INC.';
  logo.style.cssText = "font-family:'Barlow Condensed',sans-serif;font-size:20px;font-weight:900;letter-spacing:0.04em;text-transform:uppercase;color:#F5F2E8;text-decoration:none;line-height:1;background:none;border:none;padding:0;border-radius:0;box-shadow:none;white-space:nowrap;flex-shrink:0;";

  const linkWrap = document.createElement('div');
  linkWrap.style.cssText = 'display:flex;align-items:center;gap:32px;margin-left:auto;padding-left:32px;';

  links.forEach(({ href, label }) => {
    const a = document.createElement('a');
    a.href = href;
    a.textContent = label;
    const active = href === current;
    a.style.cssText = `font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:${active ? '#C8F000' : '#A8A89A'};text-decoration:none;background:none;border:none;padding:0;border-radius:0;box-shadow:none;`;
    linkWrap.appendChild(a);
  });

  const reflect = document.createElement('a');
  reflect.href = 'therapy-chat.html';
  reflect.textContent = 'Reflect';
  reflect.style.cssText = "font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:#05060a;background:#C8F000;padding:6px 14px;border-radius:3px;text-decoration:none;";
  linkWrap.appendChild(reflect);

  nav.appendChild(logo);
  nav.appendChild(linkWrap);

  // Hide any legacy page-nav elements
  document.querySelectorAll('nav:not(#sgi-nav)').forEach(el => el.style.display = 'none');

  nav.id = 'sgi-nav';

  // Portfolio pages use scroll-driven WebGL — padding breaks the animation
  const isPortfolio = /^(index|page\d+)\.html$/.test(current);
  if (!isPortfolio) {
    document.body.style.paddingTop = '56px';
  }

  document.body.insertBefore(nav, document.body.firstChild);
})();
