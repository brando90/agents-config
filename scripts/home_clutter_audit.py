#!/usr/bin/env python3
"""Read-only audit of agent clutter in the home folder (Trigger Rule 19).

Usage:
  home_clutter_audit.py                     # flag likely agent clutter in ~, ~/Documents, ~/Desktop
  home_clutter_audit.py --snapshot FILE     # record current top-level entries (run at task start)
  home_clutter_audit.py --diff FILE         # show entries created since the snapshot (run before reporting done)

It never moves or deletes anything. Exit code 1 when --diff finds new entries or the
default audit flags anything, so it can gate a task's completion step.
"""
from pathlib import Path
import argparse
import json
import re
import subprocess
import sys

HOME = Path.home()
SCAN = [HOME, HOME / 'Documents', HOME / 'Desktop']
DATED = re.compile(r'(\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2}|_\d{8})$')
SCRATCH = re.compile(r'(^|[-_])(wt|worktrees?|smoke|test|tmp|temp|scratch|dt|bak|backup|copy|old|runs|evidence|debug|audit)$', re.I)
LOOSE_EXT = {'.log', '.toml', '.json', '.jsonl', '.txt', '.md', '.py', '.sh', '.csv', '.out', '.err', '.patch', '.diff'}
KEEP_FILES = {'CLAUDE.md', 'AGENTS.md'}


def entries():
    for base in SCAN:
        if base.is_dir():
            for p in sorted(base.iterdir()):
                if not p.name.startswith('.'):
                    yield p


def origin(path):
    if not (path / '.git').exists():
        return None
    r = subprocess.run(['git', '-C', str(path), 'config', '--get', 'remote.origin.url'],
                       capture_output=True, text=True)
    url = r.stdout.strip().removesuffix('.git').rstrip('/')
    return url.split(':')[-1].split('github.com/')[-1] if url else None


def audit():
    flagged, remotes = [], {}
    for p in entries():
        why = []
        if DATED.search(p.name):
            why.append('dated task folder')
        if SCRATCH.search(p.stem):
            why.append('temporary/scratch name')
        if p.is_file() and p.parent == HOME and p.suffix.lower() in LOOSE_EXT and p.name not in KEEP_FILES:
            why.append('loose file in ~')
        if p.is_dir() and p.parent == HOME:
            o = origin(p)
            if o:
                remotes.setdefault(o, []).append(p)
        if why:
            flagged.append((p, why))
    for o, paths in remotes.items():
        if len(paths) > 1:
            canon = [p for p in paths if p.name == o.split('/')[-1]]
            for p in paths:
                if p not in canon:
                    flagged.append((p, [f'second clone of {o}' + (f' (canonical: ~/{canon[0].name})' if canon else '')]))
    return flagged


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--snapshot', metavar='FILE')
    g.add_argument('--diff', metavar='FILE')
    a = ap.parse_args()
    current = sorted(str(p) for p in entries())
    if a.snapshot:
        Path(a.snapshot).write_text(json.dumps(current, indent=1))
        print(f'Snapshot: {len(current)} entries -> {a.snapshot}')
        return 0
    if a.diff:
        before = set(json.loads(Path(a.diff).read_text()))
        new = [p for p in current if p not in before]
        for p in new:
            print(f'NEW  {p.replace(str(HOME), "~", 1)}')
        print(f'{len(new)} new top-level entries since snapshot')
        return 1 if new else 0
    flagged = audit()
    for p, why in flagged:
        print(f'{str(p).replace(str(HOME), "~", 1)}  [{"; ".join(why)}]')
    print(f'{len(flagged)} flagged of {len(current)} visible top-level entries (read-only; nothing changed)')
    return 1 if flagged else 0


if __name__ == '__main__':
    sys.exit(main())
