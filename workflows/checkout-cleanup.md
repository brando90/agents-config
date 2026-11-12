# Daily checkout cleanup

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/checkout-cleanup.md>

**TLDR:** Workers still clean up their own temporary checkouts under Rule 19. A daily Codex follow-up catches leftovers, deletes only explicitly checked clean worktrees, and reports retained work with its reason.

## Prevention and ownership

Keep one canonical project directory. Reuse it for nonconflicting work; when isolation is needed, use the owning app's managed location or `~/.worktrees/<project>/<task>`. Never make sibling temporary clones in `~`. Record the canonical directory, temporary directory and cleanup owner in the task checkpoint. Use the corrected [worktree guide](git-worktrees.md).

At task completion, land authorized changes, verify needed ignored/private files in their canonical location, and remove the temporary checkout. The dispatcher inherits cleanup if a worker stops. Age alone never proves a checkout is disposable.

## Daily backstop

The local Codex app schedule runs daily at 9:00 AM America/Los_Angeles in the existing cleanup chat. It is ongoing until Brando changes or cancels it and requires the Mac and Codex app to be available. Verify the actual automation using the app tool; this document does not install a job. Reuse the existing schedule when updating it.

1. Refresh the shared instructions without disturbing concurrent edits. Run `python3 ~/agents-config/scripts/home_clutter_audit.py` and `python3 ~/agents-config/scripts/stale_checkout_sweep.py --conservative --json`. Audit exit code 1 means candidates were found, not deletion failure. Store private inventories under `~/Documents/agent-reports/home-cleanup/`, replacing the latest snapshot rather than accumulating full repository copies.
2. Before removing any candidate, inspect active task owners, registered worktrees, processes/open working directories, automation prompts (including paused jobs with future dependencies), launch agents and other scheduled consumers. A path in a saved checkpoint is a dependency to reconcile, not proof that a worker is still running. If ownership or a consumer is unresolved, retain it with a concrete reason.
3. For each eligible worktree, run `python3 ~/agents-config/scripts/stale_checkout_sweep.py --conservative --fetch --only /absolute/eligible/path --apply --json`. Repeat `--only` for multiple verified paths. Fetch must succeed. The command rechecks process use and repository state immediately before removal and never uses force in this mode. It keeps branch refs, app-managed worktrees, submodules, local changes, untracked files, ignored files (even caches), locked/recent checkouts, hidden index changes, unpreserved detached recovery history, worktree-local references, unfinished Git operations and any HEAD not landed on the remote default branch. Git/process failures stop deletion. Do not invoke the legacy permissive `--apply` mode from a schedule.
4. Reconcile retained work with its owner: preserve unique history and needed files in the canonical project or a verified minimal recovery package, then rerun the conservative command. Scheduled runs remove checkouts only through that command after it classifies the path as SAFE; if it still says KEEP, report it for owner reconciliation. Do not land research changes or resume paused experiments merely to make cleanup pass. Full clones and app-managed worktrees require their owner's supported cleanup; the daily job reports them and does not remove them outside the conservative command.
5. For visible non-repository clutter, move verified completed reports/evidence to `~/Documents/agent-reports/<task>/` after checking consumers and verifying the transferred bytes. Remove verified empty containers with `rmdir`. Preserve Brando's project/course/data directories and functional aliases. A name heuristic is only an inspection candidate, and moving reports is organization, not disk-space reclamation.
6. Verify actual removals, surviving canonical projects and registrations. Record removed paths, retained paths/reasons, recovered artifacts and actual disk changes. Update this chat only for a meaningful cleanup, a failure, or a newly discovered unresolved dependency; deduplicate unchanged findings. Do not create a new checkout for the cleanup job itself.

## Verification

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*clutter*.py'
python3 -m unittest discover -s scripts/tests -p test_stale_checkout_sweep.py
python3 scripts/check_instruction_docs.py
git diff --check
```

The conservative path is deliberately narrower than the older content-comparison sweep: it cannot mistake an overwritten staged version or an ignored artifact for expendable content. The older mode remains available for supervised reconciliation, subject to all Rule 19 checks.
