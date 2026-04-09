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
[ ] Verify kinit works on Mac: kinit <CSID>@CS.STANFORD.EDU
[ ] Update ~/.ssh/config with the GSSAPI + ControlMaster block above
[ ] Test Cursor SSH reconnect to a SNAP server without password prompt
[ ] On each SNAP server, verify krbtmux + reauth are available at /afs/cs/software/bin/
[ ] Start using krbtmux + reauth + tmux for all long-running sessions
[ ] If ControlPersist 8h is too short, increase it
```

---

Sources:
- [Cursor forum: SSH forces full reconnect & MFA per window/folder change](https://forum.cursor.com/t/remote-ssh-forces-full-reconnect-mfa-per-window-folder-change-and-window-reload/156891)
- [ChatGPT conversation with full analysis](https://chatgpt.com/c/69d7e52e-4b24-83e8-8d27-5cdd74cb2f4e)
- `~/agents-config/machine/snap.md` — SNAP cluster docs (krbtmux, reauth, SSH config)
