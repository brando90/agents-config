#!/usr/bin/env python3
"""Make every Claude Code session of every account show up in the Claude desktop app.

The app lists only sessions that have an index record
  ~/Library/Application Support/Claude/claude-code-sessions/<account>/<org>/local_<uuid>.json
Terminal sessions (clauded, clauded-<name>, any ~/.claude* profile) write only a transcript under
<profile>/projects/<slug>/<cliSessionId>.jsonl, so the app never lists them. This script adds
the missing records (additive, never overwrites) and copies missing transcripts into ~/.claude
so the app can resume them. Dry run unless --apply. Quit the app (Cmd+Q) afterwards and reopen.
"""
import argparse, calendar, glob, json, os, shutil, subprocess, sys, time, uuid

HOME = os.path.expanduser("~")
APP = os.path.join(HOME, "Library/Application Support/Claude")
STORE = os.path.join(APP, "claude-code-sessions")


def discover_profiles():
    """label -> dir name for every ~/.claude and ~/.claude-<name> config dir that holds sessions."""
    out = {}
    extra = [os.environ["CLAUDE_CONFIG_DIR"]] if os.environ.get("CLAUDE_CONFIG_DIR") else []
    for d in sorted(glob.glob(os.path.join(HOME, ".claude*"))) + extra:
        b = os.path.basename(d)
        if os.path.isdir(os.path.join(d, "projects")):
            out["" if b == ".claude" else b[len(".claude-"):] if b.startswith(".claude-") else b.lstrip(".")] = b
    return out


PROFILES = discover_profiles()
DEFAULT_PROFILE = ".claude"  # the app resumes sessions from this profile's projects/ dir


def ms(ts):
    return calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) * 1000 if ts else None


