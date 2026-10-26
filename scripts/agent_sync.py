#!/usr/bin/env python3
"""TLDR: Shared state between Brando's agents (Codex, Claude Code, ultimate_brando9): check a project's SYNC.md
across every branch and name conflicts, watch codex/* and claude/* branch heads, and build the [PUSH] inbox comment.

Rule: Trigger Rule 71 (rules/services.md); procedure: workflows/agent-sync.md. Python 3.9+ and git only.

  check   python3 ~/agents-config/scripts/agent_sync.py check [--repo .] [--file experiments/vb-priv/SYNC.md]
          Reads the SYNC.md at the head of every branch (and the working tree), keeps each agent's newest section,
          and prints a CONFLICT line for every key two agents disagree on. Exit 1 when there is a conflict.
  watch   python3 agent_sync.py watch --repo-url https://github.com/brando90/vb-priv-bmg [--repo-url ...]
          Session-start check: prints every codex/* or claude/* branch head that moved since the last watch
          (commits, SYNC.md diff, conflicts), then remembers the heads in --state. No timer: run it when you start.
  ping-body  used by .github/workflows/agent-sync-ping.yml to write the [PUSH] comment for one push.
"""
import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ZERO = '0' * 40
META = {'updated', 'commit', 'branch', 'doing', 'next', 'note', 'notes', 'asks', 'agent'}
BULLET = re.compile(r'^\s*[-*]\s+`?([A-Za-z0-9][A-Za-z0-9_ ./-]*?)`?\s*:\s+(.*\S)\s*$')
DEFAULT_PATTERNS = ('codex/*', 'claude/*')
MAX_COMMITS, MAX_DIFF = 10, 40


def git(repo, *args, check=True):
    out = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    if check and out.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {out.stderr.strip()}")
    return out.stdout if out.returncode == 0 else None


# ---------- SYNC.md ----------

def norm(value):
    """A value as compared: comments in a trailing (parenthesis) and `code` marks left out, case and spaces folded."""
    value = re.sub(r'\s*\([^()]*\)\s*$', '', value.strip()).replace('`', '')
    return ' '.join(value.split()).casefold()


def when(text):
    try:
        t = dt.datetime.fromisoformat(text.strip().replace('Z', '+00:00'))
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def parse(text):
    """{agent: {key: value}} for each '## <agent>' section that has an 'updated:' line."""
    sections, name = {}, None
    for line in text.splitlines():
        heading = re.match(r'^##\s+(.+?)\s*#*$', line)
        if heading:
            name = heading[1].strip().strip('`')
            sections[name] = {}
            continue
        bullet = BULLET.match(line)
        if name and bullet:
            key = bullet[1].strip().lower().replace(' ', '_')
            sections[name].setdefault(key, bullet[2].strip())
    return {n: kv for n, kv in sections.items() if 'updated' in kv}


def refs(repo):
    names = []
    for space in ('refs/remotes', 'refs/heads'):  # GitHub's copies first, so a tie names origin/<branch>
        names += (git(repo, 'for-each-ref', '--format=%(refname)', space) or '').split()
    return [r for r in names if not r.endswith('/HEAD')]


def versions(repo, path, worktree=True):
    """(source, text) of path at every branch head, plus the working tree's copy."""
    found = []
    for ref in refs(repo):
        text = git(repo, 'show', f'{ref}:{path}', check=False)
        if text is not None:
            found.append((ref.replace('refs/remotes/', '').replace('refs/heads/', ''), text))
    local = Path(repo) / path
    if worktree and local.is_file():
        found.append(('working tree', local.read_text()))
    return found


def newest(found):
    """Each agent's newest section across all versions: {agent: (updated, kv, source)}; and warnings."""
    best, warn = {}, []
    for source, text in found:
        for agent, kv in parse(text).items():
            t = when(kv['updated'])
            if t is None:
                warn.append(f"{agent} in {source}: 'updated: {kv['updated']}' is not ISO 8601 (2026-10-26T11:20-07:00)")
                t = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
            if agent not in best or t > best[agent][0]:
                best[agent] = (t, kv, source)
    return best, warn


