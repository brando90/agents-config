#!/usr/bin/env python3
"""Verify the Pi ACP model menu and selection without sending any model prompt."""
import argparse
import collections
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adapter', type=Path, required=True, help='Installed pi-acp dist/index.js')
    args = parser.parse_args()
    settings = json.loads((Path.home()/'Library/Application Support/Devin/User/settings.json').read_text())
    env = dict(os.environ)
    env.update(settings.get('devin.acp.agentEnv', {}).get('pi-acp', {}))
    # No prompts are sent and no model generation is performed.
    process = subprocess.Popen(['node', str(args.adapter)], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               env=env, start_new_session=True)
    pending = b''
    def request(identifier, method, params):
        nonlocal pending
        process.stdin.write((json.dumps({'jsonrpc': '2.0', 'id': identifier,
                                         'method': method, 'params': params})+'\n').encode())
        process.stdin.flush()
        deadline = time.monotonic()+60
        while time.monotonic() < deadline:
            if b'\n' not in pending:
                if not select.select([process.stdout], [], [], 1)[0]:
                    continue
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError('Adapter exited')
                pending += chunk
            while b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                try:
                    response = json.loads(line)
                except ValueError:
                    continue
                if response.get('id') != identifier:
                    continue
                if 'error' in response:
                    # Do not dump arbitrary error payloads that might contain credentials.
                    raise RuntimeError(f'{method}: protocol error code {response["error"].get("code")}')
                return response['result']
        raise TimeoutError(method)
    try:
        request(1, 'initialize', {'protocolVersion': 1, 'clientCapabilities': {},
                                 'clientInfo': {'name': 'named-provider-check', 'version': '1'}})
        result = request(2, 'session/new', {'cwd': str(Path.home()), 'mcpServers': []})
        models = result.get('models', {}).get('availableModels', [])
        if not models:
            for option in result.get('configOptions', []):
                if option.get('category') == 'model':
                    models = [{'modelId': o['value'], 'name': o.get('name', '')}
                              for o in option.get('options', [])]
        counts = collections.Counter(m['modelId'].split('/',1)[0] for m in models)
        manifest = json.loads(Path(__file__).with_name('providers.json').read_text())
        for entry in manifest['providers']:
            name = entry['id']
            assert counts[name] > 0, f'Missing provider: {name}'
            print(f'{name}: {counts[name]} models advertised over ACP')
        target = 'personal-openai-brando/gpt-5.6-sol'
        assert any(m['modelId'] == target for m in models)
        model_option = next(o for o in result['configOptions'] if o.get('category') == 'model')
        request(3, 'session/set_config_option', {'sessionId': result['sessionId'],
                                               'configId': model_option['id'], 'value': target})
        print(f'ACP selection accepted: {target}')
        print('PASS; no session/prompt sent, no paid inference')
    finally:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=10)


if __name__ == '__main__':
    main()
