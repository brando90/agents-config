# TODO: Infinite Server-Side Kerberos Renewal (No More reauth/krbtmux)

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
[ ] Copy keytab to DFS so all nodes can access it:
      cp /lfs/skampere1/0/brando9/.keytab /dfs/scratch0/brando9/.keytab
      chmod 600 /dfs/scratch0/brando9/.keytab
[ ] Check if crontab works on SNAP: ssh into skampere1, run `crontab -l`
[ ] If cron allowed:
      crontab -e
      Add: 0 */4 * * * kinit -kt /dfs/scratch0/brando9/.keytab brando9@CS.STANFORD.EDU && aklog
      (repeat on each server, or find a way to share crontab via DFS)
[ ] If cron NOT allowed, add background loop to .bashrc (only starts once per server):
      Add to /dfs/scratch0/brando9/.bashrc:
        if [[ -z "$(pgrep -f 'kinit.*keytab.*brando9')" && -f /dfs/scratch0/brando9/.keytab ]]; then
          (while true; do kinit -kt /dfs/scratch0/brando9/.keytab brando9@CS.STANFORD.EDU && aklog; sleep 14400; done &)
        fi
[ ] Test: start a tmux session, wait 10+ hours, verify `klist` still shows valid ticket
[ ] Test: verify AFS paths still work after 10+ hours
[ ] Test: Cursor long session — verify no auth failures after hours of use
[ ] Update init_no_passwords_snap_kinit.md with server-side setup instructions
[ ] Update cursor_ssh_kerberos_todo.md to mark krbtmux/reauth as no longer needed
```

## Dependencies

- Keytab already exists on skampere1 at `/lfs/skampere1/0/brando9/.keytab` (created 2026-04-09)
- Mac-side setup is complete (see `init_no_passwords_snap_kinit.md`)

## Security notes

- The keytab on DFS is accessible from all SNAP nodes — protect with `chmod 600`
- DFS is shared storage — ensure only your user can read it
- Same password-change caveat: if you change your Stanford password, regenerate the keytab