def conflicts(best):
    keys = sorted({k for _, kv, _ in best.values() for k in kv} - META)
    out = []
    for key in keys:
        said = {a: kv[key] for a, (_, kv, _) in best.items() if key in kv}
        if len({norm(v) for v in said.values()}) > 1:
            parts = [f'{a} = "{v}" [{best[a][1]["updated"]}, commit {best[a][1].get("commit", "?")}, {best[a][2]}]'
                     for a, v in sorted(said.items())]
            out.append(f'CONFLICT {key}: ' + ' | '.join(parts))
    return out


def sync_files(repo):
    found = set()
    for ref in refs(repo):
        for p in (git(repo, 'ls-tree', '-r', '--name-only', ref, check=False) or '').splitlines():
            if p == 'SYNC.md' or p.endswith('/SYNC.md'):
                found.add(p)
    return sorted(found)


def report(repo, path, worktree=True):
    """Lines describing one SYNC.md, and its conflicts."""
    best, warn = newest(versions(repo, path, worktree))
    if not best:
        return [f'{path}: no agent sections (each needs an "- updated:" line)'], []
    agents = '; '.join(f'{a} {kv["updated"]} @{kv.get("commit", "?")} ({src})'
                       for a, (_, kv, src) in sorted(best.items()))
    found = conflicts(best)
    return [f'{path}: {len(best)} agents: {agents}'] + [f'WARNING {w}' for w in warn] + found, found


def cmd_check(a):
    repo = Path(a.repo).resolve()
    if not a.no_fetch:
        if git(repo, 'fetch', '--quiet', '--prune', 'origin', check=False) is None:
            print('WARNING: git fetch failed; checking the branches already fetched')
    files = a.file or sync_files(repo)
    if not files:
        print('No SYNC.md on any branch.')
        return 0
    bad = False
    for path in files:
        lines, found = report(repo, path)
        print('\n'.join(lines))
        bad |= bool(found)
    if bad:
        print('Name each CONFLICT to Brando and in the agent inbox; do not pick one value (Rule 71).')
    return 1 if bad else 0


# ---------- pushes ----------

def base_of(repo, before, head, default):
    if before and before != ZERO and git(repo, 'merge-base', '--is-ancestor', before, head, check=False) is not None:
        return before
    for ref in (f'refs/remotes/origin/{default}', f'refs/heads/{default}', default):
        mb = git(repo, 'merge-base', ref, head, check=False)
        if mb:
            return mb.strip()
    return None


def describe(repo, base, head, worktree=False):
    """Markdown lines for the commits base..head: subjects, SYNC.md diffs, conflicts in the changed SYNC.md."""
    span = f'{base}..{head}' if base else head
    log = (git(repo, 'log', '--format=%h %s', span) or '').splitlines()
    lines = [f'{len(log)} new commit(s):'] + [f'- {c}' for c in log[:MAX_COMMITS]]
    if len(log) > MAX_COMMITS:
        lines.append(f'- ... and {len(log) - MAX_COMMITS} more')
    changed = []
    if base:
        changed = [p for p in (git(repo, 'diff', '--name-only', base, head) or '').splitlines()
                   if p == 'SYNC.md' or p.endswith('/SYNC.md')]
    found = []
    for path in changed:
        diff = [d for d in (git(repo, 'diff', '--unified=0', base, head, '--', path) or '').splitlines()
                if d[:1] in '+-' and not d.startswith(('+++', '---'))]
        lines += [f'{path} changed:', '```diff'] + diff[:MAX_DIFF] + (['...'] if len(diff) > MAX_DIFF else []) + ['```']
        more, c = report(repo, path, worktree)
        lines += more
        found += c
    if changed and not found:
        lines.append('Conflicts: none.')
    return lines, found


def cmd_ping_body(a):
    repo = Path(a.repo).resolve()
    base = base_of(repo, a.before, a.after, a.default_branch)
    lines, found = describe(repo, base, a.after)
    subject = (git(repo, 'log', '-1', '--format=%s', a.after) or '').strip()
    new = ' (new branch)' if a.before in ('', ZERO) else ''
    head = f'[PUSH] {a.repo_name} `{a.branch}` @ {a.after[:8]}{new} by {a.pusher}: {subject}'
    body = [head, ''] + lines
    if found:
        body.append('Agents: name these conflicts to Brando and reply here; do not pick one value (Rule 71).')
    if a.compare_url:
        body += ['', a.compare_url]
    if a.notify:
        body += ['', f'@{a.notify}: automatic ping so ultimate_brando9 sees this push (Rule 71); nothing for you to do.']
    print('\n'.join(body))
    return 0


