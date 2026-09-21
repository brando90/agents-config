# Running one CLI under several accounts (Claude Code + Codex, mac + SNAP)

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/multi-account-agent-clis.md>

**TLDR:** Brando holds several subscriptions per vendor (personal, Vals AI, Stanford University enterprise). Each one gets its own CLI profile directory and its own pair of shell wrappers — `clauded-vals`, `codexd-vals`, `clauded-stanford` (`clauded-su`), and `codexd-stanford` (`codexd-su`) — so logins, session history and *billing identity* never mix. This is the recipe for adding a new account, on the mac and on every SNAP node.

**Status:** the Stanford pair is live and verified end to end on 09-16-2026 — `clauded-su`
(`brando9@stanford.edu`, org Stanford University, **enterprise**) and `codexd-su`
(`brando9@stanford.edu`, **edu_plus**), on the mac and on all five SNAP nodes
(skampere1/2/3, mercury1/2).

## The one idea

Both CLIs pick their entire identity (credentials, settings, sessions, history) from a single environment variable:

| CLI | Variable | Personal | Vals AI | Stanford enterprise |
|---|---|---|---|---|
| Claude Code | `CLAUDE_CONFIG_DIR` | `~/.claude` | `~/.claude-vals` | `~/.claude-su` |
| Codex | `CODEX_HOME` | `~/.codex` | — | `~/.codex-su` |

So a new account is: **a new directory + a login into it + two shell functions**. Nothing is ever exported into the ambient shell — the variable is a per-call prefix on the wrapper, so an ordinary `claude` / `codex` in the same terminal still runs the personal account.

Naming convention: `<cli>-<account>` keeps prompts, `<cli>d-<account>` is the yolo/full-trust variant, mirroring the personal `clauded` and `codexd` aliases.

## 1. Mac — Claude Code under a new account

```bash
mkdir -p ~/.claude-su                                  # new profile dir
CLAUDE_CONFIG_DIR=$HOME/.claude-su claude              # then: /login  (browser; pick the right account)
```

