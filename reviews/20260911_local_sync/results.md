# Local catch-up rule and coordinator schedule

**TLDR-start:** [ac: local sync] The rule is merged, one 30-minute coordinator is enabled, and the initial editor synchronization passed. Only one active experiment 71 remains; all duplicate-folder bytes were preserved before relocation.

**Status:** DONE — setup verified; scheduled executions remain prospective
**Last updated:** 2026-09-11 15:29 PDT

| Phase | State | Evidence |
|---|---|---|
| Policy publication | DONE | PR 56 merged, commit1c242753230e00519b03132ffa7d45e53ffdbefb |
| Independent acceptance review | FIXED | Fresh Astra/ultra fallback after strongest-Claude quota failure;2 major + 1 minor findings reconciled; original FAIL retained |
| Deterministic checks | PASS | Eight Git, lock, timeout and collision checks; staged secret scan; whitespace check |
| Legacy preservation | DONE | VeriBench main 3a5eb0266;24,126 files recoverable,1,191 unique versions archived; full external local backup verified |
| Initial editor sync | DONE | 027f166b4→3a5eb0266;62,906 untracked/ignored files preserved; one active 71 |
| Schedule activation | VERIFIED | veribench-remote-progress-and-local-sync;ACTIVE;30 minutes;target 01a08dfa-efbd-71e3-b877-9245ab9c1127 |
| First scheduled execution | NOT YET OBSERVED | Initial check was manual; activation is not proof of a future execution |

The saved prompt matches the reviewed/fixed prompt line-for-line; the app removes only its final newline. `activation.json` records both hashes, exact schedule fields and verification time. `initial_sync.json` records the exclusive update window, immutable checked commit and preservation result. The original evaluation task was told the verified automation identifier and kept its separate schedule paused. The other manually paused schedule also remains paused.

Remote work remains separate from this setup completion: all 150 reference controls passed and native model attempts were 0 at observed state434; mandatory Claude reference acceptance and numbering acknowledgement remain pending. The read-only remote observer is alive. The separate recovery guard stopped on a PermissionError while inspecting an SSH server process; its blocked email was accepted. No automatic-recovery health is claimed. The master checkpoint and local state receipt retain that blocker.

The canonical local agents-config checkout has an unrelated change in `claude-code-settings.json`; it was preserved, origin/main fetched, and the owned policy checkout/current session refreshed from merged main. Do not mistake this for resetting or publishing that unrelated settings change.

**TLDR-end:** [ac: local sync] Folder cleanup, policy publication, manual catch-up and one enabled coordinator are verified. The schedule checks existing remote work and reports meaningful changes; research completion and the recovery-guard blocker remain the remote coordination task's responsibility.
