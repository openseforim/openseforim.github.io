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
    author = re.sub(r"\s*\(.*\)$", "", w.get("author") or "")
    files["OEBPS/content.opf"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="en">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f'<dc:identifier id="uid">{x(w["url"])}</dc:identifier><dc:title>{x(title)}</dc:title>'
        + (f"<dc:creator>{x(author)}</dc:creator>" if author else "") +
        '<dc:contributor>Ezra Brand</dc:contributor><dc:publisher>Open Seforim</dc:publisher><dc:language>en</dc:language>'
        f'<dc:rights>{x(lic.get("name", ""))}</dc:rights><meta property="dcterms:modified">2026-01-01T00:00:00Z</meta>'
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
            z.writestr(info(name, True), files[name].encode("utf-8"))
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
    write_txt(w, chs, out / f"{slug}.txt")
    write_tei(w, chs, out / f"{slug}.tei.xml")
    write_epub(w, chs, out / f"{slug}.epub", slug)
    n = sum(len(c["units"]) for c in chs)
    sizes = ", ".join(f"{p.suffix[1:] if p.suffix != '.xml' else 'tei'} {p.stat().st_size // 1024} KB"
                      for p in sorted(out.glob(f"{slug}.*")))
    print(f"export {slug}: {len(chs)} chapters, {n} units; {sizes}", flush=True)


if __name__ == "__main__":
    main()