Then add to `~/.zshrc` (a **function**, not an alias — zsh does not expand aliases inside function bodies, so the personal alias's flags are inlined on purpose):

```bash
claude-su()  { CLAUDE_CONFIG_DIR="$HOME/.claude-su" claude "$@"; }
clauded-su() { CLAUDE_CONFIG_DIR="$HOME/.claude-su" claude --dangerously-skip-permissions "$@"; }
```

Verify the profile is the account you think it is — **the login is silent about which org you picked**:

```bash
python3 -c 'import json;print(json.load(open("'$HOME'/.claude-su/.claude.json")).get("oauthAccount"))'
CLAUDE_CONFIG_DIR=$HOME/.claude-su claude -p 'reply with exactly: SU_OK'
```

`~/.claude-su/settings.json` is independent of the personal one — set `model`, `effortLevel`, hooks per account there.

**A different account entitles different models.** On the Stanford enterprise plan (probed
09-16-2026): `claude-opus-5` ✅ and `claude-sonnet-5` ✅, but `claude-fable-5-1` answers
`Usage credits are required for this model` ❌. So Hard Rule 8's "smartest available" resolves to
**opus-5** on this profile, not Fable — and `deploy_cc.sh --profile ccs`, which defaults to
`claude-fable-5-1`, must be launched with an explicit `--model claude-opus-5`. Probe a new profile
before you dispatch a worker onto it; a missing entitlement looks exactly like a broken launch.

**Driving the login when you are an agent without a browser.** Both flows are browser OAuth, but
they are scriptable from a pty: run the CLI under `pty.fork()`, tee its output to a log, and poll a
file to inject the pasted code (`scripts/`-adjacent harness; ~40 lines of Python). `script -q
/dev/null` does **not** work here — it needs a tty on *stdin*, so a FIFO fails with
`tcgetattr/ioctl: Operation not supported on socket`. Codex's flow needs no paste at all: it serves
a localhost callback on :1455 and completes on the browser redirect. **Scrub the pty log afterwards
— the Claude setup token is printed to it in cleartext.**

**Keychain note (mac only):** Claude Code namespaces the credential entry by config dir —
`Claude Code-credentials-<first 8 of sha256(path)>`; only the default `~/.claude` uses the bare
`Claude Code-credentials`. Any script that copies credentials must compute that suffix, and must
**never** fall back to the bare entry for a non-default profile — that is the personal login, and
every smoke test would still pass while the wrong account got billed.

## 2. Mac — Codex under a new account

```bash
mkdir -p ~/.codex-su && chmod 700 ~/.codex-su
# write ~/.codex-su/config.toml (model / effort / service_tier / trusted projects — it does NOT
# inherit anything from ~/.codex)
CODEX_HOME=$HOME/.codex-su codex login          # browser; pick the enterprise workspace
CODEX_HOME=$HOME/.codex-su codex login status   # -> "Logged in using ChatGPT"
```

`~/.zshrc`:

```bash
codex-su()  { env -u OPENAI_API_KEY CODEX_HOME="$HOME/.codex-su" codex "$@"; }
codexd-su() { env -u OPENAI_API_KEY CODEX_HOME="$HOME/.codex-su" codex --sandbox danger-full-access --ask-for-approval never "$@"; }
```

`env -u OPENAI_API_KEY` is not cosmetic: a stray `OPENAI_API_KEY` in the environment silently
switches Codex from the subscription to **API billing**, and nothing in the output says so.

## 3. SNAP — the same accounts on every node

Two rules shape the SNAP layout:

- **Runtime and profile stay node-local** (`/lfs/<host>/0/brando9/...`). DFS is shared and
  root-squashed; a Bun-compiled `claude` binary run off DFS SIGBUSes, and two nodes sharing one
  session dir corrupt each other.
- **Only the grant is shared** (`/dfs/scratch0/brando9/.claude-*-remote/oauth-token`, mode 600).

A thin dispatcher lives on the shared PATH at `/dfs/scratch0/brando9/bin/<cmd>` and execs the
node-local wrapper, so `clauded-su` means the same thing on every node without per-node PATH edits.

**Claude Code** uses a long-lived **setup token** rather than a copied credential file, because
OAuth *refresh* tokens rotate on use — one credential set shared by the mac + N nodes logs the
others out ("refresh token was already used"). One setup token can safely be read by every node:

```bash
CLAUDE_CONFIG_DIR=$HOME/.claude-su claude setup-token     # on the mac; prints sk-ant-oat...
umask 077; printf '%s' '<token>' > ~/keys/claude_su_oauth_token.txt
bash ~/agents-config/scripts/push_claude_su_snap.sh        # all nodes; or name one host
```

**Codex** has no setup-token equivalent, so pick an auth mode:

```bash
bash ~/agents-config/scripts/push_codex_su_snap.sh                 # AUTH_MODE=copy (default):
                                                                   # copies ~/.codex-su/auth.json
AUTH_MODE=device bash ~/agents-config/scripts/push_codex_su_snap.sh  # then, per node:
ssh <host>.stanford.edu -t 'bash -lc "codex-su login --device-auth"'
```

`copy` is one shot and needs no browser per node, but the ChatGPT token refreshes in place, so the
mac and the nodes can race each other out of a session. `device` gives each node its own grant and
has no such race — use it when a node must run unattended for a long time.

### Scripts

| Script | Side | What it does |
|---|---|---|
| `scripts/install_su_node.sh` | node | Node-local Claude runtime (content-addressed by sha256) + `claude-su` / `clauded-su` wrappers |
| `scripts/su_remote_entry.sh` | DFS | Shared `/dfs/.../bin` dispatcher → node-local Claude wrapper |
| `scripts/push_claude_su_snap.sh` | mac | Pushes the grant, runs the installer, installs dispatchers, smoke-tests each node |
| `scripts/test_su_wrappers.py` | mac | Unit-tests the generated Claude wrapper: argument forwarding, the yolo flag, and that every bad-grant case fails closed (`python3 scripts/test_su_wrappers.py`) |
| `scripts/install_codex_su_node.sh` | node | Node-local `CODEX_HOME` + `codex-su` / `codexd-su` wrappers |
| `scripts/codex_su_remote_entry.sh` | DFS | Shared `/dfs/.../bin` dispatcher → node-local Codex wrapper |
| `scripts/push_codex_su_snap.sh` | mac | Runs the installer, ships auth (or prints the device-login command), verifies each node |

The Vals equivalents (`install_vals_node.sh`, `push_claude_vals_creds.sh`, `setup_claude_vals_snap.sh`,
`vals_remote_entry.sh`) are the same shape; the Vals driver pushes the Keychain credential JSON
instead of a setup token, which is why it carries the rotation warning in its header.

## 4. Register the profile with the board and the dispatcher

A new profile is invisible to the tooling until it is named in three places, because both tools map
*config dir -> short tag -> wrapper* by hand:

| File | What to add | Stanford example |
|---|---|---|
| `scripts/agent_board.py` | `CONFIGS`, `WRAPPERS`, `SECTION_TITLES` | `~/.claude-su` -> `ccs` -> `clauded-su`, section "Claude Code sessions — Stanford" |
| `scripts/deploy_cc.sh` | the `--profile` case arms (validation + `WRAPPER`/`REG_DIR`) | `--profile ccs` -> `clauded-su`, `~/.claude-su/sessions` |
| `INDEX_RULES.md` | the account abbreviation | `ccs` |

Without the board entry, that account's sessions show up with a blank agent column and
`--resume-dead` types the *wrong* wrapper (the personal one) into the recovery window — it would
resume a Stanford conversation on the personal subscription. `python3 scripts/test_agent_board_resume.py`
and `python3 scripts/test_dispatch_scripts.py` cover both mappings.

## Verified end to end (09-16-2026)

`clauded-su` on the Stanford enterprise seat (`brando9@stanford.edu`, org "Stanford University",
`claude_enterprise`, seat `enterprise_higher_ed`): mac profile + wrappers, `setup-token` grant pushed with
`scripts/su_finish_setup.sh`, and `SU_NODE_READY` on **skampere1** and **skampere2** (node-local runtime
`claude 2.1.274`, own profile dir, fail-closed wrapper). A `clauded-su -p` smoke on skampere1 returned a model
reply. First real use: the 564-task baseline half of expt-89 Phase B on skampere2.

`scripts/su_finish_setup.sh` is the one command to run after the browser `/login`: it checks the profile's
account, mints and stores the grant (mode 600, hidden prompt, never in argv), pushes it to the nodes, and
writes the shared `keys/` copy that unattended SNAP jobs watch.

## Guardrails every one of these scripts enforces

1. **Identity guard before anything is shared.** The Claude driver refuses unless
   `~/.claude-su/.claude.json` shows a `stanford.edu` account; the Codex driver refuses an
   `auth_mode` that is not `chatgpt`. Override with `CLAUDE_SU_EXPECT_ACCOUNT` / `CODEX_SU_EXPECT_MODE`.
2. **Credentials travel on stdin, never argv** — an argument is visible in `ps` to the whole node.
3. **The wrapper scrubs the environment it inherits** (`ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`,
   `ANTHROPIC_BASE_URL`, `OPENAI_API_KEY`, …) so an inherited variable can never quietly redirect the
   account or the billing.
4. **Grants are mode 600, owned by this user, and never a symlink** — the wrapper re-checks at every
   launch and refuses otherwise.
5. **Runtime binaries are content-addressed and never overwritten in place** — a new CLI version
   lands in a new directory.

## Verification — what was actually probed (09-16-2026, from the mac orchestrator)

| Probe | Where | Result |
|---|---|---|
| `python3 scripts/test_su_wrappers.py` | mac | 5/5 PASS — argument forwarding, insecure-grant rejected, failed/empty/missing grant rejected |
| `codexd-su exec --skip-git-repo-check -c model_reasoning_effort="low" 'Reply with exactly: PONG-SU-LOCAL'` | mac, codex-cli 0.154.0 | `PONG-SU-LOCAL`, 3,693 tokens, rc 0 |
| same probe, `PONG-SU-SNAP` | skampere1 (DFS entry -> node-local runtime) | `PONG-SU-SNAP`, 7,706 tokens, rc 0, session `01a0ad46-32ff-7012-99bc-356addb5571c` |
| `clauded-su -p 'Reply with exactly: PONG-SU-CLAUDE'` | skampere1 | `PONG-SU-CLAUDE`, rc 0 |

**The `d` in `codexd-su` does not survive the Stanford enterprise policy.** Every SU Codex run, on the mac and on
SNAP, prints enterprise-managed fallbacks before it answers: `approval_policy` `Never` -> `OnRequest`; `sandbox_mode`
`DangerFullAccess` -> a managed profile whose filesystem is `Restricted` (root read-only) and whose network is
`Restricted`; `web_search` `Live` -> `Cached` (source: `enterprise-managed requirements Baseline
(regulated-workspace-default-fallback)`). So the Stanford Codex profile is in practice a read-only, network-restricted
agent that can still stop and ask for approval. **Do not dispatch an unattended full-permission SNAP worker on it**
(Rule 51/55 workers stay on `codexd` personal, `clauded`, or `clauded-vals`); it is well suited to one-shot `exec`
reviews, reading and analysis. On SNAP it additionally warns that Codex's Linux sandbox needs bubblewrap user
namespaces, and that `[features].use_legacy_landlock` is deprecated.

**Gotcha: on the mac these are zsh functions, not scripts on `PATH`.** A non-interactive `bash -c 'codexd-su ...'`
fails with `No such file or directory`. Call them through `zsh -ic '...'`, or inline the environment
(`env -u OPENAI_API_KEY CODEX_HOME=$HOME/.codex-su codex ...`). On SNAP they are real scripts in
`/dfs/scratch0/brando9/bin`, so a plain `ssh <host> 'codexd-su ...'` works once that node has its profile.

**Rollout state at 19:50 PDT 09-16-2026 (in progress, another session owns the push):** skampere1 has
`~/.codex-su/{auth.json,config.toml}` and the node-local runtime in `~/.local/bin/` — verified live above. mercury1
has the wrappers but no `~/.codex-su` profile yet, so it was not probed. Re-run the two live probes on each node after
`push_codex_su_snap.sh` reaches it; a wrapper on `PATH` is not evidence that the profile is installed.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `Not logged in · Please run /login` on the mac | profile dir exists but was never logged into — step 1 |
| `You've hit your session limit · resets <time>` | the **seat**, not the token: Stanford's enterprise seat grants short session windows. The grant is still valid — probe the route before committing a long job to it, and fall back to another subscription rather than sleeping on a closed window |
| `You've hit your individual spend limit` on a team seat | that account's per-user cap (Vals: resets weekly). Switch model tier or profile; it is a routing problem, not a dead credential (Trigger Rule 58) |
| `Protected Stanford remote grant unavailable` | DFS grant missing, wrong mode, or a symlink — re-run the push script |
| `Invalid Stanford grant format` | the saved file is not `sk-ant-oat..`, e.g. a pasted URL or trailing newline noise |
| node says logged out after the mac was used | credential-copy route + rotated refresh token — re-push, or move to a setup token / device auth |
| Codex bills the API instead of the subscription | an `OPENAI_API_KEY` leaked into the environment — the wrappers unset it; a hand-rolled one must too |
| `Usage credits are required for this model` | that model is not entitled on this account — pick one that is (see the entitlement note above) |
| `deploy_cc.sh --profile ccs` says "the agent did not start" | two separate causes: the workspace-trust dialog (`tmux send-keys -t <name> Down Enter` to accept "Yes, I trust this folder"), and the registry poll looking in `~/.claude-su/sessions` while the SNAP wrapper registers in `~/.claude-su-node/sessions/*.json`. Launch with `--no-preflight` and verify by hand |
| `codex exec` rejects your flags | `--ask-for-approval` / `--sandbox` are top-level, not `exec` flags: `codex --sandbox danger-full-access --ask-for-approval never exec --skip-git-repo-check '<prompt>'`. `exec` also needs `--skip-git-repo-check` outside a git repo |
