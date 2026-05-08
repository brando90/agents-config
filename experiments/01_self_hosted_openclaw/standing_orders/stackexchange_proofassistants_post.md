# Standing Order — Auto-Post Questions to Proof Assistants Stack Exchange

**TLDR:** From any OpenClaw chat (Telegram default), Brando dumps a half-formed proof-assistant question. OpenClaw turns it into a well-formed Stack Exchange post (title, tags, MathJax body, runnable Lean/Coq snippet), shows the draft, runs a quality + duplicate gate, and only posts to https://proofassistants.stackexchange.com after explicit `post` approval. Never auto-posts. Implementation goes through headless-browser automation, not the SE API (see §"Critical caveat").

## Goal

Eliminate the friction of "I have a proof-assistant question → now I have to format it, find the right tags, type it on the SE web UI, log in, etc." by collapsing it to: *speak/paste into OpenClaw → review draft → say `post`.* Single-tap publish, with a quality gate that catches low-effort drafts before the SE community downvotes them.

## Why OpenClaw (not Claude Code / Codex CLI)

- **Always-on, multi-host substrate.** OpenClaw already runs 24/7 across mercury2 + Air + Pro with watchdogs, Telegram channel, approval flow, audit logging, and `~/keys/` secret management. CC / Codex are interactive dev CLIs — wrong shape for "fire from phone, get URL back."
- **The pattern already exists.** This is a near-clone of [`whatsapp_voice_draft.md`](./whatsapp_voice_draft.md): capture → clean → show draft → approve → send → log. Reusing it.
- **Approval gate is mandatory.** Proof Assistants SE is a small, technical community; low-effort posts get downvoted/closed within hours. The OpenClaw approval flow is already battle-tested.
- **Quality gate has memory.** OpenClaw can keep a running file of Brando's prior SE posts to detect near-duplicates and learn his preferred tags/voice over time.

## Critical caveat — there is no public "post a question" API

Stack Exchange's `api.stackexchange.com` exposes read + edit + vote + comment endpoints, but **does not expose `POST /questions`** (deprecated years ago for spam-prevention reasons). Confirm against current docs at the start of Phase 0; if that has changed, prefer the API path.

**Implication:** posting must go through the website, which means **headless-browser automation** (Playwright with a persisted login session), wrapped as an OpenClaw skill. Plan for that.

## Inputs

1. **Raw question dump** — speech-to-text or typed. Often half-formed: *"in lean 4 how do you do induction on a Sigma type when the second component depends on the first, I tried `Sigma.rec` and got `motive is not type-correct` what's going on"*
2. **Optional code snippet** — Lean / Coq / Isabelle / Agda fragment to embed.
3. **Optional target site override** — default `proofassistants.stackexchange.com`; allow `math.stackexchange.com`, `cstheory.stackexchange.com`, `cs.stackexchange.com`.

## Workflow

1. **Capture (Brando):** Telegram message in OpenClaw chat: `/ask <dump>` or `draft a SE question: <dump>`.
2. **Classify (OpenClaw):**
   - Is this proof-assistant–specific (Lean / Coq / Isabelle / Agda / Mizar / etc.), or is it pure math, or pure CS theory? If pure math → suggest `math.stackexchange.com`; if algorithms → `cstheory.stackexchange.com`. Default: PA SE. Justify the pick in one sentence.
3. **Search for duplicates (OpenClaw):**
   - Query `api.stackexchange.com/2.3/search/advanced?site=proofassistants&q=<keywords>`. Show top 3 results with URLs.
   - If any look like an exact duplicate, abort: *"this looks like a duplicate of <URL> — post anyway?"*
