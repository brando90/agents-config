# SNAP internet-only dispatch verification

**Doc link:** https://github.com/brando90/agents-config/blob/main/reports/snap-vpn-free-dispatch-10-07-2026.md

**TLDR:** The MacBook Air reached the official whale gateway and skampere2 without an active Cisco VPN, launched an ordinary-code detached job, and retrieved its successful completion record after the submitting connection ended. This verifies a working authenticated route and short persistent job, not all-host or long-study reliability.

## Verified evidence

- Date: 10-07-2026. Cisco Secure Client reported Disconnected; macOS active network interface was en0, and no configured VPN service appeared in its connection listing.
- Original direct-node checks timed out. Gateway SSH succeeded using the user's existing Kerberos authentication; a separate public-key-only attempt failed. No authentication keys or ticket values were printed or copied.
- Scoped ProxyJump configuration installed in the existing laptop SSH config with a private backup. Gateway excluded from its own proxy stanza, host-key checking retained. The initially unknown gateway key was accepted with OpenSSH accept-new; no independent out-of-band fingerprint verification is claimed.
- Existing protected local keytab renewal succeeded. Existing four-hour LaunchAgent was triggered and its last exit changed from a historical failure to zero; loaded schedule and observed success are separately verified.
- skampere2 returned its hostname, showed Codex and tmux installed, and reported existing ChatGPT CLI login. Login is not proof of model entitlement or remaining budget.
- The regular snap_dispatch launcher submitted `cj-gateway-proof-1007`: sleep five seconds, print hostname/date and a completion marker; no model calls, scientific results or dummy publication.
- Submitting command exited. A later connection with connection sharing disabled retrieved the node-local log and tmux pane status: completion marker present, launcher exit zero, pane dead with exit zero.

```text
[snap_dispatch] host=skampere2 start=2026-10-07T20:34:43-07:00
skampere2.stanford.edu
2026-10-07T20:34:48-07:00
CJ_GATEWAY_TEST_COMPLETED
[snap_dispatch] exit=0 end=2026-10-07T20:34:48-07:00
dead=1 exit=0
```

The preserved remote log is `/lfs/skampere2/0/brando9/snap_jobs/cj-gateway-proof-1007_2026-10-07_20-34-33.wenX8S.log`. Machine-formatted timestamps above are frozen receipt data.

## Limits and ownership

The preflight found roughly 137 GiB free on node-local storage and 60 GiB on shared storage, below percentage thresholds; this tiny receipt consumes negligible space. Large study capacity remains a separate check. An unrelated Claude configuration symlink failed its expected-layout check; this does not affect the ordinary-code transport test. Do not alter shared credentials or other jobs to address unrelated warnings.

No test workload ran on the gateway or a Slurm-gated node. No experiment claims, manuscript edits, main-branch test commits or model calls were created by this connectivity check. Other configured hosts and allocation-gated completion require their own observed outcomes. Real studies still need durable checkpoints, observed completion, deterministic verification, permitted publication and deduplicated notification. This document does not claim that a scientific completion watchdog was installed by the connection setup.
