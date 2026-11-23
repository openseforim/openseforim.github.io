"""Serve the org site and every reader at their live paths, for local checks.

py -3.13 tools/serve_all.py [port]   -> http://localhost:8765/ , /emden/ , /bochart/ ...
The reader folders come from build.py WORKS (local clones are siblings of this repo).
"""
import functools, http.server, sys
from urllib.parse import unquote
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from build import WORKS, ROOT  # noqa: E402

MOUNTS = {slug: ROOT / folder / src for slug, (folder, src) in WORKS.items()}


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parts = path.split("?", 1)[0].split("#", 1)[0].lstrip("/").split("/", 1)
        if parts[0] in MOUNTS:
            base = MOUNTS[parts[0]]
            rest = parts[1] if len(parts) > 1 else ""
            return str(base / unquote(rest))
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    h = functools.partial(Handler, directory=str(HERE))
    http.server.ThreadingHTTPServer(("127.0.0.1", port), h).serve_forever()
