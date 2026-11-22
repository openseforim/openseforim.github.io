/* Open Seforim shared header strip, theme control and footer. v1.
   Each reader page loads it with: <script src="/assets/os.js" defer></script>
   The work's metadata comes from /<slug>/work.json. */
(function () {
  // short work titles, written by build.py from the works' work.json (no flash of the slug)
  var TITLES = /*TITLES*/{"emden": "Megillat Sefer", "immanuel": "Maḥberot", "meor-einayim": "Me'or Einayim", "hyman": "Toldot Tannaim ve-Amoraim", "bochart": "Hierozoicon", "lewysohn": "Zoologie des Talmuds", "loew": "Flora der Juden", "barhebraeus": "Chronography", "defus": "Defus"}/*END*/;
  var KEY = 'os-theme';
  var OLD_KEYS = ['ms-theme', 'me-theme', 'bh-theme', 'lz-theme'];
  var root = document.documentElement;

  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // one theme for all works; take over an old per-work choice once
  var theme = get(KEY);
  if (theme === null) {
    for (var i = 0; i < OLD_KEYS.length; i++) { var o = get(OLD_KEYS[i]); if (o) { theme = o; break; } }
  }
  theme = theme || 'auto';
  function apply(v) {
    // a site with its own palette (Defus) has no paper colours: show it light
    if (v === 'paper' && root.classList.contains('os-own-palette')) v = 'light';
    if (!v || v === 'auto') root.removeAttribute('data-theme'); else root.setAttribute('data-theme', v);
  }
  apply(theme);

  var slug = location.pathname.split('/').filter(Boolean)[0] || '';
  var base = slug ? '/' + slug + '/' : '/';

  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text) e.textContent = text;
    return e;
  }

  // ---- strip ----
  var strip = el('div', { 'class': 'os-strip', role: 'navigation', 'aria-label': 'Open Seforim' });
  var inner = el('div', { 'class': 'os-strip-in' });
  inner.appendChild(el('a', { 'class': 'os-home', href: '/' }, 'Open Seforim'));
  var workLink = null;
  if (slug) {
    inner.appendChild(el('span', { 'class': 'os-sep', 'aria-hidden': 'true' }, '/'));
    workLink = el('a', { href: base, 'class': 'os-work' }, TITLES[slug] || slug);
    inner.appendChild(workLink);
  }
  inner.appendChild(el('span', { 'class': 'os-sp' }));
  inner.appendChild(el('a', { href: '/#works' }, 'All works'));
  inner.appendChild(el('a', { href: '/about/', 'class': 'os-about' }, 'About'));
  var sel = el('select', { 'aria-label': 'Colour theme', title: 'Colour theme (all works)' });
  [['auto', 'Auto'], ['light', 'Light'], ['paper', 'Paper'], ['dark', 'Dark']].forEach(function (o) {
    var op = el('option', { value: o[0] }, o[1]); sel.appendChild(op);
  });
  sel.value = theme === '' ? 'auto' : theme;
  sel.addEventListener('change', function () { set(KEY, sel.value); apply(sel.value); });
  inner.appendChild(sel);
  strip.appendChild(inner);
  document.body.insertBefore(strip, document.body.firstChild);

  // hide the readers' own theme selects (the strip replaces them)
  var own = document.querySelectorAll('select#theme');
  for (var j = 0; j < own.length; j++) {
    var s = own[j], wrap = s.closest('label') || s;
    wrap.classList.add('os-hidden');
  }

  // ---- footer from work.json ----
  if (!slug) return;
  fetch(base + 'work.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; })
    .then(function (w) { if (w) footer(w); }).catch(function () {});

  function a(href, text) { var x = el('a', { href: href }, text); if (/^https?:/.test(href)) x.rel = 'noopener'; return x; }
  function para(parts) {
    var p = el('p');
    parts.forEach(function (x) { p.appendChild(typeof x === 'string' ? document.createTextNode(x) : x); });
    return p;
  }

  function footer(w) {
    if (workLink && w.short_title) workLink.textContent = w.short_title;
    var f = el('footer', { 'class': 'os-foot' });
    var fi = el('div', { 'class': 'os-foot-in' });

    var c1 = el('div');
    c1.appendChild(el('h2', {}, 'This edition'));
    c1.appendChild(para([w.title + (w.status_label ? ' — ' + w.status_label + '.' : '')]));
    if (w.base_edition) {
      var be = ['Based on: ' + w.base_edition.label];
      if (w.base_edition.scan_url) { be.push(' · '); be.push(a(w.base_edition.scan_url, 'page scans')); }
      c1.appendChild(para(be));
    }
    if (w.method) c1.appendChild(para(['Method: ' + w.method]));
    fi.appendChild(c1);

    var c2 = el('div');
    c2.appendChild(el('h2', {}, 'Use and cite'));
    if (w.licence) {
      c2.appendChild(para(['Licence: ', w.licence.url ? a(w.licence.url, w.licence.name) : w.licence.name]));
    }
    var today = new Date().toISOString().slice(0, 10);
    var cite = (w.cite || (w.title + '. Open Seforim')) + '. https://openseforim.org' + base + ' (accessed ' + today + ').';
    c2.appendChild(el('p', { 'class': 'os-cite' }, cite));
    fi.appendChild(c2);

    var c3 = el('div');
    c3.appendChild(el('h2', {}, 'Source and corrections'));
    if (w.repo) {
      c3.appendChild(para([a(w.repo, 'Code, text and data on GitHub')]));
      c3.appendChild(para([a(w.repo + '/issues/new', 'Report a mistake')]));
    }
    if (w.updated) c3.appendChild(para(['Last updated: ' + w.updated]));
    fi.appendChild(c3);

    var b = el('div', { 'class': 'os-brand' });
    b.appendChild(para([a('/', 'Open Seforim'), ' — open readers for Hebrew and Judaica texts, by Ezra Brand · ',
      a('https://www.ezrabrand.com/', 'ezrabrand.com')]));
    fi.appendChild(b);

    f.appendChild(fi);
    document.body.appendChild(f);
  }
})();
