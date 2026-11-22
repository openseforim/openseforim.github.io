"""Export a work's reading edition as plain text, TEI P5 XML and EPUB 3, from its built HTML pages.

py -3.13 tools/export.py <slug> <site_dir> <out_dir>     (build.py runs it for every text work)

Pages are taken in the order of the work's contents page (index.html; for Hyman, mt/index.html). A "unit" is an
element whose children hold the source text (class he / heb / syr / de, or lang he / la / de / syr) and the English
(class en). Pages without units (search, indexes, about pages) are skipped. Output is deterministic, so an unchanged
work gives byte-identical files.
"""
import html, json, re, sys, zipfile
from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

sys.stdout.reconfigure(encoding="utf-8")
SITE = "https://openseforim.org"
SRC_LANGS = {"he", "la", "de", "syr", "ar"}
SRC_CLASSES = {"he", "heb", "syr", "de"}
JUNK = ".ptool, .anchor, a.self, .scanlink, .fix, .scanimg, .ln, .sn, .warn, button, script, style, .n"


def plain(s):
    return re.sub(r"\*", "", s or "")


def cls(el):
    return set(el.get("class", [])) if hasattr(el, "get") else set()


def src_lang(el):
    lang = (el.get("lang") or "").split("-")[0]
    if lang in SRC_LANGS:
        return lang
    c = cls(el)
    if c & {"he", "heb"}:
        return "he"
    if "syr" in c:
        return "syr"
    if "de" in c:
        return "de"
    return None


def is_en(el):
    return "en" in cls(el) or (el.get("lang") or "") == "en"


def text(el):
    el = BeautifulSoup(str(el), "lxml")
    for j in el.select(JUNK):
        j.decompose()
    for br in el.find_all("br"):
        br.replace_with(NavigableString("\n"))
    for p in el.find_all(["p", "div", "li", "h2", "h3", "tr"]):
        p.insert_after(NavigableString("\n"))
    t = el.get_text()
    t = re.sub(r"[ \t ]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def units(soup):
    out = []
    for el in soup.find_all(True):
        if "cols-head" in cls(el):
            continue
        kids = el.find_all(True, recursive=False)
        srcs = [k for k in kids if src_lang(k) and not is_en(k)]
        ens = [k for k in kids if is_en(k)]
        if not srcs or not ens:
            continue
        # Barhebraeus has Hebrew-letter transliteration and the Syriac: the source is the Syriac
        src = next((k for k in srcs if src_lang(k) == "syr"), srcs[0])
        s, e = text(src), text(ens[0])
        if s or e:
            out.append({"id": el.get("id") or "", "lang": src_lang(src), "src": s, "en": e})
    return out


def h1(soup):
    h = soup.find("h1")
    if not h:
        return soup.title.get_text(strip=True) if soup.title else ""
    h = BeautifulSoup(str(h), "lxml").find("h1")
    for s in h.select(".sub, small"):
        s.decompose()
    return " ".join(h.get_text(" ").split())


def page_order(slug, site):
    idx = site / ("mt/index.html" if slug == "hyman" else "index.html")
    base = idx.parent
    soup = BeautifulSoup(idx.read_text(encoding="utf-8"), "lxml")
    seen, pages = set(), []
    for a in soup.find_all("a", href=True):
        h = a["href"].split("#")[0].split("?")[0]
        if not h.endswith(".html") or h.startswith(("http", "/", "..")) or h == "index.html":
            continue
        f = (base / h).resolve()
        if f.exists() and f not in seen:
            seen.add(f); pages.append(f)
    # page-per-file works (Barhebraeus p001.html ...): the intro may link a page before the list, so sort by number
    if pages and all(re.fullmatch(r"p\d+\.html", p.name) for p in pages):
        pages.sort(key=lambda p: int(p.stem[1:]))
    return pages


def collect(slug, site):
    chapters = []
    for f in page_order(slug, site):
        soup = BeautifulSoup(f.read_text(encoding="utf-8"), "lxml")
        us = units(soup)
        if us:
            rel = f.relative_to(site).as_posix()
            chapters.append({"title": h1(soup), "url": f"{SITE}/{slug}/{rel}", "units": us})
    return chapters


# ---------------- writers ----------------
def write_txt(w, chs, path):
    lines = [plain(w["title"]), "", w.get("summary", "").replace("*", ""), "",
             f"Source text: {w.get('base_edition', {}).get('label', '')}",
             f"Licence: {w.get('licence', {}).get('name', '')}", f"Online: {w['url']} (Open Seforim)",
             "", "=" * 60, ""]
    for c in chs:
        lines += [c["title"], "-" * min(len(c["title"]), 60), c["url"], ""]
        for u in c["units"]:
            lines += [u["src"], "", u["en"], "", ""]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def x(s):
    return html.escape(s, quote=True)


def write_tei(w, chs, path):
    be = w.get("base_edition", {})
    lic = w.get("licence", {})
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<TEI xmlns="http://www.tei-c.org/ns/1.0">', "<teiHeader><fileDesc>",
           f"<titleStmt><title>{x(plain(w['title']))}</title>",
           f"<author>{x(re.sub(r'\s*\(.*\)$', '', w.get('author') or ''))}</author>",
           '<editor>Ezra Brand</editor></titleStmt>',
           '<publicationStmt><publisher>Open Seforim</publisher>',
           f'<pubPlace>{x(w["url"])}</pubPlace>',
           f'<availability><licence target="{x(lic.get("url", ""))}">{x(lic.get("name", ""))}</licence></availability>',
           "</publicationStmt>",
           f'<sourceDesc><bibl>{x(be.get("label", ""))}' + (f' <ref target="{x(be["scan_url"])}">scans</ref>' if be.get("scan_url") else "") + "</bibl></sourceDesc>",
           "</fileDesc>",
           f"<encodingDesc><p>{x(w.get('method', ''))} Each source segment (ab) is followed by its English translation "
           "(ab type=\"translation\", corresp).</p></encodingDesc>",
           "</teiHeader>", "<text><body>"]
    n = 0
    for ci, c in enumerate(chs, 1):
        out.append(f'<div type="chapter" n="{ci}" facs="{x(c["url"])}"><head>{x(c["title"])}</head>')
        for u in c["units"]:
            n += 1
            out.append(f'<ab xml:id="s{n}" xml:lang="{u["lang"]}">{x(u["src"])}</ab>')
            out.append(f'<ab type="translation" xml:lang="en" corresp="#s{n}">{x(u["en"])}</ab>')
        out.append("</div>")
    out += ["</body></text>", "</TEI>"]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


