# Valkyrie documentation and diagnosis

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/valkyrie.md>

**TLDR:** Use the official Valkyrie documentation and Vals model-library source to discover supported commands, benchmark integration and model routing. Verify the configured host and service separately, while keeping all account-specific information outside this public repository.

Public references checked 09-24-2026. Read this when setting up, diagnosing or using Vals Valkyrie, its benchmark services or its model gateway. Apply [broad investigation](broad-investigation.md); do not ask the user for facts available in these sources.

## Official sources by task

| Task | Public source |
|---|---|
| Understand the platform and its components | [How Valkyrie works](https://docs.valkyrie.vals.ai/get-started/overview) |
| Find documentation pages or recover a failed page read | [Documentation index](https://docs.valkyrie.vals.ai/llms.txt); the same documentation paths also serve a `.md` representation |
| Install and select configuration | [Configuration](https://docs.valkyrie.vals.ai/get-started/configuration) |
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

The conventional configuration path is `~/.config/valkyrie/valkyrie.yaml`. Resolve it on the actual host instead of copying another machine's username:

```bash
python3 -c 'from pathlib import Path; print((Path.home() / ".config/valkyrie/valkyrie.yaml").resolve())'
```

Inspect `VALKYRIE_CONFIG_PATH`, `VALKYRIE_ENV`, `VALKYRIE_API_KEY` and `TRACKER_SERVICE_URL` selection without printing secret values. A Git installation branch, a saved tracker environment and a gateway address are separate settings. Preserve working credentials and configuration; use the supported setup flow for a recoverable initialization error.

Check command-line interface (CLI) imports, tracker authentication, agent storage, sandbox configuration, benchmark-service reachability and gateway metadata separately. A run listing does not establish bucket access; an empty listing does not prove historical runs were deleted. Missing benchmark registration does not establish an authentication failure.

On Macs and Stanford Network Analysis Project (SNAP) hosts, record the actual interpreter, package source and selected absolute paths. A shared installation or credential file does not prove every machine has compatible libraries, network access or permissions. Resolve host-specific dependency failures in an isolated compatible runtime and verify on each target. Follow the relevant [Mac](../machine/mac.md) or [SNAP](../machine/snap.md) instructions for access and installation ownership.

## Reuse a verified configuration hub

Follow [verified-host bootstrap](verified-host-bootstrap.md) when another authorized machine already has working Valkyrie. Prefer the private SNAP distribution store and retain a verified laptop replica. Read the private manifest and compare the actual source configuration with the packet appendix before executing an installer that can replace destination settings. Reuse approved account configuration and package pins; create a native host-local runtime and record that host's checks. Private hub addresses, account settings and receipts stay outside agents-config.

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
