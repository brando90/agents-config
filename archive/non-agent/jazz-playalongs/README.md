# Jazz play-alongs: keep Google Drive, both Macs, the Pixel and Spotify in sync

**Doc link:** <https://github.com/brando90/agents-config/blob/main/workflows/jazz-playalongs/README.md>

**Mirror (Google Doc):** <https://docs.google.com/document/d/1bAeJLF661zxR4O1cQgnRa3Z_4J9CL_VuL5KzYwb6Q9U/edit>

> **SYNC NOTE.** This Markdown file in `agents-config` is the canonical copy. The Google Doc above is a verbatim mirror for reading on the phone or sharing. Edit here first, commit, then re-export the whole file to the Google Doc (any agent: read this file, `update_file` the Doc, and update the "Last synced" line in both). Last synced: 09-27-2026 (see git log for the commit).

**TLDR:** Google Drive is the single source of truth for the jazz play-along audio (Jamey Aebersold, Hal Leonard, Jim Snidero). Every new song goes to Drive first, then gets pulled to each Mac's local folder and pushed to the Pixel; Spotify playlists sync themselves through Spotify's cloud, but the audio files must exist on every device with matching tags and duration. This page is the checklist for additions and the verification commands, so nobody has to rediscover any of it.

## 1. Where things are (state as of 09-27-2026)

| Place | What | Path / link | Status |
|---|---|---|---|
| **Google Drive (source of truth)** | "Jamey Abersold Stuff" (owner: teacher George Michael, gmichael251@gmail.com; shared with brandojazz@gmail.com). 56 Aebersold volume folders. Brando's own subfolder **"Hal Leonard Jazz Play-Along"** holds the 12 Hal Leonard albums incl. **Jim Snidero**. 1,022 audio files, 6.3 GB. | Root folder id `1tFayeaB_KR5rqAOMcAsRLvjFKTZ0YD28`; Hal Leonard subfolder id `15yjH2HOTZY0WirubSLRBTQVmCGUwbgb4` | complete |
| **MacBook Pro** ("Brando's MacBook Pro (2)" in Spotify Connect) | Local copies; the playlists were built here. Pixel tooling (ADB, scrcpy) lives here. | Spotify Settings → Local Files shows the source folder(s). Records: `/Users/brandomiranda/Applications/Pixel Tools/Music Transfer Records/Jazz Playlists`, `/Users/brandomiranda/Documents/Spotify Jazz Play-Alongs/playlist-results.json` | set up 09-13-2026 (ChatGPT session); re-verified 09-27-2026 remotely over Spotify Connect: Mega, Hal Leonard Vol. 13 Coltrane and Jim Snidero playlists each played a local file on the Pro |
| **MacBook Air** ("Sanmi's MacBook Air") | Full local mirror, organised like Drive. Registered as a Spotify local-files source. | `~/Music/Spotify Local Files/{Jamey Aebersold, Hal Leonard}` (984 files, 5.9 GB) | set up + verified 09-27-2026: 96/96 jazz playlists, 1,773/1,773 local entries playable |
| **Pixel 9 Pro XL** | Local copies pushed by ADB from the MacBook Pro. | `/sdcard/Music/Jazz Play-Alongs/...` and `/sdcard/Music/Jim Snidero/...` (986 files) | set up 09-13-2026; **likely missing everything added to Drive after 09-13 (at least Hal Leonard Vol. 13 Coltrane, 10 tracks)** |
| **Spotify playlists** | 96 private playlists: "Brando's Mega Play-Alongs" (806 local tracks), one per Hal Leonard album (Play-Alongs + Melody & Split), one per Aebersold volume/disc, two Jim Snidero. Playlists live in Spotify's cloud and appear on every device; only the audio is per-device. | Mega: `spotify:playlist:11cA2OIu3sLseq2jMCAxme`; full catalog with links in the 09-13 doc below | complete |

Earlier documentation (keep, do not duplicate): Google Doc **"MacBook Pro to Pixel — Phone Control and Spotify Local Music Setup"** (09-13-2026) — Pixel/ADB procedure, Android permissions, the full playlist catalog with links: <https://docs.google.com/document/d/1Dsy1XE5gjwPzD_Gl-6gi6j-5OnffELh_rWPiBBcx75Y/edit>. Its "Hal Leonard Jazz Play-Along — Download Guide" sibling (where to buy remaining volumes): <https://docs.google.com/document/d/1_o3Xf73xLigZbHyzAM4-YXO8hCwREUpLmBFEfdqTrs4/edit>.

