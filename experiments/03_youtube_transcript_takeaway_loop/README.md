# Experiment 03 — YouTube Transcript → Repo Takeaways Loop

**Status:** Partial (transcript unavailable from sandbox; meta-takeaways captured)
**Started:** 2026-05-26
**Branch:** `claude/video-transcript-experiment-FXZNd`
**Source video:** https://youtu.be/u-2F63eD9tE
**Video title:** *Research Colloquium 05/07/26 — Vishnu Ravi, MD.*
**Channel:** Stanford Division of Computational Medicine

## What this experiment is

Brando asked Claude Code to: "go through the transcript, get the text, and make a new
experiment folder with what I can learn from this — main takeaway specially to improve
this repo."

The narrow goal was: distill one Stanford colloquium talk into concrete improvements
to `agents-config`. The broader goal — the one this folder is actually about — is to
turn arbitrary external talks/videos/papers into a repeatable "fetch → distill →
patch the repo" loop.

## Files

| File | Purpose |
|------|---------|
| `README.md` | This file — context and how to finish the experiment. |
| `video_metadata.json` | oEmbed metadata for the source video (the one piece we *could* fetch). |
| `fetch_attempts.md` | Log of every transcript-fetch method tried and how it failed. Useful as a debugging artifact and as evidence for the meta-takeaway. |
| `fetch_transcript.sh` | Reusable bash helper that takes a YouTube URL and writes `transcript.md`. Run from a non-cloud IP (cloud IPs are blocked by YouTube). |
| `transcript.md` | Placeholder. Populated either by `fetch_transcript.sh` or by pasting the transcript manually. |
| `takeaways.md` | The main deliverable: concrete `agents-config` improvements suggested by this experience. |

## How to finish (when transcript is available)

1. From a residential IP (not a cloud sandbox), run:
   ```
   bash experiments/03_youtube_transcript_takeaway_loop/fetch_transcript.sh \
     https://youtu.be/u-2F63eD9tE
   ```
   Or paste the transcript text into `transcript.md` manually.
2. Re-run Claude on this folder with the prompt: "read transcript.md and update
   takeaways.md with concrete repo improvements tied to specific files/sections."
3. Open a follow-up PR that implements the highest-value takeaway (do not bundle
   all takeaways into one PR — each should be reviewable independently).

## Why the transcript was not fetched here

Every fetch path the sandbox has — `WebFetch`, `yt-dlp`, `youtube-transcript-api`,
the YouTube `timedtext` API directly, and several third-party transcript proxies —
returned 403, 429, captcha redirects, or `IpBlocked`. The sandbox IP is in a range
YouTube blocks. See `fetch_attempts.md` for the full log. This is itself a relevant
finding for an agent-config repo (see takeaway #1 in `takeaways.md`).
