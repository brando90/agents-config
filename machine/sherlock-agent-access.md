# Reusable Sherlock access for agents

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/sherlock-agent-access.md>

**TLDR:** Use the private scheduled GitHub runner when it is active, an existing SSH connection, or authenticated OnDemand before asking for another login. Fresh Sherlock login connections still require Duo; the prepared runner's live activation status is recorded separately.

## Choose an available route

1. **Private runner:** inspect `sherlockctl status` when installed. It uses an already-authorized GitHub command-line interface (CLI) account and a repository-scoped runner executing under Slurm. An online runner permits `sherlockctl exec 'hostname; id -un'`, `sherlockctl jobs` and `sherlockctl submit /absolute/local/job.sbatch`. Follow the [private installation and command guide](https://github.com/brando90/sherlock-agent-bridge/blob/main/README.md) and [activation receipt](https://github.com/brando90/sherlock-agent-bridge/blob/main/receipts/status.md). A published script is not proof that the runner is online; check live status on the invoking host.
2. **Existing Secure Shell (SSH) connection:** check `ssh -O check sherlock`. If it succeeds, reuse it with `ssh -o BatchMode=yes sherlock 'hostname; id -un'`. Sharing applies to agents running as the same local user on that computer, not automatically to every machine. Do not terminate another agent's authentication prompt.
3. **Existing OnDemand session:** use the authorized browser's [Sherlock dashboard](https://ondemand.sherlock.stanford.edu), verify the account, and open **Clusters → Sherlock Shell Access**. Browser-capable agents can submit and inspect jobs there without establishing a separate local SSH session. Submitted jobs survive closing the browser. A command-line-only agent does not inherit browser access merely because another agent has it.
4. **Actual authentication challenge:** follow [authorized sign-in](../rules/services.md#authorized-sign-in-and-verification-codes). When Duo prompts for an SMS passcode, inspect the paired Google Messages tab (`messages.google.com/web/conversations`) on macOS before asking Brando to check his physical phone. Ask only for a physical or unavailable factor after checking usable existing routes. Do not loop failed passwords or classify one missing socket as a cluster-wide outage.
5. **Scheduler & login-node etiquette (anti-spam):** Follow official policy in `/etc/agents/AGENTS.md`: never leave tight `watch` or rapid polling loops querying Slurm, filesystems, or logs (wait at least 60 seconds between status checks); avoid rapid SSH reconnect loops that trigger firewall/DoS alarms (preserve single multiplexed `ControlMaster` sockets); and keep all compute off login nodes.

## What “without Duo” means

Sherlock's [connection documentation](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/) requires Duo for a fresh login-node connection, even when Kerberos replaces password entry. SSH public-key login is not supported. Stanford Network Analysis Project (SNAP) uses a different authentication setup; its working Kerberos route does not establish a Sherlock exemption.

Stanford explicitly supports [GitHub Actions runners as Slurm jobs](https://www.sherlock.stanford.edu/docs/software/dev/ci-cd/). A registered runner pulls authenticated requests and continues across scheduled restarts without a new Duo challenge for each request. Use its private, authorized repository rather than changing Stanford authentication or starting an SSH server. A new or expired OnDemand session can still require normal Stanford sign-in.

[Data Transfer Nodes](https://news.sherlock.stanford.edu/publications/easier-connection-to-sherlock-s-dt-ns) provide a separate supported Duo-free file-transfer route, including Kerberos authentication. They do not offer a general shell. Do not mistake transfer access for compute-job access.

## Shared SSH configuration

If a multiplexing setup already exists, inspect and preserve it. The following host aliases share one local socket; private SSH-directory permissions must be retained. The official docs recommend `%C` on macOS to avoid long socket paths.

```sshconfig
Host sherlock login.sherlock.stanford.edu
    HostName login.sherlock.stanford.edu
    User <SUNetID>
    ControlMaster auto
    ControlPath ~/.ssh/%C
    ControlPersist 12h
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

`ControlPersist 12h` is an idle lifetime for the master connection, not a guarantee that credentials never expire or that a network interruption cannot close it. Use the runner for commands from other authorized machines instead of copying socket files or browser sessions.

## Runner scope and recovery

The private implementation uses one processor and 2 GB memory on the `service` partition. A 24-hour allocation and hourly singleton restart follow Stanford's [persistent-service guidance](https://www.sherlock.stanford.edu/docs/advanced-topics/service-jobs/). Scheduler delays can cause offline intervals. Request substantial computation through its own `sbatch` job, within the experiment's existing authorization and budget.

The client reports a request identifier and workflow link. Retrieve uncertain outcomes before retrying a job submission; a new request is a new execution. Private workflow logs retain command text and output, so do not put secrets in either. Repository write access confers command execution as the configured Sherlock account; keep that repository private and limited to the already-authorized owner/agents. Registration credentials stay in an owner-only directory on Sherlock.

## Job scheduling: concurrent work vs. anti-spam safeguards, 10-18-2026

- **Concurrent multi-job execution is fine and supported:** Users and agents can submit multiple distinct Slurm jobs at once (e.g., parameter sweeps, separate evaluation benchmarks, concurrent training runs). Submit different work as ordinary `sbatch` commands or via `sherlock_dispatch.sh run <name> '<cmd>'`.
- **Do not spam Sherlock in destructive ways:**
  - **No tight polling loops:** Never run high-frequency polling on Slurm APIs (`squeue`, `sacct`, `sinfo`), filesystems, or logs (e.g., no `watch`, no `while true; do squeue; sleep 1; done`). Wait at least 60 seconds between status checks.
  - **No SSH reconnection storms:** Preserve and reuse a single multiplexed `ControlMaster` socket; do not burst new TCP/SSH logins.
  - **No duplicate submissions:** Never submit a duplicate copy of a job that is already pending (`PD`) or queued.
  - **Zero compute on login nodes:** Always dispatch computation to compute nodes via `sbatch` or `srun`.

## Evidence, 10-18-2026

Official authentication, runner and service documentation were retrieved. The local authenticated GitHub account created the private control repository (`brando90/sherlock-agent-bridge`) and installed the client; nine local deterministic checks passed. Registration, recurring scheduling under `scrontab`, and live runner execution under the `service` partition (job 48402309 on `sh03-01n69`) were activated and verified on 10-18-2026. Direct OpenSSH connection multiplexing (`ControlPersist yes`) is active concurrently on macOS. Refresh and read this guide on each host; publication alone does not reload other running agents.
