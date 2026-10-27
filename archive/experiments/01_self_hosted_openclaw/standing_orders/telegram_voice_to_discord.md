# Standing Order: Telegram Voice to Discord Routing

**TLDR:** Desired behavior is "Brando can ask the mercury2 Telegram OpenClaw bot to post to Discord," but this is not active yet. As of 2026-06-04, Telegram and Discord are connected independently; Telegram-to-Discord routing is blocked on Discord target visibility, cross-channel send approval/workflow, and voice transcription approval.

## Status

| Surface | Status | Evidence / blocker |
| --- | --- | --- |
| Telegram bot reply | Ready | `tools.profile=messaging`; Telegram reports `running, connected`. |
| Discord bot login | Ready | Discord reports `running, connected` as `@ultimate_brando9_bot`. |
| Raw Discord CLI send | Needs target | `openclaw directory groups list --channel discord` and peer lookup returned no visible targets on mercury2. |
| Telegram text to Discord | Not ready | Telegram-bound sessions hit `Cross-context messaging denied` when calling `message channel=discord`. |
| Telegram voice to Discord | Not ready | Voice arrives as `~/.openclaw/media/inbound/*.ogg`, but OpenClaw 2026.5.7 may pass `<media:audio>` without an inserted transcript. `openai-whisper-api` uses `OPENAI_API_KEY`, so it requires explicit spend approval under `~/agents-config/INDEX_RULES.md` Hard Rule 9. |

## Safe Test Order

Follow [`~/agents-config/experiments/01_self_hosted_openclaw/runbook.md#telegram-bot-to-discord-test`](../runbook.md#telegram-bot-to-discord-test).

1. Confirm both transports are connected on mercury2.
2. Invite `@ultimate_brando9_bot` to a private Discord test channel or provide a concrete `channel:<CHANNEL_ID>` / `user:<USER_ID>`.
3. Run the raw Discord CLI dry-run and send test from mercury2.
4. Only after raw Discord send works, test a plain text Telegram request.
5. Only after text routing works, consider voice; do not enable Whisper/API-backed transcription without explicit spend approval.

## Approval Flow

- `never_autonomous`: OpenClaw must confirm the exact Discord payload with Brando in Telegram before posting unless Brando explicitly says to send without asking.
- Standard approval vocabulary applies: `post`, `edit:`, `cancel`.

## Failure Handling

- If Discord target discovery returns no rows, report that the bot cannot see any Discord channel/user and ask Brando to invite the bot or provide a concrete ID.
- If Telegram-to-Discord returns `Cross-context messaging denied`, report that the bridge/taskflow is not implemented rather than retrying.
- If the input is voice and no transcript appears, report that voice transcription is not configured/approved rather than guessing from the audio file.
