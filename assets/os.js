/* Open Seforim shared header strip, theme control and footer. v1.
   Each reader page loads it with: <script src="/assets/os.js" defer></script>
   The work's metadata comes from /<slug>/work.json. */
(function () {
  // short work titles, written by build.py from the works' work.json (no flash of the slug)
  var TITLES = /*TITLES*/{"emden": "*Megillat Sefer*", "immanuel": "*Maḥberot*", "meor-einayim": "*Me'or Einayim*", "hyman": "*Toldot Tannaim ve-Amoraim*", "bochart": "*Hierozoicon*", "lewysohn": "*Zoologie des Talmuds*", "loew": "*Flora der Juden*", "barhebraeus": "*Chronography*", "defus": "Defus"}/*END*/;
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
  if (!Object.prototype.hasOwnProperty.call(TITLES, slug)) slug = '';  // site pages such as /about/ are not works
  var base = slug ? '/' + slug + '/' : '/';

  // work.json marks book titles as *Title*: show them in italics, and drop the marks in plain text
  function escHtml(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function ital(s) { return escHtml(s).replace(/\*(.+?)\*/g, '<i>$1</i>'); }
  function plain(s) { return String(s).replace(/\*/g, ''); }

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
  // a reader with its own top bar (a.brand) already names the work: the strip does not repeat it
  var ownBar = document.querySelector('a.brand');
  if (slug && !ownBar) {
    inner.appendChild(el('span', { 'class': 'os-sep', 'aria-hidden': 'true' }, '/'));
    workLink = el('a', { href: base, 'class': 'os-work' });
    workLink.innerHTML = ital(TITLES[slug] || slug);
    inner.appendChild(workLink);
  }
  inner.appendChild(el('span', { 'class': 'os-sp' }));
  inner.appendChild(el('a', { href: '/#works' }, 'All works'));
  inner.appendChild(el('a', { href: '/about/', 'class': 'os-about' }, 'About'));
  var lab = el('label', { 'class': 'os-theme', title: 'Colour theme, for all works' });
  lab.appendChild(el('span', { 'class': 'os-theme-word' }, 'Theme'));
  var sel = el('select', { 'aria-label': 'Colour theme' });
  [['auto', 'Auto'], ['light', 'Light'], ['paper', 'Paper'], ['dark', 'Dark']].forEach(function (o) {
    var op = el('option', { value: o[0] }, o[1]); sel.appendChild(op);
  });
  sel.value = theme === '' ? 'auto' : theme;
  sel.addEventListener('change', function () { set(KEY, sel.value); apply(sel.value); });
  lab.appendChild(sel);
  inner.appendChild(lab);
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
    if (workLink && w.short_title) workLink.innerHTML = ital(w.short_title);
    var f = el('footer', { 'class': 'os-foot' });
    var fi = el('div', { 'class': 'os-foot-in' });

    var c1 = el('div');
    c1.appendChild(el('h2', {}, 'About this edition'));
    var st = el('p');
    st.innerHTML = ital(w.title);
    if (w.status_label) { st.appendChild(document.createTextNode(' ')); st.appendChild(el('span', { 'class': 'os-status' }, w.status_label)); }
    c1.appendChild(st);
    if (w.base_edition) {
      var be = ['Source text: ' + w.base_edition.label];
      if (w.base_edition.scan_url) { be.push(' · '); be.push(a(w.base_edition.scan_url, 'page scans')); }
      var r = w.base_edition.scan_rights;
      if (r) { be.push(' ('); be.push(r.url ? a(r.url, r.name) : r.name); be.push(')'); }
      c1.appendChild(para(be));
    }
    if (w.method) c1.appendChild(para(['Method: ' + w.method]));
    fi.appendChild(c1);

    var c2 = el('div');
    c2.appendChild(el('h2', {}, 'Cite and reuse'));
    var dt = new Date(), MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var today = ('0' + dt.getDate()).slice(-2) + '-' + MON[dt.getMonth()] + '-' + dt.getFullYear();
    var cite = (w.cite || (w.title + '. Open Seforim')) + '. https://openseforim.org' + base + ' (accessed ' + today + ').';
    var cp = el('p', { 'class': 'os-cite' });
    cp.innerHTML = ital(cite);
    c2.appendChild(cp);
    cite = plain(cite);
    var btn = el('button', { type: 'button', 'class': 'os-copy' }, 'Copy citation');
    btn.addEventListener('click', function () {
      var done = function () { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = 'Copy citation'; }, 1600); };
      if (navigator.clipboard) navigator.clipboard.writeText(cite).then(done, function () {});
    });
    c2.appendChild(btn);
    if (w.licence) {
      c2.appendChild(para(['Licence: ', w.licence.url ? a(w.licence.url, w.licence.name) : w.licence.name]));
    }
    fi.appendChild(c2);

    var c3 = el('div');
    c3.appendChild(el('h2', {}, 'Corrections'));
    if (w.repo) {
      c3.appendChild(para(['Found a misreading or a wrong translation? ', a(w.repo + '/issues/new', 'Report a mistake'), '.']));
      c3.appendChild(para([a(w.repo, 'Code and data'), ' on GitHub']));
    }
    fi.appendChild(c3);

    var b = el('div', { 'class': 'os-brand' });
    b.appendChild(para([a('/', 'Open Seforim'), ' — open readers for Hebrew and Judaica texts, by Ezra Brand · ',
      a('https://www.ezrabrand.com/', 'ezrabrand.com')]));
    fi.appendChild(b);

    f.appendChild(fi);
    document.body.appendChild(f);
  }
})();
