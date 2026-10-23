# Pi: shared configuration and named providers

**Doc link:** <https://github.com/brando90/agents-config/blob/main/config/pi/README.md>

**TLDR:** Keep shared Pi settings, extensions and pinned packages in this directory, then apply them on each machine with `install.py --runtime-only`; `install.py --check` or Pi’s `/config-sync` shows drift. The full installer also configures named providers for `/model`, keeping credentials outside Git.

## Sync settings, extensions and packages

`runtime.json` is the portable source of truth. `sync_runtime.py` applies it to the selected Pi agent directory and stores a private receipt there. The default profile is `~/.pi/agent`; `--agent-dir` explicitly targets another profile. The installer does not copy authentication, sessions or credentials between machines, and the runtime-only path leaves model providers unchanged.

Run this on each machine after publishing your configuration changes:

```bash
git -C ~/agents-config pull --ff-only
python3 ~/agents-config/config/pi/install.py --runtime-only
python3 ~/agents-config/config/pi/install.py --check
# In an existing ordinary Pi session: /reload
# Then: /config-sync
```

A normal `python3 ~/agents-config/config/pi/install.py` now applies both runtime configuration and named model providers. `--check` is read-only, offline, and checks runtime configuration only: exit **0** means the declared files/settings/package versions match, **1** means differences, and **2** means the check could not complete. It never installs packages or calls a model. It compares against this machine's local checkout; pull first to compare against published changes. No background scheduler or automatic cross-machine push is installed.

### What is managed

- **Settings:** keys declared under `settings` are authoritative, with nested objects merged by leaf. Other settings, including existing default model/provider choices, remain local. Removed formerly managed leaves are removed only if still equal to the last applied value; locally modified values remain local.
- **Resource arrays:** `packages`, `extensions`, `skills`, `prompts` and `themes` are authoritative arrays. Apply replaces those lists (with a private timestamped backup), so add experiments you want to keep to the manifest or a host override before applying. Removing a package declaration stops loading it; its cached installation remains on disk.
- **Shared extension code:** keep it under `config/pi/extensions/`, list its `${CONFIG_DIR}` path in `settings.extensions`, and add the relative filename to `trackedFiles`. Paths expand separately on each machine. The receipt hashes these files, so edits require a new apply even when paths stay the same.
- **Packages:** use `npm:@scope/name@1.2.3`, `git:github.com/owner/repo@<full-40-character-commit>`, or `${CONFIG_DIR}/your-local-package`. npm ranges and moving Git branches are rejected. Missing or wrong versions are installed using the selected `pi` executable, in an empty working directory, under the selected profile. Git packages with local edits are preserved and reported instead of overwritten. Local package dependencies remain your responsibility, as in Pi itself.
- **External extensions:** Herdr's `herdr-agent-state.ts` remains owned by Herdr. Its presence is reported when found; it is not copied, version-checked or installed here. Other auto-discovered extension entries are reported as local-only drift until moved into the shared setup or explicitly listed in `externalExtensions`.

The shared manifest adds the read-only `/config-sync` command, enables skill commands, and declares the [Claude subscription account provider package](claude-accounts/README.md). The main installer prepares that package's pinned dependency and local account launchers before applying runtime settings; each host needs its own authorized Claude logins. Use `/model` to select `personal-claude-code`, `vals-claude-code`, or `stanford-claude-code`. Read the package's acceptance table: Vals/Stanford worked in live checks; personal needs reauthentication after a revoked-token response. Checks validate declared resource paths, tracked source content and npm versions/Git commits; they do not prove model access, arbitrary npm file integrity, running-session reload, or project-level `.pi` overrides. Shared instructions still load through the existing agents-config entry points.

### Intentional machine/profile differences

Supply a non-secret override file with `--host-config /path/to/host.json` or set `PI_SYNC_HOST_CONFIG` to that path. It recursively overrides the shared manifest; arrays replace rather than concatenate. Use the same override for apply and check; setting the environment variable also makes `/config-sync` use it. `${HOME}`, `${CONFIG_DIR}` and `${AGENT_DIR}` expand on the destination machine.

For example, a host can retain a different theme while sharing everything else:

```json
{"settings": {"theme": "dark"}}
```

`pi-local` and `pi-gemini` use separate agent directories and launch flags that disable automatic extension loading. This installer does not rewrite those wrappers. An explicit `--agent-dir` can synchronize their files, but their launch flags still determine which resources load; use ordinary `pi` for the shared extension set.

