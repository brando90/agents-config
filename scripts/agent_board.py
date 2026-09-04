#!/usr/bin/env python3
# TLDR: Scans local Claude Code / Codex session state (transcripts, Claude Code's own per-process
# registry for the exact pid<->session<->tmux mapping, tmux panes, hook self-registrations) plus
# optional SNAP node polling, and renders a self-refreshing HTML board + terminal table so you can
# see at a glance which agent session is working on what, and in which tmux window.

import argparse
import calendar
import glob
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time

HOME = os.path.expanduser("~")
BOARD_DIR = os.path.join(HOME, ".agent-board")
REGISTRY_DIR = os.path.join(BOARD_DIR, "sessions")
SNAP_CACHE = os.path.join(BOARD_DIR, "snap.json")
SUMMARY_CACHE = os.path.join(BOARD_DIR, "summaries.json")
# The summarizer runs `claude -p` with cwd=BOARD_DIR, so its own transcripts land in a
# project dir of their own and can be filtered out instead of appearing on the board.
SELF_PROJECT = "agent-board"
HOSTNAME = os.uname().nodename.split(".")[0].replace("Sanmis-MacBook-Air-2", "air")

# config dir -> short tag in Brando's notation
CONFIGS = {
    os.path.join(HOME, ".claude"): "cc",
    os.path.join(HOME, ".claude-vals"): "ccv",
}
SNAP_HOSTS = ["skampere1", "skampere2", "skampere3"]

LIVE_S = 120      # wrote within 2 min  -> live
IDLE_S = 30 * 60  # wrote within 30 min -> idle
BOOT_RE = re.compile(r"Claude Code v[\d.]+|^\s*[`▐▝▛█▀]")


SECTION_TITLES = [
    ("cc",  "Claude Code sessions — personal", "clauded / claude, ~/.claude"),
    ("ccv", "Claude Code sessions — Vals", "clauded-vals / claude-vals, ~/.claude-vals"),
]


def project_label(projects_dirname):
    """'-Users-sanmikoyejo-mba-1-veribench' -> 'veribench'."""
    return projects_dirname.rstrip("-").split("-")[-1] or projects_dirname


MODEL_RE = re.compile(r'"model":"(claude-[a-z0-9.-]+)"')
EFFORT_RE = re.compile(r'"effort":"([a-z]+)"')


def short_model(m):
    """claude-opus-5 -> opus5, claude-fable-5-1 -> fable5.1, claude-sonnet-5 -> sonnet5."""
    m = re.sub(r"^claude-", "", m or "")
    m = re.sub(r"-\d{8}$", "", m)
    parts = m.split("-")
    return (parts[0] + ".".join(parts[1:])) if parts and parts[0] else ""


def scan_transcript(path, max_lines=600, max_bytes=3_000_000):
    """One pass for the fields the board shows: topic, cwd, branch, model, effort."""
    topic, cwd, branch, model, effort = None, "", "", "", ""
    read = 0
    try:
        with open(path, errors="ignore") as fh:
            for i, ln in enumerate(fh):
                read += len(ln)
                if i > max_lines or read > max_bytes or (topic and cwd and model and effort):
                    break
                if len(ln) > 200_000:                # a giant tool result, never a user message
                    continue
                if not model:
                    mm = MODEL_RE.search(ln)
                    if mm:
                        model = mm.group(1)
                if not effort:
                    me = EFFORT_RE.search(ln)
                    if me:
                        effort = me.group(1)
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                cwd = cwd or d.get("cwd", "")
                branch = branch or d.get("gitBranch", "")
                if topic or d.get("type") != "user":
                    continue
                c = (d.get("message") or {}).get("content")
                if isinstance(c, str):
                    s = c
                elif isinstance(c, list):
                    s = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
                else:
                    continue
                s = " ".join(s.split())
                if s and not s.startswith("<") and "command-name" not in s and not BOOT_RE.search(s):
                    topic = s[:120]
    except OSError:
        pass
    return topic or "(no user message yet)", cwd, branch, model, effort


def short_path(cwd):
    """The working directory, fully expanded: the /Users/<name> prefix is what tells Brando
    which laptop a row is on (a DHCP hostname like DN5qw451345 does not), so no '~' and no
    tail-only shortening."""
    return cwd or ""


def first_topic(path, max_lines=400):
    """First substantive user message in a transcript — the session's de-facto title."""
    try:
        with open(path, errors="ignore") as fh:
            for i, ln in enumerate(fh):
                if i > max_lines:
                    break
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                if d.get("type") != "user":
                    continue
                msg = d.get("message") or {}
                c = msg.get("content")
                if isinstance(c, str):
                    t = c
                elif isinstance(c, list):
                    t = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
                else:
                    continue
                t = " ".join(t.split())
                if not t or t.startswith("<") or "command-name" in t or BOOT_RE.search(t):
                    continue
                return t[:120]
    except OSError:
        pass
    return "(no user message yet)"


def tmux_panes():
    """pane root pid -> tmux session name, for local tmux."""
    out = {}
    try:
        r = subprocess.run(
            ["tmux", "list-panes", "-a", "-F", "#{pane_pid}\t#{session_name}\t#{pane_current_command}"],
            capture_output=True, text=True, timeout=5)
        for ln in r.stdout.splitlines():
            parts = ln.split("\t")
            if len(parts) == 3:
                out[parts[0]] = (parts[1], parts[2])
    except Exception:
        pass
    return out


def process_table():
    """One ps call -> {pid: (ppid, start_epoch, command)}."""
    tab = {}
    try:
        r = subprocess.run(["ps", "ax", "-o", "pid=,ppid=,lstart=,command="],
                           capture_output=True, text=True, timeout=8)
    except Exception:
        return tab
    for ln in r.stdout.splitlines():
        f = ln.split(None, 7)
        if len(f) < 8:
            continue
        pid, ppid = f[0], f[1]
        try:
            start = time.mktime(time.strptime(" ".join(f[2:7]), "%a %b %d %H:%M:%S %Y"))
        except Exception:
            continue
        tab[pid] = (ppid, start, f[7])
    return tab


AGENT_RE = re.compile(r"(^|/)(claude|codex)(\s|$)|Claude Code")


def locate(pid, tab, panes, depth=12):
    """Walk up the process tree: which tmux window, or which app, is this agent sitting in?"""
    seen = 0
    while pid in tab and seen < depth:
        if pid in panes:
            return "tmux " + panes[pid][0]
        cmd = tab[pid][2]
        if "Cursor Helper" in cmd or "Cursor.app" in cmd:
            return "cursor"
        if "ChatGPT.app" in cmd:
            return "chatgpt"
        if "Code Helper" in cmd or "Visual Studio Code" in cmd:
            return "vscode"
        if "iTerm" in cmd:
            return "iterm"
        if "Terminal.app" in cmd:
            return "terminal"
        pid = tab[pid][0]
        seen += 1
    return "?"


def load_registry():
    """Session self-registrations written by the SessionStart hook."""
    reg = {}
    for f in glob.glob(os.path.join(REGISTRY_DIR, "*.json")):
        try:
            with open(f) as fh:
                d = json.load(fh)
            if isinstance(d, dict) and isinstance(d.get("session_id"), str):
                reg[d["session_id"]] = d
        except Exception:
            continue
    return reg


def _epoch_ms(v):
    """Claude Code's millisecond timestamps -> epoch seconds, 0 when absent or malformed."""
    try:
        v = float(v) / 1000
    except (TypeError, ValueError):
        return 0
    return v if v > 0 else 0


def _utc_ctime(s):
    """'Thu Sep  3 01:59:57 2026' (Claude Code's procStart, in UTC) -> epoch, else 0."""
    try:
        return calendar.timegm(time.strptime(str(s), "%a %b %d %H:%M:%S %Y"))
    except (TypeError, ValueError):
        return 0


