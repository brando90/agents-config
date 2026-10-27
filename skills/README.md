# Skills index

**Doc link:** <https://github.com/brando90/agents-config/blob/main/skills/README.md>

**TLDR:** Every skill is a folder with a `SKILL.md`, and all of them live in this one folder. `config/pi/skills` is a link to it, so the Pi installer and the auto-sync service link every skill here into `~/.codex/skills`, `~/.claude/skills` and `~/.agents/skills`.

## Skills

| Skill | What it does |
|---|---|
| [`atlas`](atlas/SKILL.md) | macOS AppleScript control of the ChatGPT Atlas desktop app (tabs, bookmarks, history). |
| [`pi-local-herdr`](pi-local-herdr/SKILL.md) | Local Pi (Gemini and Ollama) and Herdr machine profiles. |
| [`research-launch-stack`](research-launch-stack/SKILL.md) | Kesh-style paper launch bundle: project page, tweprint, blog draft, links, asset manifest. |
| [`review-paper`](review-paper/SKILL.md) | Paper review in Brando's words (moved here from `writing/ml_research/`). |
| [`sbsbz-cardinal-print-flyers`](sbsbz-cardinal-print-flyers/SKILL.md) | Stanford Bachata flyer printing. |
| [`sbsbz-financial-officer`](sbsbz-financial-officer/SKILL.md) | Stanford Bachata financial-officer duties and invoice checks. |

Personal skills with private content go in the Git-ignored `config/pi/private-skills/` and are never committed.

## Re-install on each host (optional)

No re-install is needed for the move. `config/pi/skills` is a link to this folder, so the live links (for example `~/.claude/skills/atlas` pointing at `~/agents-config/config/pi/skills/atlas`) still resolve after `git pull`. To make the links point at the new path and to pick up `research-launch-stack` and `review-paper`, run once per host (the Mac and the five SNAP nodes) after pulling:

```
python3 ~/agents-config/config/pi/install.py --runtime-only --adopt-skill-copies
```

If the installer reports a duplicate skill name, run `ls -l ~/.claude/skills ~/.codex/skills ~/.agents/skills` and remove the stale copy it names.
