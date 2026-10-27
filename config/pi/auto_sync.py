#!/usr/bin/env python3
"""Private, three-way Pi synchronization. No model calls or automatic Git publication."""
import argparse
import base64
import contextlib
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time

import sync_runtime as runtime

# Portable Pi 1.4 settings. Machine identity, credentials, proxy/session/shell paths
# and extension-specific unknown fields stay on the host.
SETTING_KEYS = set('''defaultProvider defaultModel defaultThinkingLevel modelThinkingLevels
transport sessionShareDestination steeringMode followUpMode theme compaction branchSummary
retry hideThinkingBlock showCacheMissNotices quietStartup defaultProjectTrust collapseChangelog
enableInstallTelemetry enableAnalytics packages extensions skills prompts themes enableSkillCommands
terminal images enabledModels defaultTools doubleEscapeAction treeFilterMode thinkingBudgets
editorPaddingX outputPad autocompleteMaxVisible showHardwareCursor markdown warnings codemode
httpIdleTimeoutMs cacheWarming websocketConnectTimeoutMs'''.split())
ROOTS = ('skills', 'private-skills', 'extensions', 'prompts', 'themes')
MAX_BYTES = 20 * 1024 * 1024
ABSENT = None


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return None if value is None else hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=str(path.parent), prefix='.auto-sync-')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def lock(path, wait=0):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('a') as stream:
        os.chmod(path, 0o600)
        deadline = time.monotonic()+wait
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)
        yield


@contextlib.contextmanager
def settings_lock(profile):
    # Same lock directory and heartbeat convention as Pi's proper-lockfile.
    directory = profile/'settings.json.lock'
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        # Pi refreshes active lock timestamps; recover abandoned empty locks
        # after a conservative two minutes (e.g. SIGKILL or a reboot).
        if time.time()-directory.stat().st_mtime <= 120:
            raise
        directory.rmdir()
        directory.mkdir(mode=0o700)
    stop = threading.Event()
    def heartbeat():
        while not stop.wait(2):
            os.utime(directory, None)
    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join()
        directory.rmdir()


def file_path(root, key):
    parts = PurePosixPath(key).parts
    if '/'.join(parts) != key:
        raise ValueError('Noncanonical file path')
    if len(parts) < 3 or parts[0] != 'file' or parts[1] not in ROOTS:
        raise ValueError('Unmanaged file path')
    if any(p in ('.', '..') or p.startswith('.') or p in ('node_modules', '__pycache__') for p in parts[1:]):
        raise ValueError('Unsafe file path')
    target = root.joinpath(*parts[1:])
    # Do not follow even an in-tree symlink: avoid confusing ownership and races.
    # The one exception is the checked-in config/pi/skills link to the repository's skills/ folder.
    shared = shared_skills_link(root)
    if any(p.is_symlink() for p in [target, *target.parents] if p != root.parent and p != shared):
        raise ValueError('Symlink in synchronized tree')
    allowed = [root.resolve()] + ([shared.resolve()] if shared else [])
    if not any(a in target.resolve().parents for a in allowed):
        raise ValueError('Path escaped configuration')
    return target


def shared_skills_link(root):
    """Return root/skills when it is the sanctioned link to the repository's skills/ folder, else None."""
    link = root/'skills'
    if link.is_symlink() and link.resolve() == (root.parent.parent/'skills').resolve():
        return link
    return None


def validate(values):
    if not isinstance(values, dict) or len(json.dumps(values)) > MAX_BYTES:
        raise ValueError('Invalid or oversized snapshot')
    for key, value in values.items():
        if key.startswith('setting/'):
            if key[8:] not in SETTING_KEYS:
                raise ValueError('Unmanaged setting')
        elif key.startswith('file/'):
            file_path(Path('/nonexistent/pi-auto-validation'), key)
            if value is not None:
                if set(value) != {'data', 'executable'} or not isinstance(value['executable'], bool):
                    raise ValueError('Invalid file record')
                if len(base64.b64decode(value['data'], validate=True)) > 2*1024*1024:
                    raise ValueError('File exceeds two MiB')
        else:
            raise ValueError('Unmanaged snapshot key')


