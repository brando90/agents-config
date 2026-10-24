#!/usr/bin/env python3
"""Verify Pi advertises canonical skills through RPC without a model request."""
import argparse
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import tempfile
import time
from sync_runtime import load_plan, skill_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent-dir', type=Path, default=Path.home()/'.pi/agent')
    parser.add_argument('--pi', default=shutil.which('pi'))
    args = parser.parse_args()
    if not args.pi:
        parser.error('Pi is not on PATH')
    profile = args.agent_dir.expanduser().resolve()
    host = os.environ.get('PI_SYNC_HOST_CONFIG')
    plan = load_plan(Path(__file__).with_name('runtime.json'), profile, Path(host) if host else None)
    expected = {'skill:' + name for name in skill_sources(plan)}
    with tempfile.TemporaryDirectory(prefix='pi-skills-probe-') as cwd:
        process = subprocess.Popen([args.pi, '--offline', '--no-extensions', '--no-mcp',
                                    '--no-session', '--mode', 'rpc'], cwd=cwd,
                                   env=dict(os.environ, PI_CODING_AGENT_DIR=str(profile)),
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True)
        selector = selectors.DefaultSelector()
        try:
            process.stdin.write(json.dumps({'id': 'verify-skills', 'type': 'get_commands'}) + '\n')
            process.stdin.flush()
            selector.register(process.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if not selector.select(timeout=1):
                    continue
                line = process.stdout.readline()
                if not line:
                    break
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get('id') != 'verify-skills':
                    continue
                commands = {c['name'] for c in event.get('data', {}).get('commands', [])}
                matched = expected & commands
                passed = bool(event.get('success')) and matched == expected and bool(expected)
                print(json.dumps({'passed': passed, 'expected_skills': len(expected),
                                  'loaded_skills': len(matched), 'model_requests': 0}))
                return 0 if passed else 1
            print('Pi command-discovery probe failed or timed out; no model request was sent.')
            return 2
        finally:
            selector.close()
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    raise SystemExit(main())
