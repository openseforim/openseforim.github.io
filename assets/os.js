/* Open Seforim shared header strip, display settings (theme, text size, Hebrew font) and footer. v2.
   Each reader page loads it with: <script src="/assets/os.js" defer></script>
   The work's metadata comes from /<slug>/work.json. */
(function () {
  // short work titles, written by build.py from the works' work.json (no flash of the slug)
  var TITLES = /*TITLES*/{"emden": "*Megillat Sefer*", "immanuel": "*Maḥberot*", "tahkemoni": "*Taḥkemoni*", "maagal-tov": "*Ma'agal Tov*", "meor-einayim": "*Me'or Einayim*", "hyman": "*Toldot Tannaim ve-Amoraim*", "bochart": "*Hierozoicon*", "lewysohn": "*Zoologie des Talmuds*", "loew": "*Flora der Juden*", "barhebraeus": "*Chronography*", "defus": "Defus"}/*END*/;
  // download files per work (plain text, TEI, EPUB in /downloads/<slug>/), written by build.py
  var DOWNLOADS = /*DOWNLOADS*/{"emden": ["jacob-emden-megillat-sefer.txt", "jacob-emden-megillat-sefer.tei.xml", "jacob-emden-megillat-sefer.epub"], "immanuel": ["immanuel-of-rome-mahberot.txt", "immanuel-of-rome-mahberot.tei.xml", "immanuel-of-rome-mahberot.epub"], "tahkemoni": ["judah-al-harizi-tahkemoni.txt", "judah-al-harizi-tahkemoni.tei.xml", "judah-al-harizi-tahkemoni.epub"], "maagal-tov": ["hida-maagal-tov.txt", "hida-maagal-tov.tei.xml", "hida-maagal-tov.epub"], "meor-einayim": ["azariah-de-rossi-meor-einayim.txt", "azariah-de-rossi-meor-einayim.tei.xml", "azariah-de-rossi-meor-einayim.epub"], "hyman": ["aaron-hyman-toldot-tannaim-ve-amoraim.txt", "aaron-hyman-toldot-tannaim-ve-amoraim.tei.xml", "aaron-hyman-toldot-tannaim-ve-amoraim.epub"], "bochart": ["samuel-bochart-hierozoicon.txt", "samuel-bochart-hierozoicon.tei.xml", "samuel-bochart-hierozoicon.epub"], "lewysohn": ["ludwig-lewysohn-die-zoologie-des-talmuds.txt", "ludwig-lewysohn-die-zoologie-des-talmuds.tei.xml", "ludwig-lewysohn-die-zoologie-des-talmuds.epub"], "loew": ["immanuel-loew-die-flora-der-juden.txt", "immanuel-loew-die-flora-der-juden.tei.xml", "immanuel-loew-die-flora-der-juden.epub"], "barhebraeus": ["barhebraeus-chronography.txt", "barhebraeus-chronography.tei.xml", "barhebraeus-chronography.epub"]}/*END*/;
  // GoatCounter site code (privacy-friendly page counts, no cookies). Empty = off.
  var GOATCOUNTER = 'openseforim';  // dashboard: https://openseforim.goatcounter.com/ (switched on 23-Nov-2026)
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
    var m = document.querySelector('meta[name="color-scheme"]');  // written by the early script in <head>
    if (m) m.content = v === 'dark' ? 'dark' : (!v || v === 'auto') ? 'light dark' : 'light';
  }
  apply(theme);

  if (GOATCOUNTER && location.hostname === 'openseforim.org') {
    var gc = document.createElement('script');
    gc.async = true; gc.src = 'https://gc.zgo.at/count.js';
    gc.setAttribute('data-goatcounter', 'https://' + GOATCOUNTER + '.goatcounter.com/count');
    document.head.appendChild(gc);
  }

  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function today() { var d = new Date(); return ('0' + d.getDate()).slice(-2) + '-' + MON[d.getMonth()] + '-' + d.getFullYear(); }

  var slug =location.pathname.split('/').filter(Boolean)[0] || '';
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
  var brandBox = el('div', { 'class': 'os-brandbox' });
  var home = el('a', { 'class': 'os-home', href: '/', 'aria-label': 'Open Seforim, home' });
  home.appendChild(el('img', { src: '/apple-touch-icon.png', alt: '', width: '26', height: '26' }));
  home.appendChild(el('span', {}, 'Open Seforim'));
  brandBox.appendChild(home);
  inner.appendChild(brandBox);
  var workLink = null;
  // a reader with its own top bar (a.brand) already names the work: the strip does not repeat it
  var ownBar = document.querySelector('a.brand');
  if (slug && !ownBar) {
    brandBox.appendChild(el('span', { 'class': 'os-sep', 'aria-hidden': 'true' }, '/'));
    workLink = el('a', { href: base, 'class': 'os-work' });
    workLink.innerHTML = ital(TITLES[slug] || slug);
    brandBox.appendChild(workLink);
  }
  inner.appendChild(el('span', { 'class': 'os-sp' }));
  var nav = el('div', { 'class': 'os-nav' });
  nav.appendChild(el('a', { href: '/#works' }, 'All works'));
  nav.appendChild(el('a', { href: '/next/', 'class': 'os-about' }, 'Planned'));
  nav.appendChild(el('a', { href: '/about/', 'class': 'os-about' }, 'About'));
  inner.appendChild(nav);
  // ---- display panel: theme, text size, Hebrew font (one choice for all works) ----
  // The choice is applied before the page paints by the early script that tools/postbuild.py writes in <head>.
  var SIZES = [['s', 'A−', 'Smaller'], ['', 'A', 'Normal'], ['l', 'A+', 'Larger'], ['xl', 'A++', 'Largest']];
  // [key, label, CSS family, Google Fonts family parameter]; the default ('') is Noto Serif Hebrew
  var HEFONTS = [['', 'Noto Serif', '"Noto Serif Hebrew"', 'Noto+Serif+Hebrew:wght@400;600'],
    ['frank', 'Frank Ruhl', '"Frank Ruhl Libre"', 'Frank+Ruhl+Libre:wght@400;600'],
    ['david', 'David', '"David Libre"', 'David+Libre:wght@400;500'],
    ['device', 'Device font', '"SBL Hebrew","Ezra SIL","Taamey Frank CLM","Frank Ruehl CLM",David,"Times New Roman"', '']];
  var SAMPLE = 'בְּרֵאשִׁית בָּרָא אֱלֹהִים';
  var ownPalette = root.classList.contains('os-own-palette');
  function fontLink(param) {
    if (!param || document.querySelector('link[data-os-font="' + param + '"]')) return;
    document.head.appendChild(el('link', { rel: 'stylesheet', 'data-os-font': param,
      href: 'https://fonts.googleapis.com/css2?family=' + param + '&display=swap' }));
  }
  var disp = el('button', { type: 'button', 'class': 'os-disp-btn', 'aria-expanded': 'false', 'aria-controls': 'os-disp',
    'aria-label': 'Display settings', title: 'Theme, text size and Hebrew font, for all works' });
  disp.innerHTML = '<span aria-hidden="true" class="os-aa">Aa</span><span class="os-disp-word">Display</span>';
  inner.appendChild(disp);

  var panel = el('div', { 'class': 'os-disp', id: 'os-disp', role: 'dialog', 'aria-label': 'Display settings' });
  panel.hidden = true;
  function row(label) {
    var r = el('div', { 'class': 'os-disp-row' });
    r.appendChild(el('div', { 'class': 'os-disp-label' }, label));
    panel.appendChild(r);
    return r;
  }
  var sel = el('select', { 'aria-label': 'Colour theme' });
  [['auto', 'Auto (as device)'], ['light', 'Light'], ['paper', 'Paper'], ['dark', 'Dark']].forEach(function (o) {
    sel.appendChild(el('option', { value: o[0] }, o[1]));
  });
  sel.value = theme === '' ? 'auto' : theme;
  sel.addEventListener('change', function () { set(KEY, sel.value); apply(sel.value); });
  row('Theme').appendChild(sel);
  if (!ownPalette) {  // Defus keeps its own type
    var curSize = root.getAttribute('data-os-size') || '';
    var sg = el('div', { 'class': 'os-seg', role: 'group', 'aria-label': 'Text size' });
    SIZES.forEach(function (z) {
      var b = el('button', { type: 'button', title: z[2], 'aria-pressed': String(z[0] === curSize) }, z[1]);
      b.addEventListener('click', function () {
        if (z[0]) root.setAttribute('data-os-size', z[0]); else root.removeAttribute('data-os-size');
        set('os-size', z[0]);
        Array.prototype.forEach.call(sg.children, function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      });
      sg.appendChild(b);
    });
    row('Text size').appendChild(sg);
    var curHe = root.getAttribute('data-os-he') || '';
    var fg = el('div', { 'class': 'os-fonts', role: 'radiogroup', 'aria-label': 'Hebrew font' });
    HEFONTS.forEach(function (f) {
      var b = el('button', { type: 'button', role: 'radio', 'aria-checked': String(f[0] === curHe) });
      b.appendChild(el('span', { 'class': 'os-fname' }, f[1]));
      var smp = el('span', { 'class': 'os-fsample', lang: 'he', dir: 'rtl' }, SAMPLE);
      smp.style.fontFamily = f[2] + ',serif';
      b.appendChild(smp);
      b.addEventListener('click', function () {
        fontLink(f[3]);
        if (f[0]) root.setAttribute('data-os-he', f[0]); else root.removeAttribute('data-os-he');
        set('os-he', f[0]);
        Array.prototype.forEach.call(fg.children, function (x) { x.setAttribute('aria-checked', String(x === b)); });
      });
      fg.appendChild(b);
    });
    row('Hebrew font').appendChild(fg);
  }
  function placePanel() {  // the panel is fixed, under the button, wherever the button is (strip or reader bar)
    var r = disp.getBoundingClientRect();
    panel.style.top = Math.round(r.bottom + 6) + 'px';
    panel.style.right = Math.max(8, Math.round(document.documentElement.clientWidth - r.right)) + 'px';
  }
  function openPanel(open) {
    if (open && !ownPalette) HEFONTS.forEach(function (f) { fontLink(f[3]); });  // load the samples
    if (open) placePanel();
    panel.hidden = !open;
    disp.setAttribute('aria-expanded', String(open));
  }
  disp.addEventListener('click', function () { openPanel(panel.hidden); });
  document.addEventListener('click', function (e) {
    if (!panel.hidden && !panel.contains(e.target) && !disp.contains(e.target)) openPanel(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !panel.hidden) { openPanel(false); disp.focus(); }
  });

  strip.appendChild(inner);
  document.body.insertBefore(strip, document.body.firstChild);
  document.body.insertBefore(panel, strip.nextSibling);

  // hide the readers' own theme selects and size buttons (the display panel replaces them)
  var own = document.querySelectorAll('select#theme, .size[aria-label="Text size"]');
  for (var j = 0; j < own.length; j++) {
    var s = own[j], wrap = s.closest('label') || s;
    wrap.classList.add('os-hidden');
  }
  window.addEventListener('resize', function () { if (!panel.hidden) placePanel(); });
  window.addEventListener('scroll', function () { if (!panel.hidden) placePanel(); }, { passive: true });

  // ---- floating header ----
  // A reader with its own sticky bar (Emden .bar, Lewysohn nav.where) gets the Display button in that bar, so it
  // stays in reach while reading: where the reader's old theme select was, or at the end. Other pages: the strip
  // itself floats (html.os-float). Decided once, at load (Emden's bar is not sticky on a phone).
  var sticky = null;
  Array.prototype.some.call(document.querySelectorAll('body > .bar, .bar, nav.where'), function (b) {
    var p = getComputedStyle(b).position;
    if ((p === 'sticky' || p === 'fixed') && b.offsetParent !== null) { sticky = b; return true; }
    return false;
  });
  if (sticky) {
    var oldSel = sticky.querySelector('select#theme');
    disp.classList.add('os-disp-inbar');
    var before = sticky.querySelector('form[role="search"]') || (oldSel && (oldSel.closest('label') || oldSel));
    if (before) before.parentNode.insertBefore(disp, before);
    else (sticky.querySelector('.barin') || sticky).appendChild(disp);
    root.classList.add('os-has-bar');
  } else if (!ownPalette) {
    root.classList.add('os-float');
  }

  // ---- footer from work.json ----
  if (!slug) return;
  // the work's home page (its contents page) gets a prominent "Start reading" button, from work.json "start"
  var isHome = location.pathname === base || location.pathname === base + 'index.html';
  if (isHome) document.documentElement.classList.add('os-home');
  fetch(base + 'work.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; })
    .then(function (w) { if (w) { if (isHome) startButton(w); footer(w); } }).catch(function () {});

  function startButton(w) {
    if (!w.start || document.querySelector('a.os-start')) return;
    var b = document.querySelector('a.cta') || el('a');  // a reader's own call-to-action is promoted, not doubled
    b.href = w.start;
    b.className = 'os-start';
    b.innerHTML = 'Start reading' + (w.start_label ? ': ' + ital(w.start_label) : '') + ' <span aria-hidden="true">→</span>';
    var h1 = document.querySelector('h1');
    var head = h1 && h1.closest('header');
    if (head) head.appendChild(b);
    else if (h1) h1.parentNode.insertBefore(b, h1.nextElementSibling && /^P$/.test(h1.nextElementSibling.tagName)
      ? h1.nextElementSibling.nextSibling : h1.nextSibling);
    else document.body.insertBefore(b, document.body.firstChild);
  }

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
    var cite = (w.cite || (w.title + '. Open Seforim')) + '. ' + (w.doi ? 'https://doi.org/' + w.doi : 'https://openseforim.org' + base) + ' (accessed ' + today() + ').';
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
    var files = DOWNLOADS[slug] || [];
    if (files.length) {
      var names = { txt: 'Plain text', xml: 'TEI XML', epub: 'EPUB' }, dl = ['Download: '];
      files.forEach(function (fn, i) {
        var ext = fn.split('.').pop(), x = a('/downloads/' + slug + '/' + fn, names[ext] || ext);
        x.setAttribute('download', '');
        if (i) dl.push(' · ');
        dl.push(x);
      });
      c2.appendChild(para(dl));
    }
    if (w.doi) c2.appendChild(para(['DOI: ', a('https://doi.org/' + w.doi, w.doi)]));
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
      a('/about/', 'About'), ' · ', a('/#works', 'All works'), ' · ', a('https://www.ezrabrand.com/', 'ezrabrand.com')]));
    fi.appendChild(b);

    f.appendChild(fi);
    document.body.appendChild(f);
    work = w;
    showPassage();
  }

  // ---- cite this passage: a bar for the passage in the address (#anchor) ----
  var work = null, bar = null;
  function passageLabel(t, id) {
    if (t.getAttribute('data-label')) return t.getAttribute('data-label');
    var m;
    if ((m = /^l(\d+)$/.exec(id))) return 'line ' + m[1];
    if ((m = /^s(\d+)$/.exec(id))) return slug === 'meor-einayim' ? 'segment ' + m[1] : '§ ' + m[1];
    if ((m = /^p(\d+)$/.exec(id)) && slug === 'bochart') return 'paragraph ' + (+m[1] + 1);
    var h = t.querySelector('h1,h2,h3,h4');
    return h ? h.textContent.replace(/\s+/g, ' ').trim().slice(0, 80) : '#' + id;
  }
  function chapterTitle() {
    var h = document.querySelector('h1');
    if (!h || location.pathname.replace(/index\.html$/, '') === base) return '';
    h = h.cloneNode(true);
    Array.prototype.forEach.call(h.querySelectorAll('.sub, small'), function (s) { s.remove(); });
    return h.textContent.replace(/\s+/g, ' ').trim();
  }
  function copyBtn(label, value) {
    var b = el('button', { type: 'button', 'class': 'os-copy' }, label);
    b.addEventListener('click', function () {
      if (navigator.clipboard) navigator.clipboard.writeText(value).then(function () {
        b.textContent = 'Copied'; setTimeout(function () { b.textContent = label; }, 1600);
      }, function () {});
    });
    return b;
  }
  function showPassage() {
    if (bar) { bar.remove(); bar = null; }
    var id = decodeURIComponent(location.hash.slice(1));
    if (!work || !id || id === 'notes' || id === 'top') return;
    var t = document.getElementById(id);
    if (!t || t.closest('footer, .os-foot, nav')) return;
    var label = passageLabel(t, id), ch = chapterTitle();
    var url = location.origin + location.pathname + '#' + encodeURIComponent(id);
    var c = plain(work.cite || work.title) + '. ' + (ch ? ch + ', ' : '') + label + '. ' + url + ' (accessed ' + today() + ').';
    bar = el('div', { 'class': 'os-passage', role: 'region', 'aria-label': 'Cite this passage' });
    bar.appendChild(el('span', { 'class': 'os-passage-label' }, 'This passage: ' + (ch ? ch + ', ' : '') + label));
    bar.appendChild(copyBtn('Copy citation', c));
    bar.appendChild(copyBtn('Copy link', url));
    var x = el('button', { type: 'button', 'class': 'os-passage-x', 'aria-label': 'Close' }, '×');
    x.addEventListener('click', function () { bar.remove(); bar = null; });
    bar.appendChild(x);
    document.body.appendChild(bar);
  }
  // references in [gray brackets] or Sefaria links: a click shows the text (assets/os-verses.js, loaded only when needed)
  if (document.querySelector('span.ref, a.ref[href*="sefaria.org/"]')) {
    var vs = document.createElement('script');
    vs.src = '/assets/os-verses.js';
    vs.defer = true;
    document.head.appendChild(vs);
  }

  window.addEventListener('hashchange', showPassage);
  document.addEventListener('click', function (e) {
    var l = e.target.closest && e.target.closest('a[href^="#"]');
    if (l && l.getAttribute('href') === location.hash) setTimeout(showPassage, 0);  // same anchor clicked again
  });
})();
