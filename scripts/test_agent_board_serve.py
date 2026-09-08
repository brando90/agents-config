"""Check private-file boundaries and freshness through real loopback requests."""

from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

import agent_board_serve as serve


class BoardServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = serve.BOARD
        serve.BOARD = Path(self.temp.name) / "board.html"
        serve.BOARD.write_text("<h1>First board</h1>")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), serve.BoardHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.opener = build_opener(ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        serve.BOARD = self.original
        self.temp.cleanup()

    def request(self, path="/", method="GET"):
        return self.opener.open(Request(self.base + path, method=method), timeout=2)

    def test_current_file_and_no_cache(self):
        with self.request() as response:
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertEqual(response.read(), b"<h1>First board</h1>")
        replacement = serve.BOARD.with_suffix(".tmp")
        replacement.write_text("<h1>New board after atomic replace</h1>")
        replacement.replace(serve.BOARD)
        with self.request("/board.html") as response:
            self.assertIn(b"New board", response.read())

    def test_neighbor_files_and_traversal_rejected(self):
        (serve.BOARD.parent / "private.json").write_text("private fixture")
        for path in ["/private.json", "/tailscale/tailscaled.state", "/../private.json",
                     "/%2e%2e/private.json", "/board.html/../private.json"]:
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                self.request(path)
            self.assertEqual(error.exception.code, 404)
            error.exception.close()

    def test_symlink_rejected(self):
        private = serve.BOARD.parent / "private.json"
        private.write_text("private fixture")
        serve.BOARD.unlink()
        serve.BOARD.symlink_to(private)
        with self.assertRaises(HTTPError) as error:
            self.request()
        self.assertEqual(error.exception.code, 503)
        error.exception.close()

    def test_missing_board_is_unavailable(self):
        serve.BOARD.unlink()
        with self.assertRaises(HTTPError) as error:
            self.request()
        self.assertEqual(error.exception.code, 503)
        error.exception.close()

    def test_head_and_write_rejection(self):
        with self.request(method="HEAD") as response:
            self.assertEqual(response.read(), b"")
        with self.assertRaises(HTTPError) as error:
            self.request(method="POST")
        self.assertEqual(error.exception.code, 501)
        error.exception.close()


if __name__ == "__main__":
    unittest.main()
