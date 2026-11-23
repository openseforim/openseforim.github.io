"""Open Seforim post-build pass for a work's built pages. Standard library only; safe to run again.

py -3.13 tools/postbuild.py <slug> <site_dir>      (slug "" for the org site root)

For each HTML page under site_dir it:
  - writes one marked block before </head> (<!--os:seo--> ... <!--/os:seo-->) with the canonical URL,
    Open Graph / Twitter tags, the site icons and, on the work's home page, JSON-LD from work.json;
  - adds a meta description when the page has none (from the first English paragraph);
  - adds lang="he" / "syr" / "ar" to right-to-left elements that have no lang attribute;
  - adds ?v=<hash> to local .css/.js links that have no version, so browsers fetch new files after a deploy.
Every reader's build script calls this at its end.
"""
import hashlib, html, json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SITE = "https://openseforim.org"
OG_IMAGE = SITE + "/assets/og.png"
SKIP_DIRS = {"pipeline", "node_modules", ".git", "scans", "data", ".venv"}
BLOCK = re.compile(r"\n?<!--os:seo-->.*?<!--/os:seo-->\n?", re.S)
# applies the saved text size and Hebrew font before the page paints; keys and fonts match assets/os.js
# (Bochart's old 'bh-size' choice is taken over once)
EARLY = ("<script>(function(){try{var d=document.documentElement,L=localStorage,s=L.getItem('os-size'),"
         "h=L.getItem('os-he'),b=L.getItem('bh-size');if(s===null&&b){s=b;L.setItem('os-size',b)}"
         "if(s)d.setAttribute('data-os-size',s);"
         "var F={frank:'Frank+Ruhl+Libre:wght@400;600',david:'David+Libre:wght@400;500'};"
         "if(h){d.setAttribute('data-os-he',h);if(F[h]){var l=document.createElement('link');l.rel='stylesheet';"
         "l.setAttribute('data-os-font',F[h]);l.href='https://fonts.googleapis.com/css2?family='+F[h]+'&display=swap';"
         "document.head.appendChild(l)}}}catch(e){}})()</script>")

HE = re.compile(r"[֐-׿]")
SYR = re.compile(r"[܀-ݏ]")
AR = re.compile(r"[؀-ۿ]")
LATIN = re.compile(r"[A-Za-z]")


def esc(s):
    return html.escape(s, quote=True)


def text_of(fragment):
    fragment = re.sub(r"(?is)<(script|style|nav|header|footer|select|form|button|sup)\b.*?</\1>", " ", fragment)
    fragment = re.sub(r"(?s)<[^>]+>", "\n", fragment)
    return html.unescape(fragment)


def first_english(body):
    """First stretch of English prose after the h1, for a meta description."""
    start = body.find("</h1>")
    t = text_of(body[start + 5:] if start >= 0 else body)
    for chunk in re.split(r"\n\s*\n|\n", t):
        c = " ".join(chunk.split())
        if len(c) < 60:
            continue
        letters = [ch for ch in c if ch.isalpha()]
        if not letters or sum(1 for ch in letters if LATIN.match(ch)) / len(letters) < 0.85:
            continue
        if len(c) > 158:
            c = c[:155].rsplit(" ", 1)[0].rstrip(",;:—-·– ") + "…"
        return c.rstrip(",;:—-·– ")
    return ""


def meta(attr, key, value):
    return f'<meta {attr}="{key}" content="{esc(value)}">'


def stamp(m, base):
    attr, url = m.group(1), m.group(2)
    if "?" in url or url.startswith(("http", "//", "/", "data:")):
        return m.group(0)
    f = base / url
    if not f.is_file():
        return m.group(0)
    h = hashlib.md5(f.read_bytes()).hexdigest()[:8]
    return f'{attr}="{url}?v={h}"'


def add_lang(m):
    tag, attrs, after = m.group(1), m.group(2), m.group(3)
    if re.search(r"\blang=", attrs):
        return m.group(0)
    sample = after[:200]
    lang = "he" if HE.search(sample) else "syr" if SYR.search(sample) else "ar" if AR.search(sample) else None
    if not lang:
        return m.group(0)
    return f"<{tag}{attrs} lang=\"{lang}\">{after}"


def jsonld(work, url):
    d = {"@context": "https://schema.org", "@type": "Book", "name": work["title"].replace("*", ""), "url": url,
         "publisher": {"@type": "Organization", "name": "Open Seforim", "url": SITE + "/"},
         "editor": {"@type": "Person", "name": "Ezra Brand"},
         "isAccessibleForFree": True}
    if work.get("author"):
        d["author"] = {"@type": "Person", "name": re.sub(r"\s*\(.*\)$", "", work["author"])}
    if work.get("summary"):
        d["description"] = work["summary"].replace("*", "")
    if work.get("licence", {}).get("url"):
        d["license"] = work["licence"]["url"]
    if work.get("base_edition"):
        b = {"@type": "Book", "name": work["base_edition"]["label"]}
        if work["base_edition"].get("scan_url"):
            b["url"] = work["base_edition"]["scan_url"]
        d["isBasedOn"] = b
    if work.get("kind") == "catalogue":
        d["@type"] = "Dataset"
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>"


