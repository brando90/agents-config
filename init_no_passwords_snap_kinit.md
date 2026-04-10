# Passwordless SSH to SNAP: One-Time Keytab Init Guide

Goal: set up a Kerberos keytab so `kinit` never prompts for a password again. After this, SSH and Cursor connections to SNAP are fully automatic.

**Prerequisites:**
- You can currently SSH to a SNAP server (with password)
- You know your Stanford CSID (e.g., `brando9`) and password

---

## Why this eliminates all password prompts

SNAP uses **Kerberos** for authentication. Normally, every SSH connection requires you to prove
your identity — either by typing your password or by having a valid Kerberos "ticket" (a
temporary token that proves you already authenticated). Tickets expire after ~10 hours.

**The problem:** You have to keep running `kinit` and typing your password to get a fresh ticket.
If the ticket expires, SSH prompts you for a password. Cursor is especially bad because it
opens new SSH connections constantly (on window reload, folder change, reconnect) — each one
checks for a valid ticket.

**The solution has three parts:**

1. **Keytab file** (`~/.keytab`) — This stores your Kerberos credentials encrypted on disk, so
   `kinit` can get a fresh ticket **without you typing a password**. It's like an SSH private
   key but for Kerberos. You create it once by typing your password, and after that it works
   forever (until you change your password).

2. **launchd auto-renewal** (every 4 hours) — A macOS background service that runs
   `kinit -kt ~/.keytab` automatically, so your ticket is **always fresh**. Unlike cron,
   launchd catches up after Mac sleep — so even if your Mac was closed overnight, it renews
   the ticket the moment you open the lid. This is what makes Cursor work without prompts.

3. **`.zshrc` snippet** — Runs `kinit` every time you open a terminal, so you always have a
   fresh ticket right before you SSH. This is a belt-and-suspenders backup for the launchd
   service.

4. **SSH config (GSSAPI + ControlMaster)** — Tells SSH to use your Kerberos ticket instead of
   asking for a password (`GSSAPIAuthentication yes`), and to reuse existing connections so
   Cursor doesn't open redundant ones (`ControlMaster auto`).

**The result:** Your Mac always has a valid Kerberos ticket (launchd keeps it fresh). SSH is
configured to use that ticket (GSSAPI). So every SSH connection — whether from Terminal,
Cursor, or any other app — authenticates silently. No password prompts, ever.

**What about the SNAP server side?** When you SSH with GSSAPI, the server accepts your ticket
automatically. The `GSSAPIDelegateCredentials yes` setting also forwards your ticket to the
server, so commands that need Kerberos on the server (like accessing AFS paths) also work
without re-authenticating. For long-running sessions, `krbtmux` + `reauth` on the server
handle server-side ticket renewal independently.

---

## How it works (the full chain)

```
launchd (every 4h) + .zshrc (every new terminal)
        ↓
kinit -kt ~/.keytab brando9@CS.STANFORD.EDU   ← no password needed
        ↓
Kerberos ticket cache stays fresh
        ↓
~/.ssh/config has GSSAPIAuthentication yes
        ↓
Any SSH connection finds valid ticket → no password prompt
        ↓
Cursor SSH reconnect → just works
```

**Why .zshrc alone isn't enough:** Cursor/VS Code launches SSH as a non-interactive, non-login
shell. `.zshrc` only runs for interactive shells (you opening a terminal). So if your ticket
expires and you haven't opened a new terminal, Cursor's SSH will prompt for a password.

**Why cron isn't enough on macOS:** macOS cron does not run missed jobs after sleep. If your Mac
sleeps overnight, cron misses its window and the ticket expires. launchd catches up on wake.

**Both together = always works.**

---

## Step-by-step init

### Part A: Create the keytab on a SNAP server

#### A1. SSH into a SNAP server from a Mac terminal

Open **Terminal.app** (not Claude Code — you need an interactive terminal for password input).

```bash
kinit brando9@CS.STANFORD.EDU
```
Type your Stanford password when prompted. Then:

```bash
ssh brando9@skampere1.stanford.edu
```

#### A2. Run `ktutil` (interactive program)

**Important:** `ktutil` is an interactive program with its own prompt (`ktutil:`). You type commands inside it one at a time. It is NOT a one-liner.

```bash
ktutil
```

You should now see:
```
ktutil:
```

#### A3. Add your credentials

At the `ktutil:` prompt, type this **all on one line** and press Enter:

```
addent -password -p brando9@CS.STANFORD.EDU -k 1 -e aes256-cts
```

If `aes256-cts` doesn't work, try the full name:
```
addent -password -p brando9@CS.STANFORD.EDU -k 1 -e aes256-cts-hmac-sha1-96
```

It will say:
```
Password for brando9@CS.STANFORD.EDU:
```

Type your Stanford password and press Enter. **You won't see characters as you type — that's normal.**

#### A4. Save the keytab to a file

Still at the `ktutil:` prompt:

```
wkt /lfs/skampere1/0/brando9/.keytab
```

No output means success.

> **Note:** The path uses your server's local filesystem. If your home dir is different
> (check with `echo $HOME`), use that path instead.

#### A5. Quit ktutil

```
quit
```

You're back at the normal shell prompt.

#### A6. Lock down permissions and verify

```bash
chmod 600 ~/.keytab
ls -la ~/.keytab
```

You should see `-rw-------` permissions and a non-zero file size.

#### A7. Test that the keytab works on the server

```bash
kinit -kt ~/.keytab brando9@CS.STANFORD.EDU
klist
```

You should see a valid ticket with no password prompt. If this fails, the keytab wasn't created correctly — go back to A2.