def claude_registry(tab, panes):
    """sid -> [proc, ...] from Claude Code's own per-process registry.

    Every running `claude` writes <config>/sessions/<pid>.json (pid, sessionId, cwd and a
    "tmux" field like "8:@8.%8" = session:window.pane) and refreshes it while it runs, so this
    is the exact process<->session mapping; no start-time correlation needed. Files of exited
    processes linger, so an entry counts only while its pid is alive, is an agent process and
    started when the file says it did (a recycled pid fails that check). The tmux name comes
    from the live process tree first, so a pane moved to another session since launch is
    reported where it is now, and from the file only when the tree walk finds no pane.
    """
    out = {}
    for cfg_dir in CONFIGS:
        for f in glob.glob(os.path.join(cfg_dir, "sessions", "*.json")):
            try:
                with open(f) as fh:
                    d = json.load(fh)
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            sid, pid = d.get("sessionId"), str(d.get("pid") or "")
            info = tab.get(pid)
            if not isinstance(sid, str) or not sid or not info or not AGENT_RE.search(info[2]):
                continue
            started = _epoch_ms(d.get("startedAt")) or _utc_ctime(d.get("procStart"))
            updated = _epoch_ms(d.get("updatedAt"))
            if not started or abs(info[1] - started) > 120:
                continue          # no verifiable start time, or the pid was recycled
            loc = locate(pid, tab, panes)
            if loc.startswith("tmux "):
                sess = loc[5:]
            else:
                # tmux forbids ':' and '.' in session names, so the first field is the name
                sess = str(d.get("tmux") or "").split(":", 1)[0] or None
            out.setdefault(sid, []).append(
                {"pid": pid, "tmux": sess, "app": None if sess else loc, "updated": updated})
    for procs in out.values():
        procs.sort(key=lambda p: p["updated"], reverse=True)
    return out


def tmux_cell(names):
    """'tmux 8'. A session with live processes in several windows is emitted as one row per
    window by collect_sessions, so a multi-window cell only appears for other agent kinds."""
    names = [str(n) for n in names]
    if all(n.isdigit() for n in names):
        return "tmux " + ",".join(names)
    return ",".join(names)


def collect_sessions(max_age_h, show_all=False, tab=None, panes=None):
    now = time.time()
    reg = load_registry()
    tab = process_table() if tab is None else tab
    panes = tmux_panes() if panes is None else panes
    cc = claude_registry(tab, panes)

    paths = []
    for cfg_dir, tag in CONFIGS.items():
        for tpath in glob.glob(os.path.join(cfg_dir, "projects", "*", "*.jsonl")):
            try:
                st = os.stat(tpath)
            except OSError:
                continue
            if now - st.st_mtime > max_age_h * 3600:
                continue
            if os.path.basename(os.path.dirname(tpath)).endswith(SELF_PROJECT):
                continue
            sid = os.path.basename(tpath)[:-6]
            paths.append((cfg_dir, tag, tpath, st, sid))
    rows = []
    ecache, edirs = load_expt_cache(), local_experiment_dirs()
    for cfg_dir, tag, tpath, st, sid in paths:
            age = now - st.st_mtime
            proj_dir = os.path.basename(os.path.dirname(tpath))
            topic, cwd, branch, model, effort = scan_transcript(tpath)
            expt, expt_also = session_expt(tpath, "claude", ecache, edirs)
            procs = cc.get(sid, [])
            seats = [p["tmux"] for p in procs if p["tmux"]]
            # One row per live process. Two `claude --resume <id>` of the same session in two
            # windows are two seats and two forks of one transcript, so they are shown as two
            # rows that name each other, never merged into one "tmux 5,9" cell (Brando 2026-09-04).
            variants = []
            if procs:
                distinct = sorted(set(seats), key=lambda x: (len(str(x)), str(x)))
                if len(distinct) > 1:
                    for seat in distinct:
                        others = ",".join(o for o in distinct if o != seat)
                        pid = next((p["pid"] for p in procs if p["tmux"] == seat), "")
                        variants.append(([seat], tmux_cell([seat]), "live",
                                         f"same session id also running in tmux {others} "
                                         "(resumed twice = two forks of one transcript; keep one)",
                                         f" pid {pid}" if pid else ""))
                else:
                    # exact: a live process, from Claude Code's own registry
                    how, app = "live", procs[0]["app"]
                    cell = tmux_cell(seats) if seats else (app if app and app != "?" else "(no tmux)")
                    variants.append((seats, cell, how, "", ""))
            else:
                # no live process, so nothing to switch to. The SessionStart hook's record of
                # the window it ran in still groups it under that seat as history.
                t = reg.get(sid, {}).get("tmux")
                seats = [str(t)] if isinstance(t, (str, int)) and str(t) else []
                variants.append((seats, "\u2014", "exited", "", ""))
            label = tag
            for seats, cell, how, note, id_suffix in variants:
              rows.append({
                "sid": sid,
                "path": tpath,
                "short": sid[:8] + id_suffix,
                "tag": tag,
                "label": label,
                "tmux": seats[0] if seats else None,
                "seats": seats,
                "proc": bool(procs),
                "alive": bool(procs),
                "tmux_cell": cell,
                "tmux_how": how,
                "note": note,
                "project": project_label(proj_dir),
                "topic": topic,
                "cwd": cwd,
                "where": short_path(cwd) if cwd else HOSTNAME,
                "branch": branch,
                "model": short_model(model),
                "effort": effort,
                "mdl": (short_model(model) + ("+" + effort if effort else "")) if model else "?",
                "expt": expt,
                "expt_also": expt_also,
                "last": st.st_mtime,
                "age": age,
                "size_mb": round(st.st_size / 1e6, 1),
                "state": "live" if age < LIVE_S else ("idle" if age < IDLE_S else "stale"),
            })
    save_expt_cache(ecache)
    if not show_all:
        rows = one_per_seat(rows)
    summaries = load_summaries()
    for r in rows:
        s = summaries.get(r["sid"])
        if s and s.get("summary"):
            r["raw_topic"], r["topic"], r["summarized"] = r["topic"], s["summary"], True
            r["next"] = s.get("next", "")
        else:
            r["raw_topic"], r["summarized"], r["next"] = r["topic"], False, ""
    rows.sort(key=lambda r: r["last"], reverse=True)
    return collapse_fanout(rows)


def load_summaries():
    try:
        with open(SUMMARY_CACHE) as fh:
            return json.load(fh)
    except Exception:
        return {}


# ---------------------------------------------------------------- Expt column
# Which experiments/<NN_name> directory is this agent working in? Answered from the
# session's OWN actions and prose (cwd, the user's and assistant's text, the assistant's
# tool inputs: paths and commands), never from tool outputs -- one `cat CLAUDE.md` mentions
# every experiment in the repo. The value is the directory referenced most often in the last
# EXPT_WINDOW mentions, so a session that moved from expt 73 to expt 77 shows 77; a
# runner-up with at least half as many mentions is shown beneath it. A bare number
# (a clone named veribench_expt78, "expt 74" in prose) resolves through the local
# experiments tree. "-" = the session never referenced an experiment.

EXPT_CACHE = os.path.join(BOARD_DIR, "expts.json")
EXPT_V = 2   # bump when the scan or naming rule changes, so cached values are recomputed
EXPT_DIR_RE = re.compile(r"experiments/(\d+_[A-Za-z0-9][A-Za-z0-9._-]*)")
EXPT_NUM_RE = re.compile(r"(?<![A-Za-z0-9])expt[_ -]?(\d{1,4})(?![0-9])", re.IGNORECASE)
EXPT_WINDOW = 200


