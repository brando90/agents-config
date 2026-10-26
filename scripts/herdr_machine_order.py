#!/usr/bin/env python3
"""Check or restore Brando's saved Herdr machine order without reconnecting."""
import argparse
import datetime
import json
import os
from pathlib import Path
import stat
import tempfile

ORDER = ['skampere1', 'skampere2', 'skampere3', 'mercury1', 'mercury2',
         'Sherlock', 'FarmShare']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='save order with backup')
    args = parser.parse_args()
    root = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state')
    path = root / 'herdr/client/endpoints.json'
    original = path.read_bytes()
    data = json.loads(original)
    if data.get('version') != 1 or not isinstance(data.get('ssh'), list):
        parser.error('Unsupported catalog schema; no changes made')
    profiles = data['ssh']
    rank = {label: i for i, label in enumerate(ORDER)}
    ordered = sorted(profiles, key=lambda p: rank.get(p['label'], len(rank)))
    print('Saved:   ' + ' -> '.join(p['label'] for p in profiles))
    print('Desired: ' + ' -> '.join(p['label'] for p in ordered))
    if profiles == ordered:
        print('OK: already ordered; no write or backup needed')
        return 0
    if not args.apply:
        print('DRIFT: run with --apply to restore ordering')
        return 1
    stamp = datetime.datetime.now().strftime('%m-%d-%Y-%H%M%S-%f')
    backup = path.with_name('endpoints.before-order-' + stamp + '.json')
    data['ssh'] = ordered
    payload = (json.dumps(data, indent=2) + '\n').encode()
    fd, temp = tempfile.mkstemp(prefix='.endpoints-order-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            os.fchmod(f.fileno(), stat.S_IMODE(path.stat().st_mode))
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        if path.read_bytes() != original:
            raise RuntimeError('Catalog changed concurrently; rerun after that edit finishes')
        with backup.open('xb') as f:
            f.write(original)
        backup.chmod(0o600)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    assert json.loads(path.read_bytes()) == data
    print('APPLIED: only profile order changed; backup: ' + str(backup))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
