#!/usr/bin/env bash
# ssh-submit.sh — SSH fire-and-forget job launcher with smart-mode agent wrapping.
#
# Launches a job on a remote SNAP node in a detached tmux session. The job is
# wrapped in an AI coding agent (clauded/codex/claude) that diagnoses failures,
# retries up to 3 times, and emails PASS/FAIL results — same semantics as the
# DFS watcher daemon's smart mode.
#
# The agent prompt lives in ~/agents-config/workflows/smart-job-agent-prompt.md
# (shared with the watcher). Keep it there, not here.
#
# Usage:
#   ssh-submit.sh --node <host> --job <path> [--name <str>] [--direct] [--tmux-prefix <str>]
#
# Examples:
#   # Fire-and-forget, smart mode (default):
#   ~/agents-config/scripts/ssh-submit.sh --node skampere2 --job /tmp/eval.sh
#
#   # Direct mode (no agent wrapping, just bash):
#   ~/agents-config/scripts/ssh-submit.sh --node skampere2 --job /tmp/eval.sh --direct
#
#   # Custom tmux session prefix (default: ssh_job):
#   ~/agents-config/scripts/ssh-submit.sh --node skampere3 --job /tmp/x.sh --tmux-prefix expt
#
# Prerequisites on the target node:
#   - Kerberos ticket (klist) OR SSH keys — whatever lets `ssh <node>` work
#     without a password from the current shell.
#   - One of: clauded / codex / claude binaries on PATH (for smart mode).
#   - tmux (for detached session). Should always be present on SNAP.
#   - ~/agents-config/ cloned at /dfs/scratch0/$USER/agents-config (standard SNAP layout).
#
# Returns immediately after ssh-spawn; does NOT wait for the job.
# You will receive TWO emails per job: STARTING (within seconds) and PASS/FAIL (at end).
#
# For live visibility: `ssh <node> "tmux attach -t <prefix>_<name>_<stamp>"`
# To list active jobs on a node:    `ssh <node> "tmux ls | grep <prefix>_"`
#
# See also:
#   - ~/agents-config/workflows/remote-job-dispatch.md — full comparison of
#     SSH vs watcher vs phone dispatch, pros/cons, when to use which.
#   - ~/agents-config/workflows/smart-job-agent-prompt.md — the agent prompt.

set -euo pipefail

# ── defaults ─────────────────────────────────────────────────────────────
NODE=""
JOB=""
NAME=""
MODE="smart"          # smart | direct
TMUX_PREFIX="ssh_job"
NOTIFY_EMAIL="brando.science@gmail.com"
NOTIFY_CC="brando9@stanford.edu"

# ── arg parse ────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --node)         NODE="$2"; shift 2 ;;
        --job)          JOB="$2"; shift 2 ;;
        --name)         NAME="$2"; shift 2 ;;
        --direct)       MODE="direct"; shift ;;
        --smart)        MODE="smart"; shift ;;
        --tmux-prefix)  TMUX_PREFIX="$2"; shift 2 ;;
        --notify-email) NOTIFY_EMAIL="$2"; shift 2 ;;
        --notify-cc)    NOTIFY_CC="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,40p' "$0"; exit 0 ;;
        *)
            echo "ssh-submit.sh: unknown arg: $1" >&2
            echo "Run with --help for usage." >&2
            exit 2
            ;;
    esac
done

if [[ -z "$NODE" || -z "$JOB" ]]; then
    echo "ssh-submit.sh: --node and --job are required" >&2
    echo "Run with --help for usage." >&2
    exit 2
fi

if [[ ! -f "$JOB" ]]; then
    echo "ssh-submit.sh: job file not found: $JOB" >&2
    exit 2
fi

# ── names, paths ─────────────────────────────────────────────────────────
JOB_BASENAME="$(basename "$JOB")"
ORIGINAL_NAME="${NAME:-${JOB_BASENAME%.sh}}"
STAMP="$(date +%Y-%m-%d__%H-%M-%S)"
SESSION="${TMUX_PREFIX}_${ORIGINAL_NAME}_${STAMP}"

# We stage everything under ~/dfs on the remote so that logs survive even if the
# local LFS fills up. ~/dfs exists on all SNAP nodes (symlinked to /dfs/scratch0/$USER).
# Resolve the remote $HOME once up front so scp sees a literal absolute path
# (scp does NOT do shell expansion on the destination side).
REMOTE_HOME="$(ssh "$NODE" 'echo $HOME')"
if [[ -z "$REMOTE_HOME" ]]; then
    echo "ssh-submit: could not resolve \$HOME on $NODE" >&2
    exit 3
