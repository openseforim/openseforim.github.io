# openseforim.github.io

Landing site for https://openseforim.org (org site of the `openseforim` GitHub org).

- `CNAME` sets the custom domain. Every project repo in the org then serves at
  `https://openseforim.org/<repo>/` without its own CNAME.
- `assets/os.css` + `assets/os.js` are the shared theme (v1): one palette (light, paper, dark) mapped onto the
  readers' own variable names, the Open Seforim strip with one theme control (`localStorage` key `os-theme`),
  and a footer built from the work's `work.json` (edition, scans, method, licence, citation, report a mistake).
  Each reader's build script puts this before `</head>`, after its own CSS:

  ```html
  <script>var osT=localStorage.getItem('os-theme');osT&&osT!='auto'&&document.documentElement.setAttribute('data-theme',osT)</script>
  <link rel="stylesheet" href="/assets/os.css">
  <script src="/assets/os.js" defer></script>
  ```

  A site with its own palette (Defus) adds `class="os-own-palette"` to `<html>`. Pages still work without
  these files (for example in a local preview); they only lose the strip and the shared colours.
- Add a work: give its repo a `work.json`, add it to `WORKS` in `build.py`, run `py -3.13 build.py`.
- `build.py` makes `index.html` (cards), `works.json` and `sitemap.xml` from each reader's `work.json`.
- `tools/export.py` writes `downloads/<slug>/<slug>.txt|.tei.xml|.epub` from a work's built pages (build.py runs it for
  every text work; `py -3.13 build.py --no-export` skips it). The footer of each work links them.
- `tools/postbuild.py` (run by every reader's build) also writes Google Scholar `citation_*` tags.
- `tools/citation_files.py` writes `CITATION.cff` and `.zenodo.json` into each work's repo, for GitHub's "Cite this
  repository" and Zenodo DOIs. Add `"doi"` to a work.json after Zenodo mints one; the footer and tags then use it.
- `assets/os.js`: set `GOATCOUNTER` to the GoatCounter site code to turn on page counts. A `#anchor` in the address
  shows a "This passage" bar with Copy citation / Copy link.
- `tools/check_downloads.py` tests every file in `downloads/`: EPUB (main epubcheck rules: mimetype, OPF, manifest, spine,
  well-formed XHTML, links, nav, cover), TEI (well-formed, header, ids, links, empty segments) and plain text (UTF-8,
  no HTML or interface text left). Run it after `build.py`.
