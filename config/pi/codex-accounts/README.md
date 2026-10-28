# Personal and Vals Codex subscriptions in Pi

**Doc link:** https://github.com/brando90/agents-config/blob/main/config/pi/codex-accounts/README.md

**TLDR:** Install this local provider package, run `/reload`, then `/model` and search `personal-codex` or `vals-codex`. Both use existing ChatGPT subscription logins, never API keys.

```bash
pi install ~/agents-config/config/pi/codex-accounts
node --test ~/agents-config/config/pi/codex-accounts/auth.test.mjs
```

Unlike the Claude adapter, this delegates to Pi's native Codex subscription transport rather than launching a Codex child agent. Pi retains the transcript and executes its own tools. Each account gets a distinct transport registration and reads only its own `~/.codex/auth.json` or `~/.codex-vals/auth.json` on every request. Environment API keys and `CODEX_HOME` do not select the account. No credentials are copied into Pi or Git. The shared ordinary-Pi default is `vals-codex/gpt-6.1-sol` with medium thinking (10-28-2026); other account switches are manual. Only use Vals for authorized Vals work.

Models are the intersection of Pi's OpenAI catalog and an account-specific catalog. Pi first reads its private `codex-account-models/<provider>.json` when its account identity matches the current login, then falls back to that profile's Codex `models_cache.json`. Model discovery needs both a locally valid subscription token and a cache. Run a current Codex client in that profile to initialize/refresh them, then `/reload`. Catalog requests from older client versions can omit newer models even with valid credentials; refresh using the current client version rather than copying another account's catalog. `/codex-accounts` checks local token validity only, not server acceptance or remaining allowance.

To refresh Pi's isolated catalog without generating tokens, use the installed current Codex client version (verified version in this rollout: `0.165.0`):

```bash
node ~/agents-config/config/pi/codex-accounts/refresh-models.mjs vals-codex 0.165.0
```

This makes one authenticated model-list request and stores only model slugs, account identity and fetch metadata in owner-only Pi storage. It never writes Codex's shared cache or tokens. An older running Codex client can overwrite its own model cache without removing newer models from Pi. Authentication failures retain the previous catalog; account identity changes reject the isolated cache. Run this per host/profile after preparing its existing authorized login, then `/reload`.

Codex owns authentication refresh. This integration intentionally does not rotate or rewrite the CLI's shared tokens. An expired token fails explicitly: refresh the appropriate profile using `codex` or `codex-vals`, then retry (reload if the provider was unavailable at startup). There is no automatic account or API-key fallback. Catalog cost estimates do not measure subscription charges or remaining allowance; existing account usage policies remain unchanged.

## Verification — 10-26-2026

- Fresh installed Pi model listing: seven models each for `personal-codex` and `vals-codex`.
- Vals `gpt-6-astra`: returned `ACCOUNT_OK`; Pi `read` tool returned this package's name.
- Personal `gpt-6-astra`: server reported usage limit reached; successful personal inference remains unverified.
- Deterministic auth tests cover file rereads, missing/malformed credentials, expiry, identity mismatch and rejection of API-key mode.
- Image input, long context, cross-provider transcript continuation and token-refresh recovery have not been live-tested.
