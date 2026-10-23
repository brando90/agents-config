# Herdr: Sherlock and FarmShare access

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/herdr-stanford-access.md>

**TLDR:** Secure Shell (SSH) alias repairs are installed on the Mac. Both saved Herdr profiles remain disabled until interactive Stanford authentication and scheduler-aware server placement are verified. This is a partial setup, not an end-to-end connectivity receipt.

## State verified 10-23-2026

- Mac: Herdr 0.9.5; existing profiles Sherlock (`sherlock`) and FarmShare (`farmshare`), both disabled. Five Stanford Network Analysis Project (SNAP) profiles are preserved.
- Sherlock private runner works on compute node `sh03-01n70` in job `48402562`. Its shared home already contains `~/.local/bin/herdr` 0.9.5 and `~/.local/bin/pi` 1.4.0. This does not prove Mac-to-Sherlock Herdr access.
- SSH repair: explicit trusted-host aliases, Generic Security Services Application Program Interface (GSSAPI) authentication and delegation, keyboard-interactive/password fallback, 12-hour idle master persistence, 30-second keepalives, three missed responses, and 15-second connection timeout.
- Removed Sherlock's overbroad `*.sherlock.stanford.edu` match that rewrote **compute-node destinations** to the login node. The existing `sherlock` alias still pins `sh04-ln07.sherlock.stanford.edu` for continuity.
- FarmShare now uses official `login.farmshare.stanford.edu`, not legacy `rice.stanford.edu`.
- Trusted identities: `login.sherlock.stanford.edu` and `login.farmshare.stanford.edu` already exist in `~/.ssh/known_hosts`. FarmShare's observed ED25519 fingerprint matches its official documentation. Host checking was not disabled.
- Existing Kerberos cache/keytab covers `CS.STANFORD.EDU`; no central Stanford ticket was found. Do not destroy that cache to obtain another realm's ticket.
- 1Password command-line access timed out waiting for authentication. Opening Terminal with AppleScript also timed out; no successful terminal launch was verified.
- Backup: `~/.ssh/config.before-herdr-10-23-2026`. No credentials were copied or changed.

## Next actual human step

In a **new local terminal tab**, not the running agent input, run:

```bash
bash ~/agents-config/scripts/herdr-stanford-login.sh
```

Enter the Stanford password and complete each cluster's Duo prompt in SSH. The helper reuses an existing master when present and verifies hostname/account. It does not store passwords, install software, launch agents, or enable profiles. It fails on the first unsuccessful login; pass `sherlock` or `farmshare` to retry only that host.

## Finish after authentication

1. Reuse the verified SSH masters; inspect the actual destination, account, and current cluster instructions.
2. **Sherlock:** current `/etc/agents/AGENTS.md` prohibits persistent Herdr servers on login nodes. Read `/etc/agents/slurm.md` and `/etc/agents/policy.md`; place the server in a suitable owned compute allocation. Do not launch another SSH server, unattended tunnel, or alternate login service. Use normal authenticated SSH through the login host to the allocated compute node. Do not commandeer or stop the existing private runner job.
3. Configure a dedicated compute target with allocation/node identity and job expiry recorded. Use supported Herdr profile operations; do not redirect the general `sherlock` login alias to a compute node. Preserve existing pane processes. Allocation expiry ends processes: session restore is not process survival.
4. **FarmShare:** inspect existing Herdr installation, current cluster policy and scheduler placement before enabling. The official load-balanced hostname can land on a different node after reconnect; pin the verified concrete endpoint for any node-local session that needs continuity.
5. Herdr manages its own SSH control socket by default. Ordinary `ssh` success alone does not prove Herdr approval. In a terminal run `herdr machine reconnect <label>` for the final saved target. This only authenticates/verifies; it does not install or update Herdr. Use interactive `herdr --remote <target>` only when its reported setup issue calls for installation/compatibility repair.
6. Enable only the verified saved profiles with `herdr machine enable <id>`. Verify `herdr machine status <label> --json`, then `herdr --machine <label> agent list` and a remote shell's hostname. Do not infer success from sidebar visibility.
7. Preserve Herdr's built-in reconnect backoff; do not add a polling daemon. Its managed connection defaults to 10 minutes of idle persistence, distinct from the ordinary SSH master's configured 12 hours. Neither setting extends Duo validity or guarantees survival across network loss.

## Sources

- [Herdr connecting machines](https://herdr.dev/docs/connecting-machines/)
- [Sherlock authentication and multiplexing](https://www.sherlock.stanford.edu/docs/advanced-topics/connection/)
- [FarmShare authentication and published fingerprints](https://docs.farmshare.stanford.edu/connecting/)
- [Existing private runner and access routes](sherlock-agent-access.md)
