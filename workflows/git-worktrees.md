# Workflow: Git worktrees for parallel agent isolation

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/git-worktrees.md>

**TLDR:** Give parallel agents separate working directories that share one repository's Git history. Keep temporary checkouts under `~/.worktrees/<project>/<task>` or the client's managed worktree area, and remove them after preserving their work under [Rule 19](../rules/maintenance.md#trigger-rule-19).

## Ownership and location

Reuse a suitable owned checkout before creating another. Each concurrent writer needs its own working directory and task branch; never switch another agent's checkout. The canonical project stays at `~/project`; temporary checkouts must not become sibling projects such as `~/project-cc-work`.

Record the canonical path, temporary path, task and cleanup owner in the existing task checkpoint. The worker owns cleanup; its dispatcher takes over if the worker exits or runs out of context or allowance. Creating a worktree is not permission to discard another owner's changes.

## Create and use worktrees

Run these commands from a shell that stops on errors. A failed worktree creation must remain visible and stop the dependent launch; do not suppress it or continue in an unintended checkout.

```bash
set -euo pipefail
PROJECT="$HOME/project"
CC_WORKTREE="$HOME/.worktrees/project/cc-feature"
CODEX_WORKTREE="$HOME/.worktrees/project/codex-feature"
mkdir -p "$HOME/.worktrees/project"

git -C "$PROJECT" worktree add -b cc-feature-branch "$CC_WORKTREE"
git -C "$PROJECT" worktree add -b codex-feature-branch "$CODEX_WORKTREE"
git -C "$PROJECT" worktree list
```

Point each agent at its assigned checkout with full access and no routine approval waits, as required by [Rule 51](../rules/hosts.md#trigger-rule-51):

```bash
# Terminal 1: Claude Code
set -euo pipefail
cd "$HOME/.worktrees/project/cc-feature"
claude --dangerously-skip-permissions
```

```bash
# Terminal 2: Codex
set -euo pipefail
cd "$HOME/.worktrees/project/codex-feature"
codex --sandbox danger-full-access --ask-for-approval never
```

## Persistent sessions

For work that needs a persistent terminal, follow [Rule 42](../rules/workers.md#trigger-rule-42) and the [dispatch workflow](reliable-agent-dispatch.md). After successful creation of the worktrees above, these commands start named local sessions:

```bash
set -euo pipefail
byobu new-session -d -s cc-project-feature \
  -c "$HOME/.worktrees/project/cc-feature" \
  'claude --dangerously-skip-permissions'
byobu new-session -d -s codex-project-feature \
  -c "$HOME/.worktrees/project/codex-feature" \
  'codex --sandbox danger-full-access --ask-for-approval never'
byobu list-sessions
```

Give each agent its task brief. Verify its actual process, effective permissions, working directory and first useful action before reporting that it is running; session creation alone is not execution evidence. Select model and effort under [Hard Rule 8](../rules/safety-and-models.md#hard-rule-8), preserving explicit task requirements.

## Finish and remove

Before removing a checkout, inspect active owners, processes and scheduled consumers; staged and unstaged changes; untracked and ignored files; and unpublished history. Verify needed work and recovery evidence reached the canonical project. A clean status or a merged branch alone does not establish that removal is safe. Follow [Rule 19](../rules/maintenance.md#trigger-rule-19) for the full preservation and cleanup procedure.

Once the owned checkout is inactive and its needed work is preserved:

```bash
set -euo pipefail
git -C "$HOME/project" worktree remove "$HOME/.worktrees/project/cc-feature"
git -C "$HOME/project" branch -d cc-feature-branch
git -C "$HOME/project" worktree list
```

Do not force past a dirty, locked or unmerged refusal. Prune only registrations verified stale, and remove only empty task containers. Run the Rule 19 sweep at the start and end of tasks that create worktrees; its dry run shows retained work and the reasons:

```bash
python3 "$HOME/agents-config/scripts/stale_checkout_sweep.py" --conservative --json
```

Follow the [daily cleanup workflow](checkout-cleanup.md) for conservative apply with explicit paths after the required checks. App-managed worktrees follow their supported cleanup operation. Confirm the retired folder is gone, surviving registrations resolve, and the canonical checkout still works before reporting completion.
