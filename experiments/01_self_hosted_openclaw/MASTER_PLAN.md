# OpenClaw Master Plan — Brando's Self-Hosted Personal Automation Agent

**TLDR:** OpenClaw is the always-on agent substrate that automates Brando's admin work across every channel he uses (email, Telegram, WhatsApp, Discord, iMessage, web forms, social) by drafting outputs, asking for approval in Telegram, and only executing on his explicit `post`. This file is the single source of truth for *what OpenClaw should do for Brando* and *how it gets there* — covering the 3-instance hosting plan (Air / Pro / mercury2), every standing-order workflow (email triage, voice drafts, Stack Exchange posting, grant applications, SBSBZ event ads, Stanford-AI-for-Lean announcements, Drive→social photo pipeline, experiment dispatch, paper announcements, and more), and the phased rollout sequence.

Last updated: 2026-05-08
Branch: `claude/review-clock-setup-Lj7CR`
Supersedes: PR #42 (`claude/auto-stackoverflow-posting-CTvnC`) — its SE-posting spec is absorbed into [`standing_orders/stackexchange_proofassistants_post.md`](./standing_orders/stackexchange_proofassistants_post.md).
Out of scope: PR #44 (Experiment 02: QA polling vs. truthfulness) — separate research benchmark, stays its own PR.

---

## 1. North star — what OpenClaw does *for Brando*

Brando is a Stanford CS PhD student (Trustworthy AI lab, advised by Sanmi Koyejo) shipping verified-code research (VeriBench, Moogle.ai, Lean 4) while also: helping organize Stanford's bachata/zouk dance community (SBSBZ — *no salsa*), participating in the Stanford AI for Lean community ([aiforlean.org](https://aiforlean.org)), applying to multiple grants per quarter, posting paper announcements on LinkedIn / X (`@BrandoHablando`) / personal blog ([brando90.github.io/brandomiranda](https://brando90.github.io/brandomiranda/)), and managing a high-volume Stanford admin inbox.

**The job of OpenClaw is to collapse all of that into one cockpit (Telegram), and to do as much of the drafting and form-filling as possible while never sending anything Brando didn't approve.**

Concrete outcomes the master plan exists to produce:

- **Inbox triage** — Stanford admin email lands in Telegram with a draft reply; Brando says `post` and it sends.
- **Voice → polished message** on any outbound channel (WhatsApp, Discord, iMessage, SMS) with one-tap approval.
- **Click-button experiment dispatch** — `/experiment <branch>` in Telegram → mercury2/Pro spins up the run → DM on completion with results + PR link.
- **One-click grant applications** — detect CFP → extract requirements → draft from Brando's bio/project library → fill safe form fields → screenshot → Brando clicks final submit.
- **SBSBZ + Stanford-AI-for-Lean announcements** drafted, multi-channel (FB Event, IG, mailing list, WhatsApp, Discord), approved, posted.
- **Drive → social pipeline** — drop photos in a tagged Drive folder → captions + schedule drafted → `post` to publish to FB + IG.
- **Paper announcements** — on a new arXiv submission or conference accept, draft cross-posts to LinkedIn + X + personal blog → `post` to publish.

The non-goal is autonomy. OpenClaw does not auto-reply, auto-submit, or auto-publish on any high-value channel.

---

## 2. Architecture

### 2.1 Substrate

- **Compute / hosts** — 3 instances of OpenClaw running 24/7:
  - **MacBook Air** (`mac-air`) — partial today; Telegram + Gmail working.
  - **MacBook Pro** (`mac-pro`) — planned (Phase 3).
  - **SNAP mercury2** (Linux, DFS-backed) — planned (Phase 4).
