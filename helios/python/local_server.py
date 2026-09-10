#!/usr/bin/env python3
"""Serve gh-pages/ and POST /api/lseg → lseg_bridge.handle.

  python3 helios/python/local_server.py

Workspace must be open. Then open http://127.0.0.1:8765/helios/
On GitHub Pages there is no this server — data.html shows the disconnect banner.
"""

from __future__ import annotations

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lseg_bridge import BridgeError, classify, handle  # noqa: E402

REPO = HERE.parents[1]
PAGES = REPO / "gh-pages"
PORT = int(os.environ.get("HELIOS_PORT") or 8765)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PAGES), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/lseg":
            self.send_error(404, "POST /api/lseg only")
            return
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n)
        try:
            req = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(req, dict):
                raise BridgeError("bad_request", "Request must be a JSON object.")
            out = handle(req)
        except Exception as exc:  # noqa: BLE001
            code, message = classify(exc)
            out = {"ok": False, "code": code, "message": message, "detail": str(exc)}
        body = json.dumps(out, default=str).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    if not (PAGES / "helios" / "index.html").is_file():
        print("Expected %s/helios/index.html" % PAGES, file=sys.stderr)
        return 1
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("Helios local  http://127.0.0.1:%d/helios/" % PORT)
    print("Data           http://127.0.0.1:%d/helios/data.html" % PORT)
    print("Workspace must be signed in. Ctrl-C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
