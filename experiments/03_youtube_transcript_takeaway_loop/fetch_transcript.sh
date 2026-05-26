#!/usr/bin/env bash
# Fetch a YouTube transcript and write it to transcript.md (next to this script).
#
# Usage:
#   bash fetch_transcript.sh <youtube_url>
#
# Run from a residential IP — YouTube blocks cloud-provider IP ranges. If you
# see "IpBlocked" or 429 errors, this script cannot help; paste the transcript
# manually instead.
#
# Requires Python 3 with `youtube-transcript-api` installed:
#   pip install youtube-transcript-api
set -euo pipefail

URL="${1:-}"
if [[ -z "$URL" ]]; then
  echo "usage: $0 <youtube_url_or_video_id>" >&2
  exit 2
fi

# Extract video id from common URL shapes; fall back to assuming arg is the id.
VIDEO_ID="$(printf '%s' "$URL" \
  | sed -E 's#.*[?&]v=([^&]+).*#\1#; s#.*youtu\.be/([^?]+).*#\1#; s#.*embed/([^?]+).*#\1#')"

OUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_FILE="$OUT_DIR/transcript.md"

python3 - "$VIDEO_ID" "$URL" "$OUT_FILE" <<'PY'
import sys, datetime
from youtube_transcript_api import YouTubeTranscriptApi

video_id, url, out_file = sys.argv[1], sys.argv[2], sys.argv[3]
api = YouTubeTranscriptApi()
segments = api.fetch(video_id)

with open(out_file, "w") as f:
    f.write(f"# Transcript — {url}\n\n")
    f.write(f"_Fetched {datetime.date.today().isoformat()} via youtube-transcript-api._\n\n")
    f.write("## Verbatim\n\n")
    for seg in segments:
        f.write(seg.text.strip() + "\n")
print(f"wrote {out_file} ({len(segments)} segments)")
PY
