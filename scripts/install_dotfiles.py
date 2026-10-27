#!/usr/bin/env python3
"""Install shared Cursor, Ghostty and Zed shortcuts; dry-run by default, preserve other settings."""
import argparse
import datetime
import difflib
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


def blank_comments(text):
    # Same length as the input, so positions found here are valid in the original.
    return re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*[\s\S]*?\*/',
                  lambda m: m.group(1) or re.sub(r'[^\n]', ' ', m.group(0)), text)


def read_text(path):
    return path.read_bytes().decode()  # keep CRLF as is


def cursor_config(text, bindings):
    # Remove only our own block; preserve all user bindings and comments.
    text = re.sub(r'\n?\s*' + re.escape(BEGIN) + r'[\s\S]*?' + re.escape(END), '', text)
    text = text if text.strip() else '[]\n'
    end = blank_comments(text).rfind(']')
    if end < 0:
        raise ValueError('Cursor keybindings must be an array')
    idx = len(blank_comments(text[:end]).rstrip())
    separator = '' if text[idx - 1] in '[,' else ','
    block = json.dumps(bindings, indent=2)[2:-2]
    result = text[:idx] + separator + text[idx:end].rstrip() + '\n  ' + BEGIN + '\n' + block + '\n  ' + END + '\n' + text[end:]
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


# Zed settings this installer owns; every other live setting (vim_mode, fonts, servers) is left alone.
ZED_MANAGED = [('base_keymap',), ('theme',), ('icon_theme',), ('profiles', 'Gruvbox Dark Soft'), ('agent', 'dock'), ('agent', 'threads_sidebar'),
               ('project_panel', 'dock'), ('git_panel', 'dock'), ('outline_panel', 'dock')]


def parse_jsonc(text):
    # Accept comments and trailing commas, as Zed does.
    blank = blank_comments(text)
    return json.loads(re.sub(r'("(?:\\.|[^"\\])*")|,(?=\s*[}\]])', lambda m: m.group(1) or ' ', blank))


def skip_space(text, i):
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text.startswith('//', i):
            i = text.find('\n', i)
            i = len(text) if i < 0 else i
        elif text.startswith('/*', i):
            i = text.index('*/', i) + 2
        else:
            break
    return i


def string_end(text, i):
    i += 1
    while text[i] != '"':
        i += 2 if text[i] == '\\' else 1
    return i + 1


def top_level_values(text):
    """Map each top-level key of a JSON-with-comments object to its value's (start, end); also return the closing brace."""
    spans = {}
    i = skip_space(text, 0)
    if text[i:i + 1] != '{':
        raise ValueError('Zed settings must be an object')
    i += 1
    while True:
        i = skip_space(text, i)
        if text[i] == '}':
            return spans, i
        if text[i] == ',':
            i += 1
            continue
        end = string_end(text, i)
        key = json.loads(text[i:end])
        i = skip_space(text, end)
        i = skip_space(text, i + 1)  # past the colon
        start, depth, last = i, 0, i
        while depth > 0 or text[i] not in ',}':
            if text[i] == '"':
                i = last = string_end(text, i)
                continue
            if text.startswith(('//', '/*'), i):
                i = skip_space(text, i)
                continue
            depth += text[i] in '{['
            depth -= text[i] in '}]'
            i += 1
            if not text[i - 1].isspace():
                last = i
        spans[key] = (start, last)


def zed_settings(text, shared):
    """Set the managed Zed values; rewrite only top-level values that differ, so comments elsewhere survive."""
    text = text if text.strip() else '{}\n'
    crlf = '\r\n' in text
    live = parse_jsonc(text)
    if not isinstance(live, dict):
        raise ValueError('Zed settings must be an object')
    wanted = {}
    for path in ZED_MANAGED:
        value = shared
        for part in path:
            value = value[part]
        if len(path) == 1:
            wanted[path[0]] = value
        else:
            current = wanted.get(path[0], live.get(path[0]))
            wanted[path[0]] = {**(current if isinstance(current, dict) else {}), path[1]: value}
    for top, value in wanted.items():
        if live.get(top) == value:
            continue
        spans, close = top_level_values(text)
        rendered = json.dumps(value, indent=2).replace('\n', '\n  ')
        if top in spans:
            a, b = spans[top]
            text = text[:a] + rendered + text[b:]
        else:
            idx = len(blank_comments(text[:close]).rstrip())
            sep = '' if text[idx - 1] in '{,' else ','
            text = text[:idx] + sep + text[idx:close].rstrip() + f'\n  {json.dumps(top)}: {rendered}\n' + text[close:]
        live[top] = value
    if parse_jsonc(text) != live:
        raise ValueError('Zed settings merge changed unrelated content')
    return text.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else text


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
    parser.add_argument('--diff', action='store_true', help='Show pending unified diffs without unrelated context')
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
    zed = home / '.config/zed'
    zed_keymap = parse_jsonc((ROOT / 'dotfiles/zed/keymap.json').read_text())
    zed_shared = parse_jsonc((ROOT / 'dotfiles/zed/settings.json').read_text())
    zed_keymap_live = zed / 'keymap.json'
    zed_settings_live = zed / 'settings.json'
    for live in (zed_settings_live, zed_keymap_live):
        if (live.is_symlink() or live.exists()) and ROOT in live.resolve().parents:
            parser.error(f'{live} is a link into this repository; replace it with a real file so the installer can merge into it')
    changes = {
        zed_settings_live: zed_settings(read_text(zed_settings_live) if zed_settings_live.exists() else '', zed_shared),
        zed_keymap_live: cursor_config(read_text(zed_keymap_live) if zed_keymap_live.exists() else '[]\n', zed_keymap),
        user: cursor_config(read_text(user) if user.exists() else '[]\n', bindings),
        ghostty: ghostty_config(read_text(ghostty) if ghostty.exists() else '', ROOT / 'dotfiles/ghostty/keybindings.conf'),
    }
    stamp = datetime.datetime.now().strftime('%m-%d-%Y_%H-%M-%S-%f')
    backup = home / '.local/state/agents-config/dotfiles/backups' / stamp
    for path, content in changes.items():
        previous = read_text(path) if path.exists() else ''
        if '\r\n' in previous:
            content = content.replace('\r\n', '\n').replace('\n', '\r\n')
        if path.exists() and previous == content:
            print(f'Unchanged: {path}')
            continue
        print(f"{'Apply' if args.apply else 'Would update'}: {path}")
        if args.diff:
            for line in difflib.unified_diff(
                    previous.splitlines(keepends=True), content.splitlines(keepends=True),
                    fromfile=str(path) if path.exists() else '/dev/null', tofile=str(path), n=0):
                sys.stdout.write(line)
                if not line.endswith('\n'):
                    print('\n\\ No newline at end of file')
        if args.apply:
            if path.exists():
                target = backup / (path.relative_to(home) if home in path.parents else Path('outside-home') / path.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode())
    if args.apply:
        print(f'Backups (if needed): {backup}')
        print('Cursor and Zed watch their config files. Reload Ghostty configuration with Command+Shift+comma.')
    else:
        print('Dry run only. Pass --apply to install.')


if __name__ == '__main__':
    main()