fi
REMOTE_STAGE_DIR="${REMOTE_HOME}/dfs/ssh_job_queue/${STAMP}__${ORIGINAL_NAME}"
REMOTE_JOB_PATH="${REMOTE_STAGE_DIR}/${JOB_BASENAME}"
REMOTE_LOG_PATH="${REMOTE_STAGE_DIR}/job.log"

# The prompt template (shared via DFS / agents-config symlink).
LOCAL_PROMPT_TMPL="${HOME}/agents-config/workflows/smart-job-agent-prompt.md"

# ── ship the job file to the remote ──────────────────────────────────────
echo "[ssh-submit] staging job on $NODE:$REMOTE_STAGE_DIR"
ssh "$NODE" "mkdir -p \"$REMOTE_STAGE_DIR\""
scp -q "$JOB" "$NODE:${REMOTE_STAGE_DIR}/${JOB_BASENAME}"
ssh "$NODE" "chmod +x \"${REMOTE_STAGE_DIR}/${JOB_BASENAME}\""

# ── build the agent prompt LOCALLY and ship it as a file ─────────────────
# We do the template substitution here (not on the remote) to avoid nested
# heredoc / quoting hell when the whole remote command is passed through
# `ssh bash -lc '…'`. The rendered prompt is copied to the remote stage dir.
if [[ "$MODE" == "smart" ]]; then
    if [[ ! -f "$LOCAL_PROMPT_TMPL" ]]; then
        echo "ssh-submit: prompt template missing at $LOCAL_PROMPT_TMPL" >&2
        exit 3
    fi
    LOCAL_PROMPT_FILE="$(mktemp -t ssh-submit-prompt.XXXXXX.txt)"
    REMOTE_HOSTNAME="$(ssh "$NODE" 'hostname')"
    EXEC_CMD_RENDERED="bash \"$REMOTE_JOB_PATH\" > \"$REMOTE_LOG_PATH\" 2>&1"
    HOSTNAME_FILLED="$REMOTE_HOSTNAME" \
    JOB_PATH_FILLED="$REMOTE_JOB_PATH" \
    ORIGINAL_NAME_FILLED="$ORIGINAL_NAME" \
    LOG_PATH_FILLED="$REMOTE_LOG_PATH" \
    EXEC_CMD_FILLED="$EXEC_CMD_RENDERED" \
    NOTIFY_EMAIL_FILLED="$NOTIFY_EMAIL" \
    NOTIFY_CC_FILLED="$NOTIFY_CC" \
    TMPL_PATH="$LOCAL_PROMPT_TMPL" \
    python3 - > "$LOCAL_PROMPT_FILE" <<'PY'
import os, sys
with open(os.environ["TMPL_PATH"]) as f:
    txt = f.read()
marker = "## The Prompt"
i = txt.find(marker)
if i < 0:
    sys.stderr.write("template missing '## The Prompt' section\n"); sys.exit(1)
rest = txt[i:]
start = rest.find("```")
end   = rest.find("```", start + 3)
if start < 0 or end < 0:
    sys.stderr.write("template prompt not in fenced block\n"); sys.exit(1)
prompt = rest[start+3:end].lstrip("\n").rstrip() + "\n"
sub = {k: os.environ[k + "_FILLED"] for k in
       ("HOSTNAME","JOB_PATH","ORIGINAL_NAME","LOG_PATH","EXEC_CMD","NOTIFY_EMAIL","NOTIFY_CC")}
for k, v in sub.items():
    prompt = prompt.replace("{{" + k + "}}", v)
sys.stdout.write(prompt)
PY
    REMOTE_PROMPT_FILE="${REMOTE_STAGE_DIR}/agent_prompt.txt"
    scp -q "$LOCAL_PROMPT_FILE" "$NODE:$REMOTE_PROMPT_FILE"
    rm -f "$LOCAL_PROMPT_FILE"
fi

# ── construct the remote launcher command ────────────────────────────────
# Two paths:
#   direct: tmux new -d -s <session> 'bash <job> > <log> 2>&1'
#   smart:  build the agent prompt from the template on the remote, then:
#           tmux new -d -s <session> 'clauded -p "<prompt>"'
#
# Heredoc escape carefully — we send *one* bash -c "..." to the remote, so the
# outer double quotes contain the whole thing. We escape $ inside with \$.

# ── build a self-contained remote launcher script and ship it ────────────
# We write the full launcher logic to a local temp file, scp it to the remote,
# and then just invoke `bash launcher.sh` over ssh. This avoids every layer of
# nested-quote hell that bit us before: the launcher is a plain shell script on
# the remote, not an inlined command string.
LOCAL_LAUNCHER="$(mktemp -t ssh-submit-launcher.XXXXXX.sh)"
REMOTE_LAUNCHER="${REMOTE_STAGE_DIR}/launcher.sh"

