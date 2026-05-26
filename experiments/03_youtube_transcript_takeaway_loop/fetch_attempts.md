# Transcript Fetch Attempts — Log

Date: 2026-05-26
Sandbox: cloud IP (YouTube/Google blocks this range)
Target: https://youtu.be/u-2F63eD9tE

| # | Method | Command / URL | Result |
|---|--------|---------------|--------|
| 1 | `WebFetch` on short URL | `https://youtu.be/u-2F63eD9tE` | 303 redirect to `youtube.com/watch?v=...` |
| 2 | `WebFetch` on long URL | `https://www.youtube.com/watch?v=u-2F63eD9tE` | 302 to `google.com/sorry/index?...` (captcha) |
| 3 | `yt-dlp` w/ `--write-auto-sub` | `yt-dlp --skip-download --write-auto-sub ...` | SSL verify failed, then 429 Too Many Requests |
| 4 | `yt-dlp` w/ `--no-check-certificates` | same as #3 + `--no-check-certificates` | "Sign in to confirm you're not a bot" |
| 5 | `youtube-transcript-api` (Python) | `YouTubeTranscriptApi().fetch('u-2F63eD9tE')` | `IpBlocked` exception — "IPs from cloud providers are blocked by YouTube" |
| 6 | Direct timedtext API | `curl https://www.youtube.com/api/timedtext?lang=en&v=u-2F63eD9tE` | Google "Sorry..." block page |
| 7 | Direct timedtext API (json3) | same as #6 + `&fmt=json3` | Google "Sorry..." block page |
| 8 | `WebFetch` to `youtubetranscript.com` | `https://youtubetranscript.com/?v=...` | 403 Forbidden |
| 9 | `curl` to `youtubetranscript.com` | with browser UA | XML response: "YouTube is currently blocking us from fetching subtitles" |
| 10 | `WebFetch` to `tactiq.io` | `https://tactiq.io/tools/youtube-transcript?yt=...` | 403 Forbidden |
| 11 | `WebFetch` to `notegpt.io` API | `https://notegpt.io/api/v1/youtube-transcript?...` | 404 Not Found |
| 12 | `WebFetch` to `kome.ai` API | `https://kome.ai/api/transcript?video_id=...` | 405 Method Not Allowed |
| 13 | `WebFetch` to youtube-transcript.io | `https://www.youtube-transcript.io/videos/u-2F63eD9tE` | 403 Forbidden |
| 14 | `WebFetch` to youtubetotranscript.com | `https://youtubetotranscript.com/transcript?v=...` | 403 Forbidden |
| 15 | `WebFetch` to Wayback Machine | `https://web.archive.org/web/2026*/...` | Claude Code blocks web.archive.org |
| 16 | oEmbed metadata fetch (worked) | `https://www.youtube.com/oembed?url=...&format=json` | 200 OK — title/author only, no transcript |
| 17 | noembed.com (worked) | `https://noembed.com/embed?url=...` | 200 OK — title/author only, no transcript |

## Root cause

YouTube blocks the sandbox IP. Every direct and proxy path eventually contacts
YouTube and fails. Cached transcript services either gate behind a frontend
captcha or are themselves blocked from YouTube.

## Workarounds that *would* work

- Run `fetch_transcript.sh` from a residential IP.
- Paste the transcript manually into `transcript.md`.
- Use a paid transcript API with rotating residential proxies (overkill for one video).
