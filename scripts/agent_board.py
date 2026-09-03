#!/usr/bin/env python3
# TLDR: Scans local Claude Code / Codex session state (transcripts, tmux panes, self-registrations)
# plus optional SNAP node polling, and renders a self-refreshing HTML board + terminal table so you
# can see at a glance which agent session is working on what.

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
    ("ccv", "Claude Code sessions — Vals", "clauded-vals / claude-vals, ~/.claude-vals"),
    ("cc",  "Claude Code sessions — personal", "clauded / claude, ~/.claude"),
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
    if not cwd:
        return ""
    p = cwd.replace(HOME, "~")
    bits = p.split("/")
    return p if len(bits) <= 3 else "~/" + "/".join(bits[-2:])


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


def all_agent_procs(tab, panes):
    """[(location, pid, start_epoch)] for every running agent process, wherever it lives."""
    out = []
    for pid, (_ppid, start, cmd) in tab.items():
        if AGENT_RE.search(cmd) and "agent_board" not in cmd:
            out.append((locate(pid, tab, panes), pid, start))
    return out


def tmux_agent_procs(tab, panes):
    """[(tmux_session_name, pid, start_epoch)] for every agent process under a tmux pane."""
    kids = {}
    for pid, (ppid, _, _) in tab.items():
        kids.setdefault(ppid, []).append(pid)
    found = []
    for pane_pid, (sess, _cmd) in panes.items():
        stack, seen, depth = [(pane_pid, 0)], set(), 0
        while stack:
            pid, d = stack.pop()
            if pid in seen or d > 5:
                continue
            seen.add(pid)
            info = tab.get(pid)
            if info and AGENT_RE.search(info[2]):
                found.append((sess, pid, info[1]))
            stack.extend((k, d + 1) for k in kids.get(pid, []))
    return found


def locate(pid, tab, panes, depth=12):
    """Walk up the process tree: which tmux window, or which app, is this agent sitting in?"""
    seen = 0
    while pid in tab and seen < depth:
        if pid in panes:
            return "tmux " + panes[pid][0]
        cmd = tab[pid][2]
        if "Cursor Helper" in cmd or "Cursor.app" in cmd:
            return "cursor"
        if "iTerm" in cmd:
            return "iterm"
        if "Terminal.app" in cmd:
            return "terminal"
        pid = tab[pid][0]
        seen += 1
    return "?"


def assign_tmux(births, agents, tol=180):
    """Greedy one-to-one match of sessions to live agent processes, closest pair first.

    A tmux pane runs one agent at a time, so a process must not be claimed by two
    sessions -- without this, an old transcript in a window steals the label from the
    session actually running there now.
    """
    pairs = sorted(
        ((abs(start - birth), sid, sess, pid)
         for sid, birth in births.items()
         for sess, pid, start in agents
         if abs(start - birth) <= tol),
        key=lambda x: x[0])
    out, used = {}, set()
    for _d, sid, sess, pid in pairs:
        if sid in out or pid in used:
            continue
        out[sid], _ = sess, used.add(pid)
    return out


def load_registry():
    """Session self-registrations written by the SessionStart hook."""
    reg = {}
    for f in glob.glob(os.path.join(REGISTRY_DIR, "*.json")):
        try:
            with open(f) as fh:
                d = json.load(fh)
            if d.get("session_id"):
                reg[d["session_id"]] = d
        except Exception:
            continue
    return reg


def collect_sessions(max_age_h, show_all=False):
    now = time.time()
    reg = load_registry()
    tab = process_table()
    panes = tmux_panes()
    agents = all_agent_procs(tab, panes)

    births, paths = {}, []
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
            births[sid] = getattr(st, "st_birthtime", st.st_ctime)
            paths.append((cfg_dir, tag, tpath, st, sid))
    inferred = assign_tmux(births, agents)
    rows = []
    for cfg_dir, tag, tpath, st, sid in paths:
            age = now - st.st_mtime
            proj_dir = os.path.basename(os.path.dirname(tpath))
            topic, cwd, branch, model, effort = scan_transcript(tpath)
            r = reg.get(sid, {})
            tmux_name, how = r.get("tmux"), "registered"
            if not tmux_name:
                # started before the hook existed: correlate transcript birth time with
                # the start time of a live agent process inside a tmux pane
                tmux_name, how = inferred.get(sid), "inferred"
            label = tag
            if tmux_name:
                cell = (f"tmux {tmux_name}" if str(tmux_name).isdigit() else str(tmux_name))
                cell += "" if how == "registered" else " ?"
            else:
                cell, how = "\u2014", "unknown"
            rows.append({
                "sid": sid,
                "path": tpath,
                "short": sid[:8],
                "tag": tag,
                "label": label,
                "tmux": tmux_name,
                "alive": sid in inferred or how == "registered",
                "tmux_cell": cell,
                "tmux_how": how,
                "project": project_label(proj_dir),
                "topic": topic,
                "cwd": cwd,
                "where": (HOSTNAME + ":" + short_path(cwd)) if cwd else HOSTNAME,
                "branch": branch,
                "model": short_model(model),
                "effort": effort,
                "mdl": (short_model(model) + ("+" + effort if effort else "")) if model else "?",
                "last": st.st_mtime,
                "age": age,
                "size_mb": round(st.st_size / 1e6, 1),
                "state": "live" if age < LIVE_S else ("idle" if age < IDLE_S else "stale"),
            })
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


