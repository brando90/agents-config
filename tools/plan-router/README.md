# Subscription plan router

Run one bounded job through an existing native subscription client. Python 3.9+ standard library only; Linux and macOS (`fcntl.flock`). This does not provide a model API, install clients, sign in, change billing, schedule work or run a daemon.

The adapters are argument arrays, never shell commands. Prompts go to standard input unless an argument contains `{prompt}`; `{workspace}` expands to the canonical workspace path. Native account wrappers/profiles retain their own credentials. This program never reads a credential file.

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
- `generic_fallback`: permits this plan as an alternative only for jobs explicitly invoked with both `--generic --allow-fallback`. Sponsor-limited plans are excluded in the example. Default execution stays on the selected plan and model.
- `allow_unknown_once`: permits one bounded job from a fresh `availability` observation when the vendor exposes no remaining-allowance meter. Record this only after a successful request on that exact route. It reports unknown remaining allowance; it never invents a percentage. That observation is consumed atomically at admission, even if the subsequent job fails. A known threshold still blocks it.

The runner removes inherited provider-key, API endpoint, cloud-provider and profile override variables, then applies only configured native profile directories. Wrappers must also be audited to preserve the declared subscription route. Codex jobs require `forced_login_method=chatgpt` and an explicit enabled sandbox. Sandbox-disabling/permission-bypass arguments and Claude `--bare` are rejected. Cursor's example uses read-only Ask mode; for coding, deliberately configure normal agent mode and workspace permissions. No global client settings are changed.

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

## Bounds and receipts

Admission stops at **80% used weekly** or **100% used in the short window**. Both observations must be current unless the explicit one-job unknown-allowance option applies. Observations are snapshots; concurrent use elsewhere can consume allowance after observation. The threshold is an admission rule, not an in-flight spend cap. Native turn limits, where configured, and an outer timeout bound each job.

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

Provider references: [Codex noninteractive mode](https://developers.openai.com/codex/noninteractive), [Codex authentication](https://developers.openai.com/codex/auth), [Claude CLI](https://code.claude.com/docs/en/cli-reference), [Claude authentication](https://code.claude.com/docs/en/authentication), [Cursor CLI authentication](https://cursor.com/docs/cli/reference/authentication), [Cursor headless mode](https://cursor.com/docs/cli/headless), [Grok CLI reference](https://docs.x.ai/build/cli/reference), [Grok headless scripting](https://docs.x.ai/build/cli/headless-scripting). Use Google's native Antigravity client for the Google adapter.
