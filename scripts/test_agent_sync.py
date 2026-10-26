#!/usr/bin/env python3
"""Checks for agent_sync.py on throwaway git repos: conflicts across branches, the watch, the [PUSH] comment."""
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import agent_sync

SYNC = 'experiments/vb-priv/SYNC.md'


def section(agent, updated, commit, **facts):
    lines = [f'## {agent}', f'- updated: {updated}', f'- commit: {commit}']
    return '\n'.join(lines + [f'- {k}: {v}' for k, v in facts.items()]) + '\n\n'


class Repos:
    """An origin repo and a clone that pushes to it, like Brando's Mac and GitHub."""

    def __init__(self, root):
        self.origin, self.work = root / 'origin.git', root / 'work'
        self.run(root, 'init', '--quiet', '--bare', '--initial-branch=main', str(self.origin))
        self.run(root, 'clone', '--quiet', str(self.origin), str(self.work))
        for k, v in (('user.email', 'a@example.org'), ('user.name', 'agent'), ('commit.gpgsign', 'false')):
            self.run(self.work, 'config', k, v)
        self.commit('main', {'README.md': 'repo\n'}, 'init', new=False, orphan=True)

    @staticmethod
    def run(cwd, *args):
        return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

    def commit(self, branch, files, message, new=True, orphan=False, base='main'):
        if orphan:
            self.run(self.work, 'checkout', '--quiet', '-B', branch)
        elif new:
            self.run(self.work, 'checkout', '--quiet', '-B', branch, f'origin/{base}')
        else:
            self.run(self.work, 'checkout', '--quiet', branch)
        for name, text in files.items():
            path = self.work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            self.run(self.work, 'add', name)
        self.run(self.work, 'commit', '--quiet', '-m', message)
        self.run(self.work, 'push', '--quiet', 'origin', branch)
        self.run(self.work, 'fetch', '--quiet', 'origin')
        return self.run(self.work, 'rev-parse', 'HEAD')