def cmd_watch(a):
    state_path = Path(os.path.expanduser(a.state))
    state = json.loads(state_path.read_text()) if state_path.is_file() else {}
    cache = state_path.parent / 'repos'
    cache.mkdir(parents=True, exist_ok=True)
    anything = False
    for url in a.repo_url:
        slug = re.sub(r'[^A-Za-z0-9._-]+', '__', url.split('://')[-1]).strip('_')
        repo = cache / f'{slug}.git'
        if not repo.exists():
            r = subprocess.run(['git', 'clone', '--quiet', '--bare', '--filter=blob:none', url, str(repo)],
                               capture_output=True, text=True)
            if r.returncode:
                print(f'ERROR {url}: clone failed: {r.stderr.strip()}')
                continue
        if git(repo, 'fetch', '--quiet', '--prune', '--filter=blob:none', 'origin',
               '+refs/heads/*:refs/heads/*', check=False) is None:
            print(f'ERROR {url}: fetch failed (access? network?)')
            continue
        default = (git(repo, 'symbolic-ref', '--short', 'HEAD', check=False) or 'main').strip()
        heads = {}
        for line in (git(repo, 'for-each-ref', '--format=%(refname:short) %(objectname)', 'refs/heads') or '').splitlines():
            name, sha = line.split()
            if any(fnmatch.fnmatch(name, p) for p in a.pattern):
                heads[name] = sha
        seen = state.get(url)
        if seen is None:
            print(f'{url}: first watch, {len(heads)} branch heads recorded as the baseline; later runs report changes.')
        else:
            moved = {n: s for n, s in heads.items() if seen.get(n) != s}
            gone = sorted(set(seen) - set(heads))
            for name, sha in sorted(moved.items()):
                anything = True
                old = seen.get(name)
                base = base_of(repo, old or ZERO, sha, default)
                subject = (git(repo, 'log', '-1', '--format=%s', sha) or '').strip()
                print(f'\n[PUSH] {url} `{name}` @ {sha[:8]}{"" if old else " (new branch)"}: {subject}')
                lines, _ = describe(repo, base, sha)
                print('\n'.join(lines))
            if gone:
                print(f'\n{url}: branches deleted since last watch: {", ".join(gone)}')
            if not moved and not gone:
                print(f'{url}: no new commits on {", ".join(a.pattern)}.')
        state[url] = heads
    if not a.dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=1, sort_keys=True))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('check', help='name conflicts in SYNC.md across all branches')
    c.add_argument('--repo', default='.')
    c.add_argument('--file', action='append', help='SYNC.md path from the repo root (default: every SYNC.md)')
    c.add_argument('--no-fetch', action='store_true')
    w = sub.add_parser('watch', help='report codex/* and claude/* heads that moved since the last watch')
    w.add_argument('--repo-url', action='append', required=True)
    w.add_argument('--pattern', action='append', help=f'branch glob (default: {" ".join(DEFAULT_PATTERNS)})')
    w.add_argument('--state', default='~/.cache/agent-sync/seen.json')
    w.add_argument('--dry-run', action='store_true', help='report without remembering the heads')
    b = sub.add_parser('ping-body', help='the [PUSH] comment for one push (GitHub Actions)')
    b.add_argument('--repo', default='.')
    b.add_argument('--repo-name', required=True)
    b.add_argument('--branch', required=True)
    b.add_argument('--before', default='')
    b.add_argument('--after', required=True)
    b.add_argument('--default-branch', default='main')
    b.add_argument('--pusher', default='?')
    b.add_argument('--compare-url', default='')
    b.add_argument('--notify', default='', help='GitHub login to @mention, so GitHub emails the push')
    a = p.parse_args(argv)
    if a.cmd == 'watch' and not a.pattern:
        a.pattern = list(DEFAULT_PATTERNS)
    return {'check': cmd_check, 'watch': cmd_watch, 'ping-body': cmd_ping_body}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