def one_per_seat(rows, keep_stale=False):
    """A tmux window is one seat: the agent you have "on" there is the newest transcript in
    it. Older transcripts in the same window are that seat's history, not extra agents."""
    seen, out = {}, []
    for r in sorted(rows, key=lambda r: r["last"], reverse=True):
        if r.get("tmux"):
            key = (r["tag"], r["tmux"])
            if key in seen:
                seen[key]["prior"] += 1
                continue
            r["prior"] = 0
            seen[key] = r
            out.append(r)
        else:
            # no window to attribute it to: keep it only while it is actually moving
            r["prior"] = 0
            if keep_stale or r["state"] != "stale":
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


def collect_codex(max_age_h, limit=8):
    """Recent Codex threads from the local session index."""
    idx = os.path.join(HOME, ".codex", "session_index.jsonl")
    seen, rows = {}, []
    try:
        with open(idx, errors="ignore") as fh:
            for ln in fh:
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                if d.get("id"):
                    seen[d["id"]] = d  # later lines win
    except OSError:
        return rows
    for d in seen.values():
        ts = d.get("updated_at", "")
        try:
            t = calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S"))  # index is UTC
        except Exception:
            continue
        age = time.time() - t
        if age > max_age_h * 3600:
            continue
        rows.append({"short": d["id"][:8], "name": (d.get("thread_name") or "")[:70],
                     "last": t, "age": age})
    rows.sort(key=lambda r: r["last"], reverse=True)
    return rows[:limit]


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
                 # panes (session, pane pid, activity) + the node's process table; the
                 # descendant walk happens locally so "running" means a real non-shell
                 # process under the pane, not whatever the pane's foreground command is
                 "tmux list-panes -a -F '#{session_name},#{pane_pid},#{session_activity}' 2>/dev/null; "
                 "echo '=PS='; ps -e -o pid=,ppid=,comm= 2>/dev/null; "
                 "echo '=N='; pgrep -c codex 2>/dev/null || echo 0"],
                capture_output=True, text=True, timeout=timeout + 15)
            if r.returncode != 0:
                raise RuntimeError(f"ssh exit {r.returncode}")
            panes_txt, _, rest = r.stdout.partition("=PS=")
            ps_txt, _, procs = rest.partition("=N=")
            kids, comm = {}, {}
            for ln in ps_txt.splitlines():
                f = ln.split(None, 2)
                if len(f) == 3:
                    kids.setdefault(f[1], []).append(f[0])
                    comm[f[0]] = os.path.basename(f[2]).strip()
            seen = {}
            for ln in panes_txt.splitlines():
                name, ppid, act = (ln.strip().split(",") + ["", ""])[:3]
                if not name:
                    continue
                try:
                    act = float(act)
                except ValueError:
                    act = 0
                # every descendant of the pane shell, depth-limited
                stack, desc, n = list(kids.get(ppid, [])), [], 0
                while stack and n < 400:
                    pid = stack.pop(); n += 1
                    desc.append(comm.get(pid, ""))
                    stack.extend(kids.get(pid, []))
                s = seen.setdefault(name, {"name": name, "activity": act, "cmds": []})
                s["cmds"].extend(c for c in desc if c)
                s["activity"] = max(s["activity"], act)
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


def read_snap_cache():
    try:
        with open(SNAP_CACHE) as fh:
            return json.load(fh)
    except Exception:
        return None


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
    """stdout on success, None on failure (so callers can tell 'no commits' from 'git broke')."""
    try:
        r = subprocess.run(["git", *args], cwd=cwd or os.path.join(HOME, "veribench"),
                           capture_output=True, text=True, timeout=10)
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