## 2. The one rule

**Drive first.** A new song or volume is uploaded to Google Drive into the right folder before anything else. Each device is a mirror of Drive, never the other way round. Folder naming: Aebersold volumes as `Vol NN - [Title]` directly under "Jamey Abersold Stuff"; Hal Leonard albums as their own folder under "Hal Leonard Jazz Play-Along". Keep the audio files exactly as bought/ripped (tags intact); do not re-encode.

## 3. Adding new songs: the checklist

1. **Upload to Drive** into the correct volume folder (see rule above).
2. **Pull to each Mac.** Two ways:
   - *Option A (recommended, automatic once set up): Google Drive for desktop.* Install it, sign in as brandojazz@gmail.com, add a shortcut to "Jamey Abersold Stuff" in My Drive, mark it **Available offline**, and register that folder (`~/Library/CloudStorage/GoogleDrive-brandojazz@gmail.com/My Drive/Jamey Abersold Stuff`) as the Spotify local-files source. From then on every upload appears on the Mac by itself. Not installed on either Mac as of 09-27-2026.
   - *Option B (what was done on 09-27-2026, agent-driven):* an agent lists the Drive folder (Drive connector `search_files` with `parentId = '<folder id>'`, paginated 5 per page), diffs against the local folder by name and byte size, and downloads the missing files: Drive connector `download_file_content` for files ≤ 10 MB (decode the base64 result with `sweep.py`-style code), or Chrome direct links `https://drive.usercontent.google.com/download?id=<id>&export=download&authuser=0` for anything (much faster, ~40 files/min). Put files under `~/Music/Spotify Local Files/<Jamey Aebersold|Hal Leonard>/<volume folder>/`.
3. **Let Spotify index the folder.** Spotify watches its registered source folders and indexes new files within seconds (its index is `~/Library/Application Support/Spotify/Users/<id>-user/local-files.bnk`). If the folder is not registered yet, run `spotify_local_setup.py` (section 5) once; it also verifies playback.
4. **Add the tracks to the playlists** once, on either Mac: in Spotify (Local Files → right-click → Add to playlist), or `spotify_cli playlist add spotify:playlist:<id> <local uri...>`. Playlists then sync to all devices automatically.
5. **Push to the Pixel** from the MacBook Pro over USB (procedure and exact commands in the 09-13 doc): `"/Users/brandomiranda/Applications/Pixel Tools/platform-tools/adb" -d push "<file>" "/sdcard/Music/Jazz Play-Alongs/<same volume folder>/"`, then let Android index it (or force-stop and reopen Spotify), then play one of the new tracks on the phone. Keep Spotify → Settings → Local audio files ON and Android → Apps → Spotify → Permissions → Music and audio = Allow.
6. **Verify on every device** (section 6). A playlist entry that shows grey/unplayable means the audio identity does not match; see section 4.

## 4. How Spotify matches a playlist entry to a local file (why grey tracks happen)

A local track's identity is `spotify:local:<artist>:<album>:<title>:<seconds>`, built from the file's tags (ID3v2 if present, else ID3v1; for M4A the iTunes atoms) and the **whole-second duration**. No title tag → the file name is used (`'` becomes `_`). The same file must therefore produce the same four values on every device:

- Keep tags identical everywhere (copy files byte-for-byte; never let one device retag).
- Duration is computed by each Spotify client; the Air's client subtracts encoder delay, so 12 files came out one second short of the identities the Pro had created. Fix = make the file's stated length match the playlist identity without touching audio: `fixdur.py <file>` (rewrites the M4A `iTunSMPB` gap-info, or appends a few frames and fixes the VBRI count for MP3). The Pixel had the same class of problem on 09-13 ("timing copies"). After any fix, Spotify re-indexes on its own.
- Two files with identical tags and length collide (Vol. 30 "Samba De Luvsme" keyboard vs bass discs): give them distinct album tags, as was done on both Macs.

## 5. Scripts in this folder (`workflows/jazz-playalongs/`)

