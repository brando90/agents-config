# Implementation prompt: Pi agent for the Valkyrie public registry

**Doc link:** <https://github.com/brando90/agents-config/blob/main/docs/pi/registry-issue-15-implementation-prompt.md>

**TLDR:** Implement the Pi coding-agent integration requested in vals-ai/public-agent-registry issue #15, including a reproducible agent repository, the registry submodule contribution, verified model-gateway routing, non-interactive execution and useful output artifacts. Keep the baseline independent of any developer's personal configuration. Demonstrate installation, protocol handling and failure behavior with deterministic tests, then report the result of one explicitly authorized bounded Valkyrie task separately from those tests.

## Copy-ready implementation prompt

Please implement <https://github.com/vals-ai/public-agent-registry/issues/15>: add the Pi coding agent (`@earendil-works/pi-coding-agent`, upstream <https://github.com/earendil-works/pi>) as a reusable Valkyrie agent so we can compare its harness with Terminus 2 using the same underlying models, including on VeriBench.

### Start with the actual contribution contract

Read the target checkout's instructions, `README.md`, `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE/add-agent.md`, and the `examples/claude_code-v1.0.0` and `examples/codex-v1.0.0` contracts, setup scripts and collectors. Record the revisions used. Inspect existing related pull requests before creating duplicate work.

The registry currently requires community agents under `agents/` to be Git submodules. Create or use an authorized agent source repository containing `contract.yaml`, `setup.sh`, a run/output wrapper, tests and `README.md`; propose a stable versioned registry path such as `agents/pi-v1.0.0`. Pin the submodule to the tested source commit and update `.gitmodules`. An example directory alone does not satisfy the current contribution policy. Keep upstream Pi itself distinct from the small repository implementing the Valkyrie contract.

The checked examples use `install_cmd`, `run_cmd`, `final_output: /logs`, typed model defaults, and substitutions including `{problem_statement_path}`, `{task_id}` and `{model}`. Validate the actual supported schema and substitutions rather than assuming arbitrary environment variables or template fields exist. The linked `vals-ai/Valkyrie` dev-branch `docs/CONTRACTS.md` returned HTTP 404 during preparation on 10-24-2026; resolve the current authorized documentation or schema before claiming contract validation. Do not copy the old examples' branch-specific installation URLs or model defaults without checking them.

### Make installation reproducible

Pin a published Pi package version and a compatible Node.js version after checking that release's requirements. Document the chosen versions and install into paths available to the benchmark runner. Make setup non-interactive and safe to rerun. Preserve the task workspace, install declared dependencies, and verify the actual `pi` executable/version. Avoid an unpinned `latest` install.

Use an isolated per-run Pi agent directory through `PI_CODING_AGENT_DIR`. Configure only the credentials and model routes supplied by the benchmark runtime. A developer's home directory, personal agents-config repository, login sessions, browser profiles and local model server must not be necessary to run the registry agent.

### Wire model and provider selection through the real Valkyrie gateway

First determine the gateway's actual supported protocol, endpoint construction, authentication/environment contract and model identifiers using current authorized documentation and a bounded protocol test. The public Claude/Codex examples document direct provider-key environment names; they do not establish Pi gateway compatibility. Do not invent a gateway URL or environment name and describe it as verified.

Expose the model and provider selection through supported contract inputs. Distinguish the requested upstream model, the Pi routing-provider identifier, and the gateway endpoint. Preserve model identifiers losslessly unless a documented mapping requires a transformation; record the mapping. Reject an unsupported combination with a useful error rather than silently switching models or billing routes.

Use Pi's supported custom provider configuration in `models.json` or an extension if the gateway requires one. Verify the chosen Pi API adapter's actual wire behavior: an OpenAI-compatible label does not by itself establish compatibility with Responses, Chat Completions or another protocol. Set only documented model capabilities/context/output limits, and distinguish gateway-reported usage/pricing from local estimates.

Load secrets from the runtime's supplied environment/secret mechanism. Keep literal tokens out of committed configuration, command arguments, logs and example artifacts. Do not copy credentials from a developer's workstation. If gateway work cannot be completed, document the exact unresolved interface and distinguish a working direct-provider experiment from the still-unverified gateway requirement.

### Run Pi as the agent, not a single model call

Use the installed version's supported non-interactive interface; a starting point to verify is `pi --print --mode json` with explicit provider/model and the task prompt supplied through stdin. Use an argument list for subprocess invocation and read the problem statement file as UTF-8; do not interpolate task text into a shell command.

