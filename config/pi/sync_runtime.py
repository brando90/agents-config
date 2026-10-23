"""Reconcile portable Pi configuration without reading credentials or calling models."""
import copy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

RESOURCE_KEYS = ('packages', 'extensions', 'skills', 'prompts', 'themes')
STATE = 'agents-config-sync.json'


def read_json(path):
    value = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(value, dict):
        raise ValueError('Configuration files must contain JSON objects')
    return value


def write_json(path, value):
    """Atomic private write, with backup only when content changes."""
    if path.exists() and read_json(path) == value:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_name(path.name + '.before-sync-' + datetime.now().strftime('%m-%d-%Y-%H%M%S-%f'))
        shutil.copy2(path, backup)
        backup.chmod(0o600)
    fd, temporary = tempfile.mkstemp(prefix='.pi-sync-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def merge(base, overlay):
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def leaves(value, prefix=()):
    for key, child in value.items():
        if isinstance(child, dict) and child:
            yield from leaves(child, prefix + (key,))
        else:
            yield prefix + (key,), child


def lookup(value, path):
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def remove_leaf(value, path):
    parent = value
    for key in path[:-1]:
        if not isinstance(parent, dict):
            return
        parent = parent.get(key)
    if isinstance(parent, dict):
        parent.pop(path[-1], None)


def expand(value, config_dir, agent_dir):
    if isinstance(value, str):
        return value.replace('${CONFIG_DIR}', str(config_dir)).replace('${AGENT_DIR}', str(agent_dir)).replace('${HOME}', str(Path.home()))
    if isinstance(value, list):
        return [expand(v, config_dir, agent_dir) for v in value]
    if isinstance(value, dict):
        return {k: expand(v, config_dir, agent_dir) for k, v in value.items()}
    return value


def package_source(entry):
    source = entry if isinstance(entry, str) else entry.get('source') if isinstance(entry, dict) else None
    if not isinstance(source, str):
        raise ValueError('Each package requires a string source')
    return source


def package_location(source, agent_dir):
    """Deliberately accept immutable npm versions/git commits, or absolute local paths."""
    npm = re.fullmatch(r'npm:((?:@[\w.-]+/)?[\w.-]+)@(\d+\.\d+\.\d+(?:-[\w.-]+)?)', source)
    if npm:
        return 'npm', agent_dir/'npm/node_modules'/npm[1], npm[2]
    git = re.fullmatch(r'git:([\w.-]+)/([\w./-]+)@([a-fA-F0-9]{40})', source)
    if git and '..' not in git[2].split('/'):
        return 'git', agent_dir/'git'/git[1]/git[2].removesuffix('.git'), git[3].lower()
    if Path(source).is_absolute():
        return 'local', Path(source), None
    raise ValueError('Packages must use exact npm versions, full git commit hashes, or ${CONFIG_DIR} local paths')


def package_problem(source, agent_dir):
    kind, path, version = package_location(source, agent_dir)
    if not path.exists():
        return 'missing installation'
    if kind == 'npm' and read_json(path/'package.json').get('version') != version:
        return 'installed version differs'
    if kind == 'git':
        head = subprocess.run(['git', '-C', str(path), 'rev-parse', 'HEAD'], capture_output=True, text=True)
        dirty = subprocess.run(['git', '-C', str(path), 'status', '--porcelain'], capture_output=True, text=True)
        if dirty.returncode or dirty.stdout.strip():
            return 'installed checkout has local changes'
        if head.returncode or head.stdout.strip().lower() != version:
            return 'installed commit differs'
    return None


def load_plan(manifest_path, agent_dir, host_config=None):
    manifest = read_json(manifest_path)
    if manifest.get('version') != 1:
        raise ValueError('Runtime manifest requires version 1')
    if host_config:
        host_config = host_config.expanduser()
        if not host_config.is_file():
            raise ValueError('Host override file is missing')
        manifest = merge(manifest, read_json(host_config))
    manifest = expand(manifest, manifest_path.parent.resolve(), agent_dir)
    settings = manifest.setdefault('settings', {})
    if not isinstance(settings, dict):
        raise ValueError('settings must be an object')
    for key in ('trackedFiles', 'externalExtensions'):
        entries = manifest.get(key, [])
        if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
            raise ValueError(f'{key} must be an array of strings')
    for key in RESOURCE_KEYS:
        entries = settings.setdefault(key, [])
        if not isinstance(entries, list):
            raise ValueError(f'{key} must be an array')
        if key != 'packages' and not all(isinstance(e, str) for e in entries):
            raise ValueError(f'{key} entries must be strings')
    for entry in settings['packages']:
        package_location(package_source(entry), agent_dir)
    return manifest


def fingerprint(manifest, manifest_path):
    """Hash declared shared files, so editing source also requires an apply receipt."""
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode())
    for relative in manifest.get('trackedFiles', []):
        path = (manifest_path.parent/relative).resolve()
        if not path.is_relative_to(manifest_path.parent.resolve()) or not path.is_file():
            raise ValueError('trackedFiles must name existing files under config/pi')
        digest.update(relative.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def inspect(manifest, manifest_path, agent_dir):
    expected = manifest['settings']
    actual = read_json(agent_dir/'settings.json')
    state = read_json(agent_dir/STATE)
    drift, notes = [], []
    for path, desired in leaves(expected):
        if lookup(actual, path) != desired:
            drift.append('settings.' + '.'.join(path) + ': differs or missing')
    for path, old in leaves(state.get('settings', {})):
        if lookup(expected, path) is None and lookup(actual, path) is not None:
            drift.append('settings.' + '.'.join(path) + ': no longer managed; apply to retire unchanged value')
    for entry in expected['packages']:
        issue = package_problem(package_source(entry), agent_dir)
        if issue:
            drift.append('package ' + package_source(entry) + ': ' + issue)
    for key in RESOURCE_KEYS[1:]:
        for entry in expected[key]:
            if entry.startswith(('builtin:', '-builtin:', '+builtin:', '!','-')) or any(c in entry for c in '*?['):
                continue
            path = Path(entry.lstrip('+')).expanduser()
            if not path.is_absolute():
                path = agent_dir/path
            if not path.exists():
                drift.append(key + ': declared path missing: ' + str(path))
    allowed = set(manifest.get('externalExtensions', []))
    extension_dir = agent_dir/'extensions'
    if extension_dir.is_dir():
        for path in sorted(extension_dir.iterdir()):
            if path.name.startswith('.'):
                continue
            if path.name in allowed:
                notes.append('externally managed extension: ' + path.name)
            else:
                drift.append('local-only extension: ' + path.name + ' (move into shared config or declare external)')
    if state.get('fingerprint') != fingerprint(manifest, manifest_path):
        drift.append('shared manifest/source changed or has not been applied')
    for key in sorted(set(actual) - set(expected)):
        notes.append('local setting preserved: ' + key)
    return drift, notes


def sync(manifest_path, agent_dir, check=False, host_config=None, pi_command='pi'):
    agent_dir = agent_dir.expanduser().resolve()
    manifest_path = manifest_path.expanduser().resolve()
    manifest = load_plan(manifest_path, agent_dir, host_config)
    desired = manifest['settings']
    digest = fingerprint(manifest, manifest_path)  # validate before any mutation
    if not check:
        for entry in desired['packages']:
            if package_problem(package_source(entry), agent_dir) == 'installed checkout has local changes':
                raise ValueError('Managed Git package has local edits; preserve them before reinstalling')
        actual = read_json(agent_dir/'settings.json')
        prior = read_json(agent_dir/STATE).get('settings', {})
        for path, old in leaves(prior):
            if lookup(desired, path) is None and lookup(actual, path) == old:
                remove_leaf(actual, path)
        updated = merge(actual, desired)
        write_json(agent_dir/'settings.json', updated)
        # Use an empty cwd, so project package declarations cannot affect installation.
        with tempfile.TemporaryDirectory(prefix='pi-sync-') as cwd:
            for entry in desired['packages']:
                source = package_source(entry)
                if package_problem(source, agent_dir):
                    if package_location(source, agent_dir)[0] == 'local':
                        raise ValueError('Local package path is missing; restore its source first')
                    env = dict(os.environ, PI_CODING_AGENT_DIR=str(agent_dir))
                    result = subprocess.run([pi_command, 'install', source], cwd=cwd, env=env,
                                            capture_output=True, text=True, timeout=180)
                    if result.returncode or package_problem(source, agent_dir):
                        raise ValueError('Package installation failed; sync receipt was not updated')
        # pi install may normalize package declarations; restore the requested filters.
        write_json(agent_dir/'settings.json', merge(read_json(agent_dir/'settings.json'), desired))
        write_json(agent_dir/STATE, {'fingerprint': digest, 'settings': desired})
    drift, notes = inspect(manifest, manifest_path, agent_dir)
    print('Pi profile: ' + str(agent_dir))
    print('Manifest: ' + str(manifest_path))
    print('Managed resources: ' + ', '.join(f'{key}={len(desired[key])}' for key in RESOURCE_KEYS))
    for item in drift:
        print('DRIFT: ' + item)
    for item in notes:
        print('INFO: ' + item)
    print('OUT OF SYNC' if drift else 'IN SYNC (files and declared package versions)')
    print('Running sessions/project overrides are separate; use /reload or restart after applying.')
    return 1 if drift else 0
