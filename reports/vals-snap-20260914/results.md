# Vals Claude Code cluster setup

**Doc link:** <https://github.com/brando90/agents-config/blob/main/reports/vals-snap-20260914/results.md>

**TLDR-start:** [snap: vals-login] Vals Claude Code now works on four reachable nodes with a separate protected grant, fast local executable/session storage, and tested job dispatch. Three requested nodes remain blocked by host or scheduler access.

**Status:** PARTIAL — four nodes verified; three access blockers
**Last updated:** 2026-09-14 13:49 PDT

| Node | State | Verified evidence |
|---|---|---|
| skampere1 | READY | Canonical clauded-vals ran Bash hostname, wrote matching receipt, returned VALS-DISPATCH-OK |
| skampere2 | READY | Same real tool-use dispatch test passed |
| mercury1 | READY | Same test; Sonnet interactive/one-shot, explicit Opus 5 max and default Opus 5 all passed |
| mercury2 | READY | Same real tool-use dispatch test passed |
| skampere3 | BLOCKED | Authentication/command request accepted, then even true and file-transfer subsystem stall; bounded probes stopped |
| hyperturing1 | BLOCKED | Slurm scheduler denies access without allocation; brando9 has no account association |
| hyperturing2 | BLOCKED | Same scheduler-access restriction |

## Commands and storage

Use `claude-vals` normally or `clauded-vals` for authorized permission-bypass jobs.
For explicit models: `clauded-vals --model claude-opus-5 --effort max` or `clauded-vals --model claude-sonnet-5 --effort high`.
A plain `clauded-vals -p` probe resolved the default to claude-opus-5 and returned VALS-DEFAULT-OK.
Initial profile settings mirror this Mac's opus / Opus 5 extra-high setting; ordinary per-session overrides remain available.

The canonical scripts in `/dfs/scratch0/brando9/bin` and their Andrew File System compatibility mirrors select `/lfs/<node>/0/brando9/.local/bin/claude-vals` or `clauded-vals`.
The verified 2.1.270 executable is a 212 mebibytes (MiB), content-addressed local copy; active sessions live in `/lfs/<node>/0/brando9/.claude-vals-node`.
The old shared Vals profile and personal commands/settings remain preserved.
The separately authorized one-year inference-only grant is stored outside git in an owner-only directory/file. The Mac's rotating login was not copied.
The deployed installer is `/dfs/scratch0/brando9/.claude-vals-remote/install_vals_node.sh`; its source is `scripts/install_vals_node.sh` in this repository.
Older shared-profile helpers must not be run over these wrappers.

## Budget and review

Mac identity: brando@vals.ai, Vals AI, team subscription. Browser current-session and weekly usage both showed 0% used before these bounded probes. This does not establish future campaign allowance or paid overage policy.
Sonnet 5 and Opus 5 both returned successful model calls. Fable 5.1/max returned an individual-spend-limit error, and interactive Fable displayed a separate purchased-credit requirement. This was model-specific, not provider-wide or a one-shot-mode restriction. No purchase, recharge setting or administrator limit was changed.
Client total_cost_usd fields are list-price accounting, not evidence of a new purchase.

Authentication-critical review: strongest Claude Fable attempt was blocked; fresh Codex gpt-6-astra/ultra reviewed the scripts and returned PASS with zero critical/major issues. Its actual model and effort were verified in its session record. Existing Codex credits were used with automatic reload verified off. The initially planned eight-minute review was extended once to fifteen minutes while it verified concrete repairs; no further reviewer was launched.
Builder repaired masked token-read failures, unsafe existing directories/links, and empty-array portability. The reviewer passed twelve mocked wrapper/routing cases and nine mocked installer cases. The builder's five portable regression checks and live node installs/dispatches passed. See review.md and per-node structured result files.

## Publication

[Pull request #60](https://github.com/brando90/agents-config/pull/60) merged as `cff25f46a6817e16f23d4ba8ea779b49199ca5a2`. The completion/partial-status email was sent successfully to brando.science@gmail.com with no copied recipients.

## Scope and remaining limits

Disk percentage alarms remain on skampere1, skampere2 and mercury2. These small installs were bounded to a 212 MiB executable plus small logs, after verifying at least 1 gibibyte (GiB) free; actual available space was over 1,200 GiB on each skampere node and 29 GiB on mercury2. This does not clear those nodes for large experiments. Personal-profile symlink differences were unrelated and preserved.
All four short smoke sessions completed; no campaign, recurring monitor, credential-renewal daemon or automatic provider failover was installed. Future long jobs still need their own resource/budget checks and recovery owner.
The original Mac and cluster agents-config checkouts contain unrelated changes; publication uses an isolated checkout and does not switch, stash or overwrite those shared trees. Operational wrappers and the protected deployed installer were synchronized directly with verified content.

**TLDR-end:** [snap: vals-login] Four nodes can run Vals Opus 5/Sonnet 5 jobs now. skampere3 and both hyperturing nodes still require host/scheduler access repair before their installation and dispatch can be verified.