def _blocks_text(content, kinds):
    """The text of the given block types from a Claude / Codex message content list."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return " ".join(str(b.get("text") or "") for b in content
                    if isinstance(b, dict) and b.get("type") in kinds)


def _tool_input_text(inp):
    if isinstance(inp, dict):
        return " ".join(str(v) for v in inp.values() if isinstance(v, (str, int, float)))
    return str(inp or "")


def _claude_own_text(d):
    """One Claude transcript line -> the text that reflects the session's own work."""
    t = d.get("type")
    parts = [str(d.get("cwd") or "")]
    msg = d.get("message") or {}
    c = msg.get("content") if isinstance(msg, dict) else None
    if t == "user":
        parts.append(_blocks_text(c, ("text",)))          # tool_result blocks are skipped
    elif t == "assistant":
        parts.append(_blocks_text(c, ("text",)))
        if isinstance(c, list):
            parts.extend(_tool_input_text(b.get("input")) for b in c
                         if isinstance(b, dict) and b.get("type") == "tool_use")
    return " ".join(parts)


def _codex_own_text(d):
    """One Codex rollout line -> session cwd, messages and tool calls; never tool outputs."""
    p = d.get("payload")
    if not isinstance(p, dict):
        return ""
    t = d.get("type")
    if t == "session_meta":
        return str(p.get("cwd") or "")
    if t != "response_item":
        return ""
    pt = p.get("type")
    if pt == "message":
        return _blocks_text(p.get("content"), ("input_text", "output_text", "text"))
    if pt == "function_call":
        return str(p.get("arguments") or "")
    if pt == "custom_tool_call":
        return str(p.get("input") or "")
    return ""


def scan_expt_mentions(path, kind):
    """Ordered experiment mentions from a transcript: '77_iclr2027_main_table', or '#77'
    when only a number is visible. Each line contributes each name at most once."""
    own = _claude_own_text if kind == "claude" else _codex_own_text
    mentions = []
    try:
        with open(path, errors="ignore") as fh:
            for ln in fh:
                if len(ln) > 200_000:
                    continue
                low = ln.lower()
                if "experiments/" not in low and "expt" not in low:
                    continue
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                if not isinstance(d, dict):
                    continue
                s = own(d)
                if not s:
                    continue
                seen_here = []
                for m in EXPT_DIR_RE.findall(s) + ["#" + n for n in EXPT_NUM_RE.findall(s)]:
                    if m not in seen_here:
                        seen_here.append(m)
                mentions.extend(seen_here)
    except OSError:
        pass
    return mentions


def pick_expt(mentions, dirs, window=EXPT_WINDOW):
    """(primary, runner-up) directory names from the last `window` mentions."""
    recent = mentions[-window:]
    if not recent:
        return "-", ""

    local = {os.path.basename(d) for d in dirs.values()}

    def name(m):
        if not m.startswith("#"):
            # a renumbered or foreign-repo directory is shown as referenced, plainly marked
            return m if m in local else f"{m} (not in ~/veribench/experiments)"
        d = dirs.get(m[1:])
        return os.path.basename(d) if d else f"expt {m[1:]} (no local dir)"

    counts, last = {}, {}
    for i, m in enumerate(recent):
        n = name(m)
        counts[n] = counts.get(n, 0) + 1
        last[n] = i
    ranked = sorted(counts, key=lambda n: (counts[n], last[n]), reverse=True)
    top = ranked[0]
    also = ranked[1] if len(ranked) > 1 and counts[ranked[1]] * 2 >= counts[top] else ""
    return top, also


def load_expt_cache():
    try:
        with open(EXPT_CACHE) as fh:
            c = json.load(fh)
        return c if isinstance(c, dict) else {}
    except Exception:
        return {}


def save_expt_cache(cache):
    now = time.time()
    for k in [k for k, v in cache.items() if now - (v or {}).get("at", 0) > 7 * 86400]:
        del cache[k]
    try:
        os.makedirs(BOARD_DIR, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=BOARD_DIR, suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(cache, fh)
        os.replace(tmp, EXPT_CACHE)
    except Exception:
        pass


def session_expt(path, kind, cache, dirs):
    """Cached by transcript size+mtime, so only transcripts that grew are rescanned."""
    try:
        st = os.stat(path)
    except OSError:
        return "-", ""
    c = cache.get(path)
    if (isinstance(c, dict) and c.get("v") == EXPT_V and c.get("size") == st.st_size
            and abs(c.get("mtime", 0) - st.st_mtime) < 1 and c.get("expt")):
        return c["expt"], c.get("also", "")
    top, also = pick_expt(scan_expt_mentions(path, kind), dirs)
    cache[path] = {"v": EXPT_V, "size": st.st_size, "mtime": st.st_mtime, "expt": top,
                   "also": also, "at": time.time()}
    return top, also


def one_per_seat(rows, keep_stale=False):
    """A tmux window is one seat: the agent you have "on" there is the newest transcript in
    it. Older transcripts in the same window are that seat's history, not extra agents."""
    seen, out = {}, []
    # Every session with a live process is shown, whatever its window (a `claude -p` child
    # shares its parent's pane). A transcript with no live process is history: folded into
    # the seat holder's "+N earlier here" when its window is taken, shown only if it is free.
    for r in sorted(rows, key=lambda r: (not r.get("proc"), -r["last"])):
        keys = [(r["tag"], s) for s in (r.get("seats") or [])]
        taken = [k for k in keys if k in seen]
        if taken and not r.get("proc"):
            seen[taken[0]]["prior"] += 1
            continue
        r["prior"] = 0
        for k in keys:
            seen.setdefault(k, r)
        # a seatless, dead transcript is kept only while it is still moving
        if keys or keep_stale or r.get("proc") or r["state"] != "stale":
            out.append(r)
    return out


def collapse_fanout(rows, threshold=3):
    """A `-p` fan-out (N judges, N reviewers) is one job, not N sessions worth reading."""
    groups, order = {}, []
    for r in rows:
        key = (r["tag"], r["project"], r["topic"][:45])
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)
    out = []
    for key in order:
        g = groups[key]
        if len(g) >= threshold and all(x["state"] == "stale" and not x.get("alive") for x in g):
            head = dict(g[0])
            head["short"] = f"x{len(g)} sessions"
            head["label"] = head["tag"] + " (fan-out)"
            head["topic"] = head["topic"]
            out.append(head)
        else:
            out.extend(g)
    return out


CODEX_DIR = os.path.join(HOME, ".codex")
CODEX_RE = re.compile(r"(^|/)codex(\s|$)")


def scan_rollout(path, max_lines=300):
    """(start_epoch, cwd, originator, model, effort) from a Codex rollout transcript: the
    session_meta line carries the start time and cwd, the first turn_context the model."""
    start, cwd, orig, model, effort = None, "", "", "", ""
    try:
        with open(path, errors="ignore") as fh:
            for i, ln in enumerate(fh):
                if i > max_lines or (start and model):
                    break
                if len(ln) > 200_000 or ('"session_meta"' not in ln and '"turn_context"' not in ln):
                    continue
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                if not isinstance(d, dict):
                    continue
                p = d.get("payload") or {}
                if not isinstance(p, dict):
                    continue
                if d.get("type") == "session_meta":
                    ts = str(p.get("timestamp") or d.get("timestamp") or "")
                    try:
                        start = calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))
                    except Exception:
                        pass
                    cwd, orig = str(p.get("cwd") or ""), str(p.get("originator") or "")
                elif d.get("type") == "turn_context":
                    model = str(p.get("model") or model)
                    cm = p.get("collaboration_mode")
                    cm = cm.get("settings") if isinstance(cm, dict) else None
                    cm = cm if isinstance(cm, dict) else {}
                    effort = str(p.get("effort") or p.get("reasoning_effort")
                                 or cm.get("reasoning_effort") or effort)
    except OSError:
        pass
    return start, cwd, orig, model, effort


