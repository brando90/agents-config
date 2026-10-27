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

The old Pi copy of `pi-local-herdr` is kept in [`archive/pi-local-herdr-pi-copy-2026-10-27/`](../archive/pi-local-herdr-pi-copy-2026-10-27/); deleting it is part of Stage 3 and waits on Brando's word.

## Rolling this out to the hosts

No re-install is needed. `config/pi/skills` is a link to this folder, so live links (for example `~/.claude/skills/atlas` pointing at `~/agents-config/config/pi/skills/atlas`) keep resolving after `git pull` and are not rewritten. Enrolled hosts link the two skills that are new to the sync (`research-launch-stack`, `review-paper`) through the auto-sync service by themselves.

Order matters: pull on every enrolled host (the Mac and the SNAP shared checkout) at about the same time. A host that has not pulled yet receives the new skill files from the auto-sync hub into its old real `config/pi/skills/` folder, and its next `git pull` then stops with "config/pi/skills ... Aborting" (the refresh hook prints a warning). Recovery on that host:

```
git -C ~/agents-config status --short config/pi/skills
# move the listed files into ~/Desktop/skills-aside/ (they are copies of files that now live in skills/), then:
git -C ~/agents-config pull --ff-only
```

If the installer ever reports a duplicate skill name, run `ls -l ~/.claude/skills ~/.codex/skills ~/.agents/skills` and remove the stale copy it names.
