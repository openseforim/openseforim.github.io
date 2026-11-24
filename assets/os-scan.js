/* Open Seforim: the scan panel. A "Scan" button beside "Display" shows the page scan in the right margin, and the
   panel follows the reading: it shows the page whose start marker is the last one above a line 30% down the window.
   Loaded by os.js on pages that have page markers. Off by default; the choice is kept (localStorage "os-scan").

   Page markers, in the order of the text: a.pg (Bochart, Lewysohn, Löw), a.pb (Me'or Einayim), a.scanlink
   (Ma'agal Tov), or any element with data-scan-img. A page with no markers in the text but one link to an
   archive.org page (Barhebraeus: one scan per reader page) shows that page.
   The image: data-scan-img if given; else the page's own thumbnail with the same link (div.scans), enlarged;
   else an IIIF or archive.org image built from the link (MDZ / digitale-sammlungen, UB Frankfurt, archive.org).
   A checkbox with class os-scan-toggle on the page works as a second switch. */
(function () {
  if (document.documentElement.classList.contains('os-home')) return;  // a work's contents page is not a reading page
  var W = 900;  // requested image width
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  function iiifWidth(u) { return u.replace(/\/full\/[^/]+\/0\//, '/full/' + W + ',/0/').replace(/\/0\/d$/, '/0/default.jpg'); }
  function fromHref(href) {
    var m;
    if ((m = href.match(/digitale-sammlungen\.de\/\w+\/view\/(bsb\d+)\?page=(\d+)/)))
      return 'https://api.digitale-sammlungen.de/iiif/image/v2/' + m[1] + '_' + ('0000' + m[2]).slice(-5) + '/full/' + W + ',/0/default.jpg';
    if ((m = href.match(/sammlungen\.ub\.uni-frankfurt\.de\/.*\/pageview\/(\d+)/)))
      return 'https://sammlungen.ub.uni-frankfurt.de/i3f/v20/' + m[1] + '/full/' + W + ',/0/default.jpg';
    if ((m = href.match(/archive\.org\/details\/([^/]+)\/page\/(n\d+)/)))
      return 'https://archive.org/download/' + m[1] + '/page/' + m[2] + '_w' + W + '.jpg';
    return null;
  }
  var thumbs = {};
  Array.prototype.forEach.call(document.querySelectorAll('div.scans a[href] img'), function (im) {
    var src = im.getAttribute('src') || im.getAttribute('data-src') || '';
    if (src) thumbs[im.parentNode.getAttribute('href')] = /\/full\//.test(src) ? iiifWidth(src) : src;
  });
  function imageOf(a) {
    if (a.dataset && a.dataset.scanImg) return a.dataset.scanImg;
    var href = a.getAttribute('href') || '';
    var t = thumbs[href];
    if (t && /\/full\//.test(t)) return t;   // an IIIF thumbnail, asked for at full width
    return fromHref(href) || t;               // else the library's full image; a local thumbnail only as a last resort
  }
  function labelOf(a) {
    if (a === single) return 'Scan of this page';
    var t = (a.dataset && a.dataset.scanLabel) || a.textContent.replace(/\s+/g, ' ').trim();
    return /^\d+$/.test(t) ? 'p. ' + t : t;
  }

  var marks = Array.prototype.filter.call(
    document.querySelectorAll('a.pg, a.pb, a.scanlink, [data-scan-img]'), function (a) { return imageOf(a); });
  var single = null;
  if (!marks.length) {
    var one = Array.prototype.filter.call(document.querySelectorAll('a[href*="archive.org/details/"][href*="/page/n"]'),
      function (a) { return fromHref(a.href); });
    if (one.length === 1) single = one[0];
  }
  if (!marks.length && !single) return;

  // ---- interface ----
  var btn = document.createElement('button');
  btn.type = 'button'; btn.className = 'os-scan-btn'; btn.setAttribute('aria-pressed', 'false');
  btn.title = 'Show the page scan beside the text';
  btn.innerHTML = '<span aria-hidden="true" class="os-scan-ico">▤</span><span class="os-scan-word">Scan</span>';
  var disp = document.querySelector('.os-disp-btn');
  if (disp && disp.parentNode) disp.parentNode.insertBefore(btn, disp);
  else return;

  var panel = document.createElement('aside');
  panel.className = 'os-scan'; panel.setAttribute('aria-label', 'Page scan'); panel.hidden = true;
  panel.innerHTML = '<div class="os-scan-head"><span class="os-scan-lbl"></span>' +
    '<a class="os-scan-ext" rel="noopener" target="_blank">Open in the library viewer ↗</a>' +
    '<button type="button" class="os-scan-x" aria-label="Close the scan">×</button></div>' +
    '<div class="os-scan-img"><img alt="" decoding="async"><p class="os-scan-wait">Loading the scan…</p></div>';
  document.body.appendChild(panel);
  var img = panel.querySelector('img'), lbl = panel.querySelector('.os-scan-lbl'),
    ext = panel.querySelector('.os-scan-ext'), wait = panel.querySelector('.os-scan-wait');
  img.addEventListener('load', function () { wait.hidden = true; });
  img.addEventListener('error', function () { wait.hidden = false; wait.textContent = 'The scan could not be loaded. Use the link above.'; });

  var shown = null;
  function show(a) {
    if (!a || a === shown) return;
    shown = a;
    var src = imageOf(a);
    if (img.getAttribute('src') !== src) { wait.hidden = false; wait.textContent = 'Loading the scan…'; img.src = src; }
    img.alt = 'Scan: ' + labelOf(a);
    lbl.textContent = labelOf(a);
    ext.href = a.href;
  }
  function current() {
    if (single) return single;
    // the marker closest above the reading line; markers can be in two side-by-side columns (Bochart's Latin and
    // English), so all are checked, not only the first ones in document order
    var line = window.innerHeight * 0.3, best = null, bestTop = -Infinity, first = null, firstTop = Infinity;
    for (var i = 0; i < marks.length; i++) {
      var r = marks[i].getBoundingClientRect();
      if (r.height === 0 && r.width === 0) continue;  // hidden copy of a marker
      if (r.top <= line && r.top > bestTop) { best = marks[i]; bestTop = r.top; }
      if (r.top < firstTop) { first = marks[i]; firstTop = r.top; }
    }
    return best || first;
  }
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { ticking = false; show(current()); });
  }
  var toggles = document.querySelectorAll('input.os-scan-toggle');
  function apply(on) {
    document.documentElement.classList.toggle('os-scan-on', on);
    panel.hidden = !on;
    btn.setAttribute('aria-pressed', String(on));
    Array.prototype.forEach.call(toggles, function (t) { t.checked = on; });
    set('os-scan', on ? '1' : '0');
    if (on) { show(current()); window.addEventListener('scroll', onScroll, { passive: true }); }
    else window.removeEventListener('scroll', onScroll);
  }
  btn.addEventListener('click', function () { apply(panel.hidden); });
  panel.querySelector('.os-scan-x').addEventListener('click', function () { apply(false); });
  Array.prototype.forEach.call(toggles, function (t) { t.addEventListener('change', function () { apply(t.checked); }); });
  // with the panel on, a click on a page marker shows that page here instead of leaving the page
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('a.pg, a.pb, a.scanlink');
    if (!a || panel.hidden || marks.indexOf(a) < 0 || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    ev.preventDefault(); shown = null; show(a);
  });
  window.addEventListener('resize', function () { if (!panel.hidden) show(current()); });
  apply(get('os-scan') === '1' && window.matchMedia('(min-width: 1000px)').matches);
})();