4. **Draft (OpenClaw):**
   - **Title** ≤ 150 chars, specific, ends with `?`. Avoid "How to do X" → prefer "Why does `Sigma.rec` fail with `motive is not type-correct` when the second component depends on the first?"
   - **Body** in Markdown with proper code fences (` ```lean `, ` ```coq `, ` ```agda `, ` ```isabelle `) and MathJax (`$…$`, `$$…$$`).
   - Required sections: *Context / setup* → *what I tried (with a minimal reproducible example)* → *what happens* → *what I expected* → *specific question*.
   - **MWE check:** if the question has a code snippet, lint that it's actually minimal — strip imports / decls not needed to reproduce.
   - **Tags:** pick 1–5 from the site's existing tag list (fetch via `api.stackexchange.com/2.3/tags?site=proofassistants`). **NEVER invent a new tag** (new tags require ≥150 rep on most SE sites). Common PA SE tags: `lean`, `lean4`, `coq`, `isabelle-hol`, `agda`, `metavariables`, `tactics`, `dependent-types`, `mathlib`, `definitional-equality`, etc.
   - **Quality-gate self-check** — refuse the draft (`WARN`) if any of:
     - No MWE and the question is about specific code behavior.
     - Title is "how to" without specifics.
     - Body < 50 words.
     - More than 5 candidate tags (scope too broad).
     - Looks like homework with no shown attempt.
5. **Show (OpenClaw):** in Telegram, render:
   - Site, title, tags, body preview (collapsed if > 200 lines).
   - Duplicate-search hits (top 3).
   - Quality verdict (`PASS` / `WARN: <reasons>`).
6. **Approve (Brando):** one of:
   - `post` / `send` / `y` → publish as-is.
   - `edit: <text>` → replace body and re-show.
   - `tweak: <instruction>` → e.g. *"tighten title"*, *"drop the agda tag"*, *"add the import line"* — regenerate, loop to step 5.
   - `tags: <list>` → override tags.
   - `site: <slug>` → switch site, restart from step 4.
   - `cancel` / `n` → discard, no post.
7. **Post (OpenClaw):**
   - Headless-browser flow (Playwright): load `~/keys/se_session_<site>.json` storage state → `https://<site>/questions/ask` → fill title / body / tags → click "Post Your Question" → wait for redirect to question URL.
   - On 2FA prompt, captcha, or session expiry → halt, ping Brando in Telegram with the error.
   - On success, return the question URL to the chat.
8. **Log:** append to `~/openclaw/audit/se_posts.jsonl`:
   - `{timestamp, site, question_id, url, title, tags, body_chars, approval_token, hostname}`.
9. **Follow-up watcher (separate, optional):** for each posted question, daily check answers/comments via API, summarize new activity in Telegram. Spec'd separately — out of scope for this standing order.

## Safety rules

- **Approval level:** `approve_to_send`. Silence ≠ approval. Each post requires an explicit approval token in the same Telegram turn.
- **Never auto-post.** Even on a `tweak` loop, the final send requires a fresh approval.
- **Rate limit:** ≤ 1 post / 30 min / site, ≤ 3 posts / day / site. SE anti-spam blocks faster cadences for low-rep accounts.
- **No cross-posting:** never the same question to two SE sites simultaneously. If migration is wanted, post once and request migration via flag.
- **No homework / official forms:** if the dump matches Brando's coursework or grant text, refuse and tell him to post manually under his own identity.
- **Secret scrub:** strip API keys, file paths under `~/keys/`, non-public emails before posting. Use the same regex as in `INDEX_RULES.md` Hard Rule 1.
- **Idempotency:** before posting, query the API for any question Brando posted in the last 24 h whose body has cosine similarity > 0.9 to the current draft. If hit → abort.
- **Account safety:** post under Brando's existing PA SE account, never a fresh one. New accounts have post throttles + reputation hurdles.

## Open setup questions (need answers before going live)

