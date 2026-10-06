# Maintenance: detailed rules

**Doc link:** <https://github.com/brando90/agents-config/blob/main/rules/maintenance.md>

**TLDR:** Read the matching rule sections when routed here by `~/agents-config/INDEX_RULES.md`; this is on-demand policy, not startup reading. Existing rule numbers remain stable.

## Hard Rule 2

2. **Verify before pushing.** Review diffs for secrets, unintended changes, broken imports.

## Hard Rule 6

6. **Refresh agents-config before each new user task.** At the start of every non-trivial user request: (1) `git -C ~/agents-config pull` to fetch remote changes, (2) re-read `~/agents-config/INDEX_RULES.md` into your active context so the current session has the latest rules and doc references, (3) if the pull brought changes, also re-read any changed machine or workflow files relevant to your current environment. For long sessions (over 1 hour), also refresh mid-task — check with `date` and compare to your last pull. Publish only your owned agents-config changes after verification; model review remains opt-in under Hard Rule 3.

## Hard Rule 7

7. **Agent CLI freshness.** Claude Code's `SessionStart` hook (`~/.claude/settings.json`) runs `~/agents-config/scripts/auto-update-tools.sh` on every session start. Major CLIs: `codex`, `claude` / `clauded`, `antigravity` (Google — replaces the deprecated Gemini CLI; install per https://antigravity.google). The old Gemini CLI must not be installed or used. Example extras: Cursor, Mistral, Harmonic, Axiom, and similar installed tools. If one looks stale, use the right package manager or print a one-line reminder with the exact update command. Never assume `npm` for a Homebrew-installed binary.

## Trigger Rule 6

6. **Commit, push, and re-read agents-config after any edit.** _Trigger: you or the user modify any file under `~/agents-config/`._ (1) Re-read the changed file(s) so your context stays current for the rest of the conversation. (2) Commit and push to the remote before continuing with the next task — other agents on other machines pull from this repo, so stale config causes drift. Also ensure project-level config files that reference agents-config (e.g., a project's `CLAUDE.md`) stay consistent.

## Trigger Rule 7

7. **Keep PRs short.** _Trigger: creating a pull request._ The PR description must start with a **Summary** section of at most 10 concise bullet points (fewer for small changes). Follow with a short **Test plan** (2–3 bullets). Include links to the experiment-folder Markdown report and relevant docs; link an existing optional Weights & Biases (W&B) report when relevant, but do not create one unless the user explicitly requests it. After these two sections, an optional **Appendix** may contain extended details, file lists, or context — but assume the reader stops after the summary. No walls of text.

## Trigger Rule 8

8. **Commit and push once verification passes.** _Trigger: the deterministic checks pass and, if Brando requested QA (Hard Rule 3), its verdict is PASS or FIXED with 0 critical issues._ Immediately `git commit` and `git push` without asking the user. Only escalate to the human if a requested QA verdict includes critical issues (CRITICAL_ISSUES > 0) or is FAIL. Major-only issues in non-active files (archives, historical results) do not block the commit.

## Trigger Rule 11

11. **Publish ultimate-utils to PyPI after QA-gated push to `master`.** _Trigger: QA passes on `~/ultimate-utils/` and changes are pushed to `master`._ After the QA-approved code is on `master`: (1) bump the `version` field in `~/ultimate-utils/pyproject.toml` (patch increment, e.g., `0.10.3` → `0.10.4`), (2) commit and push the version bump to `master`, (3) build and upload: `cd ~/ultimate-utils && bash scripts/publish_to_pypi.sh` (handles token auth from `~/keys/push-pypi-all.txt`, builds, checks, and uploads). This keeps Git and PyPI in sync so other machines and downstream users get the latest via `pip install ultimate-utils --upgrade`.

## Trigger Rule 17

17. **Run user tasks end-to-end; never ask mid-task.** _Trigger: any user task._ Flow: smoke → full E2E → deterministic verification, plus QA only if Brando requested it (Hard Rule 3) → commit + `git push` (Trigger Rule 8) → only then surface to the user. If mid-task verification is needed, run the deterministic checks for the task first; dispatch a reviewer only when Brando requested QA. Halt at smoke only on explicit ask ("smoke only", "stop after smoke").

## Trigger Rule 18

18. **Paper appendix / low-readership changes default to `main`.** _Trigger: a branch's only changes are to paper appendix files (e.g., `paper_latex_and_notes/.../9*_appendix*.tex`), factual / numeric refreshes from a completed eval run (table numbers, abstract numbers consistent with appendix tables), small polishing edits, or other sections few reviewers will read closely._ Merge directly to `main` without asking for per-merge approval (use `git merge --ff` if fast-forward, otherwise a small merge commit, or fast-merged PR — whichever the repo's convention). **Why:** few people read the appendix, so the cost of waiting on explicit human approval exceeds the cost of a small revert; as long as the content is correct and high-quality, defaulting to `main` keeps the trunk fresh and avoids stale feature branches. **How to apply:** First run `git diff --stat origin/main...<branch>` and skim the actual diffs. If everything is appendix / numeric refresh / typo fix, merge to main. If the branch also touches substantive claims (abstract argument changes, intro framing, method definitions, new headline numbers in main eval) **beyond** consistency with new appendix numbers, hold and ask. The user's explicit "don't push to main" overrides this rule for that branch.

