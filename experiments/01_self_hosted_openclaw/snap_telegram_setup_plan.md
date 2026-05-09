# OpenClaw on SNAP — Telegram-Bridged Self-Hosted Agent on a GPU Node

**TLDR:** Step-by-step deployment plan for installing OpenClaw on a SNAP GPU node (default: `mercury2`) so Brando can DM a Telegram bot from his phone and have an agent run on the lab GPU box. Expands [`MASTER_PLAN.md`](./MASTER_PLAN.md) **Phase 4** (4-step stub) into a concrete, executable runbook covering host selection, DFS-backed install layout, the missing Linux installer, Telegram bot creation, Kerberos + reboot survival, smoke tests, and rollback. Sister doc to [`scripts/install_openclaw_instance.sh`](./scripts/install_openclaw_instance.sh) (macOS) — the missing Linux counterpart is **deliverable #1** of this plan.

> **Why this lives here.** This is OpenClaw instance #3 (after Air + Pro). Same architecture, same `bots.yaml` + `openclaw-ops` channel ([`chatops.md`](./chatops.md)), same idempotency story. The reason it needs its own doc is that SNAP is **Linux + DFS + no launchd + Slurm-migration-volatile**, so the macOS install script doesn't transfer.

---

## 1. Decisions to confirm before starting

