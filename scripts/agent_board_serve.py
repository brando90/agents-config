#!/usr/bin/env python3
"""Serve only the current board on loopback, for private Tailscale forwarding."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


BOARD = Path.home() / ".agent-board/board.html"
PORT = 8766


class BoardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.reply(include_body=True)

    def do_HEAD(self):
        self.reply(include_body=False)

    def reply(self, include_body):
        if urlsplit(self.path).path not in ("/", "/board.html"):
            self.send_error(404)
            return
        try:
            if BOARD.is_symlink():
                raise OSError("board must be a regular file")
            content = BOARD.read_bytes()
        except OSError:
            self.send_error(503, "Board is not available yet")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Agent-Board", "1")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; "
                         "style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
                         "frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        if include_body:
            self.wfile.write(content)

    def log_message(self, format, *args):
        pass  # No task data, visitor URLs, or routine access logs on disk.


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), BoardHandler).serve_forever()
