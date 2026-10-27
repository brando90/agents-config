"""Minimal Chrome DevTools Protocol client for Spotify's xpui page (localhost only)."""
import json, sys, urllib.request, websocket
def page_ws():
    for t in json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10)):
        if t["type"] == "page" and "xpui.app.spotify.com" in t["url"]:
            return t["webSocketDebuggerUrl"]
    raise SystemExit("xpui page not found")
def evaluate(expr, timeout=60):
    ws = websocket.create_connection(page_ws(), timeout=timeout, origin="http://127.0.0.1:9222")
    ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
    while True:
        m = json.loads(ws.recv())
        if m.get("id") == 1:
            ws.close()
            r = m.get("result", {})
            if "exceptionDetails" in r: return {"error": r["exceptionDetails"].get("exception", {}).get("description") or r["exceptionDetails"]}
            return r.get("result", {}).get("value")
if __name__ == "__main__":
    print(json.dumps(evaluate(open(sys.argv[1]).read() if sys.argv[1].endswith(".js") else sys.argv[1]), indent=1)[:4000])
