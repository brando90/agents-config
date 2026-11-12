#!/usr/bin/env python3
"""Find and remove leftover agent worktrees that hold nothing unique (Trigger Rule 19 backstop).

Usage:
  stale_checkout_sweep.py                   # dry run: classify every agent worktree as SAFE or KEEP
  stale_checkout_sweep.py --apply           # remove only the SAFE ones
  stale_checkout_sweep.py --fetch --min-age-hours 48 --json
  stale_checkout_sweep.py --conservative --json
  stale_checkout_sweep.py --conservative --fetch --only ~/.worktrees/project/finished-task --apply

Agents that run out of credits, context or turns die before their cleanup step, so their
worktrees stay behind. This sweep is the backstop any later agent (or a scheduled job) runs.
Scheduled jobs use --conservative and verify active task/schedule ownership before applying
explicit --only paths. That mode never forces removal or deletes branches/containers.

A worktree is SAFE only when every check passes: not locked; no process has its working
directory inside or names it on its command line; untouched for --min-age-hours; every path it
changed (uncommitted, untracked or in commits on no remote) has its exact content on the remote
default branch, anywhere in that branch's history (so renamed or superseded files count), or in the
main checkout; ignored files are rebuildable caches or copies found in those same places. Anything
else is KEEP with its reasons. Main checkouts and full clones are never removed. Claude desktop worktrees (<repo>/.claude/worktrees) are reported, not removed: the app's
own cleanup owns them. --apply runs `git worktree remove` (adding --force only when the dirty paths
were verified identical on the default branch), deletes the local task branch when it is merged
into the remote default branch, prunes registrations whose folder is gone, and removes empty
parent folders and empty container folders (or ones holding only a Codex
.codex-worktree-name marker) under the scanned roots. Full clones in the worktree areas are reported only.
"""
from pathlib import Path
import argparse
import filecmp
import functools
import json
import math
import os
import subprocess
import sys
import time

HOME = Path.home()
CACHE_NAMES = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.lake', 'node_modules',
               '.venv', 'venv', '.tox', '.eggs', '.cache', '.ipynb_checkpoints', '.DS_Store'}
CACHE_SUFFIXES = ('.pyc', '.egg-info', '.aux', '.bbl', '.blg', '.bcf', '.fls', '.fdb_latexmk', '.synctex.gz',
                  '.run.xml', '.toc', '.lof', '.lot', '.nav', '.snm', '.vrb')
PROTECTED_BRANCHES = {'main', 'master', 'develop', 'release'}
EMPTY_MARKERS = {'.codex-worktree-name', '.DS_Store'}  # a parent folder holding only these counts as empty
MAX_FILES = 5000              # compare at most this many changed or ignored files per worktree
MAX_COMPARE_BYTES = 2 << 30   # and at most this many bytes of ignored files


def default_roots():
    roots = [(HOME / '.worktrees', 3), (HOME / '.codex' / 'worktrees', 3),
             (HOME / '.cursor' / 'worktrees', 3), (HOME, 1)]
    roots += [(p, 1) for p in sorted(HOME.glob('*/.claude/worktrees'))]
    return roots


def git(path, *args, stdin=None):
    # --no-optional-locks: never refresh the index, so the sweep itself does not reset a worktree's age
    return subprocess.run(['git', '--no-optional-locks', '-C', str(path), *args], capture_output=True, text=True,
                          input=stdin, timeout=60, env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})


def tilde(p):
    s = str(p)
    return '~' + s[len(str(HOME)):] if s.startswith(str(HOME) + os.sep) else s


def find_worktrees(root, depth):
    """Yield folders whose .git is a file (a linked worktree), at most `depth` levels below root."""
    stack = [(root, 0)]
    while stack:
        d, n = stack.pop()
        g = d / '.git'
        if n and g.is_file():
            yield d
            continue
        if (n and g.exists()) or n >= depth:
            continue
        try:
            kids = [k for k in d.iterdir() if k.is_dir() and not k.is_symlink()]
        except OSError:
            continue
        stack += [(k, n + 1) for k in kids]


def registered(main_repo):
    """Linked worktrees a main checkout knows about: (path, prunable)."""
    r = git(main_repo, 'worktree', 'list', '--porcelain')
    out, cur = [], None
    for line in r.stdout.splitlines() + ['']:
        if line.startswith('worktree '):
            cur = {'path': Path(line[9:]), 'prunable': False}
        elif line.startswith('prunable') and cur:
            cur['prunable'] = True
        elif not line and cur:
            out.append(cur)
            cur = None
    return out[1:]  # the first entry is the main checkout itself


