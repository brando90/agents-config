# Pi: fresh local coding verification — 10-22-2026

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/pi-fresh-verification-10-22-2026.md>

**Google Doc:** <https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4/edit>

**TLDR:** Both local Pi routes passed fresh disposable coding tests. Allen's Gemini route was configured and tested earlier, but the newly requested Gemini checks were left pending on 10-22-2026 under the then-current confirmation wording (since relaxed by Hard Rule 9).

| Route | Verified provider/model | Pi elapsed | Independent checks | Completion |
| --- | --- | --- | --- | --- |
| Mac `pi-local` | `ollama-local/qwen3.5:9b-q4_K_M` | 37.747 s | 1/6 before → 6/6 after | Exit 0 |
| skampere3 `pi` | `snap-coder/qwen3-coder-30b`, existing service on skampere1 | 127.978 s | 1/6 before → 6/6 after | Exit 0 |
| Mac `pi-gemini`, Allen's key | configured `google/gemini-3-flash-preview` | Not rerun | Fresh tests pending confirmation | No new request sent |

Each local run used its own disposable Python project with a broken arithmetic-mean function. Tests covered positive values, a singleton, negative values, zeros, a fractional result and rejection of empty input. Pi read and edited the source and ran tests; the coordinator independently reran all six afterward and verified the test file's SHA-256 hash was unchanged. Native Pi message records confirmed the provider and model shown above. Both finished inside the 180-second bound. These are single setup checks, not a benchmark or a speed comparison under controlled load. Existing interactive sessions were preserved.

The Gemini disclosure named `~/.local/bin/pi-gemini`, which loads `~/keys/gemini_allen_key.txt`. Proposed tests: one exact reply and one short function repair with six independent checks, estimated below $0.01 total. The [official pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3-flash-preview) lists $0.50 per million input tokens and $3 per million output tokens on the paid tier; actual billing tier was not verified. At the time, the older Hard Rule 9 wording required explicit confirmation after disclosure; since 10-23-2026 Hard Rule 9 allows in-scope provider-key use (VeriBench only for this key) without asking, within existing budgets. Do not mistake the earlier 1.578-second PONG check for a new test. No other provider keys were tested or copied.

## Previously open Herdr session

The skampere3 pane still had `snap-qwen/pi-qwen3.6-27b` selected. Exited the idle Pi process, refreshed that shell's PATH with `/dfs/scratch0/brando9/bin` and `~/.local/bin`, and cleared Bash's command cache. `pi --version` returned 1.4.0 and `pi --check-local` passed. Resumed saved session `01a166e4-13f1-75c0-8c71-ee3a7d876e29` with `--provider snap-coder --model qwen3-coder-30b --thinking off`; its live reply was `PI_READY`. No Herdr server restart or other-pane change was needed. Saved histories still contain old error messages; use the current model footer and a fresh response to judge the current state.

Local receipts and native logs are under `~/.local/share/pi-local-setup/10-22-2026/fresh-pi-checks/`; the remote coding workspace is `/tmp/user/22003/pi-snap-local-smfazslz`, with receipts under `~/.local/share/pi-fresh-checks-10-22-2026/` on skampere3. The earlier live-pane repair receipt is `herdr-skampere3-live-restart.json` in the parent local receipt directory. Temporary project paths are evidence locations, not permanent install targets.
