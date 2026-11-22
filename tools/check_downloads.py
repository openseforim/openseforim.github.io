"""Check every file in downloads/: EPUB (main epubcheck rules), TEI (well-formed, header, ids, links), plain text.

py -3.13 tools/check_downloads.py      -> prints one line per file, then the problems; exit code 1 if any
"""
import posixpath, re, sys, zipfile
from pathlib import Path
from urllib.parse import unquote, urldefrag
from lxml import etree

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent.parent
NS = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/",
      "x": "http://www.w3.org/1999/xhtml", "c": "urn:oasis:names:tc:opendocument:xmlns:container",
      "ops": "http://www.idpf.org/2007/ops", "tei": "http://www.tei-c.org/ns/1.0"}
XMLID = "{http://www.w3.org/XML/1998/namespace}id"
STRICT = etree.XMLParser(resolve_entities=False, no_network=True, recover=False, huge_tree=True)
problems = []


def bad(f, msg):
    problems.append(f"{f.parent.name}/{f.name}: {msg}")


def check_epub(f):
    z = zipfile.ZipFile(f)
    infos = z.infolist()
    if infos[0].filename != "mimetype" or infos[0].compress_type != zipfile.ZIP_STORED or infos[0].extra:
        bad(f, "mimetype is not the first, uncompressed entry without extra field")
    if z.read("mimetype") != b"application/epub+zip":
        bad(f, "wrong mimetype content")
    names = set(z.namelist())
    cont = etree.fromstring(z.read("META-INF/container.xml"), STRICT)
    opf_path = cont.find(".//c:rootfile", NS).get("full-path")
    opf = etree.fromstring(z.read(opf_path), STRICT)
    base = posixpath.dirname(opf_path)
    if opf.get("version") != "3.0":
        bad(f, "package version is not 3.0")
    uid = opf.get("unique-identifier")
    if opf.find(f".//dc:identifier[@id='{uid}']", NS) is None:
        bad(f, "unique-identifier does not point to a dc:identifier")
    for tag in ("title", "language"):
        if opf.find(f".//dc:{tag}", NS) is None:
            bad(f, f"no dc:{tag}")
    mod = opf.find(".//opf:meta[@property='dcterms:modified']", NS)
    if mod is None or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", mod.text or ""):
        bad(f, "dcterms:modified missing or badly formed")
    ids = {e.get("id") for e in opf.iter() if e.get("id")}
    for m in opf.findall(".//opf:meta[@refines]", NS):
        if m.get("refines")[1:] not in ids:
            bad(f, f"meta refines a missing id {m.get('refines')}")
    items = opf.findall(".//opf:manifest/opf:item", NS)
    man_ids = [i.get("id") for i in items]
    if len(man_ids) != len(set(man_ids)):
        bad(f, "duplicate manifest ids")
    hrefs = {}
    for i in items:
        p = posixpath.normpath(posixpath.join(base, i.get("href")))
        hrefs[p] = i
        if p not in names:
            bad(f, f"manifest item missing from the zip: {p}")
    for n in names:
        if n not in hrefs and n != "mimetype" and not n.startswith("META-INF/") and n != opf_path:
            bad(f, f"file in zip but not in manifest: {n}")
    props = [i.get("properties", "") for i in items]
    if sum("nav" in p.split() for p in props) != 1:
        bad(f, "there must be exactly one nav item")
    if sum("cover-image" in p.split() for p in props) != 1:
        bad(f, "no cover-image item")
    spine = opf.findall(".//opf:spine/opf:itemref", NS)
    for r in spine:
        if r.get("idref") not in man_ids:
            bad(f, f"spine itemref to a missing id {r.get('idref')}")
    # every XHTML document: well-formed, namespaced, titled, links and images resolve
    targets = {}
    docs = [p for p, i in hrefs.items() if i.get("media-type") == "application/xhtml+xml"]
    parsed = {}
    for p in docs:
        try:
            parsed[p] = etree.fromstring(z.read(p), STRICT)
        except etree.XMLSyntaxError as e:
            bad(f, f"{p} is not well-formed: {e}")
            continue
        root = parsed[p]
        if root.tag != "{http://www.w3.org/1999/xhtml}html":
            bad(f, f"{p}: root is not XHTML html")
        if root.find(".//x:head/x:title", NS) is None or not (root.find(".//x:head/x:title", NS).text or "").strip():
            bad(f, f"{p}: no title")
        targets[p] = {e.get("id") for e in root.iter() if e.get("id")}
    for p, root in parsed.items():
        d = posixpath.dirname(p)
        for a in root.iter("{http://www.w3.org/1999/xhtml}a", "{http://www.w3.org/1999/xhtml}img",
                           "{http://www.w3.org/1999/xhtml}link"):
            ref = a.get("href") or a.get("src")
            if not ref or re.match(r"^[a-z]+:", ref):
                continue
            path, frag = urldefrag(ref)
            tp = posixpath.normpath(posixpath.join(d, unquote(path))) if path else p
            if tp not in names:
                bad(f, f"{p}: link to a missing file {ref}")
            elif frag and tp in targets and frag not in targets[tp]:
                bad(f, f"{p}: link to a missing fragment {ref}")
    navp = next(p for p, i in hrefs.items() if "nav" in i.get("properties", "").split())
    if navp in parsed and parsed[navp].find(".//x:nav[@ops:type='toc']", NS) is None:
        bad(f, "nav document has no epub:type=toc nav")
    return f"{len(docs)} documents, {len(spine)} in spine"


