#!/usr/bin/env bash
# Fetch a YouTube video's oEmbed metadata and (when reachable) its transcript.
#
# Usage:
#   bash scripts/fetch_youtube_transcript.sh <youtube_url_or_video_id> [out_dir]
#
# Writes into <out_dir> (default = current directory):
#   - video_metadata.json   always written (oEmbed succeeds even when transcript fetch is blocked)
#   - transcript.md         written only if youtube-transcript-api succeeds
#   - fetch_attempts.md     appended on failure with the failure mode
#
# YouTube blocks cloud-provider IP ranges. If you see "IpBlocked", "429", or
# captcha redirects, run this from a residential network or paste the
# transcript manually into transcript.md (see experiments/03 README).
#
# Requires: bash, curl, python3, `pip install youtube-transcript-api`.
set -euo pipefail

URL_OR_ID="${1:-}"
OUT_DIR="${2:-.}"
if [[ -z "$URL_OR_ID" ]]; then
  echo "usage: $0 <youtube_url_or_video_id> [out_dir]" >&2
  exit 2
fi
mkdir -p "$OUT_DIR"

VIDEO_ID="$(printf '%s' "$URL_OR_ID" \
  | sed -E 's#.*[?&]v=([^&]+).*#\1#; s#.*youtu\.be/([^?]+).*#\1#; s#.*embed/([^?]+).*#\1#')"
URL="https://youtu.be/${VIDEO_ID}"

echo "[1/2] fetching oEmbed metadata for $URL ..."
META_RAW="$(curl -sfL --max-time 15 \
  "https://www.youtube.com/oembed?url=${URL}&format=json" \
  || curl -sfL --max-time 15 "https://noembed.com/embed?url=${URL}" \
  || true)"

if [[ -z "$META_RAW" ]]; then
  echo "  oEmbed failed (both endpoints). Writing stub." >&2
  printf '{"source_url":"%s","fetched_at":"%s","error":"oembed_unreachable"}\n' \
    "$URL" "$(date -I)" > "$OUT_DIR/video_metadata.json"
else
  python3 - "$URL" "$META_RAW" "$OUT_DIR/video_metadata.json" <<'PY'
import json, sys, datetime
url, raw, out = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.loads(raw)
data["source_url"] = url
data["fetched_at"] = datetime.date.today().isoformat()
data["fetched_via"] = "oembed"
with open(out, "w") as f:
    json.dump(data, f, indent=2)
PY
  echo "  wrote $OUT_DIR/video_metadata.json"
fi

echo "[2/2] fetching transcript ..."
if ! python3 -c "import youtube_transcript_api" 2>/dev/null; then
  echo "  youtube-transcript-api not installed; skipping. Run: pip install youtube-transcript-api" >&2
  exit 0
fi

set +e
python3 - "$VIDEO_ID" "$URL" "$OUT_DIR/transcript.md" <<'PY' 2> "$OUT_DIR/.transcript_err"
import sys, datetime
from youtube_transcript_api import YouTubeTranscriptApi

video_id, url, out_file = sys.argv[1], sys.argv[2], sys.argv[3]
segments = YouTubeTranscriptApi().fetch(video_id)
with open(out_file, "w") as f:
    f.write(f"# Transcript — {url}\n\n")
    f.write(f"_Fetched {datetime.date.today().isoformat()} via youtube-transcript-api._\n\n")
    f.write("## Verbatim\n\n")
    for seg in segments:
        f.write(seg.text.strip() + "\n")
print(f"wrote {out_file} ({len(segments)} segments)")
PY
RC=$?
set -e

if [[ $RC -ne 0 ]]; then
  ERR="$(cat "$OUT_DIR/.transcript_err" 2>/dev/null | tail -3 | tr '\n' ' ')"
  rm -f "$OUT_DIR/.transcript_err"
  echo "  transcript fetch failed: $ERR" >&2
  {
    echo ""
    echo "## $(date -I) — additional attempt"
    echo "- \`scripts/fetch_youtube_transcript.sh $URL\` failed: \`${ERR}\`"
  } >> "$OUT_DIR/fetch_attempts.md"
  exit $RC
fi

rm -f "$OUT_DIR/.transcript_err"