def call(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = agent_sync.main(list(argv))
    return code, out.getvalue()


class AgentSyncTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.r = Repos(self.root)
        base = '# vb-priv SYNC\n\n' + section('ultimate_brando9', '2026-10-26T10:00-07:00', 'aaaa1111',
                                              accepted_tasks='11/180 (new rule 10-26-2026)', gate='new')
        base += section('codex', '2026-10-26T09:00-07:00', 'aaaa1111', accepted_tasks='11/180', gate='new')
        self.r.commit('main', {SYNC: base}, 'seed SYNC', new=False)
        self.base = base

    def test_agreement_ignores_comments_in_parentheses(self):
        code, out = call('check', '--repo', str(self.r.work), '--no-fetch')
        self.assertEqual(code, 0, out)
        self.assertIn('2 agents', out)
        self.assertNotIn('CONFLICT', out)

    def test_conflict_on_another_branch_is_named_not_picked(self):
        # Check (c): Codex writes 5/180 on its own branch while the assistant's section says 11/180.
        text = self.base.replace(section('codex', '2026-10-26T09:00-07:00', 'aaaa1111', accepted_tasks='11/180', gate='new'),
                                 section('codex', '2026-10-26T11:20-07:00', 'dd49f649', accepted_tasks='5/180 (old gate)', gate='old'))
        self.r.commit('codex/vb-status', {SYNC: text}, 'codex: vb-priv status')
        self.r.run(self.r.work, 'checkout', '--quiet', 'main')
        code, out = call('check', '--repo', str(self.r.work), '--no-fetch')
        self.assertEqual(code, 1, out)
        self.assertIn('CONFLICT accepted_tasks:', out)
        self.assertIn('codex = "5/180 (old gate)"', out)
        self.assertIn('ultimate_brando9 = "11/180 (new rule 10-26-2026)"', out)
        self.assertIn('origin/codex/vb-status', out)
        self.assertIn('CONFLICT gate:', out)
        self.assertIn('do not pick one value', out)

    def test_newest_section_wins_over_an_older_branch(self):
        old = self.base.replace('accepted_tasks: 11/180\n', 'accepted_tasks: 29/180\n')
        old = old.replace('2026-10-26T09:00-07:00', '2026-10-26T08:00-07:00')
        self.r.commit('claude/old-count', {SYNC: old}, 'claude: stale count')
        code, out = call('check', '--repo', str(self.r.work), '--no-fetch', '--file', SYNC)
        self.assertEqual(code, 0, out)

    def test_bad_timestamp_is_warned(self):
        text = self.base.replace('2026-10-26T09:00-07:00', '10-26-2026 9am')
        self.r.commit('codex/bad-date', {SYNC: text}, 'codex: date')
        code, out = call('check', '--repo', str(self.r.work), '--no-fetch')
        self.assertIn('WARNING codex', out)

    def test_watch_reports_a_new_codex_push_once(self):
        # Check (a), offline: a baseline, then Codex pushes a one-line SYNC.md change on a new branch.
        state = self.root / 'state' / 'seen.json'
        url = self.r.origin.as_uri()
        code, out = call('watch', '--repo-url', url, '--state', str(state))
        self.assertIn('first watch', out)
        text = self.base.replace('accepted_tasks: 11/180\n', 'accepted_tasks: 11/180\n- doing: rerun batch 3\n')
        sha = self.r.commit('codex/sync-test', {SYNC: text}, 'codex: one-line SYNC change')
        code, out = call('watch', '--repo-url', url, '--state', str(state))
        self.assertIn(f'`codex/sync-test` @ {sha[:8]} (new branch): codex: one-line SYNC change', out)
        self.assertIn('+- doing: rerun batch 3', out)
        self.assertIn('Conflicts: none.', out)
        code, out = call('watch', '--repo-url', url, '--state', str(state))
        self.assertIn('no new commits', out)
        self.r.commit('main', {'README.md': 'repo 2\n'}, 'main moves', new=False)
        code, out = call('watch', '--repo-url', url, '--state', str(state))
        self.assertIn('no new commits', out)
        self.assertEqual(sorted(json.loads(state.read_text())[url]), ['codex/sync-test'])

    def test_ping_body_for_a_new_branch(self):
        text = self.base.replace('accepted_tasks: 11/180\n', 'accepted_tasks: 5/180\n')
        text = text.replace('2026-10-26T09:00-07:00', '2026-10-26T11:20-07:00')
        sha = self.r.commit('codex/count', {SYNC: text}, 'codex: count')
        code, out = call('ping-body', '--repo', str(self.r.work), '--repo-name', 'brando90/vb-priv-bmg',
                         '--branch', 'codex/count', '--before', agent_sync.ZERO, '--after', sha,
                         '--pusher', 'brando90', '--notify', 'brando90')
        self.assertTrue(out.startswith(f'[PUSH] brando90/vb-priv-bmg `codex/count` @ {sha[:8]} (new branch) by brando90: codex: count'), out)
        self.assertIn('1 new commit(s):', out)
        self.assertIn('-- accepted_tasks: 11/180', out)
        self.assertIn('+- accepted_tasks: 5/180', out)
        self.assertIn('CONFLICT accepted_tasks:', out)
        self.assertIn('@brando90: automatic ping', out)

    def test_ping_body_for_a_later_push(self):
        first = self.r.commit('claude/work', {'a.txt': '1\n'}, 'claude: one')
        second = self.r.commit('claude/work', {'a.txt': '2\n'}, 'claude: two', new=False)
        code, out = call('ping-body', '--repo', str(self.r.work), '--repo-name', 'x/y', '--branch', 'claude/work',
                         '--before', first, '--after', second)
        self.assertIn('1 new commit(s):', out)
        self.assertIn('claude: two', out)
        self.assertNotIn('claude: one', out)
        self.assertNotIn('SYNC.md changed', out)


if __name__ == '__main__':
    unittest.main()
