# Vals setup checkpoint

**TLDR:** Continue node setup from this isolated checkout; protect the separate Vals grant and preserve other sessions.

Created: 2026-09-14 13:22 PDT
Last updated: 2026-09-14 13:22 PDT

- Owner: Codex task 01a0a18c-93b6-7b23-a940-b9804f6318d6 on Sanmi MacBook Air.
- Branch: snap-vals-access-20260914; base 3fedd59c0031c31c082bd490633d9824cc7f9b46.
- Local checkout: /Users/sanmikoyejo-mba-1/.codex/vals-snap-setup/repo.
- Remote grant: /dfs/scratch0/brando9/.claude-vals-remote/oauth-token; never print/copy to repository.
- Installer works on mercury1. Sonnet interactive and one-shot passed; Fable blocked by credit policy. Independent Codex review running in local tmux snap-vals-code-review-20260914. Next inspect ../codex-review.jsonl and apply findings before activating canonical wrappers.
- Exact models: builder gpt-6-astra; acceptance claude-fable-5-1/max; probes claude-sonnet-5/low.
- No campaign workers dispatched; short setup/review only, no unattended recovery claim.
- Blockers: user has no Slurm association; skampere3 connection stalled; disk percentage failures on several nodes.
