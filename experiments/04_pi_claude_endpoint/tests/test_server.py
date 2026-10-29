"""Run: python3 -m unittest experiments/04_pi_claude_endpoint/tests/test_server.py (echo backend, no model call)."""
import json, os, subprocess, sys, tempfile, time, unittest, urllib.error, urllib.request
from pathlib import Path

SRV = Path(__file__).resolve().parents[1] / "server.py"


def call(port, path, token=None, body=None):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.tf = os.path.join(cls.dir, "token")
        cls.tok = "t" * 40
        Path(cls.tf).write_text(cls.tok); os.chmod(cls.tf, 0o600)
        cls.port = 18391
        cls.p = subprocess.Popen([sys.executable, str(SRV), "--backend", "echo", "--port", str(cls.port), "--token-file", cls.tf],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        cls.p.stdout.readline()

    @classmethod
    def tearDownClass(cls):
        cls.p.terminate()

    def test_health_open_models_closed(self):
        self.assertEqual(call(self.port, "/healthz")[0], 200)
        self.assertEqual(call(self.port, "/v1/models")[0], 401)
        self.assertEqual(call(self.port, "/v1/models", "wrong")[0], 401)
        self.assertEqual(call(self.port, "/v1/models", self.tok)[0], 200)

    def test_chat(self):
        b = {"model": "claude-opus-5-5", "messages": [{"role": "user", "content": "hi"}]}
        self.assertEqual(call(self.port, "/v1/chat/completions", None, b)[0], 401)
        c, t = call(self.port, "/v1/chat/completions", self.tok, b)
        self.assertEqual(c, 200)
        self.assertIn("ECHO", json.loads(t)["choices"][0]["message"]["content"])
        c, t = call(self.port, "/v1/chat/completions", self.tok, {**b, "stream": True})
        self.assertIn("[DONE]", t)

    def test_rejects(self):
        b = {"model": "claude-opus-5-5", "messages": [{"role": "user", "content": "hi"}]}
        self.assertEqual(call(self.port, "/v1/chat/completions", self.tok, {**b, "tools": [{"type": "function"}]})[0], 400)
        self.assertEqual(call(self.port, "/v1/chat/completions", self.tok, {**b, "model": "gpt-4"})[0], 400)

    def test_token_file_mode(self):
        os.chmod(self.tf, 0o644)
        r = subprocess.run([sys.executable, str(SRV), "--backend", "echo", "--token-file", self.tf], capture_output=True, text=True)
        os.chmod(self.tf, 0o600)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
