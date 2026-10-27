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

## Round 2 (Brando approved the refactoring on 10-27-2026, minimal deletions)

Moved with `git mv` (nothing deleted, links rewritten, relative links inside moved files fixed):
- `machine/*-10-22-2026.*` (8 dated proof files) to `archive/machine-proofs/`.
- `experiments/01_self_hosted_openclaw/` to `archive/experiments/`.
- `workflows/jazz-playalongs/` to `archive/non-agent/`.
- README gained a file map with a Kind column.

Left in place because live code or core docs read them: `dotfiles/legacy/` (read by `tests/test_install_dotfiles.py`), `docs/instruction-audit/` (read by `scripts/check_instruction_docs.py` and the startup docs), `workflows/assets/` (linked from many guides).

## Stage 2 (AT-1626, Brando said go on 10-27-2026)

- One skills folder: `config/pi/skills/{atlas,sbsbz-cardinal-print-flyers,sbsbz-financial-officer}` moved to `skills/` with `git mv`. The two `pi-local-herdr` copies were merged into `skills/pi-local-herdr/SKILL.md` (Pi copy for the Sherlock/FarmShare state, the `skills/` copy for lines 57 and 62, which carry the merged-PR text); the other copy's files were identical apart from `SKILL.md`. The old Pi copy is kept in `archive/pi-local-herdr-pi-copy-2026-10-27/` (SKILL.md and agents/openai.yaml); removing it is part of Stage 3 and waits on Brando's word.
- `config/pi/skills` is now a relative link to `../../skills`, so live links on the Mac and SNAP nodes keep resolving. `config/pi/auto_sync.py` and `config/pi/sync_runtime.py` accept that one link (`shared_skills_link`) and still refuse every other symlink; `config/pi/test_auto_sync.py` and `test_sync_runtime.py` cover it.
- The 17 `scripts/test_*.py` files moved to `scripts/tests/` (with `git mv`); path lookups point at `scripts/`, and `scripts/tests/_path.py` puts `scripts/` on `sys.path`. Run all: `python3 -m unittest discover -s scripts/tests -p 'test_*.py'`.
- Rollout order and recovery for hosts that have not pulled yet are in [skills/README.md](../skills/README.md); `scripts/refresh-agents-config.sh` now warns when a real `config/pi/skills` folder blocks the pull. `docs/instruction-audit/inventory.tsv` keeps the old test paths (dated receipt).

## Proposed, not done (needs Brando's word)

1. ~~Reconcile the `pi-local-herdr` duplicate~~ Reconciled into one folder in Stage 2 above. **Still to do (Stage 3):** delete the archived old Pi copy, `archive/pi-local-herdr-pi-copy-2026-10-27/`.
2. ~~Move `config/pi/skills/*` into `skills/`~~ Done in Stage 2 above.
3. **Stale candidates:** `archive/experiments/01_self_hosted_openclaw/` (his earlier OpenClaw assistant attempt, superseded), `dotfiles/legacy/`, `machine/*-10-22-2026.*` proof files, `docs/instruction-audit/` (one-time receipt), `archive/non-agent/jazz-playalongs/` (not agent config), `workflows/assets/` (talk transcript).
4. **Remote branches:** 60+ merged or abandoned remote branches; list with `git branch -r --merged origin/main` for his review before any deletion.