def only_markers(d):
    """True when folder d holds nothing but EMPTY_MARKERS files and folders that do the same."""
    try:
        return all((k.is_file() and not k.is_symlink() and k.name in EMPTY_MARKERS)
                   or (k.is_dir() and not k.is_symlink() and only_markers(k)) for k in d.iterdir())
    except OSError:
        return False


def leftovers(roots, min_age_hours, now):
    """Empty container folders and full clones directly in the worktree areas (not in ~ itself)."""
    empty, clones = [], []
    for root, depth in roots:
        if root == HOME or depth < 2 or not root.is_dir():
            continue
        level = [k for k in root.iterdir() if k.is_dir() and not k.is_symlink()]
        for n in range(1, depth):
            nxt = []
            for d in level:
                if (d / '.git').is_dir():
                    clones.append(d)
                elif not (d / '.git').exists():
                    if only_markers(d):
                        if (now - d.lstat().st_mtime) / 3600 >= min_age_hours:
                            empty.append(d)
                    elif n + 1 < depth:
                        nxt += [k for k in d.iterdir() if k.is_dir() and not k.is_symlink()]
            level = nxt
    return sorted(empty), sorted(clones)


def remove_empty(d):
    for k in d.iterdir():
        remove_empty(k) if k.is_dir() else k.unlink()
    d.rmdir()


def busy_paths():
    r = subprocess.run(['lsof', '-a', '-d', 'cwd', '-u', str(os.getuid()), '-Fn'], capture_output=True, text=True,
                       timeout=30)
    if r.returncode or not r.stdout.strip() or r.stderr.strip():
        raise RuntimeError('cannot establish process working directories; cleanup withheld')
    cwds = {Path(l[1:]) for l in r.stdout.splitlines() if l.startswith('n/')}
    r = subprocess.run(['ps', '-axo', 'pid=,ppid=,command='], capture_output=True, text=True, timeout=30)
    if r.returncode or not r.stdout.strip():
        raise RuntimeError('cannot establish process commands; cleanup withheld')
    processes = {int(parts[0]): (int(parts[1]), parts[2]) for line in r.stdout.splitlines()
                 if len(parts := line.strip().split(None, 2)) == 3}
    ancestors, pid = set(), os.getpid()
    while pid and pid not in ancestors:
        ancestors.add(pid)
        pid = processes.get(pid, (0, ''))[0]
    # A wrapper shell repeats --only in argv. Exclude its argv, but retain
    # ALL working directories above, so a launcher inside a checkout protects it.
    commands = [cmd for pid, (_, cmd) in processes.items() if pid not in ancestors]
    return cwds, commands


