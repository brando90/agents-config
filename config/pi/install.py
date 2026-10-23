#!/usr/bin/env python3
"""Install named Pi providers. Reads catalogs and key metadata, never key contents."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def build_providers(manifest, catalog_dir, keys_dir):
    result, notices = {}, []
    for entry in manifest['providers']:
        key = keys_dir / entry['keyFile']
        if not key.is_file():
            notices.append(f"{entry['id']}: missing key file (skipped)")
            continue
        if key.stat().st_mode & 0o077:
            raise ValueError(f'Credential file must be private (chmod 600): {key}')
        catalog = json.loads((catalog_dir / (entry['provider'] + '.json')).read_text())
        models = [dict(m) for group in catalog.values() for m in group.values()
                  if m.get('type', 'chat') == 'chat']
        wanted = entry.get('models')
        if wanted:
            missing = set(wanted) - {m['id'] for m in models}
            if missing:
                raise ValueError(f"{entry['id']}: models missing from Pi catalog: {sorted(missing)}")
            models = [m for m in models if m['id'] in wanted]
        if not models:
            raise ValueError(f"{entry['id']}: no chat models")
        for m in models:
            m.pop('provider', None)
            m.pop('type', None)
            # Include sponsor and key nickname even if Pi displays the model name only.
            m['name'] = f"{m['name']} [{entry['id']}]"
        result[entry['id']] = {
            'name': entry['id'],
            'baseUrl': models[0]['baseUrl'],
            'api': models[0]['api'],
            'apiKey': '!cat ' + shlex.quote(str(key)),
            'models': models,
        }
    return result, notices


def install(manifest, catalog_dir, keys_dir, agent_dir):
    providers, notices = build_providers(manifest, catalog_dir, keys_dir)
    agent_dir.mkdir(parents=True, exist_ok=True)
    target = agent_dir / 'models.json'
    previous = json.loads(target.read_text()) if target.exists() else {}
    # Add/update only manifest-owned provider IDs; preserve unrelated providers/settings.
    previous.setdefault('providers', {}).update(providers)
    if target.exists():
        backup = target.with_name('models.json.before-named-' + datetime.now().strftime('%m-%d-%Y-%H%M%S-%f'))
        shutil.copy2(target, backup)
        backup.chmod(0o600)
    temporary = target.with_suffix('.json.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(previous, stream, indent=2)
        stream.write('\n')
    temporary.chmod(0o600)
    temporary.replace(target)
    for name, provider in providers.items():
        print(f"{name}: {len(provider['models'])} catalog models configured (access untested)")
    for notice in notices:
        print(notice)
    print(f'Installed: {target}; open /model or restart Pi.')


def find_catalog():
    # Follow the selected Pi executable before consulting npm, which may belong
    # to a different Node installation on this host.
    executable = shutil.which('pi')
    if executable:
        for parent in Path(executable).resolve().parents:
            candidate = parent/'node_modules/@earendil-works/pi-ai/dist/providers/data'
            if (candidate/'openai.json').is_file():
                return candidate
    npm_root = subprocess.check_output(['npm', 'root', '-g'], text=True).strip()
    candidate = Path(npm_root)/'@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/providers/data'
    if not (candidate/'openai.json').is_file():
        raise ValueError('Cannot locate installed Pi catalog; provide --catalog-dir')
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent-dir', type=Path, default=Path.home()/'.pi/agent')
    parser.add_argument('--keys-dir', type=Path, default=Path.home()/'keys')
    parser.add_argument('--catalog-dir', type=Path)
    args = parser.parse_args()
    catalog_dir = args.catalog_dir.expanduser() if args.catalog_dir else find_catalog()
    install(json.loads((ROOT/'providers.json').read_text()), catalog_dir,
            args.keys_dir.expanduser(), args.agent_dir.expanduser())


if __name__ == '__main__':
    main()