def collect_codex(max_age_h, tab, panes, limit=8):
    """Recent Codex threads from the local session index, as board rows.

    Codex keeps no pid registry, so a thread is tied to its process by the one fact both
    record: the thread's start time (rollout session_meta) is the start of the `codex`
    process that created it, to within a few seconds. Only interactive / exec processes
    qualify (the ChatGPT and Cursor app-servers are not agents you sit at); each process is
    claimed once, closest thread first, and its tmux window comes from the process tree.
    """
    idx = os.path.join(CODEX_DIR, "session_index.jsonl")
    seen = {}
    try:
        with open(idx, errors="ignore") as fh:
            for ln in fh:
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                if isinstance(d, dict) and d.get("id"):
                    seen[d["id"]] = d  # later lines win
    except OSError:
        return []
    now = time.time()
    threads = []
    for d in seen.values():
        ts = str(d.get("updated_at", ""))
        try:
            t = calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))  # index is UTC
        except Exception:
            continue
        if now - t <= max_age_h * 3600:
            threads.append((t, d))
    threads.sort(key=lambda x: x[0], reverse=True)

    procs = [(pid, start) for pid, (_p, start, cmd) in tab.items()
             if CODEX_RE.search(cmd) and "app-server" not in cmd and " sandbox " not in cmd]
    rows, claimed = [], set()
    ecache, edirs = load_expt_cache(), local_experiment_dirs()
    for t, d in threads[:limit]:
        tid = str(d["id"])
        hits = (glob.glob(os.path.join(CODEX_DIR, "sessions", "*", "*", "*", f"rollout-*-{tid}.jsonl"))
                if re.fullmatch(r"[0-9a-f-]{8,64}", tid) else [])
        start, cwd, orig, model, effort = scan_rollout(hits[0]) if hits else (None, "", "", "", "")
        expt, expt_also = session_expt(hits[0], "codex", ecache, edirs) if hits else ("-", "")
        cell, seats = "—", []
        if start:
            near = sorted((abs(s - start), pid) for pid, s in procs
                          if pid not in claimed and abs(s - start) <= 15)
            if near:
                pid = near[0][1]
                claimed.add(pid)
                loc = locate(pid, tab, panes)
                if loc.startswith("tmux "):
                    seats, cell = [loc[5:]], tmux_cell([loc[5:]])
                else:
                    cell = loc if loc != "?" else "(no tmux)"
        age = now - t
        rows.append({
            "sid": tid, "short": tid[:8], "tag": "cxd", "label": "cxd",
            "tmux_cell": cell, "seats": seats, "proc": cell != "—", "alive": cell != "—",
            "where": short_path(cwd) if cwd else HOSTNAME,
            "branch": orig, "mdl": (model + ("+" + effort if effort else "")) if model else "?",
            "expt": expt, "expt_also": expt_also,
            "topic": str(d.get("thread_name") or "")[:120], "next": "", "prior": 0,
            "last": t, "age": age,
            "state": "live" if age < LIVE_S else ("idle" if age < IDLE_S else "stale"),
        })
    save_expt_cache(ecache)
    return rows


def poll_snap(timeout=10, max_age=600):
    """Skip the ssh round-trip when the cache is still fresh."""
    cached = read_snap_cache()
    if cached and time.time() - cached.get("at", 0) < max_age:
        return cached["hosts"]
    return _poll_snap_now(timeout)


def _poll_snap_now(timeout=10):
    """SSH each SNAP node. A failed poll keeps that host's previous data, marked stale,
    instead of replacing it with an empty (falsely healthy) result."""
    prev = {h["host"]: h for h in ((read_snap_cache() or {}).get("hosts", []))}
    out = []
    for h in SNAP_HOSTS:
        entry = {"host": h, "tmux": [], "procs": "0", "error": None, "at": time.time()}
        try:
            r = subprocess.run(
                ["ssh", "-o", f"ConnectTimeout={timeout}", "-o", "BatchMode=yes",
                 f"brando9@{h}.stanford.edu",
                 # panes (session, pane pid, activity, cwd) + the node's process table + the
                 # args of my own processes (agent kind, model) + my codex defaults; the
                 # descendant walk happens locally so "running" means a real non-shell
                 # process under the pane, not whatever the pane's foreground command is
                 "tmux list-panes -a -F '#{session_name}\t#{pane_pid}\t#{session_activity}\t"
                 "#{pane_current_path}' 2>/dev/null; "
                 "echo '=PS='; ps -e -o pid=,ppid=,comm= 2>/dev/null; "
                 "echo '=ARGS='; ps -u $USER -o pid=,args= 2>/dev/null; "
                 "echo '=CFG='; grep -E '^(model|model_reasoning_effort) *=' "
                 "~/.codex/config.toml 2>/dev/null; "
                 "echo '=N='; pgrep -c codex 2>/dev/null || echo 0"],
                capture_output=True, text=True, timeout=timeout + 15)
            if r.returncode != 0:
                raise RuntimeError(f"ssh exit {r.returncode}")
            panes_txt, _, rest = r.stdout.partition("=PS=")
            ps_txt, _, rest = rest.partition("=ARGS=")
            args_txt, _, rest = rest.partition("=CFG=")
            cfg_txt, _, procs = rest.partition("=N=")
            kids, comm, args, default = {}, {}, {}, {}
            for ln in ps_txt.splitlines():
                f = ln.split(None, 2)
                if len(f) == 3:
                    kids.setdefault(f[1], []).append(f[0])
                    comm[f[0]] = os.path.basename(f[2]).strip()
            for ln in args_txt.splitlines():
                f = ln.split(None, 1)
                if len(f) == 2:
                    args[f[0]] = f[1].strip()
            for ln in cfg_txt.splitlines():
                k, _, v = ln.partition("=")
                default[k.strip()] = v.strip().strip('"').strip("'")
            seen = {}
            for ln in panes_txt.splitlines():
                # tab-separated: a comma may legally appear in a session name or a path
                name, ppid, act, path = (ln.rstrip("\n").split("\t", 3) + ["", "", ""])[:4]
                name = name.strip()
                if not name:
                    continue
                try:
                    act = float(act)
                except ValueError:
                    act = 0
                # every descendant of the pane shell, shallowest first, depth-limited
                stack, desc, n = [(k, 1) for k in kids.get(ppid, [])], [], 0
                while stack and n < 400:
                    pid, depth = stack.pop(0); n += 1
                    desc.append(pid)
                    stack.extend((k, depth + 1) for k in kids.get(pid, []))
                s = seen.setdefault(name, {"name": name, "activity": act, "cmds": [],
                                           "args": [], "path": path})
                s["cmds"].extend(comm[p] for p in desc if comm.get(p))
                s["args"].extend(args[p] for p in desc if p in args)
                s["path"] = s["path"] or path
                s["activity"] = max(s["activity"], act)
            for s in seen.values():
                s["agent"], s["mdl"] = snap_agent(s.pop("args"), default)
            entry["tmux"] = list(seen.values())
            toks = procs.split()
            entry["procs"] = toks[-1] if toks else "0"
        except Exception as e:
            old = prev.get(h, {})
            entry.update({"tmux": old.get("tmux", []), "procs": old.get("procs", "?"),
                          "error": str(e) if isinstance(e, RuntimeError) else type(e).__name__,
                          "at": old.get("at", 0)})
        out.append(entry)
    os.makedirs(BOARD_DIR, exist_ok=True)
    with open(SNAP_CACHE, "w") as fh:
        json.dump({"at": time.time(), "hosts": out}, fh)
    return out


def snap_agent(args, default):
    """(agent tag, model+effort) for one SNAP pane from its descendant command lines,
    shallowest first. Only the executable decides the kind (`codex`, `node .../codex`,
    `claude`) -- never a file name or prompt text further down the line -- and the model is
    read from that agent's own leading options (`-m`/`--model`, `model_reasoning_effort=`),
    else from the node's ~/.codex/config.toml defaults. An em dash means only shells run."""
    for a in args:
        toks = str(a).split()
        exe = os.path.basename(toks[0]) if toks else ""
        if exe in ("node", "nodejs") and len(toks) > 1:
            exe, toks = os.path.basename(toks[1]), toks[1:]
        if exe not in ("codex", "claude"):
            continue
        head = " ".join(toks[1:17])          # options come first; the prompt is last
        if exe == "codex":
            m = re.search(r"(?:^|\s)(?:-m|--model)[ =]([\w.\-]+)", head)
            e = re.search(r"model_reasoning_effort\s*=\s*[\"']?([A-Za-z]+)", head)
            model = m.group(1) if m else default.get("model", "")
            effort = e.group(1) if e else default.get("model_reasoning_effort", "")
            return "cxd", (model + ("+" + effort if effort else "")) if model else "?"
        m = re.search(r"(?:^|\s)--model[ =]([\w.\-\[\]]+)", head)
        return "cc", (short_model(m.group(1)) if m else "?")
    return "—", ""


