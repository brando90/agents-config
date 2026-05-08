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

## Status

| Date | Status |
|------|--------|
| 2026-05-08 | Skeleton drafted. Setup questions pending. Implementation deferred until Phase 6.5 of [`MASTER_PLAN.md`](../MASTER_PLAN.md). |
