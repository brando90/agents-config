#!/usr/bin/env bash
# run_swe_slice.sh — Run a small SWE-bench-Verified slice with each QA arm
# wrapping a single CC builder. Compares resolved-rate, tokens, wall-clock.
#
# TLDR: Setup A (no QA), B (V1 mega-QA), C (V2 single), D (V3 routed).
# Default 20-instance stratified slice (5 easy / 10 medium / 5 hard).
#
# Usage:
#   bash run_swe_slice.sh --n 20 --out ~/dfs/qa-polling-results/swe-slice/<date>/
#
# Prereqs:
#   - SWE-bench Verified env installed locally (https://www.swebench.com)
#   - At minimum: `pip install swebench` and a runnable `swebench/harness/run_evaluation.py`
#   - clauded / codex / gemini CLIs authed for the QA arms
#   - Anthropic-credentialed CC for the builder (subscription via clauded)
#
# This script is intentionally a wrapper around the SWE-bench harness — it
# does NOT re-implement evaluation. It produces:
#   OUT/setup_A/results.json   # baseline
#   OUT/setup_B/results.json   # +V1 mega-QA
#   OUT/setup_C/results.json   # +V2 single-judge
#   OUT/setup_D/results.json   # +V3 routed
#   OUT/summary.md             # consolidated table

set -euo pipefail

N=20
OUT=""
SLICE_FILE="$(dirname "$0")/swe_slice_default.txt"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --n) N="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --slice) SLICE_FILE="$2"; shift 2 ;;
    --help|-h)
      sed -n '1,/^set -euo/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$OUT" ]]; then
  echo "ERROR: --out is required" >&2
  exit 2
fi

mkdir -p "$OUT"

# Sanity: SWE-bench installed?
if ! python -c "import swebench" 2>/dev/null; then
  cat <<EOF >&2
ERROR: swebench package not importable.
Install it once with:
  python -m pip install --user swebench
Or follow the official setup at https://www.swebench.com.
This script does NOT bootstrap SWE-bench — too many environment-specific
choices (Docker vs native, Python version, model harness).
EOF
  exit 3
fi

# Sanity: builder CLI present?
if ! command -v clauded >/dev/null 2>&1; then
  echo "ERROR: clauded not on PATH — needed as the builder." >&2
  exit 3
fi

# Sanity: SWE-bench thin wrappers present? These are NOT installed by the
# upstream swebench package — they are local helpers expected to live on PATH
# and to: (a) build a candidate patch for an instance, (b) optionally invoke a
# QA arm against the patch. If missing, every per-instance step would silently
# record builder_failed; surface the missing-tool error up front instead.
for tool in swebench-build-instance swebench-qa-instance; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    cat <<EOF >&2
ERROR: '$tool' not on PATH. This script wraps a thin local helper that is
expected to call the SWE-bench harness for one instance. Provide a script of
that name (in PATH) that accepts the documented args (see lines marked
'1. Builder' and '2. QA arm' inside this file). Without it, every instance
will be marked builder_failed.
EOF
    exit 3
  fi
done

# Default slice: 20 instance IDs sampled across difficulty deciles.
# We do NOT hard-code instance IDs here (they evolve with SWE-bench releases).
# Instead, generate the slice on first run and cache it for reproducibility.
if [[ ! -f "$SLICE_FILE" ]]; then
  echo "Generating $N-instance stratified slice (cached at $SLICE_FILE)..."
  python - "$N" "$SLICE_FILE" <<'PY'
import json, random, sys
n = int(sys.argv[1])
out = sys.argv[2]
try:
    from datasets import load_dataset
except ImportError:
    print("pip install datasets first", file=sys.stderr); sys.exit(3)
ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
# stratify on FAIL_TO_PASS length as a rough difficulty proxy
items = [(i, len(json.loads(r["FAIL_TO_PASS"])) if r.get("FAIL_TO_PASS") else 0)
         for i, r in enumerate(ds)]
