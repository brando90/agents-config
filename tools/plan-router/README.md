# Subscription plan router

Run one bounded job through an existing native subscription client. Python 3.9+ standard library only; Linux and macOS (`fcntl.flock`). This does not provide a model API, install clients, sign in, change billing, schedule work or run a daemon.

The adapters are argument arrays, never shell commands. Prompts go to standard input unless an argument contains `{prompt}`; `{workspace}` expands to the canonical workspace path. Native account wrappers/profiles retain their own credentials. This program never reads a credential file.

Google consumer-plan assistant dispatch is currently held: [Google's FAQ](https://antigravity.google/docs/faq) excludes wrapping native `agy` in a third-party assistant and warns of suspension. Direct user scripting differs from assistant orchestration. The included adapter and passing access tests do not establish policy permission. Keep that profile disabled pending the account owner's explicit risk decision; see the [workflow](../../workflows/subscription-plan-routing.md). Disabled routes make no native refresh or inference calls.

## Quick start

From the repository root, after preparing a private configuration and fresh account observations:

```bash
python3 tools/plan-router/router.py --config ~/.config/plan-router/config.json status --refresh
python3 tools/plan-router/router.py --config ~/.config/plan-router/config.json run \
  --prompt-file ./job.md --workspace ./project
```

The runner must execute on the machine holding the native client sign-ins. A remote installation can keep `router.py` under `~/.local/lib/plan-router/`, the configuration under `~/.config/plan-router/` and logs under `~/.local/state/plan-router/`. Running it does not require changing existing experiment drivers.

## Configure

Copy `config.example.json` into a private directory outside the source checkout and job workspace. The example plans are **disabled and unverified**. Check installed CLI versions, account/sponsor scope, supported model IDs and existing billing controls before enabling each one. Cursor/Grok example model IDs are placeholders for a verified installed catalog, not verified entitlements.

Each plan pins `model`, `argv` and timeout. `argv` must explicitly select that exact model. `subscription_only` is an expiring local record of a checked entitlement and the absence of additional-credit/on-demand spillover; set `verified`, `expires_at` (timezone required) and `evidence` only after checking the actual account. It is an attestation, not a vendor billing switch or guarantee. The program does not purchase anything or alter existing billing settings.

Optional fields:

- `env`: only `CODEX_HOME` and `CLAUDE_CONFIG_DIR`, expanded per child process. Use existing native profiles or wrappers, never credentials in JSON.
- `auth.argv`: non-inference native status command. Claude requires JSON `authMethod` equal to `claude.ai` or `oauth_token`; Codex requires its native ChatGPT status message. Other clients use a configured positive `auth.match`, with common negative status messages rejected. These checks do not prove server acceptance or remaining allowance.
- Without `auth.argv`, record a fresh `auth` observation after checking the native account.
- `quota_group`: the same value for aliases sharing allowance; otherwise defaults to plan ID. Aliases must also share the configured vendor model pool. It does not reserve allowance against unrelated clients.
- `refresh_argv` and `refresh_group`: native Antigravity `agy -p /usage` reads the matching TSV pool (`Gemini Models`, or `Claude and GPT models`) only. Remaining percentages become used percentages. The observation expires after 15 minutes or at reset, whichever comes first. Native refresh runs before each job; `status --refresh` is optional. Missing/invalid refresh results stop the invocation.
- `allow_unknown_native`: explicit approval for bounded native Claude/Codex/Cursor/Grok subscription jobs when those clients expose no percentage meter. Requires their native authentication-status command and the current subscription-only attestation. Remaining allowance stays unknown and the native client enforces its own limit; a known fresh quota threshold still blocks. This avoids requiring a separate token-consuming probe before every job after an idle period.
- `require_fresh_weekly`: boolean reserve gate, required for every Cursor/Grok plan that sets `allow_unknown_native` (config load rejects it otherwise). Before any inference the shared `quota_group` must hold a real, unexpired weekly observation (`observe --window weekly` from the signed-in dashboard, with a future reset) with `status` ready and `used_percent` below 80. Unknown, stale, reset, malformed or at-or-above-80 weekly values block the plan even though `allow_unknown_native` still tolerates an unmetered short window. Never record an unmeasured short-window percentage. Jobs already running are unaffected; the gate checks admission only.
- `renew_availability_on_success`: with `allow_unknown_once`, a completed native job renews one admission for at most 15 minutes (bounded by entitlement expiry). Failed/partial/timed-out jobs never renew it. This supports an approved native subscription without pretending it exposes a percentage; known quota thresholds still win. Leave disabled unless that route and existing billing scope have been checked.
- `generic_fallback`: permits this plan as an alternative only for jobs explicitly invoked with both `--generic --allow-fallback`. Sponsor-limited plans are excluded in the example. Default execution stays on the selected plan and model.
- `allow_unknown_once`: permits one bounded job from a fresh `availability` observation when the vendor exposes no remaining-allowance meter. Record this only after a successful request on that exact route. It reports unknown remaining allowance; it never invents a percentage. That observation is consumed atomically at admission, even if the subsequent job fails. A known threshold still blocks it.

The runner removes inherited provider-key, API endpoint, cloud-provider and profile override variables, then applies only configured native profile directories. Wrappers must also be audited to preserve the declared subscription route. Codex jobs require `forced_login_method=chatgpt` and an explicit enabled sandbox. Sandbox-disabling/permission-bypass arguments and Claude `--bare` are rejected. Cursor's example uses native read-only Ask mode and `--trust` for the deliberately selected workspace; Grok uses native Plan permission mode. These are analysis routes, not editing routes. No global client settings are changed.

## Cursor and Grok sign-in recovery

Use the exact executable and environment intended for dispatch. Cursor `agent status` may print a positive login line while saying it cannot fetch user details; reject that state. Complete `NO_OPEN_BROWSER=1 agent login`, including any fresh provider sign-in and the final CLI approval, while the native poller remains alive. Confirm both `agent status` and `agent models`. Browser approval alone is insufficient. `agent update` may itself need working authentication.

Grok Build supports `grok login --device-auth`; complete its displayed device code in the browser, then confirm `grok models` says the account is logged in with grok.com. Its installed catalog and flags take precedence over guessed model IDs or example flags. The verified selections on 11-16-2026 were Cursor `grok-4.7-high` and Grok `grok-4.7` (native result metadata reported `grok-4.7-build`). Only these exact selections were exercised here; both installed-router results passed 18 independently evaluated clamp edge cases. See the [native check record](native-live-checks.json).

Some Linux hosts cannot start the optional bubblewrap sandbox. Keep the existing host controls and use the documented native read-only modes for analysis; this does not establish kernel isolation or authorize changing to editing/automatic-approval modes. The examples omit an explicit sandbox request for these two read-only clients, rather than passing a sandbox-disabling or force flag. Other hosts may deliberately enable a supported sandbox. Grok 1.0.34 did not advertise `--no-memory`; do not assume an example flag exists.

Cursor and Grok can share the same first-party subscription pool: use one `quota_group` for both. Check the signed-in dashboard and actual billing treatment. First-party included usage differs from third-party Cursor models, which may require prepaid Additional Usage from their first request. Do not mark a third-party model eligible merely because it appears in the catalog. Check prepaid credit and optional automatic top-up as well as the current included pool; an expiring local attestation is not a billing control. See [usage limits](https://docs.x.ai/x-subscription/usage-limits) and [credits and top-ups](https://docs.x.ai/x-subscription/extra-usage).

When no native short-window meter exists, leave it unknown. The same explicit `allow_unknown_native` option supported for Claude/Codex also accepts verified Cursor/Grok native status commands; it checks native authentication on each bounded request and still requires a current subscription-only attestation. Known fresh shared-pool thresholds still block. A successful independently checked native request can seed `allow_unknown_once`; only completed subsequent requests renew its short-lived admission when `renew_availability_on_success` is explicitly set. A failed request never supplies that proof. The native clients retain their own credentials; do not copy active refresh credentials between hosts.

## Observe and run

Examples below use an already prepared private configuration at `~/.config/plan-router/config.json`. Relative prompt paths are interpreted from the caller's directory.

```bash
python3 router.py --config ~/.config/plan-router/config.json status
python3 router.py --config ~/.config/plan-router/config.json refresh --plan personal-agy
python3 router.py --config ~/.config/plan-router/config.json status --refresh

# Replace timestamps and percentages with current native observations.
python3 router.py --config ~/.config/plan-router/config.json observe \
  --plan personal-claude --window weekly --used-percent 20 \
  --reset-at 2026-11-23T18:00:00Z --expires-at 2026-11-16T20:00:00Z \
  --source 'Native usage panel checked at observation time'
python3 router.py --config ~/.config/plan-router/config.json observe \
  --plan personal-claude --window short --used-percent 10 \
  --reset-at 2026-11-16T22:00:00Z --expires-at 2026-11-16T20:00:00Z \
  --source 'Native five-hour usage panel'

python3 router.py --config ~/.config/plan-router/config.json run \
  --plan personal-claude --prompt-file ./job.md --workspace ./project

# An explicitly generic job can consider the finite configured alternatives.
python3 router.py --config ~/.config/plan-router/config.json run \
  --prompt-file ./job.md --workspace ./project --generic --allow-fallback
```

For an account without a machine-readable allowance meter:

```bash
python3 router.py --config ~/.config/plan-router/config.json observe \
  --plan personal-grok --window auth --status ready \
  --expires-at 2026-11-16T20:00:00Z --source 'Native account checked'
python3 router.py --config ~/.config/plan-router/config.json observe \
  --plan personal-grok --window availability --status ready \
  --expires-at 2026-11-16T20:00:00Z --source 'Successful bounded request; remaining allowance unknown'
```

Those example timestamps expire: replace them with real current evidence. Do not reset an availability observation merely to retry a failed/partial job.

## Model and effort selection

`models --plan personal-agy` lists exact native IDs and their verified/enabled state. Each optional `models` entry contains `id`, `label`, `family`, `effort`, `refresh_group`, `quota_group`, and boolean `frontier`, `enabled`, `verified` fields. The configured pinned `model` must exist in the catalog. Effort embedded in an ID is sufficient; set `effort_flag: "--effort"` only for clients and models that support a separate switch. Orchestrator uses `effort: "default"` and no independent effort switch.

`run --model ID` selects an exact entry; a family name selects its medium variant unless `--effort` is given. An effort-only override selects that variant of the pinned family. Unsupported, disabled, unverified or ambiguous choices are rejected before dispatch. `--frontier-only` rejects nonfrontier selections; frontier tags are explicit local metadata and must reflect the project's requirements.

Generic jobs without an explicit plan use `difficulty_defaults` (or `frontier_difficulty_defaults`) mapping `easy`, `medium`, `hard`, `multistep` to exact IDs. `--difficulty auto` uses a transparent keyword heuristic; an explicit difficulty overrides it. Research runs and explicit plans stay model-pinned unless a model/effort override is explicitly given. No capability comparison is inferred from the heuristic. See the [routing workflow](../../workflows/subscription-plan-routing.md).

Model copies share the account's credentials and their configured native quota pool. `status` keeps one account row and adds local per-model token/job counts plus the corresponding shared-pool windows. It does not treat multiple variants as independent allowances. Receipts record selected effort, difficulty and selection reason.

## Bounds and receipts

Admission stops at **80% used weekly** or **100% used in the short window**. Both observations must be current unless an explicitly configured unknown-allowance option applies. Observations are snapshots; concurrent use elsewhere can consume allowance after observation. The threshold is an admission rule, not an in-flight spend cap. Native turn limits, where configured, and an outer timeout bound each job.

A nonblocking lock covers the canonical workspace across router processes, including different configuration/state directories. The child inherits the lock descriptor, so the native client continues to hold it if the parent is abruptly killed. Normal completion, interruption or timeout terminates the owned process group. Clients that deliberately detach into a different process group are outside this containment contract; use native bounded, non-detaching CLI modes.

Fallback is preflight-only: unavailable quota, missing client or rejected subscription authentication can select the next configured candidate, once. **Once an inference command starts, any error, timeout or partial tool work ends this invocation without fallback or retry.** This includes an immediate server-side quota error: the runner does not assume that no work happened. Authentication-check and quota-refresh timeouts also stop the invocation. Scientific runs stay pinned unless a separate, explicit generic run is requested. No cross-provider transcript continuation is claimed.

Private state defaults to `~/.local/state/plan-router` (`--state-dir` overrides it). Directories/files use owner-only permissions. Each job records plan, configured model, workspace, prompt hash, timestamps, return code and private stdout/stderr. A receipt marked `running` after an abrupt parent failure is unresolved, not completed. Preserve logs and reconcile partial work before another manual invocation. This tool does not decide whether an artifact is correct or automatically resume it.

`status` emits one JSON row per configured plan: fresh/stale/unknown quota windows, source and reset timestamps, availability admission status, job/completion counts and available token counters. Token counters are read from JSON result/turn events; absent counters remain `null`. They are not an allowance or billing estimate. Counts cover this state directory only, not every other application using the account. The recorded model is the configured selection; verify actual provider model metadata in native logs for experiments.

## Deterministic verification

```bash
python3 -m unittest discover -s . -p 'test_*.py' -v
```

Tests use fake clients and temporary owned files only: exact prompt transport, API environment scrubbing, auth-source rejection, quota/expiry gates, pool-specific native refresh, one-job unknown allowance, explicit fallback, partial writes, process-group timeout cleanup and competing workspace writers. They do not sign in, call a provider or prove actual entitlement.

## Live verification (11-16-2026)

A native Antigravity `gemini-4-argon-high` job passed through this runner on Linux. It corrected `min(lo, max(hi, x))` to `max(lo, min(hi, x))`; an independent assertion checked outputs `[5, 0, 10]` for the three requested clamp cases. The native JSON reported success and token counters, and `/usage` supplied both matching Gemini quota windows. This verifies that installation and account at that time; every other installation must verify its own login, entitlement and allowance. Adapters and example entries alone do not establish live access.

The [catalog smoke-check record](live-checks.json) covers 22 native model/effort choices. Each returned a successful clamp correction, independently checked on 18 edge cases. Some required a clarified prompt or a new disposable check after timeout/service error; Orchestrators reject a separate effort switch. These are access checks, not a quality ranking. `status --refresh` reads each configured shared quota pool once.

Provider references: [Codex noninteractive mode](https://developers.openai.com/codex/noninteractive), [Codex authentication](https://developers.openai.com/codex/auth), [Claude CLI](https://code.claude.com/docs/en/cli-reference), [Claude authentication](https://code.claude.com/docs/en/authentication), [Cursor CLI authentication](https://cursor.com/docs/cli/reference/authentication), [Cursor headless mode](https://cursor.com/docs/cli/headless), [Grok CLI reference](https://docs.x.ai/build/cli/reference), [Grok headless scripting](https://docs.x.ai/build/cli/headless-scripting). Use Google's native Antigravity client for the Google adapter.


## Timed weekly browser observation (2026-11-21)

Cursor and Grok can import a shared Premium observation from a browser producer.
This imports a capture; it does **not** fetch the dashboard from a headless host.
The producer must navigate to the signed-in dashboard and extract current visible
usage before submitting each job. Do not copy browser cookies or credentials.
If no producer/browser session is available, starts stop once the original capture
is ten minutes old. This is not an unattended server-side browser service.

Set `refresh_format` to `timed-weekly-json` and `refresh_argv` to a command that
prints one JSON object with these fields (values below describe the format):

- `schema`: `xai-weekly-v1`; `status`: `ready`.
- `url`: `https://grok.com/dashboard`.
- `observed_at`, `expires_at`, `reset_at`: timezone-aware ISO timestamps from the
  original capture. Expiry is at most capture + 600 seconds and no later than reset.
- `used_percent`: a finite JSON number from 0 through 100.

Capture time cannot be in the future or ten minutes old. The router removes the
previous weekly observation before refresh, imports the original timestamps and
checks the existing below-80%-used gate before authentication and admission.
Malformed/missing data, failed commands, stale dates and 80% or more block starts.
There is no fabricated short-window measurement. Importing old JSON never renews it.
A failed read must publish an error rather than leave an earlier successful capture.

`plan-rr.py` preserves the installed rotation and routes both `native:cursor` and
`native:grok` through the main router, with its quota, entitlement and read-only
clamp. These two entries no longer launch native commands directly or trust the
legacy expiry-only `xai-usage-guard` file. Other entries retain their existing routes.
No billing, spending-limit, credit or auto-top-up setting is changed.

## Lane limit events (11-23-2026, AT-3335)
A Claude plan with `"limit_events": true` (argv must carry `--output-format stream-json --verbose`) needs no dashboard reading or browser sign-in. It starts as "no reading yet". After each job the router stores the lane's own `rate_limit_event` (status, window, `resetsAt`, fraction used from `unifiedWindows`, `isUsingOverage`). The plan then pauses until `resetsAt` on `allowed_warning`, `rejected`, a `rate_limit` error, any overage in use, or a reported fraction used of 80% or more (the 20% reserve). Used by `stanford-claude` (one-year setup-token lane). Real first event, Stanford seat, 11-23-2026: `status allowed`, `five_hour`, `utilization 0`, `overageStatus rejected` (`org_level_disabled`), `isUsingOverage false`.

## Order of routes (11-23-2026, AT-3397)
Brando, 11-23-2026 17:25: "let's always start with vals and stanford first before my personal accounts". `plan-rr` is now a priority list, not a rotating counter. Order: Vals Claude (Opus 5.5), Stanford Claude, Stanford Codex, Vals key, Stanford gateway key, lab key; then personal Codex, personal Claude; then Cursor and Grok; then Allen's Gemini key; the Google plan last. A route is skipped only when the router gate says it is off, gated, or low (20% left). `--experiment` removes the Google plan (real experiment runs, Brando 11-23-2026 12:10); `--order` prints the order. The installed config lists the plans in the same order and its `default_plan` is `vals-claude-opus`. Included usage only, no extra charges, no keys printed, running jobs are never stopped.

## Vals Codex profile and admission guard (2026-11-24)

The restored skampere1 lane uses its own native profile, `~/.codex-vals-skampere1`, and GPT-6 Astra. Keep that sign-in on its host; do not copy rotating credentials between hosts. Install `vals-codex.py` as `~/.local/bin/vals-codex`; set `CODEX_HOME` to the host-specific directory, use `auth.argv = ["python3", "/absolute/home/.local/bin/vals-codex", "--check"]`, and prefix the existing native Codex argument array with `["python3", "/absolute/home/.local/bin/vals-codex", "--"]`. Retain explicit `forced_login_method=chatgpt`, model selection and the workspace sandbox. The private live configuration is intentionally excluded from this repository.

The guard verifies the intended Vals Pro account and current included usage through the native app server, rejects credits/unavailable usage, requires a reported weekly window, and stops at 80% used in any reported window. The actual account currently reports a weekly primary window and no secondary window; missing short-window data remains unknown. `allow_unknown_native` permits that absent short-window observation while the guard enforces the actual weekly reserve on every launch. The metadata-only `--check` makes no model request. A full job holds a nonblocking profile lock, first requires a real `OK` response from the configured model, rechecks allowance, then starts the requested command. Inherited provider-key overrides are removed. The full child inherits the profile lock descriptor.

Native Codex keeps and renews the saved sign-in. Revocation or failed refresh blocks the pre-job request before the requested work starts; an authenticated metadata row alone is insufficient. Today's successful native and routed requests establish working saved access, not a future renewal guarantee. The guard's deterministic tests cover the weekly-only response, wrong/missing account, reserve, credits, stale/nonfinite readings, real-response failure and a competing profile lock.


## Wait rule, difficulty tags and the 80% gate on personal lanes (11-24-2026, AT-3455)

Why: on 11-24 jobs fell to Brando's personal Codex whenever a Vals or Stanford lane was only paused for a short time, and the personal lanes had no usage gate, so personal Codex ran to 100% weekly. Brando's rules: Vals and Stanford first, personal last, 80% reserve, included usage only, no extra charges.

- **80% gate on personal Codex**: its router `auth` step is `codex-usage.py --gate 80 --expect <account>`: reads `account/rateLimits/read` (no inference, no key printed), refuses at 80% used on any window, without ordinary usage, or if credits could exist. Same for Vals Codex (`vals-codex --check`) and Stanford Codex (`stanford-plan-auth.py`).
- **Personal Claude**: `--output-format stream-json --verbose` with `limit_events: true`, so Claude Code's own limit report pauses it at 80% used until the window resets.
- **Claude lanes, `warn_gate: false` and `limit_probe: true` (11-24-2026, AT-3491 personal, AT-3494 Vals and Stanford)**: an `allowed_warning` alone no longer pauses the lane; only `rejected`, another non-allowed status, overage or 80% used (`item_blocks`). A stored old event is re-judged, so it self-heals. `limit_probe` makes one one-word `claude -p` call to refresh the stored limit event when it is older than 10 minutes, at `status --refresh` and before each run. Included usage only, no extra charges.
- **`plan-rr --difficulty light|medium|heavy` (default medium), `--urgent`**:
  - light: small lanes first (Cursor, Grok, Pi keys, Stanford gateway), then Vals and Stanford; never a personal lane.
  - medium: the normal order. A personal lane only when no Vals or Stanford lane returns within 3 hours (or `--urgent`), and not once that lane is 50% used.
  - heavy: Vals Codex, Vals Claude, Stanford Codex, Stanford Claude, STAIR Claude, then Cursor and Grok (Brando 11:28: heavy is allowed there; native CLIs, included allowance, 80% reserve and the fresh-reading guard stay). A personal lane only with `--urgent`; otherwise the job is queued for the first lane that returns.
- **Queue, no loss**: a job that would fall to personal while a Vals or Stanford lane returns in time is not run: exit 5, `plan-rr: WAIT until <time> for <lane>`, and a file in `~/.local/state/plan-router/queue/`. `plan-rr --queue` lists it, `plan-rr --resume <id>` runs it again (`--force` skips the wait). Exit 3 = no route.
- **Vals Codex takes one job at a time**: `plan-rr` waits up to 2 minutes for its lock before using a lower lane, and counts a busy lane as back in minutes.
- Return times come from the lane's own limit events (`observations.json`) and from `codex-usage.py` reads (cached 5 minutes).
- Tests: `python3 -m unittest test_plan_rr` (17 tests, stubs only) and `python3 -m unittest test_router`.
- **Prompts and the Google plan (Brando 2026-11-24 11:31)**: every lane takes a plain precise prompt; no "MY VOICE REQUEST" header or voice text to agy, Cursor or Grok. agy (`personal-agy`) stays last, light and medium jobs only, at most 10 a day (`~/.local/state/plan-router/agy-log.jsonl`), never bulk grids or experiment runs, no timing tricks.

## Daily Stanford Claude attestation (2026-11-24, AT-3467)
`plan-attest-auto.py` (installed as `~/.local/bin/plan-attest-auto`, run by `plan-rr` before each job) renews the `stanford-claude` attestation by itself. When under 6 h are left (or it expired) it makes one tiny native `claude -p` call on the lane (same argv, `--max-turns 1`, API keys scrubbed) and renews for 24 h only if Claude's own `rate_limit_event` shows status `allowed`, `overageStatus` `rejected`, `isUsingOverage` false and the window under 80% used. Otherwise the old attestation lapses and the reason goes to `~/.local/state/plan-router/attest-auto.jsonl`; a failed try is not repeated for 10 minutes. It edits only that plan's proof, never enables a plan or paid fallback. Tests: `python3 -m unittest tools/plan-router/test_attest_auto.py`.