def classify_conservative(p, busy, min_age_hours, now):
    """Periodic cleanup: require a clean, landed checkout; preserve every local file.

    The caller must also establish that no scheduled consumer or active task owns it.
    Never infer that staged content or ignored files are expendable from their names.
    """
    info = {'path': str(p), 'status': 'KEEP', 'reasons': [], 'notes': [],
            'force': False, 'branch': None, 'common': None}
    why = info['reasons']
    gd = git(p, 'rev-parse', '--absolute-git-dir')
    cd = git(p, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    if gd.returncode or cd.returncode:
        why.append('not a readable linked worktree')
        return info
    gitdir, common = Path(gd.stdout.strip()), Path(cd.stdout.strip())
    info['common'] = str(common)
    if gitdir == common or not (p / '.git').is_file() or p.is_symlink():
        why.append('not a standalone linked worktree path')
    if any(x in p.parts or x in p.resolve().parts for x in ('.claude', '.codex', '.cursor')):
        why.append('app-managed worktree: use the owning app cleanup')
    if (gitdir / 'locked').exists():
        why.append('locked')
    real = p.resolve()
    cwds, cmds = busy
    if any(c == real or real in c.parents for c in cwds) or any(str(p) in c or str(real) in c for c in cmds):
        why.append('in use by a running process')
    rc, entries = status_entries(p)
    if rc or entries:
        why.append('git status failed' if rc else 'local changes, untracked or ignored files require owner reconciliation')
    index = git(p, 'ls-files', '-v', '-z')
    if index.returncode or any(x and (x[0] == 'S' or x[0].islower()) for x in index.stdout.split('\0')):
        why.append('index may hide local modifications (skip-worktree/assume-unchanged)')
    # A clean, landed HEAD may still have unique detached commits in its own
    # reflog. Removing the worktree would discard that recovery handle.
    reflog = git(p, 'reflog', 'show', '--format=%H', 'HEAD')
    if reflog.returncode:
        why.append('HEAD recovery history could not be inspected')
    elif reflog.stdout.strip():
        unique = git(p, 'rev-list', '--stdin', '--not', '--branches', '--tags', '--remotes', stdin=reflog.stdout)
        if unique.returncode or unique.stdout.strip():
            why.append('HEAD recovery history contains commits not preserved by repository refs')
    if (any((gitdir / 'refs').rglob('*')) or any(gitdir.glob('BISECT_*'))
            or any((gitdir / x).exists() for x in ('rebase-merge', 'rebase-apply', 'sequencer',
                                                  'MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD'))):
        why.append('worktree-local refs or in-progress Git operation require owner reconciliation')
    if (p / '.gitmodules').exists():
        why.append('submodules require owner reconciliation')
    base = default_branch(p)
    if not base or git(p, 'merge-base', '--is-ancestor', 'HEAD', base).returncode:
        why.append('HEAD is not proven landed on the remote default branch')
    age = (now - last_activity(p, gitdir)) / 3600
    if age < min_age_hours:
        why.append(f'touched {age:.0f}h ago (< {min_age_hours:g}h)')
    # Keep shared branch refs; the worktree's own HEAD reflog is removed by Git,
    # so its unique history must already have been rejected above.
    if not why:
        info['status'] = 'SAFE'
    return info


def is_cache(rel):
    return any(p in CACHE_NAMES or p.endswith(CACHE_SUFFIXES) for p in Path(rel.rstrip('/')).parts)


def reflog_time(gitdir):
    """Timestamp of the newest HEAD reflog entry (its file mtime is unreliable: gc rewrites reflogs)."""
    try:
        with open(gitdir / 'logs' / 'HEAD', 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 4096))
            last = f.read().splitlines()[-1].decode(errors='replace')
        return float(last.split('\t', 1)[0].split()[-2])
    except (OSError, IndexError, ValueError):
        return 0


def last_activity(p, gitdir, files=()):
    """Newest of the folder, HEAD, its reflog entry and the changed files (not the index, which any `git status`
    rewrites, nor the reflog file, which gc rewrites)."""
    times = [reflog_time(gitdir)]
    for f in (p, gitdir / 'HEAD', *(p / x for x in files)):
        try:
            times.append(f.lstat().st_mtime)
        except OSError:
            pass
    return max(times)


def status_entries(p):
    """(returncode, [(XY, path)]) from `git status --porcelain -z --ignored`; a rename's old path counts as deleted."""
    r = subprocess.run(['git', '--no-optional-locks', '-C', str(p), 'status', '--porcelain', '-z',
                        '--ignored', '--untracked-files=normal'], capture_output=True, timeout=60)
    toks, out, i = r.stdout.decode(errors='surrogateescape').split('\0'), [], 0
    while i < len(toks):
        t = toks[i]
        i += 1
        if len(t) < 4:
            continue
        out.append((t[:2], t[3:]))
        if t[0] in 'RC' and i < len(toks):
            out.append(('D ', toks[i]))
            i += 1
    return r.returncode, out


def expand(p, rels, skip_cache=False):
    """Relative file paths under `rels` (directories walked), or None past MAX_FILES."""
    files = []
    for rel in rels:
        full = p / rel
        if rel.endswith('/') and full.is_dir() and not full.is_symlink():
            for root, dirs, names in os.walk(full):
                if skip_cache:
                    dirs[:] = [d for d in dirs if not is_cache(d)]
                files += [os.path.relpath(os.path.join(root, n), p) for n in names if not (skip_cache and is_cache(n))]
                if len(files) > MAX_FILES:
                    return None
        else:
            files.append(rel.rstrip('/'))
    return files if len(files) <= MAX_FILES else None