- **Model calls** — Codex Pro CLI (per-host `~/.codex/auth.json`) → free GPT-5.5 inference. No per-call API spend.
- **Runtime** — OpenClaw 2026.4.x ([github.com/openclaw/openclaw](https://github.com/openclaw/openclaw), [docs.openclaw.ai](https://docs.openclaw.ai)).
- **Auto-restart** — `launchd` on macOS; `tmux` + `cron` + `krenew` on Linux.

### 2.2 Telegram is the cockpit, not a destination

(This explicitly answers "I'm still not clear how Telegram plays into all this.")

Telegram is the **single human-in-the-loop surface** for OpenClaw. It is **not** where most outbound messages go — those go to Gmail, WhatsApp, Discord, FB, IG, mailing lists, web forms. Telegram is where:

1. **OpenClaw shows you drafts** — *"here's the proposed reply / post / form-fill — `post` / `edit:` / `tweak:` / `cancel`."*
2. **You issue commands** — *"draft a WhatsApp to X saying Y"*, `/experiment foo`, *"post tonight's bachata recap to FB+IG."*
3. **OpenClaw posts heartbeats and status** to the private `openclaw-ops` channel — `[mac-air] alive @ 14:23`, `[mac-pro] STARTING`, `[mercury2] SILENT >30min`.
4. **You approve or veto** every consequential action with a single token.

Why Telegram specifically:
- **Reliable cross-platform** — phone, laptop, web all stay in sync.
- **Clean bot APIs** — no phone number / multi-device caps the way WhatsApp has.
- **Per-instance bots** — Air / Pro / mercury2 each get their own `@BotFather` bot, avoiding `getUpdates` 409 conflicts (per [Telegram channel docs](https://docs.openclaw.ai/channels/telegram.md)). Brando ends up DMing 3 bots; rate-limit caps the total to 2 DMs/min so it stays manageable.
- **Private ops channel** — heartbeats and lifecycle events go to `openclaw-ops` (channel, not DM), so Brando's main bot threads stay clean.

WhatsApp is for outbound to friends/family (Baileys, currently parked on upstream `status=500`). Discord is for Lean-AI-style multi-server triage (parked on Message Content Intent toggle). iMessage is local-Mac only via AppleScript bridge (deferred).

### 2.3 Channel matrix

| Channel | Direction | Approval level | Notes |
|---|---|---|---|
| Gmail | in + out | `approve_to_send` | via `gog` skill (gogcli, OAuth) |
| Telegram | in (cmds + approvals) + out (heartbeats + drafts) | n/a (the cockpit itself) | per-host bot; private `openclaw-ops` channel |
| WhatsApp | out (drafts approved in TG) | `approve_to_send` | Baileys, parked on upstream |
| Discord | in + out | `approve_to_send` | parked on Message Content Intent toggle |
| iMessage | out (Mac-local) | `approve_to_send` | AppleScript bridge, future |
| Web forms | out | `never_autonomous` | Playwright + screenshot-before-submit |
| FB Page / Event | out | `never_autonomous` | Graph API where possible; Playwright fallback |
| IG | out | `never_autonomous` | Graph API for business/creator accounts; Playwright fallback |
| Mailing list | out | `never_autonomous` | SBSBZ + Stanford-AI-for-Lean |
| Stack Exchange | out | `never_autonomous` | Playwright (no public POST API) |
| LinkedIn / X | out | `never_autonomous` | Paper announcements; per-platform API or Playwright |

### 2.4 Approval vocabulary (canonical)

All standing orders use the same approval tokens. Standardizing avoids drift between specs.

| Token | Meaning |
|---|---|
| `post` | Finalize and execute the draft as shown. |
| `edit: <new text>` | Replace the draft with the provided text and execute. |
| `tweak: <instruction>` | Regenerate the draft with the given instruction (e.g. "shorter", "more formal", "add 'see you Friday'"). Loop back to the show step. |
| `cancel` | Discard the draft, no execution, log the cancel. |

Aliases (friction-reduction; OpenClaw maps them to canonical tokens):
- `send` / `yes` / `y` → `post`
- `no` / `n` / `scrap` → `cancel`

For bulk operations (>3 recipients, mailing-list blasts, multi-platform social posts), require a separate `confirm-bulk` token instead of `post`.

### 2.5 Idempotency, heartbeat, audit (cross-instance)

- **Gmail label idempotency** — each instance applies `claw-claimed-by-${HOSTNAME}` atomically on pickup; final swap to `triaged-by-claw` only after `gmail.send` returns success. 5-minute stale-claim TTL (tightened from spec's 30 min for 3 readers).
- **Heartbeat** — every 15 min each instance posts `[host] alive @ <ts>` to private Telegram channel `openclaw-ops`. Lifecycle events (`STARTING`, `RECOVERED`) post immediately. SILENT >30 min triggers an alert from the other instances.
- **Rate limit** — *none by default*. (Original spec had max 1 approval-DM/min/instance + max 2/min total to "not spam Brando", but per Brando 2026-05-08: he prefers max throughput over throttling, especially on his own Codex Pro / Claude Pro subscription where there's no API spend pressure. Re-introduce only as a runaway-loop circuit-breaker if a real spam incident happens.)
- **Audit logs** — per-workflow JSONL appended to `~/openclaw/audit/<workflow>.jsonl`:
  - `gmail_sends.jsonl`, `whatsapp_sends.jsonl`, `discord_sends.jsonl`
  - `se_posts.jsonl`, `grants_drafted.jsonl`, `grants_filled.jsonl`
  - `social_posts.jsonl` (FB + IG + mailing list)
  - `experiments_dispatched.jsonl`, `paper_announcements.jsonl`
- **Cross-instance audit aggregation** — deferred to Phase 6 (weekly summary report DM'd to Brando).

---

## 3. Standing-orders inventory

| Workflow | File | State | Phase |
|---|---|---|---|
| Email triage (Stanford admin) | §6 Phase 1 + [`config/agent-prompt.md`](./config/agent-prompt.md) | partial (Air) | Phase 1 |
| WhatsApp voice-draft | [`standing_orders/whatsapp_voice_draft.md`](./standing_orders/whatsapp_voice_draft.md) | specced | Phase 6.1 |
| Stack Exchange `/ask` posting | [`standing_orders/stackexchange_proofassistants_post.md`](./standing_orders/stackexchange_proofassistants_post.md) | specced (absorbed from #42) | Phase 6.2 |
| Grant applications | [`standing_orders/grant_applications.md`](./standing_orders/grant_applications.md) | skeleton | Phase 6.3 |
| FB event posting (SBSBZ + general) | [`standing_orders/fb_event_post.md`](./standing_orders/fb_event_post.md) | skeleton | Phase 6.4 |
| IG posting | [`standing_orders/ig_post.md`](./standing_orders/ig_post.md) | skeleton | Phase 6.4 |
| Drive → social photo pipeline | [`standing_orders/drive_to_social.md`](./standing_orders/drive_to_social.md) | skeleton | Phase 6.4 |
| Stanford AI for Lean announcements | [`standing_orders/lean_ai_club.md`](./standing_orders/lean_ai_club.md) | skeleton | Phase 6.5 |
| Experiment dispatch | [`standing_orders/experiment_dispatch.md`](./standing_orders/experiment_dispatch.md) | skeleton | Phase 6.6 |
| Paper announcements | [`standing_orders/paper_announcements.md`](./standing_orders/paper_announcements.md) | skeleton | Phase 6.7 |
| Travel search (flights + price drops) | [`standing_orders/travel_search.md`](./standing_orders/travel_search.md) | skeleton | Phase 6.8 |

Shared template + approval-vocab standard: [`standing_orders/README.md`](./standing_orders/README.md). Every new standing order should follow that shape.

**Adjacent artifacts** (same experiment dir, not standing orders):

| Artifact | File | Purpose |
|---|---|---|
| Concepts / Q&A explainer | [`concepts.md`](./concepts.md) | Plain-English explainers (Telegram 409, cron, idempotency, etc.); TLDR-first per Trigger Rule 27 |
| Test tasks (one-shot validation) | [`test_tasks/`](./test_tasks/) | One-off agent test inputs (DM Sri, email Saumya) — not recurring workflows |
| Chatops / fleet management | [`chatops.md`](./chatops.md) | Future extension: bots.yaml registry + DM-driven restart commands; absorbs conjecture-prover dispatcher reliability |

---

## 4. Domain plans

### 4.1 Communications unification

- **Email (Gmail)** — triage admin emails matched by [`config/admin-filter.txt`](./config/admin-filter.txt) patterns; OpenClaw drafts; Brando approves in Telegram; OpenClaw sends via `gog gmail send` + applies `triaged-by-claw` label.
- **WhatsApp** — voice-dictation → cleaned draft → approve → send (`whatsapp_voice_draft.md`). Parked on Baileys upstream `status=500`.
- **Discord** — triage Lean-AI + personal servers; draft replies; summarize long threads → 1-paragraph. Parked on Message Content Intent toggle (90s of Brando's time).
- **Telegram (cockpit)** — see §2.2.
- **iMessage** — AppleScript bridge for Mac-local sends (future; low priority).
- **SMS** — out of scope for Phase 1–5; consider Twilio if a real need surfaces.

### 4.2 Research workflow

Three standing orders cover Brando's research surface:

1. **Experiment dispatch** ([`experiment_dispatch.md`](./standing_orders/experiment_dispatch.md)) — `/experiment <branch>` in Telegram → OpenClaw on mercury2 (or Pro) checks out the branch, reads `cc_prompt.md` (or equivalent spec at the branch root), runs in tmux, posts heartbeats, DMs Brando on completion with results + PR link. Future experiments (after PR #44) follow this pattern.
2. **Stack Exchange posting** ([`stackexchange_proofassistants_post.md`](./standing_orders/stackexchange_proofassistants_post.md), absorbed from PR #42) — raw question dump → duplicate check → MathJax-formatted draft → quality gate → `post` → Playwright posts to proofassistants.stackexchange.com (no public POST API).
3. **Paper announcements** ([`paper_announcements.md`](./standing_orders/paper_announcements.md)) — on arXiv submission or conference accept, draft cross-posts to LinkedIn + X (`@BrandoHablando`) + personal blog → Brando approves each surface independently → publish.

PR #44 (Experiment 02: QA polling vs. truthfulness) is **not** part of OpenClaw scope; it's a separate research benchmark and stays its own PR.

### 4.3 Grant pipeline

Scope (per Brando's choice 2026-05-08): **detect → extract → draft → fill safe fields → Brando clicks submit.**

Workflow (full spec in [`standing_orders/grant_applications.md`](./standing_orders/grant_applications.md)):

1. **Detect** — triage agent flags grant CFPs in inbox + Discord (heuristic: keywords like "deadline", "eligibility", "stipend", "fellowship", "application", or sender domain in known-grant list).
2. **Extract** — deadline, eligibility, page limits, budget rules, required materials, links, letters needed. Structured into a checklist DM'd to Brando.
3. **Draft** — produce application material from a reusable library:
   - Bios at 50 / 100 / 250 / 500 words.
   - Project summaries (VeriBench, Moogle.ai, Stanford AI for Lean, formal verification more broadly).
   - Reusable diversity / impact / research-statement paragraphs.
4. **Fill safe fields** (Playwright) — name, email, affiliation, ORCID, links — anything Brando has pre-confirmed in `config/brando_personal_facts.json`. Do **not** fill: payment info, free-form essays Brando hasn't approved, anything that requires a signature.
5. **Screenshot before submit** — full-page screenshot DM'd to Brando.
6. **Brando clicks submit** — manually, in his own browser session. **OpenClaw never clicks the final submit button on a grant portal.**

Library files to build (Phase 6.3 prerequisites):

> **Design pivot 2026-05-08 (per Brando):** the original plan kept the bio + project library as flat files in this repo (`config/brando_bio.md`, `config/brando_projects.md`). That goes stale fast — when Brando writes a new paper or wins an award, he'd have to remember to update *two places* (his actual CV and these files). Replaced with a hybrid that uses Brando's existing artifacts as source-of-truth.

**Hybrid identity-source design (single source of truth where possible):**

| Data class                | Source                                                                                                                                              | Why                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **Bio (4 lengths + elevator pitch)** | `_data/bio.yml` in [`brando90/brandomiranda`](https://github.com/brando90/brandomiranda) website repo                                       | Brando updates his website anyway for his own CV; agent fetches via raw GitHub URL.          |
| **Active project list (top 15)** | GitHub API: `api.github.com/users/brando90/repos?sort=pushed&per_page=15`                                                                       | Automatic freshness — `pushed_at` is maintained by every commit; no manual list to keep current. |
| **Per-project narrative** | Each repo's `README.md` (raw GitHub URL); fallback to `_data/projects.yml` override in website repo for projects whose READMEs are stubs or whose narrative differs for grant context | Repo READMEs are already maintained for code reasons; grants want a slightly different framing for some projects, so an override file handles that small gap. |
| **Awards / talks / mentorship / non-code activity** | Website pages (e.g. `/about/`, `/cv/`) or `_data/cv.yml`                                                                       | Live on the website Brando already curates; agent scrapes / fetches as needed.               |
| **Reusable diversity / impact / research-statement paragraphs** | `_data/grant_paragraphs.yml` in website repo                                                                          | Small structured file; lives alongside bio; rarely changes more than a few times a year.      |
| **Sensitive personal facts** (home address, SSN, citizenship, letter-writer contact info) | `~/keys/brando_personal_facts.json` (mode 600, never committed)                                  | Never goes on the public website; never goes in agents-config; agent reads locally per run.  |
| **Known-grants seed list** (sender domains / keywords for triage detection) | `experiments/01_self_hosted_openclaw/config/known_grants.txt` (this repo)                                          | Small, stable, slow-changing; lives near the workflow that uses it.                           |

**Why this beats the flat-file approach:**

- ✅ Brando's website is updated anyway when he writes a paper / wins an award / changes affiliation — agent picks up the change automatically on next grant draft, no separate sync step.
- ✅ GitHub `pushed_at` provides automatic "what am I currently working on?" signal — top 15 by recent push is exactly the projects you'd put in a grant.
- ✅ Sensitive data has its own home (`~/keys/`) and isn't tempted to drift into the agents-config repo.
- ✅ Removes 3 manual config files this repo would otherwise have to keep fresh.

**What Brando has to do once (Phase 6.3 setup, mostly his side):**

- [ ] Add `_data/bio.yml` to [`brando90/brandomiranda`](https://github.com/brando90/brandomiranda) with 4 length variants + 1 elevator pitch.
- [ ] Audit top 15 most-recently-pushed repos; for any with a stub README that wouldn't survive a grant reviewer, write a paragraph-length README *or* override in `_data/projects.yml`.
- [ ] Add `_data/grant_paragraphs.yml` with 3–5 reusable paragraphs (diversity statement, broader impact, research statement core).
- [ ] Populate `~/keys/brando_personal_facts.json` (mode 600) with: legal name, ORCID, citizenship, current affiliation, home + mailing address, letter-writer roster (name + email + relationship). **Never committed.**
- [ ] Seed `experiments/01_self_hosted_openclaw/config/known_grants.txt` with 5–10 grant programs currently being watched.

**Seed entries for `_data/projects.yml`** (Brando's idea 2026-05-08 — pre-populate the override file with his ongoing projects so they're never missed even if their repos are private / paused / renamed):

```yaml
# brando90/brandomiranda/_data/projects.yml — seed
- slug: veribench
  full_name: VeriBench
  status: active
  description: |
    Lean 4 formal-verification benchmark for AI agents. Headline benchmark of
    Brando's PhD; <fill from real bullets>.
  repos: [brando90/veribench]
  # links: [paper_arxiv_url, project_page_url]

- slug: veribench-dt
  full_name: VeriBench-DT
  status: active
  description: |
    VeriBench extension <Brando fills the one-paragraph "what + why">.
  repos: [TBD]

- slug: veribench-deps
  full_name: VeriBench-Deps
  status: active
  description: |
    VeriBench extension <Brando fills>.
  repos: [TBD]

- slug: cert-judge
  full_name: Cert-Judge
  status: active
  description: |
    <Brando fills — "certified judge / verifier for ML-generated proofs"?>
  repos: [TBD]

- slug: openclaw-self-hosted
  full_name: OpenClaw self-hosted personal assistant (Experiment 01)
  status: active
  description: |
    3-instance self-hosted OpenClaw deployment that triages admin email,
    drafts replies, posts cross-channel content (Discord/Telegram/IG/FB),
    on-demand grant + travel automation. This experiment.
  repos: [brando90/agents-config]
  # links: [https://github.com/brando90/agents-config/pull/46]
```

The point of this seed file is to capture every active or paused project, even those without a public repo — so a grant reviewer never sees a one-line "I work on AI." When Brando spins up a new project, add a stub here within a day; the entry will get filled out as the project progresses.

**Cost:** Brando does the bio + grant_paragraphs YAMLs once, then maintains them as he would maintain his website. README updates happen naturally through code work. The `~/keys/` file is roughly never updated (annual at most). Net: less manual work over time than the flat-file approach, and dramatically less stale.

### 4.4 SBSBZ — Stanford bachata/zouk events

Brando helps organize SBSBZ (Stanford bachata/zouk org — *no salsa*; **TODO: expand acronym in spec**). OpenClaw drafts and posts event content across:

- **FB Event** ([`fb_event_post.md`](./standing_orders/fb_event_post.md)) — create/update events with title, date/time/venue, description, cover image. Graph API where possible; Playwright fallback for Group events.
- **IG** ([`ig_post.md`](./standing_orders/ig_post.md)) — feed post + story + reel caption variants.
- **Mailing list** — Gmail send to SBSBZ list address, formatted plain-text + HTML.
- **WhatsApp / Telegram broadcast** — group chat blasts; `confirm-bulk` token required for >3 recipients.
- **Discord** — SBSBZ server announcement channel post (if a server exists; else skip).

Reusable templates (in `config/sbsbz_templates/`):

- `class_announcement.md` — weekly bachata/zouk class
- `social_event.md` — social dance night
- `reminder.md` — 24-hr / 1-hr reminders
- `cancellation.md` / `venue_change.md` — schedule disruptions
- `recap.md` — post-event with photos (feeds into Drive→social, §4.5)

### 4.5 Drive → social photo pipeline

Scope (per Brando's choice 2026-05-08): **tagged Drive folder; OpenClaw drafts caption + schedule; Brando says `post`.**

Workflow (full spec in [`standing_orders/drive_to_social.md`](./standing_orders/drive_to_social.md)):

1. Brando drops photos into `Drive/OpenClaw/social-queue/<event-name>/`.
2. OpenClaw watches the folder via the `gog` skill (Drive list + change watch).
3. On new files: pick the best 1–10 (heuristic: faces visible, not blurry, varied angles); draft a caption using event templates from §4.4; suggest a posting schedule (immediate / next-morning / golden-hour-tomorrow).
4. DM Brando the preview: thumbnails + caption + schedule + target channels (FB / IG / both).
5. On `post`: schedule via FB Graph + IG Graph (or Playwright fallback). On `tweak: <instr>`: regenerate caption.
6. Log to `~/openclaw/audit/social_posts.jsonl` with the Drive file IDs (for traceability).

Permissions setup needed (Phase 6.4 prerequisites):

- **FB** — Page admin token via Graph API (long-lived).
- **IG** — Business or Creator account linked to FB Page (Graph API path); else Playwright with persisted login.
- **Drive** — already wired via `gog`.

### 4.6 Stanford AI for Lean

Brando participates in [aiforlean.org](https://aiforlean.org) (existing community — confirmed 2026-05-08). OpenClaw helps with:

- **Meeting announcements** — weekly / bi-weekly post to mailing list + Discord/Slack.
- **Speaker / reading-group / project recruiting** — drafted, approved, sent.
- **Grant-opportunity broadcasts** — when a grant relevant to Lean-AI hits Brando's inbox, summarize and forward to the community.
- **Follow-ups** — "thanks for attending" + post-event resources.
- **Lean-AI-specific grant drafting** — reusable paragraphs in `config/brando_projects.md`.

Full spec: [`standing_orders/lean_ai_club.md`](./standing_orders/lean_ai_club.md).

### 4.7 Stanford admin / travel / personal portals

- **Stanford forms** — fill repetitive bureaucracy forms (visa, employment, reimbursement, registrar). Screenshot-before-submit. **Never submit autonomously.**
- **Travel** — flight search via Kayak/Google Flights scrape, summarize options, never book. Brando books in his own session. Preference template: home airport, alternates, max layovers, red-eye tolerance, reimbursement constraints.
- **Personal portals** (SuperCare Health, etc., per [`todos.md`](./todos.md):75) — Playwright with credentials in `~/keys/<service>_credentials.json` (mode 600). 2FA via DM-the-code-back. Defer until email triage is rock-solid.

---

## 5. Doc-verified corrections vs. earlier repo notes

Cross-checking `cc_prompt.md` / `setup-tutorial.md` / `todos.md` against [docs.openclaw.ai](https://docs.openclaw.ai/llms.txt) surfaced four things this plan corrects:

1. **One Telegram bot per instance — not one shared bot.** Per [Telegram channel docs](https://docs.openclaw.ai/channels/telegram.md): *"If you still see `getUpdates` 409 conflicts, another OpenClaw gateway, script, or external poller is likely using the same token."* Three instances polling the same bot will collide. Each host needs its own `@BotFather` bot; Brando ends up DMing 3 bots (or picks one primary + 2 silent failover via `--profile rescue`). The existing scripts assume one shared token — that needs to change before Phase 3.
2. **Gmail is already wired via the `gog` skill — there is no `openclaw channels add --channel google`.** Per [docs index](https://docs.openclaw.ai/llms.txt), the only Google channel documented is **Google Chat** (not Gmail). `setup-tutorial.md:118-198` already documents the correct path (gogcli + bundled `gog` skill auto-flips to Ready), and `todos.md:14` confirms it's working on the Air. The "Wire Gmail" line in `todos.md:40` and the install-script tail message are outdated — what's actually needed is *verifying the agent can invoke `gog` as a tool*, not running a non-existent OAuth command.
3. **Use the built-in `openclaw cron add`, not a custom cron.** Per [cron-jobs docs](https://docs.openclaw.ai/automation/cron-jobs.md), OpenClaw ships with `openclaw cron add --cron "*/15 * * * *" --message ...`, persisted at `~/.openclaw/cron/jobs.json`, surviving restarts. The earlier plan / `agent-prompt.md:111-127` shows raw `*/15 * * * *` cron syntax — keep the schedule but register via OpenClaw's CLI so it's gateway-managed.
4. **SecretRef schema.** Per [secrets docs](https://docs.openclaw.ai/gateway/secrets.md), the schema is `{source, provider, id}`, with `source ∈ {env, file, exec}`. Cleanest path for a raw-text token in `~/keys/`: load it into `TELEGRAM_BOT_TOKEN` env var via the launchd plist, then config holds `{source: "env", provider: "default", id: "TELEGRAM_BOT_TOKEN"}`. Avoids needing to restructure `~/keys/` into a JSON file.

There's also one **production gotcha** worth surfacing: the existing IPv6/DNS workaround we already added to the plist (`NODE_OPTIONS=--dns-result-order=ipv4first`) is documented upstream as `network.autoSelectFamily: false` in OpenClaw config — equivalent fix, but the config-level setting is more durable than env-var patching.

---

## 6. Phasing roadmap

### Legend

- 👤 **Brando** — manual, requires you (browser OAuth, phone, physical access, decisions)
- 🤖 **Claude** — automatable from a session (script, edit, verify, commit)
- 🟡 **Parked** — known blocker, deferred (don't waste cycles)
- ⏱ time estimate is for that step only

The plan is sequenced **smallest-unblocked-next-step first**. Don't skip ahead — Phase 2 idempotency assumes Phase 1 works on the Air; Phase 3/4 replication assumes Phase 1 + 2 are stable; Phase 6 standing-order rollout assumes Phase 5 soak passed.

---

### Phase 0 — Where we are now (Air partial, Pro/mercury2 untouched)

From `todos.md:13-21` (verified 2026-04-26):

| Capability                                  | Air | Pro | mercury2 |
| ------------------------------------------- | --- | --- | -------- |
| OpenClaw 2026.4.24 installed                | ✅  | ◯   | ◯        |
| Codex Pro CLI auth (`~/.codex/auth.json`)   | ✅  | ◯   | ◯        |
| Gateway smoke test (`PONG`)                 | ✅  | ◯   | ◯        |
| Telegram bot wired + paired                 | ✅  | ◯   | ◯        |
| Gmail / Calendar / Drive via `gog` skill    | ✅  | ◯   | ◯        |
| Discord                                     | 🟡  | ◯   | ◯        |
| WhatsApp                                    | 🟡  | —   | —        |
| Triage agent loop end-to-end                | ◯   | ◯   | ◯        |
| Idempotency labels + heartbeat + rate limit | ◯   | ◯   | ◯        |
| Daemon survives reboot                      | ✅  | ◯   | ◯        |

**Out of scope for this plan:** WhatsApp (Baileys upstream `status=500` — `todos.md:17`), Discord (parked behind a 90s manual toggle — `todos.md:16`; can be picked up anytime but not on the critical path). Telegram is the mandatory channel.

---

### Phase 1 — Finish the Air triage loop (smallest-unblocked first)

Goal: one real admin email triaged end-to-end (read → classify → DM Brando → approve → send → label) on the Air alone, before replicating.

#### Step 1.1 — 👤 Brando: write `config/admin-filter.txt` ⏱ 2 min

You list the senders/domains that count as "admin" so the agent only DMs you about those.

- 👤 Open `experiments/01_self_hosted_openclaw/config/admin-filter.txt` (Claude will create a starter file with placeholders if it doesn't exist — see Step 1.1b).
- 👤 Add 3–8 lines, one per sender pattern. Examples:
  ```
  *@stanford.edu
  *@cs.stanford.edu
  *financialaid*@*
  *@neurips.cc
  noreply@*conference*
  *@registrar.*
  ```
- 👤 Commit: `git -C ~/agents-config add experiments/01_self_hosted_openclaw/config/admin-filter.txt && git commit -m "OpenClaw: seed admin-email filter" && git push`

#### Step 1.1b — 🤖 Claude: create the empty `admin-filter.txt` skeleton ⏱ 1 min

If the file doesn't exist yet, write a placeholder with comments explaining the syntax so Brando isn't editing a blank file.

```text
# admin-filter.txt — sender patterns the triage agent treats as "admin"
# One pattern per line. Glob-style. Lines starting with # are comments.
# Match against From: header; case-insensitive.
#
# Example:
# *@stanford.edu
# *financialaid*@*
```

#### Step 1.2 — 🤖 Claude: verify the `gog` skill is exposed to the agent ⏱ 5 min

**Correction from earlier notes:** Gmail is already wired via the `gog` skill (gogcli) per `todos.md:14` and `setup-tutorial.md:118-198`. There is no `openclaw channels add --channel google` for Gmail in the [official channel list](https://docs.openclaw.ai/llms.txt) — only Google **Chat**. So this step isn't OAuth, it's verification that the agent can actually call `gog` as a tool.

- 🤖 On the Air, confirm skill state:
  ```bash
  openclaw skills info gog       # expect: "✓ Ready"
  gog -a brandojazz@gmail.com gmail list "is:unread" --max 1 -p   # expect: real data
  ```
- 🤖 DM the bot in Telegram: *"send me an email saying hi from the openclaw test"*. Watch `openclaw logs --follow` to confirm the agent picks `gog gmail send` as the tool.
- 👤 Brando confirms the email lands in his inbox.
- ❌ If skill reports not-Ready, re-run `gog auth add` per `setup-tutorial.md:136-140`.

#### Step 1.3 — 🤖 Claude: unlock agent shell/tool execution ⏱ 15 min

The agent currently reports "shell commands blocked by the local hook relay" (`todos.md:41`). Need to identify and flip the right exec-policy / approval setting.

- 🤖 Read OpenClaw's exec-policy docs: `openclaw config get agents.defaults.execPolicy` and `openclaw doctor`.
- 🤖 Identify the gating setting (likely `agents.defaults.execPolicy.shell` or a per-tool allowlist).
- 🤖 Propose the diff to Brando before applying — exec unlock has security implications (the agent is reading arbitrary email + has shell). Ask before flipping.
- 👤 Brando: approve or push back on the proposed setting.
- 🤖 Apply, restart gateway, verify with a smoke prompt that asks the agent to run `whoami`.

#### Step 1.4 — 🤖 Claude + 👤 Brando: finalize triage agent prompt ⏱ 10 min

Skeleton already exists at `config/agent-prompt.md`. Three placeholders need Brando's input (see `config/agent-prompt.md:129-141`).

- 👤 Brando answers in chat or by editing the file:
  1. Home shipping address (or "store in `~/keys/brando_personal_facts.json` and let agent read it").
  2. Default payment posture: agent drafts "I'll update by EOD" vs. pauses + asks?
  3. 2–3 sample emails Brando has actually sent, showing tone (so the agent can pattern-match).
- 🤖 Substitute the `<peer-host-1>` / `<peer-host-2>` placeholders with the real hostnames once Pro and mercury2 are known. (For Air-only Phase 1, just use `OPENCLAW_HOST=mac-air` and leave peer hostnames as `pending`.)
- 🤖 Load the prompt into OpenClaw's agent config and restart gateway.

#### Step 1.5 — 👤 Brando: create private Telegram channel `openclaw-ops` ⏱ 2 min

This is where heartbeats land. Phase 2 needs it; create it now so Phase 1 testing can also exercise the channel.

- 👤 In Telegram: tap pencil (new message) → New Channel → name `openclaw-ops` → Private.
- 👤 Add `@ultimate_brando9_sk_air_bot` (renamed from `@ultimate_brando9_bot` per BotFather `/setusername`) as **admin** (Channel info → Administrators → Add Admin).
- 👤 Send the channel ID to Claude. Easiest way:
  ```bash
  # On the Air, after the bot is in the channel and you've sent any message:
  curl -s "https://api.telegram.org/bot$(cat ~/keys/openclaw_telegram_bot_token.txt)/getUpdates" \
    | python3 -c 'import json,sys; [print(u["channel_post"]["chat"]["id"]) for u in json.load(sys.stdin)["result"] if "channel_post" in u]'
  ```
- 🤖 Store the channel ID in `~/.openclaw/openclaw.json` under `channels.telegram.opsChannelId` (or whatever OpenClaw's config schema names it — verify via `openclaw config schema`).

#### Step 1.6 — 🤖 Claude + 👤 Brando: end-to-end real-email test ⏱ 10 min

The proof point. One real unread admin email goes through the full loop.

- 👤 Brando: identify one unread email from a sender already in `admin-filter.txt`. Don't open it (so it stays unread and the agent picks it up).
- 🤖 Claude: poke the agent (`openclaw agent poke main` or DM the bot "check my email") and watch logs (`openclaw logs --follow`).
- Expected: bot DMs Brando with the `📬 [sender] subject / summary / Draft / approve / edit / skip` format.
- 👤 Brando: reply `approve` (or `edit: <text>`) in Telegram.
- 🤖 Claude: verify Gmail Sent folder has the message and the email got the `triaged-by-claw` label.
- 🤖 Claude: log result in `todos.md` Status & Log.

**If anything fails at this step, STOP. Do not move to Phase 2 until E2E works on Air.** Capture the error in `todos.md` and debug.

---

### Phase 2 — Idempotency + ops layer (Air only, before replicating)

These are the multi-instance prerequisites. Build them on the Air first; the labels and heartbeats are no-ops with one instance, but that's fine — verify the mechanism works before adding readers that race on it.

#### Step 2.1 — 🤖 Claude: implement Gmail label idempotency ⏱ 1 hr

Per `cc_prompt.md:64-71` + the `agent-prompt.md` "Loop" section:
- 🤖 Patch the agent prompt / agent runtime to apply `claw-claimed-by-${OPENCLAW_HOST}` atomically on pickup.
- 🤖 Final swap to `triaged-by-claw` only after `gmail.send` returns success.
- 🤖 5-min stale-claim TTL (tightened from spec's 30 min — `cc_prompt.md:160`).
- 🤖 Test: simulate a crash mid-draft (kill gateway after claim label applied, no triaged label). On restart, verify the next loop steals the claim after 5 min.
- 👤 Brando: spot-check Gmail labels in the web UI once to confirm the labels are appearing as expected.

#### Step 2.2 — 🤖 Claude: implement heartbeat via built-in `openclaw cron` ⏱ 20 min

Per [cron-jobs docs](https://docs.openclaw.ai/automation/cron-jobs.md), OpenClaw ships a built-in scheduler that persists across restarts (`~/.openclaw/cron/jobs.json`).

- 🤖 Register the heartbeat:
  ```bash
  openclaw cron add --name "heartbeat-${HOSTNAME}" --cron "*/15 * * * *" \
    --tz "America/Los_Angeles" --session isolated \
    --message "post '[${HOSTNAME}] alive @ '$(date -u +%FT%TZ)' to telegram channel openclaw-ops"
  ```
- 🤖 Verify: `openclaw cron list` shows the job; `openclaw cron run <jobId>` triggers an immediate post; check `openclaw-ops` channel.
- 🤖 Hook gateway lifecycle events: `STARTING` on start, `RECOVERED` after a restart-from-crash. (Verify whether OpenClaw exposes lifecycle hooks via plugin API; if not, fall back to a launchd `LaunchEvents` trigger that posts via `openclaw message send --channel telegram --target <ops-chat-id> --message "..."`.)
- 🤖 Add the SILENT watcher: a separate `openclaw cron add` job that fetches recent `openclaw-ops` posts via `gog`-style Telegram lookup (or just maintains its own state file of last-seen-ts per peer), and posts `[<peer>] SILENT >30min — investigate` if threshold breached. No-op until Pro/mercury2 are up; verify the cron itself fires.

#### Step 2.3 — Skip default rate-limiting (per Brando 2026-05-08) ⏱ 0 min

Brando explicitly opted out of artificial DM throttling — preferring max throughput on his own Codex Pro / Claude subscription. Keep the rate-limit primitive available in code as a circuit-breaker (e.g. `--max-dms-per-min N`) but do not enable it by default. Re-evaluate only if a real runaway-loop spam incident occurs.

- 🤖 No work needed for default behavior. Document the circuit-breaker hook in `config/agent-prompt.md` so a future incident can flip it on without code changes.

---

### Phase 3 — Replicate to MacBook Pro

Goal: byte-identical OpenClaw on the Pro using the install script.

#### Step 3.1 — 👤 Brando: create a SECOND Telegram bot for the Pro ⏱ 3 min

**Critical: do not reuse the Air's bot token.** Per [Telegram channel docs](https://docs.openclaw.ai/channels/telegram.md), two gateways polling `getUpdates` on the same token cause 409 conflicts. Each instance needs its own bot.

- 👤 Telegram → `@BotFather` → `/newbot` → name e.g. `ultimate_brando9_pro_bot` → copy token.
- 👤 Add the new bot as admin to the `openclaw-ops` channel (so this instance can also post heartbeats).
- 👤 Decide: do you want to DM 3 different bots (one per host) or use the [`--profile rescue` failover pattern](https://docs.openclaw.ai/gateway/multiple-gateways.md) where only the primary bot DMs you and the others stay silent until the primary is silent? Default recommendation: **3 separate bots, all DM-capable**, since the triage loop already rate-limits to 2 DMs/min total — redundancy > tidiness here.

#### Step 3.2 — 👤 Brando: choose access path ⏱ 1 min decision

- **Option A (faster, recommended):** Brando provides SSH access from the Air (or wherever Claude runs) to the Pro. Add to `~/.ssh/config`:
  ```
  Host mac-pro
    HostName <pro's local IP or .local>
    User <brando's username on pro>
    IdentityFile ~/.ssh/id_ed25519
  ```
- **Option B (more friction, no SSH config needed):** Brando opens a Terminal on the Pro himself and pastes commands Claude prepares.

#### Step 3.3 — 👤 Brando: per-host prereqs on the Pro ⏱ 10 min

- 👤 `codex login` on the Pro (don't copy `auth.json` — refresh tokens rotate; per `cc_prompt.md:161` and `setup-tutorial.md:208`).
- 👤 Install Node 24 if not already (`brew install node@24`).
- 👤 Install `gogcli` (`brew install gogcli`).

#### Step 3.4 — 🤖 Claude: scp per-host secrets from Air → Pro ⏱ 2 min

- 👤 Brando: write the **Pro's new bot token** (from Step 3.1) to `~/keys/openclaw_telegram_bot_token.txt` on the Pro (mode 600). NOT the Air's token.
- 🤖 From the Air, copy gogcli auth (this is shared — same Google account, tokens auto-refresh):
  ```bash
  scp -r "$HOME/Library/Application Support/gogcli" mac-pro:'~/Library/Application Support/gogcli'
  ```
- 🤖 Verify the scp'd `gogcli` directory works on the Pro (`ssh mac-pro 'gog -a brandojazz@gmail.com gmail list "is:unread" --max 1 -p'`). Tokens auto-refresh; no re-OAuth needed (per `setup-tutorial.md:198`).

#### Step 3.5 — 🤖 Claude: run the install script on the Pro ⏱ 5 min

```bash
ssh mac-pro 'git -C ~/agents-config pull && bash ~/agents-config/experiments/01_self_hosted_openclaw/scripts/install_openclaw_instance.sh'
```

Per `scripts/install_openclaw_instance.sh:6-23`, the script handles npm install, plist patching, daemon install, Telegram wiring, and smoke test. **Note:** the script's tail message references `openclaw channels add --channel google` for Gmail OAuth — that's the outdated path; on the Pro, just rely on the scp'd gogcli tokens (Step 3.4) plus a `gog` skill verification (same as Step 1.2 but on the Pro).

#### Step 3.6 — 👤 Brando: post-install manual steps on Pro ⏱ 3 min

- 👤 Open Telegram, `/start` the **Pro's** bot (not the Air's), then run the pairing-approve command on the Pro:
  ```bash
  openclaw pairing list telegram                    # shows the pending code
  openclaw pairing approve telegram <CODE>
  ```
  (Per [docs](https://docs.openclaw.ai/channels/telegram.md): pairing codes expire after 1 hour.)
- 👤 DM the Pro's bot once to confirm it replies as the agent.

#### Step 3.7 — 🤖 Claude: verify Pro joins the heartbeat + idempotency dance ⏱ 10 min

- 🤖 Watch `openclaw-ops` channel — Pro should start posting `[mac-pro] alive @ <ts>` within 15 min.
- 🤖 Force a label race: send Brando a test email, watch logs on both Air and Pro. Confirm only one instance applies `triaged-by-claw`. The race is real because OpenClaw [explicitly does not coordinate gateways on the same inbox](https://docs.openclaw.ai/gateway/multiple-gateways.md) — the Gmail-label lock from Step 2.1 is what prevents double-processing.

---

### Phase 4 — Replicate to mercury2 (Linux, different recipe)

mercury2 is a SNAP node — different daemon mechanism, different filesystem. Per `cc_prompt.md:154-165` and `machine/snap.md`.

#### Step 4.1 — 👤 Brando: SSH access to mercury2 ⏱ 5 min

- 👤 Confirm `ssh mercury2` works from the launching machine. If not, add SSH config entry + accept host key once. (Per `cc_prompt.md:175`, last attempt failed with "Host key verification failed".)
- 👤 Confirm Kerberos keytab is set up per `~/agents-config/machine/init_no_passwords_snap_kinit.md` (so `krenew` cron can refresh tokens unattended).

#### Step 4.2 — 🤖 Claude: install on mercury2 ⏱ 30 min

mercury2 install is **not** identical to macOS — needs the Linux path:
- 🤖 Clone OpenClaw to `/dfs/scratch0/<user>/openclaw` with symlink `~/openclaw → /dfs/scratch0/<user>/openclaw` (DFS-backed, survives node reboots — per `cc_prompt.md:46`).
- 🤖 No `launchd`. Use the SNAP pattern from `machine/snap.md`: tmux session `openclaw` running watchdog while-loop + `@reboot` cron + `krenew` cron.
- 🤖 The existing `install_openclaw_instance.sh` is macOS-flavored — needs a Linux branch added, OR write a sibling `install_openclaw_instance_linux.sh`. **Decision point:** propose the cleaner path to Brando before implementing.

#### Step 4.3 — 👤 Brando + 🤖 Claude: secrets + smoke ⏱ 15 min

- 👤 Brando: create a **third** bot via `@BotFather` (e.g. `ultimate_brando9_mercury2_bot`), add to `openclaw-ops` channel as admin, write token to `~/keys/openclaw_telegram_bot_token.txt` on mercury2 (mode 600). Same reason as Step 3.1 — no shared bot.
- 🤖 scp gogcli tokens from Air → mercury2 — but note path differs by OS: `~/.config/gogcli/` on Linux vs. `~/Library/Application Support/gogcli/` on macOS (per `setup-tutorial.md:198`).
- 👤 Brando: `codex login` once on mercury2.
- 🤖 Smoke test: `PONG` via gateway; agent reads one Gmail; posts heartbeat to `openclaw-ops`.

#### Step 4.4 — 🤖 Claude: SNAP-specific hardening ⏱ 30 min

Per `machine/snap.md`:
- 🤖 `krenew` cron for Kerberos refresh.
- 🤖 `@reboot` cron to re-launch tmux watchdog after node reboots.
- 🤖 logrotate for `~/openclaw/*.log`.
- 🤖 Document slurm-migration warnings in the experiment's status log (mercury2 may go down for maintenance; the other two instances cover the gap).

---

### Phase 5 — 7-day soak (Definition of Done)

Per `cc_prompt.md:102-114`. Mostly autonomous; Brando provides the "did this actually reduce friction?" signal.

#### What runs autonomously (🤖)

- All 3 instances post heartbeats every 15 min.
- Each instance is killed at least once during the window (Claude or Brando triggers); auto-restart within 1 min, verified in logs.
- Gmail label audit: every `triaged-by-claw` came from exactly one host (zero double-processing).
- Zero replies sent without explicit `approve` (verified by inspecting `gmail.send` logs vs. Telegram approval log).

#### What Brando does (👤)

- 👤 Triage **≥10 real admin emails** entirely from Telegram. Don't open Gmail web UI for them.
- 👤 Subjective check-in at end of week: did this actually reduce friction? (Per `cc_prompt.md:112` — this is the real ROI test.)

#### Bail-out criteria

If any of the 6 measurable DoD items (`cc_prompt.md:106-111`) fail and aren't fixable in a day, document in `todos.md` Status & Log and recommend either:
- (a) consolidate to one instance,
- (b) switch channel (already on Telegram — n/a),
- (c) park experiment.

---

### Phase 6 — Standing-order rollout (post-soak)

Once Phases 0–5 are green, ship the new standing orders one at a time. Each gets its own E2E test before moving on. Order is rough — when blockers shift, re-prioritize.

| Sub-phase | Standing order | Blocking on |
|---|---|---|
| 6.1 | WhatsApp voice-draft | Baileys upstream stable |
| 6.2 | Stack Exchange `/ask` | Playwright skill + persisted SE login |
| 6.3 | Grant applications | Bio/project library populated (`config/brando_bio.md`, `config/brando_projects.md`, `config/brando_personal_facts.json`) |
| 6.4 | SBSBZ event posting (FB + IG + mailing list + Drive→social) | FB Graph token + IG account linkage |
| 6.5 | Stanford AI for Lean announcements | Mailing-list address + (Discord/Slack ID) |
| 6.6 | Experiment dispatch | mercury2 install (Phase 4) complete |
| 6.7 | Paper announcements | LinkedIn API or Playwright; X API token |

Each sub-phase ends with: end-to-end success on one real input + audit-log entry + `todos.md` Status & Log update + `wishlist.md` checkbox ticked.

---

## 7. Hygiene (do alongside, not blocking)

These are not on the critical path but should not be forgotten.

### H.1 — 👤 Brando + 🤖 Claude: rotate Telegram bot token ⏱ 5 min

Current Air token was pasted in a Claude Code chat log (per `todos.md:80`). Risk: anyone with that log can hijack the bot. (Pro and mercury2 bots from Phase 3/4 will have fresh, never-leaked tokens — no rotation needed there at first.)

- 👤 Open Telegram → `@BotFather` → `/revoke` → select `@ultimate_brando9_sk_air_bot` (formerly `@ultimate_brando9_bot`) → confirm. Copy new token.
- 👤 Paste new token into `~/keys/openclaw_telegram_bot_token.txt` on **the Air only** (mode 600). The other instances have their own bots.
- 🤖 Re-load on Air via env var (see H.2) or in-place config edit; restart gateway.
- 🤖 Verify pairing still works post-rotation (`openclaw pairing list telegram`).

### H.2 — 🤖 Claude: move secrets to SecretRef ⏱ 30 min

Per `todos.md:81` and [secrets docs](https://docs.openclaw.ai/gateway/secrets.md). Currently the bot token sits plaintext inside `~/.openclaw/openclaw.json`. Verified SecretRef schema: `{source, provider, id}`.

**Cleanest path for raw-text token files in `~/keys/` — env-var indirection:**

- 🤖 Patch the launchd plist (macOS) / systemd-user unit (Linux) to load the file into an env var:
  ```xml
  <key>EnvironmentVariables</key>
  <dict>
    <key>TELEGRAM_BOT_TOKEN</key>
    <string><!-- read from ~/keys/openclaw_telegram_bot_token.txt at daemon start --></string>
  </dict>
  ```
  (launchd doesn't support file-substitution in plist directly — use a small wrapper script in `ProgramArguments` that exports the env then execs `openclaw gateway`.)
- 🤖 Patch `~/.openclaw/openclaw.json` to use the SecretRef form:
  ```json
  "channels": {
    "telegram": {
      "enabled": true,
      "token": { "source": "env", "provider": "default", "id": "TELEGRAM_BOT_TOKEN" }
    }
  }
  ```
- 🤖 Verify with `openclaw secrets audit --check` (per docs) — should report zero plaintext secrets after.
- 🤖 Update `install_openclaw_instance.sh` to write the SecretRef form, not the inline form. Add the wrapper-script generation for the plist's `ProgramArguments`.

### H.3 — 🤖 Claude: file upstream OpenClaw issues ⏱ 30 min

Per `todos.md:71`. Documenting the bugs we hit:
1. `openclaw onboard --help` returns nothing.
2. Codex harness "not registered" without onboarding.
3. Gateway Telegram `sendMessage` HttpError despite `NODE_EXTRA_CA_CERTS` being set.
4. `paste-token` UI consumes piped stdin char-by-char without submitting.

Filing these is good open-source citizenship and forces upstream to think about the fixes.

---

## 8. Effort summary

| Role        | Total time | Spread                                                                |
| ----------- | ---------- | --------------------------------------------------------------------- |
| 👤 Brando   | ~45–60 min (Phases 0–5) + ~30 min (Phase 6 prereqs: bio/project library, FB/IG account linkage) | Many short async touchpoints (≤5 min each), spread over 2–4 weeks |
| 🤖 Claude   | ~5–8 hr (Phases 0–5) + ~6–10 hr (Phase 6 standing-order specs → working) | Continuous work across multiple sessions |
| ⏱ Wall time | ~3–5 weeks | Dominated by the 7-day soak window + standing-order rollout cadence (one per sub-phase) |

---

## 9. Open decisions (Brando, please pick when convenient)

### Carried over from existing plan:

1. **Discord:** flip Message Content Intent toggle now (90s, parallelizable with everything else) or defer until Telegram triage is proven? Default: defer, since the critical path is email-triage and Telegram already works.
2. **mercury2 install script:** add Linux branch to existing `install_openclaw_instance.sh`, or sibling `_linux.sh`? Default: sibling file — keeps each script readable.
3. **Triage prompt placeholders:** answer the 3 questions in `config/agent-prompt.md:129-141` — home address, payment posture, tone calibration examples.
4. **SuperCare Health + general "do X" capability** (`todos.md:75-76`): in scope after triage works, or separate experiment? Default: separate experiment (keeps DoD scoped to admin-email triage).

### New (Phase 6 prerequisites):

5. **SBSBZ acronym expansion** — what do the 5 letters stand for? Confirmed *bachata + zouk, no salsa*; fill in the spec when known.
6. **SBSBZ posting permissions** — does Brando have admin access to the SBSBZ FB Page / IG account / mailing list? If not, who does, and what's the path to delegation?
7. **Stanford AI for Lean channels** — what's the official mailing-list address? Is there a Discord/Slack? Where do meeting announcements go today?
8. **Grant-detection seed list** — 5–10 grant programs Brando is currently watching (NSF GRFP, Hertz, etc.) so the detection heuristic has a real corpus to test against.
9. **Bio + project library bootstrap** — Brando provides 1 existing successful application (e.g., the GRFP) so OpenClaw can extract bio paragraphs at 4 lengths + project summaries.
10. **LinkedIn / X credentials posture** — LinkedIn API requires Marketing Developer Platform approval (slow); is Playwright-with-persisted-login acceptable for paper announcements? Same question for X (now charges for write API access).
11. **Drive → social Drive folder path** — confirm `Drive/OpenClaw/social-queue/<event-name>/` is the convention, or pick something else.
12. **iMessage / SMS scope** — needed at all? Default: defer indefinitely; the cockpit + Gmail + WhatsApp covers 95%.

---

## 10. Cross-references

### Internal (this repo)

- Standing orders (per-feature specs): [`standing_orders/`](./standing_orders/) — see [`standing_orders/README.md`](./standing_orders/README.md) for the shared template
- Concepts / Q&A explainers: [`concepts.md`](./concepts.md) — TLDR-first format per `INDEX_RULES.md` Trigger Rule 27
- Test tasks (one-shot validation): [`test_tasks/`](./test_tasks/) — see [`test_tasks/README.md`](./test_tasks/README.md)
- Chatops / fleet management (future): [`chatops.md`](./chatops.md) — bots.yaml registry + DM-driven commands
- Operational artifacts: [`config/`](./config/) (`admin-filter.txt`, `agent-prompt.md`, `openclaw.json.template`), [`scripts/`](./scripts/) (`install_openclaw_instance.sh`, etc.)
- SNAP playbook: [`~/agents-config/machine/snap.md`](../../machine/snap.md)
- Mac playbook: [`~/agents-config/machine/mac.md`](../../machine/mac.md)
- Redirect stub: [`PLAN.md`](./PLAN.md) (points here)
- Project history — prior `cc_prompt.md` / `setup-tutorial.md` / `todos.md` / `wishlist.md` content is now absorbed into **Appendices A–F** at the bottom of this file.

### Upstream OpenClaw docs (verified 2026-05-08)

- Doc index: https://docs.openclaw.ai/llms.txt
- Install + onboard: https://docs.openclaw.ai/install
- Telegram channel (CLI, pairing, gotchas, 409 conflict warning): https://docs.openclaw.ai/channels/telegram.md
- Cron / scheduler (`openclaw cron add`, persistence): https://docs.openclaw.ai/automation/cron-jobs.md
- Multiple gateways (rescue-bot pattern, no shared-inbox coordination): https://docs.openclaw.ai/gateway/multiple-gateways.md
- Gateway lock (per-host, per-port, **not** cross-host): https://docs.openclaw.ai/gateway/gateway-lock.md
- Secrets / SecretRef schema (`{source, provider, id}`): https://docs.openclaw.ai/gateway/secrets.md
- SecretRef credential surface: https://docs.openclaw.ai/reference/secretref-credential-surface.md
- Repo: https://github.com/openclaw/openclaw
- npm package: https://www.npmjs.com/package/openclaw

### Brando's online surfaces (where outbound posts land)

- Personal site / blog: https://brando90.github.io/brandomiranda/
- Stanford profile: https://profiles.stanford.edu/brando-miranda
- STAIR lab: https://stairlab.stanford.edu/members/brando_miranda.html
- LinkedIn: https://www.linkedin.com/in/brando-miranda-40821046/
- X / Twitter: https://x.com/BrandoHablando
- Google Scholar: https://scholar.google.com/citations?user=_NQJoBkAAAAJ
- Stanford AI for Lean: https://aiforlean.org

---

# Appendices

These sections absorb content from the prior `cc_prompt.md`, `setup-tutorial.md`, `todos.md`, and `wishlist.md` so this file is the single source of truth.

## Appendix A — Reproducible Install Recipe

Verified end-to-end on macOS (MacBook Air, Apple Silicon, Node 25 via Homebrew) on 2026-04-26. Same recipe is meant to repeat on Mac Pro and SNAP `mercury2`.

> **Prerequisite (one-time, per machine):** `codex login` against your ChatGPT/Codex Pro account. Verify with `cat ~/.codex/auth.json | grep chatgpt_plan_type` → `"chatgpt_plan_type": "pro"`.

### A.1 Install (~30 s)

macOS (Homebrew Node) needs an `~/.npmrc` cafile entry first:

```bash
test -f ~/.npmrc || echo "cafile=/etc/ssl/cert.pem" > ~/.npmrc
npm install -g openclaw@latest
openclaw --version    # expect: OpenClaw 2026.4.24 (cbcfdf6) or newer
```

If you see `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`: add the cafile line, then `rm -rf ~/.openclaw/plugin-runtime-deps` and retry.

### A.2 Onboarding — must be in a real Terminal (~1 min)

Run in Terminal.app or iTerm — needs a TTY (do **not** drive from inside another Claude Code / Codex session):

```bash
openclaw onboard
```

Answer the prompts:
- **Where will the Gateway run?** → `Local (this machine)`
- **Auth choice** → `Codex (ChatGPT/OpenAI)` (auto-detects `~/.codex/auth.json`)
- **Default model** → accept `openai/gpt-5.5` (routes through the codex harness, billed against your Pro plan)
- **Daemon install** → yes (writes `~/Library/LaunchAgents/ai.openclaw.gateway.plist` on macOS)

If onboarding picked a different model:

```bash
openclaw config set agents.defaults.model.primary openai/gpt-5.5
openclaw config set agents.defaults.embeddedHarness.runtime codex
openclaw gateway restart
```

### A.3 Smoke test (~5 s)

```bash
openclaw infer model run --gateway --prompt "say only the word PONG"
# expect: provider: openai / model: gpt-5.5 / PONG
```

If `Requested agent harness "codex" is not registered` → onboarding didn't take; re-run A.2 in a real Terminal.
If `gateway closed (1006/1000)` → `openclaw gateway restart && sleep 5`, retry.

Sanity-check Codex Pro billing (not API key billing):
```bash
grep chatgpt_plan_type ~/.codex/auth.json   # → "pro"
openclaw config get agents.defaults.embeddedHarness.runtime   # → "codex"
```

### A.4 Telegram channel (~5 min, requires phone)

1. Telegram → `@BotFather` → `/newbot` → name (e.g. `ultimate_brando9_<host>_bot`) → copy token
2. (Optional) `/newchannel` → create private `openclaw-ops` channel; add bot as admin

```bash
mkdir -p ~/keys && chmod 700 ~/keys
echo 'PASTE_TOKEN_HERE' > ~/keys/openclaw_telegram_bot_token.txt
chmod 600 ~/keys/openclaw_telegram_bot_token.txt

openclaw channels add --channel telegram --token "$(cat ~/keys/openclaw_telegram_bot_token.txt)"
openclaw gateway restart
sleep 4
openclaw channels status   # → "Telegram default: enabled, configured, running"
```

First contact (the bot can't DM you until you DM it):
1. Search for your bot's `@handle`, tap `/start`, send any message
2. Bot replies with a pairing code (e.g. `KBK4LMYU`) and the approval command
3. Run: `openclaw pairing approve telegram <CODE>`
4. DM the bot again — it now replies as the agent (Codex Pro / GPT-5.5)

### A.5 Google Workspace via the bundled `gog` skill

> **Important:** OpenClaw's stock `google` plugin is for Gemini models, NOT Gmail/Calendar/Drive. Workspace integration is the *skill* `gog` wrapping the `gogcli` Homebrew binary.

```bash
brew install gogcli
gog --version                                                       # 0.13.0+
gog auth credentials set ~/keys/client_secret_*.apps.googleusercontent.com.json
gog auth add YOUR_GOOGLE_EMAIL@gmail.com                            # opens browser
```

**Enable APIs in your GCP project** (otherwise: `403 accessNotConfigured`). Open `https://console.cloud.google.com/apis/library?project=<YOUR_PROJECT_ID>` and enable each (~30s propagation each):
Gmail · Calendar · Drive · Docs · Sheets · Tasks · People · Slides.

Smoke test gog:
```bash
A=YOUR_GOOGLE_EMAIL@gmail.com
gog -a $A gmail send --to $A --subject "🦞 gog test" --body "via gog"
gog -a $A gmail list "is:unread" --max 5 -p
gog -a $A calendar list --max 5 -p
gog -a $A drive ls --max 5 -p
```

Confirm OpenClaw picked up the skill:
```bash
openclaw skills info gog   # → "🎮 gog ✓ Ready" with "Binaries: ✓ gog"
```

DM the bot *"send me an email saying hi"* and watch it execute.

> **Multi-instance:** `gog` tokens at `~/Library/Application Support/gogcli/` (macOS) / `~/.config/gogcli/` (Linux). To avoid re-OAuthing, `scp` that directory between hosts. Tokens auto-refresh.

### A.6 Gotchas (real ones)

| Symptom | Cause | Fix |
|---|---|---|
| `npm` SSL: `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` | Homebrew Node has no CA bundle | `echo cafile=/etc/ssl/cert.pem > ~/.npmrc` |
| `Error: No provider plugins found.` | Stale plugin cache from partial install | `rm -rf ~/.openclaw/plugin-runtime-deps` then retry |
| `models auth login requires an interactive TTY` | Auth wizards need a real terminal | Run in Terminal.app, not from a non-TTY shell |
| `Requested agent harness "codex" is not registered` | Onboarding skipped or failed | Re-run `openclaw onboard` in a real Terminal |
| `claude -p` subprocess hangs forever | OpenClaw spawning `claude -p` deadlocks on `~/.claude/sessions` lockfiles when called from inside another claude session | Don't drive OpenClaw from inside Claude Code; use Codex harness |
| Telegram `Network request for 'sendMessage' failed!` despite working `curl` | Gateway lacks `NODE_EXTRA_CA_CERTS` in launchd env | Edit plist → add `NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem` to `EnvironmentVariables`, `openclaw gateway restart` |
| Bot won't DM you proactively | Telegram bots can't initiate; user must `/start` first | Open chat, hit `/start`, then approve the pairing code |

### A.7 What not to do

- **Don't** sign up at clawhub.ai for the smoke test — the 63 stock plugins (`google`, `telegram`, `whatsapp`, etc.) are bundled with the npm package. ClawHub is the optional marketplace for *third-party* skills.
- **Don't** put `gateway.auth.token`, `channels.telegram.botToken`, or any other secret in agents-config — they live in `~/keys/` (mode 600) per machine, scp'd between hosts.
- **Don't** copy `~/.codex/auth.json` between machines — refresh tokens rotate and break whichever host pulled it last.
- **Don't** run multiple instances pointing at the same Gmail label without the idempotency strategy from §2.5.

---

## Appendix B — Hard rules for the executing agent

Agents picking this experiment up cold should re-read `~/agents-config/INDEX_RULES.md` first.

- **Refresh agents-config** (`git -C ~/agents-config pull`) and re-read `INDEX_RULES.md` (Hard Rule #5).
- **Never commit secrets.** Tokens live in `~/keys/`, mode 600 (Hard Rule #1).
- **Run QA** before reporting any non-trivial milestone done (Hard Rule #3).
- **Email Brando** at `brando.science@gmail.com` (CC `brando9@stanford.edu` + `brandojazz@gmail.com`) when each phase completes — counts as a "big task" (Hard Rule #13). Per Trigger Rule 26: always CC all 3 of Brando's emails on outbound mail.
- **Dual TLDR** on every response (Hard Rule #4).
- **Q&A leads with `**A (TLDR):**`** before detail (Trigger Rule 27).
- **Just-do-it** (Guideline #14) — but for OpenClaw, **stop and ask** before any of these:
  - Sending a reply from Gmail before the approval flow is verified end-to-end on **all** instances.
  - Pairing Baileys to a WhatsApp account other than Brando's.
  - Granting OpenClaw shell access on a SNAP node shared with other users (mercury2 — coordinate with `machine/mercury2.md`).
  - Modifying `~/Library/LaunchAgents/` outside the OpenClaw plist.

---

## Appendix C — Decision rationale (rejected paths)

- **Why not extend `uutils` with inbound webhook handlers + bot frameworks?** `uutils` is a notification utility library (one-way: `emailing.py`, `discord_uu.py`, `whatsapp_uu.py` — called from job schedulers and watchers). Building inbound + agent loop inside `uutils` would change its shape from utility to service. See `~/ultimate-utils/README.md` §"Notifications vs. Interactive Agents" and issue [brando90/ultimate-utils#41](https://github.com/brando90/ultimate-utils/issues/41).
- **Why not pay for `myclaw.ai` ($33–$66/mo hosted)?** Brando has the hardware and skills to self-host. Codex Pro covers the model calls. The recurring fee provides no benefit.
- **Why not make Claude Code the in-app agent?** It's a coding CLI, not a personal-assistant runtime. Wrong shape for "fire from phone, get reply back."
- **Why 3 instances and not 2 (the original spec)?** Original 2-instance plan (mercury2 + Mac mini) was superseded 2026-04-26 because the actual hardware is 3 (mercury2 + MacBook Air + MacBook Pro), and dropping WhatsApp (4-device cap exceeded) for Telegram-as-substrate let us scale up without device-cap pain.

---

## Appendix D — Status & Log (project history)

Append-only. Most recent entry on top.

| Date | Author | Phase | Status | Notes |
|------|--------|-------|--------|-------|
| 2026-05-08 | claude-code (mac-air) | — | files consolidated | Absorbed prior `cc_prompt.md`, `setup-tutorial.md`, `todos.md`, `wishlist.md` into MASTER_PLAN.md Appendices A–F; deleted those 4 files. Bot handle update (`@ultimate_brando9_sk_air_bot`) preserved across the absorption. SuperCare ASV resupply 4-tier analysis + McAllen summer 2026 travel test case + Outlook notification silence TODO absorbed into Appendix F. |
| 2026-05-08 | claude-code (mac-air) | — | persistence pass | Captured all chat-drafted artifacts: added `concepts.md` (Q&A explainers), `chatops.md` (fleet-management design), `standing_orders/travel_search.md`, `test_tasks/` (DM Sri + Saumya/NeurIPS email). Renamed Telegram bot `@ultimate_brando9_bot` → `@ultimate_brando9_sk_air_bot` across 5 sites. Added `lean_ai_club.md` "Monthly workhackathon nudge" sub-template. Added `INDEX_RULES.md` Trigger Rules 26 + 27. |
| 2026-05-08 | claude-code (mac-air) | — | master plan consolidated | Renamed `PLAN.md` → `MASTER_PLAN.md`; expanded to single source of truth. Absorbed PR #42's SE standing order verbatim. Added 7 new standing-order skeletons (grants, FB events, IG, Drive→social, Lean AI, experiment dispatch, paper announcements). Closed PR #42 as superseded by #46. Cross-checked against [docs.openclaw.ai](https://docs.openclaw.ai/llms.txt). 4 doc-verified corrections folded in. 8 new open decisions added to §9. |
| 2026-04-26 | claude-code (mac-air) | 0–1 | Air partially working | Codex-Pro-backed install live on the Air (gateway under launchd, `openclaw infer model run --gateway` returns `PONG` via `openai/gpt-5.5` on codex harness, Telegram bot `@ultimate_brando9_sk_air_bot` paired and chats with Brando). Open: gateway-side `openclaw message send --channel telegram` still fails with `HttpError: Network request for 'sendMessage' failed!` despite `NODE_EXTRA_CA_CERTS` + `NODE_OPTIONS=--dns-result-order=ipv4first --use-system-ca` + `NODE_TLS_REJECT_UNAUTHORIZED=0` set in plist; agent runtime's reply path through grammy works fine, so this only blocks operator CLI not the feature itself — parked. Architecture v2 (3 instances + Telegram-as-substrate) committed alongside. |
| 2026-04-26 | claude-code (worktree) | — | scope expanded | Added wishlist (full backlog) and `standing_orders/whatsapp_voice_draft.md` (voice-dictation → cleanup → approve → send flow, `never_autonomous` for auto-reply). Email-MVP plan unchanged. |
| 2026-04-26 | claude-code (mac-air, pre-flight) | 0 | blocked | Verified the spec's repo URL `steipete/claw-bot` returns 404; canonical repo is `https://github.com/openclaw/openclaw` (latest release v2026.4.24, MIT, Node 24 recommended). Spec edited to fix the dead URL and reference the built-in `openclaw onboard --install-daemon` (which obsoletes most of Phase 5's manual launchd work). |
| 2026-04-26 | claude-code (planning) | — | spec drafted | Initial spec drafted. Two-instance plan, Codex Pro as model, auto-restart required. No setup actions taken yet. |

---

## Appendix E — Current pickup state

(Verified 2026-04-26; bot handle updated 2026-05-08; refresh as state changes.)

| Channel / capability | State | Notes |
|---|---|---|
| Telegram (chat surface) | ✅ working | Bot `@ultimate_brando9_sk_air_bot` (renamed 2026-05-08 from `@ultimate_brando9_bot` via BotFather `/setusername`; token unchanged) paired with Brando, agent replies via Codex Pro / GPT-5.5. Token at `~/keys/openclaw_telegram_bot_token.txt` (mode 600), already rotated once. |
| Gmail (read + send) | ✅ working via `gog` skill | `gogcli` 0.13.0 installed, OAuth done, all 7 Workspace APIs enabled in GCP project 721441778080. `openclaw skills info gog` shows ✓ Ready. |
| Calendar / Drive / Docs / Sheets / Tasks / People | ✅ working via `gog` skill | All verified end-to-end |
| Discord | 🟡 blocked on user actions | Bot created (ID `1498169663278813254`, token in `~/keys/openclaw_discord_bot_token.txt`), wired into config, Discord refuses with **code 4014** because Message Content Intent is OFF on dev portal AND bot is in 0 servers. **To resume:** flip the toggle in Bot tab → Save Changes; run OAuth2 URL Generator and invite bot to a server Brando owns. |
| WhatsApp | 🟡 parked on upstream | Baileys 7.0.0-rc.9 returns `status=500` from web.whatsapp.com on every pair attempt. Not local. **To resume:** wait 24h+ then retry once; if still broken, defer until stable Baileys v7. |
| Gmail label idempotency / heartbeat / rate limit | ◯ not started | Blocked on Air email-triage E2E first |
| Triage admin-email loop end-to-end | ◯ not started | Needs admin-filter list (Brando) + one real test email |
| MacBook Pro install | ◯ not started | Needs SSH config OR Brando runs install script himself |
| mercury2 install | ◯ not started | Needs SSH access; Linux path (no launchd) |

**Suggested resume sequence (smallest unblocked next step first):**
1. Brando enables Discord Message Content Intent + invites bot to a server (~90s) → Claude restarts gateway, confirms Discord ✓ (parallelizable)
2. Brando edits `config/admin-filter.txt` with his real admin-sender list (~1 min) and DMs the Telegram bot one real triage to validate the loop
3. Replicate to Pro via the install script
4. Replicate to mercury2 (Linux path — different recipe; see §6 Phase 4)
5. Wire idempotency labels + heartbeat + rate limit (autonomous)
6. 7-day soak

---

## Appendix F — Beyond admin-email triage (post-MVP capabilities)

Downstream of the Phase 5 soak and the Phase 6 standing-order rollout. Tracked as Phase 7+ work.

### F.1 Personal-portal automation

- **SuperCare Health login + tasks (general)** — agent should log in to supercare.com (and similar personal portals) via OpenClaw's bundled `browser` plugin and complete tasks Brando assigns ("check my prescription status", "request a refill", "schedule X"). Requires: (a) browser plugin enabled (already loaded in stock 63); (b) credentials in `~/keys/supercare_credentials.json` (mode 600, not committed); (c) per-task prompt from Brando in Telegram; (d) 2FA strategy — for sites that require it, agent DMs Brando the code request, Brando pastes back. Start with non-2FA flows.

- **SuperCare ASV resupply auto-confirmation** — Brando uses a ResMed AirCurve / BiPAP ASV machine for sleep apnea. SuperCare Health (his DME supplier) gates each insurance-defined resupply cycle (masks every 1–3 mo, headgear/tubing on staggered cadences) on Brando confirming "yes still using, ship the next batch."
  - **Tier 1 (easy)** if SuperCare's trigger is **email-based**: add their sender to `config/admin-filter.txt`; triage agent drafts "yes please ship, machine in active daily use" → Brando approves in Telegram → agent sends. Slots straight into the email-triage MVP.
  - **Tier 2 (medium)** if **portal login required**: use OpenClaw's bundled `browser` plugin. Credentials in `~/keys/supercare_credentials.json` (mode 600). Screenshot-before-submit per the standing-orders default safety rules.
  - **Tier 2.5 (harder)** if **SMS**: needs Twilio or iMessage relay; Telegram can't see SMS.
  - **Tier 0 (out of scope)** if **phone-call only**: voice-agent territory; not realistic for v1.
  - **Status:** blocked on Brando forwarding one recent SuperCare resupply notification (any redacted PII fine) so we know which tier applies before designing.

- **General "do X for me" capability** — extend the triage prompt to handle ad-hoc requests Brando DMs the bot (not just inbox triage): "book me a haircut", "summarize my W&B runs from this week", etc. Requires the same exec-policy / tool-execution unlock as the triage shell unlock plus per-capability prompts and credential storage.

### F.2 Quick personal TODOs (track here, don't lose)

Small ad-hoc fixes Brando wants to do once and forget:

- [ ] **Silence Outlook (Stanford email) notification sounds without closing the app.** Beeps from Outlook while working are disruptive. Fix path (any one):
  - **macOS System Settings:** Settings → Notifications → Outlook → uncheck **Allow notifications** (or just **Play sound for notifications** to keep banners but kill sound).
  - **Outlook for Mac in-app:** Outlook → Settings → Notifications & Sounds → uncheck "Play a sound" (also "Show on screen" if Brando wants full silence).
  - **Outlook web:** Settings → General → Notifications → uncheck the relevant ones.
  - Effect: Outlook keeps running in the background (mail still syncs); no more sounds. Brando can re-enable any time.
  - This is a 30-second fix; tracked here so it doesn't get lost.

### F.3 First test cases queued

Concrete real-world inputs to validate pipelines as standing orders ship:

- **Travel search (Phase 6.8):** McAllen / Harlingen summer 2026 trip.
  - **Window:** Sat Jun 13 → Sun Jun 21 2026 (8-day natural gap between Stanford spring quarter end Jun 10 and summer quarter start Jun 22). Backup: Aug 16 → Aug 23.
  - **Origin:** SFO (alt: SJC, OAK). **Destinations:** MFE (McAllen) or HRL (Harlingen) — flexible, pick cheaper.
  - **Airline preference:** Southwest (free carry-on, frequent SFO→DAL/HOU→RGV routes); American/United also fine.
  - **Verified Stanford 2026 calendar:** spring quarter ends Wed Jun 10, commencement Sun Jun 14, summer quarter Mon Jun 22 → Sat Aug 15 ([source](https://studentservices.stanford.edu/calendar-events/academic-calendars/stanford-academic-calendar-2025-2026)).
  - **Status:** spec'd, blocked on `travel_search.md` going live.

- Other concrete validation inputs live in [`test_tasks/`](./test_tasks/) — `dm_sri_agent_flex.md` (Discord DM test) and `email_saumya_neurips.md` (Gmail send + CC-3-emails rule test).

These are tracked here; they're not on the Phase 0–6 critical path.
