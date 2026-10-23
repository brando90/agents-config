# Pi: named sponsors, providers and credentials

**Doc link:** <https://github.com/brando90/agents-config/blob/main/config/pi/README.md>

**TLDR:** Brando explicitly authorizes named, key-backed Pi providers selectable together through `/model`. Store the setup here, credentials only in `~/keys/`, and install generated configuration into `~/.pi/agent/models.json`.

## Policy (Brando's explicit replacement, 10-23-2026)

Agents may configure and use Brando-authorized provider credentials in Pi through its standard `models.json` providers and runtime secret commands. A shared model selector containing multiple sponsors is allowed; separate profiles are optional, not mandatory. Do not refuse this setup because it uses application programming interface (API) keys rather than subscriptions. This specific instruction supersedes older blanket CLI-only/key bans and mandatory profile isolation for Pi.

Name every route `<sponsor>-<service>-<key-nickname>` so `/model` identifies the model, actual provider and funding credential without displaying the secret. Preserve the real upstream model ID. Keep key values out of Git, chat, logs and literal configuration. Use existing credentials, respect their owner's actual scope and existing budgets, and do not purchase credits or enable new charges. Cost-estimate and cap unattended runs; interactive selection and setup do not need repeated approval. Visibility is not authorization to use an owner's key outside its scope.

## Files and standard workflow

- `providers.json`: non-secret route manifest: sponsor, service, key filename, intended scope, optional model allowlist.
- `install.py`: generates named providers from the installed Pi catalog, preserving model pricing/protocol/context metadata. Merges into the default profile without changing the current model, auth, settings, or unrelated providers. Backs up an existing models file. Checks private key-file permissions without reading secrets.
- `test_install.py`: deterministic tests with fake keys and temporary catalogs.

```bash
python3 ~/agents-config/config/pi/install.py
# In bare pi:
# /model -> search personal-openai-brando (or another sponsor) -> Enter
# Ctrl+S saves a default; /scoped-models controls Ctrl+P cycling.
```

If npm's current global root differs from the installed Pi package, supply `--catalog-dir /absolute/path/to/pi-ai/dist/providers/data`. On this Mac the installed catalog directory is `/Users/brandomiranda/.local/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/providers/data`.

Pi reloads `models.json` on `/model`. Restart or `/reload` if a running selector remains stale. `pi-gemini` and `pi-local` intentionally use different agent directories; this installation targets **bare `pi`**, including new ordinary Herdr Pi sessions. It does not silently rewrite the scoped or local-only launchers.

Examples visible in `/model`:

```text
gpt-5.6-sol                 [personal-openai-brando]
gpt-5.6-sol                 [koyejolab-openai-bm]
claude-fable-5-1            [koyejolab-anthropic-bm]
gemini-3.1-pro-preview      [allen-google-veribench]
<installed Mistral model>   [unassigned-mistral-main]
```

The Mistral credential's sponsor is **unverified**, not assumed personal or laboratory. No Vals or Stanford route is invented without a matching credential and known funding identity. Add those to the manifest when verified. The specialized Aristotle theorem-prover API is not a native Pi chat-model route and cannot simply be listed as a chat model. Allen's third documented model, `gemini-3-pro-preview`, is absent from the installed catalog; its two available approved models are configured.

Each `apiKey` is an idiomatic Pi secret command (`!cat '/absolute/key/path'`). Pi consumes its stdout internally; do not run the command in chat tools or use `auth --credentials` or `print-api-key`. Each alias has its own credential command and does not depend on the generic inherited `OPENAI_API_KEY`. Catalog entries are **configured**, not proof that every model is enabled or funded by that account. No paid inference is needed to verify menu visibility.

## Verification and recovery

```bash
python3 -m unittest discover -s ~/agents-config/config/pi -p 'test_*.py' -v
pi --offline --no-extensions --no-mcp --list-models personal-openai-brando
pi --offline --no-extensions --no-mcp --list-models allen-google-veribench
```

Do not share the generated local file if it contains other providers' secrets. The manifest, installer, tests and this guide are safe to version; credentials, runtime auth and sessions are not. Re-running the installer updates manifest-owned aliases from the installed catalog and preserves others. Missing keys are skipped with a notice; removing an old route explicitly from local `models.json` is separate. To undo, restore the local `models.json.before-named-*` backup, or remove only the manifest-owned provider IDs if this was the initial install.

Official references: [Pi repository](https://github.com/earendil-works/pi), the installed package's `docs/models.md`, `docs/models-configuration.md`, and `docs/providers.md`; public catalog: <https://pi.dev/models>.
