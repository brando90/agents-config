---
name: claude-app-session-sync
description: "Keep all Claude accounts in sync from agents-config (shared CLAUDE.md import, repo skills and refresh hooks in every profile), and make every Claude Code session of every account (personal ~/.claude, Vals ~/.claude-vals, Stanford ~/.claude-su) appear in the Claude desktop app's session list. Use when Brando says sessions are missing from the Claude app, after using clauded-vals / clauded-su in a terminal, after signing in to a different account in the app, or on a new Mac."
---

# claude-app-session-sync: all Claude accounts in sync

**TLDR:** Two scripts. `sync_claude_profiles.py` makes the personal, Vals and Stanford profiles load the same agents-config (CLAUDE.md import, every repo skill, the two refresh hooks). `sync_claude_app_sessions.py` lists all their sessions in the app. The Claude desktop app lists only sessions that have an index record. Terminal sessions (`clauded`, `clauded-vals`, `clauded-su`) leave only a transcript, so they never show up. Run `sync_claude_app_sessions.py`: it adds the missing records for the signed-in app account and copies missing transcripts into `~/.claude`, so each session can be opened and resumed. Quit the app (Cmd+Q) and reopen it afterwards.

## Profiles: same agents-config everywhere

```bash
python3 ~/agents-config/skills/claude-app-session-sync/sync_claude_profiles.py          # dry run per profile
python3 ~/agents-config/skills/claude-app-session-sync/sync_claude_profiles.py --apply
```

For `~/.claude`, `~/.claude-vals`, `~/.claude-su` it adds, if missing: the `@~/agents-config/CLAUDE.md` import, a symlink to every `skills/<name>` folder, and the `auto-update-tools.sh` / `refresh-agents-config.sh` hooks. Skills are symlinks into the repo, so a `git pull` updates all accounts at once. It never replaces an existing skill, hook or text, backs up each edited file as `<file>.bak-ac-sync-<date>`, and is idempotent. Rerun it after adding a skill to `skills/` (new sessions pick it up). Settings that are per account (model, effort, theme, the personal Herdr hook) stay as they are. Verified 11-02-2026: Vals had no hooks and no skills, Stanford had no CLAUDE.md import; all three now report "already in sync".

## Sessions: why Vals sessions were missing (found 11-02-2026)

- App index: `~/Library/Application Support/Claude/claude-code-sessions/<account uuid>/<org uuid>/local_<uuid>.json`, one folder per signed-in account/org. The app shows only the folder of the account it is signed in as.
- Personal sessions were already copied into the Vals folder once by hand (75 records). The terminal sessions under `~/.claude-vals/projects` and `~/.claude-su/projects` have no record at all, and the app resumes only from `~/.claude/projects`.
- Interactive sessions are listed; headless worker runs (`entrypoint` sdk-cli, `claude -p`) are skipped unless `--include-headless`, so the list is not flooded.

## Use

```bash
python3 ~/agents-config/skills/claude-app-session-sync/sync_claude_app_sessions.py            # dry run: counts and a sample
python3 ~/agents-config/skills/claude-app-session-sync/sync_claude_app_sessions.py --apply    # write, with a backup first
```

Then Cmd+Q the Claude app (closing the window is not enough: a running app does not reread the index) and reopen it.

- Target is the signed-in account (`CLAUDE_CODE_ACCOUNT_UUID` / `CLAUDE_CODE_ORGANIZATION_UUID`), else the most recently used folder; `--target <account>/<org>` overrides it.
- Additive and idempotent: it never overwrites a record or a transcript; a second run reports 0 to create. Every `--apply` first copies the target folder to `claude-code-sessions-backup-<date-time>/` next to it; restore by copying that back.
- Titles come from the transcript's own title, else the first prompt. Vals and Stanford sessions get a `[Vals]` / `[Stanford]` prefix (`--no-tag` to drop it).
- Needs Python 3 only. No credentials are read or copied; only session metadata and transcripts move.

## Limits

- A session resumed from the app is written into `~/.claude/projects`, so later turns live there and not in the original profile; the original transcript stays untouched.
- Billing follows the account the app is signed in as, not the profile the session started in. Switch accounts in the app for Vals-funded work.
- The index format is the app's private format (verified on app 4.4212.0, CLI 2.1.309). If a later update stops listing the records, check the fields against a record the app wrote itself.