def site_jsonld():
    d = {"@context": "https://schema.org", "@type": "WebSite", "name": "Open Seforim", "url": SITE + "/",
         "description": "Open readers for Hebrew and Judaica texts: source text, page scans and English translation side by side.",
         "publisher": {"@type": "Person", "name": "Ezra Brand", "url": "https://www.ezrabrand.com/"}}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>"


def process(page, root, slug, work):
    t = page.read_text(encoding="utf-8")
    if "</head>" not in t:
        return False
    orig = t
    t = BLOCK.sub("\n", t, count=1)
    rel = page.relative_to(root).as_posix()
    path = rel[:-len("index.html")] if rel.endswith("index.html") else rel
    url = f"{SITE}/{slug + '/' if slug else ''}{path}"
    head, body = t.split("</head>", 1)

    title_m = re.search(r"(?is)<title>(.*?)</title>", head)
    title = html.unescape(" ".join(title_m.group(1).split())) if title_m else "Open Seforim"
    desc_m = re.search(r'(?is)<meta\s+name="description"\s+content="([^"]*)"', head)
    desc = html.unescape(desc_m.group(1)) if desc_m else ""
    tags = []
    if not desc:
        desc = first_english(body) or (work or {}).get("summary", "").replace("*", "")
        if desc:
            tags.append(meta("name", "description", desc))
    if not re.search(r'rel="canonical"', head):
        tags.append(f'<link rel="canonical" href="{esc(url)}">')
    is_home = rel == "index.html"
    have = set(re.findall(r'<meta\s+(?:property|name)="((?:og|twitter):[a-z:_]+)"', head))
    og = {"og:title": title, "og:description": desc, "og:url": url, "og:type": "website" if is_home else "article",
          "og:site_name": "Open Seforim", "og:image": OG_IMAGE, "og:image:width": "1200", "og:image:height": "630"}
    for k, v in og.items():
        if k not in have and v:
            tags.append(meta("property", k, v))
    if "twitter:card" not in have:
        tags.append(meta("name", "twitter:card", "summary_large_image"))
    if not re.search(r'rel="(?:shortcut )?icon"', head):
        tags.append('<link rel="icon" href="/favicon.svg" type="image/svg+xml">')
        tags.append('<link rel="icon" href="/favicon.ico" sizes="any">')
        tags.append('<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
    # Google Scholar (Highwire Press) tags, so the editions can be found and cited as scholarly works
    if work and "citation_title" not in head:
        wt = work["title"].replace("*", "")
        h1m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", body)
        h1t = " ".join(html.unescape(re.sub(r"(?s)<span class=\"sub\">.*?</span>|<[^>]+>", " ", h1m.group(1))).split()) if h1m else ""
        ctitle = wt if is_home or not h1t or h1t == wt else f"{wt}: {h1t}"
        tags.append(meta("name", "citation_title", ctitle))
        if work.get("author"):
            tags.append(meta("name", "citation_author", re.sub(r"\s*\(.*\)$", "", work["author"])))
        tags.append(meta("name", "citation_author", "Brand, Ezra"))
        tags.append(meta("name", "citation_publication_date", "2026"))
        tags.append(meta("name", "citation_publisher", "Open Seforim"))
        tags.append(meta("name", "citation_language", "en"))
        tags.append(meta("name", "citation_public_url", url))
        if work.get("doi"):
            tags.append(meta("name", "citation_doi", work["doi"]))
    if is_home and 'application/ld+json' not in head:
        tags.append(jsonld(work, url) if work else site_jsonld() if not slug else "")
    # shared reading type (assets/os.css): the body face for pages that do not load it, and the reader's
    # text size and Hebrew font choice applied before the page paints (os.js changes them later)
    if "os-own-palette" not in t[:t.find("<head")]:
        if "Noto+Serif:" not in head:
            tags.insert(0, '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif:ital,wght@0,400;0,600;1,400'
                           '&family=Noto+Serif+Hebrew:wght@400;600&display=swap">')
        tags.insert(0, EARLY)
    block = "<!--os:seo-->\n" + "\n".join(x for x in tags if x) + "\n<!--/os:seo-->\n"

    head = re.sub(r'(href|src)="([^"]+\.(?:css|js))"', lambda m: stamp(m, page.parent), head)
    body = re.sub(r'(src)="([^"]+\.js)"', lambda m: stamp(m, page.parent), body)
    body = re.sub(r"<(\w+)((?:\s[^<>]*?)?\sdir=[\"']rtl[\"'][^<>]*?)>([^<]{0,200})", add_lang, body)
    body = re.sub(r'<(\w+)((?:\s[^<>]*?)?\sclass="(?:[^"]*\s)?he(?:\s[^"]*)?"[^<>]*?)>([^<]{0,200})', add_lang, body)
    t = head.rstrip("\n") + "\n" + block + "</head>" + body
    if t != orig:
        page.write_text(t, encoding="utf-8")
        return True
    return False


def main():
    slug, root = sys.argv[1].strip("/"), Path(sys.argv[2]).resolve()
    wj = root / "work.json"
    work = json.loads(wj.read_text(encoding="utf-8")) if wj.exists() else None
    pages = [p for p in root.rglob("*.html")
             if not SKIP_DIRS & set(p.relative_to(root).parts[:-1]) and p.name != "404.html"]
    changed = sum(process(p, root, slug, work) for p in sorted(pages))
    print(f"postbuild {slug or '(root)'}: {changed}/{len(pages)} pages updated", flush=True)


if __name__ == "__main__":
    main()