| # | Decision | Default (this plan assumes) | Alternatives |
|---|---|---|---|
| D1 | **Target node** | `mercury2` (per Phase 4) | `skampere1` (8× A100, also non-Slurm-gated). Avoid: `hyperturing2`, `turing3`, `ampere1–9`, `blackwell1` (Slurm-gated → daemon needs `sbatch` wrapper). |
| D2 | **GPU usage by OpenClaw itself** | None — agent runs CPU-only; the node's GPUs stay free for training jobs | If we later want a local LLM as fallback, reserve 1× GPU and pin via `CUDA_VISIBLE_DEVICES`. Out of scope for v1. |
| D3 | **Install script shape** | Sibling `install_openclaw_instance_linux.sh` (per [`MASTER_PLAN.md`](./MASTER_PLAN.md) §9 open decision #2) | Add a `case "$(uname -s)"` branch to the existing macOS script. Default is sibling — keeps each script readable and matches what `MASTER_PLAN.md` Phase 4.2 already proposes. |
| D4 | **State dir location** | `~/.openclaw → /dfs/scratch0/brando9/.openclaw` (DFS-backed symlink, mirrors `~/.claude` per `machine/snap.md:228`) | Keep `~/.openclaw` on LFS (node-local, faster but lost on node migration). DFS-backed wins because: (a) survives node reboot/reimage, (b) makes future node-swap a 1-line change, (c) consistent with `agents-config` and `~/.claude`. |
| D5 | **Daemon mechanism** | tmux session `openclaw-gateway` + watchdog while-loop + `@reboot` cron (per `machine/snap.md:108-113`) | systemd-user unit. Rejected: SNAP nodes don't reliably honor user-systemd; the existing watcher infra already uses tmux + cron and works. |
| D6 | **Heartbeat ID** | `mercury2-openclaw` (matches `chatops.md` schema) | — |
| D7 | **Bot per host** | Yes — third `@BotFather` bot `@ultimate_brando9_sk_mercury2_bot` (per [`concepts.md`](./concepts.md) Q1: shared token = 409 conflicts) | — |

**👤 Brando: confirm D1, D2, D3 before Step 4.2 fires.** Defaults are safe but worth a 30-second sanity check.

---

## 2. Prerequisites — what must be true before step 1

A row fails ⇒ STOP and fix that row first.

| Check | Command | Pass criterion |
|---|---|---|
| SSH to target node works | `ssh mercury2.stanford.edu hostname` | Prints `mercury2`, no host-key prompt |
| DFS scratch is mounted | `ssh mercury2 'ls /dfs/scratch0/brando9 \| head -3'` | Lists files (no `Stale file handle`) |
| `agents-config` checked out on DFS | `ssh mercury2 'ls /dfs/scratch0/brando9/agents-config/CLAUDE.md'` | Exists |
| Kerberos auto-renewal active | `ssh mercury2 'crontab -l \| grep krenew'` | One `0 */4 * * * .../krenew.sh` line present (per `machine/snap.md:108-113`) |
| Keytab present on DFS | `ssh mercury2 'stat -c %a /dfs/scratch0/brando9/.keytab'` | `600` |
| Node 22.14+ available | `ssh mercury2 'source ~/.bashrc && node --version'` | `v22.14.x` or `v24.x` (via NVM, per `machine/snap.md:160`) |
| `codex` CLI logged in | `ssh mercury2 'source ~/.bashrc && codex whoami'` | Returns Brando's account, not `not logged in` |
| Telegram bot token file | `ssh mercury2 'stat -c %a ~/keys/openclaw_telegram_bot_token.txt'` | `600` (created in Step 4.1 — initially absent, will be added) |

⚠ **If `mercury2` ever migrates behind `pam_slurm_adopt`** (per `machine/snap.md:81-103` table), this plan needs a `sbatch --time=∞` wrapper. As of 2026-04-24 mercury2 is open. Re-check before you start.

---

## 3. End-state architecture (one picture)

```
┌──────────────────────── Brando's phone ────────────────────────┐
│  Telegram  →  @ultimate_brando9_sk_mercury2_bot  (per-host)    │
└────────────────────────────────┬───────────────────────────────┘
                                 │  long-poll (one process per token)
                                 ▼
┌──────────────────────── mercury2.stanford.edu ─────────────────┐
│                                                                │
│  tmux session: openclaw-gateway                                │
│    └─ openclaw gateway  (port 18789, loopback only)            │
│       └─ codex harness (gpt-5.5, model_reasoning_effort=xhigh) │
│                                                                │
│  cron:                                                         │
│    0 */4 * * *  krenew.sh                # K5 ticket refresh   │
│    @reboot      start_openclaw_at_reboot.sh                    │
│    */15 * * * * openclaw cron run heartbeat-mercury2           │
│                                                                │
│  paths:                                                        │
│    ~/.openclaw → /dfs/scratch0/brando9/.openclaw  (state, DFS) │
│    ~/openclaw  → /dfs/scratch0/brando9/openclaw   (code, DFS)  │
│    ~/keys/openclaw_telegram_bot_token.txt         (LFS, 600)   │
│                                                                │
└─────────────┬──────────────────────────────────┬───────────────┘
              │                                  │
              ▼                                  ▼
        ┌──────────────┐                ┌──────────────────┐
        │ Gmail (gog)  │                │  openclaw-ops    │
        │  brando9@cs  │                │  (TG channel,    │
        └──────────────┘                │   shared by all  │
                                        │   3 instances)   │
                                        └──────────────────┘
```

**Why the gateway binds loopback-only:** SNAP nodes are reachable from anywhere on the Stanford network. Binding to `0.0.0.0` would expose the gateway's auth token surface to every other CS user. Loopback + `auth.mode=token` keeps it locked down; the only entry path is Telegram.

---

## 4. Steps

Each step has an owner (👤 = Brando, 🤖 = Claude), an ETA, and a "done when" condition. Ordering matters — don't skip ahead.

### Step 4.1 — 👤 Brando: create the mercury2 Telegram bot ⏱ 5 min

1. Open Telegram → `@BotFather` → `/newbot`.
2. Name: `Brando OpenClaw mercury2`. Username: `ultimate_brando9_sk_mercury2_bot`.
3. Copy the token. On any machine with SSH to mercury2:
   ```bash
   ssh mercury2 'mkdir -p ~/keys && umask 077 && cat > ~/keys/openclaw_telegram_bot_token.txt' <<< 'PASTE_TOKEN_HERE'
   ssh mercury2 'chmod 600 ~/keys/openclaw_telegram_bot_token.txt && wc -c ~/keys/openclaw_telegram_bot_token.txt'
   ```
   Expect ~46 bytes printed.
4. In Telegram: open the existing private `openclaw-ops` channel → Manage Channel → Administrators → add `@ultimate_brando9_sk_mercury2_bot` with **Post Messages** permission only.
5. DM the new bot once (`/start`). Don't expect a reply yet — gateway isn't running. The DM just unlocks the bot's ability to message you back later.

**Done when:** `~/keys/openclaw_telegram_bot_token.txt` exists on mercury2 with mode 600.

---

### Step 4.2 — 🤖 Claude: write `install_openclaw_instance_linux.sh` ⏱ 30 min

Sibling to the existing macOS installer, lives at `experiments/01_self_hosted_openclaw/scripts/install_openclaw_instance_linux.sh`. Differences from the macOS version:

| Concern | macOS does | Linux must do |
|---|---|---|
| Daemon | `launchd` plist + `launchctl bootstrap` | tmux session `openclaw-gateway` running watchdog while-loop |
| State dir | `~/.openclaw` (on internal SSD) | `~/.openclaw` symlinked to `/dfs/scratch0/brando9/.openclaw` (idempotent: `ln -sfn`) |
| Code dir | npm global → Homebrew prefix | npm global → NVM prefix (per `machine/snap.md:160`); the install lands under `$NVM_DIR/versions/node/<v>/lib/node_modules/openclaw` |
| Permission file | `chmod 600` on `openclaw.json` | same |
| Cert fix | macOS-only `cafile=/etc/ssl/cert.pem` | skip (Linux uses system CA bundle by default) |
| Reboot survival | `RunAtLoad` in plist | `@reboot` cron entry calling `start_openclaw_at_reboot.sh` |
| Kerberos | n/a | rely on existing `0 */4 * * * krenew.sh` (already installed per `machine/snap.md:108-113`) |
| stdin to gateway | child of launchd (no tty) | `tmux new-session -d -s openclaw-gateway` |
| Slurm awareness | n/a | exit early with a clear error if the node is gated (`groups | grep -q slurm` heuristic) |

The script reuses the existing `openclaw.json.template` rendering Python block from the macOS installer verbatim — only the daemon-installation tail differs.

Companion script `start_openclaw_at_reboot.sh` (also new):
```bash
#!/usr/bin/env bash
# Re-launch openclaw gateway in tmux after node reboot.
# Logs to /tmp/start_openclaw_at_reboot_<host>.log so failures are recoverable.
set -euo pipefail
LOG="/tmp/start_openclaw_at_reboot_$(hostname -s).log"
exec >>"$LOG" 2>&1
echo "=== $(date -Is) start_openclaw_at_reboot ==="

# 1. wait for DFS to come up (mirrors machine/snap.md pattern)
for i in $(seq 1 60); do
  [[ -d /dfs/scratch0/brando9 ]] && break
  sleep 5
done
[[ -d /dfs/scratch0/brando9 ]] || { echo "DFS never came up; aborting"; exit 1; }

# 2. refresh Kerberos before doing anything that touches AFS/DFS-protected paths
/dfs/scratch0/brando9/bin/krenew.sh || true

# 3. launch gateway in tmux (idempotent — kill old session first)
source ~/.bashrc
tmux kill-session -t openclaw-gateway 2>/dev/null || true
tmux new-session -d -s openclaw-gateway "openclaw gateway run 2>&1 | tee -a ~/.openclaw/logs/gateway-$(date +%F).log"
echo "=== launched ==="
```

**Done when:** the new script exists, is `chmod +x`, and a `bash -n` syntax check passes.

---

### Step 4.3 — 🤖 Claude: prepare DFS layout on mercury2 ⏱ 5 min

```bash
ssh mercury2 bash -lc '
  set -euo pipefail
  mkdir -p /dfs/scratch0/brando9/.openclaw/logs
  ln -sfn /dfs/scratch0/brando9/.openclaw ~/.openclaw       # state on DFS
  mkdir -p /dfs/scratch0/brando9/openclaw                   # code on DFS (npm prefix override below if needed)
  ln -sfn /dfs/scratch0/brando9/openclaw ~/openclaw         # convenience symlink
  ls -la ~/.openclaw ~/openclaw
'
```

**Done when:** both symlinks resolve to `/dfs/scratch0/brando9/...`.

---

### Step 4.4 — 🤖 Claude: copy gogcli auth from Air ⏱ 5 min

Per `MASTER_PLAN.md` Step 4.3 — different OS path:

```bash
# from the Air (instance #1):
scp ~/.config/gogcli/credentials.json mercury2:.config/gogcli/credentials.json   # NB: macOS path is ~/Library/Application Support/gogcli/
ssh mercury2 'chmod 600 ~/.config/gogcli/credentials.json && gog gmail list --max-results 1'
```

If the path differs on the Air's macOS install (typically `~/Library/Application Support/gogcli/`), adjust the source side. The destination path on Linux is always `~/.config/gogcli/` per XDG.

**Done when:** `gog gmail list` on mercury2 returns ≥1 message.

---

### Step 4.5 — 🤖 Claude: run the Linux installer ⏱ 5 min

```bash
ssh mercury2 bash -lc '
  cd ~/agents-config && git pull --ff-only
  bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/install_openclaw_instance_linux.sh
'
```

**What the script does (executable summary of Step 4.2's spec):**
1. Pre-flight (node version, codex login, keytab, token file mode).
2. `npm install -g openclaw@latest` under NVM.
3. `openclaw onboard --non-interactive --accept-risk` to seed config dir.
4. Render `~/.openclaw/openclaw.json` from `config/openclaw.json.template` (preserving any existing per-host gateway token).
5. Install + register `start_openclaw_at_reboot.sh` in cron.
6. Start tmux session immediately (so we don't have to reboot to validate).
7. Smoke test: `openclaw infer model run --gateway --prompt "say only the word PONG"`.

**Done when:** the script exits 0 and prints `✓ smoke test passed`.

---

### Step 4.6 — 🤖 Claude: register the heartbeat cron ⏱ 5 min

```bash
ssh mercury2 bash -lc '
  openclaw cron add \
    --id heartbeat-mercury2 \
    --cron "*/15 * * * *" \
    --action "send-channel" \
    --channel telegram \
    --target openclaw-ops \
    --message "[mercury2-openclaw] alive @ \$(date -u +%FT%TZ)"
  openclaw cron list | grep heartbeat-mercury2
'
```

**Done when:** within 15 min, `openclaw-ops` channel shows `[mercury2-openclaw] alive @ ...`.

---

### Step 4.7 — 👤 Brando: pair the bot ⏱ 3 min

DM `@ultimate_brando9_sk_mercury2_bot` and follow the prompt. If pairing requires a code:
```bash
ssh mercury2 'openclaw pairing approve telegram <CODE>'
```

Then send a test DM: `what host are you on?` → expect a reply that says `mercury2` and includes hostname/uptime.

**Done when:** Brando gets a coherent reply from the bot DM.

---

### Step 4.8 — 🤖 Claude: SNAP-specific hardening ⏱ 20 min

Per `MASTER_PLAN.md` Step 4.4 + lessons from `machine/snap.md`:

1. **Verify krenew cron is present** (don't add if it already exists — `machine/snap.md:108-113` shows the canonical line):
   ```bash
   ssh mercury2 'crontab -l | grep -E "krenew|start_openclaw_at_reboot"'
   ```
   Expect both lines.

2. **logrotate config** at `~/.openclaw/logs/logrotate.conf`:
   ```
   /dfs/scratch0/brando9/.openclaw/logs/*.log {
       daily
       rotate 14
       compress
       missingok
       notifempty
       copytruncate
   }
   ```
   Add to user crontab: `5 4 * * * /usr/sbin/logrotate -s ~/.openclaw/logs/.logrotate.state ~/.openclaw/logs/logrotate.conf`.

3. **tmux watchdog**: a 30-line bash script that loops `until tmux has-session -t openclaw-gateway; do tmux new-session -d -s openclaw-gateway 'openclaw gateway run'; sleep 30; done`. Wire it as `*/2 * * * *` so a crashed gateway respawns within 2 min. (Equivalent of `openclaw-health-watcher.sh` but Linux-flavored.)

4. **Document Slurm-migration risk** in this file's §6 "Status & Log" — if mercury2 gets gated, the watchdog will fail silently after the next reboot since cron jobs can't `ssh` into a Slurm-only node.

**Done when:** `crontab -l` on mercury2 shows krenew + reboot + logrotate + watchdog (4 lines), and a manual `tmux kill-session -t openclaw-gateway` triggers respawn within 2 min.

---

### Step 4.9 — 🤖 Claude + 👤 Brando: end-to-end proof ⏱ 10 min

Three round-trips, all from Brando's phone:

1. **Liveness:** DM the bot `status` → reply names mercury2 and lists current load.
2. **Email round-trip:** DM `triage my admin emails` → bot picks the oldest unread admin email, drafts a reply, asks for `approve`. Brando says `approve` → bot sends → confirms `sent at <ts>`.
3. **Channel visibility:** check `openclaw-ops` — heartbeat from mercury2 visible alongside Air + Pro.

**Done when:** all three pass without manual intervention.

---

## 5. Test plan / DoD

Lift directly from `MASTER_PLAN.md` Phase 5 but scoped to mercury2:

- [ ] mercury2 heartbeats every 15 min for 7 consecutive days, no gaps >30 min
- [ ] `tmux kill-session -t openclaw-gateway` triggers respawn within 2 min (verified once during week)
- [ ] Node reboot (or simulated: `tmux kill-server`) recovers within 5 min via `@reboot` cron
- [ ] No double-sends across Air/Pro/mercury2 (Gmail label idempotency catches it — same as Phase 2)
- [ ] Brando triages ≥3 real admin emails *via the mercury2 bot specifically* (not just Air)

If any item fails for >24h: roll back per §7.

---

## 6. Status & Log

Append-only. New entries on top.

| Date | Owner | Note |
|---|---|---|
| 2026-05-09 | Claude | Plan drafted in branch `claude/telegram-snap-setup-plan-0zMqQ`. Awaiting Brando approval of D1–D7 before Step 4.1 fires. |

---

## 7. Rollback

If the experiment goes sideways (gateway in crashloop, eating CPU on mercury2, or Slurm migration breaks reboot survival):

```bash
ssh mercury2 bash -lc '
  tmux kill-session -t openclaw-gateway 2>/dev/null || true
  crontab -l | grep -vE "openclaw|start_openclaw_at_reboot" | crontab -
  # State preserved at ~/.openclaw — uninstall is reversible by undoing the crontab edits.
  npm uninstall -g openclaw   # optional; leaves room to redeploy later
'
```

Notify the `openclaw-ops` channel manually: `[mercury2-openclaw] DECOMMISSIONED <date> <reason>`. Air + Pro continue covering Brando's triage load.

---

## 8. Cross-references

- Master plan (Phase 4 stub this expands): [`MASTER_PLAN.md`](./MASTER_PLAN.md) §6 Phase 4
- Why per-host bots: [`concepts.md`](./concepts.md) Q1
- Why heartbeats + ops layer: [`concepts.md`](./concepts.md) Q2 + Q3
- Fleet management once mercury2 lands: [`chatops.md`](./chatops.md) (`bots.yaml` registry adds a `mercury2-openclaw` entry)
- SNAP filesystem + reboot + Kerberos playbook: [`../../machine/snap.md`](../../machine/snap.md)
- Existing watcher pattern this borrows from: `machine/snap.md:104-120` (`launch_watcher_remote.sh` + `start_watcher_at_reboot.sh`)
- Keytab one-time setup: [`../../init_no_passwords_snap_kinit.md`](../../init_no_passwords_snap_kinit.md)
- macOS installer to mirror: [`scripts/install_openclaw_instance.sh`](./scripts/install_openclaw_instance.sh)
- Phase 4 TODO checkboxes this drives: [`TODO.md`](./TODO.md) §"Phase 4 — replicate to mercury2"
