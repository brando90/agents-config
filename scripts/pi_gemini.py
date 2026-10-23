#!/usr/bin/env python3
"""Launch Pi for VeriBench using Allen's existing Gemini credential at runtime."""
import os
from pathlib import Path
import re
import sys


def gemini_command(args):
    home = Path.home()
    options = args[:args.index('--')] if '--' in args else args
    for arg in options:
        if arg.split('=')[0] in {'--provider', '--model', '--models', '--api-key',
                                '--extension', '-e'}:
            raise ValueError('Use PI_GEMINI_MODEL to select a Gemini model; provider and credential are fixed')
    model = os.environ.get('PI_GEMINI_MODEL', 'gemini-3-flash-preview')
    if not re.fullmatch(r'gemini-[A-Za-z0-9._-]+', model):
        raise ValueError('PI_GEMINI_MODEL must be a Gemini model ID, without a provider prefix')
    key_path = home / 'keys/gemini_allen_key.txt'
    key = key_path.read_text().strip()
    if not key or any(c.isspace() for c in key):
        raise ValueError('Gemini key file must contain one nonempty credential; contents not displayed')
    env = {k: v for k, v in os.environ.items() if not k.endswith('_API_KEY')}
    env.update(GEMINI_API_KEY=key, PI_CODING_AGENT_DIR=str(home / '.local/share/pi-gemini'),
               PI_OFFLINE='1')
    command = [str(home / '.local/bin/pi'), '--offline', '--no-extensions',
               '--no-mcp', '--no-prompt-templates', '--no-approve',
               '--provider', 'google', '--model', model, '--models', f'google/{model}',
               '--thinking', 'minimal', '--append-system-prompt',
               'This Pi session is for authorized VeriBench work using the existing Gemini key. '
               'Preserve task budgets, scientific model pins, failed gates, and other owners\' work. '
               'Do not disclose credentials or change billing settings.']
    integration = home / '.pi/agent/extensions/herdr-agent-state.ts'
    if integration.is_file():
        command += ['--extension', str(integration)]
    return command + args, env


def main():
    command, env = gemini_command(sys.argv[1:])
    os.execve(command[0], command, env)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        print(f'pi-gemini: {error}', file=sys.stderr)
        sys.exit(2)