def scan(path):
    """Summarize a transcript: cwd, title, model, first/last timestamp, entrypoint."""
    info = {"cwd": None, "title": None, "first_user": None, "model": None,
            "t0": None, "t1": None, "entry": None, "perm": None}
    with open(path, errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            ts = r.get("timestamp")
            if ts:
                info["t0"] = info["t0"] or ts
                info["t1"] = ts
            info["cwd"] = info["cwd"] or r.get("cwd")
            info["entry"] = info["entry"] or r.get("entrypoint")
            info["perm"] = info["perm"] or r.get("permissionMode")
            t = r.get("type")
            if t in ("ai-title", "custom-title"):
                info["title"] = r.get("aiTitle") or r.get("customTitle") or r.get("title") or info["title"]
            elif t == "user" and not info["first_user"] and not r.get("isSidechain"):
                c = (r.get("message") or {}).get("content")
                if isinstance(c, list):
                    c = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
                if isinstance(c, str) and c.strip() and not c.lstrip().startswith("<"):
                    info["first_user"] = " ".join(c.split())[:70]
            elif t == "assistant":
                info["model"] = (r.get("message") or {}).get("model") or info["model"]
    return info


def detect_target():
    acct, org = os.environ.get("CLAUDE_CODE_ACCOUNT_UUID"), os.environ.get("CLAUDE_CODE_ORGANIZATION_UUID")
    if acct and org and os.path.isdir(os.path.join(STORE, acct, org)):
        return os.path.join(STORE, acct, org)
    dirs = [d for d in glob.glob(os.path.join(STORE, "*", "*")) if os.path.isdir(d)]
    return max(dirs, key=lambda d: os.path.getmtime(d)) if dirs else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write records (default: dry run)")
    ap.add_argument("--target", help="<account>/<org> dir to fill (default: signed-in account)")
    ap.add_argument("--include-headless", action="store_true",
                    help="also list sdk/-p worker runs (default: interactive sessions only)")
    ap.add_argument("--all-accounts", action="store_true", help="fill every signed-in app account/org folder, not only the current one")
    ap.add_argument("--no-tag", action="store_true", help="do not prefix titles with the profile name, e.g. [vals]")
    a = ap.parse_args()

    if a.all_accounts:
        targets = [d for d in sorted(glob.glob(os.path.join(STORE, "*", "*"))) if os.path.isdir(d)]
    else:
        t = a.target if a.target and os.path.isabs(a.target) else (os.path.join(STORE, a.target) if a.target else detect_target())
        targets = [t] if t and os.path.isdir(t) else []
    if not targets:
        sys.exit("no target account dir found under " + STORE)
    for target in targets:
        run(target, a)


def run(target, a):
    print("target:", target)

    records, have = {}, set()  # records: cliSessionId -> a source file in some other account dir
    for f in glob.glob(os.path.join(STORE, "*", "*", "local_*.json")):
        try:
            cid = json.load(open(f)).get("cliSessionId")
        except ValueError:
            continue
        if os.path.dirname(f) == target:
            have.add(cid)
        else:
            records.setdefault(cid, f)

    new, copied_rec = [], 0
    # 1) records that exist for another account/org but not here (same-machine sessions)
    for cid, f in records.items():
        if cid not in have:
            new.append(("copy", cid, f, None))
    copied_rec = len(new)
    seen = set(records) | have

    # 2) terminal-only transcripts from every profile
    for label, prof in PROFILES.items():  # label "" = default profile (untagged)
        for p in glob.glob(os.path.join(os.path.expanduser(os.path.join("~", prof)) if not os.path.isabs(prof) else prof, "projects", "*", "*.jsonl")):
            cid = os.path.basename(p)[:-6]
            if cid in seen:
                continue
            seen.add(cid)
            info = scan(p)
            if not info["t0"]:
                continue
            if info["entry"] not in (None, "cli") and not a.include_headless:
                continue
            new.append(("make", cid, p, (label, prof, info)))

    print(f"existing here: {len(have)}  | to copy from other accounts: {copied_rec}  | "
          f"to create from transcripts: {len(new) - copied_rec}")
    by = {}
    for kind, cid, p, extra in new:
        k = kind if kind == "copy" else extra[0]
        by[k] = by.get(k, 0) + 1
    print("by source:", by)
    if not a.apply:
        for kind, cid, p, extra in new[:15]:
            print(" ", kind, cid[:8], (extra[2]["title"] or extra[2]["first_user"] or "") if extra else os.path.basename(p))
        print("dry run; add --apply to write")
        return

    backup = os.path.join(APP, "claude-code-sessions-backup-" + time.strftime("%m-%d-%Y-%H%M%S"))
    shutil.copytree(target, backup)
    print("backup:", backup)
    n = t = 0
    for kind, cid, p, extra in new:
        if kind == "copy":
            dst = os.path.join(target, os.path.basename(p))
            if not os.path.exists(dst):
                shutil.copy2(p, dst); n += 1
            continue
        label, prof, info = extra
        if prof != DEFAULT_PROFILE:  # let the app resume it: it reads ~/.claude/projects
            slug = os.path.basename(os.path.dirname(p))
            dst = os.path.join(HOME, DEFAULT_PROFILE, "projects", slug, cid + ".jsonl")
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(p, dst); t += 1
        title = info["title"] or info["first_user"] or "Untitled session"
        if label and not a.no_tag:
            title = f"[{label}] {title}"
        rec = {"sessionId": "local_" + str(uuid.uuid4()), "cliSessionId": cid,
               "cwd": info["cwd"] or HOME, "originCwd": info["cwd"] or HOME,
               "createdAt": ms(info["t0"]), "lastActivityAt": ms(info["t1"]),
               "isArchived": False, "title": title,
               "permissionMode": info["perm"] or "default", "adoptedFromOtherSurface": True}
        if info["model"]:
            rec["model"] = info["model"]
        with open(os.path.join(target, rec["sessionId"] + ".json"), "w") as f:
            json.dump(rec, f)
        n += 1
    print(f"wrote {n} records, copied {t} transcripts into ~/{DEFAULT_PROFILE}/projects")
    print("Now quit the Claude app fully (Cmd+Q) and reopen it; a running app does not reread the index.")


if __name__ == "__main__":
    main()
