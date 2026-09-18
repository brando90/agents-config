# Mac stall: Chrome zombie leak (Cursor terminal “taking ages”)

**Doc link:** <https://github.com/brando90/agents-config/blob/main/machine/macos-chrome-zombie-leak.md>

**TLDR:** When the Mac’s Cursor terminal freezes and the chassis is hot, it is usually a **wedged Google Chrome** that stopped `wait()`-ing dead children (zombies), not a broken Cursor PTY. Load this playbook (Trigger Rule 59). Zombies cannot be `kill`’d; quit/SIGKILL the Chrome parent. Recurrence: relaunch after Chrome updates, disable tab-debugger extensions, and keep `com.brando.chrome-zombie-watch` installed.

## What happened (09-17-2026, M1 Max, 10 cores, 64 GB)

| Signal | Wedged | After SIGKILL Chrome PID 722 |
|---|---|---|
| Load average (1 min) | **~650** (healthy is ≲10) | **~290** and falling |
| Chrome zombie children | **731** (`<defunct>`, PPID 722) | **0** |
| Live CPU | Chrome main ~150% + NetworkService ~78% + StorageService ~77% ≈ **306%** | Chrome gone |
| GPU helper | ~1% | — |
| Crashpad dumps (48 h) | **0** | not a crash-loop |
| Running Chrome | **153.0.8010.36** for **~1d 22.7h** | — |
| On-disk Chrome | already **153.0.8010.48** | relaunch picks this up |
| Wall power | **90–96 W** USB-C PD | heat from that draw |

Cursor was a **second** load (4-root window: cert-judge + VeriBench + agents-config + ultimate-utils, retrieval indexers, ~220–360% CPU). Nested **byobu/tmux** inside Cursor terminals forked status scripts into the same run queue. Those make the *terminal* feel dead; they are not the 731-zombie factory.

## Unix fact agents get wrong

A zombie (`Z` / `<defunct>`) is **already dead**. It uses **0% CPU**. `kill -9 <zombie-pid>` does nothing. The parent must `wait()`, or the parent must exit so `launchd` (PID 1) reaps. Here the parent was `Google Chrome.app` PID 722. Cmd-Q and `SIGTERM` were **ignored**; **`SIGKILL` on 722** reaped all 731.

## Fast diagnose (no `sudo`)

```bash
python3 ~/agents-config/scripts/chrome_zombie_watch.py --check
# or:
uptime
ps -axo pid,ppid,stat,comm | awk '$3 ~ /Z/ {c[$2]++} END {for (p in c) print c[p], p}'
ps -p <ppid> -o pid,pcpu,etime,command=
```

Healthy: Chrome zombie children **0** (a few age-`00:01` zombies under `tmux`/`byobu` are status-bar blips). Wedged: **dozens to hundreds** of zombies, all PPID = Chrome, Chrome main + Network + Storage all `R` and high CPU, `renderer-client-id` in the thousands with only tens of live renderers.

## Immediate fix

1. Quit unused Dock apps if the box is already at load hundreds (keep Cursor, iTerm2, Finder, Cisco Secure Client / VPN, Dropbox).
2. `osascript -e 'tell application "Google Chrome" to quit'` then wait ~5 s.
3. If Chrome is still there: `kill -TERM <chrome-pid>`; if still there after 10 s: **`kill -KILL <chrome-pid>`**.
4. Do **not** kill Cursor, `tmux` servers, `claude`/`codex` CLIs, or `paper_watch`.
5. Do **not** edit `Secure Preferences` by hand (HMAC-protected; Chrome will reject/reset).

## So it does not come back (real plan, not a kill-cron)

Scheduled “kill Chrome every N hours” is a **workaround**. The leak is: Chrome left up **~2 days**, an **update sitting on disk unused**, plus **extensions that attach a debugger to every tab**.

1. **Install the tripwire** (once per Mac):
   `bash ~/agents-config/scripts/install_chrome_zombie_watch.sh`
   Every 5 min it counts Chrome’s zombie children. At **≥50** it notifies. At **≥100** it SIGKILLs that Chrome (already broken). Log: `~/Library/Logs/chrome_zombie_watch.log`. Uninstall: same script `--uninstall`.
2. **Next Chrome open (Brando, once):** About Google Chrome → confirm **≥ 153.0.8010.48**. Then `chrome://extensions` → disable (until needed on a specific tab):
   - ChatGPT `hehggadaopoacecdllhhajmbjkdcmajg` (native host `com.openai.codexextension`)
   - Claude `fcoeoabgfenejglbffodgkkbkcdhcgfn`
   - Fireflies `meimoidfecamngeoanhnpdjjdcefoldn`
3. **Ordinary Quit (Cmd-Q) when done for the night.** Leaving Chrome 40+ hours is how Network/Storage wedge and stop `wait()`-ing. That is not an agent cron.
4. **Cursor hygiene when writing one paper:** open that repo alone; do not wrap Cursor’s terminal in byobu (14 attached tmux sessions were forking `byobu-status` into a load-650 run queue).

## Do not

- Turn off hardware acceleration (GPU was ~1% in the incident).
- Reinstall macOS or delete the Chrome profile.
- `kill` individual zombie PIDs.
- Auto-kill Chrome on a timer while it is healthy.
