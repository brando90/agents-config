#!/usr/bin/env python3
"""Verify generated command forwarding and fail-closed grant reads with fake credentials."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

source = Path(__file__).with_name('install_su_node.sh').read_text()
template = source.split('  cat > "$tmp" <<WRAPPER\n', 1)[1].split('\nWRAPPER', 1)[0]
with tempfile.TemporaryDirectory(prefix='su-wrapper-test-') as d:
    root = Path(d)
    for name in ('runtime', 'profile', 'bin'):
        (root / name).mkdir()
    grant = root / 'grant'
    grant.write_text('sk-ant-oat01-' + 'A' * 48)
    grant.chmod(0o600)
    exe = root / 'runtime/claude'
    exe.write_text('#!/bin/bash\nprintf "%s\\n" "$@"\n')
    exe.chmod(0o700)
    # Portable stand-in for GNU stat, using actual fixture ownership and mode.
    stat = root / 'bin/stat'
    stat.write_text(f'#!{sys.executable}\nimport os,sys\ns=os.lstat(sys.argv[3])\nprint(s.st_uid if sys.argv[2]=="%u" else oct(s.st_mode & 0o777)[2:])\n')
    stat.chmod(0o700)
    render = f"profile='{root}/profile'\ngrant='{grant}'\nruntime='{root}/runtime'\ncat <<WRAPPER\n{template}\nWRAPPER\n"
    wrapper_text = subprocess.run(['bash', '-c', render], capture_output=True, text=True, check=True).stdout
    env = os.environ.copy()
    env['PATH'] = str(root / 'bin') + ':/usr/bin:/bin'
    for name in ('claude-su', 'clauded-su'):
        wrapper = root / name
        wrapper.write_text(wrapper_text)
        args = ['space value', 'literal $HOME', '*', '']
        out = subprocess.run(['bash', str(wrapper), *args], capture_output=True, text=True, env=env)
        assert out.returncode == 0, out.stderr
        expected = (['--dangerously-skip-permissions'] if name == 'clauded-su' else []) + args
        assert out.stdout.splitlines() == expected
    print('PASS argument forwarding and permission flags')
    wrapper = root / 'claude-su'
    def rejects():
        out = subprocess.run(['bash', str(wrapper)], capture_output=True, text=True, env=env)
        assert out.returncode != 0 and not out.stdout, (out.returncode, out.stdout, out.stderr)
    grant.chmod(0o644)
    rejects()
    print('PASS insecure grant mode rejected')
    grant.chmod(0o600)
    cat = root / 'bin/cat'
    cat.write_text('#!/bin/bash\nexit 1\n')
    cat.chmod(0o700)
    rejects()
    cat.unlink()
    print('PASS failed grant read rejected')
    grant.write_text('\n')
    rejects()
    print('PASS empty grant rejected')
    grant.unlink()
    rejects()
    print('PASS missing grant rejected')