def check_tei(f):
    try:
        t = etree.parse(str(f), STRICT).getroot()
    except etree.XMLSyntaxError as e:
        bad(f, f"not well-formed: {e}"); return "not well-formed"
    if t.tag != "{http://www.tei-c.org/ns/1.0}TEI":
        bad(f, "root is not tei:TEI")
    for path in ("tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title", "tei:teiHeader/tei:fileDesc/tei:publicationStmt",
                 "tei:teiHeader/tei:fileDesc/tei:sourceDesc", "tei:text/tei:body"):
        if t.find(path, NS) is None:
            bad(f, f"missing {path}")
    ids = [e.get(XMLID) for e in t.iter() if e.get(XMLID)]
    if len(ids) != len(set(ids)):
        bad(f, "duplicate xml:id")
    idset = set(ids)
    abs_ = t.findall(".//tei:ab", NS)
    src = [a for a in abs_ if a.get("type") != "translation"]
    tr = [a for a in abs_ if a.get("type") == "translation"]
    if len(src) != len(tr):
        bad(f, f"{len(src)} source segments but {len(tr)} translations")
    for a in tr:
        if a.get("corresp", "#")[1:] not in idset:
            bad(f, f"translation points to a missing id {a.get('corresp')}"); break
    empty_src = sum(1 for a in src if not (a.text or "").strip())
    # an empty translation is right only when the source has no letters (OCR fragments such as ":" or "0")
    by_id = {a.get(XMLID): a for a in src}
    empty_en = sum(1 for a in tr if not (a.text or "").strip()
                   and any(ch.isalpha() for ch in (by_id.get(a.get("corresp", "#")[1:]).text or "")))
    if empty_src or empty_en:
        bad(f, f"empty segments: {empty_src} source, {empty_en} English")
    divs = t.findall(".//tei:body/tei:div", NS)
    if any(d.find("tei:head", NS) is None for d in divs):
        bad(f, "a chapter div without head")
    return f"{len(divs)} chapters, {len(src)} segment pairs"


def check_txt(f):
    raw = f.read_bytes()
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        bad(f, f"not UTF-8: {e}"); return "not UTF-8"
    if "\ufffd" in t:
        bad(f, "contains U+FFFD replacement characters")
    tags = re.findall(r"</?(?:div|span|p|a|i|b|em|strong|br|sup|table|td|tr)\b[^>]*>", t)
    if tags:
        bad(f, f"{len(tags)} HTML tags left, e.g. {tags[0]!r}")
    ents = re.findall(r"&(?:amp|lt|gt|quot|nbsp|#\d+|#x[0-9a-f]+);", t)
    if ents:
        bad(f, f"{len(ents)} HTML entities left, e.g. {ents[0]!r}")
    for junk in ("Report a mistake", "report a mistake", "Copy citation", "HebrewBooks scan", "Suggest a correction"):
        if junk in t:
            bad(f, f"interface text left: {junk!r}")
    return f"{t.count(chr(10)):,} lines"


for f in sorted((HERE / "downloads").glob("*/*")):
    kind = "epub" if f.suffix == ".epub" else "tei" if f.name.endswith(".tei.xml") else "txt"
    try:
        info = {"epub": check_epub, "tei": check_tei, "txt": check_txt}[kind](f)
    except Exception as e:  # noqa: BLE001
        bad(f, f"checker error {type(e).__name__}: {e}"); info = "error"
    print(f"{f.parent.name}/{f.name}: {info}", flush=True)

print(f"\n{len(problems)} problems")
for p in problems[:80]:
    print(" -", p)
sys.exit(1 if problems else 0)
