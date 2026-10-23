#!/usr/bin/env python3
"""Local Pi launch and checkpoint recovery; never starts a paid agent."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def local_command(args):
    home = Path.home()
    options = args[:args.index('--')] if '--' in args else args
    for arg in options:
        if arg.split('=')[0] in {'--provider', '--model', '--models', '--api-key',
                                '--extension', '-e', '--skill'}:
            raise ValueError(f'{arg}: edit the local profile instead of overriding its provider')
    config = home / '.local/share/pi-local'
    providers = json.loads((config / 'models.json').read_text())['providers']
    provider = providers['ollama-local']
    if provider['baseUrl'] != 'http://127.0.0.1:11434/v1':
        raise ValueError('Local profile must use http://127.0.0.1:11434/v1')
    model = provider['models'][0]['id']
    if 'cloud' in model.lower():
        raise ValueError('Cloud models are not eligible for this launcher')
    env = os.environ.copy()
    env.update(PI_CODING_AGENT_DIR=str(config), PI_OFFLINE='1',
               OLLAMA_HOST='127.0.0.1:11434', OLLAMA_NO_CLOUD='1')
    # Do not inherit provider-key variables into the local agent.
    for name in list(env):
        if name.endswith('_API_KEY'):
            del env[name]
    command = [str(home / '.local/bin/pi'), '--offline', '--no-extensions',
               '--no-mcp', '--no-prompt-templates', '--no-approve',
               '--provider', 'ollama-local', '--model', model,
               '--models', f'ollama-local/{model}', '--thinking', 'off',
               '--append-system-prompt',
               'This is a free local-only coding fallback. Use this local model for all '
               'language-model work. Do not invoke paid agents, provider services or '
               'provider keys; do not change passwords, keytabs or login state. '
               'Preserve task budgets, failed gates, and other owners\' work.', *args]
    return command, env


def main():
    mode = Path(sys.argv[0]).name
    args = sys.argv[1:]
    if mode == 'pi-local':
        command, env = local_command(args)
        os.execve(command[0], command, env)
    parser = argparse.ArgumentParser(description=(
        'Continue a saved task with local Pi after the previous writer has stopped. '
        'This starts a new checkpoint-based session, not a native Codex/Claude resume.'))
    parser.add_argument('checkpoint', type=Path)
    parser.add_argument('--error-log', type=Path,
                        help='Optional quota-error evidence; required for pi-resilient')
    parser.add_argument('--previous-pid', type=int,
                        help='Refuse takeover if this previous writer process is still alive')
    parser.add_argument('--print', '-p', action='store_true', help='Run noninteractively')
    options = parser.parse_args(args)
    if options.previous_pid is not None:
        if options.previous_pid <= 0:
            raise ValueError('previous-pid must be a positive process ID')
        try:
            os.kill(options.previous_pid, 0)
        except ProcessLookupError:
            pass
        else:
            raise ValueError('Previous writer is still alive; preserve it and resolve ownership first')
    checkpoint = options.checkpoint.expanduser().resolve(strict=True)
    content = checkpoint.read_text()
    if not content.strip():
        raise ValueError('Checkpoint is empty')
    if mode == 'pi-resilient':
        if options.error_log is None:
            raise ValueError('pi-resilient requires --error-log with saved quota evidence')
        evidence = options.error_log.read_text()
        if not re.search(r'quota|usage limit|rate.limit|credit|capacity|429|context.{0,20}(limit|exceed)', evidence, re.I):
            raise ValueError('No recognized quota/context limit in the supplied log; use pi-takeover for other handoffs')
    root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
    identity = hashlib.sha256(root.encode()).hexdigest()[:16]
    state = Path.home() / '.local/state/pi-local' / identity
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (state / 'recovery.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        receipt = {'mode': mode, 'repository': root, 'checkpoint': str(checkpoint),
                   'checkpoint_sha256': hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                   'started_at': time.time(), 'status': 'running'}
        receipt_path = state / f'recovery-{time.time_ns()}.json'
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        prompt = ('Continue this saved task in the current repository. Inspect the existing diff '
                  'and checkpoint before editing; preserve other owners\' work, completed results, '
                  'task limits and failed gates. Use the local model only; do not call paid agents '
                  'or change authentication. Run the requested deterministic checks and record '
                  'remaining work accurately.\n\nSaved checkpoint:\n' + content +
                  '\n\nTL;DR: Continue the saved task using local Pi and verify the result.')
        command, env = local_command((['--print'] if options.print else []) + ['--', prompt])
        try:
            code = subprocess.call(command, env=env)
        except BaseException:
            receipt.update(status='interrupted', finished_at=time.time())
            receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
            raise
        receipt.update(status='agent_exited', exit_code=code, finished_at=time.time())
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        print(f'Recovery receipt: {receipt_path}; independently verify the task result.', file=sys.stderr)
        return code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(f'{Path(sys.argv[0]).name}: {error}', file=sys.stderr)
        sys.exit(2)
