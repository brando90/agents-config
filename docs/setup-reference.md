# Setup and migration reference

**Doc link:** <https://github.com/brando90/agents-config/blob/main/docs/setup-reference.md>

**TLDR:** Detailed host and migration recipes moved from the main README. Load
only the relevant section; current shared rules and maintained machine/workflow
guides take precedence over older operational examples.

This is an operator reference, not a startup instruction file. Procedures were
preserved from the earlier README on 10-04-2026; the move does not establish
that every old command still matches an installed client. Check the active
account, profile, host, and current documentation before applying a recipe.
Commands with repository-relative paths assume `cd ~/agents-config`.

For entrypoint installation that preserves existing files, use the
[short quick start](../README.md#quick-start). For client discovery and current
scope, use [the instruction audit](instruction-audit/README.md) and
[CATALOG.md](../CATALOG.md). References are on demand; do not eagerly import
this whole document into an agent's startup context.

## Reusable macOS AI App Setup

For each Mac, first use [`~/agents-config/machine/macos-ai-apps/ai_agent_automatable_setup_codex_clauded.md`](../machine/macos-ai-apps/ai_agent_automatable_setup_codex_clauded.md) to configure shell-automatable trusted-agent setup, then use [`~/agents-config/machine/macos-ai-apps/manual_macos_permissions_checklist_ai_apps.md`](../machine/macos-ai-apps/manual_macos_permissions_checklist_ai_apps.md) for the macOS Privacy & Security toggles that require manual approval.

---

## New Server Setup

Setting up a new SNAP node? See [`machine/snap-init.md`](../machine/snap-init.md) -- copy-paste prompt that checks/fixes all symlinks, auth, tools, keys, and GPUs on a fresh SNAP node.

**Important convention:** On SNAP, all project directories under `~/` (LFS) must be **symlinks** to their canonical location on `/dfs/scratch0/<user>/`. For example, `~/veribench` → `/dfs/scratch0/brando9/veribench`. This ensures every server sees the same repo state. Never clone or copy repos directly to LFS. See [`machine/snap.md`](../machine/snap.md) for details.

### OpenClaw self-healing watcher (per host)

Brando's OpenClaw bots must be alive 24/7. `launchd KeepAlive` only catches process death — it doesn't catch a stuck agent session or a half-installed plugin cache (the kind of failure where the bot delivers ✓✓ but never replies). Install the self-healing watcher on every host that runs OpenClaw:

```bash
# 1. Run the script every 5 min via launchd (macOS) or cron (Linux); see
#    install instructions at the bottom of:
sh ~/agents-config/experiments/01_self_hosted_openclaw/scripts/openclaw-health-watcher.sh
#    The script: checks gateway is up + Telegram is `running, connected`
#    + PONG round-trip works. On failure it escalates: restart → full
#    reset (clear plugin-runtime-deps + reload) → DM openclaw-ops if it
#    still can't recover.

# 2. Pre-grant macOS TCC prompts once per host so the agent is fire-and-forget:
sh ~/agents-config/experiments/01_self_hosted_openclaw/scripts/pre-grant-tcc-automation.sh
```

Full design + decision tree: [`experiments/01_self_hosted_openclaw/MASTER_PLAN.md`](../experiments/01_self_hosted_openclaw/MASTER_PLAN.md) §A.0.5 (TCC pre-grants), §A.6 (gotchas), §A.8 (triage flow when bot stops replying).

### OpenClaw on a new SNAP / Linux node — fast path

> **Historical recipe — not authorized execution.** This retained setup uses an
> Anthropic provider key and predates the current command-line-only policy.
> Hard Rule 9 forbids agents from treating these instructions as permission to
> run direct model-provider calls. Preserve the historical reference; use the
> maintained client/dispatch workflows for current work. Any user-owned legacy
> script that loads provider keys requires the rule's explicit spending review
> and confirmation before execution.

<details>
<summary>Earlier OpenClaw Linux procedure (historical only)</summary>

The Linux install path is automated. From a fresh SNAP node (after the standard SNAP node setup has run):

```bash
# 1. Create a per-host bot via @BotFather on Telegram. /newbot, name it after
#    the host (e.g. ubrando_<HOST>_bot). Copy the token — DO NOT paste it
#    anywhere that gets recorded (chat logs, screenshots), and if it leaks,
#    /revoke + /token to rotate before continuing.
#    Why per-host: one bot can only be long-polled by one process. Sharing
#    causes HTTP 409 conflicts that drop messages — see:
#    experiments/01_self_hosted_openclaw/concepts.md Q1.

# 2. Drop the token on the host (mode 600):
printf '%s\n' '<TOKEN-FROM-BOTFATHER>' > ~/keys/openclaw_telegram_bot_token.txt
chmod 600 ~/keys/openclaw_telegram_bot_token.txt

# 3. Make sure these prereqs are in place:
#      - Node 22.14+ (SNAP installs nvm to /dfs/scratch0/<user>/.nvm — already loaded by .bashrc)
#      - codex CLI logged in: codex login   (interactive ChatGPT OAuth)
#      - tmux on PATH
#      - ~/keys/anthropic_api_key.txt (the Linux installer pins anthropic/claude-haiku-4-5
#        as default model since openai-codex chatgpt-OAuth is currently flaky on Linux)

# 4. Run the installer:
bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/install_openclaw_instance_linux.sh
#    What it does: npm install openclaw, install the @openclaw/codex plugin,
#    render ~/.openclaw/openclaw.json from the template, write a tmux respawn
#    wrapper + an @reboot wrapper (waits for DFS, runs krenew first), launch
#    the gateway in tmux session 'openclaw-gateway', install both cron entries
#    (@reboot + 5-min health-watcher), and PONG-test through the gateway.

# 5. Manual finish on Telegram:
#    Open Telegram → search the new bot → /start → if OpenClaw asks for a
#    pairing code: 'openclaw pairing approve telegram <CODE>'.

# 6. Quick verification (try these from the bot DM):
#    hostname && pwd && nvidia-smi --list-gpus | head -1
#    ssh skampere1.stanford.edu 'nvidia-smi --query-gpu=name,memory.free --format=csv,noheader | head -2'
```

Restart / recovery (any host):

```bash
# Tail the live log:
tail -f ~/openclaw/gateway.log

# Force a restart (the respawn wrapper rebuilds within 5s):
tmux kill-session -t openclaw-gateway

# Manually re-run the health-watcher to trigger self-heal logic:
bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/openclaw-health-watcher.sh

# Hit gateway health directly (loopback only):
curl -s http://127.0.0.1:18789/health
```

Architecture summary: gateway runs in `tmux new-session -d -s openclaw-gateway` wrapped by `~/openclaw/run_gateway_respawn.sh` (a `while true; do openclaw gateway run --force; sleep 5; done` loop). `@reboot` cron starts a fresh tmux session after a node reboot once DFS is mounted and Kerberos has been renewed via the keytab (same pattern as the DFS job-queue watcher in [`machine/snap.md`](../machine/snap.md)). The 5-min cron runs the cross-platform health-watcher which checks gateway → Telegram-connected → PONG round-trip and self-heals via restart → full plugin-cache reset → DM `openclaw-ops` on give-up.

---

</details>

## Remote Access (Claude Remote Control & Codex)

### Claude Remote Control — setup

Remote Control (RC) lets you hand off a Claude Code session to your phone or another device via `claude.ai/code`. It requires a **full claude.ai login** — long-lived env vars like `CLAUDE_CODE_OAUTH_TOKEN` block RC.

#### Mac (zsh + Cursor)

Cursor injects `CLAUDE_CODE_OAUTH_TOKEN` into its terminal env. tmux/byobu sessions started from Cursor inherit it, silently blocking RC.

**One-time fix** — add to `~/.zshrc`:

```bash
# Strip Cursor-injected CLAUDE_CODE_OAUTH_TOKEN inside tmux/byobu — blocks RC
if [ -n "$TMUX" ]; then
  unset CLAUDE_CODE_OAUTH_TOKEN
fi
```

Also make sure `CLAUDE_CODE_OAUTH_TOKEN` is NOT exported anywhere in `~/.zshrc` or `~/.zprofile`:

```bash
# Check:
grep -n 'CLAUDE_CODE_OAUTH_TOKEN' ~/.zshrc ~/.zprofile 2>/dev/null
# Any uncommented export lines → comment them out
```

Then auth (one-time):

```bash
claude auth logout
claude auth login        # signs in via browser
claude auth status --text  # verify: "Claude Max Account", no env overrides
claude remote-control    # success = Environment ID + claude.ai/code URL
```

#### SNAP servers (bash + DFS)

On SNAP, shell config lives at `/dfs/scratch0/<user>/.bashrc` (shared across all nodes via symlink). Fix it **once on DFS** and all servers get it.

**Step 1 — Remove `CLAUDE_CODE_OAUTH_TOKEN` from `.bashrc`:**

```bash
DFS="/dfs/scratch0/brando9"

# Find it
grep -n 'CLAUDE_CODE_OAUTH_TOKEN' "${DFS}/.bashrc"

# Comment it out (if found)
sed -i 's/^export CLAUDE_CODE_OAUTH_TOKEN/#export CLAUDE_CODE_OAUTH_TOKEN/' "${DFS}/.bashrc"
```

**Step 2 — Add tmux guard to `.bashrc`:**

Add this block to `${DFS}/.bashrc` (works for krbtmux, tmux, byobu):

```bash
# Strip CLAUDE_CODE_OAUTH_TOKEN inside tmux/byobu/krbtmux — blocks Remote Control
if [ -n "$TMUX" ]; then
  unset CLAUDE_CODE_OAUTH_TOKEN
fi
```

**Step 3 — Auth (one-time, from any server):**

```bash
source ~/.bashrc
claude auth logout
claude auth login
# No browser on server — copy the URL, open on Mac/phone, sign in, paste code back
claude auth status --text  # verify: "Claude Max Account", no env overrides
```

**Step 4 — Share auth across all nodes via DFS:**

Claude stores credentials in `~/.claude/`. On SNAP, `$HOME` is per-server LFS, so auth is per-server by default. Fix by symlinking `~/.claude/` to DFS:

```bash
# On the FIRST server (after claude auth login succeeds):
mv ~/.claude "${DFS}/.claude"
ln -sfn "${DFS}/.claude" ~/.claude

# On every OTHER server (or in new-node setup):
rm -rf ~/.claude
ln -sfn "${DFS}/.claude" ~/.claude
```

**Step 5 — Start RC:**

```bash
# For persistent sessions, use krbtmux first:
/afs/cs/software/bin/krbtmux
/afs/cs/software/bin/reauth

# Then start RC inside the tmux session:
claude remote-control
# Open claude.ai/code on phone/Mac to connect
```

<a id="codex--no-rc-equivalent-use-tmux"></a>
### Codex remote interaction and durable execution

The earlier claim that Codex has no Remote Control equivalent is retired;
see [official Codex Remote documentation](https://learn.chatgpt.com/docs/remote).
For current host setup, use [the maintained Mac guide](../machine/mac.md) and
[remote dispatch workflow](../workflows/remote-job-dispatch.md). Inspect the actual
client's supported tools and current official documentation before selecting
remote interaction. A persistent terminal session remains an execution option,
not a statement about which remote interfaces the client supports.

### Other providers and the deprecated Gemini CLI

Do not revive the deprecated Gemini CLI as an untested fallback. The master may select Google models through a working supported subscription client, or Cursor-hosted models, Grok and other providers, after verifying the target client, exact model/effort, tools and subscription-only billing under [Rule 48](../workflows/reliable-agent-dispatch.md). Codex and Claude remain the preferred reviewers; the [acceptance policy](../workflows/qa-correctness.md#review-fallback-and-acceptance) preserves mandatory families and capability. A provider name alone neither establishes access nor authorizes API keys or paid credits.

### Server rollout checklist

```
[ ] Comment out CLAUDE_CODE_OAUTH_TOKEN in DFS .bashrc (one edit, all servers)
[ ] Add tmux guard (unset inside TMUX) to DFS .bashrc
[ ] Remove primaryApiKey from ~/.claude/config.json (forces API mode, blocks RC)
[ ] claude auth login (once, from any server — DFS shares it)
[ ] Symlink ~/.claude/ → DFS on each server
[ ] Verify: claude auth status --text (no env overrides)
[ ] Accept workspace trust: run `claude` in the working directory, accept the trust dialog, then exit
[ ] Start: claude remote-control
[ ] Mac: add tmux guard to ~/.zshrc, verify RC works in tmux
[ ] For Codex: choose ChatGPT login or API key, run inside tmux
```

### Troubleshooting Remote Control

RC can fail silently for several reasons. Use this diagnostic sequence:

**1. Check env vars in your current shell:**

```bash
test -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && echo "TOKEN=unset" || echo "TOKEN=set"
test -z "${ANTHROPIC_API_KEY:-}" && echo "API_KEY=unset" || echo "API_KEY=set"
claude auth status --text
```

- If `TOKEN` is set → it overrides OAuth login and blocks RC. Fix: `unset CLAUDE_CODE_OAUTH_TOKEN`
- If auth status says authentication through the `CLAUDE_CODE_OAUTH_TOKEN` environment variable → same problem, token is taking priority
- If auth status says `Claude Max Account` → auth is fine, problem is elsewhere

**2. "Long-lived tokens are limited to inference-only":**

RC requires a browser-based OAuth login. This error means Claude is using either:
- `CLAUDE_CODE_OAUTH_TOKEN` env var (even if commented out in `.bashrc`, your current shell may still have it from before the fix)
- `primaryApiKey` in `~/.claude/config.json`

Fix:
```bash
# Remove API key from config
echo '{}' > ~/.claude/config.json

# Unset env var
unset CLAUDE_CODE_OAUTH_TOKEN

# Re-auth via browser
claude auth logout && claude auth login
```

**3. "Workspace not trusted":**

Claude must accept the workspace trust dialog before RC can start. Run `claude` (not `claude remote-control`) in the target directory, accept the trust prompt, then exit and retry `claude remote-control`.

**4. Cursor SSH / IDE-injected tokens:**

Cursor (and similar IDEs) inject `CLAUDE_CODE_OAUTH_TOKEN` into their terminal environment. This token persists for the lifetime of the SSH connection — even after you comment it out of `.bashrc`. Every terminal tab and child process inherits it.

Fix: **Reconnect the SSH extension** (or restart the IDE remote session) after editing `.bashrc`. Alternatively, run `unset CLAUDE_CODE_OAUTH_TOKEN` in each terminal before using `claude`.

**5. Full diagnostic one-liner:**

```bash
unset CLAUDE_CODE_OAUTH_TOKEN && echo '{}' > ~/.claude/config.json && claude auth status --text && claude remote-control
```

### Verify node setup

After setup, see [`machine/snap-init.md`](../machine/snap-init.md) for a paste-into-Claude-Code prompt that checks paths, symlinks, RC auth, tools, keys, and GPUs.

---

## DFS Job Queue (Running Experiments Across SNAP Nodes)

> ⚠ **SNAP Slurm access (audited 2026-09-03).** `ampere*`, `hyperturing*`, `turing*`, and `blackwell1` are present but gated by `pam_slurm_adopt`: start from `ilc.stanford.edu`, confirm `showaccount` lists `infolab`, then allocate the node with `srun`/`sbatch`. Direct SSH remains available on `mercury1/2` and `skampere1/2/3`. Run `bash ~/agents-config/scripts/snap_health.sh` before dispatch. See [`machine/snap.md`](../machine/snap.md) § "Slurm-gated nodes".

On SNAP's direct-SSH nodes, the DFS job queue lets you submit experiment scripts from **any one node** and have watchers on the other direct nodes pick them up and run them. Slurm-gated nodes require a scheduler-aware launcher and an active account association.

**How it works:**

1. Each SNAP node runs a **watcher daemon** (usually in tmux). The daemon polls `~/dfs/job_queue/pending/` every 15 seconds.
2. You (or an agent) **drop a script** into `pending/` from any node. Because `~/dfs/` is on the shared DFS, every node sees it immediately.
3. The first watcher to see the job **atomically claims it** (NFS-safe hardlink protocol — no double-execution even with multiple nodes racing) and moves it to `running/`.
4. The watcher **executes the script**, inheriting the host's environment (`CUDA_VISIBLE_DEVICES`, API keys, etc.). By default it runs in smart mode, wrapping the job in a coding agent that can diagnose failures and retry; final email is optional and reserved for explicitly tracked significant jobs. If no agent binary is available, it falls back to direct subprocess execution. Separately, there is a 48-hour wall-clock safety timeout and a 4-hour continuous GPU-idle kill.
5. When it finishes, the job moves to `completed/` (exit 0) or `failed/` (non-zero or timeout). Logs go to `logs/`.

**The key idea:** You log into one server, submit jobs, and walk away. The other servers are already listening. No coordinator, no scheduler, no manual SSH — just a shared directory and a simple protocol.

```
~/dfs/job_queue/
    pending/      ← drop jobs here (from any node)
    running/      ← claimed by a watcher (job.sh___<hostname>)
    completed/    ← exit 0
    failed/       ← exit != 0 or timeout
    logs/         ← per-job stdout+stderr
```

**Code:** [`ultimate-utils/py_src/uutils/job_scheduler_uu/`](https://github.com/brando90/ultimate-utils/tree/master/py_src/uutils/job_scheduler_uu) (scheduler, submitter, tmux launcher).
**Full usage guide:** [`workflows/remote-job-dispatch.md`](../workflows/remote-job-dispatch.md) (covers the DFS watcher alongside SSH fire-and-forget and phone git-inbox dispatch — start/stop commands, submit examples, atomic claim details).

### Keeping watchers alive: keytab + cron (no password prompt, ever)

Two failure modes can silently kill a watcher: (a) Kerberos/AFS ticket expiry (~10h) — outbound smtp/agent calls from inside the watcher start failing; (b) node reboot — the tmux session is gone. Both are neutralised by two cron entries on each watcher node, both pointing at scripts on shared DFS:

```
0 */4 * * * /dfs/scratch0/brando9/bin/krenew.sh                       # 4-hourly Kerberos+AFS renewal
@reboot     /dfs/scratch0/brando9/bin/start_watcher_at_reboot.sh      # waits for DFS, krenew, relaunch
```

**No password is ever entered** — `krenew.sh` does `kinit -kt /dfs/scratch0/brando9/.keytab brando9@CS.STANFORD.EDU`, which uses the **keytab** as proof of identity. The keytab is a one-time artifact derived from your Stanford password (created interactively via `ktutil` on a Mac terminal — see [`init_no_passwords_snap_kinit.md`](../init_no_passwords_snap_kinit.md) Part A). After it exists on DFS at `chmod 600`, every node and every cron invocation can refresh tickets without prompting. **An automation session (Claude Code, cron, Codex, etc.) never needs the password — it just needs read access to the keytab file.** If you change your Stanford password, the keytab becomes invalid until regenerated.

**Helper scripts** (all in `/dfs/scratch0/brando9/bin/`, shared across nodes):
- `krenew.sh` — `kinit -kt …; aklog`. Used by the 4-hourly cron and by `start_watcher_at_reboot.sh`.
- `launch_watcher_remote.sh` — auto-detects python, bootstraps deps, pins `--job-dir /dfs/scratch0/brando9/job_queue`, wraps in `tmux new-session -d -s job_watcher 'bash -c …'` so import errors show up in `logs/watcher_daemon_<host>.log` instead of vanishing.
- `start_watcher_at_reboot.sh` — boot wrapper: waits up to 5 min for DFS, runs `krenew.sh`, then `launch_watcher_remote.sh`. Logs to `/tmp/start_watcher_at_reboot_<host>.log`.

**Verify on a node:**
```bash
crontab -l | grep -E 'krenew|start_watcher'    # both lines present
klist                                          # ticket valid
tmux ls | grep job_watcher                     # watcher session up
ls /dfs/scratch0/brando9/job_queue/watchers/<host>.stanford.edu.heartbeat
```

---

## How to Integrate with Your Project Repos

Each project repo should have **two canonical entry points** (`~/your-project/CLAUDE.md` for Claude Code, `~/your-project/AGENTS.md` for Codex) that point to **two indexes**: the home-level `~/agents-config/INDEX_RULES.md` (environment context) and the project's own `~/your-project/docs/agent-docs/INDEX.md` (project-specific docs).

Project docs live in the repo so they're versioned with the code and available to anyone who clones it.

```
~/your-project/
├── CLAUDE.md                         ← points to BOTH indexes
├── AGENTS.md                         ← same for Codex
├── docs/
│   └── agent-docs/
│       ├── INDEX.md                  ← project-specific doc routing
│       ├── architecture.md           ← how the codebase is structured
│       ├── eval-pipeline.md          ← evaluation workflow docs
│       └── conventions.md            ← project-specific conventions
├── src/
└── tests/
```

Your project's `~/your-project/CLAUDE.md` looks like:

```markdown
# Project: your-project

Read the home-level agent index for environment context:
- `~/agents-config/INDEX_RULES.md`

Read the project-level agent index for project-specific docs:
- `~/your-project/docs/agent-docs/INDEX.md`
```

### Fork and customize

1. Fork this repo
2. Fill in `~/agents-config/machine/` with your actual machine specs (non-sensitive info). Reference existing config files (`~/.ssh/config`, `~/keys/`) for secrets — don't duplicate them.
3. Add your own workflow docs

---

## Migrating from a Monolithic CLAUDE.md

If you've been using Claude Code's `/init` command, each project already has a CLAUDE.md with project overview, build commands, architecture docs, and conventions all in one file. This section explains how to migrate that content into the three-layer architecture.

### What migration looks like

**Before** — one CLAUDE.md mixing global policy, project essentials, and task-specific procedures:
```
my-project/
└── CLAUDE.md    ← project overview, build commands, architecture, conventions, etc.
```

**After** — modular docs with shared environment context:
```
~/my-project/
├── CLAUDE.md                         ← short entry point for both indexes
├── AGENTS.md                         ← same reference for Codex
└── docs/agent-docs/
    ├── INDEX.md                      ← project doc routing
    ├── overview.md                   ← project overview + key entry points
    ├── build-and-dev.md              ← setup, build, test commands
    ├── architecture.md               ← codebase structure + key patterns
    └── conventions.md                ← project-specific conventions
```

### Step-by-step migration

#### 1. Back up your old CLAUDE.md

```bash
cd ~/my-project
cp CLAUDE.md CLAUDE.md.bak
```

#### 2. Triage the content

Read through your old CLAUDE.md and sort each section into one of these buckets:

| Bucket | Where it goes | Examples |
|:-------|:-------------|:---------|
| **Project-specific** | `~/my-project/docs/agent-docs/*.md` | Project overview, architecture, build commands, test commands, key entry points, dataset structure, experiment conventions |
| **Already in agent-config** | Drop it (`~/agents-config/` provides it) | Machine specs, SSH config, general workflow rules (explicit opt-in QA, worktrees), global rules (no secrets, verify before push) |
| **Cross-references to other repos** | `~/my-project/docs/agent-docs/` or drop | `@/path/to/other/CLAUDE.md` references — replace with a reference in your project INDEX.md if still needed |
| **Stale/outdated** | Drop it | Old experiment notes, deprecated commands, hardcoded model IDs that have changed |

#### 3. Create the project docs directory and split the content

```bash
mkdir -p ~/my-project/docs/agent-docs
```

Split your old CLAUDE.md into focused files. A typical project needs 2–4 files. **Do not over-split.** Leave an already concise, relevant project file intact; measure bytes and words as well as lines, and split only when the separation reduces irrelevant context.

**Suggested split for a typical research project:**

- **`overview.md`** — Project purpose (1–3 sentences), environment variables, key entry points
- **`build-and-dev.md`** — Setup, build, test, and lint commands
- **`architecture.md`** — Directory structure, core components, key patterns
- **`conventions.md`** — Only if there are project-specific rules (file naming, experiment layout, etc.)

#### 4. Create the project INDEX.md

```markdown
# INDEX.md — my-project

Load only the docs relevant to your current task.

## Docs

- [`overview.md`](overview.md) — project purpose, env vars, entry points
- [`build-and-dev.md`](build-and-dev.md) — setup, build, test commands
- [`architecture.md`](architecture.md) — codebase structure and key patterns
```

#### 5. Replace CLAUDE.md with the two-reference format

```markdown
# Project: my-project

Read the home-level agent index for environment context:
- `~/agents-config/INDEX_RULES.md`

Read the project-level agent index for project-specific docs:
- `~/my-project/docs/agent-docs/INDEX.md`
```

Create `~/my-project/AGENTS.md` with the same references for Codex. Do not add a case-only duplicate inside the repository; it cannot be checked out reliably on case-insensitive filesystems.

#### 6. Delete the backup

Once you've verified the migration, remove the backup:
```bash
rm ~/my-project/CLAUDE.md.bak
```

### Handling common patterns in old CLAUDE.md files

**`@/path/to/other/CLAUDE.md` references** (e.g., `@/dfs/scratch0/brando9/CLAUDE.md`):
These were used to pull in shared context from a cluster-level CLAUDE.md. Agent-config replaces this — the shared context now lives in `~/agents-config/machine/` and `~/agents-config/workflows/`. Drop the `@` reference.

**Machine-specific sections** (GPU setup, cluster paths, Docker auth):
These belong in `~/agents-config/machine/*.md`, not in individual projects. If a machine doc doesn't exist yet, create one in agent-config.

**Experiment-specific sections** (e.g., "Harbor x VeriBench Experiment 35"):
These are project-specific and should go into `~/my-project/docs/agent-docs/`. For large experiment sections, give them their own file (e.g., `~/my-project/docs/agent-docs/experiment-35.md`).

**SOTA model ID lookups** (e.g., "web-search for current models before each run"):
This is a workflow convention. If it applies across projects, add it to `~/agents-config/workflows/`. If project-specific, keep it in `~/my-project/docs/agent-docs/conventions.md`.

### Migration checklist

For each project, verify:
- [ ] `~/my-project/CLAUDE.md` clearly routes to shared rules and retains the project essentials; move detail only when selective loading helps
- [ ] `~/my-project/docs/agent-docs/INDEX.md` exists and lists all project doc files
- [ ] No secrets, API keys, or tokens appear in any doc file
- [ ] No hardcoded machine specs (reference `~/agents-config/machine/` instead)
- [ ] Old `~/my-project/CLAUDE.md.bak` has been deleted
- [ ] Agent can still find build/test commands by reading the project INDEX

---
