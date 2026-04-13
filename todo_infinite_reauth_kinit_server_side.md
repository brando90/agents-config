# TODO: Infinite Server-Side Kerberos Renewal (No More reauth/krbtmux)

**GitHub Issue:** [brando90/agents-config#11](https://github.com/brando90/agents-config/issues/11)

Goal: auto-renew Kerberos tickets + AFS tokens on SNAP servers using the keytab, so
tmux/byobu/Cursor sessions never lose access. Eliminates the need for `krbtmux` and `reauth`.

## Why this is needed

The Mac-side keytab + launchd setup (see `init_no_passwords_snap_kinit.md`) handles SSH login —
you never type a password to connect. But once on the server, the delegated Kerberos ticket
expires after ~10h. When it expires:

- AFS paths (`/afs/cs/...`) stop working
- Any Kerberos-authenticated command fails
- tmux/byobu sessions that have been running for days break
- Long-lived Cursor sessions lose server-side auth

Currently this requires manually running `krbtmux` + `reauth`. With a server-side keytab +
auto-renewal, all sessions stay alive forever — no manual intervention.

## How it will work

```
Server-side cron or background loop (every 4h):
  kinit -kt ~/.keytab brando9@CS.STANFORD.EDU && aklog
        ↓
Server Kerberos ticket + AFS token always fresh
        ↓
ALL sessions benefit: tmux, byobu, Cursor, background jobs
        ↓
No krbtmux, no reauth, no manual intervention ever
```

## TODO

```
[x] Copy keytab to DFS (done 2026-04-09): /dfs/scratch0/brando9/.keytab (chmod 600)
[x] Check if crontab works on SNAP: yes, cron is available (done 2026-04-09)
[x] Created standalone krenew.sh script at /dfs/scratch0/brando9/bin/krenew.sh (done 2026-04-09)
[x] Added .bashrc background loop with PID-file guard + disown (done 2026-04-09)
[x] Added cron (0 */4 * * *) on: skampere1-3, mercury1-2, hyperturing1 (done 2026-04-09)
[x] Fixed .bashrc nvidia-htop noise for non-interactive shells (done 2026-04-09)
[x] Multi-node sweep: all 6 nodes pass — ticket valid, PID alive, AFS OK, cron set (done 2026-04-09)
[x] scp test passed (no more "Received message too long") (done 2026-04-09)
[ ] Long-duration test: tmux session 10+ hours, verify klist + AFS still work
[ ] Long-duration test: Cursor SSH session 10+ hours, verify no auth failures
[ ] Add cron to Slurm-gated nodes (ampere1/8/9, hyperturing2) when jobs are running
```

## Dependencies

- Keytab already exists on skampere1 at `/lfs/skampere1/0/brando9/.keytab` (created 2026-04-09)
- Mac-side setup is complete (see `init_no_passwords_snap_kinit.md`)

## Security notes

- The keytab on DFS is accessible from all SNAP nodes — protect with `chmod 600`
- DFS is shared storage — ensure only your user can read it
- Same password-change caveat: if you change your Stanford password, regenerate the keytab
