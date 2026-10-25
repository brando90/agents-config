# Automatic Pi sync: six-machine verification — 10-24-2026

**Doc link:** <https://github.com/brando90/agents-config/blob/main/config/pi/auto-sync-rollout-10-24-2026.md>

**TLDR:** Automatic private synchronization is enabled on the Mac and five existing cluster profiles. Scheduled runs propagated edits in both directions and restored the original setting/deleted the test files; all six profiles finished at hub revision 4 with zero runtime drift and Pi advertised 5/5 personal skills on each.

## Verified scope

| Machine | Scheduler | Final hub revision | Runtime drift | Skills advertised |
|---|---|---:|---:|---:|
| Mac | LaunchAgent | 4 | 0 | 5/5 |
| skampere1 | Per-user cron | 4 | 0 | 5/5 |
| skampere2 | Per-user cron | 4 | 0 | 5/5 |
| skampere3 | Per-user cron | 4 | 0 | 5/5 |
| mercury1 | Per-user cron | 4 | 0 | 5/5 |
| mercury2 | Per-user cron | 4 | 0 | 5/5 |

The normal interval is 60 seconds; a change can need another client's next tick to arrive. The Mac's retry delay grows to at most 30 minutes after failures. Cluster clients access the shared private hub directly and can synchronize while the Mac is asleep. The Mac needs its existing Secure Shell (SSH) authentication and connectivity to return before it catches up.

## Actual propagation test

1. Edited `collapseChangelog` and created inert test files in the canonical public and private resource trees on the Mac. Scheduled jobs picked them up; no destination installer was manually invoked for propagation.
2. Edited that setting and both test files from skampere2. Scheduled jobs propagated the reverse edit to the Mac and the other enrolled profiles. All six readbacks agreed at hub revision 3.
3. Restored the original absent setting and deleted both test files on the Mac. Scheduled retries propagated cleanup. Final readbacks at 09:18 p.m. America/Los_Angeles on 10-24-2026 showed revision 4, zero runtime drift, the original absent setting, and both files absent on all six profiles.
4. Queried Pi's command inventory on every host: all five canonical personal skills advertised, with zero model requests. A separate ordinary-Pi inventory on the Mac also registered `/config-sync` with the updated extension loaded.

The automated suite passes 39 tests locally. The 14 automatic-sync tests also pass on mercury1 with Python 3.8. Tests cover independent and conflicting edits, deletion/edit conflicts, private files, intentional host differences, offline and concurrent edits, exact peer convergence, mutable npm-version capture, path/symlink restrictions, lock contention, abandoned-lock recovery and idempotency. Instruction-document and whitespace checks pass.

## Corrections found during rollout

- The cluster user-service manager could not access its unit through the Andrew File System (AFS) home configuration. The final installer preserves the existing per-user crontab and adds one marked sync job. The failed unit was removed; the temporary linger change was reverted. Scheduled receipts after the installation shell exited establish real cron execution.
- Simultaneous cron ticks initially contended for the hub lock. A bounded 20-second lock wait serializes them. When another client sharing the source tree has already applied exactly the desired revision, that convergence is accepted; a different new edit remains protected and retried.
- The Mac's cleanup edit raced with an in-flight sync. The concurrency check preserved it, and its scheduled retry completed without a manual apply.

## Boundaries and recovery

This synchronizes canonical skills/resources and supported ordinary-Pi preferences, not every file in a home directory. Source and private skill changes travel privately; there is no automatic public Git commit or push. Authentication, sessions, model-provider credentials, machine identity, vendor skill collections and arbitrary local package source directories remain separately managed. Intentional host overrides are retained. Working-tree changes from synchronized public skill edits can be committed normally when ready for publication.

Native scheduler registration configures login/reboot persistence; no machine was rebooted for this verification. Existing active Pi sessions still need `/reload` for resource discovery and may retain their selected model; their turns were not interrupted. Specialized profiles, other laptops, Sherlock and FarmShare were not enrolled by this rollout. Skill discovery does not prove availability of host applications, external connectors or provider authentication.

Status: `python3 ~/agents-config/config/pi/auto_sync.py status`, or `/config-sync` in Pi. Private backups and baseline receipts remain under the enrolled profile's `auto-sync/` directory and the private hub. Conflict resolution commands and enrollment details are in the [guide](README.md#automatic-sync--10-24-2026).

[Google companion](https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4).
