# Pi: shared configuration and named providers

**Doc link:** <https://github.com/brando90/agents-config/blob/main/config/pi/README.md>

**TLDR:** Automatic sync captures portable ordinary-Pi settings and canonical skill/resource edits through a private hub, checks for conflicting edits, and applies updates in the background. `install.py --check` and Pi’s `/config-sync` report drift; the full installer also configures named providers, keeping credentials outside Git.

## Automatic sync — 10-24-2026

`auto_sync.py` synchronizes the ordinary Pi profile every 60 seconds using native macOS LaunchAgent / Linux per-user cron jobs. The private hub is an owner-only directory on the existing shared cluster filesystem. Cluster clients use that directory directly; the Mac uses its existing authenticated Secure Shell (SSH) route to skampere1. Cluster synchronization can continue while the Mac sleeps; the Mac catches up after waking and reconnecting. Failed connections back off to at most one attempt every 30 minutes. No model calls or Codex scheduled-agent runs are used.

**What happens after an edit:** changes through an existing Codex/Claude skill symlink, or directly under `config/pi/skills` (a link to the repository's `skills/` folder) / `private-skills`, are detected and propagated. The same applies to `extensions`, `prompts` and `themes` beneath `config/pi`, portable keys in the ordinary Pi `settings.json`, and changes to `runtime.json`'s portable settings. Package declarations propagate; installed mutable npm references are normalized to their installed version. Missing pinned packages are installed. Authentication, `models.json`, sessions, machine identifiers, shell/proxy paths, vendor skills and dependency caches are excluded. New personal skills belong in the canonical skill directories; unrelated new copies elsewhere are not silently adopted. Arbitrary local package source directories are not copied by this service; distribute their source through Git or a package manager.

**Conflict behavior:** the hub compares each item with that client's last accepted version. Non-overlapping edits merge; two differing edits to the same file or top-level setting stop that client with a `conflict` status. Nothing is silently chosen by timestamp. File deletions propagate and replaced/deleted files have private backups. A settings edit racing with apply is preserved and retried. The service uses Pi's settings lock and a separate per-profile lock. Offline edits remain local until connectivity returns.

**Privacy and Git:** transport and history are private. There is no automatic Git commit, push, stash, reset or pull of the working checkout. This deliberately makes ordinary skill/setting synchronization independent of Git publication, so private text and newly entered values cannot accidentally be published to the public repository. Canonical source edits appear as normal working-tree changes; tested public changes can still be committed normally. Published installer/code changes require the normal software update workflow. Remote settings are stored in the private profile file `agents-config-auto-settings.json`, applied before intentional `agents-config-host.json` overrides. Enrollment removes only redundant host overrides identical to the shared manifest; actual differences stay local.

**Running sessions:** new Pi sessions load synchronized files. Existing sessions still need `/reload` for newly discovered skills/extensions and may retain their selected model/settings. The service never interrupts an active turn. Editing the contents of an already discovered skill changes the canonical file, but discovery is not evidence that its external applications or credentials are available.

Enrollment (once per new machine, ordinary profile):

```bash
# On the initial source only, add --seed. Other clients enroll from the hub.
python3 ~/agents-config/config/pi/install_auto_sync.py \
  --hub /path/to/private/shared/pi-sync-hub \
  --ssh-host existing-host-alias \
  --remote-script /path/to/agents-config/config/pi/auto_sync.py
# On a cluster node with direct access to the hub, omit --ssh-host/--remote-script.
```

The installer refuses to discard an existing baseline on reinstallation. Linux installs one marked `agents-config-pi-auto-sync` line in the existing per-user crontab, preserving all other jobs; it runs across logout and reboot. macOS uses `com.brando.pi-config-sync`, starting at user login and restarting after failure. Sleep/network outages cannot provide instantaneous delivery. These services target the enrolled ordinary profile; specialized `pi-local`, `pi-gemini`, project overrides, other laptops and un-enrolled machines remain separate.

Status and recovery:

```bash
python3 ~/agents-config/config/pi/auto_sync.py status
python3 ~/agents-config/config/pi/install.py --check
# Optional immediate sync; normally the background service does this:
python3 ~/agents-config/config/pi/auto_sync.py once
# For a reported conflict, choose only after reviewing both versions:
python3 ~/agents-config/config/pi/auto_sync.py resolve --prefer local
# Or: resolve --prefer remote
```

`/config-sync` includes automatic-sync status. Status reports the last checked time, hub revision, change count and errors/conflict paths without file or setting contents; an otherwise successful receipt older than three minutes is reported stale. Local state/backups live in `~/.pi/agent/auto-sync/`; hub history is private too. A conflict resolution only selects the listed conflicting items; unrelated hub changes still merge. Pause/resume with `launchctl bootout/bootstrap` for the installed plist on macOS, or comment/uncomment only the marked `agents-config-pi-auto-sync` crontab line on Linux. Do not restore an old baseline to resolve a conflict; restore the desired source/settings and use the resolution command.

Verified installation and two-way scheduled propagation on all six machines: [10-24-2026 rollout receipt](auto-sync-rollout-10-24-2026.md).

## Manual installer and shared defaults

Brando's selected everyday default is **GPT-6.1 Sol, medium thinking, through the Koyejo Lab OpenAI key** (10-23-2026). Keep future ordinary-Pi preference decisions in this shared configuration, publish them to `main`, and apply/verify them on configured machines rather than stopping at a local settings edit. Explicit specialized profiles and host overrides remain intentional exceptions. Git publication alone does not update machines or running sessions.

The credential stays in each machine's private key store; only the named route and preferences are shared. On a machine without that provider, run the full installer with its existing authorized key before using the default. Owner scope and unattended-run budget caps still apply. New sessions load the default; resumed sessions retain their previous selection.

`runtime.json` supplies the portable baseline; enrolled profiles layer privately synchronized preferences over it. `sync_runtime.py` applies it to the selected Pi agent directory and stores a private receipt there. The default profile is `~/.pi/agent`; `--agent-dir` explicitly targets another profile. The installer does not copy authentication, sessions or credentials between machines, and the runtime-only path leaves model providers unchanged.

For machines without automatic sync, or for publishing installer/code updates, use:

```bash
git -C ~/agents-config pull --ff-only
python3 ~/agents-config/config/pi/install.py --runtime-only
python3 ~/agents-config/config/pi/install.py --check
# In an existing ordinary Pi session: /reload
# Then: /config-sync
```

A normal `python3 ~/agents-config/config/pi/install.py` now applies both runtime configuration and named model providers. `--check` is read-only, offline, and checks runtime configuration only: exit **0** means the declared files/settings/package versions match, **1** means differences, and **2** means the check could not complete. It never installs packages or calls a model. It compares against this machine's local checkout; pull first to compare against published changes. Automatic-sync enrollment and its private propagation layer are described above.

### What is managed

- **Settings:** keys declared under `settings` are authoritative, with nested objects merged by leaf. The shared ordinary-Pi default is `koyejolab-openai-bm/gpt-6.1-sol` with `medium` thinking, including its per-model thinking setting. Other undeclared settings remain local. Removed formerly managed leaves are removed only if still equal to the last applied value; locally modified values remain local.
- **Resource arrays:** `packages`, `extensions`, `skills`, `prompts` and `themes` are authoritative arrays. Apply replaces those lists (with a private timestamped backup), so add experiments you want to keep to the manifest or a host override before applying. Removing a package declaration stops loading it; its cached installation remains on disk.
- **Shared extension code:** keep it under `config/pi/extensions/`, list its `${CONFIG_DIR}` path in `settings.extensions`, and add the relative filename to `trackedFiles`. Paths expand separately on each machine. The receipt hashes these files, so edits require a new apply even when paths stay the same.
- **Packages:** use `npm:@scope/name@1.2.3`, `git:github.com/owner/repo@<full-40-character-commit>`, or `${CONFIG_DIR}/your-local-package`. npm ranges and moving Git branches are rejected. Missing or wrong versions are installed using the selected `pi` executable, in an empty working directory, under the selected profile. Git packages with local edits are preserved and reported instead of overwritten. Local package dependencies remain your responsibility, as in Pi itself.
- **External extensions:** Herdr's `herdr-agent-state.ts` remains owned by Herdr. Its presence is reported when found; it is not copied, version-checked or installed here. Other auto-discovered extension entries are reported as local-only drift until moved into the shared setup or explicitly listed in `externalExtensions`.

The shared manifest adds the read-only `/config-sync` command, enables skill commands, and declares the [Claude subscription account provider package](claude-accounts/README.md). The main installer prepares that package's pinned dependency and local account launchers before applying runtime settings; each host needs its own authorized Claude logins. Use `/model` to select `personal-claude-code`, `vals-claude-code`, or `stanford-claude-code`. Read the package's acceptance table: Vals/Stanford worked in live checks; personal needs reauthentication after a revoked-token response. Checks validate declared resource paths, tracked source content and npm versions/Git commits; they do not prove model access, arbitrary npm file integrity, running-session reload, or project-level `.pi` overrides. Shared instructions still load through the existing agents-config entry points.

### Intentional machine/profile differences

Supply a non-secret override file with `--host-config /path/to/host.json` or set `PI_SYNC_HOST_CONFIG` to that path. With neither specified, the installer and checker automatically use `agents-config-host.json` in the selected agent directory when present. It recursively overrides the shared manifest; arrays replace rather than concatenate. Use the same override for apply and check; setting the environment variable also makes `/config-sync` use it. `${HOME}`, `${CONFIG_DIR}` and `${AGENT_DIR}` expand on the destination machine.

For example, a host can retain a different theme while sharing everything else:

```json
{"settings": {"theme": "dark"}}
```

`pi-local` and `pi-gemini` use separate agent directories and launch flags that disable automatic extension loading. This installer does not rewrite those wrappers. An explicit `--agent-dir` can synchronize their files, but their launch flags still determine which resources load; use ordinary `pi` for the shared extension set.

### Changing configuration and recovering

On enrolled machines, edit canonical skills/resources or portable ordinary-Pi settings and let the service synchronize them. Use the manual workflow for code publication or un-enrolled profiles. `--check` identifies runtime drift; unsupported or intentionally host-local settings remain local.

Apply makes `settings.json.before-sync-*` backups only when content changes and writes settings/receipts atomically. Restore the needed backup to undo a settings change, and restore the corresponding manifest revision before applying again. Failed package installation exits nonzero without advancing the success receipt; correct the failure and rerun. Existing sessions are never interrupted by the installer.

### Verified rollout — 10-23-2026

**Sol-medium default update:** published to `main` and applied to ordinary Pi on this Mac plus skampere1, skampere2, skampere3, mercury1 and mercury2. All six runtime checks report IN SYNC; all five remote catalogs advertise `koyejolab-openai-bm/gpt-6.1-sol`. The 21 installer/runtime tests and instruction-document checks pass. Remote setup needs `--catalog-dir "$HOME/.local/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/providers/data"` because the shared Pi wrapper is not colocated with its catalog. Credentials remained in existing private stores; no inference was used to verify this rollout. Other Macs, Sherlock and FarmShare were not verified in this rollout. Existing sessions were not reloaded or switched. The Claude subscription extension is installed remotely but reports login required there; that is separate from the Koyejo OpenAI-key default.

The earlier extension-only rollout follows:

The ordinary Pi profile reports IN SYNC on this Mac and skampere1, skampere2, skampere3, mercury1 and mercury2. All 20 installer tests pass on the Mac; the 13 runtime tests also pass on each Mercury host with its older Python. A disposable Mac Pi session loaded and executed `/config-sync` without model generation. Existing user sessions were not restarted; their loaded state and other machines remain unverified. The remote checkout retained its pre-existing unrelated changes.

Human-readable companion: [existing Pi and Herdr guide](https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4).

## Shared skills migration — 10-24-2026

Every skill lives in the repository's `skills/` folder, reached here through the checked-in link `config/pi/skills` (so older links into `config/pi/skills/<name>` keep resolving). Four installed skills came from the old `config/pi/skills/`: `atlas`, `pi-local-herdr`, `sbsbz-cardinal-print-flyers`, and `sbsbz-financial-officer`. Their scripts, references, assets and applicable license files are included. Vendor/system/plugin-managed skill collections remain with their package managers; copying those instruction files does not reproduce their tools or authentication.

Personal skill content lives in the Git-ignored `config/pi/private-skills/` directory, with private directory permissions. It is included in Pi discovery and local drift hashing when present, but is not published or fetched through Git. The automatic service synchronizes that directory privately on enrolled machines. Without enrollment, transfer it separately over an authenticated private connection. The private content is intentionally absent from the public manifest and this guide.

For manual recovery on the current Mac → shared SNAP checkout, private skills can be copied with backups over Secure Shell (SSH), then applied/checked on each node. The five SNAP nodes share this source directory:

```bash
rsync -a --chmod=D700,F600 --backup --backup-dir="/dfs/scratch0/brando9/.local/state/agents-config/private-skill-backups/$(date +%m-%d-%Y-%H%M%S)" \
  "$HOME/agents-config/config/pi/private-skills/" \
  skampere1:/dfs/scratch0/brando9/agents-config/config/pi/private-skills/
```

The backup directory is on the destination. This copy does not delete remote-only files. Reconcile deletions or conflicting edits deliberately. Git pull and the local drift check cannot establish that a private copy on another machine is current.

The installer creates canonical links for these skills in `~/.codex/skills`, `~/.claude/skills` and `~/.agents/skills`. A first migration of an existing independent copy requires `--adopt-skill-copies`; it moves the old copy into the private `~/.local/state/agents-config/skill-backups/` directory before linking. Without that flag, conflicting copies are preserved and reported. Built-in/vendor directories and unrelated skills are untouched. Pi deduplicates links resolving to the same source file.

```bash
python3 ~/agents-config/config/pi/install.py --runtime-only --adopt-skill-copies
python3 ~/agents-config/config/pi/install.py --check
python3 ~/agents-config/config/pi/verify_skills.py
```

Subsequent ordinary syncs need no adoption flag. `trackedDirectories` hashes the entire public skill tree, including supporting scripts and assets; additions, edits and removals produce drift until applied. The checker also verifies client links. The no-generation verifier asks an isolated Pi session for its command inventory and confirms every canonical skill is advertised. Discovery does not establish that a host has the required Mac applications, printer, connectors or authentication. Existing running sessions need `/reload`; skill instructions are read when selected, not all injected at startup.

Implementation prompt for the separate Valkyrie integration request: [registry issue #15 prompt](../../docs/pi/registry-issue-15-implementation-prompt.md). The benchmark integration should remain independent of this personal skill collection.

## Policy (Brando's explicit replacement, 10-23-2026)

Agents may configure and use Brando-authorized provider credentials in Pi through its standard `models.json` providers and runtime secret commands. A shared model selector containing multiple sponsors is allowed; separate profiles are optional, not mandatory. Do not refuse this setup because it uses application programming interface (API) keys rather than subscriptions. This specific instruction supersedes older blanket CLI-only/key bans and mandatory profile isolation for Pi.

Name every route `<sponsor>-<service>-<key-nickname>` so `/model` identifies the model, actual provider and funding credential without displaying the secret.
**Persistent naming preference (Brando, 10-27-2026):** show the verified sponsor (for example, Koyejo Lab, Stanford or Vals), not just a generic `openai` or `anthropic` label; preserve this preference in the shared provider manifest and startup defaults.
Do not relabel a generic route as a sponsor without verifying its credential source, and do not invent a sponsor route without matching credentials.
The named provider ID and model display name both carry the sponsor; upstream model IDs remain unchanged. Keep key values out of Git, chat, logs and literal configuration. Use existing credentials, respect their owner's actual scope and existing budgets, and do not purchase credits or enable new charges. Cost-estimate and cap unattended runs; interactive selection and setup do not need repeated approval. Visibility is not authorization to use an owner's key outside its scope.

## Files and standard workflow

- `providers.json`: non-secret route manifest: sponsor, service, key filename, intended scope, optional model allowlist.
- `install.py`: generates named providers from the installed Pi catalog, preserving model pricing/protocol/context metadata. Merges named providers without changing auth or unrelated providers, then applies the shared runtime settings (including startup model defaults). It does not change a running session's model. Backs up an existing models file. Checks private key-file permissions without reading secrets.
- `test_install.py`: deterministic tests with fake keys and temporary catalogs.

```bash
python3 ~/agents-config/config/pi/install.py
# In bare pi:
# /model -> search personal-openai-brando (or another sponsor) -> Enter
# Ctrl+S saves a default; /scoped-models controls Ctrl+P cycling.
```

The installer follows the selected Pi executable to find its catalog before consulting npm's global root. For an unusual wrapper, supply `--catalog-dir /absolute/path/to/pi-ai/dist/providers/data`. On this Mac the installed catalog directory is `/Users/brandomiranda/.local/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/@earendil-works/pi-ai/dist/providers/data`.

Pi reloads `models.json` on `/model`. Restart or `/reload` if a running selector remains stale.
If only generic providers appear even though the runtime check passes, run the **full** `python3 ~/agents-config/config/pi/install.py`: `--runtime-only` and automatic sync intentionally do not install providers, and `--check` verifies runtime settings, not provider availability.
The installer discovers the selected catalog for both package symlinks and managed Pi launchers (`install/current-version`); it does not require a separate global npm installation.
Then choose `koyejolab-openai-bm/gpt-6.1-sol` in `/model` for the shared default; a resumed session retains its previous provider until explicitly switched. `pi-gemini` and `pi-local` intentionally use different agent directories; this installation targets **bare `pi`**, including new ordinary Herdr Pi sessions. It does not silently rewrite the scoped or local-only launchers.

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
