#!/usr/bin/env python3
"""Make Spotify (macOS) play the jazz play-along local files on this Mac. Idempotent; run from any Mac that has the audio folder.
Steps: (1) relaunch Spotify with a localhost DevTools port, (2) call Spotify's own LocalFilesAPI to enable local files and add the
audio folder as a source, (3) restart Spotify normally (closes the port), (4) verify with spotify_cli that a jazz playlist plays a local file.
Requires: /Applications/Spotify.app, python3 + websocket-client (pip install websocket-client), user logged in to Spotify.
Usage: python3 spotify_local_setup.py [--folder "~/Music/Spotify Local Files"] [--playlist spotify:playlist:11cA2OIu3sLseq2jMCAxme] [--verify-only]
"""
import argparse, json, os, subprocess, sys, time, urllib.request
CLI = "/Applications/Spotify.app/Contents/MacOS/spotify_cli"
PORT = 9222
GET_API = r"""
(async () => {
  let req; rspackChunk.push([[Symbol("p")], {}, r => { req = r; }]);
  const ctx = req(48817).N, mk = req(93416).u;           // RegistryContext, platform-API key factory (xpui 1.3.0.277)
  const el = document.querySelector("#main") || document.body.firstElementChild;
  const fk = Object.keys(el).find(k => k.startsWith("__reactFiber$") || k.startsWith("__reactContainer$"));
  let f = el[fk]; const stack = [f && f.stateNode && f.stateNode.current ? f.stateNode.current : f]; let registry = null; const seen = new Set();
  while (stack.length && !registry) { const x = stack.pop(); if (!x || seen.has(x)) continue; seen.add(x); const t = x.type;
    if (t && (t === ctx || t._context === ctx) && x.memoizedProps && x.memoizedProps.value) { registry = x.memoizedProps.value; break; }
    if (x.child) stack.push(x.child); if (x.sibling) stack.push(x.sibling); }
  window.__lfapi = registry.resolve(mk("LocalFilesAPI")); window.__plapi = registry.resolve(mk("PlaylistAPI"));
  return "ok";
})()"""

def sh(*a, timeout=60):
    return subprocess.run(a, capture_output=True, text=True, timeout=timeout).stdout

def spotify_quit():
    subprocess.run(["pkill", "-TERM", "-x", "Spotify"])
    for _ in range(30):
        if subprocess.run(["pgrep", "-x", "Spotify"], capture_output=True).returncode != 0: return
        time.sleep(1)
    subprocess.run(["pkill", "-KILL", "-x", "Spotify"]); time.sleep(2)

def evaluate(expr, timeout=120):
    import websocket
    for _ in range(60):
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list", timeout=5))
            page = next(t for t in tabs if t["type"] == "page" and "xpui.app.spotify.com" in t["url"]); break
        except Exception: time.sleep(1)
    else: raise SystemExit("Spotify DevTools page not found on port %d" % PORT)
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=timeout, origin=f"http://127.0.0.1:{PORT}")
    ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
    while True:
        m = json.loads(ws.recv())
        if m.get("id") == 1:
            ws.close(); r = m.get("result", {})
            if "exceptionDetails" in r: raise RuntimeError(r["exceptionDetails"])
            return r.get("result", {}).get("value")

def wait_ready(timeout=90):
    """Wait until the local Spotify client is up and registered as a Connect device (after a relaunch)."""
    for _ in range(timeout // 3):
        try:
            dev = json.loads(sh(CLI, "devices", "list", "--format", "json"))
            me = next((d for d in dev["devices"] if d.get("is_self")), None)
            if me: return me
        except Exception: pass
        time.sleep(3)
    raise SystemExit("Spotify client did not become ready")

def verify(playlist, tries=3):
    """Play the playlist on THIS Mac and confirm a local file is actually playing (uri spotify:local:, is_playing, file open in lsof)."""
    me = wait_ready()
    for attempt in range(tries):
        subprocess.run([CLI, "play", playlist, "--device", me["device_id"]], capture_output=True, timeout=60)
        np = {}
        for _ in range(15):                                   # poll up to ~30 s
            time.sleep(2)
            np = json.loads(sh(CLI, "now-playing", "--format", "json") or "{}").get("currently_playing", {}) or {}
            if np.get("uri", "").startswith("spotify:local:") and np.get("is_playing"): break
        else:
            continue                                            # not playing yet: re-issue play
        pids = sh("pgrep", "-f", "Spotify.app/Contents").split()
        opened = sorted({l.split(None, 8)[-1] for p in pids for l in sh("lsof", "-p", p).splitlines()
                         if "/Music/" in l and l.rstrip().endswith((".mp3", ".m4a"))})
        subprocess.run([CLI, "pause"], capture_output=True, timeout=30)
        print(f"verify (attempt {attempt+1}): now-playing={np.get('description')!r} uri={np.get('uri','')[:70]} is_playing={np.get('is_playing')} | local files open: {len(opened)} e.g. {opened[-1:]}")
        ok = bool(opened)
        print("VERIFY PASS" if ok else "VERIFY FAIL"); return ok
    subprocess.run([CLI, "pause"], capture_output=True, timeout=30)
    print(f"verify: playback never reported a playing local track after {tries} attempts; last now-playing={np}"); print("VERIFY FAIL"); return False

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--folder", default="~/Music/Spotify Local Files")
    ap.add_argument("--playlist", default="spotify:playlist:11cA2OIu3sLseq2jMCAxme"); ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args(); folder = os.path.expanduser(a.folder)
    if a.verify_only: sys.exit(0 if verify(a.playlist) else 1)
    assert os.path.isdir(folder), f"missing folder {folder}"
    spotify_quit()
    subprocess.run(["open", "-g", "-a", "Spotify", "--args", f"--remote-debugging-port={PORT}", f"--remote-allow-origins=http://127.0.0.1:{PORT}"])
    time.sleep(8); evaluate(GET_API)
    evaluate("(async () => { const a = window.__lfapi; if (!(await a.getIsEnabled())) await a.setIsEnabled(true); return await a.getIsEnabled(); })()")
    src = evaluate("(async () => await window.__lfapi.getSources())()")
    if folder not in [f["path"] for f in src.get("folders", [])]:
        evaluate("(async () => { await window.__lfapi.addFolder({path: %s}); return 1; })()" % json.dumps(folder))
        time.sleep(15)
    src = evaluate("(async () => await window.__lfapi.getSources())()")
    n = evaluate("(async () => (await window.__lfapi.getTracks()).length)()")
    print(f"sources: {src} | indexed local tracks: {n}")
    spotify_quit(); subprocess.run(["open", "-g", "-a", "Spotify"])
    sys.exit(0 if verify(a.playlist) else 1)

if __name__ == "__main__": main()
