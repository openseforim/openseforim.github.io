"""Write sitemap.xml for openseforim.org from the local clones of the org's reader repos.

py -3.13 build_sitemap.py   (run from this folder; clones are siblings in ..\\)
Add a line to WORKS when a repo moves into the org.
"""
import sys
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
SKIP_PARTS = {"pipeline", "node_modules", ".git", "scans"}

urls = ["https://openseforim.org/"]
for slug, (folder, src) in WORKS.items():
    base = ROOT / folder / src
    if not base.exists():
        print(f"missing: {base}", flush=True)
        continue
    pages = sorted(p for p in base.rglob("*.html")
                   if not SKIP_PARTS & set(p.relative_to(base).parts) and p.name != "404.html")
    for p in pages:
        rel = p.relative_to(base).as_posix()
        rel = "" if rel == "index.html" else rel.removesuffix("index.html")
        urls.append(f"https://openseforim.org/{slug}/{rel}")
    print(f"{slug}: {len(pages)} pages", flush=True)

today = date.today().isoformat()
body = "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
(HERE / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n",
    encoding="utf-8")
(HERE / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://openseforim.org/sitemap.xml\n",
                                 encoding="utf-8")
print(f"sitemap.xml: {len(urls)} URLs", flush=True)
