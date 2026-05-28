# Standing Order — Stanford AI for Lean Announcements

**TLDR:** Drafts and sends meeting announcements, speaker invites, recruiting messages, and grant broadcasts for the Stanford AI for Lean community ([aiforlean.org](https://aiforlean.org)). Multi-channel: mailing list + Discord/Slack. Approval required per send.

## Goal

Reduce the friction of running a research community: same templates, same recurring rhythms, same approval pattern as everything else OpenClaw does.

## When this fires

- **Brando-initiated (Telegram)** — `/leanai meeting <date> <topic>` — drafts a meeting announcement.
- **Brando-initiated (Telegram)** — `/leanai recruit <role>` — drafts a recruiting message.
- **Brando-initiated (Telegram)** — `/leanai grant <funder>` — drafts a grant-opportunity broadcast.
- **Cron (optional)** — weekly reminder draft at T-24h before recurring meeting; Brando approves or skips.

## Inputs

1. **Message type** — meeting / speaker-invite / recruiting / grant-broadcast / follow-up.
2. **Variables** — date, topic, speaker name, role description, funder, etc.
3. **Target channels** — mailing list (default), Discord, Slack (per channel-specific approval).

## Workflow

1. **Capture**: Brando command + variables.
2. **Classify** message type.
3. **Draft** from `config/leanai_templates/<type>.md`.
4. **Show**: rendered preview per channel.
5. **Approve (Brando)**: `post` / per-channel edits / `cancel`.
6. **Execute**: mailing list via Gmail send (`gog gmail send --to <list-address>`); Discord/Slack via channel-specific connector.
7. **Log**: `~/openclaw/audit/leanai_announcements.jsonl`.

## Outputs

- Sent announcement(s) per approved channel.
- Audit log entry.

## Safety rules

- **Approval level:** `never_autonomous` (mailing list = bulk).
- **`confirm-bulk` token** required for mailing-list send.
- **Cross-post timing** — recommend separate sends > 30 min apart so subscribers don't get hit on multiple channels back-to-back.

## Open setup questions

1. **Mailing list address** — what's the official aiforlean.org list?
2. **Discord / Slack ID** — does the community use Discord, Slack, or both? Where do meeting announcements go today?
3. **Templates** — populate `config/leanai_templates/` (meeting, recruiting, grant, follow-up).
4. **Brando's role** — participant / co-organizer / lead? Affects what Brando is authorized to send vs. just draft for someone else.

## Recurring sub-templates

### Monthly workhackathon nudge

Specific instance of the `meeting / grant-broadcast` flow above. Lives here rather than as a separate standing order because it reuses every other section of this file (templates, audit log, safety rules, approval flow).

**Goal.** Once a month, ask the Lean AI Club leadership Discord channel + Fred / Henry B / Eric Pineda by email about the state of using the $10k Lean AI grant to host a monthly co-working session at Stanford CoHo (food + nice snacks + group work for a few hours).

**Trigger.** `openclaw cron add --name "lean-ai-workhackathon" --cron "0 10 1 * *" --tz "America/Los_Angeles"` (10am on the 1st of each month). Plus first-run manual: Brando DMs *"fire workhackathon nudge"* and the agent runs the full flow once.

**Channels.**
1. Discord — leadership channel of Lean AI Club server (channel name TBD by Brando).
2. Email — to Fred / Henry B / Eric Pineda (full emails TBD), CC `brando.science@gmail.com` for auditability per [`INDEX_RULES.md`](../../../INDEX_RULES.md) Trigger Rule 26; add Stanford/personal CCs only if Brando explicitly asks.

**Discord draft.**

> hey team — quick check: what's the state of accessing the $10k lean ai grant for monthly workhackathons? thinking once a month at coho, nice food + snacks, group work session for a few hours. who's the right person to start the budget request with? happy to draft a one-pager if useful.

**Email draft.**

- **Subject:** `lean ai workhackathon — $10k grant access status`
- **Body:** same content as the Discord message, slightly more formal framing (one paragraph). Lowercase, direct, no "I hope this finds you well".

**Approval flow.** Same as parent — agent renders both, DMs Brando in Telegram with combined preview, awaits `post / edit-discord: / edit-email: / cancel`. On `post`: posts Discord first (lower-stakes), waits 30s, sends email; applies Gmail label `lean-ai-club-nudge-<YYYY-MM>` for idempotency.

**Cadence + idempotency.** One run per calendar month. Agent skips if a `lean-ai-club-nudge-<YYYY-MM>` Gmail label already exists for the current month — protects against double-fire if cron triggers twice or instances race.

**Prereqs.**
- [ ] Discord intent enabled + bot invited to Lean AI server (per [`MASTER_PLAN.md`](../MASTER_PLAN.md) Appendix E "Current pickup state" — Discord row marked 🟡 blocked)
- [ ] Bot has post permissions in #leadership channel
- [ ] Fred / Henry B / Eric Pineda emails captured (Brando provides)
- [ ] Lean AI Club Discord server name + leadership channel name (Brando provides)

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.5 of [`MASTER_PLAN.md`](../MASTER_PLAN.md). |
| 2026-05-08 | Added "Monthly workhackathon nudge" sub-template (Discord + email about $10k grant for CoHo co-working). Blocked on Discord intent + Fred/Henry/Eric emails. |