| Script | Purpose |
|---|---|
| `spotify_local_setup.py` | One-shot, idempotent: relaunch Spotify with a localhost DevTools port, enable local files, add the audio folder as a source through Spotify's own `LocalFilesAPI`, restart Spotify normally, then play a jazz playlist on this Mac and confirm a local file is open. `--verify-only` just runs the playback check. Needs `pip install websocket-client`. (Spotify and Music are blocked for screen control by policy; this is the supported alternative.) |
| `spuri.py` | Compute the Spotify local identity for every audio file under a folder (uses `mutagen`). |
| `fixdur.py` | Nudge a file's stated duration so it matches a playlist identity (section 4). Backs up first. |
| `mp4atoms.py` | Inspect M4A duration atoms / `iTunSMPB` when debugging a mismatch. |
| `cdp.py` | Tiny Chrome DevTools client used by the setup script (localhost only). |

Useful Spotify CLI (bundled with the app, no install): `/Applications/Spotify.app/Contents/MacOS/spotify_cli` — `status`, `devices list`, `play <uri> --device <id>`, `now-playing --format json`, `pause`, `playlist get <uri> --format json`, `playlist add`. Prove a local file is really playing with `lsof -p $(pgrep -x Spotify) | grep "Spotify Local Files"`.

## 6. Verification commands

- Mac, full check (all jazz playlists, Spotify's own playability flag): run `spotify_local_setup.py --verify-only` for a playback smoke test; for the exhaustive check, launch Spotify with `--remote-debugging-port=9222` and evaluate `PlaylistAPI.getContents(<playlist>)` per playlist, counting `isPlayable` on local items (see the 09-27-2026 session for the exact snippet; 96/96 playlists, 1,773/1,773 entries passed).
- Mac, quick: `spotify_cli play spotify:playlist:11cA2OIu3sLseq2jMCAxme --device <this Mac's device id>`; after ~8 s `spotify_cli now-playing --format json` must show a `spotify:local:` uri with `is_playing: true`; then `spotify_cli pause`.
- Pixel: open the Mega playlist, tracks must not be grey; play one new track. Details and troubleshooting in the 09-13 doc.
- Drive vs Mac drift: count audio files in Drive (connector listing) vs `find ~/Music/Spotify\ Local\ Files -name '*.mp3' -o -name '*.m4a' | wc -l` (984 on 09-27-2026; Drive had 1,022 incl. duplicates/PDF-adjacent extras and tuning notes not needed by playlists).

## 7. Known gaps / next actions

- **Pixel:** push Hal Leonard Vol. 13 Coltrane (10 files, Drive folder `1hv1k3zxWSqSkr5wqtSoHuztJ7pPcmgWc`) and anything else added after 09-13-2026; re-verify the Mega playlist on the phone.
- **MacBook Pro:** current as of 09-27-2026 (Vol. 13 Coltrane plays there). Nothing pending.
- **Both Macs:** install Google Drive for desktop (Option A) to make future additions automatic; then point Spotify at the CloudStorage folder and drop the manual pull.
- Non-jazz playlists with local tracks (bachata, zouk, Mozart) are out of scope; those files are not in Drive.

## 8. Keeping this page and the Google Doc in sync

- Canonical = this file. The Google Doc is a read-only mirror (Brando can read it on the phone; George could be given it).
- After editing here: `git commit && git push`, then re-export. The Drive connector's `update_file` cannot change a Doc's text, so an agent re-exports by creating a fresh Doc from this file (`create_file` with `contentMimeType: text/markdown`, same title), moving/trashing the old one, and putting the new URL in the "Mirror" line above. Update the "Last synced" date in both.
- Drift check: compare the "Last synced" date in the Doc with `git log -1 --format=%cd -- workflows/jazz-playalongs/README.md`.

## 9. History

- 09-13-2026: ChatGPT session set up MacBook Pro + Pixel (ADB/scrcpy), built the 91 playlists, verified 937 entries on the phone. Doc linked in section 1.
- 09-20-2026: Hal Leonard Vol. 13 Coltrane added to Drive and to playlists (Mega grew 781 → 806 local tracks).
- 09-27-2026: Claude Code session set up the MacBook Air: downloaded 947 needed tracks from Drive (connector + Chrome), fixed 12 duration identities, registered the folder via `LocalFilesAPI`, verified 96/96 playlists playable; freed 26 GB of caches; verified the MacBook Pro remotely over Spotify Connect (Mega, Vol. 13 Coltrane, Snidero all play local files there). This runbook and scripts written; Google Doc mirror created.