if [[ "$MODE" == "direct" ]]; then
    cat > "$LOCAL_LAUNCHER" <<LAUNCHER_EOF
#!/usr/bin/env bash
set -e
cd "$REMOTE_STAGE_DIR"
tmux new-session -d -s "$SESSION" \\
    "bash \"$REMOTE_JOB_PATH\" > \"$REMOTE_LOG_PATH\" 2>&1; echo FINAL_EXIT_CODE: \\\$? >> \"$REMOTE_LOG_PATH\""
echo "direct-mode: tmux session $SESSION started"
echo "log: $REMOTE_LOG_PATH"
LAUNCHER_EOF
else
    # Local: write two remote-side scripts:
    #   launcher.sh — picks an agent binary, starts tmux
    #   agent_runner.sh — reads the prompt, invokes the right agent
    # Shipping both as files eliminates all nested-quote issues.
    LOCAL_RUNNER="$(mktemp -t ssh-submit-runner.XXXXXX.sh)"
    REMOTE_RUNNER="${REMOTE_STAGE_DIR}/agent_runner.sh"
    cat > "$LOCAL_RUNNER" <<RUNNER_EOF
#!/usr/bin/env bash
# agent_runner.sh — runs inside tmux; invokes the detected agent with the prompt.
set -e
cd "$REMOTE_STAGE_DIR"
PROMPT="\$(cat "$REMOTE_PROMPT_FILE")"
case "\${AGENT:-}" in
    clauded) exec clauded -p "\$PROMPT" ;;
    codex)   exec codex exec --full-auto "\$PROMPT" ;;
    claude)  exec claude -p --dangerously-skip-permissions "\$PROMPT" ;;
    *)       echo "agent_runner: unknown AGENT=\${AGENT:-<unset>}" >&2; exit 2 ;;
esac
RUNNER_EOF
    scp -q "$LOCAL_RUNNER" "$NODE:$REMOTE_RUNNER"
    ssh "$NODE" "chmod +x \"$REMOTE_RUNNER\""
    rm -f "$LOCAL_RUNNER"

    cat > "$LOCAL_LAUNCHER" <<LAUNCHER_EOF
#!/usr/bin/env bash
# smart-mode launcher — generated by ssh-submit.sh
set -e
cd "$REMOTE_STAGE_DIR"

AGENT=""
for cand in clauded codex claude; do
    if command -v "\$cand" >/dev/null 2>&1; then AGENT="\$cand"; break; fi
done
if [[ -z "\$AGENT" ]]; then
    echo "ssh-submit(remote): no agent binary found — falling back to direct mode" >&2
    tmux new-session -d -s "$SESSION" "bash \"$REMOTE_JOB_PATH\" > \"$REMOTE_LOG_PATH\" 2>&1; echo FINAL_EXIT_CODE: \\\$? >> \"$REMOTE_LOG_PATH\""
    exit 0
fi

if [[ ! -f "$REMOTE_PROMPT_FILE" ]]; then
    echo "ssh-submit(remote): prompt file missing at $REMOTE_PROMPT_FILE" >&2
    exit 1
fi

export AGENT
tmux new-session -d -s "$SESSION" -e "AGENT=\$AGENT" "bash \"$REMOTE_RUNNER\""
echo "smart-mode: tmux session $SESSION started with agent \$AGENT"
echo "prompt: $REMOTE_PROMPT_FILE"
echo "stage:  $REMOTE_STAGE_DIR"
LAUNCHER_EOF
fi

scp -q "$LOCAL_LAUNCHER" "$NODE:$REMOTE_LAUNCHER"
ssh "$NODE" "chmod +x \"$REMOTE_LAUNCHER\""
rm -f "$LOCAL_LAUNCHER"

# ── ship & run ────────────────────────────────────────────────────────────
echo "[ssh-submit] dispatching $ORIGINAL_NAME → $NODE (mode=$MODE, tmux=$SESSION)"
ssh "$NODE" "bash \"$REMOTE_LAUNCHER\""

echo "[ssh-submit] dispatched."
echo "[ssh-submit] attach:  ssh $NODE \"tmux attach -t $SESSION\""
echo "[ssh-submit] sessions: ssh $NODE \"tmux ls | grep ^${TMUX_PREFIX}_\""
echo "[ssh-submit] expect email from $NOTIFY_EMAIL within ~1 min (STARTING) and on finish (PASS|FAIL)."