EPUB_CSS = """body{font-family:serif;line-height:1.5}
h1{font-size:1.4em}.src{margin:1em 0 .2em}.src[dir=rtl]{text-align:right;font-size:1.1em}
.en{margin:0 0 1em;color:#333}.note{font-size:.85em;color:#555}"""


def xhtml(title, body, lang="en"):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE html>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}" xml:lang="{lang}">'
            f'<head><meta charset="UTF-8"/><title>{x(title)}</title><link rel="stylesheet" href="style.css"/></head>'
            f"<body>{body}</body></html>\n")


def para(s):
    return "<br/>".join(x(line) for line in s.split("\n"))


LANG_NAMES = {"he": "Hebrew", "la": "Latin", "de": "German", "syr": "Syriac", "ar": "Arabic"}


def author_name(w):
    return re.sub(r"\s*\(.*\)$", "", w.get("author") or "")


def file_as(name):
    """'Jacob Emden' -> 'Emden, Jacob'; longer names ('Immanuel of Rome', "Azariah de' Rossi") stay as they are."""
    parts = name.split()
    return f"{parts[-1]}, {parts[0]}" if len(parts) == 2 else name


def book_title(w):
    """The book's own title, without the author: 'Jacob Emden, *Megillat Sefer*' -> 'Megillat Sefer'."""
    t = plain(w["title"])
    return t.split(", ", 1)[1] if ", " in t else t


def sub_title(chs):
    langs = [u["lang"] for c in chs for u in c["units"]]
    main = max(set(langs), key=langs.count) if langs else "he"
    return f"{LANG_NAMES.get(main, 'Source')} text and English translation"


