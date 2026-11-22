"""Write CITATION.cff (GitHub "Cite this repository") and .zenodo.json (DOI metadata) into each work's repo.

py -3.13 tools/citation_files.py      (reads WORKS from build.py; run again after work.json changes)
"""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from build import WORKS  # noqa: E402

LIC = {"CC BY-SA 4.0": ("CC-BY-SA-4.0", "cc-by-sa-4.0")}


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


for slug, (folder, src) in WORKS.items():
    repo = HERE.parent / folder
    w = json.loads((repo / src / "work.json").read_text(encoding="utf-8"))
    title = w["title"].replace("*", "")
    kind = {"translation": "Hebrew/source text with English translation", "source": "source text",
            "catalogue": "catalogue"}.get(w.get("kind"), "")
    full = title if w.get("kind") == "catalogue" else f"{title}: reading edition with English translation"
    if w.get("kind") == "source":
        full = f"{title}: reading edition"
    summary = (w.get("summary") or "").replace("*", "")
    abstract = summary + (" " + w["method"] if w.get("method") else "")
    spdx, zen = LIC["CC BY-SA 4.0"]
    keywords = ["Judaica", "Hebrew", "digital humanities", "translation", "digital edition"]
    cff = ["cff-version: 1.2.0",
           'message: "If you use this edition, please cite it as below."',
           f"title: {q(full)}",
           "type: dataset",
           "authors:",
           "  - family-names: Brand",
           "    given-names: Ezra",
           f"abstract: {q(abstract)}",
           f"license: {spdx}",
           f"url: {q(w['url'])}",
           f"repository-code: {q(w['repo'])}",
           "keywords:"] + [f"  - {q(k)}" for k in keywords]
    if w.get("doi"):
        cff.append(f"doi: {q(w['doi'])}")
    (repo / "CITATION.cff").write_text("\n".join(cff) + "\n", encoding="utf-8")
    zj = {"title": full, "upload_type": "publication", "publication_type": "book" if w.get("kind") != "catalogue" else "other",
          "description": f"<p>{summary}</p><p>{w.get('method', '')}</p><p>Read online: <a href=\"{w['url']}\">{w['url']}</a></p>",
          "creators": [{"name": "Brand, Ezra"}], "license": zen, "access_right": "open", "keywords": keywords,
          "language": "eng",
          "related_identifiers": [{"identifier": w["url"], "relation": "isDocumentedBy", "resource_type": "publication-other"}]}
    if w.get("base_edition", {}).get("scan_url"):
        zj["related_identifiers"].append({"identifier": w["base_edition"]["scan_url"], "relation": "isDerivedFrom",
                                          "resource_type": "publication-book"})
    (repo / ".zenodo.json").write_text(json.dumps(zj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("citation files:", folder, flush=True)
