# TODO: Make Codex QA Work on SNAP Cluster (skampere nodes)

**GitHub Issue:** [brando90/agents-config#31](https://github.com/brando90/agents-config/issues/31)

## Problem

`codex exec --full-auto` fails on SNAP cluster nodes (skampere1, skampere2, etc.) because
the default bubblewrap (bwrap) sandbox tries to create a network namespace, which requires
`CAP_NET_ADMIN` — not available to unprivileged users on shared cluster nodes:

```
bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted
```

This blocks the cross-agent QA chain (Hard Rule 3 in `~/agents-config/INDEX_RULES.md`),
which requires Claude Code to dispatch `codex exec --full-auto "<review prompt>"`.

## Root Cause

Codex CLI 0.115.0 defaults to bubblewrap (bwrap) for Linux sandboxing. Bwrap requires
user namespace support for network isolation. SNAP cluster nodes restrict unprivileged
user namespaces, so bwrap fails before any command runs.

## Fix (applied 2026-04-09)

- [x] **Switch sandbox to landlock.** Set `use_legacy_landlock = true` in `~/.codex/config.toml`.
      Landlock is a Linux kernel security module (5.13+) that doesn't need user namespaces.
      Tested and confirmed working on skampere1 (kernel 6.8.0-101-generic).

- [x] **Inherit env vars.** Set `shell_environment_policy.inherit = "all"` in config.toml
      so Codex inherits `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc. from the parent shell.

- [x] **Verify.** `codex exec --full-auto "echo hello && git log --oneline -3"` succeeds
      on skampere1 with landlock.

- [x] **Document in agents-config.** Added bwrap fix to `~/agents-config/machine/snap.md`
      Common Issues section.

- [x] **Add auto-fallback to QA dispatch.** Updated `~/agents-config/workflows/qa-correctness.md`
      with `||` fallback so QA completes even if Codex fails.

## Config applied (`~/.codex/config.toml` on skampere1)

```toml
[features]
use_legacy_landlock = true

[shell_environment_policy]
inherit = "all"
```

## Remaining items

- [ ] **Replicate on other SNAP nodes.** Copy the config to skampere2, skampere3, etc.
      (or symlink `~/.codex/config.toml` since home is shared NFS — verify this).

- [ ] **Test full QA dispatch end-to-end.** After a real Claude Code task completes, run
      the full QA correctness prompt from `~/agents-config/workflows/qa-correctness.md`
      via `codex exec --full-auto` and confirm it produces the VERDICT block.

- [ ] **Test with file writes.** Confirm Codex can apply fixes (FIXED verdict) when the
      QA review finds issues. Landlock's `workspace-write` mode should allow writes
      to the repo working directory.

- [ ] **Test network access (if needed).** Landlock does NOT restrict network by default
      (unlike bwrap). Verify that Codex can make API calls (e.g., for `--search` mode
      or MCP servers) if future QA steps require it. For current QA (git diff + review),
      network is not needed.

- [ ] **Pin Codex version.** If a future Codex update changes sandbox defaults or removes
      the `use_legacy_landlock` flag, the fix breaks. Note the working version (0.115.0)
      and test after upgrades.

## Quick reference

```bash
# QA dispatch from Claude Code on SNAP nodes (now works):
codex exec --full-auto "Review all changes in this directory since the last commit on main. ..."

# Manual test:
codex exec --full-auto "echo hello && pwd && git status"

# If config.toml is missing/wrong, one-shot override:
codex exec --full-auto --enable use_legacy_landlock "..."
```
