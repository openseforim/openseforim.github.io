"""Build the openseforim.org landing page, sitemap.xml and robots.txt from the readers' work.json files.

py -3.13 build.py   (run from this folder; the reader clones are siblings in ..\\)
Add a line to WORKS when a repo moves into the org. Rerun after a reader adds pages or changes work.json.
"""
import html, json, re, sys
from datetime import date
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
# slug: (local folder, Pages source folder inside it)
WORKS = {
    "emden": ("emden-megillat-sefer", "docs"),
    "hyman": ("hyman-toldot", "."),
    "immanuel": ("immanuel-mahberot", "docs"),
    "meor-einayim": ("meor-einayim", "docs"),
    "bochart": ("bochart-hierozoicon", "docs"),
    "lewysohn": ("lewysohn-zoologie", "docs"),
    "loew": ("low-flora", "docs"),
    "barhebraeus": ("barhebraeus-chronography", "docs"),
    "defus": ("defus", "."),
}
SECTIONS = [("translation", "Translations"), ("source", "Source texts"), ("catalogue", "Catalogue")]
SKIP_PARTS = {"pipeline", "node_modules", ".git", "scans"}
e = html.escape


def load():
    works = []
    for slug, (folder, src) in WORKS.items():
        base = ROOT / folder / src
        w = json.loads((base / "work.json").read_text(encoding="utf-8"))
        assert w["slug"] == slug, (slug, w["slug"])
        w["_base"] = base
        works.append(w)
    return sorted(works, key=lambda w: w.get("order", 999))


def ital(s):
    """Escape, then show *Book Title* in italics (work.json marks titles with asterisks)."""
    return re.sub(r"\*(.+?)\*", r"<i>\1</i>", e(s))


def card(w):
    """One row: plain-text title (selectable, copyable), Hebrew title, summary, status, and a separate link."""
    he = f'\n        <div class="he" lang="he" dir="rtl">{e(w["title_he"])}</div>' if w.get("title_he") else ""
    badge = f'<span class="badge">{e(w["status_label"])}</span>' if w.get("status_label") else ""
    return f'''    <article class="work">
      <div class="work-main">
        <h3>{ital(w["title"])}</h3>{he}
        <p>{ital(w.get("summary", ""))}</p>
      </div>
      <div class="work-side">{badge}<a class="open" href="/{w["slug"]}/">Open<span class="vh"> {e(re.sub(r"[*]", "", w["title"]))}</span> →</a></div>
    </article>'''


def landing(works):
    parts = []
    for kind, label in SECTIONS:
        ws = [w for w in works if w.get("kind") == kind]
        if ws:
            parts.append(f'  <h2 class="sect">{label}</h2>\n  <section class="works">\n'
                         + "\n".join(card(w) for w in ws) + "\n  </section>")
    sections = "\n".join(parts)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Open Seforim</title>
<meta name="description" content="Open readers for Hebrew and Judaica texts: source text, page scans and English translation side by side.">
<meta property="og:title" content="Open Seforim"><meta property="og:type" content="website">
<link rel="canonical" href="https://openseforim.org/">
<script>var osT=localStorage.getItem('os-theme');osT&&osT!='auto'&&document.documentElement.setAttribute('data-theme',osT)</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:ital,wght@0,400;0,600;1,400&family=Noto+Serif+Hebrew:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/os.css">
<script src="/assets/os.js" defer></script>
</head><body class="os-landing">
<main class="wrap" id="works">
  <section class="hero">
    <h1><img class="logo" src="/apple-touch-icon.png" alt="" width="40" height="40">Open Seforim</h1>
    <p>Open readers for Hebrew and Judaica texts. Each work gives the source text, links to the page scans, and an English translation, with its sources and method stated. <a href="/about/">How the editions are made →</a></p>
  </section>
{sections}
</main>
<footer class="os-foot"><div class="os-foot-in"><div class="os-brand"><p>Open Seforim — open readers for Hebrew and Judaica texts, by Ezra Brand · <a href="/about/">About</a> · <a href="https://www.ezrabrand.com/">ezrabrand.com</a> · <a href="https://github.com/openseforim">GitHub</a></p></div></div></footer>
</body></html>
'''


def sitemap(works):
    urls = ["https://openseforim.org/", "https://openseforim.org/about/"]
    for w in works:
        base = w["_base"]
        pages = sorted(p for p in base.rglob("*.html")
                       if not SKIP_PARTS & set(p.relative_to(base).parts) and p.name != "404.html")
        for p in pages:
            rel = p.relative_to(base).as_posix()
            rel = "" if rel == "index.html" else rel.removesuffix("index.html")
            urls.append(f"https://openseforim.org/{w['slug']}/{rel}")
        print(f"{w['slug']}: {len(pages)} pages", flush=True)
    today = date.today().isoformat()
    body = "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
    (HERE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + body + "</urlset>\n", encoding="utf-8")
    (HERE / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://openseforim.org/sitemap.xml\n",
                                     encoding="utf-8")
    print(f"sitemap.xml: {len(urls)} URLs", flush=True)


if __name__ == "__main__":
    ws = load()
    (HERE / "index.html").write_text(landing(ws), encoding="utf-8")
    (HERE / "works.json").write_text(json.dumps([{k: v for k, v in w.items() if not k.startswith("_")} for w in ws],
                                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"index.html: {len(ws)} works", flush=True)
    import subprocess
    # downloads: plain text, TEI and EPUB of every text work (tools/export.py), in downloads/<slug>/
    if "--no-export" not in sys.argv:
        for w in ws:
            if w.get("kind") != "catalogue":
                subprocess.run([sys.executable, str(HERE / "tools" / "export.py"), w["slug"], str(w["_base"]),
                                str(HERE / "downloads" / w["slug"])], check=True)
    order = {"txt": 0, "xml": 1, "epub": 2}
    downloads = {w["slug"]: sorted((p.name for p in (HERE / "downloads" / w["slug"]).glob("*.*")),
                                   key=lambda n: order.get(n.rsplit(".", 1)[1], 9))
                 for w in ws if (HERE / "downloads" / w["slug"]).is_dir()}
    # short titles for the strip, and the download files, for os.js (shown at once, before work.json loads)
    js = HERE / "assets" / "os.js"
    titles = json.dumps({w["slug"]: w.get("short_title", w["title"]) for w in ws}, ensure_ascii=False)  # *...* = italics, rendered by os.js
    t = js.read_text(encoding="utf-8")
    t = re.sub(r"/\*TITLES\*/.*?/\*END\*/", lambda m: "/*TITLES*/" + titles + "/*END*/", t, flags=re.S)
    t = re.sub(r"/\*DOWNLOADS\*/.*?/\*END\*/", lambda m: "/*DOWNLOADS*/" + json.dumps(downloads) + "/*END*/", t, flags=re.S)
    js.write_text(t, encoding="utf-8")
    sitemap(ws)
    subprocess.run([sys.executable, str(HERE / "tools" / "postbuild.py"), "", str(HERE)], check=True)
