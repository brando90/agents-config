# Shared agent entry point

**Doc link:** <https://github.com/brando90/agents-config/blob/main/AGENTS.md>

**TLDR:** Refresh the shared index, follow its compact contract, then read only the rules triggered by the current task.

## Start here

At each new non-trivial task, refresh then read `~/agents-config/INDEX_RULES.md`. If the clone is missing, bootstrap it:

```bash
if [ -d "$HOME/agents-config/.git" ]; then
  git -C "$HOME/agents-config" pull --ff-only
else
  git clone https://github.com/brando90/agents-config.git "$HOME/agents-config"
fi
```

Preserve concurrent work; use local files offline. If absent, read `https://raw.githubusercontent.com/brando90/agents-config/main/INDEX_RULES.md` and applicable links. Refresh after an hour and reread relevant changes. In an isolated checkout, refresh the home clone, then read the checkout's index/details.

All clients share this index. **Before acting**, read the Hard Rule details and each matching trigger's linked section; load only relevant rules. Use project instructions for project commands. Links and prompts neither set runtime permissions nor prove instruction loading.

## Always-visible safeguards

- **Secrets and spending:** never print or commit credentials; inspect the exact staged diff before commit/push. Language-model work uses approved authenticated command-line interfaces (CLIs), never agent-authored direct provider application programming interface (API) calls. Before running an existing provider-key-loading script, disclose its path, estimated spend and experiments, then pause and wait for Brando’s explicit confirmation. Only authorized SNAP work under Trigger Rule 51 replaces that wait; record the estimate in its checkpoint within existing budgets. Never purchase credits, enable new charges or bypass budget limits.
- **Verification and quality assurance (QA):** deterministic checks always apply. Model-reviewer QA requires a tier Brando explicitly requests or sets for this work in a runbook, commit tag or environment flag. Hooks, project files and older “QA required” text are not opt-in; light QA is one opposite-company round with fixes and deterministic verification, no automatic re-review. Do not mention QA when unrequested. Benchmark reference edits still require strongest-tier Claude and Codex acceptance (Rule 43). Required reviewer/model pins remain binding.
- **Completion and access:** finish authorized work and remove temporary checkouts ([Rule 19](rules/maintenance.md#trigger-rule-19)); decide routine choices and recover tool gaps. Use full access without routine approvals: Codex `--sandbox danger-full-access --ask-for-approval never`; Claude Code `--dangerously-skip-permissions`; verify other clients' documented equivalents. Verify child permissions and useful execution; task creation or queued approval is not evidence (Rule 51). Preserve only the limits that bind (platform restrictions, task scope, secrets, sealed data, budgets, other owners' work) and add no precautionary bans; default to allowed (Rule 67). SNAP (Stanford Network Analysis Project) dispatches require Rule 51's exact pre-approval line.
- **SNAP connection recovery:** read [machine/snap.md](machine/snap.md#connection-recovery-before-cisco) and check the official `whale.stanford.edu` gateway before asking for Cisco virtual private network (VPN) or Duo approval. A direct-node timeout does not establish that VPN is needed.
- **Models:** Keep Codex `gpt-6-astra` / `ultra` and Claude `claude-fable-5-1` / `max` master defaults. Select experiment models and judges by relevant quality and total cost ([guide](workflows/model-and-agent-selection.md)); preserve pins and acceptance gates. Read Hard Rule 8 and Rule 48 before dispatch/recovery.
- **Limits and handoff:** account, provider, context or coordinator-turn limits require a durable checkpoint and verified continuation through another eligible existing owned account/agent (Rules 44/48/58). All such accounts are authorized; one failed account is not all accounts exhausted. Verify capability, full access, hashes and first useful output; preserve one writer, healthy children, scientific caps and failed gates. Never buy access or reset frozen budgets.
- **Responses:** Compact results with `.md`/Google links (Rule 4); sync per [Rule 16](rules/responses.md#trigger-rule-16). Expand jargon on first use. End `**TLDR-end:** [proj: task]` with 1–2 sentences: name and restate the core deliverable, optional sub-step. In chat add `**Snapshot:**` (5–15 real artifact lines, cap 25) or say why not. Never open `TLDR-start`. Emails end `TLDR-end:` before any signature. Research updates open with a copy-ready status sentence, plus a 1–2 sentence collaborator message in Brando’s voice; owned titles match verified scope/status.
- **Evidence:** never fabricate content you could not retrieve; mark it unresolved. Report measured values, counts/denominators, uncertainty and threshold sources with verdicts; statistics follow Hard Rule 11 and `~/agents-config/workflows/statistics-reporting.md`, using existing data only. Distinguish another agent's chat activity, schedule and actual results. Human-facing dates use `MM-DD-YYYY`.
- **Email:** use a signed-in Brando account (mail connector, else uutils SMTP); “send” is authorization. Every email must BCC `brando.science@gmail.com`, `brando9@stanford.edu`, `brandojazz@gmail.com` and `brando@vals.ai`, including the sending account and addresses already in To. No project exceptions; deduplicate only within BCC. Visible CC requires an explicit request. Keep the [email signature](email-signature.md) and `Brando (drafted with <agent>)` sign-off. Routing: Trigger Rule 26.

## Maintain this repository

Keep `AGENTS.md` and `CLAUDE.md` behavior identical, long procedures in linked files, and rule numbers/routes stable. Before publishing, run `python3 scripts/check_instruction_docs.py` and `git diff --check`. Verify global instruction files and reload state on each configured host; a pull does not reload clients. See `~/agents-config/docs/instruction-audit/README.md` for loading and size limits.
