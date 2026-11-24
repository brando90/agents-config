#!/usr/bin/env python3
"""Check the Vals Codex account and reserve, then serialize a native job (2026-11-24).

Needs the native Codex CLI and its host-specific Vals sign-in, never an API key.
Examples: vals-codex.py --check; vals-codex.py -- codex exec --model gpt-6-astra ...
"""
import argparse
import datetime as dt
import fcntl
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time


def validate(account, result, now):
    if not isinstance(account, dict) or account.get('type') != 'chatgpt' or account.get('email') != 'brando@vals.ai' or account.get('planType') != 'pro':
        raise ValueError('Expected brando@vals.ai on ChatGPT Pro')
    rates = result['rateLimitsByLimitId']['codex']
    if not result.get('ordinaryUsageAllowed', True) or rates.get('rateLimitReachedType') or result.get('spendControlReached'):
        raise ValueError('Ordinary included usage unavailable')
    credits = rates.get('credits')
    if not isinstance(credits, dict) or credits.get('hasCredits') is not False or credits.get('unlimited') is not False:
        raise ValueError('Cannot rule out usage credits')
    usage = {}
    for window in ('primary', 'secondary'):
        row = rates.get(window)
        if row is None:
            continue
        value = row['usedPercent']
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value < 80 or row['resetsAt'] <= now:
            raise ValueError('Quota reserve reached or reading requires refresh')
        usage[window] = row
    if not usage or not any(row.get('windowDurationMins') == 10080 for row in usage.values()):
        raise ValueError('Fresh weekly allowance is required')
    return {'loggedIn': True, 'account': account, 'usage': usage, 'credits': credits}


def read_account(env):
    p = subprocess.Popen(['codex', 'app-server', '--stdio'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, env=env, start_new_session=True)
    replies, pending = {}, b''
    def send(v):
        p.stdin.write((json.dumps(v) + '\n').encode())
        p.stdin.flush()
    try:
        send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'vals_plan_reserve', 'version': '1.0'}}})
        with selectors.DefaultSelector() as selector:
            selector.register(p.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 14
            while time.monotonic() < deadline and len(replies) < 2:
                if not selector.select(.2):
                    continue
                chunk = os.read(p.stdout.fileno(), 65536)
                if not chunk:
                    break
                pending += chunk
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    v = json.loads(line)
                    if v.get('id') == 1:
                        if 'error' in v:
                            raise ValueError('Native initialization failed')
                        send({'method': 'initialized', 'params': {}})
                        send({'id': 2, 'method': 'account/read', 'params': {'refreshToken': False}})
                        send({'id': 3, 'method': 'account/rateLimits/read', 'params': {}})
                    if v.get('id') in (2, 3):
                        replies[v['id']] = v
        return validate(replies[2]['result']['account'], replies[3]['result'], time.time())
    finally:
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        p.wait(timeout=3)


def health_check(command, env):
    """A cached account row can outlive revocation; demand a real reply."""
    model = command[command.index('--model') + 1]
    probe = ['codex', '--ask-for-approval', 'never', 'exec', '--json',
             '--skip-git-repo-check', '--sandbox', 'read-only', '--model', model,
             '--ignore-user-config', '-c', 'forced_login_method=chatgpt', '-']
    p = subprocess.run(probe, input='Reply exactly OK. Do not use tools.\n',
                       env=env, capture_output=True, text=True, timeout=60)
    replies = []
    for line in p.stdout.splitlines():
        value = json.loads(line)
        if value.get('type') == 'item.completed' and value.get('item', {}).get('type') == 'agent_message':
            replies.append(value['item']['text'].strip())
    if p.returncode != 0 or replies != ['OK']:
        raise ValueError('Vals Codex real-request sign-in check failed')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('command', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    env = dict(os.environ, CODEX_HOME=str(Path.home() / '.codex-vals-skampere1'))
    for name in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_ORG_ID', 'OPENAI_PROJECT_ID', 'CODEX_ACCESS_TOKEN'):
        env.pop(name, None)
    folder = Path.home() / '.local/state/plan-router'
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (folder / 'vals-codex.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Vals Codex profile already in use')
        data = read_account(env)
        data['observed_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (folder / 'vals-codex-reserve.json').write_text(json.dumps(data, indent=2) + '\n')
        if a.check:
            print('Logged in using ChatGPT; fresh Vals included-usage reserve passed')
            print(json.dumps(data))
            return 0
        command = a.command[1:] if a.command[:1] == ['--'] else a.command
        if not command or command[0] != 'codex':
            raise ValueError('Expected native codex command')
        health_check(command, env)
        data = read_account(env)
        data['observed_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (folder / 'vals-codex-reserve.json').write_text(json.dumps(data, indent=2) + '\n')
        return subprocess.run(command, env=env, pass_fds=(lock.fileno(),)).returncode


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, IndexError, OSError, subprocess.SubprocessError):
        print('Vals Codex account/quota check blocked; inspect current sign-in and reserve', file=sys.stderr)
        raise SystemExit(1)