def file_base(w):
    """Descriptive, URL-safe file name: 'jacob-emden-megillat-sefer'."""
    import unicodedata
    t = plain(w["title"])
    for a, b in (("ö", "oe"), ("ü", "ue"), ("ä", "ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("Ä", "Ae")):
        t = t.replace(a, b)  # German convention: Löw -> Loew
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def make_cover(w, main_title, subtitle, author):
    """A simple typographic cover (1600 x 2400 PNG), in the site's colours."""
    import io
    from PIL import Image, ImageDraw, ImageFont, features
    F = Path(r"C:\Windows\Fonts")
    W, H = 1600, 2400
    bg, fg, muted, accent = "#f3ead6", "#2b2116", "#6f5f48", "#7a4b12"
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 36], fill=accent); d.rectangle([0, H - 36, W, H], fill=accent)
    d.rectangle([90, 90, W - 90, H - 90], outline="#d8c7a4", width=4)

    def font(name, size):
        return ImageFont.truetype(str(F / name), size)

    def wrap(text, f, width):
        lines, cur = [], ""
        for word in text.split():
            t = (cur + " " + word).strip()
            if d.textlength(t, font=f) <= width or not cur:
                cur = t
            else:
                lines.append(cur); cur = word
        return lines + ([cur] if cur else [])

    def centered(lines, f, y, fill, gap=1.18):
        for ln in lines:
            wdt = d.textlength(ln, font=f)
            d.text(((W - wdt) / 2, y), ln, font=f, fill=fill)
            y += int(f.size * gap)
        return y

    y = 420
    if author:
        y = centered([author], font("georgia.ttf", 78), y, muted) + 70
    tf = font("georgiab.ttf", 150 if len(main_title) < 18 else 118)
    y = centered(wrap(main_title, tf, W - 320), tf, y, fg) + 40
    he = w.get("title_he")
    if he:
        hf = font("FRANKB.TTF", 110)
        txt = he if features.check("raqm") else he[::-1]  # without libraqm Pillow does not reorder right-to-left text
        if features.check("raqm"):
            wdt = d.textlength(txt, font=hf, direction="rtl"); d.text(((W - wdt) / 2, y), txt, font=hf, fill=accent, direction="rtl")
        else:
            wdt = d.textlength(txt, font=hf); d.text(((W - wdt) / 2, y), txt, font=hf, fill=accent)
        y += 170
    d.line([(W / 2 - 160, y + 20), (W / 2 + 160, y + 20)], fill=accent, width=4)
    y = centered(wrap(subtitle, font("georgiai.ttf", 70), W - 360), font("georgiai.ttf", 70), y + 80, fg)
    ed = "Edited by Ezra Brand"
    centered([ed], font("georgia.ttf", 58), H - 520, muted)
    centered(["Open Seforim"], font("georgiab.ttf", 72), H - 360, accent)
    centered(["openseforim.org"], font("georgia.ttf", 48), H - 270, muted)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def write_epub(w, chs, path, slug):
    title = plain(w["title"])
    files = {}
    files["OEBPS/style.css"] = EPUB_CSS
    lic = w.get("licence", {})
    files["OEBPS/title.xhtml"] = xhtml(title, f"<h1>{x(title)}</h1><p>{x(plain(w.get('summary', '')))}</p>"
                                       f"<p class=\"note\">Source text: {x(w.get('base_edition', {}).get('label', ''))}.<br/>"
                                       f"{x(w.get('method', ''))}<br/>Licence: {x(lic.get('name', ''))}.<br/>"
                                       f"Open Seforim · {x(w['url'])}</p>")
    for i, c in enumerate(chs, 1):
        parts = [f"<h1>{x(c['title'])}</h1>"]
        for u in c["units"]:
            rtl = ' dir="rtl"' if u["lang"] in ("he", "syr", "ar") else ""
            parts.append(f'<p class="src" lang="{u["lang"]}"{rtl}>{para(u["src"])}</p><p class="en">{para(u["en"])}</p>')
        files[f"OEBPS/c{i:04d}.xhtml"] = xhtml(c["title"], "".join(parts))
    nav = "".join(f'<li><a href="c{i:04d}.xhtml">{x(c["title"])}</a></li>' for i, c in enumerate(chs, 1))
    files["OEBPS/nav.xhtml"] = xhtml("Contents", f'<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>'
                                     f'<li><a href="title.xhtml">{x(title)}</a></li>{nav}</ol></nav>')
    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="css" href="style.css" media-type="text/css"/>',
                '<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>']
    spine = ['<itemref idref="title"/>']
    for i in range(1, len(chs) + 1):
        manifest.append(f'<item id="c{i}" href="c{i:04d}.xhtml" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="c{i}"/>')
    author = author_name(w)
    main_title, subtitle = book_title(w), sub_title(chs)
    # cover: an image, and a cover page first in the reading order
    files["OEBPS/cover.png"] = make_cover(w, main_title, subtitle, author)
    files["OEBPS/cover.xhtml"] = xhtml(main_title, '<div style="text-align:center;margin:0;padding:0">'
                                       f'<img src="cover.png" alt="{x(main_title)}" style="max-width:100%;max-height:100vh"/></div>')
    manifest += ['<item id="cover-image" href="cover.png" media-type="image/png" properties="cover-image"/>',
                 '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>']
    spine.insert(0, '<itemref idref="cover"/>')
    be = w.get("base_edition", {}).get("label", "")
    files["OEBPS/content.opf"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="en">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f'<dc:identifier id="uid">{x(w.get("doi") and "doi:" + w["doi"] or w["url"])}</dc:identifier>'
        f'<dc:title id="t1">{x(main_title)}</dc:title><meta refines="#t1" property="title-type">main</meta>'
        f'<dc:title id="t2">{x(subtitle)}</dc:title><meta refines="#t2" property="title-type">subtitle</meta>'
        + (f'<dc:creator id="aut">{x(author)}</dc:creator><meta refines="#aut" property="role" scheme="marc:relators">aut</meta>'
           f'<meta refines="#aut" property="file-as">{x(file_as(author))}</meta>' if author else "") +
        '<dc:contributor id="edt">Ezra Brand</dc:contributor><meta refines="#edt" property="role" scheme="marc:relators">edt</meta>'
        '<meta refines="#edt" property="file-as">Brand, Ezra</meta>'
        '<dc:publisher>Open Seforim</dc:publisher><dc:language>en</dc:language><dc:date>2026</dc:date>'
        f'<dc:description>{x(plain(w.get("summary", "")))}</dc:description>'
        + (f"<dc:source>{x(be)}</dc:source>" if be else "") +
        f'<dc:rights>{x(lic.get("name", ""))}</dc:rights><meta name="cover" content="cover-image"/>'
        '<meta property="dcterms:modified">2026-01-01T00:00:00Z</meta>'
        f'</metadata><manifest>{"".join(manifest)}</manifest><spine>{"".join(spine)}</spine></package>\n')
    files["META-INF/container.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<container version="1.0" '
                                       'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
                                       '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
                                       '</rootfiles></container>\n')

    def info(name, compress):
        zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
        zi.external_attr = 0o644 << 16
        return zi
    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w") as z:
        z.writestr(info("mimetype", False), "application/epub+zip")
        for name in sorted(files):
            data = files[name]
            z.writestr(info(name, not name.endswith(".png")), data if isinstance(data, bytes) else data.encode("utf-8"))
    if path.exists() and path.read_bytes() == tmp.read_bytes():
        tmp.unlink()
    else:
        tmp.replace(path)


def main():
    slug, site, out = sys.argv[1], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
    w = json.loads((site / "work.json").read_text(encoding="utf-8"))
    chs = collect(slug, site)
    if not chs:
        print(f"export {slug}: no text units found", flush=True)
        return
    out.mkdir(parents=True, exist_ok=True)
    base = file_base(w)
    for old in out.glob("*"):
        if old.is_file() and not old.name.startswith(base + "."):
            old.unlink()  # files under an earlier name
    write_txt(w, chs, out / f"{base}.txt")
    write_tei(w, chs, out / f"{base}.tei.xml")
    write_epub(w, chs, out / f"{base}.epub", slug)
    n = sum(len(c["units"]) for c in chs)
    sizes = ", ".join(f"{p.name} {p.stat().st_size // 1024} KB" for p in sorted(out.glob(f"{base}.*")))
    print(f"export {slug}: {len(chs)} chapters, {n} units; {sizes}", flush=True)


if __name__ == "__main__":
    main()
