# Pi: switch Claude subscription accounts with /model

**Doc link:** <https://github.com/brando90/agents-config/blob/main/config/pi/claude-accounts/README.md>

**TLDR:** This local Pi **provider extension** exposes three existing Claude Code accounts in `/model`. It is not a skill. Vals and Stanford passed live text tests, a Vals Pi-tool round trip, and a Vals-to-Stanford same-session history test on 10-23-2026. Personal is configured but its live request failed because Anthropic reported its token revoked; cached `auth status` alone did not detect that.

## Use

In ordinary Pi, run `/reload`, then `/model` and search:

- `personal-claude-code`
- `vals-claude-code`
- `stanford-claude-code`

Each has `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5`, and `claude-haiku-4-5`. These are actual upstream IDs, not model-renaming aliases. Model availability can still differ by plan; live acceptance used Haiku, not every model. The default model/effort is unchanged.

Switch manually when a plan is exhausted. `/scoped-models` chooses the routes used by Ctrl+P. `/claude-accounts` checks identity and the local tool bridge without inference. That command reports cached sign-in, not guaranteed server acceptance or remaining allowance. No automatic cross-sponsor fallback is installed. Only use each sponsor for work it authorizes.

**Personal reauthentication:** use the normal personal `claude auth login` with `CLAUDE_CONFIG_DIR` unset. A bounded login attempt was made but browser approval did not complete. Vals uses `.claude-vals`; Stanford uses `.claude-su`. The personal profile intentionally leaves `CLAUDE_CONFIG_DIR` unset because explicitly setting `.claude` selects a different keychain namespace on this Mac. No login tokens are extracted, copied or placed in Git.

## Reproduce and synchronize

The shared `../runtime.json` declares this local package. The main installer prepares its locked dependency, applies the hash-checked compatibility patch, generates host-specific launchers, and then writes the normal sync receipt:

```bash
python3 ~/agents-config/config/pi/install.py --runtime-only
python3 ~/agents-config/config/pi/install.py --check
# In the running Pi: /reload
```

Or install just this package, preserving unrelated settings:

```bash
python3 ~/agents-config/config/pi/claude-accounts/install.py
```

Prerequisites: a working `claude` executable, npm, Python 3, and the locally authorized Claude account logins. Installation does not copy Mac credentials to remote machines. Configure account directories/expected identities in `accounts.json` for intentional changes; absence of matching authentication is a visible failure, not a fallback to another payer.

Generated files live under the selected Pi agent directory:
- `claude-accounts.json`: non-secret launcher locations and expected account metadata.
- `claude-account-bin/*`: one executable per provider, each selecting its own profile.
- `settings.json`: adds the package without replacing defaults or unrelated settings.

Source and the lockfile live here; `node_modules` is excluded from Git. Account selection is per child process, not process-global environment mutation, so simultaneous requests cannot swap each other's profile. The launcher checks both email and organization ID before inference and strips inherited API-key/gateway/other-profile overrides. Claude Code retains responsibility for authentication and refresh.

## Transport and limitations

Pinned dependency: `pi-claude-code-provider@0.6.0`, [chem's MIT-licensed transport](https://github.com/chem/pi-claude-code-provider). Its author mothballed it; this integration is **experimental**, not an Anthropic-supported product or a promise of compatibility with future Claude/Pi releases. The lockfile includes npm integrity. Update only with new acceptance tests.

The unmodified official Claude CLI runs in print mode. Its proposal-only tool transport returns tool calls for **Pi** to execute. Pi owns history, branching, compaction and file changes; Claude's own native tools do not execute them invisibly. Each request replays Pi's transcript; this can use more context than a native model endpoint. Mid-response abort and context limits retain the upstream transport's behavior. Visual terminal testing, long conversations, images, and every model/account combination were not exhaustively tested here.

Claude Code 2.1.309 needed two narrow compatibility adjustments:
1. The child settings disable the new optional `plugin-authoring@builtin`, not the user's saved settings.
2. `patch_dependency.py` permits the exact built-in `cc-plugin-sec-default` name in the adapter's initialization inventory. The native security plugin remains active. Unexpected tools, skills, other plugins, credential sources and MCP servers are still rejected. The patch verifies the original source SHA-256 before applying and verifies it again on repeat application.

Quota errors surface to Pi; there is no silent alternative-account retry. This does **not** disable already-enabled Anthropic extra usage or enforce an account billing cap. Do not interpret Pi's catalog-price estimate as an actual subscription charge, free usage or a remaining-balance indicator. No credits, overage settings, budgets or subscriptions were changed.

## Evidence, 10-23-2026

Versions: Pi 1.4.0; Claude Code 2.1.309; transport 0.6.0.

| Check | Result |
|---|---|
| Model discovery | 12 routes: 3 accounts × 4 models |
| Local account identity checks | All three matched configured email/organization; personal's cached result was stale |
| Personal live request | FAILED: server returned 401, OAuth token revoked; needs login |
| Vals live Haiku response | PASS: `ACCOUNT_OK` |
| Stanford live Haiku response | PASS: `ACCOUNT_OK` |
| Pi tool execution through Vals | PASS: Pi `read` event and requested file-content response |
| Same-session account switch | PASS: Vals remembered a test word; Stanford returned it from the same Pi session |

Tests use ephemeral directories and owned process groups, disable retries, and make only bounded short subscription requests. Failed initialization attempts are not counted as successful inference. No model API keys were loaded. No running user session was restarted or changed to another model.

```bash
python3 -m unittest discover -s ~/agents-config/config/pi/claude-accounts/tests -v
pi --offline --no-extensions -e ~/agents-config/config/pi/claude-accounts/tests/protocol.ts --no-mcp --list-models
python3 ~/agents-config/config/pi/claude-accounts/verify.py
# Optional LIVE checks consume subscription allowance:
python3 ~/agents-config/config/pi/claude-accounts/verify.py --live --account vals
python3 ~/agents-config/config/pi/claude-accounts/verify.py --live --account stanford
python3 ~/agents-config/config/pi/claude-accounts/verify.py --live --account vals --tool-only
```

The same-session switch was separately exercised with a disposable `--session` file. Both processes used the same file but different explicit provider IDs. No tokens or full private transcripts are needed to reproduce it.

To remove: remove the package declaration from the runtime manifest (or the applicable host override), apply runtime sync, then `/reload`. Do not remove or log out of the user's Claude profiles. `pi-local` and `pi-gemini` retain their intentionally separate extension-loading policies.