1. **SE account** — confirm Brando's existing PA SE handle + reputation. New account = throttled.
2. **Auth method** — saved Playwright `storage_state.json` (`~/keys/se_session_proofassistants.json`), refreshed monthly when cookies expire? Single shared session file scp'd between hosts (similar to the `gog` token pattern), or per-host login?
3. **Headless host** — run Playwright on which OpenClaw instance? mercury2 (Linux, headless-friendly, no display server needed) is the natural pick; Air / Pro fall back if mercury2 is down. Confirm Chromium installs cleanly on the SNAP node.
4. **Default tags** — Brando's most-used PA SE tags for cold-start (saves a tag-search round-trip for common cases).
5. **Quality bar** — strict (refuse any low-MWE draft outright) or permissive (`WARN` but allow override)? Default proposed: strict.
6. **Cross-site fallback** — if PA SE classification is uncertain, default to PA SE or to math SE?
7. **Follow-up cadence** — daily summary of new answers, or only when an answer is posted?

## Implementation phases

### Phase 0 — Pre-flight
- Re-verify SE has no public `POST /questions` endpoint; if changed, switch to API path and skip Phases 1–2 of the browser flow.
- Confirm Brando's PA SE account + rep level.
- Verify mercury2 has Chromium + Playwright installable: `pip install playwright && playwright install --with-deps chromium`. SNAP nodes may lack `apt-get` — fall back to `playwright install chromium` (no system deps) and `LD_LIBRARY_PATH` workarounds if needed. See [`machine/mercury2.md`](../../../machine/mercury2.md).

### Phase 1 — One-time auth
- One-time interactive login on a Mac (X / GUI available): `python scripts/se_login.py --site proofassistants` → opens Chromium → Brando logs in (incl. SSO / 2FA) → script saves `storage_state.json`.
- `scp` to mercury2: `~/keys/se_session_proofassistants.json` (mode 600). Also keep on Air / Pro as redundancy.
- Smoke test: `python scripts/se_session_check.py --site proofassistants` should print Brando's username + rep, no login prompt.

### Phase 2 — `se_post` skill
- New OpenClaw skill `se_post` calling `scripts/se_post.py --site <site> --title <t> --body-file <f> --tags <csv>`.
- `se_post.py` loads storage_state, navigates to the ask URL, fills the form, submits, returns posted URL.
- Smoke test: post a deliberately throwaway draft to a SE *meta sandbox* (`meta.stackexchange.com` or the per-site meta), verify URL returns, then **delete the post** as cleanup.
- If posting fails (captcha / session expiry / unknown error), the skill returns a structured error and the agent surfaces it to Brando.

### Phase 3 — Quality gate + duplicate check
- `scripts/se_check.py`: tag fetch, duplicate search (cosine sim on titles + body excerpts), MWE lint (count code-fence chars vs prose chars), quality verdict.
- Wire into agent prompt: agent must call `se_check` before showing the draft.

### Phase 4 — Telegram UX polish
- `/ask` slash-command in Telegram registers a draft session.
- Inline keyboard buttons for `post / edit / tweak / cancel` (grammY supports inline keyboards natively).
- Persist draft state in `~/openclaw/state/se_drafts/<chat_id>.json` so a draft survives gateway restart.

### Phase 5 — Audit + follow-up watcher
- Append every successful post to `~/openclaw/audit/se_posts.jsonl`.
- Optional cron (daily): API-poll each posted question for new answers/comments, summarize in Telegram. Keep this in a separate standing order so it doesn't gate the post-MVP.

## Definition of done

The standing order is "live" when, sustained for ≥4 weeks of real use:

1. From a Telegram dump on Brando's phone, a posted PA SE question URL is returned within 2 minutes (after Brando types `post`).
2. The quality gate has caught at least 3 borderline drafts (`WARN` + `tweak` loop) before going live — i.e., it earned its keep.
3. Zero accidental posts: no question on PA SE without an explicit `post` token in the audit log.
4. Auth session refresh has happened at least once without intervention beyond a single re-login.
5. Brando has used it for ≥ 5 real PA SE questions and reports the friction reduction is real (subjective check-in).
6. No bans, post-rate flags, or community downvotes that trace to OpenClaw-formatted posts.

