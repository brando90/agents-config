# Herdr: Sherlock and FarmShare access

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/herdr-stanford-access.md>

**TLDR:** Both existing profiles are enabled persistently, with dedicated destinations and preserved profile IDs. Sherlock’s server was verified in its own bounded compute allocation; Mac-to-cluster authentication still blocks complete connectivity, so this is a partial repair.

## Verified state, 10-23-2026

- Mac: Herdr 0.9.5. Sherlock (`c27f312d1fad46959429603e07a92257`) targets `herdr-sherlock`; FarmShare (`e3976461afe44d98b37ff24c3ac31aed`) targets `herdr-farmshare`. Both report `enabled: true` in fresh command-line processes.
- All five Stanford Network Analysis Project (SNAP) profiles retain their IDs, order, targets and enabled flags. All five returned `reachable`, and all five explicit saved-machine agent-list commands succeeded.
- Sherlock: separate job `49231871`, `service` partition, one processor, 2 GiB memory, eight-hour limit, on `sh03-01n69`. Herdr 0.9.5 reported `running` and compatible through the existing authenticated private runner’s ordinary connection to this compute node. The recorded end is **10-23-2026 at 9:14:31 p.m. America/Los_Angeles**. This observation expires with the job; inspect live state before reuse.
- The existing private runner’s allocation was preserved. The new server has no automatic renewal or agent supervisor. The reusable job script requests no requeue.
- FarmShare’s dedicated destination is `rice-02.farmshare.stanford.edu`, resolved from the official login alias. Its host-key identity remains the official `login.farmshare.stanford.edu`; successful hostname/account verification and remote setup remain pending authentication.
- Mac saved-profile checks fail at authentication: Sherlock’s login jump reports `Permission denied (gssapi-with-mic,password)`; FarmShare reports `Permission denied (gssapi-keyex,gssapi-with-mic,password)`. Neither is currently proven connected from Herdr on this Mac.
- 1Password’s desktop vault is available, but command-line access requires physical Touch ID. Two bounded authorization attempts timed out. Matching central Stanford Internet-password entries were unavailable through Keychain. No password was retrieved or written.
- The earlier Terminal login helper remains waiting; it was not terminated. Computer-use tools refused Terminal and Ghostty access, so the live sidebar and that prompt could not be inspected. Saved-catalog readback proves enabled state, not a green connection indicator.

## Persistent configuration

- `~/.ssh/config` includes `~/.ssh/herdr-stanford.conf`. The general `sherlock` and `farmshare` login aliases remain intact.
- `herdr-sherlock` uses the current concrete compute host through the existing authenticated `sherlock` login master. Its ProxyCommand is `scripts/herdr_sherlock_proxy.py`, which refuses an expired or mismatched local allocation lease before networking. It does not query the scheduler on background retries. Early job cancellation can precede the recorded expiry; the cluster’s normal access checks and Herdr checks still apply.
- `herdr-farmshare` pins the concrete login node so a reconnect does not silently move a node-local session to another load-balanced host.
- The compute host key was retrieved through the authenticated private runner and saved under the concrete compute host. Existing host-key checks remain active. Allocation refresh refuses changed known keys.
- Catalog: `~/.local/state/herdr/client/endpoints.json`. Target migration preserved IDs, order, selection and unrelated fields, with private byte-exact backups. Herdr 0.9.5 has no supported target-edit command, so `scripts/herdr_stanford_recover.py migrate-target` performs this guarded, atomic implementation-level migration. Keep competing catalog edits idle during migration; upstream does not honor the helper’s advisory lock.
- Ordinary connection keepalives and Herdr’s managed ten-minute idle connection persistence remain distinct. Neither extends Stanford authentication or Slurm allocation lifetimes.

## Complete the remaining authentication

