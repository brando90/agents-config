# Universal four-inbox blind copies

**Doc link:** <https://github.com/brando90/agents-config/blob/main/reports/email-bcc-all-four-10-16-2026.md>

**TLDR:** Every outgoing agent email must explicitly BCC all four Brando inboxes, including the sending account and any address already in To. Policy and active templates are published; this is not a claim that every already-running agent has reloaded them.

## Required recipients

```
brando.science@gmail.com
brando9@stanford.edu
brandojazz@gmail.com
brando@vals.ai
```

Deduplicate within BCC only. Preserve primary addressees and requested collaborator copies. There are no project substitutions; visible CC requires an explicit request and does not replace these BCC entries unless Brando explicitly overrides that requirement. Do not resend old messages merely to apply the new preference.

## Published changes and verification

- Rule change: `0c57898`; recovery-template follow-up: `746c847`.
- Both entry points, index, Rule 26, Rule 70, maintenance/email guidance, contacts, signature, response/recovery/landing rules and active job templates agree.
- The conflicting visible-copy instruction in `brando90/ultimate-utils/CLAUDE.md` was replaced and pushed in `bb0731f`.
- `python3 scripts/check_instruction_docs.py`: PASS, 89 routed rules and 280 checked local links. Entry files 6,136 bytes each; index 22,473 bytes.
- `python3 scripts/test_instruction_docs.py`: all nine tests pass. `git diff --check`: pass.

## Verified deployment scope

On the current Mac, `/Users/brandomiranda/.codex/AGENTS.md` and `.codex-vals/AGENTS.md` resolve to the shared entry, `.codex-su/AGENTS.md` routes to the shared index, and `.claude/CLAUDE.md` imports the shared entry. No default Codex override was present. The existing `.claude-vals/CLAUDE.md` lacked an import; an absolute import was added while preserving profile notes. This active Codex conversation reloaded the new entry and relevant details.

On skampere1, skampere2, skampere3, mercury1 and mercury2, read-only checks verified nonempty Codex and Claude global entries and the home CLAUDE link. The shared `/dfs/scratch0/brando9/agents-config` clone was fast-forwarded through `746c847`, preserving an unrelated deletion and local backup. The shared Vals Claude profile also lacked an import; `/dfs/scratch0/brando9/.claude-vals/CLAUDE.md` now imports the shared entry, preserving its notes. All five inspected Vals profile paths resolve to that shared file.

The separately configured `Sanmis-MacBook-Air.local` could not be resolved through Secure Shell (SSH) from this Mac; its on-disk deployment is unverified. No claim is made about gated compute nodes or unrelated hosts. A pull/import repair does not reload another running agent. Other sessions adopt the change when they refresh and read the shared rules; their current contexts were not inspected or interrupted.

## Verified send

The experiment START message `1a14670035f2ac4f` was sent on 10-16-2026. Gmail returned SENT and the stored headers showed From `brandojazz@gmail.com`, To `brando.science@gmail.com`, and BCC all four required addresses, including both From and To. This verifies one real send, not delivery to every downstream mailbox or universal behavior by other agents.
