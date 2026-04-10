# Cursor SSH + Kerberos Auto-Reconnect on SNAP

Goal: minimize password prompts when Cursor reconnects SSH to SNAP servers.

**Limitation:** Cursor creates a fresh SSH session on new window/folder change/reload, which can force re-auth. [Cursor forum thread](https://forum.cursor.com/t/remote-ssh-forces-full-reconnect-mfa-per-window-folder-change-and-window-reload/156891). The workaround is SSH ControlMaster multiplexing + Kerberos GSSAPI.

---

## Setup

### 1. Get a Kerberos ticket on your Mac

```bash
kinit <CSID>@CS.STANFORD.EDU
# optionally for AFS tokens:
aklog
```

### 2. SSH config (`~/.ssh/config`)

```sshconfig
Host *.stanford.edu
  GSSAPIAuthentication yes
  GSSAPIDelegateCredentials yes
  PreferredAuthentications gssapi-with-mic,publickey,password
  ControlMaster auto
  ControlPath ~/.ssh/%r@%h:%p
  ControlPersist 8h
  ServerAliveInterval 60
  ServerAliveCountMax 10
```

- **GSSAPI** — SSH uses your Kerberos ticket instead of prompting for password
- **ControlMaster** — multiplexes connections so Cursor reuses the existing SSH session
- **ControlPersist 8h** — keeps the master connection alive for 8 hours after last session closes
- **ServerAliveInterval** — prevents idle disconnects

### 3. Server-side persistent sessions (krbtmux + reauth)

Don't rely on Cursor for session survival. On each SNAP server:

```bash
/afs/cs/software/bin/krbtmux     # tmux wrapper that manages Kerberos ticket renewal
/afs/cs/software/bin/reauth       # re-authenticates your Kerberos credentials
tmux new -As work                 # persistent session for all important work
```

Run jobs inside tmux. If Cursor disconnects, your work survives.

---

## What this gets you

- Cursor reconnects without password prompt (most of the time)
- If Cursor disconnects, work is alive in tmux
- Kerberos auth reused via GSSAPI, not re-prompted

## What this does NOT guarantee

- Kerberos tickets still expire — if fully expired with no renewable ticket, you re-authenticate manually
- Cursor still has reconnect edge cases on some SSH setups

---

## TODO

```
[x] Verify kinit works on Mac: kinit brando9@CS.STANFORD.EDU (done 2026-04-09)
[x] Update ~/.ssh/config with the GSSAPI + ControlMaster block (done 2026-04-09)
[x] Automate kinit — created keytab on skampere1, copied to Mac (done 2026-04-09)
[x] Add kinit -kt snippet to ~/.zshrc (done 2026-04-09)
[x] Create launchd plist for kinit -kt every 4h (done 2026-04-09)
[x] Verify launchd is running: launchctl list | grep kinit && klist (done 2026-04-09)
[x] Test passwordless SSH from Mac: ssh -o BatchMode=yes brando9@skampere1 (done 2026-04-09)
[ ] Test Cursor SSH reconnect to a SNAP server without password prompt
[ ] If ControlPersist 8h is too short, increase it
[x] Server-side auto-renewal deployed — krbtmux/reauth no longer needed (done 2026-04-09)
    See: todo_infinite_reauth_kinit_server_side.md for details.
    krenew.sh + .bashrc loop + cron handle all ticket renewal automatically.
```

---

## Auto-password for kinit (keytab approach)

A **keytab** file stores your Kerberos credentials so `kinit` can run without a password prompt. This enables fully unattended SSH via GSSAPI.

### 1. Create a keytab on a SNAP server

```bash
# On a SNAP server where you're already authenticated:
ktutil
# Inside ktutil:
addent -password -p <CSID>@CS.STANFORD.EDU -k 1 -e aes256-cts-hmac-sha1-96
# (enter your password when prompted)
wkt /afs/cs.stanford.edu/u/<CSID>/.keytab
quit
```

**Important:** Lock down the keytab — it's equivalent to your password:
```bash
chmod 600 /afs/cs.stanford.edu/u/<CSID>/.keytab
```

### 2. Copy the keytab to your Mac (optional, for local kinit)

```bash
scp <CSID>@snap-server.stanford.edu:/afs/cs.stanford.edu/u/<CSID>/.keytab ~/.keytab
chmod 600 ~/.keytab
```

### 3. Use the keytab for passwordless kinit

```bash
kinit -kt ~/.keytab <CSID>@CS.STANFORD.EDU
```

### 4. Add to `~/.zshrc` (covers interactive terminal → SSH workflow)

```bash
# Auto-renew Kerberos ticket if keytab exists
if [[ -f ~/.keytab ]]; then
  kinit -kt ~/.keytab <CSID>@CS.STANFORD.EDU 2>/dev/null
fi
```

**Why this helps:** Every time you open a new terminal tab/window, `kinit` runs and refreshes
your ticket. So when you then `ssh` to SNAP, GSSAPI already has a valid ticket — no password prompt.

**Why this is NOT enough on its own:** `.zshrc` only runs for **interactive** shells (i.e., you
opening a terminal). Cursor/VS Code launches SSH as a **non-interactive, non-login** shell
(`ssh user@host "command..."`), so `.zshrc` is never sourced. If your ticket expires while
you're in Cursor without opening a new terminal, Cursor's next SSH reconnect will prompt for
a password. That's why you also need cron (below).

### 5. Automate via launchd (the reliable way on macOS)

**Why not cron?** macOS cron does **not** run missed jobs after the Mac wakes from sleep. If
your Mac sleeps overnight (8+ hours), the ticket expires, cron never fired, and the next
Cursor SSH reconnect prompts for a password. **launchd** fixes this — it runs missed jobs
immediately on wake.

**Step 1:** Create the plist file:

```bash
cat > ~/Library/LaunchAgents/com.stanford.kinit-renew.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.stanford.kinit-renew</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/kinit</string>
        <string>-kt</string>
        <string>/Users/YOUR_MAC_USERNAME/.keytab</string>
        <string>YOUR_CSID@CS.STANFORD.EDU</string>
    </array>
    <key>StartInterval</key>
    <integer>14400</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/kinit-renew.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/kinit-renew.out</string>
</dict>
</plist>
PLIST
```

Replace `YOUR_MAC_USERNAME` and `YOUR_CSID` with your actual values.

**Step 2:** Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.stanford.kinit-renew.plist
```

**What this does:**
- `RunAtLoad: true` → runs `kinit` immediately on login (Mac boot / user login)
- `StartInterval: 14400` → re-runs every 4 hours (14400 seconds)
- **On wake from sleep:** launchd sees the missed interval and runs `kinit` right away
- Logs errors to `/tmp/kinit-renew.err` for debugging

**Step 3:** Verify it's running:

```bash
launchctl list | grep kinit
# Should show: PID  0  com.stanford.kinit-renew
klist
# Should show a valid ticket for <CSID>@CS.STANFORD.EDU
```

**To unload/stop:**
```bash
launchctl unload ~/Library/LaunchAgents/com.stanford.kinit-renew.plist
```

### Summary: use both .zshrc + launchd

| Approach | What it covers | What it misses |
|---|---|---|
| `.zshrc` | Every new terminal → immediate fresh ticket before SSH | Cursor (non-interactive), long sessions without new terminals |
| launchd (every 4h) | Cursor, background, survives sleep/wake, runs on login | Slight delay if ticket just expired and interval hasn't fired yet |
| **Both together** | **Always works** — no password prompts | — |

**Why both?** `.zshrc` gives you an instant refresh the moment you open a terminal (no waiting
for the 4h interval). launchd is the background safety net that keeps the ticket alive for
Cursor and survives Mac sleep. Together they cover every scenario.

### Caveats

- **Security:** The keytab is your password in a file. Protect it like `~/.ssh/id_rsa`.
- **Password changes:** If you change your Stanford password, you must regenerate the keytab.
- **Stanford policy:** Check if Stanford/CS IT allows keytab usage — some orgs restrict it.
- **Alternative:** If keytabs aren't allowed, you can use `expect` or `sshpass` to pipe the password, but these are less secure (password in plaintext on disk or in a script).

---

Sources:
- [Cursor forum: SSH forces full reconnect & MFA per window/folder change](https://forum.cursor.com/t/remote-ssh-forces-full-reconnect-mfa-per-window-folder-change-and-window-reload/156891)
- [ChatGPT conversation with full analysis](https://chatgpt.com/c/69d7e52e-4b24-83e8-8d27-5cdd74cb2f4e)
- `~/agents-config/machine/snap.md` — SNAP cluster docs (krbtmux, reauth, SSH config)
