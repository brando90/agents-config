#!/usr/bin/env python3
"""Bounded optional live smoke. Defaults to deterministic model-list verification."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('installer', ROOT/'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def run(cmd, **kwargs):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         start_new_session=True, **kwargs)
    try:
        out, err = p.communicate(timeout=100)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGTERM)
        try:
            p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
        raise RuntimeError('100-second verification timeout; owned process group stopped')
    return p.returncode, out, err


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true', help='Use existing subscription quota: three short text tests, then one two-request Pi tool test; no retries')
    parser.add_argument('--account', choices=['personal', 'vals', 'stanford'])
    parser.add_argument('--tool-only', action='store_true', help='Run just the Pi tool round trip on --account')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='pi-claude-accounts-') as td:
        root = Path(td); agent = root/'agent'; work = root/'work'; work.mkdir()
        import shutil
        installer.install(agent, shutil.which('claude'), sys.executable)
        settings = json.loads((agent/'settings.json').read_text())
        settings.update(retry={'enabled': False}, compaction={'enabled': False})
        (agent/'settings.json').write_text(json.dumps(settings))
        env = dict(os.environ, PI_CODING_AGENT_DIR=str(agent))
        code, out, err = run(['pi', '--offline', '--no-mcp', '--list-models', 'claude-code'], env=env, cwd=work)
        if code: raise RuntimeError(err)
        for account in ['personal', 'vals', 'stanford']:
            assert f'{account}-claude-code' in out
        print('PASS: 3 providers registered, models discoverable')
        if not args.live: return
        # Expected text under 100 output tokens per call. At most five model
        # requests in normal execution, using Haiku; no API keys/billing changes.
        common = ['pi', '--offline', '--no-mcp', '--no-skills', '--no-prompt-templates', '--no-context-files', '--no-session', '--mode', 'json', '--thinking', 'off', '--system-prompt', 'This is an integration test. Follow the request exactly.']
        guard = root/'limit.ts'
        guard.write_text('export default function(pi) { let n = 0; pi.on("before_provider_request", () => { if (++n > 3) throw new Error("Verification request cap reached"); }); }')
        common += ['--extension', str(guard)]
        for account in ([] if args.tool_only else ([args.account] if args.account else ['personal', 'vals', 'stanford'])):
            code, out, err = run(common + ['--no-tools', '--model', f'{account}-claude-code/claude-haiku-4-5', '-p', 'Reply with exactly ACCOUNT_OK'], env=env, cwd=work)
            events = [json.loads(line) for line in out.splitlines() if line.startswith('{')]
            messages = [e['message'] for e in events if e.get('type') == 'message_end' and e.get('message', {}).get('role') == 'assistant']
            if code or not messages or messages[-1].get('stopReason') == 'error':
                raise RuntimeError(f'{account}: {err or (messages[-1].get("errorMessage") if messages else "no assistant message")}')
            assert 'ACCOUNT_OK' in json.dumps(messages[-1]['content'])
            print(f'PASS: {account} response via actual CLI')
        if args.account and not args.tool_only: return
        (work/'probe.txt').write_text('PI_TOOL_BRIDGE_OK_7139')
        tool_account = args.account or 'personal'
        code, out, err = run(common + ['--tools', 'read', '--model', f'{tool_account}-claude-code/claude-haiku-4-5', '-p', 'Use the read tool once to read probe.txt. Then reply with exactly its contents.'], env=env, cwd=work)
        if code: raise RuntimeError(err or 'Pi tool test failed')
        events = [json.loads(line) for line in out.splitlines() if line.startswith('{')]
        assert any(e.get('type') == 'tool_execution_end' and e.get('toolName') == 'read' and not e.get('isError') for e in events), 'No successful Pi read tool event'
        assert 'PI_TOOL_BRIDGE_OK_7139' in out
        print('PASS: Pi-owned read tool round trip')


if __name__ == '__main__':
    main()
