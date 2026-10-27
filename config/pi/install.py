#!/usr/bin/env python3
"""Sync Pi runtime configuration and named providers; --check reports runtime drift."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

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


def configure_devin(settings_path, pi_command, agent_dir):
    """Point Devin's existing pi-acp connector at the same Pi/profile as the CLI."""
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    settings.setdefault('devin.acp.agentEnv', {}).setdefault('pi-acp', {}).update({
        'PI_ACP_PI_COMMAND': str(pi_command),
        'PI_CODING_AGENT_DIR': str(agent_dir),
        'PI_OFFLINE': '1',
    })
    settings.setdefault('devin.acp.enabledAgents', {})['pi-acp'] = True
    if settings_path.exists():
        backup = settings_path.with_name('settings.json.before-pi-providers-' + datetime.now().strftime('%m-%d-%Y-%H%M%S-%f'))
        shutil.copy2(settings_path, backup)
        backup.chmod(0o600)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2)+'\n')
    print('Devin Desktop: pi-acp linked to the named-provider Pi profile.')


def find_catalog():
    # Follow the selected Pi executable before consulting npm, which may belong
    # to a different Node installation on this host.
    executable = shutil.which('pi')
    if executable:
        launcher = Path(executable).resolve()
        # Managed Pi installs use a shell launcher, not a symlink to the package.
        # Resolve its selected release before falling back to a global npm install.
        managed_root = launcher.parent.parent/'install'
        version_file = managed_root/'current-version'
        if version_file.is_file():
            version = version_file.read_text().strip()
            if not version or version in ('.', '..') or any(
                    c not in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._+-'
                    for c in version):
                raise ValueError('Invalid managed Pi release version')
            candidate = managed_root/'releases'/version/'node_modules/@earendil-works/pi-ai/dist/providers/data'
            if (candidate/'openai.json').is_file():
                return candidate
        for parent in launcher.parents:
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
    parser.add_argument('--check', action='store_true', help='Read-only runtime drift check; exit 1 for differences')
    parser.add_argument('--runtime-only', action='store_true', help='Sync settings/resources without changing model providers')
    parser.add_argument('--adopt-skill-copies', action='store_true', help='Back up existing client skill copies and replace them with canonical links')
    parser.add_argument('--runtime-manifest', type=Path, default=ROOT/'runtime.json')
    parser.add_argument('--host-config', type=Path, default=os.environ.get('PI_SYNC_HOST_CONFIG'), help='Optional explicit machine/profile overrides')
    parser.add_argument('--devin-desktop', action='store_true', help='Also configure the existing Devin Desktop pi-acp connector (macOS)')
    args = parser.parse_args()
    if (args.check or args.runtime_only) and args.devin_desktop:
        parser.error('--check/--runtime-only cannot be combined with --devin-desktop')
    from sync_runtime import sync, load_plan, package_source
    plan = load_plan(args.runtime_manifest, args.agent_dir.expanduser().resolve(), args.host_config)
    account_package = str(ROOT/'claude-accounts')
    if not args.check and any(package_source(p) == account_package for p in plan['settings']['packages']):
        # Local Pi packages do not install their own dependencies. Prepare the
        # pinned transport and host-specific launchers before advancing sync state.
        subprocess.run([sys.executable, str(ROOT/'claude-accounts/install.py'),
                        '--agent-dir', str(args.agent_dir.expanduser().resolve())], check=True)
    status = sync(args.runtime_manifest, args.agent_dir, check=args.check,
                  host_config=args.host_config, adopt_skills=args.adopt_skill_copies)
    if args.check or args.runtime_only:
        return status
    catalog_dir = args.catalog_dir.expanduser() if args.catalog_dir else find_catalog()
    install(json.loads((ROOT/'providers.json').read_text()), catalog_dir,
            args.keys_dir.expanduser(), args.agent_dir.expanduser())
    if args.devin_desktop:
        pi = shutil.which('pi')
        if not pi:
            raise ValueError('Pi executable is not on PATH')
        configure_devin(Path.home()/'Library/Application Support/Devin/User/settings.json',
                        Path(pi), args.agent_dir.expanduser().resolve())
    return status


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.SubprocessError):
        print('Pi setup failed: invalid configuration, missing dependency, or failed package operation. No secret values displayed.', file=sys.stderr)
        sys.exit(2)
