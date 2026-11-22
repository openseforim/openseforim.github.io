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
