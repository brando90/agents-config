# Experiment 02 — Bench Scripts

**TLDR:** Three runners — `run_ac_self_audit.py` (cheap, repo-specific),
`run_swe_slice.sh` (medium, public benchmark), `run_bug_injection.py` (cheap,
adversarial). Each emits per-PR / per-instance JSON that `vibe_check.py`
consumes to surface 5 best/worst examples for Brando's eyeball pass.

---

## Quick start

```bash
# 1. Cheap repo-specific audit (Tier 1):
python ~/agents-config/experiments/02_qa_polling_truthfulness/bench/run_ac_self_audit.py \
    --n 10 \
    --repo ~/agents-config \
    --out ~/dfs/qa-polling-results/ac-self/$(date +%Y%m%d)/

# 2. Vibe check on the results:
python ~/agents-config/experiments/02_qa_polling_truthfulness/bench/vibe_check.py \
    --in  ~/dfs/qa-polling-results/ac-self/$(date +%Y%m%d)/ \
    --out ~/dfs/qa-polling-results/vibe/$(date +%Y%m%d)/ \
    --k 5

# 3. SWE-bench Verified slice (Tier 2, slow + expensive):
bash ~/agents-config/experiments/02_qa_polling_truthfulness/bench/run_swe_slice.sh \
    --n 20 \
    --out ~/dfs/qa-polling-results/swe-slice/$(date +%Y%m%d)/

# 4. Bug-injection (Tier 3, validates H3):
python ~/agents-config/experiments/02_qa_polling_truthfulness/bench/run_bug_injection.py \
    --n 20 \
    --repo ~/agents-config \
    --out ~/dfs/qa-polling-results/bug-injection/$(date +%Y%m%d)/
```

## Output schema

Every per-PR / per-instance result is a JSON file with:

```json
{
  "id": "<pr-number or swe-instance-id>",
  "diff_summary": {
    "files_changed": <int>,
    "additions": <int>,
    "deletions": <int>,
    "languages": ["md", "py", ...],
    "has_runnable_verifier": true | false
  },
  "v1": { ... per qa_v1_polling_baseline.md logging schema ... },
  "v2": { ... per qa_v2_verifier_first.md logging schema ... },
  "v3": { ... per qa_v3_verifier_routed.md logging schema ... },
  "timing": {
    "v1_seconds": <float>,
    "v2_seconds": <float>,
    "v3_seconds": <float>
  },
  "tokens": {
    "v1_total": <int>,
    "v2_total": <int>,
    "v3_total": <int>
  },
  "agreement": {
    "v1_v2_jaccard": <float in [0,1]>,
    "v1_v3_jaccard": <float in [0,1]>,
    "v2_v3_jaccard": <float in [0,1]>
  }
}
```

Jaccard is over `flagged_issues` lists, comparing `(file, line bucket)` pairs.

## Aggregation

`vibe_check.py` produces:

- `summary.md` — one-page table of per-arm metrics + cost ratios + win/loss/tie.
- `examples/example_NN.md` — top-K disagreement cases for human rating.
- `auto_judge.json` — Opus-4.7 pre-rating per example (which arm more useful).
- `human_rating_template.md` — pre-filled markdown for Brando to drop A/B/T.
- `agreement.json` — Brando-vs-auto-judge agreement (filled after Brando rates).

## Dependencies

Python 3.10+. `run_swe_slice.sh` additionally needs `pip install swebench
datasets` (the harness + the SWE-bench-Verified dataset loader). The
reviewer CLIs (`codex`, `clauded`, `gemini`) must be installed and authed
locally — bench scripts do not bootstrap auth.

If a CLI is unavailable, the run logs `"reviewer_unavailable": true` for
that arm and continues with the others; downstream aggregation excludes
that arm from win/loss tallies but keeps the partial result for inspection.