def reconcile(base, local, remote):
    """Absence is deletion; conflicts return no merged state (all-or-nothing)."""
    merged, conflicts = dict(remote), []
    for key in set(base) | set(local):
        before, here, there = base.get(key), local.get(key), remote.get(key)
        if digest(here) == before:
            continue
        if digest(there) not in (before, digest(here)):
            conflicts.append(key)
        elif here is None:
            merged.pop(key, None)
        else:
            merged[key] = here
    return merged, sorted(conflicts)


def exchange(hub, request):
    validate(request['local'])
    if not isinstance(request['base'], dict):
        raise ValueError('Invalid baseline')
    hub.mkdir(parents=True, exist_ok=True, mode=0o700)
    hub.chmod(0o700)
    with lock(hub/'lock', wait=20):
        path = hub/'state.json'
        state = runtime.read_json(path)
        remote = state.get('values', {})
        if not state:
            if not request.get('seed'):
                raise ValueError('Hub must be explicitly seeded once')
            merged, conflicts = request['local'], []
        elif request.get('enroll'):
            merged, conflicts = remote, []
        else:
            merged, conflicts = reconcile(request['base'], request['local'], remote)
        if conflicts:
            return {'status': 'conflict', 'conflicts': conflicts, 'revision': state.get('revision', 0)}
        validate(merged)
        if not state or merged != remote:
            if state:
                # Private recovery history; no values ever enter a log or Git.
                save(hub/'backups'/('revision-%08d.json' % state['revision']), state)
            state = {'revision': state.get('revision', 0)+1, 'updated': stamp(), 'values': merged}
            save(path, state)
        return dict(state, status='ok')


def portable(value, root, profile):
    if isinstance(value, str):
        # Most specific paths first. Only replace leading resource paths.
        for source, token in [(str(root), '${CONFIG_DIR}'), (str(profile), '${AGENT_DIR}'), (str(Path.home()), '${HOME}')]:
            if value == source or value.startswith(source+'/'):
                return token+value[len(source):]
        return value
    if isinstance(value, list):
        return [portable(v, root, profile) for v in value]
    if isinstance(value, dict):
        return {k: portable(v, root, profile) for k, v in value.items()}
    return value


def exclusions(profile):
    return set(runtime.read_json(profile/'agents-config-host.json').get('settings', {}))


def pin_packages(entries, profile):
    result = []
    for entry in entries:
        source = runtime.package_source(entry)
        if source.startswith('npm:'):
            match = re.fullmatch(r'npm:((?:@[\w.-]+/)?[\w.-]+)(?:@.*)?', source)
            if not match:
                raise ValueError('Invalid npm package declaration')
            installed = runtime.read_json(profile/'npm/node_modules'/match[1]/'package.json')
            # Only normalize mutable references. Explicit pins keep their requested version.
            if not re.fullmatch(r'npm:.+@\d+\.\d+\.\d+(?:-[\w.-]+)?', source):
                version = installed.get('version')
                if not version:
                    raise ValueError('Install the package before synchronizing its declaration')
                source = 'npm:'+match[1]+'@'+version
        if isinstance(entry, dict):
            entry = dict(entry, source=source)
        else:
            entry = source
        result.append(entry)
    return result


def snapshot(root, profile, state):
    actual = runtime.read_json(profile/'settings.json')
    source = runtime.read_json(root/'runtime.json').get('settings', {})
    old_source = state.get('sourceSettings', source)
    prior = state.get('base', {})
    excluded = exclusions(profile)
    result = {}
    for key in SETTING_KEYS-excluded:
        value = portable(actual.get(key), root, profile)
        if key == 'packages' and value is not None:
            value = pin_packages(value, profile)
        # A deliberate edit of runtime.json also counts as an input. Concurrent
        # edits to the live setting and manifest require explicit reconciliation.
        if source.get(key) != old_source.get(key):
            desired = source.get(key)
            if digest(value) not in (state.get('live', prior).get('setting/'+key), digest(desired)):
                raise ValueError('Live setting and manifest both changed: '+key)
            value = desired
        if value is not None:
            result['setting/'+key] = value
    # The private discovery path is derived by load_plan, not an exported setting.
    if 'setting/skills' in result:
        result['setting/skills'] = [v for v in result['setting/skills'] if v != '${CONFIG_DIR}/private-skills']
    for directory in ROOTS:
        base = root/directory
        if not base.exists():
            continue
        for path in sorted(base.rglob('*')):
            relative = path.relative_to(root)
            if any(p.startswith('.') or p in ('node_modules', '__pycache__') for p in relative.parts) or path.suffix == '.pyc':
                continue
            if path.is_symlink():
                raise ValueError('Symlink in synchronized tree')
            if path.is_file():
                key = 'file/'+relative.as_posix()
                file_path(root, key)
                result[key] = {'data': base64.b64encode(path.read_bytes()).decode(), 'executable': bool(path.stat().st_mode & 0o111)}
    validate(result)
    return result, source


