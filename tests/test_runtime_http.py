from __future__ import annotations

from http.server import ThreadingHTTPServer
import json
import queue
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from _load import EXAMPLE, load_script

runtime = load_script("lumanim_runtime")


class FakeRenderer:
    def status(self):
        return {"ok": True, "engine": "3b1b/manim", "lesson_id": "test"}


class RuntimeHTTPTests(unittest.TestCase):
    def setUp(self):
        self.render_queue = queue.Queue()
        handler = runtime.make_handler(EXAMPLE, FakeRenderer(), self.render_queue, 0)
        self.server = ThreadingHTTPServer((runtime.HOST, 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://{runtime.HOST}:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request_error(self, request, status):
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=2)
        self.assertEqual(caught.exception.code, status)
        caught.exception.close()

    def test_status_is_json(self):
        with urlopen(f"{self.base}/api/status", timeout=2) as response:
            body = json.load(response)
        self.assertTrue(body["ok"])
        self.assertEqual(body["engine"], "3b1b/manim")

    def test_foreign_origin_is_rejected(self):
        request = Request(f"{self.base}/api/status", headers={"Origin": "https://evil.example"})
        self.request_error(request, 403)

    def test_malformed_state_is_rejected(self):
        request = Request(
            f"{self.base}/api/frame",
            data=b"{bad}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        self.request_error(request, 400)

    def test_traversal_cannot_leave_workspace(self):
        self.request_error(f"{self.base}/%2e%2e/%2e%2e/etc/passwd", 404)

    def test_valid_state_returns_rendered_frame(self):
        def render_once():
            request = self.render_queue.get(timeout=2)
            request.frame = b"\xff\xd8\xff\xd9"
            request.done.set()

        worker = threading.Thread(target=render_once)
        worker.start()
        request = Request(
            f"{self.base}/api/frame",
            data=b'{"value": 0.5}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            self.assertEqual(response.headers["Content-Type"], "image/jpeg")
            self.assertEqual(response.read(), b"\xff\xd8\xff\xd9")
        worker.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
