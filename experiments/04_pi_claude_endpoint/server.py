#!/usr/bin/env python3
"""OpenAI-style chat endpoint that answers Pi (or any OpenAI client) with Claude Code.

Text-only: POST /v1/chat/completions, GET /v1/models, GET /healthz. Each request runs the
configured Claude Code launcher once in print mode with no tools. Requests that carry `tools`
are refused (use Pi's own claude-accounts provider for agentic runs).

Security: binds 127.0.0.1 by default, every /v1 call needs `Authorization: Bearer <token>`,
the token is read from a mode-600 file outside the repo, and nothing here holds a key.
"""
import argparse, hmac, json, os, stat, subprocess, sys, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MODELS = {  # id served -> id passed to `claude --model`
    "claude-opus-5-5": "claude-opus-5-5",
    "claude-fable-5-1": "claude-fable-5-1",
    "claude-sonnet-5-5": "claude-sonnet-5-5",
    "claude-haiku-4-5": "claude-haiku-4-5",
}
MAX_BODY = 4_000_000
DEFAULT_TOKEN_FILE = "~/.config/pi-claude-endpoint/token"


def load_token(path):
    p = Path(path).expanduser()
    if not p.is_file():
        raise SystemExit(f"token file missing: {p} (run gen_token.sh)")
    if p.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise SystemExit(f"token file {p} must be mode 600")
    tok = p.read_text().strip()
    if len(tok) < 32:
        raise SystemExit("token must be at least 32 characters")
    return tok


def flatten(messages):
    """Chat messages -> (system text, transcript prompt)."""
    system, turns = [], []
    for m in messages:
        c = m.get("content")
        if isinstance(c, list):
            c = "\n".join(part.get("text", "") for part in c if isinstance(part, dict))
        c = c or ""
        role = m.get("role")
        if role in ("system", "developer"):
            system.append(c)
        else:
            turns.append(f"[{role}]\n{c}")
    return "\n\n".join(system), "\n\n".join(turns)


def run_claude(args, model, messages):
    system, prompt = flatten(messages)
    cmd = [*args.claude_cmd, "-p", "--output-format", "json", "--model", MODELS[model],
           "--tools", "", "--no-session-persistence", "--disable-slash-commands",
           "--setting-sources", "", "--strict-mcp-config"]
    if system:
        cmd += ["--system-prompt", system]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=args.timeout)
    try:
        out = json.loads(r.stdout)
    except ValueError:
        out = None
    if out is None:
        raise RuntimeError((r.stderr or r.stdout).strip()[-400:] or f"exit {r.returncode}")
    if out.get("is_error") or r.returncode != 0:
        raise RuntimeError(str(out.get("result"))[:400])
    u = out.get("usage") or {}
    return out.get("result", ""), u.get("input_tokens", 0), u.get("output_tokens", 0)


def run_echo(args, model, messages):  # test backend, no model call
    _, prompt = flatten(messages)
    return "ECHO: " + prompt[-200:], len(prompt) // 4, 8


def make_handler(args, token):
    backend = run_echo if args.backend == "echo" else run_claude
    slots = threading.BoundedSemaphore(args.max_concurrent)

    class H(BaseHTTPRequestHandler):
        server_version = "pi-claude-endpoint"

        def log_message(self, fmt, *a):  # no bodies, no headers in logs
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % a))

        def send_json(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def err(self, code, msg):
            self.send_json(code, {"error": {"message": msg, "type": "invalid_request_error"}})

        def authed(self):
            got = self.headers.get("Authorization", "")
            ok = got.startswith("Bearer ") and hmac.compare_digest(got[7:].encode(), token.encode())
            if not ok:
                self.err(401, "invalid or missing bearer token")
            return ok

        def do_GET(self):
            if self.path == "/healthz":
                return self.send_json(200, {"ok": True})
            if not self.authed():
                return
            if self.path == "/v1/models":
                return self.send_json(200, {"object": "list", "data": [
                    {"id": m, "object": "model", "owned_by": "claude-code"} for m in MODELS]})
            self.err(404, "not found")

        def do_POST(self):
            if not self.authed():
                return
            if self.path != "/v1/chat/completions":
                return self.err(404, "not found")
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > MAX_BODY:
                return self.err(413, "body missing or too large")
            try:
                req = json.loads(self.rfile.read(n))
            except ValueError:
                return self.err(400, "invalid JSON")
            model = req.get("model")
            if model not in MODELS:
                return self.err(400, f"unknown model; served: {sorted(MODELS)}")
            if req.get("tools") or req.get("functions"):
                return self.err(400, "tools are not supported by this endpoint; run Pi with --no-tools")
            if not isinstance(req.get("messages"), list) or not req["messages"]:
                return self.err(400, "messages required")
            if not slots.acquire(timeout=5):
                return self.err(429, "busy, retry")
            try:
                text, tin, tout = backend(args, model, req["messages"])
            except subprocess.TimeoutExpired:
                return self.err(504, "claude timed out")
            except Exception as e:  # sign-in failures surface here, no fallback
                return self.err(502, f"backend error: {e}")
            finally:
                slots.release()
            cid, now = "chatcmpl-" + uuid.uuid4().hex[:24], int(time.time())
            usage = {"prompt_tokens": tin, "completion_tokens": tout, "total_tokens": tin + tout}
            if req.get("stream"):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                def ev(delta, fin, u=None):
                    d = {"id": cid, "object": "chat.completion.chunk", "created": now, "model": model,
                         "choices": [{"index": 0, "delta": delta, "finish_reason": fin}]}
                    if u: d["usage"] = u
                    self.wfile.write(b"data: " + json.dumps(d).encode() + b"\n\n")
                ev({"role": "assistant", "content": text}, None)
                ev({}, "stop", usage)
                self.wfile.write(b"data: [DONE]\n\n")
                return
            self.send_json(200, {"id": cid, "object": "chat.completion", "created": now, "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                "usage": usage})
    return H


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=18300)
    ap.add_argument("--token-file", default=os.environ.get("PI_CLAUDE_ENDPOINT_TOKEN_FILE", DEFAULT_TOKEN_FILE))
    ap.add_argument("--backend", choices=["claude", "echo"], default="claude")
    ap.add_argument("--claude-cmd", nargs="+", default=["claude"],
                    help="launcher, e.g. ~/.pi/agent/claude-account-bin/vals-claude-code (checks the signed-in account)")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--max-concurrent", type=int, default=4)
    args = ap.parse_args()
    args.claude_cmd = [os.path.expanduser(c) for c in args.claude_cmd]
    token = load_token(args.token_file)
    srv = ThreadingHTTPServer((args.host, args.port), make_handler(args, token))
    print(f"listening on {args.host}:{args.port} backend={args.backend}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