def collect_experiments(snap):
    """Cross SNAP tmux jobs with repo state to answer: which experiments are DONE but unlanded?"""
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
        for s in h.get("tmux", []):
            name = s["name"] if isinstance(s, dict) else str(s)
            act = s.get("activity", 0) if isinstance(s, dict) else 0
            if name in IGNORE_TMUX:
                continue
            num = JOB_ALIASES.get(name)
            if not num:
                m = re.search(r"(\d+)", name)
                num = m.group(1) if m else None
            key = (num, name)
            idle = now - act if act else None
            cmds = s.get("cmds") if isinstance(s, dict) else None
            busy = None if cmds is None else any(c not in SHELLS for c in cmds)
            jobs[key] = {"num": num, "job": name, "host": h["host"], "idle": idle, "busy": busy,
                         "cmds": sorted({c for c in (cmds or []) if c not in SHELLS})[:4]}

    rows = []
    for (num, name), j in sorted(jobs.items(), key=lambda kv: (kv[0][0] or "zz", kv[0][1])):
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

        rows.append({
            "ext": ext.get("note", "") if ext else "",
            "num": num or "?", "job": name, "host": j["host"],
            "idle": j["idle"], "state": state, "dirty": is_dirty,
            "dir": os.path.basename(d) if d else "(no local dir)",
            "cmds": ", ".join(j["cmds"][:3]),
            "commit_age": commit_age, "subject": subject,
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
    if sec < 60:
        return f"{int(sec)}s"
    if sec < 3600:
        return f"{int(sec // 60)}m"
    if sec < 86400:
        return f"{int(sec // 3600)}h{int((sec % 3600) // 60):02d}"
    return f"{int(sec // 86400)}d"


# ---------------------------------------------------------------- renderers

def render_text(sessions, codex, snap, panes, experiments=None, net=None):
    W = "\033[0m"
    C = {"live": "\033[32m", "idle": "\033[33m", "stale": "\033[90m"}
    if net:
        if net.get("reachable"):
            tick = f"kerberos until {net['expires']}" if net.get("ticket") else "NO kerberos ticket (run kinit)"
            print(f"\n  \U0001F7E2 Stanford / SNAP reachable   \033[90m{tick}\033[0m")
        else:
            print("\n  \U0001F534 No Stanford access \u2014 connect the VPN "
                  "\033[90m(SNAP nodes unreachable)\033[0m")
    print(f"\n  \033[32m\u25cf\033[0m working now (<2m)   "
          f"\033[33m\u25cf\033[0m waiting on you (2-30m)   "
          f"\033[90m\u25cf\033[0m idle / finished (>30m)")
    print(f"\n  AGENT BOARD — {time.strftime('%a %d %b %H:%M:%S')}"
          f"   ({sum(1 for s in sessions if s['state']=='live')} live,"
          f" {len(sessions)} recent)\n")
    for tag, title, sub in SECTION_TITLES:
        group = [s for s in sessions if s["tag"] == tag]
        if not group:
            continue
        nlive = sum(1 for s in group if s["state"] == "live")
        print(f"  {title.upper()}  ({nlive} live / {len(group)})   {sub}")
        print(f"  {'TMUX/APP':<9} {'CFG':<5} {'ID':<9} {'WHERE':<18} {'MDL+EFF':<12} {'AGE':>5}  TOPIC")
        print(f"  {'-'*9} {'-'*5} {'-'*9} {'-'*18} {'-'*12} {'-'*5}  {'-'*34}")
        for s in group:
            c = C.get(s["state"], "")
            prior = f"  \033[90m(+{s['prior']})\033[0m" if s.get("prior") else ""
            print(f"  \033[1m{s['tmux_cell']:<9}\033[0m{c}{s['label']:<5} {s['short']:<9} "
                  f"{s['where'][:18]:<18} {s['mdl'][:12]:<12} {ago(s['age']):>5}  "
                  f"{s['topic'][:34]}{W}{prior}")
            if s.get("next"):
                print(f"  {'':<9}{'':<5} {'':<9} {'':<18} {'':<12} {'':>5}  "
                      f"\033[1mnext:\033[0m {s['next'][:64]}")
        print()
    if codex:
        print(f"\n  CODEX (local)")
        for r in codex:
            print(f"  {'cxd':<10} {r['short']:<9} {'':<12} {ago(r['age']):>6}  {r['name'][:46]}")
    if snap:
        stamp = time.strftime('%H:%M', time.localtime(snap["at"]))
        print(f"\n  SNAP  (polled {stamp})")
        for h in snap["hosts"]:
            t = ",".join(s["name"] if isinstance(s, dict) else str(s)
                         for s in h["tmux"]) or "-"
            print(f"  {'+s':<10} {h['host']:<9} {'':<12} {'':>6}  tmux[{t}]  codex procs: {h['procs']}")
    if experiments:
        print(f"\n  EXPERIMENTS  (SNAP job x repo state)")
        print(f"  {'STATE':<26} {'JOB':<24} {'HOST':<10} {'IDLE':>6} {'LANDED':>7}")
        print(f"  {'-'*26} {'-'*24} {'-'*10} {'-'*6} {'-'*7}")
        for r in experiments:
            mark = "\033[33m" if r["state"].startswith("DONE") else (
                   "\033[32m" if r["state"] == "RUNNING" else "\033[90m")
            print(f"  {mark}{r['state']:<26} {r['job']:<24} {r['host']:<10} "
                  f"{(ago(r['idle']) if r['idle'] is not None else '?'):>6} "
                  f"{(ago(r['commit_age']) if r['commit_age'] is not None else '-'):>7}\033[0m")
    live_panes = sum(1 for _, (_, cmd) in panes.items() if "codex" in cmd or cmd[0].isdigit())
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
      white-space:nowrap;width:78px;color:var(--accent)}
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


def render_html(sessions, codex, snap, out_path, refresh, experiments=None, net=None):
    net = net or {}
    E = html.escape

    def row(s):
        br = f'<div class="sub2">{E(s["branch"])}</div>' if s.get("branch") else ""
        prior = (f' <span style="color:var(--mut)">+{s["prior"]} earlier here</span>'
                 if s.get("prior") else "")
        nxt = (f'<div class="next"><b>Suggested next action:</b> {E(s["next"])}</div>'
               if s.get("next") else "")
        return (f'<tr class="{s["state"]}">'
                f'<td class="tmux">{E(s["tmux_cell"])}</td>'
                f'<td class="lbl"><span class="dot"></span>{E(s["label"])}</td>'
                f'<td class="id">{E(s["short"])}</td>'
                f'<td class="id">{E(s["where"])}{br}</td>'
                f'<td class="id">{E(s["mdl"])}</td>'
                f'<td class="topic">{E(s["topic"])}{prior}{nxt}</td>'
                f'<td class="age">{ago(s["age"])}</td></tr>')

    live = sum(1 for s in sessions if s["state"] == "live")
    parts = ['<title>Agent Board</title>',
             f'<meta http-equiv="refresh" content="{refresh}">',
             f'<style>{CSS}</style>', '<div class="wrap">',
             '<h1>Agent board</h1>',
             f'<div class="sub">{time.strftime("%a %d %b %Y, %H:%M:%S")} &nbsp;·&nbsp; '
             f'{live} live &nbsp;·&nbsp; {len(sessions)} current sessions '
             f'&nbsp;·&nbsp; refreshes every {refresh}s</div>']

    # --- connectivity banner
    if net.get("reachable"):
        tick = (f'<i>Kerberos ticket until {E(net.get("expires", ""))}</i>' if net.get("ticket")
                else '<i>no Kerberos ticket &mdash; run <code>kinit</code></i>')
        parts.append(f'<div class="net ok">&#x1F7E2; <b>Stanford / SNAP reachable</b>{tick}</div>')
    else:
        parts.append('<div class="net bad">&#x1F534; <b>No Stanford access</b>'
                     '<i>connect the Stanford VPN &mdash; SNAP nodes unreachable from here</i></div>')

    # --- colour key
    parts.append('<div class="key">'
                 '<span class="k live"><span class="dot"></span><b>working now</b>'
                 '<i>wrote in the last 2 min</i></span>'
                 '<span class="k idle"><span class="dot"></span><b>waiting on you</b>'
                 '<i>last wrote 2&ndash;30 min ago</i></span>'
                 '<span class="k stale"><span class="dot"></span><b>idle / finished</b>'
                 '<i>nothing for over 30 min</i></span></div>')

    # --- one card per config
    HEAD = ('<tr><th>tmux / app</th><th>Cfg</th><th>Id</th><th>Where</th>'
            '<th>Model+effort</th><th>Topic</th><th>Last</th></tr>')
    for tag, title, sub in SECTION_TITLES:
        group = [s for s in sessions if s["tag"] == tag]
        nlive = sum(1 for s in group if s["state"] == "live")
        parts.append(f'<h2>{E(title)}'
                     f'<span style="text-transform:none;letter-spacing:0;font-weight:400"> '
                     f'&nbsp;·&nbsp; {nlive} live / {len(group)} &nbsp;·&nbsp; '
                     f'<code>{E(sub)}</code></span></h2><div class="card"><table>{HEAD}')
        parts.append("".join(row(s) for s in group) if group
                     else '<tr><td colspan="7" class="empty">no current sessions</td></tr>')
        parts.append('</table></div>')

    # --- codex
    if codex:
        parts.append('<h2>Codex threads (local)</h2><div class="card"><table>'
                     '<tr><th>Label</th><th>Id</th><th>Thread</th><th>Last</th></tr>')
        for r in codex:
            st = "live" if r["age"] < LIVE_S else ("idle" if r["age"] < IDLE_S else "stale")
            parts.append(f'<tr class="{st}"><td class="lbl"><span class="dot"></span>cxd</td>'
                         f'<td class="id">{E(r["short"])}</td>'
                         f'<td class="topic">{E(r["name"])}</td>'
                         f'<td class="age">{ago(r["age"])}</td></tr>')
        parts.append('</table></div>')

    # --- experiments
    if experiments:
        parts.append('<h2>Experiments &mdash; SNAP job &times; repo state</h2><div class="card"><table>'
                     '<tr><th>State</th><th>Job</th><th>Running</th><th>Host</th>'
                     '<th>Experiment dir</th><th>Job idle</th><th>Landed</th></tr>')
        for r in experiments:
            cls = ("idle" if r["state"].startswith("DONE") else
                   "live" if r["state"].startswith("RUNNING") else "stale")
            note = (f'<div style="color:var(--mut);font-size:11.5px">{E(r["ext"])}</div>'
                    if r.get("ext") else "")
            parts.append(
                f'<tr class="{cls}"><td class="lbl"><span class="dot"></span>{E(r["state"])}{note}</td>'
                f'<td class="id">{E(r["job"])}</td>'
                f'<td class="id">{E(r.get("cmds", ""))}</td>'
                f'<td class="id">{E(r["host"])}</td>'
                f'<td>{E(r["dir"])}</td>'
                f'<td class="age">{ago(r["idle"]) if r["idle"] is not None else "?"}</td>'
                f'<td class="age">{ago(r["commit_age"]) if r["commit_age"] is not None else "&mdash;"}</td>'
                f'</tr>')
        parts.append('</table></div>')

    # --- snap nodes
    if snap:
        stamp = time.strftime("%H:%M", time.localtime(snap["at"]))
        parts.append(f'<h2>SNAP nodes <span style="text-transform:none;letter-spacing:0">'
                     f'(polled {stamp})</span></h2><div class="card"><table>'
                     '<tr><th>Host</th><th>tmux sessions</th><th>codex procs</th></tr>')
        for h in snap["hosts"]:
            names = ", ".join(s["name"] if isinstance(s, dict) else str(s) for s in h["tmux"]) or "&mdash;"
            err = (f' <span style="color:var(--idle)">stale: {E(str(h["error"]))}</span>'
                   if h.get("error") else "")
            parts.append(f'<tr><td class="lbl">+s {E(h["host"])}</td>'
                         f'<td>{names}{err}</td><td>{E(str(h["procs"]))}</td></tr>')
        parts.append('</table></div>')

    parts.append(
        '<div class="legend" style="margin-top:26px"><b>Notation.</b> '
        '<code>cc</code> Claude Code (personal config) &nbsp; '
        '<code>ccv</code> Claude Code (Vals config) &nbsp; '
        '<code>cxd</code> Codex &nbsp; '
        '<code>tmux N</code> local tmux session N (<code>?</code> = inferred from process '
        'start time; <code>cursor</code> = a Cursor terminal without tmux) &nbsp; '
        '<code>+s</code> SNAP<br>'
        'Only the newest session per tmux window is shown; <i>+N earlier here</i> counts the '
        'older transcripts in that window. Experiment state: <b>RUNNING</b> = a process is alive '
        'in the SNAP pane; <b>DONE?</b> = pane is idle, results not yet committed; '
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

    sessions = collect_sessions(a.hours, a.all)
    codex = collect_codex(a.hours)
    snap = poll_snap() and read_snap_cache() if a.snap else read_snap_cache()

    if a.summarize:
        n = summarize(sessions, limit=a.summarize_limit, verbose=not a.quiet)
        if not a.quiet:
            print(f"  summarized {n} session(s)")
        sessions = collect_sessions(a.hours, a.all)

    experiments = collect_experiments({"hosts": snap["hosts"]} if snap else None)

    net = stanford_status()

    if a.html:
        p = render_html(sessions, codex, snap, a.html, a.refresh, experiments, net)
        if not a.quiet:
            print(f"  wrote {p}")
    if not a.quiet:
        render_text(sessions, codex, snap, tmux_panes(), experiments, net)
    return 0


if __name__ == "__main__":
    sys.exit(main())