def transport(config, request):
    if config.get('sshHost'):
        command = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                   '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
                   config['sshHost'], 'python3 '+shlex.quote(config['remoteScript'])+' hub --hub '+shlex.quote(config['hub'])]
        run = subprocess.run(command, input=json.dumps(request), text=True, capture_output=True, timeout=50)
        if run.returncode:
            raise RuntimeError('Hub connection failed; local edits retained')
        return json.loads(run.stdout)
    return exchange(Path(config['hub']), request)


def backup_file(path, backup_root, key):
    if path.is_file():
        destination = backup_root/key
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copy2(path, destination)
        destination.chmod(0o600)


def install_missing(values, root, profile):
    for entry in values.get('setting/packages', []):
        source = runtime.package_source(runtime.expand(entry, root, profile))
        problem = runtime.package_problem(source, profile)
        if problem:
            if runtime.package_location(source, profile)[0] == 'local' or problem == 'installed checkout has local changes':
                raise ValueError('Package requires source repair; existing files retained')
            with tempfile.TemporaryDirectory(prefix='pi-auto-package-') as cwd:
                run = subprocess.run(['pi', 'install', source], cwd=cwd,
                                     env=dict(os.environ, PI_CODING_AGENT_DIR=str(profile)),
                                     capture_output=True, timeout=180)
            if run.returncode:
                raise ValueError('Package installation failed')
            return True  # re-snapshot next cycle after the package manager's writes
    return False


def apply(root, profile, state, before, desired, state_dir):
    excluded = exclusions(profile)
    desired = {k:v for k,v in desired.items() if not (k.startswith('setting/') and k[8:] in excluded)}
    if install_missing(desired, root, profile):
        return None
    with settings_lock(profile):
        current, source = snapshot(root, profile, state)
        if current != before:
            # Cluster profiles share the resource tree. Another enrolled client
            # may already have applied exactly this hub revision while we waited.
            # Accept that convergence, but never overwrite a different new edit.
            if any(current.get(k) != before.get(k) and current.get(k) != desired.get(k)
                   for k in set(current) | set(before)):
                raise ValueError('Files changed during sync; retrying without overwrite')
            before = current
        changed = sorted(k for k in set(before)|set(desired) if before.get(k) != desired.get(k))
        backup_root = state_dir/'backups'/str(time.time_ns())
        for key in changed:
            if not key.startswith('file/'):
                continue
            target = file_path(root, key)
            backup_file(target, backup_root, key)
            record = desired.get(key)
            if record is None:
                if target.exists():
                    target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                fd, name = tempfile.mkstemp(dir=str(target.parent), prefix='.pi-sync-')
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(base64.b64decode(record['data']))
                os.chmod(name, 0o700 if record['executable'] else 0o600)
                os.replace(name, target)
        settings = {k[8:]:v for k,v in desired.items() if k.startswith('setting/')}
        managed = sorted(SETTING_KEYS-excluded)
        overlay = {'settings': settings, 'managedKeys': managed}
        if runtime.read_json(profile/'agents-config-auto-settings.json') != overlay:
            runtime.write_json(profile/'agents-config-auto-settings.json', overlay)
        # Retire deleted settings before the regular installer merges its plan.
        actual = runtime.read_json(profile/'settings.json')
        for key in managed:
            if key not in settings:
                actual.pop(key, None)
        runtime.write_json(profile/'settings.json', actual)
        with contextlib.redirect_stdout(io.StringIO()):
            status = runtime.sync(root/'runtime.json', profile)
        if status:
            raise ValueError('Installer reports drift; see install.py --check')
        after, source = snapshot(root, profile, {'base': {}, 'sourceSettings': source})
        if after != desired:
            raise ValueError('Readback differs; edits retained for retry')
        hashes = {k:digest(v) for k,v in after.items()}
        return {'base': hashes, 'live': hashes, 'sourceSettings': source, 'changed': len(changed)}


