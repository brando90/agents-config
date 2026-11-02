#!/usr/bin/env python3
"""Make every Claude Code profile (personal ~/.claude, Vals ~/.claude-vals, Stanford ~/.claude-su)
load the same agents-config: shared CLAUDE.md import, repo skills, and the two refresh hooks.

Additive and idempotent. Never replaces an existing skill, hook or CLAUDE.md text; each file it
edits is first copied to <file>.bak-ac-sync-<date>. Dry run unless --apply. Holds no credentials.
"""
import argparse, json, os, shutil, time

HOME = os.path.expanduser("~")
AC = os.path.join(HOME, "agents-config")
PROFILES = [".claude", ".claude-vals", ".claude-su"]
IMPORT = f"@{AC}/CLAUDE.md"
HOOKS = {  # event -> (matcher-less command, extra fields); same commands the personal profile uses
    "SessionStart": {"type": "command", "command": "bash ~/agents-config/scripts/auto-update-tools.sh",
                     "timeout": 60, "async": True},
    "UserPromptSubmit": {"type": "command", "command": "bash ~/agents-config/scripts/refresh-agents-config.sh",
                         "timeout": 20, "statusMessage": "Refreshing agents-config"},
}
STAMP = time.strftime("%m-%d-%Y")


def backup(path, apply):
    if apply and os.path.exists(path):
        shutil.copy2(path, f"{path}.bak-ac-sync-{STAMP}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    skills = sorted(d for d in os.listdir(os.path.join(AC, "skills"))
                    if os.path.isfile(os.path.join(AC, "skills", d, "SKILL.md")))
    for prof in PROFILES:
        root = os.path.join(HOME, prof)
        if not os.path.isdir(root):
            print(f"{prof}: missing, skipped"); continue
        todo = []
        # 1) CLAUDE.md imports the shared entry point
        cm = os.path.join(root, "CLAUDE.md")
        text = open(cm).read() if os.path.exists(cm) else ""
        if IMPORT not in text:
            todo.append("CLAUDE.md import")
            if a.apply:
                backup(cm, True)
                with open(cm, "a") as f:
                    f.write(("\n" if text and not text.endswith("\n") else "") +
                            ("\n" if text else "") + "## Shared agent instructions\n\n" + IMPORT + "\n")
        # 2) repo skills linked (a real folder or any existing link of that name is left alone)
        sd = os.path.join(root, "skills")
        missing = [s for s in skills if not os.path.lexists(os.path.join(sd, s))]
        if missing:
            todo.append("skills " + ",".join(missing))
            if a.apply:
                os.makedirs(sd, exist_ok=True)
                for s in missing:
                    os.symlink(os.path.join(AC, "skills", s), os.path.join(sd, s))
        # 3) refresh hooks present (matched by script name, so a user's variant is kept)
        sp = os.path.join(root, "settings.json")
        cfg = json.load(open(sp)) if os.path.exists(sp) else {}
        hooks, added = cfg.setdefault("hooks", {}), []
        for ev, h in HOOKS.items():
            script = h["command"].split("/")[-1]
            if not any(script in x.get("command", "") for g in hooks.get(ev, []) for x in g.get("hooks", [])):
                hooks.setdefault(ev, []).append({"hooks": [h]}); added.append(ev)
        if added:
            todo.append("hooks " + ",".join(added))
            if a.apply:
                backup(sp, True)
                json.dump(cfg, open(sp, "w"), indent=2); open(sp, "a").write("\n")
        print(f"{prof}: " + ("; ".join(todo) if todo else "already in sync"))
    if not a.apply:
        print("dry run; add --apply to write")


if __name__ == "__main__":
    main()
