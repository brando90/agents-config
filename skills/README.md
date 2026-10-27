# Skills index

**Doc link:** <https://github.com/brando90/agents-config/blob/main/skills/README.md>

**TLDR:** Every skill is a folder with a `SKILL.md`. Skills in this folder are plain repo skills; four Pi-synced skills still live in `config/pi/skills/` because the Pi installer and the auto-sync service link them into `~/.codex/skills`, `~/.claude/skills` and `~/.agents/skills` from there.

## In `skills/`

| Skill | What it does |
|---|---|
| [`research-launch-stack`](research-launch-stack/SKILL.md) | Kesh-style paper launch bundle: project page, tweprint, blog draft, links, asset manifest. |
| [`review-paper`](review-paper/SKILL.md) | Paper review in Brando's words (moved here from `writing/ml_research/`). |
| [`pi-local-herdr`](pi-local-herdr/SKILL.md) | Duplicate of the Pi/Herdr skill below; this copy has the newer 10-26 text, the Pi-synced copy is the one the installer links. To be reconciled, then removed, with Brando's word. |

## In `config/pi/skills/` (canonical, Pi-synced)

| Skill | What it does |
|---|---|
| [`atlas`](../config/pi/skills/atlas/SKILL.md) | macOS AppleScript control of the ChatGPT Atlas desktop app (tabs, bookmarks, history). |
| [`pi-local-herdr`](../config/pi/skills/pi-local-herdr/SKILL.md) | Local Pi (Gemini and Ollama) and Herdr machine profiles. |
| [`sbsbz-cardinal-print-flyers`](../config/pi/skills/sbsbz-cardinal-print-flyers/SKILL.md) | Stanford Bachata flyer printing. |
| [`sbsbz-financial-officer`](../config/pi/skills/sbsbz-financial-officer/SKILL.md) | Stanford Bachata financial-officer duties and invoice checks. |

Personal skills with private content go in the Git-ignored `config/pi/private-skills/` and are never committed.

## Moving the Pi-synced skills here

Not done in this change: the installer, `runtime.json` and live symlinks on enrolled machines point at `config/pi/skills/`, so moving them needs a coordinated re-install (`config/pi/install.py --runtime-only --adopt-skill-copies`) on each host. See [docs/restructure-2026-10-27.md](../docs/restructure-2026-10-27.md).