def once(config, enroll=False, seed=False):
    root, profile = Path(config['root']).resolve(), Path(config['profile']).resolve()
    state_dir = profile/'auto-sync'
    state_dir.mkdir(exist_ok=True, mode=0o700)
    with lock(state_dir/'lock'):
        state = runtime.read_json(state_dir/'baseline.json')
        if not state and not (seed or enroll):
            raise ValueError('Run explicit enrollment before starting the service')
        before, source = snapshot(root, profile, state)
        result = transport(config, {'local':before, 'base':state.get('base', {}), 'seed':seed, 'enroll':enroll})
        if result['status'] == 'conflict':
            save(state_dir/'status.json', dict(result, checked=stamp()))
            return 1
        # Record our accepted submissions before applying remote edits. If a
        # concurrent editor or crash interrupts apply, the next local edit is
        # based on our accepted revision, not a false conflict with ourselves.
        accepted = dict(state.get('base', {}))
        for key in set(accepted) | set(before):
            if before.get(key) == result['values'].get(key):
                accepted[key] = digest(before.get(key))
        state = dict(state, base=accepted)
        save(state_dir/'baseline.json', state)
        new_state = apply(root, profile, state, before, result['values'], state_dir)
        if new_state is None:
            save(state_dir/'status.json', {'status':'installing', 'checked':stamp()})
            return 1
        save(state_dir/'baseline.json', new_state)
        save(state_dir/'status.json', {'status':'ok', 'checked':stamp(), 'revision':result['revision'],
                                      'changed':new_state['changed'], 'modelRequests':0})
        return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['hub','once','watch','status','resolve'])
    parser.add_argument('--config', type=Path, default=Path.home()/'.pi/agent/auto-sync/config.json')
    parser.add_argument('--hub', type=Path)
    parser.add_argument('--enroll', action='store_true')
    parser.add_argument('--seed', action='store_true')
    parser.add_argument('--prefer', choices=['local','remote'])
    args = parser.parse_args()
    if args.action == 'hub':
        request = json.loads(sys.stdin.read(MAX_BYTES+1))
        print(json.dumps(exchange(args.hub, request)))
        return 0
    config = runtime.read_json(args.config)
    status_path = Path(config['profile'])/'auto-sync/status.json'
    if args.action == 'status':
        result = runtime.read_json(status_path)
        if result.get('status') == 'ok' and (datetime.now(timezone.utc)-datetime.fromisoformat(result['checked'])).total_seconds() > 180:
            result['status'] = 'stale'
        print(json.dumps(result, indent=2))
        return 0 if result.get('status') == 'ok' else 1
    if args.action == 'resolve':
        if not args.prefer:
            parser.error('resolve requires --prefer local or --prefer remote')
        state_dir = status_path.parent
        with lock(state_dir/'lock'):
            state = runtime.read_json(state_dir/'baseline.json')
            status = runtime.read_json(status_path)
            conflicts = status.get('conflicts', [])
            if not conflicts:
                raise ValueError('No recorded conflicts to resolve')
            local, _ = snapshot(Path(config['root']), Path(config['profile']), state)
            remote = transport(config, {'local':{},'base':{},'enroll':True})['values']
            for key in conflicts:
                state['base'][key] = digest(remote.get(key) if args.prefer == 'local' else local.get(key))
            save(state_dir/'baseline.json', state)
        args.action = 'once'
    failures = 0
    while True:
        try:
            result = once(config, args.enroll, args.seed)
            failures = 0
        except Exception as error:
            # No raw subprocess output or setting/file values in diagnostics.
            save(status_path, {'status':'error', 'checked':stamp(), 'errorType':type(error).__name__,
                               'message':str(error) if isinstance(error, (ValueError, RuntimeError)) else 'Retry pending; local data retained'})
            result = 2
            failures += 1
        if args.action == 'once':
            print(status_path.read_text())
            return result
        # Bounded exponential backoff prevents gateway flooding when offline.
        time.sleep(min(1800, config.get('interval',60)*2**min(failures,5)))


if __name__ == '__main__':
    raise SystemExit(main())