def not_on_base(p, base, paths):
    """Paths whose current worktree content (or absence) differs from `base`, or None if too many to check."""
    if paths is None or len(paths) > MAX_FILES:
        return None
    paths = sorted(set(paths))
    if not paths:
        return []
    r = git(p, 'cat-file', '--batch-check', stdin=''.join(f'{base}:{x}\n' for x in paths))
    on_base = dict(zip(paths, (l.split()[0] if not l.endswith(' missing') else None for l in r.stdout.splitlines())))
    present = [x for x in paths if (p / x).is_file() and not (p / x).is_symlink()]
    h = git(p, 'hash-object', '--stdin-paths', stdin=''.join(f'{x}\n' for x in present))
    here = dict(zip(present, h.stdout.split()))
    diff = []
    for x in paths:
        if x in here:
            if here[x] != on_base.get(x):
                diff.append(x)
        elif os.path.lexists(p / x) or on_base.get(x):  # symlink, directory or nested repo; or deleted here only
            diff.append(x)
    return diff


@functools.lru_cache(maxsize=None)
def history_objects(common, base):
    """Every object id reachable from `base` in the repository at `common` (all paths, all history)."""
    r = git(common, 'rev-list', '--objects', base)
    return frozenset(l.split(' ', 1)[0] for l in r.stdout.splitlines())


def in_history(p, common, base, paths):
    """Paths whose exact current content appears anywhere in `base`'s history (renamed or later superseded)."""
    present = [x for x in paths if (p / x).is_file() and not (p / x).is_symlink()]
    if not (base and present):
        return set()
    seen = history_objects(str(common), base)
    h = git(p, 'hash-object', '--stdin-paths', stdin=''.join(f'{x}\n' for x in present))
    return {x for x, sha in zip(present, h.stdout.split()) if sha in seen}


def same_in_main(p, main, rel):
    """True when the main checkout holds the same file at `rel` (or neither has it)."""
    if main is None:
        return False
    a, b = p / rel, main / rel
    if not os.path.lexists(a):
        return not os.path.lexists(b)
    return (a.is_file() and not a.is_symlink() and b.is_file() and not b.is_symlink()
            and filecmp.cmp(a, b, shallow=False))


def not_in_main(p, main, rels):
    """Ignored non-cache files that are not byte-identical in the main checkout, or None if too many to check."""
    files = expand(p, rels, skip_cache=True)
    if files is None or main is None:
        return None
    size, diff = 0, []
    for x in files:
        a, b = p / x, main / x
        if a.is_symlink() or not a.is_file():
            continue
        size += a.stat().st_size
        if size > MAX_COMPARE_BYTES:
            return None
        if not b.is_file() or not filecmp.cmp(a, b, shallow=False):
            diff.append(x)
    return diff


def default_branch(repo):
    r = git(repo, 'symbolic-ref', '--quiet', '--short', 'refs/remotes/origin/HEAD')
    if r.stdout.strip():
        return r.stdout.strip()
    for b in ('origin/main', 'origin/master'):
        if not git(repo, 'rev-parse', '--verify', '--quiet', b).returncode:
            return b
    return None


def some(paths):
    return ', '.join(paths[:3]) + (' ...' if len(paths) > 3 else '')


