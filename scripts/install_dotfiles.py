#!/usr/bin/env python3
"""Install shared macOS pane shortcuts; dry-run by default, preserve other settings."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
BEGIN = '// BEGIN agents-config pane shortcuts'
END = '// END agents-config pane shortcuts'


def without_comments(text):
    return re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*[\s\S]*?\*/',
                  lambda m: m.group(1) or '', text)


def cursor_config(text, bindings):
    # Remove only our own block; preserve all user bindings and comments.
    text = re.sub(r'\n?\s*' + re.escape(BEGIN) + r'[\s\S]*?' + re.escape(END), '', text)
    end = text.rfind(']')
    if end < 0:
        raise ValueError('Cursor keybindings must be an array')
    head = text[:end].rstrip()
    tail = without_comments(head).rstrip()
    separator = '' if tail.endswith(('[', ',')) else ','
    block = json.dumps(bindings, indent=2)[2:-2]
    result = head + separator + '\n  ' + BEGIN + '\n' + block + '\n  ' + END + '\n' + text[end:]
    # Accept JSON-with-comments and a trailing comma in existing user bindings.
    clean = without_comments(result)
    clean = re.sub(r',\s*([}\]])', r'\1', clean)
    if not isinstance(json.loads(clean), list):
        raise ValueError('Cursor keybindings must be an array')
    return result


def ghostty_config(text, fragment):
    begin, end = '# BEGIN agents-config pane shortcuts', '# END agents-config pane shortcuts'
    text = re.sub(r'\n?' + re.escape(begin) + r'[\s\S]*?' + re.escape(end) + r'\n?', '', text)
    return text.rstrip() + f'\n\n{begin}\nconfig-file = {fragment}\n{end}\n'


def verify_legacy():
    manifest = json.loads((ROOT / 'dotfiles/legacy-manifest.json').read_text())
    for name, digest in manifest['files'].items():
        data = (ROOT / 'dotfiles/legacy' / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f'Legacy checksum mismatch: {name}')
    print(f"Legacy migration verified: {len(manifest['files'])} files")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--home', type=Path, default=Path.home(), help='Override target home for tests')
    args = parser.parse_args()
    if sys.platform != 'darwin' and args.home == Path.home():
        parser.error('macOS only; use --home for isolated tests')
    verify_legacy()
    home = args.home
    user = home / 'Library/Application Support/Cursor/User/keybindings.json'
    ghostty = home / 'Library/Application Support/com.mitchellh.ghostty/config.ghostty'
    # Ghostty loads the XDG path before the macOS Application Support path.
    xdg = Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config'))) / 'ghostty/config'
    if xdg.exists():
        ghostty = xdg
    bindings = json.loads((ROOT / 'dotfiles/cursor/keybindings.json').read_text())
    changes = {
        user: cursor_config(user.read_text() if user.exists() else '[]\n', bindings),
        ghostty: ghostty_config(ghostty.read_text() if ghostty.exists() else '', ROOT / 'dotfiles/ghostty/keybindings.conf'),
    }
    stamp = datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S-%f')
    backup = home / '.local/state/agents-config/dotfiles/backups' / stamp
    for path, content in changes.items():
        if path.exists() and path.read_text() == content:
            print(f'Unchanged: {path}')
            continue
        print(f"{'Apply' if args.apply else 'Would update'}: {path}")
        if args.apply:
            if path.exists():
                target = backup / path.relative_to(home)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    if args.apply:
        print(f'Backups (if needed): {backup}')
        print('Cursor watches keybindings. Reload Ghostty configuration with Command+Shift+comma.')
    else:
        print('Dry run only. Pass --apply to install.')


if __name__ == '__main__':
    main()