def read_snap_cache():
    """The cached poll, or None; only well-formed host entries survive (the file is rewritten
    by every poll, so a torn or foreign file must not take the board down)."""
    try:
        with open(SNAP_CACHE) as fh:
            c = json.load(fh)
    except Exception:
        return None
    if not isinstance(c, dict) or not isinstance(c.get("hosts"), list):
        return None
    hosts = [h for h in c["hosts"] if isinstance(h, dict) and isinstance(h.get("host"), str)]
    try:
        at = float(c.get("at") or 0)
    except (TypeError, ValueError):
        at = 0
    return {"at": at, "hosts": hosts}


EXP_ROOT = os.path.join(HOME, "veribench", "experiments")
IGNORE_TMUX = {"job_watcher", "snaphealth", "codex_handoff", "lean_env_prep"}
# SNAP tmux names that carry no experiment number of their own
JOB_ALIASES = {"gold_sorry_closure": "75", "judge_val": "73", "judge_val_A": "73"}
# Optional state pushed in by something this script cannot see itself (e.g. a scheduled
# agent that reads completion mail sent to brando.science). Shape:
#   {"<job or expt number>": {"state": "DONE", "note": "...", "at": <epoch>}}
EXTERNAL = os.path.join(BOARD_DIR, "external.json")
STALL_S = 20 * 60   # a job with no tmux activity this long is probably finished or wedged
SHELLS = {"bash", "zsh", "sh", "fish", "tmux", "sleep", "tail", "less", "vim", "vi", "nano", "ps", ""}
# a pane whose only descendants are shells / pagers / a `sleep` loop has no job running in it


def git(*args, cwd=None):
    """stdout on success, None on failure (so callers can tell 'no commits' from 'git broke').
    GIT_OPTIONAL_LOCKS=0: a read-only `git status` from a 20-second loop must never take
    .git/index.lock -- a lock left behind by an interrupted run blocks every session's pull."""
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    try:
        r = subprocess.run(["git", *args], cwd=cwd or os.path.join(HOME, "veribench"),
                           capture_output=True, text=True, timeout=10, env=env)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


GIT_CACHE = os.path.join(BOARD_DIR, "gitstate.json")