items.sort(key=lambda x: x[1])
buckets = 3  # easy / medium / hard
per = [n // buckets] * buckets
for i in range(n - sum(per)):
    per[i] += 1
random.seed(42)
chosen = []
chunk = max(1, len(items) // buckets)
for b, k in enumerate(per):
    bucket = items[b*chunk : (b+1)*chunk]
    chosen.extend(random.sample(bucket, min(k, len(bucket))))
ids = [ds[i]["instance_id"] for i, _ in chosen]
with open(out, "w") as f:
    f.write("\n".join(ids))
print(f"wrote {len(ids)} instance ids -> {out}")
PY
fi

PROMPTS_DIR="$(cd "$(dirname "$0")/.." && pwd)/prompts"

run_one_setup () {
  local label="$1"
  local qa_arm="$2"      # none | v1 | v2 | v3
  local outdir="$OUT/setup_${label}"
  mkdir -p "$outdir"

  echo ">>> Setup $label (qa=$qa_arm) — writing to $outdir"

  # The harness loop: for each instance,
  #   1. clauded builder produces a patch
  #   2. if qa_arm != none, dispatch the corresponding QA prompt against the patch
  #   3. swebench harness scores the (possibly-fixed) patch
  python - "$SLICE_FILE" "$outdir" "$qa_arm" "$PROMPTS_DIR" <<'PY'
import json, os, subprocess, sys, time
from pathlib import Path

slice_path, outdir, qa_arm, prompts_dir = sys.argv[1:5]
instance_ids = Path(slice_path).read_text().strip().splitlines()
results = []
t_start = time.monotonic()

builder_prompt = (
    "You are solving a SWE-bench Verified instance. Produce a minimal git "
    "patch that resolves the issue. Use the existing test suite as your "
    "verifier. Do not introduce unrelated changes."
)

qa_prompt_path = {
    "v1": Path(prompts_dir) / "qa_v1_polling_baseline.md",
    "v2": Path(prompts_dir) / "qa_v2_verifier_first.md",
    "v3": Path(prompts_dir) / "qa_v3_verifier_routed.md",
}.get(qa_arm)

for iid in instance_ids:
    record = {"instance_id": iid, "qa_arm": qa_arm,
              "build_seconds": None, "qa_seconds": None,
              "patch_applied": False, "swebench_resolved": None}
    t0 = time.monotonic()
    # 1. Builder. We assume a thin wrapper script `swebench-build-instance`
    # has been provided locally. If not, mark instance as skipped.
    builder = subprocess.run(
        ["swebench-build-instance", iid, "--prompt", builder_prompt],
        capture_output=True, text=True, timeout=3600,
    )
    record["build_seconds"] = time.monotonic() - t0
    if builder.returncode != 0:
        record["error"] = "builder_failed"
        results.append(record); continue
    record["patch_applied"] = True

    # 2. QA arm.
    if qa_arm != "none" and qa_prompt_path and qa_prompt_path.exists():
        t1 = time.monotonic()
        qa = subprocess.run(
            ["swebench-qa-instance", iid, "--prompt-file", str(qa_prompt_path),
             "--arm", qa_arm],
            capture_output=True, text=True, timeout=3600,
        )
        record["qa_seconds"] = time.monotonic() - t1
        if qa.returncode != 0:
            record["error"] = "qa_failed"

    # 3. Score with SWE-bench harness.
    score = subprocess.run(
        ["python", "-m", "swebench.harness.run_evaluation",
         "--instance_id", iid, "--predictions_path",
         f"{outdir}/predictions.jsonl"],
        capture_output=True, text=True, timeout=1800,
    )
    record["swebench_resolved"] = "RESOLVED" in score.stdout
    results.append(record)

Path(outdir, "results.json").write_text(json.dumps(results, indent=2))
total = time.monotonic() - t_start
print(f"setup done in {total:.0f}s; {sum(1 for r in results if r['swebench_resolved'])} resolved out of {len(results)}")
PY
}

run_one_setup A none
run_one_setup B v1
run_one_setup C v2
run_one_setup D v3

# Consolidated summary
python - "$OUT" <<'PY'
import json
from pathlib import Path
import sys
out = Path(sys.argv[1])
rows = ["| setup | resolved | total | resolved_pct | mean_qa_s |", "|---|---|---|---|---|"]
for label in ("A", "B", "C", "D"):
    rp = out / f"setup_{label}" / "results.json"
    if not rp.exists():
        rows.append(f"| {label} | - | - | - | - |"); continue
    data = json.loads(rp.read_text())
    n = len(data)
    res = sum(1 for r in data if r.get("swebench_resolved"))
    qa = [r["qa_seconds"] for r in data if r.get("qa_seconds")]
    qa_mean = sum(qa)/len(qa) if qa else 0.0
    rows.append(f"| {label} | {res} | {n} | {100.0*res/n:.1f}% | {qa_mean:.0f} |")
(out / "summary.md").write_text(
    "# SWE-bench Verified slice — QA arm comparison\n\n"
    "**TLDR:** Per-setup resolved-rate on a small SWE-bench Verified slice. "
    "A = no QA, B = V1 mega-QA, C = V2 single+verifier, D = V3 routed.\n\n"
    + "\n".join(rows) + "\n"
)
print((out / "summary.md").read_text())
PY
