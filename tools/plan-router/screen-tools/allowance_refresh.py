"""Refresh the allowance block in Brando's tracker Doc from the live plan router, with no model call; writes the spec for his top line and the block (step 1 of 2).

Use in every 90-minute refresh run (7:00 to 22:00): run this with tool_script, read its printed summary, then run notes/tools/doc_tables_at.py through tool_script with
args ["1FBeITQ-Rp6moDD38FTZWsDOQP4ZC8X7xskXMzr-RVAw", "scratch/allowance_refresh/spec.txt", "Weekly Jobs/Allowance for ub9cw used", "TLDR ("] to swap the block (step 2), then run notes/tools/doc_format_fix.py (step 3, restores column widths, padding and fonts that a rebuilt table loses), then read the Doc back.
Needs only toollib (ssh_run to skampere1 for the router status and for the imported Cursor/Grok reading, ~/.local/state/plan-router/xai-weekly-reading.json). The spec carries Brando's top line, so step 2 rewrites it with the block. Rows for keys, STAIR and Sundial are static in ROWS_STATIC: edit them here when a fact changes. The Cursor and Grok rows are built from the imported reading (value, read time, expiry, current or not current); nothing about them is hard-coded.
Example: tool_script notes/tools/allowance_refresh.py args ["--own-used", "about 50%"]
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import zoneinfo

import toollib

DOC = "1FBeITQ-Rp6moDD38FTZWsDOQP4ZC8X7xskXMzr-RVAw"
PT = zoneinfo.ZoneInfo("America/Los_Angeles")
ap = argparse.ArgumentParser()
ap.add_argument("--own-used", default="about 50%")
ap.add_argument("--out", default="scratch/allowance_refresh/spec.txt")
a = ap.parse_args()

r = toollib.call("mcp__ssh__ssh_run", {"host": "skampere1", "timeout": 120, "command":
    "python3 ~/.local/lib/plan-router/router.py --config ~/.config/plan-router/config.json status 2>&1"}, whole=True)
txt = r if isinstance(r, str) else json.dumps(r)
txt = txt.replace("\\n", "\n").replace('\\"', '"')
plans = {}
for m in re.finditer(r'\{"plan": "([^"]+)".*', txt):
    line = m.group(0)
    try:
        plans[m.group(1)] = json.loads(line[:line.rfind("}") + 1])
    except Exception:
        pass
now = dt.datetime.now(PT)

# Cursor and Grok share one weekly pool, read from the dashboard and imported by the launch flow.
xr = toollib.call("mcp__ssh__ssh_run", {"host": "skampere1", "timeout": 60, "command":
    "cat ~/.local/state/plan-router/xai-weekly-reading.json 2>&1"}, whole=True)
xtxt = xr if isinstance(xr, str) else json.dumps(xr)
xtxt = xtxt.replace("\\n", "\n").replace('\\"', '"')
xm = re.search(r'\{[^{}]*"schema": "xai-weekly-v1"[^{}]*\}', xtxt, re.S)
try:
    xai = json.loads(xm.group(0)) if xm else None
except Exception:
    xai = None


def t(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(PT)


def fmt(d):
    return d.strftime("%b %-d %-I:%M %p")


def win(p, key):
    w = (plans.get(p) or {}).get("windows", {}).get(key, {})
    if w.get("used_percent") is None:
        return None, None
    return w["used_percent"], (w.get("reset_at"), w.get("observed_at"))


def ev(p):
    e = ((plans.get(p) or {}).get("limit_events") or {}).get("five_hour")
    if not e:
        return "Not reported", "Not read", ""
    u = round(e["utilization"] * 100)
    obs = t(e["observed_at"])
    blocked = t(e["blocked_until"]) if e.get("blocked_until") else None
    st = "Paused until " + blocked.strftime("%-I:%M %p") if blocked and blocked > now else "Window reset, eligible"
    return "%d%% left (%d%% used)" % (100 - u, u), fmt(obs) + " (limit event)", st


rows = []
used, meta = win("vals-codex", "weekly")
rows.append(["1", "Vals Codex", "Not reported", ("%d%% left (%d%% used); resets %s" % (100 - used, used, fmt(t(meta[0])))) if used is not None else "Not reported",
             "ON, lane 1", (fmt(t(meta[1])) if meta else "Not read") + "; checked again at every launch"])
# Newer read than the router's own (AT-3455, 2026-11-24 11:41 PST): Vals Codex weekly 4% used. Drop this override when the router's read is newer than 11:41.
if meta and t(meta[1]) < dt.datetime(2026, 11, 24, 11, 41, tzinfo=PT):
    rows[-1][3] = "96%% left (4%% used); resets %s" % fmt(t(meta[0]))
    rows[-1][5] = "Nov 24 11:41 AM; checked again at every launch"
five, read, st = ev("vals-claude-opus")
rows.append(["2", "Vals Claude", five, "Not reported", st or "Not read", read])
# Stanford lanes: router status shows no windows for them; readings below are AT-3455's live reads (2026-11-24 11:41 PST for Stanford Codex, 11:12 to 11:17 for Stanford Claude). Update by hand when a newer read exists.
rows.append(["3", "Stanford Codex", "9% left (91% used); back 3:19 PM", "18% left (82% used); resets Nov 30", "Skipped until its 5-hour window resets (over 80%)", "Nov 24 11:41 AM"])
# AT-3494: Stanford Claude reads the router's stored five_hour limit event too (live one-word probe, warn_gate off: pauses only at 80% used, rejected or overage).
five4, read4, st4 = ev("stanford-claude")
rows.append(["4", "Stanford Claude", five4, "Not reported", st4 or "Not read", read4])
rows.sort(key=lambda x: x[0])
def xai_rows():
    if not xai or xai.get("status") != "ready" or xai.get("used_percent") is None:
        why = "reading missing or failed"
        return [["8", "Cursor", "Not shown", "Not read (" + why + ")", "A fresh read comes before the next job", "Not read"],
                ["9", "Grok", "Not shown", "Same shared pool as Cursor", "Same as Cursor", "Not read"]]
    used = xai["used_percent"]
    obs, exp = t(xai["observed_at"]), t(xai["expires_at"])
    cur = exp > now
    weekly = "%.2f%% left (%.2f%% used), shared with Grok; resets %s" % (100 - used, used, fmt(t(xai["reset_at"])).rsplit(" ", 2)[0])
    if cur:
        state = "ON, 80% gate; reading valid until " + exp.strftime("%-I:%M %p")
    else:
        state = "Reading expired " + exp.strftime("%-I:%M %p") + "; a fresh read comes before the next job"
    read = "Nov %d %s%s" % (obs.day, obs.strftime("%-I:%M %p"), "" if cur else " (not current)")
    return [["8", "Cursor", "Not shown", weekly, state, read],
            ["9", "Grok", "Not shown", "Same shared pool as Cursor", "Same as Cursor", read]]


def xai_row(index, title, plan):
    w = (plans.get(plan) or {}).get("windows", {}).get("weekly", {})
    base = "Automatic browser refresh in the prelaunch flow when stale; 80% gate"
    try:
        used = w["used_percent"]
        assert isinstance(used, (int, float)) and not isinstance(used, bool) and math.isfinite(used) and 0 <= used <= 100
        seen, expiry, reset = (t(w[k]) for k in ("observed_at", "expires_at", "reset_at"))
        fresh = w.get("status") == "ready" and dt.timedelta(0) <= now-seen < dt.timedelta(minutes=10) and now < expiry <= min(seen+dt.timedelta(minutes=10), reset)
        quota = "%.2f%% left, shared pool; resets %s (clock not shown)" % (100-used, reset.strftime("%b %-d"))
        state = ("Ready; " if fresh and used < 80 else "80% gate reached; " if fresh else "Reading expired; ") + base
        return [index, title, "Not shown", quota, state, fmt(seen) + (" (dated reading)" if not fresh else "")]
    except (KeyError, TypeError, ValueError, AssertionError):
        return [index, title, "Not shown", "Not reported", "Fresh browser reading required; " + base, "Not read"]


ROWS_STATIC = [
    ["5", "STAIR enterprise Claude", "n/a", "n/a", "TODO, not set up yet (the group is getting it)", "n/a"],
    ["6", "Sundial", "n/a", "n/a", "Writing jobs only", "n/a"],
    ["7", "Koyejo lab key", "Pay per call", "6 small jobs a day", "ON, small gate", "Nov 24 10:08"],
    ["7b", "STAIR bm key (Opus 5.5, gateway)", "Pay per call", "6 starts a day, about $0.25 a day estimated", "ON, key change waits for Zeyu (Fri Nov 27)", "Nov 24 10:07"],
    ["10", "Vals key", "Pay per call", "6 small jobs a day", "ON, small gate", "Nov 24 10:08"],
    ["11", "Stanford gateway key (sol)", "Pay per call", "Same gate as 7b", "ON, small gate", "Nov 24 10:08"],
]
pc = (plans.get("personal-codex") or {}).get("note", "")
m = re.search(r"weekly (\d+)% used, resets ([^.]+)\.", pc)
rows += [r2 for r2 in ROWS_STATIC[:4]] + xai_rows() + [r2 for r2 in ROWS_STATIC[4:]]
rows.append(["12", "Personal Codex", "Not reported", ("%d%% left (%s%% used); resets %s" % (100 - int(m.group(1)), m.group(1), m.group(2).replace(" PST", " AM"))) if m else "Not reported", "Skipped while 80% or more used" if m and int(m.group(1)) >= 80 else "ON, 80% gate", "Nov 24 11:12"])
cn = (plans.get("personal-claude") or {}).get("note", "")
m2 = re.search(r"seven_day utilization ([0-9.]+) read ([0-9:]+) PST", cn)
# AT-3491: personal Claude reads the router's own stored seven_day limit event (refreshed live by the router's one-word probe); the note is only a fallback
e7 = ((plans.get("personal-claude") or {}).get("limit_events") or {}).get("seven_day")
if e7 and e7.get("utilization") is not None:
    u7 = round(e7["utilization"] * 100)
    rows.append(["13", "Personal Claude", "Not reported", "%d%% left (%d%% used); resets Mon Nov 30 11 PM" % (100 - u7, u7),
                 "Paused until the reset (80% or more used)" if e7.get("blocked_until") else "ON, 80% gate", fmt(t(e7["observed_at"])) + " (limit event)"])
else:
    rows.append(["13", "Personal Claude", "Not reported", ("%d%% left (%d%% used); resets Mon Nov 30 11 PM" % (100 - round(float(m2.group(1)) * 100), round(float(m2.group(1)) * 100))) if m2 else "Not reported", "ON, 80% gate", ("Nov 24 " + m2.group(2)) if m2 else "Not read"])
rows.append(["14", "Allen's Gemini key", "Pay per call", "Small share", "ON, small share", "Not read today"])
ag = (plans.get("personal-agy") or {}).get("windows", {})
if ag.get("weekly", {}).get("used_percent") is not None:
    rows.append(["15", "Google plan (agy)", "%d%% left (Gemini, %d%% used)" % (100 - ag["short"]["used_percent"], ag["short"]["used_percent"]),
                 "%d%% left (Gemini, %d%% used)" % (100 - ag["weekly"]["used_percent"], ag["weekly"]["used_percent"]),
                 "ON for any job incl. real experiments (Nov 25); cap 10 a day; last in the order",
                 fmt(t(ag["weekly"]["observed_at"]))])
else:
    rows.append(["15", "Google plan (agy)", "Not reported", "Not reported", "Last in the order; any job incl. real experiments (Nov 25)", "Not read"])
nxt = [dt.time(7, 0), dt.time(8, 30), dt.time(10, 0), dt.time(11, 30), dt.time(13, 0), dt.time(14, 30), dt.time(16, 0), dt.time(17, 30), dt.time(19, 0), dt.time(20, 30), dt.time(22, 0)]
later = [x for x in nxt if x > now.time()]
nxt_s = later[0].strftime("%-I:%M %p") if later else "7:00 AM tomorrow"
stamp = now.strftime("%Y-%m-%d %H:%M PST")
lines = ["Weekly Jobs/Allowance for ub9cw used: %s (as of %s; estimate from the work units left)" % (a.own_used, stamp),
         "H2: Allowance left, per account (as of %s; refreshed every 90 minutes, 7 AM to 10 PM; next %s)" % (stamp, nxt_s),
         "My own allowance (ub9cw): %s of this week used (%s). Everything below is your plans, read from the router and each account's own check. \"Not reported\" means the account does not show it; I never guess it." % (a.own_used, stamp),
         "| # | Account | 5-hour window | Weekly | State now | Read (PST) |", "|---|---|---|---|---|---|"]
for row in rows:
    lines.append("| " + " | ".join(c.replace("|", "/") for c in row) + " |")
os.makedirs(os.path.dirname(a.out), exist_ok=True)
open(a.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("rows", len(rows), "plans read", sorted(plans))
print("\n".join(lines[:3]))
