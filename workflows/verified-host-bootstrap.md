# Reuse a verified host when configuring another machine

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/verified-host-bootstrap.md>

**TLDR:** Start from an authorized working host before rebuilding an integration or asking the user for discoverable setup details. Use Stanford Network Analysis Project (SNAP) as the preferred private configuration distribution hub when applicable, keep shared procedures in Git, and verify every receiving machine independently.

User instruction, 09-24-2026. Applies across tools and personal laptops, including another owner's machine only within its authorized account and access scope. Complements [broad investigation](broad-investigation.md), [reliable dispatch](reliable-agent-dispatch.md) and [Valkyrie diagnosis](valkyrie.md).

## Assign authority to the right layer

| Layer | Canonical location and responsibility |
|---|---|
| Shared behavior and public installation procedures | The agents-config Git repository; mirror enduring rules in both agent entry points. |
| Approved private configuration, setup packets and verification receipts | The authorized private store, with SNAP as the preferred distribution hub where available. Record the source owner, version, hashes and verification date. Existing service or secret-store authority remains unchanged. |
| Executables, dependency environments, local paths and interactive sign-ins | The receiving host. Build or authenticate there and keep host-specific overrides explicit. |

The hub supplies approved snapshots; it is not automatically the authority for every service or every newer local edit. Keep a verified private replica on an authorized laptop so a hub or virtual private network (VPN) outage does not block unrelated work. Never place private packets, credentials, account identifiers or internal addresses in this public repository.

## Reuse, compare, install, verify

1. **Find working evidence.** Inspect the relevant verified host, existing packet and receipt before rediscovering settings. Determine the actual configuration selected by its command-line interface (CLI), environment overrides, package revision, owner and intended destination. Use the existing authorized connection; do not ask for facts available there.
2. **Check freshness before applying anything.** Compare the approved source configuration, embedded packet configuration and destination's existing settings. Bind a manifest to content hashes, source provenance and dated checks. File modification time alone does not establish authority. Resolve drift from evidence, preserve existing work and back up replaced settings; an old packet must not overwrite newer configuration merely because its installer runs successfully. Reconcile divergent edits explicitly instead of introducing automatic two-way synchronization.
3. **Transfer only the authorized portable material.** Use protected private transport and owner-only storage. Recreate the runtime for the target operating system and processor using recorded versions and installation steps; [Python virtual environments are not generally portable](https://docs.python.org/3/library/venv.html#how-venvs-work). Do not copy whole credential stores, Linux environments or another user's shell and login state as a shortcut. Derive the destination home and report expanded absolute paths.
4. **Verify on the destination.** Check imports, selected configuration, relevant service and storage access, and requested capabilities. Record failures separately. Check that actual global Codex and Claude instruction files are nonempty and resolve to the intended content. Existing running agents need an explicit re-read or a new session; changing files does not prove they reloaded them.
5. **Publish a dated receipt and maintain replicas.** Record exact versions, hashes, checks and unresolved host-specific issues in the private store. Publish approved portable changes with their packet and manifest together, and verify replicas after transfer. Keep an older verified copy during replacement. If the hub is unavailable, use a verified cached copy within its recorded scope and disclose that freshness against the hub remains unverified.

Metadata readiness, successful model inference and completed evaluation are separate outcomes. Setup does not authorize additional paid calls, alter scientific settings or change funding routes. Finish the verification the user actually requested and leave a reusable private instruction for the next host.
