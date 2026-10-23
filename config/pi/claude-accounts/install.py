#!/usr/bin/env python3
"""Install the local Pi package and per-account launchers; never copy login tokens."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def save(path, content):
    if path.exists() and path.read_text() == content:
        return
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + '.before-' + datetime.now().strftime('%m-%d-%Y-%H%M%S-%f')))
    path.write_text(content)
    path.chmod(0o600)


def install(agent_dir, claude, python):
    agent_dir.mkdir(parents=True, exist_ok=True)
    bins = agent_dir / 'claude-account-bin'
    bins.mkdir(mode=0o700, exist_ok=True)
    accounts = json.loads((ROOT / 'accounts.json').read_text())
    for account, plan in zip(accounts, ['max', 'team', 'enterprise']):
        target = bins / account['id']
        command = [python, str(ROOT / 'launch.py'), account['id'], claude]
        save(target, '#!/bin/sh\nexec ' + ' '.join(shlex.quote(arg) for arg in command) + ' "$@"\n')
        target.chmod(0o700)
        account['executable'] = str(target)
        account['subscriptionType'] = plan
    save(agent_dir / 'claude-accounts.json', json.dumps({'claude': claude, 'accounts': accounts}, indent=2) + '\n')
    settings_path = agent_dir / 'settings.json'
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    packages = settings.setdefault('packages', [])
    if not any((p if isinstance(p, str) else p.get('source')) == str(ROOT) for p in packages):
        packages.append(str(ROOT))
    save(settings_path, json.dumps(settings, indent=2) + '\n')
    return accounts


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--agent-dir', type=Path, default=Path.home()/'.pi/agent')
    p.add_argument('--claude', default=shutil.which('claude'))
    p.add_argument('--skip-deps', action='store_true')
    args = p.parse_args()
    if not args.claude:
        p.error('claude executable not found')
    if not args.skip_deps:
        subprocess.run(['npm', 'ci', '--ignore-scripts', '--omit=peer', '--no-audit', '--no-fund'], cwd=ROOT, check=True)
    from patch_dependency import apply
    apply()
    accounts = install(args.agent_dir.expanduser().resolve(), str(Path(args.claude).absolute()), sys.executable)
    for account in accounts:
        result = subprocess.run([account['executable'], 'auth', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
        print(account['id'] + ': ' + ('identity verified' if result.returncode == 0 else 'LOGIN REQUIRED (route installed, no fallback)'))
    print('Installed. In Pi: /reload, then /claude-accounts and /model. Current/default model unchanged.')
