# Valkyrie documentation and diagnosis

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/valkyrie.md>

**TLDR:** Hosted Valkyrie now uses a Vals login, organization secrets and server-side provider/service settings. Follow the cloud migration below instead of restoring a legacy AWS/YAML setup; verify each execution host and preserve prior results and scientific settings.

Public references checked 10-14-2026. Read this when setting up, diagnosing or using Vals Valkyrie, its benchmark services or its model gateway. Apply [broad investigation](broad-investigation.md); do not ask the user for facts available in these sources.

## Hosted-cloud migration (10-14-2026)

**Use the new hosted setup for new work.** [Hosting modes](https://docs.valkyrie.vals.ai/get-started/hosting) separates Vals-operated infrastructure from self-hosted and local deployments. Hosted users no longer bootstrap their own Amazon Web Services (AWS) account. Preserve old artifacts: changing the client or signing in does not transfer historical runs from a previous deployment. Do not rerun completed scientific cells merely to populate the new service.

The current [quickstart](https://docs.valkyrie.vals.ai/get-started/quickstart), [login reference](https://docs.valkyrie.vals.ai/reference/cli/login) and [provider guide](https://docs.valkyrie.vals.ai/get-started/sandbox-providers) specify:

```bash
uv tool install git+https://github.com/vals-ai/Valkyrie@prod
valkyrie login
valkyrie whoami
valkyrie secret set daytona < daytona.json
valkyrie provider set daytona daytona
valkyrie provider default daytona
valkyrie provider list
```

For an existing uv installation, use its supported upgrade operation (`uv tool upgrade valkyrie`) and confirm the resolved source revision and help expose `login`, `secret` and `provider`; an already-installed message is not an update. Coordinate changes to a shared runtime with its active users. The `@prod` Git branch selects package code, **not** the Tracker environment. Confirm the intended organization with `whoami` and select an existing one with `valkyrie org use NAME` when necessary; do not create a replacement organization just because a previous login is absent.

Keep `daytona.json` in private storage with restrictive permissions. The documented schema contains `DAYTONA_API_KEY`, `DAYTONA_API_URL` and `DAYTONA_TARGET`; use the approved account's values. A provider mapping belongs to the organization, while its default is per user within that organization. Confirm existing mappings before changing a shared one. Store agent secrets with `valkyrie secret set <KEY_NAME>` under the names the agent's `contract.yaml` references. The hosted Tracker accepts only letters, digits and `_+=.@-` in a secret name, so a reference containing `/` from an older deployment needs a new name, mapped either in an updated contract or with `-s ENV_VAR NAME` at run start (a run-time mapping overrides the contract). Keep the previous client runnable separately while its old access still works, so historical runs and artifacts stay readable. Verify model credential ownership and payer separately from the sandbox provider: a successful login or Daytona mapping does not establish Vals-funded model access.

### Replace local configuration assumptions

The current [configuration guide](https://docs.valkyrie.vals.ai/get-started/configuration) saves browser sessions under `~/.config/valkyrie/sessions`. It selects the Tracker with `VALKYRIE_URL` and supports `VALKYRIE_API_KEY` access keys for noninteractive jobs; inspect whether an old key overrides the intended login without printing it. Use `valkyrie login --no-browser` for the supported remote sign-in flow. Do not copy live refresh credentials between hosts as an upgrade shortcut.

Legacy `valkyrie config init`, `valkyrie.yaml`, `VALKYRIE_CONFIG_PATH`, `VALKYRIE_ENV`, client-side AWS credentials and direct bucket/Secrets Manager checks are **not the current hosted setup**. Before reviving a launcher that depends on them, adapt its transport and identity checks together. Keep old pinned environments and frozen receipts identifiable as historical; do not treat their configuration as evidence the new tenant is ready.

[Custom benchmark services](https://docs.valkyrie.vals.ai/benchmarks/custom-services) now register with `valkyrie benchmark service set <name> <url>`, with an organization secret named by `--auth-secret` where required. A private YAML entry for `custom_benchmark_services` or `benchmark_auth` does not register the endpoint on the current service. These saved endpoints apply across machines for that user and organization: preserve concurrent consumers and use distinct benchmark names for distinct services. Saved endpoints and the default provider belong to a signed-in user: an access key follows the settings of the user who created it, an organization-level key from an older deployment has none, and the Tracker replaces any service address a client sends with the saved one. Keep a signed-in session (`valkyrie login --no-browser` works on headless hosts) where services are deployed, since a key can start runs but cannot save or update an endpoint. Check the current [benchmark authentication guide](https://docs.valkyrie.vals.ai/benchmarks/authentication) before upgrading a service that implements older static bearer authentication.

Before admitting work, verify host/client revision, Tracker, organization, provider mapping/default, contract secrets, agent bundle access, benchmark reachability/authentication and model payer. Record non-secret evidence in the private project checkpoint. Transport migration preserves model/effort, prompts, rubric, task manifest, budget, completed cells and existing run holds. A migration announcement alone does not resolve an earlier authorization failure or authorize resumed experiments.

## One large paid experiment at a time

Before starting, resuming or retrying a run, follow [Trigger Rule 72](../rules/services.md#trigger-rule-72): the shared `valk` wrappers refuse a large launch while another experiment has unfinished work, and only Brando approves running two at once.

## Official sources by task

| Task | Public source |
|---|---|
| Understand the platform and its components | [How Valkyrie works](https://docs.valkyrie.vals.ai/get-started/overview) |
| Find documentation pages or recover a failed page read | [Documentation index](https://docs.valkyrie.vals.ai/llms.txt); the same documentation paths also serve a `.md` representation |
| Install and select configuration | [Quickstart](https://docs.valkyrie.vals.ai/get-started/quickstart), [configuration](https://docs.valkyrie.vals.ai/get-started/configuration), [hosting modes](https://docs.valkyrie.vals.ai/get-started/hosting) |
| Sign in and configure sandbox credentials | [Login](https://docs.valkyrie.vals.ai/reference/cli/login), [sandbox providers](https://docs.valkyrie.vals.ai/get-started/sandbox-providers) |
| Discover agent packaging and management | [Manage agents](https://docs.valkyrie.vals.ai/agents/manage-agents) |
| Inspect or monitor runs | [Monitor runs](https://docs.valkyrie.vals.ai/runs/monitor) |
| Wrap an existing dataset and grader | [Convert a benchmark into a service](https://docs.valkyrie.vals.ai/benchmarks/convert-a-benchmark) |
| Connect an existing benchmark endpoint | [Custom benchmark services](https://docs.valkyrie.vals.ai/benchmarks/custom-services) |
| Work on the platform itself | [Local development](https://docs.valkyrie.vals.ai/contributing/local-development) and [Valkyrie source](https://github.com/vals-ai/Valkyrie) |
| Inspect model selection, provider adapters and supported parameters | [Vals model-library](https://github.com/vals-ai/model-library) and [model configuration](https://github.com/vals-ai/model-library/blob/main/model_library/config/README.md) |
| Understand gateway transport and metadata discovery | [Model gateway guide](https://github.com/vals-ai/model-library/blob/main/docs/gateway.md) |

Valkyrie coordinates agents and task sandboxes; benchmark-specific task preparation and grading belong to a benchmark service. The conversion guide explains how to expose an existing benchmark through that service. Local tracker development is a different workflow from using an already hosted account; select the relevant guide before changing configuration.

## Diagnose each layer independently

**Use installed help for command syntax and the intended host's state for access claims.** Begin with `valk --help`, `valk run --help` or `valk agent --help`, then the relevant command's help. Discover a supported equivalent when the user's requested alias does not exist. Check noninteractive output options before scripting a listing.

For current hosted clients, inspect `VALKYRIE_URL`, whether `VALKYRIE_API_KEY` is set, and the selected login using `valkyrie whoami`, without printing secret values. Resolve private paths on the actual host instead of copying another machine's username. For a deliberately retained legacy client, inspect its own documented configuration selection separately. A Git installation branch, a Tracker address and a model gateway address are separate settings.

Check command-line interface (CLI) imports, Tracker authentication, agent access, sandbox configuration, benchmark-service reachability and gateway metadata separately. An empty listing in a new organization does not prove historical runs were deleted. Missing benchmark registration does not establish an authentication failure.

On Macs and Stanford Network Analysis Project (SNAP) hosts, record the actual interpreter, package source and selected absolute paths. A shared installation or credential file does not prove every machine has compatible libraries, network access or permissions. Resolve host-specific dependency failures in an isolated compatible runtime and verify on each target. Follow the relevant [Mac](../machine/mac.md) or [SNAP](../machine/snap.md) instructions for access and installation ownership.

## Reuse a verified configuration hub

Follow [verified-host bootstrap](verified-host-bootstrap.md) for reusable package pins and compatible host setup. Check a private packet's date and configuration format before applying it: a pre-migration YAML/AWS packet is not a current hosted login. Authenticate and verify each destination using the supported flow above. Keep private hub addresses, account settings and receipts outside agents-config.

## Model, agent and benchmark access are separate

**Model access does not grant access to every agent.** Inspect the authenticated gateway catalog for model routes, `valk agent list` for accessible agent bundles, and the selected bundle's contract for model/effort compatibility. A model can be available while an agent archive is absent or inaccessible, or its wrapper lacks the required model interface. Reuse a permitted compatible agent or package an authorized implementation; do not promise arbitrary agent access from gateway access alone. Record the exact agent bundle/version alongside the model and effort in each experiment.

Research/public and proprietary benchmark variants may reuse the same agent while supplying different datasets through separately versioned benchmark services. An authorized locally hosted service is a supported integration route; publishing tasks upstream is not a prerequisite. Keep public and private task manifests, references and results distinct, and never upload proprietary data merely to make a benchmark discoverable. Verify each variant's actual task count instead of assuming a remembered approximate count.

## Verify model routing and effort

**A public registry and an authenticated deployed catalog can differ.** Inspect the official library, the deployed gateway's documented read-only model/registry endpoints, and the actual uploaded agent contract. Record exact model selector, resolved provider model, effort parameter, fallback behavior and relevant versions in the private experiment record.

The library distinguishes `reasoning_effort` from `compute_effort`; provider adapters can consume different fields. An agent may override a registry alias with its own default or fail to expose the required field. Trace the supplied launch argument through the wrapper into the library before claiming the requested effort is honored. Check tool support and the underlying provider interface when relevant.

Fallback aliases may select a different model after a failure. Preserve the authorized scientific model and settings; select a documented no-fallback route or a separately versioned wrapper change when required. Never silently substitute models or modify a frozen experiment to make transport work.

Treat catalog visibility as metadata access, not successful inference or proof of the model payer. Read-only discovery may proceed within existing authorization. Actual model calls follow the project's explicit funding, budget and execution rules; do not automatically run upstream quickstarts, validators or integration tests that make model calls.

## What belongs in this public repository

**Store transferable procedures here and account-specific material in the private host store.** Public documentation and repository links, documented configuration field names, generic path conventions and troubleshooting methods belong here.

Do not add raw credentials, private bootstrap packets or their credential appendices, private endpoint addresses, account or resource identifiers, assigned cloud secret names, internal-only model aliases or authenticated private catalog dumps. A private network does not make a Git repository private. Inspect the exact staged content before publishing; access for diagnosis is not permission to publish it.

Use an authorized private handoff for the actual host configuration and any credential-bearing setup packet. Do not copy that packet into agents-config or ask the user to paste its contents into chat. Record only a sanitized outcome here; keep per-host evidence and the precise private routing in their authorized location.