Run from the benchmark-provided workspace and permit the normal Pi coding tools to read, edit and execute there according to the runner's permissions. Verify that a disposable task actually causes tool execution and a file change, rather than merely returning prose. Preserve the benchmark's instruction policy and task context. Document exactly which project context files are loaded and avoid importing unrelated ancestor/home instructions.

Make optional skills, extensions, prompt templates, connector configuration and packages explicit and versioned if supported. A minimal reproducible baseline is sufficient for this issue; reproducing somebody's personal plugin installation is not required. Report enabled resources and settings for each run, and keep an optional customized harness distinguishable from the baseline. A skill's presence does not prove its required tools or host applications are available.

Honor runner timeouts and cancellation, terminate the owned child process group, and propagate failures. Configure bounded retries and resource limits through interfaces the selected Pi version actually supports; do not invent flags. Avoid interactive approval/login prompts in unattended runs. Record the actual provider/model, thinking setting where supported, tool/resource configuration, Pi version and wrapper revision.

### Collect Pi-specific artifacts accurately

Match the repository's output conventions with `summary.json`, `metrics_total.json`, `final_message.txt`, `trajectory.jsonl` and `raw_output.txt` under the declared output directory. Keep stdout JSON events parseable and capture stderr without treating arbitrary stderr text as trajectory events. Preserve useful diagnostics for partial output, cancellation and process failures, with credential redaction.

Parse Pi's actual event types rather than reusing the Claude collector unchanged. In the inspected Pi documentation, completed assistant messages arrive in `message_end.message`, partial updates can carry cumulative usage, and `agent_end` is a low-level run boundary that can be followed by recovery/retry. Verify final-settlement behavior for the pinned release. Select final assistant text, not the most recent user prompt, tool result or thinking block.

Aggregate usage once per completed assistant response; do not sum repeated cumulative streaming snapshots or double-count messages repeated in later events. Distinguish provider-reported cost from estimated cost; unavailable usage/cost remains null or explicitly unavailable. Capture elapsed wall time and the subprocess return code. A process exit code or nonempty final message alone is not proof of benchmark success: distinguish execution completion, harness failure, and benchmark scoring.

Write summary/failure artifacts even when execution fails, the stream truncates, or a timeout occurs. Preserve a nonzero failure status through the wrapper and contract. Supply synthetic, non-sensitive example artifacts.

### Verification and pull-request delivery

Add deterministic tests for command construction and prompt quoting; paths containing spaces; model/provider/gateway mapping; missing credentials/configuration; tool-use event streams; final-text extraction; usage aggregation; malformed/non-JSON lines; empty output; terminal provider errors; retries; timeout/cancellation; and nonzero child exits. Test the selected protocol using a local mock server so endpoint, headers, model ID and tool-call payloads are inspectable without real credentials.

Test fresh installation and rerunning setup in a representative Linux container. Then, within explicitly authorized credentials and a stated small budget, install through Valkyrie and run one task at concurrency 1 using a publicly available or authorized task. Verify workspace execution and artifact collection. A registry-wide benchmark or private dataset publication is outside this initial integration test. Record the exact commands, tested revisions, selected model/provider, observed result and any untested route. Never describe a mock or a catalog lookup as a successful gateway run.

Open the implementation pull request in the agent source repository as appropriate and the registry pull request pointing to the tested source commit. Follow the registry's add-agent template, reference issue #15, include supported models/protocols, required secret names only, installation/run instructions, evidence and known limitations. Keep incomplete gateway or live-run verification visible. Do not merge or close the issue unless the repository workflow and maintainer authorization support it.

**TL;DR:** Produce a reproducible Pi agent repository and registry submodule contribution with verified Valkyrie model routing, real non-interactive coding execution, accurate artifacts and deterministic tests. Report live one-task validation separately, preserving model identity and keeping personal configuration and credentials out of the public integration.

## Preparation sources

- [Issue #15](https://github.com/vals-ai/public-agent-registry/issues/15)
- [Contribution requirements](https://github.com/vals-ai/public-agent-registry/blob/main/CONTRIBUTING.md)
- [Claude example](https://github.com/vals-ai/public-agent-registry/tree/main/examples/claude_code-v1.0.0)
- [Codex example](https://github.com/vals-ai/public-agent-registry/tree/main/examples/codex-v1.0.0)
- [Add-agent pull request template](https://github.com/vals-ai/public-agent-registry/blob/main/.github/PULL_REQUEST_TEMPLATE/add-agent.md)
- Pi's installed 1.4.0 documentation: `docs/cli.md`, `docs/json.md`, `docs/models-configuration.md`, `docs/skills.md`; recheck against the version chosen for implementation.
