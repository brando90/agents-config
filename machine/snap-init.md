# SNAP Node Init & Verification

Copy-paste prompt for a new Claude Code / Codex session on a fresh SNAP node. It checks and fixes everything needed for the agents-config workflow.

Also useful as a periodic health check on existing nodes.

---

## Prerequisites

Before running this on a **brand-new node**, the DFS-level setup must already exist:
- `/dfs/scratch0/<user>/.bashrc` (shared shell config)
- `/dfs/scratch0/<user>/.claude/` (shared Claude auth)
- `/dfs/scratch0/<user>/agents-config/` (this repo, cloned)
- `/dfs/scratch0/<user>/keys/` (API keys)

If DFS isn't set up yet, run `~/veribench/snap_setup.sh` first (see [`snap.md`](snap.md) > New Node Setup).

---

## The Prompt

Paste this into a Claude Code session (or send via Remote Control) on the target node:

````
Check and fix my SNAP node setup. Run these checks and fix anything broken:

1. **Verify paths:**
   - `$HOME` should be `/lfs/<hostname>/0/brando9`
   - `$DFS` or equivalent should be `/dfs/scratch0/brando9`
   - `$AFS` or equivalent should be `/afs/cs.stanford.edu/u/brando9`

2. **Verify symlinks (create any that are missing):**
   - `~/.bashrc` -> `/dfs/scratch0/brando9/.bashrc`
   - `~/agents-config` -> `/dfs/scratch0/brando9/agents-config`
   - `~/CLAUDE.md` -> `~/agents-config/CLAUDE.md`
   - `~/agents.md` -> `~/agents-config/agents.md`
   - `~/.claude` -> `/dfs/scratch0/brando9/.claude` (shared auth across nodes)
   - `~/keys` -> `/dfs/scratch0/brando9/keys`
   - `~/dfs` -> `/dfs/scratch0/brando9` (required by DFS job queue watcher and any `~/dfs/...` path). Create with `ln -sfn /dfs/scratch0/brando9 ~/dfs` if missing.
   - All project dirs under `~/` (e.g., `~/veribench`, `~/harbor-fork`) should be symlinks to `/dfs/scratch0/brando9/<project>`, NOT real directories. Run: `for d in /dfs/scratch0/brando9/*/; do name=$(basename "$d"); [ -L ~/"$name" ] || echo "WARNING: ~/$name is not a symlink to DFS"; done`

3. **Verify RC auth:**
   - `env | grep CLAUDE_CODE_OAUTH_TOKEN` should print NOTHING
   - If it prints a value, find it in `/dfs/scratch0/brando9/.bashrc` and comment it out
   - `~/.claude/config.json` should NOT contain `primaryApiKey`
   - `.bashrc` should have `if [ -n "$TMUX" ]; then unset CLAUDE_CODE_OAUTH_TOKEN; fi`
   - `claude auth status --text` should show "Claude Max Account", no env overrides

4. **Verify agents-config is current:**
   - `cd ~/agents-config && git pull`
   - `cat ~/agents-config/CLAUDE.md` should show the Mandatory Response Protocol
   - `cat ~/agents-config/INDEX_RULES.md` should show a `## Hard Rules` section

5. **Verify tools:**
   - `which claude && claude --version`
   - `which codex && codex --version`

6. **Verify keys exist:**
   - `ls -la ~/keys/` -- should have wandb key, anthropic key, openai key, hf token, etc.

7. **Check GPUs:**
   - `nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader`

8. **Verify remote-job-dispatch infrastructure:**
   - **Kerberos ticket (enables SSH fire-and-forget):** `klist` should print a TGT with `Expires` in the future. If expired, `kinit` and retry.
   - **SSH to peers without password:** `ssh skampere2 hostname` should print the peer hostname with no prompt. If it prompts for a password, your local Kerberos TGT is almost certainly expired or missing — `kinit` and retry. (Peer-side keytab scope is rarely the real cause on SNAP.)
   - **ssh-submit.sh present:** `ls -la ~/agents-config/scripts/ssh-submit.sh` should show an executable file. If missing, `git -C ~/agents-config pull`.
   - **DFS watcher daemon alive on at least one node:** `ls -lt ~/dfs/job_queue/watchers/` and `cat ~/dfs/job_queue/watchers/*.heartbeat | jq '.hostname, .state, .last_heartbeat'`. `last_heartbeat` must be younger than ~3× `poll_interval_s`. If stale, start one: `bash ~/ultimate-utils/py_src/uutils/job_scheduler_uu/start_watcher.sh`.
   - **Git-inbox poller alive (phone dispatch bridge):** `cat ~/dfs/job_queue/git_inbox_heartbeat.json | jq '.hostname, .state, .last_heartbeat'`. If missing or stale, start one on the long-lived node (typically skampere1) — ONE poller total, not per-node: `tmux new -d -s git_inbox_poller "bash ~/agents-config/scripts/git-inbox-poller.sh"`.
   - **Full reference:** `~/agents-config/workflows/remote-job-dispatch.md`.

Report what passed, what failed, and what you fixed. End with a summary table.
````

---

## Expected Results (all pass)

| # | Check | Expected |
|---|-------|----------|
| 1 | Paths | `HOME=/lfs/<hostname>/0/brando9`, `DFS=/dfs/scratch0/brando9`, `AFS=/afs/cs.stanford.edu/u/brando9` |
| 2 | Symlinks (7 + project dirs) | All point to correct DFS/agents-config targets (including `~/dfs → /dfs/scratch0/brando9`); all `~/` project dirs are symlinks to DFS |
| 3 | RC auth | No `CLAUDE_CODE_OAUTH_TOKEN` in env, no `primaryApiKey`, TMUX guard present, Claude Max Account |
| 4 | agents-config | Up to date, CLAUDE.md has Mandatory Response Protocol, INDEX_RULES.md has Hard Rules |
| 5 | Tools | `claude` and `codex` on PATH with recent versions |
| 6 | Keys | `~/keys/` has anthropic, openai, hf, wandb, github keys |
| 7 | GPUs | `nvidia-smi` shows GPUs (A100/H200/B200 depending on node) |
| 8 | Remote-job-dispatch | `klist` valid; `ssh <peer> hostname` passwordless; `ssh-submit.sh` present; ≥1 watcher heartbeat fresh; git-inbox poller heartbeat fresh (on one long-lived node) |

## Known Limitations

- **Codex sandbox on SNAP:** `codex exec` works for code tasks but `bwrap` sandbox fails with `RTM_NEWADDR: Operation not permitted` due to missing user namespace privileges on shared HPC nodes. Codex QA dispatch may need `--skip-git-repo-check` or must run from inside a git repo.
