# Checklist: from a candidate work to a new reader

A high-level standard procedure, written from the readers built so far (most recently *Ma'agal Tov*, 24-Nov-2026).
Candidate works and their research are in [openseforim/candidates](https://github.com/openseforim/candidates)
(shown at <https://openseforim.org/next/>). Local clones are expected side by side in one folder.

## 1. Choose and check the work

- [ ] Public domain: author died 70+ years ago (EU) and published before 1931 (US). A modern edition of an old text
      can be in copyright; use only its readings that the scan shows, never its notes or added passages.
- [ ] Existing text first: Project Ben-Yehuda (public-domain dump), Sefaria, Wikisource (he, de), Daat. A text layer
      in a PDF is not a text: test a page (the Daat layer of *Dor Dor ve-Dorshav* was reversed and scrambled).
- [ ] Existing translations: note them and their copyright in the candidate file. A reader adds value when it gives an
      open text with an open translation, not only when it is the first translation.
- [ ] Update the candidate file (`status: researched`, `checked:` with the date and what was checked).

## 2. Choose the scan, with a test before committing to it

- [ ] Prefer greyscale or colour page images of 400+ ppi (archive.org `_jp2.zip`, the original images).
      1-bit scans of about 300 dpi are poor for OCR (HebrewBooks *Ma'agal Tov*: 26% wrong words).
- [ ] OCR one typical page and score it against a hand transcription (`maagal-tov/scripts/eval_gt.py`).
      If the error rate is high, look for another scan or another work before trying model training.
- [ ] Keep downloads under `openseforim-scans/scans/<candidate-slug>/` (not in the reader repo).

## 3. OCR

- [ ] One script per page (Hebrew, Syriac, Latin): Kraken with the PP-OCRv6 medium model.
      Find lines with the row-profile splitter and read with `ocr --no-segmentation -B 16 --base-dir R`
      (`maagal-tov/scripts/split_image.py`, `ocr_images.py`); Kraken's own segmenter drops lines on 1-bit print.
      `--base-dir R` gives logical order, with numbers the right way round.
- [ ] Mixed scripts on one line (German or Latin with Hebrew, Greek, Arabic): a vision model, or Kraken with a second pass.
- [ ] **Before any batch (cloud or long local run): read a sample of the actual output yourself**: 5–10 varied
      pages per book (chapter openings, pages with headings and footnotes), against the scan, and look at the number
      of lines per page across the run so far: it should form one cluster. Two clusters mean a fault (Weiss,
      24-Nov-2026: on about a third of the pages the line finder merged lines in pairs). Equal output on CPU and GPU
      proves only that the run is reproducible, not that it is right.
- [ ] Long runs: in the background, resumable (one output file per page, skip pages already done), with a log and a
      progress line; one OCR job at a time on a laptop. Do not hold a log file open with `tail -F` on Windows:
      it can stop the writer.

## 4. Check the text against the scan

- [ ] Line by line against the page image. Keep spelling, abbreviations and punctuation as printed; drop catchwords
      and running heads. Never "correct" a word from memory: if a word looks wrong, enlarge that line of the scan.
- [ ] Note the typical OCR errors of the type (for example צ read as ל) in the repo's notes.
- [ ] Keep raw OCR (`data/he_raw/`) and checked pages (`data/he/`) apart, so it is always clear what was checked.

## 5. Translate

- [ ] One English unit per source unit (line, verse, paragraph or section, whatever the print gives), so the
      build can check that the counts agree.
- [ ] Biblical and rabbinic phrases: references in [gray brackets]. Uncertain renderings and unresolved
      abbreviations: ⚠n in the text and a note at the end of the page. Do not guess silently.
- [ ] Credit: "by Claude (Anthropic), directed and reviewed by Ezra Brand".
- [ ] The owner approves new translation text before it is published.

## 6. Build the reader

- [ ] Copy the structure of a recent reader (`tahkemoni`, `maagal-tov`): `scripts/build_site.py` writes `docs/`,
      `docs/style.css` from that reader, and `docs/work.json` (schema 1: slug, order, kind, title, author,
      status_label, start, start_label, summary, base_edition, method, cite, url, repo, licence).
      `start` (the first reading page) makes the shared script show a "Start reading" button on the work's home page.
- [ ] Head of every page: the page's own CSS, then `/assets/os.css` and `/assets/os.js` (see README).
      The build ends with `tools/postbuild.py <slug> docs`.
- [ ] Phone layout: the source text comes before the English when the columns stack.
- [ ] Scans: mark each printed page start in the text with a link to the scan (`a.pg`, or `a.scanlink` with
      `data-scan-img` for copies kept in the reader). The shared `os-scan.js` then adds the "Scan" button and the
      margin panel by itself. Test one link in the library's viewer: archive.org's viewer can leave out images.
- [ ] Class names: check that a new class does not collide with one that `tools/export.py` treats specially
      (scan-page links: use `scanlink`, which the export skips; `.pg` is a page citation in Bochart and Lewysohn and is kept).
- [ ] Preview with `tools/serve_all.py` (all readers at their live paths). To preview a work that is not yet in
      `WORKS`, add its folder to `MOUNTS` locally and do not commit that change.

## 7. Publish

- [ ] Repo: `gh repo create openseforim/<slug> --public --source . --push`. `.gitignore` for scans, line images
      and OCR experiments. `LICENSE` (CC BY-SA 4.0 for texts and translation; MIT for code where the repo has much code),
      README with status table, sources, method, layout, licence.
- [ ] GitHub Pages from `main` `/docs`; topics `judaica`, `hebrew`, `open-seforim`, `translation`.
- [ ] Site: add the slug to `WORKS` in `build.py`, run `tools/citation_files.py`, then `build.py`
      (cards, `works.json`, sitemap, downloads), then `tools/check_downloads.py`.
- [ ] Read `git diff --stat` before committing: only the new work, `index.html`, `works.json`, `sitemap.xml`,
      `assets/os.js` and EPUB dates should change. Changes in other works' txt or TEI files mean a regression.
- [ ] Candidates: `status: started` and `reader:` URL; push; the site build updates /next/.
- [ ] Check live after the Pages builds: rows, links, notes, canonical URL, landing card, /next/, downloads.

## 8. After publishing

- [ ] Zenodo: the owner switches the new repo on at zenodo.org; then make a release (`vYYYY.MM.DD`), add `doi`
      to `work.json`, rerun `citation_files.py` and `build.py`.
- [ ] Old URLs: only for a repo moved into the org (`EzraBrand.github.io` 404 map and `build_redirects.py`).
- [ ] Record the state (what is checked, translated, next part) in the repo README and in the candidate file.
