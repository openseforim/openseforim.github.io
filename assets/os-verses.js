/* Open Seforim: click a reference to see its text (Hebrew and English) from the Sefaria API.
   Loaded by os.js on pages that have references:
   - span.ref "[Gen 1:2; cf. b. Shabbat 31a]" (Taḥkemoni, Immanuel, Me'or Einayim): the references inside become buttons;
   - a.ref with a Sefaria URL (Emden): a click opens the popup; ctrl/cmd/middle click still opens Sefaria.
   Bible: Hebrew "Miqra according to the Masorah" (CC BY-SA), English the Koren Jerusalem Bible (CC BY-NC, shown
   from Sefaria, not copied), with JPS 1917 (public domain) where Koren has no text.
   Other texts: Sefaria's default Hebrew and English versions (the popup names them).
   Words of the text that also occur in the Hebrew of the same row are marked. */
(function () {
  "use strict";
  if (window.__osVerses) return;
  window.__osVerses = true;

  var BOOKS = {
    "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers", "Deut": "Deuteronomy",
    "Josh": "Joshua", "Judg": "Judges", "Ruth": "Ruth", "1 Sam": "I Samuel", "2 Sam": "II Samuel",
    "1 Kgs": "I Kings", "2 Kgs": "II Kings", "Isa": "Isaiah", "Jer": "Jeremiah", "Ezek": "Ezekiel",
    "Hos": "Hosea", "Joel": "Joel", "Amos": "Amos", "Obad": "Obadiah", "Jonah": "Jonah", "Mic": "Micah",
    "Nah": "Nahum", "Hab": "Habakkuk", "Zeph": "Zephaniah", "Hag": "Haggai", "Zech": "Zechariah",
    "Mal": "Malachi", "Ps": "Psalms", "Prov": "Proverbs", "Job": "Job", "Song": "Song of Songs",
    "Lam": "Lamentations", "Eccl": "Ecclesiastes", "Esth": "Esther", "Dan": "Daniel", "Ezra": "Ezra",
    "Neh": "Nehemiah", "1 Chr": "I Chronicles", "2 Chr": "II Chronicles"
  };
  // tractate spellings used in the readers -> Sefaria titles
  var TRACT = {
    "B. Bat.": "Bava Batra", "B. Metz.": "Bava Metzia", "B. Qam.": "Bava Kamma", "Mo'ed Qat.": "Moed Katan",
    "Mo'ed Katan": "Moed Katan", "Ta'anit": "Taanit", "Me'ilah": "Meilah", "Betsah": "Beitzah",
    "Ketubbot": "Ketubot", "Pesahim": "Pesachim", "Pesaḥim": "Pesachim", "Hullin": "Chullin", "Ḥullin": "Chullin",
    "Menahot": "Menachot", "Menaḥot": "Menachot", "Hagigah": "Chagigah", "Ḥagigah": "Chagigah",
    "Zevahim": "Zevachim", "Zevaḥim": "Zevachim", "Pe'ah": "Peah", "Avot": "Pirkei Avot", "Qiddushin": "Kiddushin"
  };
  var MIDRASH = {
    "Gen. Rab.": "Bereshit Rabbah", "Bereshit Rabbah": "Bereshit Rabbah", "Genesis Rabbah": "Bereshit Rabbah",
    "Lev. Rab.": "Vayikra Rabbah", "Leviticus Rabbah": "Vayikra Rabbah", "Vayikra Rabbah": "Vayikra Rabbah",
    "Pirkei de-Rabbi Eliezer": "Pirkei DeRabbi Eliezer"
  };
  // Bible English: the Koren Jerusalem Bible; JPS 1917 only where Koren has no text
  var HE_BIBLE = "Miqra according to the Masorah", EN_BIBLE = "The Koren Jerusalem Bible",
    EN_BIBLE_2 = "The Holy Scriptures: A New Translation (JPS 1917)";

  function rx(list) { return list.map(function (s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }).join("|"); }
  var bookKeys = Object.keys(BOOKS).sort(function (a, b) { return b.length - a.length; });
  var midKeys = Object.keys(MIDRASH).sort(function (a, b) { return b.length - a.length; });
  var TRACT_NAME = "[A-ZḤ][\\w'ḥḤ.]*(?: [A-Z][\\w'.]*)?";
  // one regex, alternatives in order: commentary on a verse, Bible, Talmud/Mishnah/Tosefta, Midrash
  var FIND = new RegExp(
    "((?:Rashi|Ibn Ezra|Ramban|Radak) on )?\\b(" + rx(bookKeys) + ") (\\d+)(?::(\\d+)(?:[–-](\\d+))?)?(?![\\w:])" +
    "|\\b([bmyt])\\. (" + TRACT_NAME + ") (\\d+[ab]?(?::\\d+)?(?:[–-]\\d+[ab]?|[–-][ab])?)(?![\\w:])" +
    "|\\b(" + rx(midKeys) + ") (\\d+(?::\\d+)?)(?![\\w:])", "g");

  function sefariaRef(m) {
    if (m[2]) {
      // a one-chapter book with a lone number ("Obad 6"): the number is the verse
      var one = m[2] === "Obad" && !m[4];
      var r = BOOKS[m[2]] + " " + (one ? "1:" : "") + m[3] + (m[4] ? ":" + m[4] + (m[5] ? "-" + m[5] : "") : "");
      if (m[1]) return { ref: m[1].replace(/ on $/, "") + " on " + r, bible: false };
      return { ref: r, bible: true };
    }
    if (m[6]) {
      var t = TRACT[m[7]] || m[7], loc = m[8].replace(/–/g, "-");
      var x = loc.match(/^(\d+)([ab])-([ab])$/);  // 99a-b -> 99a-99b
      if (x) loc = x[1] + x[2] + "-" + x[1] + x[3];
      var pre = { b: "", m: "Mishnah ", y: "Jerusalem Talmud ", t: "Tosefta " }[m[6]];
      if (t === "Pirkei Avot") pre = "";
      return { ref: pre + t + " " + loc, bible: false };
    }
    return { ref: MIDRASH[m[9]] + " " + m[10], bible: false };
  }

  window.__osVersesParse = function (text) { // for tests: the Sefaria refs found in a text
    var out = [], m; FIND.lastIndex = 0;
    while ((m = FIND.exec(text))) out.push([m[0], sefariaRef(m).ref]);
    return out;
  };

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  // 1. span.ref: wrap each reference found in its text in a button
  Array.prototype.forEach.call(document.querySelectorAll("span.ref"), function (span) {
    if (span.querySelector("a, button") || span.closest("header, footer, details")) return;
    var text = span.textContent, out = "", last = 0, m, n = 0;
    FIND.lastIndex = 0;
    while ((m = FIND.exec(text))) {
      var s = sefariaRef(m);
      out += esc(text.slice(last, m.index)) + '<button type="button" class="os-vref" data-ref="' + esc(s.ref) +
        '" data-bible="' + (s.bible ? 1 : "") + '" aria-haspopup="dialog" aria-expanded="false">' + esc(m[0]) + "</button>";
      last = FIND.lastIndex; n++;
    }
    if (n) span.innerHTML = out + esc(text.slice(last));
    if (n && text.length < 30) span.style.whiteSpace = "nowrap"; // keep "[Gen 24:14]" whole, no lone bracket
  });
  // 2. a.ref with a Sefaria URL ("Psalms.68.31", "I_Samuel.2.3"): Bible books get the Bible versions
  var BOOKS_FULL = new RegExp("^(" + Object.keys(BOOKS).map(function (k) { return BOOKS[k].replace(/ /g, "[ _]"); }).join("|") + ")[ ._]\\d");
  Array.prototype.forEach.call(document.querySelectorAll('a.ref[href*="sefaria.org/"]'), function (a) {
    var path = decodeURIComponent(a.pathname.replace(/^\//, ""));
    if (!path) return;
    a.dataset.ref = path;
    a.dataset.bible = BOOKS_FULL.test(path) ? 1 : "";
    a.classList.add("os-vref");
    a.setAttribute("aria-haspopup", "dialog");
    a.setAttribute("aria-expanded", "false");
  });
  if (!document.querySelector(".os-vref")) return;

  var cache = {}, pop = null, openBtn = null;
  var NIQQUD = /[֑-ׇ]/g, TROPE = /[֑-ֽ֯׀׃]/g;
  var FINALS = { "ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ" };
  function bare(w) { return w.replace(NIQQUD, "").replace(/[^א-ת]/g, "").replace(/[ךםןףץ]/g, function (c) { return FINALS[c]; }); }
  // endings removed when comparing (pronoun suffixes, plurals), longest first; letters already de-finalized
  var SUFFIXES = ["יהמ", "יכמ", "יהנ", "ותיו", "ותי", "ותנו", "יו", "ימ", "ות", "נו", "כמ", "המ", "הנ", "י", "ו", "ה", "כ", "מ", "נ"];
  function stems(w) { // the word, without up to two prefix letters (ו ה ב כ ל מ ש), and each of those without an ending
    var b = bare(w), pre = [b], out = [];
    for (var i = 0; i < 2 && b.length > 3 && "והבכלמש".indexOf(b[0]) >= 0; i++) { b = b.slice(1); pre.push(b); }
    pre.forEach(function (p) {
      out.push(p);
      for (var k = 0; k < SUFFIXES.length; k++) {
        var s = SUFFIXES[k];
        if (p.length - s.length >= 3 && p.slice(-s.length) === s) { out.push(p.slice(0, -s.length)); break; }
      }
    });
    return out;
  }
  // function words that would mark half of any text
  var STOP = {};
  ("אשר אין היה הוא היא הם הנה את אתה אל על כי גם מה זה זאת לא אלא כל עד עם אם או בין לו לה לי כן " +
   "אמר אומר אמרו אמרה שנאמר דכתיב כתיב מאי איכא הכא התמ תנו תניא דאמר רבי רבנ ליה להו").split(" ")
    .forEach(function (w) { STOP[w] = 1; });
  function flat(t) { return Array.isArray(t) ? t.map(flat).join(" ") : (t || ""); }
  function clean(html) {
    var d = document.createElement("div");
    d.innerHTML = html;
    Array.prototype.forEach.call(d.querySelectorAll("sup, i.footnote, .footnote-marker"), function (x) { x.remove(); });
    return d.textContent.replace(/\s+/g, " ").trim();
  }

  function fetchRef(s) {
    if (cache[s.ref]) return cache[s.ref];
    var u = "https://www.sefaria.org/api/v3/texts/" + encodeURIComponent(s.ref) +
      (s.bible ? "?version=hebrew|" + encodeURIComponent(HE_BIBLE) + "&version=english|" + encodeURIComponent(EN_BIBLE) +
                 "&version=english|" + encodeURIComponent(EN_BIBLE_2)
               : "?version=hebrew&version=english");
    cache[s.ref] = fetch(u).then(function (r) {
      if (!r.ok) throw new Error(r.status === 404 ? "not found" : "HTTP " + r.status);
      return r.json();
    }).then(function (j) {
      var d = { ref: j.ref || s.ref, heRef: j.heRef || "", he: "", en: "", heT: "", enT: "" };
      var vs = (j.versions || []).slice().sort(function (a, b) { // the preferred English first
        return (b.versionTitle === EN_BIBLE) - (a.versionTitle === EN_BIBLE);
      });
      vs.forEach(function (v) {
        if (v.language === "he" && !d.he) { d.he = clean(flat(v.text)); d.heT = v.versionTitle; }
        if (v.language === "en" && !d.en) { var t = clean(flat(v.text)); if (t) { d.en = t; d.enT = v.versionTitle; } }
      });
      if (!d.he && !d.en) throw new Error("no text");
      return d;
    });
    cache[s.ref].catch(function () { delete cache[s.ref]; });
    return cache[s.ref];
  }

  function markHebrew(text, line) {
    var have = {}, any = false;
    line.split(/[\s־]+/).forEach(function (w) { stems(w).forEach(function (s) { if (s.length > 2 && !STOP[s]) { have[s] = 1; any = true; } }); });
    text = text.replace(TROPE, "");
    if (!any) return esc(text);
    return text.split(/(\s+|־)/).map(function (w) {
      if (/^\s+$|^־$/.test(w)) return w;
      var hit = stems(w).some(function (s) { return s.length > 2 && !STOP[s] && have[s]; });
      return hit ? "<mark>" + esc(w) + "</mark>" : esc(w);
    }).join("");
  }

  // the Hebrew of the same row (line-aligned readers); none in Emden, so nothing is marked there
  function rowHebrew(btn) {
    var row = btn.closest(".row, .seg, tr");
    if (!row) return "";
    var he = row.querySelector('.he, [lang="he"]');
    return he ? he.textContent : "";
  }

  function close(refocus) {
    if (pop) { pop.remove(); pop = null; }
    if (openBtn) { openBtn.setAttribute("aria-expanded", "false"); if (refocus) openBtn.focus({ preventScroll: true }); openBtn = null; }
  }

  function place(btn) {
    if (!pop) return;
    if (innerWidth < 600) { pop.classList.add("os-vpop-sheet"); pop.style.cssText = ""; return; } // phone: bottom sheet
    pop.classList.remove("os-vpop-sheet");
    var r = btn.getBoundingClientRect(), w = Math.min(460, innerWidth - 24);
    pop.style.width = w + "px";
    pop.style.left = Math.max(12, Math.min(r.left + scrollX, scrollX + innerWidth - w - 12)) + "px";
    var h = pop.offsetHeight, below = innerHeight - r.bottom - 70; // keep clear of the bottom "This passage" bar
    pop.style.top = (h > below && r.top > h + 60 ? r.top + scrollY - h - 6 : r.bottom + scrollY + 6) + "px";
  }

  function head(title, heRef) {
    return '<div class="os-vpop-h"><b>' + esc(title) + "</b>" + (heRef ? ' <span lang="he" dir="rtl">' + esc(heRef) + "</span>" : "") +
      '<button type="button" class="os-vpop-x" aria-label="Close">×</button></div>';
  }

  function open(btn) {
    close(false);
    openBtn = btn;
    btn.setAttribute("aria-expanded", "true");
    var s = { ref: btn.dataset.ref, bible: !!btn.dataset.bible }, line = rowHebrew(btn);
    pop = document.createElement("div");
    pop.className = "os-vpop";
    pop.setAttribute("role", "dialog");
    pop.setAttribute("aria-label", s.ref);
    pop.innerHTML = head(s.ref.replace(/_/g, " ").replace(/\.(\d)/g, " $1"), "") + '<p class="os-vpop-msg">Loading…</p>';
    document.body.appendChild(pop);
    place(btn);
    fetchRef(s).then(function (d) {
      if (!pop || openBtn !== btn) return;
      var link = "https://www.sefaria.org/" + encodeURIComponent(d.ref.replace(/ /g, "_")).replace(/%3A/g, ".") + "?lang=bi";
      pop.innerHTML = head(d.ref, d.heRef) + '<div class="os-vpop-body">' +
        (d.he ? '<p class="os-vpop-he" lang="he" dir="rtl">' + markHebrew(d.he, line) + "</p>" : "") +
        (d.en ? '<p class="os-vpop-en" lang="en">' + esc(d.en) + "</p>" : "") + "</div>" +
        '<p class="os-vpop-src">' + esc([d.heT, d.enT].filter(Boolean).join(" · ")) +
        ' · <a href="' + link + '" target="_blank" rel="noopener">Sefaria ↗</a></p>';
      place(btn);
      // a long text (a Talmud page): scroll to the densest group of marked words, not to the first one
      var body = pop.querySelector(".os-vpop-body"), mks = pop.querySelectorAll("mark");
      if (body && mks.length && body.scrollHeight > body.clientHeight) {
        var best = 0, bestN = 0;
        for (var i = 0; i < mks.length; i++) {
          var n = 0;
          for (var j = i; j < mks.length && mks[j].offsetTop - mks[i].offsetTop < 90; j++) n++;
          if (n > bestN) { bestN = n; best = i; }
        }
        body.scrollTop = mks[best].offsetTop - 40;
      }
    }).catch(function (e) {
      if (!pop || openBtn !== btn) return;
      pop.querySelector(".os-vpop-msg").innerHTML = "Could not load the text from Sefaria (" + esc(e.message) + "). " +
        '<a href="https://www.sefaria.org/' + encodeURIComponent(s.ref.replace(/ /g, "_")) + '" target="_blank" rel="noopener">Search Sefaria ↗</a>';
    });
  }

  document.addEventListener("click", function (ev) {
    if (pop && ev.target.closest(".os-vpop-x")) { close(true); return; }
    var b = ev.target.closest(".os-vref");
    if (b) {
      if (b.tagName === "A" && (ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.button === 1)) return; // open Sefaria as before
      ev.preventDefault();
      if (b === openBtn) close(true); else open(b);
      return;
    }
    if (pop && !pop.contains(ev.target)) close(false);
  });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && pop) close(true); });
  addEventListener("resize", function () { if (pop && openBtn) place(openBtn); });

  var css = document.createElement("style");
  css.textContent =
    "button.os-vref{all:unset;cursor:pointer;color:inherit;border-bottom:1px dotted currentColor}" +
    ".os-vref:hover,.os-vref[aria-expanded=true]{color:var(--os-accent,var(--accent))}" +
    ".os-vref:focus-visible{outline:2px solid var(--os-accent,var(--accent));outline-offset:1px}" +
    ".os-vpop{position:absolute;z-index:900;background:var(--os-bg,#fff);color:var(--os-fg,#222);" +
    "border:1px solid var(--os-line,#ddd);border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.18);" +
    "padding:10px 14px 8px;font:.95rem/1.5 var(--os-serif,Georgia,serif);text-align:left}" +
    ".os-vpop-h{display:flex;gap:.6em;align-items:baseline;font:.85rem var(--os-sans,system-ui,sans-serif);color:var(--os-muted,#777)}" +
    ".os-vpop-h b{color:var(--os-fg,#222)}" +
    ".os-vpop-x{all:unset;cursor:pointer;margin-left:auto;font-size:1.2rem;line-height:1;padding:0 2px}" +
    ".os-vpop-body{max-height:min(55vh,420px);overflow:auto;position:relative}" +
    ".os-vpop-he{font-family:var(--os-he,'Noto Serif Hebrew',serif);font-size:1.2rem;line-height:1.7;text-align:right;margin:.4em 0}" +
    ".os-vpop-he mark{background:var(--os-mark,#f3e6b8);color:inherit;border-bottom:2px solid var(--os-accent,#8a3b12);border-radius:2px}" +
    ".os-vpop-en{margin:.3em 0;font-style:normal}" +
    ".os-vpop-src,.os-vpop-msg{font:.75rem var(--os-sans,system-ui,sans-serif);color:var(--os-muted,#777);margin:.5em 0 0}" +
    ".os-vpop.os-vpop-sheet{position:fixed;left:8px;right:8px;bottom:8px;top:auto;z-index:1000}" +
    ".os-vpop-sheet .os-vpop-body{max-height:45vh}";
  document.head.appendChild(css);
})();