## Trigger Rule 19

19. **Delete merged branches.** _Trigger: a feature / topic branch has been fully merged (or squashed / rebased) into `main`._ Immediately delete it both locally and on the remote: `git branch -d <name>` then `git push origin --delete <name>` — this is the standard post-merge cleanup. **Why:** keeps `git branch -a` uncluttered, removes "is this still in flight?" ambiguity, prevents accidental new commits on a finished topic. Recovery is trivial: the SHA lives on in main's merge commit (`<merge>^2`), so `git branch <name> <merge>^2` re-creates it. **How to apply:** `git branch -d` (lowercase) refuses if the branch isn't fully merged — trust that as your safety net; never escalate to `-D` without inspecting `git log <branch> --not main`. Skip for long-running release/integration branches (`release/*`, `dev`, `staging`) and shared collaboration branches that multiple agents are still pushing to.

## Guideline Rule 14

14. **Just do it.** Follow direct instructions immediately. Do not draft when told to send. Do not ask for confirmation unless the action is truly destructive (e.g., force-push to main, deleting production data).

## Guideline Rule 15

15. **Prefer references over full context loading.** Cite file paths as text (e.g., `~/agents-config/machine/mac.md`); load the file only when the task needs it. A "reference" here is a written path to a doc — not a symlink or memory address.

## Guideline Rule 16

16. **Keep `agents-config` self-consistent.** When modifying this repo, ensure INDEX_RULES.md, README.md, and listed doc paths remain accurate. Mirror shared behavior reminders in both `AGENTS.md` (Codex) and `CLAUDE.md` (Claude), with the full rule here or in its linked workflow. When configuring a host, verify the actual global instruction files are nonempty and resolve to the intended content; preserve existing local instructions when repairing links. Report the host, expanded paths and whether the running agent reloaded them—a successful pull alone does not establish that it did.

## Guideline Rule 18

18. **Always use `ls -la` (not `ls`) when listing directories for keys, tokens, configs, or credentials.** Hidden (dot-prefixed) files are common for sensitive data — plain `ls` omits them. This applies to any directory likely to hold secrets (e.g., `~/keys/`, `~/.ssh/`, `~/.config/`).

## Guideline Rule 21

21. **Check `~/keys/` for non-LLM credentials.** Before asking the user for non-LLM credentials, always check `~/keys/` first (`ls -la ~/keys/`). Common non-LLM files: `master_hf_token.txt` (HuggingFace), `brandos_wandb_key.txt` (W&B), `.brando90_github_token.txt` (GitHub), `push-pypi-all.txt` (PyPI), `gmail_app_password.txt` (Gmail SMTP). Load them transiently into the authorized tool or environment without printing secret values. **LLM-provider keys (`anthropic_*`, `openai_*`, `gemini_*`, `aristotle_*`) are excluded from this guideline** — per Hard Rule 9, agents may not load or use them; route LLM work through `clauded` / `codex` instead.

## Guideline Rule 22

22. **No hardcoded Node/nvm versions in `.bashrc` PATH prepends.** `nvm.sh` (sourced in `.bashrc`) already puts the active node's bin first in PATH. A hardcoded line like `export PATH=".../.nvm/versions/node/v24.14.0/bin:$PATH"` will silently shadow a newer node after `nvm install`, causing `npm install -g <tool>` to update one install while the shell runs another — the "please update" loop bug. See [`machine/snap.md`](../machine/snap.md) § "npm globals — update loop gotcha" for the diagnose/fix recipe.

## Guideline Rule 23

23. **Email: send from whichever of Brando's accounts is already signed in, and CC his other inboxes.** When told to send an email, send it from an account the agent can already use: the client's mail connector if it has one (as of 10-06-2026 Claude's Gmail connector is `brandojazz@gmail.com` and Codex's is `brando@vals.ai`), otherwise `uutils.emailing.send_email_smtp()` from `~/ultimate-utils/` (or `pip install ultimate-utils`) with `smtp_pass_file="~/keys/gmail_app_password.txt"`, which works on every SNAP node without browser auth. Do not hold an email for a particular sender address, a browser sign-in or a password-manager prompt (Brando, 10-06-2026: "sending a simple email should not need my approval or interaction in any way"). Brando's request to send is the go-ahead for that email; never create a draft when told to "send". Recipients per [`email-signature.md`](../email-signature.md) and Trigger Rule 26: internal notifications go to `brando.science@gmail.com` with no CC; emails to other people CC `brando@vals.ai` and `brandojazz@gmail.com` (minus whichever is the sender) so reply-all reaches both inboxes, and BCC `brando.science@gmail.com` for audit. Writing to Vals people from a personal address, add one line saying `brando@vals.ai` is cc'd. Contacts workflow: [`contacts.md`](../contacts.md).

## Guideline Rule 24

24. **Paper PDFs: see Trigger Rule 35.** Recompiling the PDF after a semantic `.tex` edit and keeping the compiled PDF committed is now a mandatory Trigger Rule, not a guideline.
