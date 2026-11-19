#!/usr/bin/env python3
"""TLDR: Writer-independent paper auto-compile. Polls every paper dir (paper_latex*/<VENUE>/) of the given repos
for changed .tex/.bib/figure files, no matter who changed them (Cursor save, Claude/Codex shell edits, git pull),
and hands each change to the repo's own PostToolUse compile hook (.claude/hooks/compile_paper_on_edit.sh), which
rebuilds every 00_main_*.tex and atomically replaces the committed PDFs. Falls back to latexmk when a repo has no
hook. Runs forever; meant to be started by launchd (see install_paper_watch.sh). Log: ~/Library/Logs/paper_watch.log.

Usage: python3 paper_watch.py [--interval 2] [--once] REPO [REPO ...]
"""
import argparse, json, os, stat, subprocess, sys, time
from pathlib import Path

WATCHED_SUFFIXES = {".tex", ".bib", ".sty", ".bst", ".cls", ".png", ".pdf", ".jpg", ".jpeg", ".csv", ".txt"}
SKIP_DIRS = {"_build", ".git", "node_modules", "__pycache__"}
LOG = Path.home() / "Library" / "Logs" / "paper_watch.log"


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%m-%d-%Y %H:%M:%S")
    with LOG.open("a") as fh:
        fh.write(f"{stamp} {msg}\n")


def paper_dirs(repo: Path):
    """Every paper_latex*/<VENUE>/ dir that holds a 00_main_*.tex and no .no-autocompile marker."""
    for bucket in sorted(repo.glob("paper_latex*")):
        if not bucket.is_dir():
            continue
        for venue in sorted(bucket.iterdir()):
            if venue.is_dir() and not (venue / ".no-autocompile").exists() and list(venue.glob("00_main_*.tex")):
                yield venue


def snapshot(venue: Path):
    """{relative path: mtime_ns} for watched sources under a paper dir (committed PDFs excluded: they are outputs)."""
    snap = {}
    mains = {p.stem for p in venue.glob("00_main_*.tex")}
    venue_str = str(venue)
    for root, dirnames, filenames in os.walk(venue_str):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_root = os.path.relpath(root, venue_str)
        is_top = rel_root == "."
        for fn in filenames:
            stem, ext = os.path.splitext(fn)
            ext_low = ext.lower()
            if ext_low not in WATCHED_SUFFIXES:
                continue
            if is_top and ext_low == ".pdf" and stem in mains:
                continue  # the compiled outputs, not inputs
            full = os.path.join(root, fn)
            try:
                st = os.stat(full)
            except OSError:
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            rel = fn if is_top else os.path.join(rel_root, fn)
            snap[rel] = st.st_mtime_ns
    return snap


def recompile(repo: Path, venue: Path, changed: str) -> None:
    hook = repo / ".claude" / "hooks" / "compile_paper_on_edit.sh"
    trigger = venue / changed
    if hook.exists():
        payload = json.dumps({"tool_input": {"file_path": str(trigger)}})
        subprocess.run(["bash", str(hook)], input=payload, text=True, capture_output=True, timeout=60)
        log(f"{venue.name}: change in {changed} -> hook dispatched")
        return
    # Fallback: build each main in place with latexmk, copy the PDF next to the sources.
    env = dict(os.environ)
    env["PATH"] = "/usr/local/texlive/2024/bin/universal-darwin:" + env.get("PATH", "")
    build = venue / "_build"; build.mkdir(exist_ok=True)
    for main in sorted(venue.glob("00_main_*.tex")):
        res = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-f", f"-outdir={build}", main.name],
                             cwd=venue, env=env, capture_output=True, text=True, timeout=900)
        pdf = build / (main.stem + ".pdf")
        if pdf.exists():
            tmp = venue / f".{main.stem}.pdf.tmp"; tmp.write_bytes(pdf.read_bytes()); tmp.replace(venue / (main.stem + ".pdf"))
        log(f"{venue.name}: change in {changed} -> latexmk {main.name} exit {res.returncode}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--once", action="store_true", help="scan once and exit (for tests)")
    args = ap.parse_args()
    repos = [Path(r).expanduser().resolve() for r in args.repos]
    state = {}
    for repo in repos:
        for venue in paper_dirs(repo):
            state[venue] = snapshot(venue)
    log(f"watching {sum(len(s) for s in state.values())} files in {len(state)} paper dirs across {len(repos)} repos")
    while True:
        for repo in repos:
            for venue in paper_dirs(repo):
                new = snapshot(venue)
                old = state.get(venue)
                state[venue] = new
                if old is None:
                    log(f"{venue.name}: new paper dir, now watched"); continue
                changed = [k for k in new if new[k] != old.get(k)] + [k for k in old if k not in new]
                if changed:
                    recompile(repo, venue, changed[0] if changed[0] in new else next(iter(new)))
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
