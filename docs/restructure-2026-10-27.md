# Restructure toward a Pi-agent-style layout (10-27-2026)

**Doc link:** <https://github.com/brando90/agents-config/blob/main/docs/restructure-2026-10-27.md>

**TLDR:** This change moves root clutter, dated records and one skill into their own folders, with every in-repo link rewritten and nothing deleted. Deletions and the live-synced skill move are proposed below and wait for Brando's word.

## Target shape

Small core (`AGENTS.md`, `CLAUDE.md`, `INDEX_RULES.md`, `CATALOG.md`, `rules/`), skills each in a folder, machine notes in `machine/` and `config/`, personal data in `personal/`, records in `experiments/`, `archive/` and `docs/`.

## What moved (all with `git mv`, history kept)

| From | To |
|---|---|
| `contacts.md`, `email-signature.md` | `personal/` |
| `todo_*.md`, `codex_remote_control_todo.md`, `cursor_ssh_kerberos_todo.md` | `docs/todo/` |
| `init_no_passwords_snap_kinit.md`, `koyejo_stair_cluster_guide.md` | `machine/` |
| `writing/ml_research/review-paper/` | `skills/review-paper/` |
| `reports/`, `reviews/`, `workflows/qa-reports/` | `archive/reports/`, `archive/reviews/`, `archive/qa-reports/` |

New: `skills/README.md` (index of every skill and where it lives), a rewritten Directory Structure section in `README.md`. Links in rules, workflows, machine notes, README and CATALOG were rewritten to the new paths. `docs/instruction-audit/inventory.tsv` is a dated receipt and keeps the old paths.

## Checks run

- `scripts/check_instruction_docs.py`: PASS before and after (AGENTS.md and CLAUDE.md stay inside the 6240-byte budget).
- Markdown link check over the whole repo: 9 findings before, the same 9 after (pre-existing, mostly placeholders).
- `config/pi` unit tests (39) and `tests/test_install_dotfiles.py`: pass.
- `docs/instruction-audit/verify_migration.py` fails on main already (`hard-8`) and fails the same way after; it is a one-time receipt.

## Left in place on purpose

- `claude-code-settings.json` and `bm-agents-config.code-workspace`: `claude-code-settings.json` is the Claude Code hook config (its hook calls `scripts/refresh-agents-config.sh`) and is symlinked to `~/.claude/settings.json` per `machine/mac.md`; the workspace file is whitelisted in `.gitignore`.
- `config/pi/skills/` (atlas, pi-local-herdr, sbsbz-cardinal-print-flyers, sbsbz-financial-officer): the Pi installer, `runtime.json` and live symlinks on enrolled machines point there. Moving them into `skills/` needs a re-install on each host.
- Other agents outside this repo may still read `~/agents-config/contacts.md` or `~/agents-config/email-signature.md` by the old path (`contacts.md`, `email-signature.md`, `init_no_passwords_snap_kinit.md`, `todo_infinite_reauth_kinit_server_side.md`); the in-repo routes are updated. A few `../` link simplifications in `workflows/broad-investigation.md` are incidental and resolve the same.

## Proposed, not done (needs Brando's word)

1. **Reconcile, then delete** `skills/pi-local-herdr/`: it duplicates `config/pi/skills/pi-local-herdr/` and only `SKILL.md` differs (lines 8, 34, 57, 62). The `skills/` copy has the newer commit (10-26-2026, a port of a 10-22 branch) but partly older content; the Pi copy (10-24-2026, the one the installer links) carries the later Sherlock/FarmShare state (`machine/herdr-stanford-access.md`). Reconcile line by line with the Pi copy authoritative for that state, then remove the `skills/` one and repoint the links in `CATALOG.md` line 25 and `machine/mac-pi-herdr-10-22-2026.md` line 35.
2. **Move** `config/pi/skills/*` into `skills/` and point `config/pi/runtime.json` at it, then run the installer with `--adopt-skill-copies` on the Mac and the five SNAP nodes.
3. **Stale candidates:** `experiments/01_self_hosted_openclaw/` (his earlier OpenClaw assistant attempt, superseded), `dotfiles/legacy/`, `machine/*-10-22-2026.*` proof files, `docs/instruction-audit/` (one-time receipt), `workflows/jazz-playalongs/` (not agent config), `workflows/assets/` (talk transcript).
4. **Remote branches:** 60+ merged or abandoned remote branches; list with `git branch -r --merged origin/main` for his review before any deletion.