def classify(p, busy, min_age_hours, now):
    info = {'path': str(p), 'status': 'KEEP', 'reasons': [], 'notes': [], 'force': False,
            'branch': None, 'common': None}
    gd = git(p, 'rev-parse', '--absolute-git-dir')
    cd = git(p, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    if gd.returncode or cd.returncode:
        info['reasons'].append('not a readable git worktree')
        return info
    gitdir, common = Path(gd.stdout.strip()), Path(cd.stdout.strip())
    info['common'] = str(common)
    if gitdir == common:
        info['reasons'].append('main checkout, not a worktree')
        return info
    why, notes = info['reasons'], info['notes']
    main = common.parent if common.name == '.git' else None
    if '.claude' in p.parts and p.parent.name == 'worktrees':
        why.append('Claude desktop worktree: use the app cleanup')
    if (gitdir / 'locked').exists():
        why.append('locked')
    cwds, cmds = busy
    real = p.resolve()
    if any(c == real or real in c.parents for c in cwds) or any(str(p) in c or str(real) in c for c in cmds):
        why.append('in use by a running process')
    base = default_branch(p)
    rc, entries = status_entries(p)
    if rc:
        why.append('git status failed')
    changed = [x for xy, x in entries if xy != '!!' and not (xy == '??' and is_cache(x))]
    paths = expand(p, changed, skip_cache=True)
    age = (now - last_activity(p, gitdir, paths or ())) / 3600
    if age < min_age_hours:
        why.append(f'touched {age:.0f}h ago (< {min_age_hours:g}h)')
    ahead = git(p, 'rev-list', '--count', 'HEAD', '--not', '--remotes')
    n_ahead = int(ahead.stdout.strip() or 0) if not ahead.returncode else None
    if n_ahead is None:
        why.append('HEAD unreadable')
    if changed or n_ahead:
        touched = git(p, 'log', '--format=', '--name-only', '--no-renames', 'HEAD', '--not', '--remotes')
        if paths is not None:
            paths += [x for x in touched.stdout.splitlines() if x]
        diff = not_on_base(p, base, paths) if base else None
        if diff:
            diff = [x for x in diff if not same_in_main(p, main, x)]
        if diff:
            old = in_history(p, common, base, diff)
            diff = [x for x in diff if x not in old]
        what = ', '.join([f'{len(changed)} uncommitted/untracked paths'] * bool(changed) +
                         [f'{n_ahead} commits on no remote'] * bool(n_ahead))
        if diff is None:
            why.append(f'{what} (too many to compare)' if base else f'{what} (no remote default branch)')
        elif diff:
            why.append(f'{what}; {len(diff)} differ from {base}: {some(diff)}')
        else:
            notes.append(f'{what}, all on {base} (now or in its history) or in the main checkout')
            info['force'] = bool(changed)
    extra = [x for xy, x in entries if xy == '!!' and not is_cache(x)]
    if extra:
        diff = not_in_main(p, main, extra)
        if diff:
            old = in_history(p, common, base, diff)
            diff = [x for x in diff if x not in old]
        if diff is None:
            why.append(f'ignored non-cache files (too many to compare): {some(extra)}')
        elif diff:
            why.append(f'{len(diff)} ignored files not in main checkout: {some(diff)}')
        else:
            notes.append('ignored files identical in main checkout')
    info['branch'] = git(p, 'symbolic-ref', '--quiet', '--short', 'HEAD').stdout.strip() or None
    if not why:
        info['status'] = 'SAFE'
    return info


def remove(info, roots):
    p, common, branch = Path(info['path']), info['common'], info['branch']
    base = default_branch(common)
    merged = bool(branch and base and branch not in PROTECTED_BRANCHES and branch != base.split('/', 1)[-1]
                  and not git(common, 'merge-base', '--is-ancestor', branch, base).returncode)
    r = git(common, 'worktree', 'remove', *(['--force'] if info['force'] else []), str(p))
    if r.returncode or p.exists():
        return f'FAILED  {tilde(p)}: {((r.stderr or "").strip().splitlines() or ["folder still present"])[-1]}'
    note = ''
    if merged and not git(common, 'branch', '-d', branch).returncode:
        note = f' (deleted merged local branch {branch})'
    tops = [r for r, _ in roots if r != HOME]
    d = p.parent
    while d not in tops and d != HOME and any(t in d.parents for t in tops):
        try:
            if any(k.name not in EMPTY_MARKERS or not k.is_file() for k in d.iterdir()):
                break
            for k in d.iterdir():
                k.unlink()
            d.rmdir()
        except OSError:
            break
        d = d.parent
    return f'REMOVED {tilde(p)}{note}'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true', help='remove the SAFE worktrees')
    ap.add_argument('--fetch', action='store_true', help='git fetch each repository first so the default branch is current')
    ap.add_argument('--min-age-hours', type=float, default=24.0)
    ap.add_argument('--root', action='append', metavar='DIR[:DEPTH]', help='scan these roots instead of the defaults')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--conservative', action='store_true',
                    help='require clean landed worktrees; retain all local/ignored files and app-managed worktrees')
    ap.add_argument('--only', action='append', metavar='PATH',
                    help='inspect/apply only this exact linked worktree (repeatable); verify task/schedule ownership first')
    a = ap.parse_args()
    if not math.isfinite(a.min_age_hours) or a.min_age_hours < 0:
        ap.error('--min-age-hours must be finite and nonnegative')
    if a.conservative and a.apply and (not a.fetch or not a.only):
        ap.error('conservative apply requires --fetch and explicit --only paths after ownership checks')
    roots = [(Path(s.rsplit(':', 1)[0]).expanduser(), int(s.rsplit(':', 1)[1]) if ':' in s else 3)
             for s in a.root] if a.root else default_roots()

    found = ({Path(p).expanduser().absolute(): Path(p).expanduser().absolute() for p in a.only}
             if a.only else {p.resolve(): p for r, depth in roots if r.is_dir() for p in find_worktrees(r, depth)})
    mains = set() if a.only else {p for r, _ in roots if r.is_dir() for p in r.iterdir() if (p / '.git').is_dir()}
    for m in sorted(mains):
        for w in registered(m):
            if w['path'].is_dir():
                found.setdefault(w['path'].resolve(), w['path'])
    commons = {Path(git(p, 'rev-parse', '--path-format=absolute', '--git-common-dir').stdout.strip())
               for p in found.values()}
    owners = {c.parent if c.name == '.git' else c for c in commons if str(c) != '.'}
    repos = mains | owners
    failed_fetch = set()
    if a.fetch:
        for m in sorted(owners):
            if git(m, 'fetch', '--quiet', 'origin').returncode:
                failed_fetch.add(str(m))

    busy, now = busy_paths(), time.time()
    classifier = classify_conservative if a.conservative else classify
    results = [classifier(p, busy, a.min_age_hours, now) for p in sorted(found.values())]
    for i in results:
        common = Path(i['common']) if i['common'] else None
        owner = common.parent if common and common.name == '.git' else common
        if str(owner) in failed_fetch:
            i['status'] = 'KEEP'
            i['reasons'].append('fetch failed; remote state not verified')
    prunable = sorted(m for m in repos if any(w['prunable'] for w in registered(m)))
    empty, clones = ([], []) if a.only else leftovers(roots, a.min_age_hours, now)
    actions = []
    if a.apply:
        for i in results:
            if i['status'] != 'SAFE':
                continue
            if a.conservative:
                try:
                    fresh = classifier(Path(i['path']), busy_paths(), a.min_age_hours, time.time())
                except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
                    i['status'] = 'KEEP'
                    i['reasons'].append(f'pre-removal check failed: {type(exc).__name__}')
                    actions.append(f'FAILED  {tilde(Path(i["path"]))}: pre-removal check failed; remaining cleanup withheld')
                    break
                i.update(fresh)
                if i['status'] != 'SAFE':
                    continue
            try:
                actions.append(remove(i, [] if a.conservative else roots))
            except (OSError, subprocess.TimeoutExpired) as exc:
                actions.append(f'FAILED  {tilde(Path(i["path"]))}: removal interrupted ({type(exc).__name__}); inspect path')
                break
        for d in ([] if a.conservative else empty):
            if d.exists() and only_markers(d):
                remove_empty(d)
                actions.append(f'REMOVED empty folder {tilde(d)}')
        for m in ([] if a.conservative else prunable):
            git(m, 'worktree', 'prune')
            actions.append(f'PRUNED  stale registrations in {tilde(m)}')

    if a.json:
        print(json.dumps({'results': results, 'actions': actions, 'prunable': list(map(str, prunable)),
                          'empty': list(map(str, empty)), 'clones': list(map(str, clones))}, indent=1))
        return 1 if failed_fetch or any(x.startswith('FAILED') for x in actions) else 0
    for i in results:
        extra = i['reasons'] or i['notes']
        print(f'{i["status"]:4}  {tilde(i["path"])}' + (f'  [{"; ".join(extra)}]' if extra else ''))
    for m in prunable:
        print(f'PRUNE {tilde(m)}  [registered worktree folder already deleted]')
    for d in empty:
        print(f'EMPTY {tilde(d)}  [container folder with no worktree left]')
    for d in clones:
        print(f'CLONE {tilde(d)}  [full clone in a worktree area: verify its refs and files elsewhere, then remove by hand]')
    for line in actions:
        print(line)
    safe = sum(i['status'] == 'SAFE' for i in results)
    removed = sum(x.startswith('REMOVED ') and not x.startswith('REMOVED empty folder') for x in actions)
    mode = f'eligible, {removed} removed' if a.apply else 'eligible (dry run)'
    print(f'{len(results)} worktrees: {safe} SAFE {mode}, {len(results) - safe} KEEP; '
          f'{len(empty)} empty folders, {len(prunable)} repos with stale registrations, {len(clones)} full clones')
    return 1 if failed_fetch or any(x.startswith('FAILED') for x in actions) else 0


if __name__ == '__main__':
    sys.exit(main())
