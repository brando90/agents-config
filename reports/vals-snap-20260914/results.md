# Vals Claude Code cluster setup

**Doc link:** <https://github.com/brando90/agents-config/blob/snap-vals-access-20260914/reports/vals-snap-20260914/results.md>

**TLDR-start:** [snap: vals-login] Restore the Vals Claude Code account on the requested nodes using a separate authorized grant and local runtime storage.

**Status:** RUNNING
**Last updated:** 2026-09-14 13:29 PDT

| Phase | State | Evidence |
|---|---|---|
| Mac identity | DONE | brando@vals.ai, Vals AI, team subscription |
| Budget check | DONE | Vals browser current session and weekly usage both 0%; no new purchases authorized |
| Separate grant | DONE | User approved one-year inference-only setup-token; stored outside git |
| Node installer | IN PROGRESS | Local immutable binary and per-node profile |
| Dispatch | DONE on mercury1 | Sonnet 5 low passed interactive and one-shot calls; see sonnet-print.json |
| Independent review | IN PROGRESS | Fable 5.1 requires purchased usage credits; fresh Codex Astra ultra review using existing credits, auto-reload off |
| Publication | PENDING | Isolated branch; original checkout contains unrelated edits |

Reachability: skampere1, skampere2, mercury1, mercury2 reachable using full domain names. skampere3 connection is stalled. hyperturing1 and hyperturing2 deny access without Slurm (cluster scheduler) allocations; showaccount on ilc.stanford.edu lists no association for brando9.

Storage health: skampere1 and skampere2 each have over 1,200 GiB free but fail the percentage threshold; mercury2 has 29 GiB free and fails; mercury1 has 339 GiB free and warns. Use mercury1 for the first bounded test. Personal profile link differences are unrelated and are preserved.

Budget: up to one 8-minute review at claude-fable-5-1/max, one corrective retry only if needed, then up to five one-turn probes on claude-sonnet-5/low, sequential. Stop on usage or administrator-limit errors; do not purchase, raise limits or enable extra usage. This setup does not promise sufficient allowance or automatic recovery for arbitrary future campaigns.

**TLDR-end:** [snap: vals-login] Sonnet 5 remote dispatch is verified on mercury1. Fable returned an individual spending-limit error; interactive Fable explicitly prompts for separately purchased usage credits. Hyperturing scheduler access remains blocked independently.

Evidence interpretation: the initial Fable rejection was not provider-wide or a blanket one-shot restriction. The subsequent Sonnet one-shot succeeded. The reported total_cost_usd is client list-price accounting, not proof of a new credit purchase. No billing settings were changed.