The missing dependency is an actual physical 1Password Touch ID authorization (or the user completing the already-open Stanford login). User consent alone cannot supply that factor. On resumption, use the existing matching Stanford login, keep the password transient, and complete the current official Duo challenge. Inspect the existing Terminal helper before creating another prompt. Never use the SNAP password as an assumed central Stanford password.

Once authenticated:

1. Verify an ordinary `sherlock` login master and current compute allocation. Central Stanford Kerberos credentials may also be needed for the compute hop. Do not replace the existing computer-science Kerberos cache.
2. Read current cluster instructions. Sherlock forbids persistent servers on login nodes; use the owned allocation. Inspect FarmShare’s live policy and installation before starting its server.
3. Run `python3 ~/agents-config/scripts/herdr_stanford_recover.py reconnect Sherlock FarmShare` from an interactive terminal. This enables each existing profile **before** reconnecting, then checks `reachable` and its exact saved-machine agent list. Failure is nonzero and never reported as success.
4. If FarmShare reports a missing server, use documented interactive `herdr --remote herdr-farmshare --session default` setup after the live-policy check. Avoid `machine add`, which creates another profile.
5. Through each saved Herdr profile, create a disposable unfocused tab, verify `hostname` and `id -un`, and remove only that tab. Verify the live sidebar and an explicit reconnect while preserving useful panes.

**Ordering correction:** Herdr 0.9.5 rejects `machine reconnect <label>` and targeted `machine status <label>` when disabled. Earlier instructions to reconnect first and enable last were impossible to complete. Do not disable profiles merely to hide an authentication error.

## Recovery after sleep, authentication expiry, or allocation expiry

Use `python3 ~/agents-config/scripts/herdr_sherlock_allocate.py` to refresh Sherlock’s explicitly requested bounded allocation. It reuses one existing job, submits only if none exists, and returns an informative failure if queued. It never waits in a polling loop, schedules an automatic restart, or restarts a running server. On a running job it refreshes the guarded lease, concrete host key and dedicated alias. Then complete normal Stanford authentication and run the recovery command above.

Allocation expiry ends its processes. A restored terminal layout is not proof that those processes survived. The lease intentionally stops forwarding after the recorded expiry until the explicit refresh command succeeds.

## Verification

The 34 focused deterministic tests passed: 12 profile/reconnect tests, 12 lease-proxy tests, and 10 allocation-refresh tests. The allocation refresh also succeeded against the live existing job without another submission. The instruction-document checker reported zero errors; shell syntax and Git whitespace checks passed. Full authenticated Mac reconnect, FarmShare server setup, remote Herdr panes and live sidebar verification remain incomplete.

## Reproducible files and evidence

- Job source: `scripts/herdr_sherlock_job.sh`; installed Sherlock copy: `~/.local/share/herdr-stanford/server.sbatch`.
- Local lease: `~/.local/state/herdr-stanford/sherlock.json`; compute-side receipt: `~/.local/state/herdr-stanford/runtime.json`.
- Mac SSH backup: `~/.ssh/config.before-herdr-durable-10-23-2026`; endpoint backups sit beside the catalog.
- Private original screenshot, pasted context and hashes: `~/.local/state/herdr-stanford/evidence-10-23-2026/`. The pasted earlier-agent prompt was treated as context, not independent authorization.
- Human-readable companion: <https://docs.google.com/document/d/1VkkBXmcezvHvq_XRrV1gw4Q_yPZ6Ni73-efcMhkoCm4>.

## Sources

- [Herdr connecting machines](https://herdr.dev/docs/connecting-machines/)
- [Herdr 0.9.5 saved-target resolution](https://github.com/herdrdev/herdr/blob/v0.9.5/src/cli/target.rs)
- [Sherlock authentication and multiplexing](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/)
- [Sherlock service jobs](https://www.sherlock.stanford.edu/docs/advanced-topics/service-jobs/)
- [FarmShare authentication and published fingerprints](https://docs.farmshare.stanford.edu/connecting/)
- [Existing private runner and access routes](sherlock-agent-access.md)