### Changing configuration and recovering

Edit `runtime.json` and any tracked extension source, run the tests, commit/push, then pull/apply on each machine. A one-off `pi install` or `pi config` edit is local until promoted to the manifest; `--check` identifies a changed resource list or managed setting. Unmanaged scalar settings are listed as local information, not treated as failures.

Apply makes `settings.json.before-sync-*` backups only when content changes and writes settings/receipts atomically. Restore the needed backup to undo a settings change, and restore the corresponding manifest revision before applying again. Failed package installation exits nonzero without advancing the success receipt; correct the failure and rerun. Existing sessions are never interrupted by the installer.

### Verified rollout — 10-23-2026

The ordinary Pi profile reports IN SYNC on this Mac and skampere1, skampere2, skampere3, mercury1 and mercury2. All 20 installer tests pass on the Mac; the 13 runtime tests also pass on each Mercury host with its older Python. A disposable Mac Pi session loaded and executed `/config-sync` without model generation. Existing user sessions were not restarted; their loaded state and other machines remain unverified. The remote checkout retained its pre-existing unrelated changes.

Human-readable companion: [existing Pi and Herdr guide](https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4).

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

The installer follows the selected Pi executable to find its catalog before consulting npm's global root. For an unusual wrapper, supply `--catalog-dir /absolute/path/to/pi-ai/dist/providers/data`. On this Mac the installed catalog directory is `/Users/brandomiranda/.local/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/providers/data`.

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

## Devin Desktop: use the same named providers

Devin Desktop's **Pi ACP** agent runs `pi-acp`, which launches `pi --mode rpc`. It can expose the same providers; Devin Local and the standalone Devin CLI use Devin's own model catalog instead. This is not a bulk key import into Devin Local.

```bash
python3 ~/agents-config/config/pi/install.py --devin-desktop
```

On macOS this backs up and merges `~/Library/Application Support/Devin/User/settings.json`. The supported `devin.acp.agentEnv` map pins `pi-acp` to the selected Pi executable through `PI_ACP_PI_COMMAND` and the installed provider directory through `PI_CODING_AGENT_DIR`. Only non-secret paths are stored, and the preferred/default agent is unchanged. `PI_OFFLINE=1` disables startup catalog/network activity, not model inference.

For an existing stale connection, run **Devin: Reload ACP Connections** in the Command Palette. This reconnects agents, so wait until other active turns finish. Then start a **Pi ACP** conversation and use the model dropdown. New connections read the named providers; an existing session's cached list may require a new conversation. In this adapter `/model` itself is not implemented: the desktop dropdown is the supported selector.

`verify_devin_acp.py --adapter /path/to/pi-acp/dist/index.js` performs initialization, creates a disposable session, verifies all manifest providers are advertised, and selects `personal-openai-brando/gpt-5.6-sol` through `session/set_config_option`. It sends **no `session/prompt`** and does not generate tokens. Verification on 10-23-2026 with pi-acp 0.0.34 advertised 42 + 42 + 17 + 2 + 37 = 140 named model routes and accepted selection. This verifies the agent-to-client protocol, not the already-open desktop menu or successful paid inference.

Sources: [Devin Desktop ACP](https://docs.devin.ai/desktop/acp.md), [custom agents and reload](https://docs.devin.ai/desktop/acp-custom.md), [pi-acp](https://github.com/svkozak/pi-acp).

## Verification and recovery

```bash
python3 -m unittest discover -s ~/agents-config/config/pi -p 'test_*.py' -v
pi --offline --no-extensions --no-mcp --list-models personal-openai-brando
pi --offline --no-extensions --no-mcp --list-models allen-google-veribench
```

Do not share the generated local file if it contains other providers' secrets. The manifest, installer, tests and this guide are safe to version; credentials, runtime auth and sessions are not. Re-running the installer updates manifest-owned aliases from the installed catalog and preserves others. Missing keys are skipped with a notice; removing an old route explicitly from local `models.json` is separate. To undo, restore the local `models.json.before-named-*` backup, or remove only the manifest-owned provider IDs if this was the initial install.

Official references: [Pi repository](https://github.com/earendil-works/pi), the installed package's `docs/models.md`, `docs/models-configuration.md`, and `docs/providers.md`; public catalog: <https://pi.dev/models>.