def experiment_git_state(dirs, cache_s=60):
    """{num: [dirty, last_commit_epoch, subject]} + ok flag. One `git status` and ONE `git log`
    for the whole experiments tree (not two per dir), cached 60s so the 20s loop stays cheap."""
    try:
        with open(GIT_CACHE) as fh:
            c = json.load(fh)
        if time.time() - c.get("at", 0) < cache_s:
            return c["state"], c["ok"]
    except Exception:
        pass
    ok, state = True, {}
    status = git("status", "--porcelain", "--", EXP_ROOT)
    if status is None:
        ok, status = False, ""
    dirty = {m.group(1) for m in (re.search(r"experiments/(\d+)_", ln) for ln in status.splitlines()) if m}
    log = git("log", "--format=%x1e%ct%x1f%s", "--name-only", "-n", "400", "--", EXP_ROOT)
    if log is None:
        ok, log = False, ""
    latest = {}
    for rec in log.split("\x1e"):
        head, _, files = rec.partition("\n")
        ct, _, subj = head.partition("\x1f")
        for f in files.splitlines():
            m = re.match(r"experiments/(\d+)_", f.strip())
            if m and m.group(1) not in latest:
                try:
                    latest[m.group(1)] = (float(ct), subj[:58])
                except ValueError:
                    pass
    for num in dirs:
        ct, subj = latest.get(num, (None, ""))
        state[num] = [num in dirty, ct, subj]
    try:
        os.makedirs(BOARD_DIR, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=BOARD_DIR, suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump({"at": time.time(), "state": state, "ok": ok}, fh)
        os.replace(tmp, GIT_CACHE)
    except Exception:
        pass
    return state, ok


def local_experiment_dirs():
    out = {}
    for d in sorted(glob.glob(os.path.join(EXP_ROOT, "[0-9]*_*"))):
        m = re.match(r"(\d+)_", os.path.basename(d))
        if m:
            out[m.group(1)] = d
    return out


def short_remote(path):
    """A SNAP working directory, fully expanded (Brando reads the /lfs/<node>/0/brando9 or
    /dfs/scratch0/brando9 prefix as the filesystem it lives on)."""
    return path or ""


def collect_experiments(snap):
    """One board row per SNAP tmux job, crossed with repo state to answer: which experiments
    are DONE but unlanded? Same columns as the local session tables: the tmux cell is the
    byobu/tmux session name on that node, Id the experiment number, Where host:cwd."""
    dirs = local_experiment_dirs()
    now = time.time()
    try:
        with open(EXTERNAL) as fh:
            external = json.load(fh)
    except Exception:
        external = {}

    gstate, git_ok = experiment_git_state(dirs)

    jobs = {}
    for h in (snap or {}).get("hosts", []):
        if not isinstance(h, dict) or not isinstance(h.get("host"), str):
            continue
        for s in (h.get("tmux") or []):
            if not isinstance(s, dict):
                s = {"name": str(s)}
            name = str(s.get("name") or "")
            if not name or name in IGNORE_TMUX:
                continue
            try:
                act = float(s.get("activity") or 0)
            except (TypeError, ValueError):
                act = 0
            num = JOB_ALIASES.get(name)
            if not num:
                m = re.search(r"(\d+)", name)
                num = m.group(1) if m else None
            key = (num, name, h["host"])            # the same name may run on two nodes
            idle = now - act if act else None
            cmds = s.get("cmds")
            cmds = [str(c) for c in cmds] if isinstance(cmds, list) else None
            busy = None if cmds is None else any(c not in SHELLS for c in cmds)
            jobs[key] = {"num": num, "job": name, "host": h["host"], "idle": idle, "busy": busy,
                         "cmds": sorted({c for c in (cmds or []) if c not in SHELLS})[:4],
                         "path": str(s.get("path") or ""), "agent": str(s.get("agent") or ""),
                         "mdl": str(s.get("mdl") or ""), "stale": bool(h.get("error"))}

    rows = []
    for (num, name, _host), j in sorted(jobs.items(),
                                        key=lambda kv: (kv[0][0] or "zz", kv[0][1], kv[0][2])):
        d = dirs.get(num)
        is_dirty, ct, subject = gstate.get(num, [False, None, ""])
        commit_age = now - ct if ct else None

        if j["busy"] is True:
            state = "RUNNING"                       # a non-shell process is alive in the pane
        elif j["busy"] is None and j["idle"] is not None and j["idle"] < STALL_S:
            state = "RUNNING?"                      # old cache: activity only, no process check
        elif not git_ok:
            state = "??  git unavailable"
        elif is_dirty:
            state = "DONE?  results uncommitted"
        elif commit_age is not None and j["idle"] is not None and commit_age < j["idle"]:
            state = "LANDED"
        elif d is None:
            state = "DONE?  no local expt dir"
        else:
            state = "DONE?  nothing landed"

        ext = external.get(name) or external.get(num or "")
        if ext and ext.get("state"):
            state = f"{ext['state']}  (reported)"

        notes = []
        if j["cmds"]:
            notes.append("running: " + ", ".join(j["cmds"][:3]))
        if commit_age is not None:
            notes.append(f"landed {ago(commit_age)} ago" + (f": {subject}" if subject else ""))
        if ext and ext.get("note"):
            notes.append(str(ext["note"]))
        if j["stale"]:
            notes.append("(stale poll: showing the last successful ssh data)")
        cls = ("idle" if state.startswith("DONE") else
               "live" if state.startswith("RUNNING") else "stale")
        rows.append({
            "sid": f"{j['host']}:{name}", "short": num or "?", "tag": "snap",
            "label": j["agent"] or "—", "tmux_cell": name, "seats": [],
            "proc": j["busy"] is True, "alive": j["busy"] is True,
            "where": f"{j['host']}:{short_remote(j['path'])}" if j["path"] else j["host"],
            "branch": "",
            "expt": os.path.basename(d) if d else (f"expt {num} (no local dir)" if num else "-"),
            "expt_also": "",
            "mdl": j["mdl"] or "?", "topic": state, "next": "", "note": " · ".join(notes),
            "prior": 0, "last": (now - j["idle"]) if j["idle"] is not None else 0,
            "age": j["idle"], "state": cls, "dirty": is_dirty, "job": name, "host": j["host"],
        })
    return rows


SUMMARY_V = 2   # bump to invalidate cached summaries after a prompt change

SUMMARY_PROMPT = """Below is a digest of one Claude Code session: the user's messages, \
oldest first. Reply with EXACTLY two lines and nothing else:

WHAT: one sentence (max 25 words, third person) saying what this session is working on, \
concrete enough to tell it apart from other sessions on the same repo.
NEXT: one sentence (max 20 words) suggesting the most useful next action for this session, \
starting with a verb. If it looks finished, say what to verify or land.

No preamble, no quotes, no markdown.

--- session digest ---
%s
--- end digest ---"""


def session_digest(path, head=2, tail=6, cap=260):
    """The user's own messages are the cheapest accurate signal of what a session is doing."""
    msgs = []
    try:
        with open(path, errors="ignore") as fh:
            for ln in fh:
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                if d.get("type") != "user":
                    continue
                c = (d.get("message") or {}).get("content")
                if isinstance(c, str):
                    m = c
                elif isinstance(c, list):
                    m = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
                else:
                    continue
                m = " ".join(m.split())
                # drop tool results, hook noise and the CLI banner
                if not m or m.startswith("<") or "command-name" in m or BOOT_RE.search(m):
                    continue
                if "tool_use_id" in m or m.startswith("[Request interrupted"):
                    continue
                msgs.append(m[:cap])
    except OSError:
        return ""
    if len(msgs) > head + tail:
        msgs = msgs[:head] + ["..."] + msgs[-tail:]
    return "\n".join(f"- {m}" for m in msgs)


def _child_env():
    e = dict(os.environ)
    for k in ("CLAUDE_CODE_EFFORT_LEVEL", "CLAUDE_EFFORT"):
        e.pop(k, None)
    e["AGENT_BOARD_SUMMARIZER"] = "1"
    return e


def summarize(rows, limit=6, min_growth=40_000, max_age=1800, model="claude-sonnet-5",
              verbose=False):
    """Top up ~/.agent-board/summaries.json. Out of band: never called by the render loop."""
    cache = load_summaries()
    now = time.time()
    todo = []
    for r in rows:
        c = cache.get(r["sid"])
        try:
            size = os.path.getsize(r["path"])
        except OSError:
            continue
        if (c is None
                or c.get("v") != SUMMARY_V
                or now - c.get("at", 0) > max_age
                or size - c.get("size", 0) > min_growth):
            todo.append((r, size))
    todo.sort(key=lambda x: x[0]["last"], reverse=True)

    done = 0
    for r, size in todo[:limit]:
        digest = session_digest(r["path"])
        if not digest:
            continue
        try:
            # CLI-only: never a direct provider API call (agents-config Hard Rule 9)
            proc = subprocess.run(
                ["claude", "-p", "--model", model, SUMMARY_PROMPT % digest],
                capture_output=True, text=True, cwd=BOARD_DIR, timeout=180,
                env=_child_env())
            what, nxt = "", ""
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.upper().startswith("WHAT:"):
                    what = line[5:].strip()[:200]
                elif line.upper().startswith("NEXT:"):
                    nxt = line[5:].strip()[:200]
            out = what or " ".join(proc.stdout.split())[:200]
        except Exception as e:
            if verbose:
                print(f"  ! {r['short']}: {type(e).__name__}")
            continue
        if out:
            cache[r["sid"]] = {"summary": out, "next": nxt, "at": now,
                               "size": size, "v": SUMMARY_V}
            done += 1
            if verbose:
                print(f"  + {r['short']}  {out[:88]}")

    for sid in [k for k in cache if now - cache[k].get("at", 0) > 7 * 86400]:
        del cache[sid]
    os.makedirs(BOARD_DIR, exist_ok=True)
    tmp = SUMMARY_CACHE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(cache, fh, indent=1)
    os.replace(tmp, SUMMARY_CACHE)
    return done


NET_CACHE = os.path.join(BOARD_DIR, "net.json")


def stanford_status(cache_s=60):
    """Can we reach SNAP, and is there a live Kerberos ticket? Cached so the 20s loop is cheap."""
    try:
        with open(NET_CACHE) as fh:
            c = json.load(fh)
        if time.time() - c.get("at", 0) < cache_s:
            return c
    except Exception:
        pass

    import socket
    reachable = False
    try:
        socket.create_connection(("skampere1.stanford.edu", 22), timeout=2.5).close()
        reachable = True
    except Exception:
        pass

    ticket, expires = False, ""
    try:
        r = subprocess.run(["klist"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            for ln in r.stdout.splitlines():
                if "krbtgt/" in ln:      # "Sep  3 12:04:54 2026  Sep  3 22:04:54 2026  krbtgt/..."
                    parts = ln.split()
                    if len(parts) >= 9:
                        expires, ticket = " ".join(parts[4:7]), True
                        break
    except Exception:
        pass

    c = {"at": time.time(), "reachable": reachable, "ticket": ticket, "expires": expires}
    try:
        os.makedirs(BOARD_DIR, exist_ok=True)
        tmp = NET_CACHE + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(c, fh)
        os.replace(tmp, NET_CACHE)
    except Exception:
        pass
    return c


def ago(sec):
    if sec is None:
        return "?"
    if sec < 60:
        return f"{int(sec)}s"
    if sec < 3600:
        return f"{int(sec // 60)}m"
    if sec < 86400:
        return f"{int(sec // 3600)}h{int((sec % 3600) // 60):02d}"
    return f"{int(sec // 86400)}d"


# ---------------------------------------------------------------- renderers

def build_sections(sessions, codex, experiments, snap):
    """The board is one row schema everywhere; only the grouping differs. Local Claude Code
    per config, local Codex, then the SNAP jobs (with the per-node summary as the note)."""
    secs = [{"title": title, "sub": sub, "rows": [s for s in sessions if s["tag"] == tag]}
            for tag, title, sub in SECTION_TITLES]
    secs.append({"title": "Codex — local", "sub": "codex / codex exec, ~/.codex",
                 "rows": codex})
    note = ""
    if snap:
        stamp = time.strftime("%H:%M", time.localtime(snap.get("at", 0)))
        bits = []
        for h in snap.get("hosts", []):
            if not isinstance(h, dict):
                continue
            names = [str(s.get("name", "")) if isinstance(s, dict) else str(s)
                     for s in (h.get("tmux") or [])]
            infra = [n for n in names if n in IGNORE_TMUX]
            b = f"{h.get('host', '?')}: {len(names)} tmux sessions, {h.get('procs', '?')} codex procs"
            if infra:
                b += f" (infra: {', '.join(infra)})"
            if h.get("error"):
                b += f" [stale: {h['error']}]"
            bits.append(b)
        note = f"polled {stamp} · " + " · ".join(bits)
    secs.append({"title": "SNAP — jobs in tmux/byobu on the cluster",
                 "sub": "ssh brando9@<host>.stanford.edu; tmux attach -t <tmux>",
                 "rows": experiments, "note": note})
    return secs


COLS_TEXT = (f"  {'TMUX':<20} {'AGENT':<6} {'ID':<9} {'WHERE':<40} {'MDL+EFF':<17} "
             f"{'EXPT':<26} {'LAST':>5}  TASK")
COLS_RULE = (f"  {'-' * 20} {'-' * 6} {'-' * 9} {'-' * 40} {'-' * 17} {'-' * 26} {'-' * 5}  "
             f"{'-' * 34}")
COLS_PAD = f"  {'':<20} {'':<6} {'':<9} {'':<40} {'':<17} {'':<26} {'':>5}  "


def render_text(sections, net=None, panes=None):
    W = "\033[0m"
    C = {"live": "\033[32m", "idle": "\033[33m", "stale": "\033[90m"}
    if net:
        if net.get("reachable"):
            tick = f"kerberos until {net['expires']}" if net.get("ticket") else "NO kerberos ticket (run kinit)"
            print(f"\n  \U0001F7E2 Stanford / SNAP reachable   \033[90m{tick}\033[0m")
        else:
            print("\n  \U0001F534 No Stanford access — connect the VPN "
                  "\033[90m(SNAP nodes unreachable)\033[0m")
    print(f"\n  \033[32m●\033[0m working now (<2m / job RUNNING)   "
          f"\033[33m●\033[0m waiting on you (2-30m / results not landed)   "
          f"\033[90m●\033[0m idle / finished (>30m / LANDED)")
    rows_all = [s for sec in sections for s in sec["rows"]]
    print(f"\n  AGENT BOARD — {time.strftime('%a %d %b %H:%M:%S')}"
          f"   ({sum(1 for s in rows_all if s['state'] == 'live')} working,"
          f" {len(rows_all)} rows)\n")
    for sec in sections:
        rows = sec["rows"]
        nlive = sum(1 for s in rows if s["state"] == "live")
        print(f"  {sec['title'].upper()}  ({nlive} live / {len(rows)})   \033[90m{sec['sub']}\033[0m")
        if sec.get("note"):
            print(f"  \033[90m{sec['note']}\033[0m")
        print(COLS_TEXT)
        print(COLS_RULE)
        if not rows:
            print("  (none)")
        for s in rows:
            c = C.get(s["state"], "")
            prior = f"  \033[90m(+{s['prior']})\033[0m" if s.get("prior") else ""
            print(f"  \033[1m{s['tmux_cell'][:20]:<20}\033[0m {c}{s['label'][:6]:<6} "
                  f"{s['short'][:9]:<9} {s['where'][-40:]:<40} {s['mdl'][:17]:<17} "
                  f"{(s.get('expt') or '-')[:26]:<26} "
                  f"{ago(s['age']):>5}  {s['topic'][:34]}{W}{prior}")
            if s.get("next"):
                print(f"{COLS_PAD}\033[1mnext:\033[0m {s['next'][:64]}")
            elif s.get("note"):
                print(f"{COLS_PAD}\033[90m{s['note'][:72]}\033[0m")
        print()
    if panes is not None:
        live_panes = sum(1 for _, (_, cmd) in panes.items()
                         if "codex" in cmd or cmd[:1].isdigit())
        print(f"\n  local tmux panes running an agent: {live_panes}\n")


CSS = """
:root{--bg:#fbfaf8;--fg:#1c1b19;--mut:#6b6862;--line:#e5e1da;--card:#fff;
      --live:#1a7f4b;--idle:#a8730a;--stale:#9a958d;--accent:#3b5bdb}
:root:not([data-theme=light]) @media (prefers-color-scheme:dark){}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
  --bg:#141311;--fg:#ece9e3;--mut:#9a958d;--line:#2c2a26;--card:#1c1b19;
  --live:#4ade80;--idle:#fbbf24;--stale:#6b6862;--accent:#8ea3ff}}
:root[data-theme=dark]{--bg:#141311;--fg:#ece9e3;--mut:#9a958d;--line:#2c2a26;--card:#1c1b19;
  --live:#4ade80;--idle:#fbbf24;--stale:#6b6862;--accent:#8ea3ff}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);margin:0;padding:28px 22px 60px;
  font:14px/1.5 ui-sans-serif,-apple-system,"SF Pro Text",system-ui,sans-serif}
.wrap{max-width:1060px;margin:0 auto}
h1{font-size:17px;margin:0 0 2px;letter-spacing:-.01em}
.sub{color:var(--mut);font-size:12.5px;margin-bottom:22px}
h2{font-size:11px;text-transform:uppercase;letter-spacing:.09em;color:var(--mut);
   margin:26px 0 8px;font-weight:600}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
table{width:100%;border-collapse:collapse}
td,th{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--mut);font-weight:600}
tr:last-child td{border-bottom:none}
.lbl{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;font-weight:600;
     white-space:nowrap}
.id{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:var(--mut)}
.topic{color:var(--fg);max-width:430px}
.expt{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;max-width:200px;
      word-break:break-word}
.age{font-variant-numeric:tabular-nums;color:var(--mut);white-space:nowrap;text-align:right}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:7px;
     vertical-align:middle}
.live .dot{background:var(--live);box-shadow:0 0 0 3px color-mix(in srgb,var(--live) 22%,transparent)}
.idle .dot{background:var(--idle)}
.stale .dot{background:var(--stale)}
.stale td{color:var(--mut)}
.legend{color:var(--mut);font-size:11.5px;margin-top:18px;line-height:1.7}
code{font-family:ui-monospace,Menlo,monospace;background:var(--line);padding:1px 5px;
     border-radius:4px;font-size:11.5px}
.tmux{font-family:ui-monospace,Menlo,monospace;font-weight:700;font-size:13px;
      white-space:nowrap;min-width:78px;color:var(--accent)}
.next{margin-top:5px;font-size:12px;color:var(--fg);border-left:2px solid var(--accent);
      padding-left:8px}
.next b{color:var(--accent)}
.sub2{color:var(--mut);font-size:11px;font-family:ui-monospace,Menlo,monospace}
.empty{padding:14px 12px;color:var(--mut);font-size:12.5px}
.net{display:flex;align-items:baseline;gap:8px;border-radius:8px;padding:9px 13px;
     margin:0 0 12px;font-size:13px;border:1px solid}
.net i{font-style:normal;font-size:11.5px;opacity:.85}
.net.ok{background:color-mix(in srgb,var(--live) 12%,transparent);border-color:var(--live)}
.net.bad{background:color-mix(in srgb,#e5484d 14%,transparent);border-color:#e5484d}
.key{display:flex;flex-wrap:wrap;gap:9px;margin:0 0 22px}
.k{display:flex;align-items:baseline;gap:6px;background:var(--card);
   border:1px solid var(--line);border-radius:8px;padding:7px 12px;font-size:12.5px}
.k b{font-weight:600}
.k i{font-style:normal;color:var(--mut);font-size:11.5px}
.k .dot{position:relative;top:-1px}
"""


def render_html(sections, out_path, refresh, net=None):
    net = net or {}
    E = html.escape

    def row(s):
        br = f'<div class="sub2">{E(s["branch"])}</div>' if s.get("branch") else ""
        prior = (f' <span style="color:var(--mut)">+{s["prior"]} earlier here</span>'
                 if s.get("prior") else "")
        nxt = (f'<div class="next"><b>Suggested next action:</b> {E(s["next"])}</div>'
               if s.get("next") else "")
        note = (f'<div class="sub2" style="margin-top:4px">{E(s["note"])}</div>'
                if s.get("note") else "")
        also = (f'<div class="sub2">also {E(s["expt_also"])}</div>'
                if s.get("expt_also") else "")
        return (f'<tr class="{E(s["state"])}">'
                f'<td class="tmux">{E(s["tmux_cell"])}</td>'
                f'<td class="lbl"><span class="dot"></span>{E(s["label"])}</td>'
                f'<td class="id">{E(s["short"])}</td>'
                f'<td class="id">{E(s["where"])}{br}</td>'
                f'<td class="id">{E(s["mdl"])}</td>'
                f'<td class="topic">{E(s["topic"])}{prior}{nxt}{note}</td>'
                f'<td class="expt">{E(s.get("expt") or "-")}{also}</td>'
                f'<td class="age">{ago(s["age"])}</td></tr>')

    rows_all = [s for sec in sections for s in sec["rows"]]
    live = sum(1 for s in rows_all if s["state"] == "live")
    parts = ['<title>Agent Board</title>',
             f'<meta http-equiv="refresh" content="{refresh}">',
             f'<style>{CSS}</style>', '<div class="wrap">',
             '<h1>Agent board</h1>',
             f'<div class="sub">{time.strftime("%a %d %b %Y, %H:%M:%S")} &nbsp;·&nbsp; '
             f'{live} working &nbsp;·&nbsp; {len(rows_all)} rows '
             f'&nbsp;·&nbsp; refreshes every {refresh}s</div>']

    # --- connectivity banner
    if net.get("reachable"):
        tick = (f'<i>Kerberos ticket until {E(net.get("expires", ""))}</i>' if net.get("ticket")
                else '<i>no Kerberos ticket &mdash; run <code>kinit</code></i>')
        parts.append(f'<div class="net ok">&#x1F7E2; <b>Stanford / SNAP reachable</b>{tick}</div>')
    else:
        parts.append('<div class="net bad">&#x1F534; <b>No Stanford access</b>'
                     '<i>connect the Stanford VPN &mdash; SNAP nodes unreachable from here</i></div>')

    # --- colour key (one meaning per colour, in every table)
    parts.append('<div class="key">'
                 '<span class="k live"><span class="dot"></span><b>working now</b>'
                 '<i>wrote in the last 2 min &middot; SNAP job RUNNING</i></span>'
                 '<span class="k idle"><span class="dot"></span><b>waiting on you</b>'
                 '<i>last wrote 2&ndash;30 min ago &middot; SNAP results not landed</i></span>'
                 '<span class="k stale"><span class="dot"></span><b>idle / finished</b>'
                 '<i>nothing for over 30 min &middot; SNAP job LANDED</i></span></div>')

    # --- every section: the same eight columns
    HEAD = ('<tr><th>tmux</th><th>Agent</th><th>Id</th><th>Where</th>'
            '<th>Model+effort</th><th>Task</th><th>Expt</th><th>Last</th></tr>')
    for sec in sections:
        rows = sec["rows"]
        nlive = sum(1 for s in rows if s["state"] == "live")
        note = (f'<div class="sub2" style="margin:-4px 0 8px">{E(sec["note"])}</div>'
                if sec.get("note") else "")
        parts.append(f'<h2>{E(sec["title"])}'
                     f'<span style="text-transform:none;letter-spacing:0;font-weight:400"> '
                     f'&nbsp;·&nbsp; {nlive} live / {len(rows)} &nbsp;·&nbsp; '
                     f'<code>{E(sec["sub"])}</code></span></h2>{note}<div class="card"><table>{HEAD}')
        parts.append("".join(row(s) for s in rows) if rows
                     else '<tr><td colspan="8" class="empty">none</td></tr>')
        parts.append('</table></div>')

    parts.append(
        '<div class="legend" style="margin-top:26px"><b>Columns, same in every table.</b> '
        '<b>tmux</b>: the tmux/byobu session the agent runs in &mdash; locally '
        '<code>tmux N</code> (from the per-process registry Claude Code itself keeps, '
        '<code>~/.claude*/sessions/&lt;pid&gt;.json</code>; for Codex, the thread whose start '
        'time is the process start), a session resumed in two windows appears as two rows (one per live process, each noting the other window), '
        '<code>cursor</code> / <code>chatgpt</code> / <code>vscode</code> = an app terminal '
        'outside tmux, <code>&mdash;</code> = no live process (<code>claude --resume '
        '&lt;id&gt;</code> continues it); on SNAP the session name on that node '
        '(<code>tmux attach -t &lt;name&gt;</code> there). '
        '<b>Agent</b>: <code>cc</code> Claude Code (personal config), <code>ccv</code> Claude '
        'Code (Vals config), <code>cxd</code> Codex, <code>&mdash;</code> only shells in the '
        'pane. <b>Id</b>: Claude session id / Codex thread id / experiment number. '
        '<b>Where</b>: the working directory, fully expanded (the <code>/Users/&lt;you&gt;</code> '
        'prefix says which laptop; SNAP rows are <code>node:/lfs/…</code>), with the git '
        'branch or Codex originator beneath. '
        '<b>Task</b>: what it is doing (SNAP: job state). <b>Expt</b>: the '
        '<code>experiments/&lt;NN_name&gt;</code> directory the agent&#39;s own recent actions '
        'and messages reference most (its last 200 mentions in cwd, prose and tool inputs; '
        'tool outputs are ignored), a runner-up beneath when it has at least half as many; '
        'on SNAP the job&#39;s experiment dir; <code>-</code> = never referenced one. '
        '<b>Last</b>: time since it last wrote (SNAP: pane idle time).<br>'
        'Every session with a live process is shown (a <code>claude -p</code> child shares its '
        'parent&#39;s window); older transcripts in a window fold into its holder&#39;s '
        '<i>+N earlier here</i>. SNAP job state: <b>RUNNING</b> = a process is '
        'alive in the pane; <b>DONE?</b> = pane idle, results not yet committed; '
        '<b>LANDED</b> = a commit touched the experiment dir after the job went quiet.'
        '</div></div>')

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(out_path), suffix=".html")
    with os.fdopen(fd, "w") as fh:
        fh.write("\n".join(parts))
    os.chmod(tmp, 0o600)       # the page embeds session topics: owner-readable only
    os.replace(tmp, out_path)  # atomic + unique tmp, so concurrent writers cannot collide
    return out_path


def main():
    ap = argparse.ArgumentParser(description="Local agent session board.")
    ap.add_argument("--html", nargs="?", const=os.path.join(BOARD_DIR, "board.html"),
                    help="write the HTML board (default ~/.agent-board/board.html)")
    ap.add_argument("--snap", action="store_true", help="poll SNAP nodes over ssh (slow)")
    ap.add_argument("--hours", type=float, default=6, help="how far back to list (default 6)")
    ap.add_argument("--all", action="store_true",
                    help="every transcript, not just the current one per tmux window")
    ap.add_argument("--refresh", type=int, default=20, help="HTML auto-refresh seconds")
    ap.add_argument("--quiet", action="store_true", help="no terminal table")
    ap.add_argument("--summarize", action="store_true",
                    help="top up AI session summaries via `claude -p` (slow; run out of band)")
    ap.add_argument("--summarize-limit", type=int, default=6,
                    help="max sessions to summarize per invocation")
    a = ap.parse_args()

    tab, panes = process_table(), tmux_panes()
    sessions = collect_sessions(a.hours, a.all, tab, panes)
    codex = collect_codex(a.hours, tab, panes)
    snap = poll_snap() and read_snap_cache() if a.snap else read_snap_cache()

    if a.summarize:
        n = summarize(sessions, limit=a.summarize_limit, verbose=not a.quiet)
        if not a.quiet:
            print(f"  summarized {n} session(s)")
        sessions = collect_sessions(a.hours, a.all, tab, panes)

    experiments = collect_experiments({"hosts": snap["hosts"]} if snap else None)
    net = stanford_status()
    sections = build_sections(sessions, codex, experiments, snap)

    if a.html:
        p = render_html(sections, a.html, a.refresh, net)
        if not a.quiet:
            print(f"  wrote {p}")
    if not a.quiet:
        render_text(sections, net, panes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
