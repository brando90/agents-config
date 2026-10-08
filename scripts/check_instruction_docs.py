#!/usr/bin/env python3
"""Check the portable instruction layer; no model calls or third-party packages."""
from pathlib import Path
import argparse
import re
import unicodedata
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
# Local maintenance budgets, not claims about model context windows.
BUDGETS = {
    'AGENTS.md': (6144, 1000, 200),
    'CLAUDE.md': (6144, 1000, 200),
    'INDEX_RULES.md': (22528, 3200, 250),
}
EXPECTED = {'hard': set(range(1, 12)), 'trigger': set(range(6, 66)),
            'guideline': set(range(14, 25))}
LINK = re.compile(r'\]\((?:<([^>]+)>|([^\s)]+))(?:\s+"[^"]*")?\)')


def prose(text):
    """Ignore fenced examples when checking Markdown links and heading IDs."""
    result, fence = [], None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            token = match[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            result.append(line)
    return '\n'.join(result)


def anchors(text):
    result, used = set(), {}
    for title in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', prose(text), re.M):
        title = re.sub(r'<[^>]+>', '', title).lower()
        title = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', title)
        slug = ''.join(c for c in title if c in '-_ ' or unicodedata.category(c)[0] in 'LN').replace(' ', '-')
        suffix = used.get(slug, 0)
        used[slug] = suffix + 1
        result.add(slug + (f'-{suffix}' if suffix else ''))
    result.update(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)', text))
    return result


def check(root=ROOT):
    errors, counts = [], {}
    for name, (byte_cap, word_cap, line_cap) in BUDGETS.items():
        path = root / name
        if not path.is_file():
            errors.append(f'Missing startup file: {name}')
            continue
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        counts[name] = (len(raw), len(text.split()), len(text.splitlines()))
        for label, value, cap in zip(('bytes', 'words', 'lines'), counts[name], (byte_cap, word_cap, line_cap)):
            if value > cap:
                errors.append(f'{name}: {value} {label} exceeds local budget {cap}')
    entries = [root / name for name in ('AGENTS.md', 'CLAUDE.md')]
    if all(p.is_file() for p in entries):
        bodies = [re.sub(r'(?m)^\*\*Doc link:\*\*.*$', '', p.read_text()) for p in entries]
        if bodies[0] != bodies[1]:
            errors.append('AGENTS.md and CLAUDE.md shared content differs')
    index_path = root / 'INDEX_RULES.md'
    if not index_path.is_file():
        return errors, counts, 0, 0
    index = index_path.read_text()
    for label, kind, number in re.findall(r'\[(\d+)\]\(rules/[^)]+#(trigger|guideline)-rule-(\d+)\)', index):
        if label != number:
            errors.append(f'Index label {label} points to {kind} rule {number}')
    for label, number in re.findall(r'^(\d+)\. .*?\[Details\]\(rules/[^)]+#hard-rule-(\d+)\)', index, re.M):
        if label != number:
            errors.append(f'Hard Rule label {label} points to rule {number}')
    seen = {kind: set() for kind in EXPECTED}
    rule_files = sorted((root / 'rules').glob('*.md'))
    for path in rule_files:
        for kind, number in re.findall(r'^## (Hard|Trigger|Guideline) Rule (\d+)$', path.read_text(), re.M):
            kind, number = kind.lower(), int(number)
            if number in seen[kind]:
                errors.append(f'Duplicate {kind} rule {number}')
            seen[kind].add(number)
            dest = f'{path.relative_to(root).as_posix()}#{kind}-rule-{number}'
            if f']({dest})' not in index:
                errors.append(f'Index does not route to {dest}')
    for kind, expected in EXPECTED.items():
        if seen[kind] != expected:
            errors.append(f'{kind} coverage mismatch: missing={sorted(expected-seen[kind])}, extra={sorted(seen[kind]-expected)}')
    paths = entries + [root / 'INDEX_RULES.md', root / 'CATALOG.md'] + rule_files
    paths += [root / p for p in ('README.md', 'docs/setup-reference.md', 'docs/reference/background.md', 'workflows/repo-init.md', 'workflows/question-screenshot-ingest.md', 'workflows/broad-investigation.md', 'machine/snap-init.md') if (root / p).is_file()]
    paths += sorted((root / 'docs/instruction-audit').glob('*.md'))
    link_count = 0
    for path in paths:
        if not path.is_file():
            errors.append(f'Missing routed document: {path.relative_to(root)}')
            continue
        for match in LINK.finditer(prose(path.read_text())):
            target = match[1] or match[2]
            parts = urlsplit(target)
            if parts.scheme or target.startswith(('/', '~')):
                continue
            dest = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not dest.exists():
                errors.append(f'{path.relative_to(root)}: missing link {target}')
            elif parts.fragment and dest.suffix == '.md' and unquote(parts.fragment) not in anchors(dest.read_text()):
                errors.append(f'{path.relative_to(root)}: missing anchor {target}')
            link_count += 1
    return errors, counts, sum(map(len, seen.values())), link_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Check an isolated fixture or checkout')
    args = parser.parse_args()
    errors, counts, rules, links = check(args.root.resolve())
    for name, (size, words, lines) in counts.items():
        print(f'{name}: {size} bytes, {words} words, {lines} lines')
    print(f'Rules routed: {rules}; local links checked: {links}')
    for error in errors:
        print(f'ERROR: {error}')
    print(f'{"FAIL" if errors else "PASS"}: {len(errors)} errors')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