## Hard rules for the executing agent

(From [`~/agents-config/INDEX_RULES.md`](../../../INDEX_RULES.md).)

- Refresh agents-config first (`git -C ~/agents-config pull`); re-read `INDEX_RULES.md`.
- **Never commit secrets** — `storage_state.json`, OAuth tokens, all live in `~/keys/` mode 600 (Hard Rule 1).
- Run **QA** before reporting any phase done (Hard Rule 3).
- **Email Brando** on phase completion — counts as a big task (Trigger Rule 14).
- **Dual TLDR** on every response (Hard Rule 4).
- **Stop and ask** before:
  - The first real post to PA SE (not a meta sandbox).
  - Posting under any account other than Brando's.
  - Auto-following up to existing posted questions.
  - Posting on any non-default site (math SE, cstheory SE) without explicit per-site approval.

## Agent prompt (drop-in for OpenClaw `/ask`)

> You are OpenClaw's Stack Exchange drafting agent. Brando just sent you a raw question dump for a proof-assistant question. Your job:
>
> 1. Decide the right SE site. Default `proofassistants.stackexchange.com`. Switch to `math.stackexchange.com` if pure math; `cstheory.stackexchange.com` if pure CS theory; `cs.stackexchange.com` for general CS. Justify the pick in one sentence.
> 2. Search the chosen site for duplicates via `api.stackexchange.com/2.3/search/advanced`. Show top 3 results with URLs.
> 3. Produce a draft with: title (≤ 150 chars, specific, ends with `?`), body in Markdown with proper code fences and MathJax, 1–5 tags from the site's existing tag list (NEVER invent tags — fetch via `api.stackexchange.com/2.3/tags?site=<slug>`).
> 4. Run the quality gate: minimal reproducible example present? Title specific? Body ≥ 50 words? Tags ≤ 5 and all real? If any fail, mark draft `WARN` with reasons; otherwise `PASS`.
> 5. Show in Telegram: site, title, tags, body, duplicate hits, quality verdict.
> 6. Wait for an approval token from Brando: `post`, `edit: <text>`, `tweak: <instruction>`, `tags: <list>`, `site: <slug>`, or `cancel`. **Silence ≠ approval.**
> 7. On `post`, call the `se_post` skill with the final draft. Return the posted question URL to the chat.
> 8. Append the audit entry to `~/openclaw/audit/se_posts.jsonl`.
>
> Hard rules: never post without an explicit approval token in this chat turn. Never invent tags. Never post the same question to two sites. Strip secrets, file paths under `~/keys/`, and non-public emails before posting. Rate limit: ≤ 1 post / 30 min / site, ≤ 3 / day / site. Respect SE anti-spam — if the site returns "you're posting too fast," halt and report to Brando.

## References

- [`experiments/01_self_hosted_openclaw/cc_prompt.md`](../cc_prompt.md) — parent OpenClaw architecture
- [`experiments/01_self_hosted_openclaw/standing_orders/whatsapp_voice_draft.md`](./whatsapp_voice_draft.md) — pattern this is based on
- [`experiments/01_self_hosted_openclaw/wishlist.md`](../wishlist.md) — broader OpenClaw backlog
- Proof Assistants SE: https://proofassistants.stackexchange.com
- Stack Exchange API docs: https://api.stackexchange.com/docs
- Playwright (Python): https://playwright.dev/python/
- Mercury2 machine doc: [`~/agents-config/machine/mercury2.md`](../../../machine/mercury2.md)

## Status

| Date | Status |
|------|--------|
| 2026-05-02 | Spec drafted on branch `claude/auto-stackoverflow-posting-CTvnC`. Awaiting answers to setup questions (1–7). Implementation deferred until Brando confirms account + auth strategy and OpenClaw email-MVP (`cc_prompt.md` Phases 0–5) is stable on at least 1 host. |