#### A8. Exit the server

```bash
exit
```

---

### Part B: Copy the keytab to your Mac

Back on your Mac terminal.

**Try scp first:**

```bash
scp brando9@skampere1.stanford.edu:/lfs/skampere1/0/brando9/.keytab ~/.keytab
chmod 600 ~/.keytab
```

**If scp fails with "Received message too long":** This happens when the server's `.bashrc`
prints output during non-interactive sessions (e.g., a `pip install` line). Use base64 instead:

```bash
ssh -t brando9@skampere1.stanford.edu 'base64 ~/.keytab'
```

Ignore any `.bashrc` output (e.g., `Requirement already satisfied: ...`). Copy only the
base64-encoded string (looks like `BQIAAAB...AAAE=`), then on your Mac:

```bash
echo "PASTE_THE_BASE64_STRING_HERE" | base64 -d > ~/.keytab
chmod 600 ~/.keytab
```

**Test it works locally:**

```bash
kinit -kt ~/.keytab brando9@CS.STANFORD.EDU
klist
```

You should see a valid ticket.

---

### Part C: Set up auto-renewal on Mac

#### C1. Add to `~/.zshrc`

Add this near the top of `~/.zshrc` (replaces any old kinit block):

```bash
# Auto-renew Kerberos ticket if keytab exists (passwordless kinit for SNAP SSH)
if [[ -f ~/.keytab ]]; then
  kinit -kt ~/.keytab brando9@CS.STANFORD.EDU 2>/dev/null
fi
```

#### C2. Create launchd plist

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
        <string>/Users/brandomiranda/.keytab</string>
        <string>brando9@CS.STANFORD.EDU</string>
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

#### C3. Load the launchd agent

```bash
launchctl load ~/Library/LaunchAgents/com.stanford.kinit-renew.plist
```

#### C4. Verify everything

```bash
# Check launchd is running:
launchctl list | grep kinit

# Check you have a valid ticket:
klist

# Test passwordless SSH:
ssh brando9@skampere1.stanford.edu echo "SUCCESS - no password needed"
```

---

### Part D: Verify with Cursor

1. Open Cursor
2. Connect to a SNAP server via Remote SSH
3. It should connect **without a password prompt**
4. Close the window, reopen — should reconnect without a password prompt

---

### Part E: Server-side auto-renewal (eliminates krbtmux/reauth)

Parts A-D handle the **Mac side** (SSH login). But server-side tickets also expire after ~10h,
breaking AFS access in tmux/byobu/Cursor sessions. This part auto-renews server-side tickets.

**What was deployed:**
1. **Keytab on DFS:** `/dfs/scratch0/brando9/.keytab` (accessible from all nodes)
2. **`krenew.sh` script:** `/dfs/scratch0/brando9/bin/krenew.sh` — runs `kinit -kt` + `aklog`
3. **`.bashrc` background loop:** Runs `krenew.sh` on login + spawns a PID-guarded loop every 4h
4. **Cron (secondary):** `0 */4 * * *` on each node as backup

**Result:** All sessions (tmux, byobu, Cursor, background jobs) have valid Kerberos tickets
and AFS tokens forever. No more `krbtmux` or `reauth` needed.

**Logs:** `/tmp/krenew_brando9.log` on each server.

**Verify on any node:**
```bash
klist                              # valid ticket
cat /tmp/krenew_brando9.pid        # PID exists
ps -p $(cat /tmp/krenew_brando9.pid)  # process alive
tail -3 /tmp/krenew_brando9.log    # recent OK entries
```

See `~/agents-config/todo_infinite_reauth_kinit_server_side.md` for full details.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ktutil: addent` says "unknown enctype" | Try `-e aes256-cts` (short) or `-e aes128-cts-hmac-sha1-96` or `-e arcfour-hmac` |
| `kinit -kt` says "Key table entry not found" | Keytab was created with wrong principal or enctype. Redo Part A. Check server's supported enctypes with `klist -e` |
| `scp` says "Received message too long" | Server `.bashrc` prints output on non-interactive login (e.g., `pip install nvidia-htop`). Use the base64 workaround in Part B instead. Long-term fix: wrap the noisy line in `.bashrc` with `if [[ $- == *i* ]]; then ... fi` so it only runs interactively |
| `scp` can't find the keytab | Check your home dir: `ssh brando9@skampere1.stanford.edu 'echo $HOME'` and use that path |
| launchd isn't running | Check: `launchctl list \| grep kinit`. If missing: `launchctl load ~/Library/LaunchAgents/com.stanford.kinit-renew.plist` |
| Ticket expires overnight | Verify launchd is loaded (not just cron). Check `/tmp/kinit-renew.err` for errors |
| Changed Stanford password | Regenerate the keytab — redo Part A and Part B |

---

## What was configured

After completing this guide, these files were created or modified:

| File | What | Where |
|---|---|---|
| `~/.keytab` | Kerberos keytab (equivalent to your password — protect it) | Mac |
| `~/.zshrc` | kinit snippet for interactive shells | Mac |
| `~/Library/LaunchAgents/com.stanford.kinit-renew.plist` | launchd auto-renewal every 4h | Mac |
| `~/.ssh/config` | GSSAPI + ControlMaster for `*.stanford.edu` | Mac |
| `~/.keytab` | Kerberos keytab (copy) | SNAP server |

## Security notes

- The keytab is **equivalent to your password in a file**. Protect it like `~/.ssh/id_rsa`.
- If you change your Stanford password, you **must** regenerate the keytab (redo Part A + B).
- Check with Stanford CS IT if keytab usage is allowed — some orgs restrict self-service keytabs.
