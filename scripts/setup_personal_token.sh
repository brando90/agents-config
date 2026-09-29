#!/bin/bash
# TLDR: run `claude setup-token` for Brando's personal Claude account in a 1000-column pseudo-terminal (so the token cannot wrap) and save the token, mode 600, to ~/keys/claude_personal_oauth_token.txt without echoing it elsewhere.
set -u
umask 077
LOG="$HOME/keys/.claude_setup_token_session.log"
script -q "$LOG" sh -c 'stty cols 1000 rows 60 2>/dev/null; claude setup-token'
python3 - "$LOG" <<'PY'
import os, re, sys
s = open(sys.argv[1], 'rb').read().decode('utf-8', 'replace')
s = re.sub(r'\x1b\[[0-9;?]*[ -/]*[@-~]', '', s)          # CSI sequences
s = re.sub(r'\x1b[\]P].*?(?:\x07|\x1b\\)', '', s, flags=re.S)  # OSC / DCS sequences
m = re.findall(r'sk-ant-oat\d{2}-[A-Za-z0-9_-]{32,}', s)
out = os.path.expanduser('~/keys/claude_personal_oauth_token.txt')
with open(out, 'w') as f:
    f.write(m[-1] if m else '')
os.chmod(out, 0o600)
print(f'PERSONAL_TOKEN_SAVED length={len(m[-1])}' if m else 'PERSONAL_TOKEN_MISSING')
PY
rm -f "$LOG"
