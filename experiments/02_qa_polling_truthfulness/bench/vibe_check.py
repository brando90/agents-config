#!/usr/bin/env python3
"""
vibe_check.py — Surface 5 best/worst examples from ac-self-audit results
for Brando to eyeball-rate, plus an Opus-4.7 auto-judge per example so we
can later compare auto vs human and stop needing the human pass.

TLDR: Reads run_ac_self_audit.py output, ranks by V1/V2 disagreement,
writes per-example side-by-side markdowns + a pre-rating from an LLM judge.

Usage:
    python vibe_check.py --in IN_DIR --out OUT_DIR --k 5
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


JUDGE_PROMPT_TEMPLATE = """\
You are a meta-judge comparing two QA reviews of the same code diff. Decide
which review's set of flagged issues is more useful to a human maintainer.

GROUND RULES:
- "More useful" means: catches real bugs, omits false alarms, gives actionable
  citations. Cosmetic flags ("could be cleaner") count less than correctness
  flags ("this overwrites the wrong path").
- If both reviews flag mostly the same real issues, return TIE — do not break
  ties on count.
- If one review made up issues that don't exist in the diff, that's a strong
  vote against it.
- You may NOT see the ground truth. Reason from the diff and the flagged
  issues alone.

DIFF (truncated to 8k chars):
{diff}

REVIEW A flagged issues:
{a_flags}
REVIEW A summary: {a_summary}

REVIEW B flagged issues:
{b_flags}
REVIEW B summary: {b_summary}

Output exactly one of: A | B | TIE
Then a one-sentence reason.
"""


def load_results(in_dir: Path) -> list[dict]:
    records = []
    for f in sorted(in_dir.glob("pr_*.json")):
        try:
            records.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            print(f"skip malformed {f}", file=sys.stderr)
    return records


def disagreement_score(rec: dict) -> float:
    """1 - jaccard(V1, V2). Higher = more disagreement = more interesting."""
    return 1.0 - rec.get("agreement", {}).get("v1_v2_jaccard", 1.0)


def all_v1_flags(rec: dict) -> list:
    return [f for s in rec.get("v1", {}).get("stages", [])
            for f in s.get("flagged_issues", [])]


def v2_flags(rec: dict) -> list:
    return rec.get("v2", {}).get("flagged_issues", [])


def v1_summary(rec: dict) -> str:
    stages = rec.get("v1", {}).get("stages", [])
    return " | ".join(s.get("summary", "") for s in stages if s.get("summary"))


def v2_summary(rec: dict) -> str:
    return rec.get("v2", {}).get("summary", "")


def render_example(rec: dict, idx: int, ab_swap: bool) -> str:
    """Side-by-side markdown for one example. ab_swap randomizes which arm is
    labeled A vs B so the human's rating is at least order-blind."""
    arm_a, arm_b = ("v1", "v2") if not ab_swap else ("v2", "v1")
    a_flags = all_v1_flags(rec) if arm_a == "v1" else v2_flags(rec)
    b_flags = all_v1_flags(rec) if arm_b == "v1" else v2_flags(rec)
    a_sum = v1_summary(rec) if arm_a == "v1" else v2_summary(rec)
    b_sum = v1_summary(rec) if arm_b == "v1" else v2_summary(rec)
    return f"""# Example {idx:02d} — {rec.get('subject', '<no subject>')}

**TLDR:** Side-by-side QA review for SHA `{rec.get('id', '')[:10]}`.
Disagreement: jaccard distance = {disagreement_score(rec):.2f}.

## Diff summary
- files changed: {rec['diff_summary']['files_changed']}
- additions: {rec['diff_summary']['additions']}
- deletions: {rec['diff_summary']['deletions']}
- languages: {', '.join(rec['diff_summary']['languages'])}
- runnable verifier present: {rec['diff_summary']['has_runnable_verifier']}

## Review A — flagged issues
{_render_flags(a_flags)}
**Summary:** {a_sum}

## Review B — flagged issues
{_render_flags(b_flags)}
**Summary:** {b_sum}

---

## Brando's rating (fill in)

`A` / `B` / `T` (tie):

Reason (one sentence):

---

(Order is randomized: see `mapping.json` to decode.)
"""


def _render_flags(flags: list) -> str:
    if not flags:
        return "_(none)_"
    rows = []
    for f in flags[:25]:
        loc = f.get("file", "?")
        if f.get("line"):
            loc += f":{f['line']}"
        rows.append(f"- `{loc}` — {f.get('claim', '')}")
    if len(flags) > 25:
        rows.append(f"- _(+{len(flags) - 25} more)_")
    return "\n".join(rows)


def auto_judge(rec: dict, ab_swap: bool, repo: Path | None = None) -> dict:
    """Dispatch a single best-model to auto-rate which arm is more useful.
    Falls back to "no_judge_available" if no CLI is on PATH."""
    arm_a, arm_b = ("v1", "v2") if not ab_swap else ("v2", "v1")
    diff_text = ""
    if repo:
        try:
            diff_text = subprocess.run(
                ["git", "-C", str(repo), "diff",
                 f"{rec['id']}^1..{rec['id']}"],
                capture_output=True, text=True, timeout=30,
            ).stdout[:8000]
        except Exception:
            pass

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        diff=diff_text or "(diff unavailable)",
        a_flags=json.dumps(all_v1_flags(rec) if arm_a == "v1" else v2_flags(rec),
                           indent=2)[:4000],
        a_summary=v1_summary(rec) if arm_a == "v1" else v2_summary(rec),
        b_flags=json.dumps(all_v1_flags(rec) if arm_b == "v1" else v2_flags(rec),
                           indent=2)[:4000],
        b_summary=v1_summary(rec) if arm_b == "v1" else v2_summary(rec),
    )

    for cli in (["clauded", "-p"], ["codex", "exec", "--full-auto"], ["gemini", "-p"]):
        if shutil.which(cli[0]):
            try:
                proc = subprocess.run(cli + [prompt], capture_output=True,
                                      text=True, timeout=600)
                pick = _parse_judge(proc.stdout)
                return {"judge_cli": cli[0], "pick": pick,
                        "raw": proc.stdout[-500:]}
            except subprocess.TimeoutExpired:
                continue
    return {"judge_cli": "none", "pick": "no_judge_available", "raw": ""}


def _parse_judge(text: str) -> str:
    for line in text.strip().splitlines():
        token = line.strip().split()
        if token and token[0] in {"A", "B", "TIE"}:
            return token[0]
    return "unparseable"


def _extract_human_rating(text: str) -> str:
    """Pull Brando's rating out of a filled-in example_NN.md. Tolerates both
    "answer on its own line" and "answer inline after the prompt colon"
    formats. Skips the unfilled-template line itself (which contains all of
    A / B / T as backticked option markers)."""
    marker = "Brando's rating (fill in)"
    if marker not in text:
        return "unrated"
    after = text.split(marker, 1)[1]
    template_re = re.compile(r"`A`\s*/\s*`B`\s*/\s*`T`")
    inline_re = re.compile(r":\s*`?([ABT]|TIE)`?\s*$", re.IGNORECASE)
    standalone_re = re.compile(r"^\s*`?([ABT]|TIE)`?\s*$", re.IGNORECASE)
    for raw in after.splitlines():
        line = raw.rstrip()
        is_template = bool(template_re.search(line))
        m_inline = inline_re.search(line)
        if is_template and m_inline:
            token = m_inline.group(1).upper()
            return "TIE" if token == "T" else token
        if is_template:
            continue
        m_inline = inline_re.search(line)
        if m_inline:
            token = m_inline.group(1).upper()
            return "TIE" if token == "T" else token
        m_alone = standalone_re.match(line)
        if m_alone:
            token = m_alone.group(1).upper()
            return "TIE" if token == "T" else token
    return "unrated"


def write_summary(records: list[dict], out_dir: Path) -> None:
    n = len(records)
    if n == 0:
        return

    def avg(key, default=0.0):
        return sum(r["agreement"].get(key, default) for r in records) / n

    def avg_int(arm: str, field: str) -> float:
        vals = []
        for r in records:
            if arm == "v1":
                vals.extend(s.get(field, 0)
                            for s in r.get("v1", {}).get("stages", []))
            else:
                vals.append(r.get(arm, {}).get(field, 0))
        return sum(vals) / max(1, len(vals))

    summary = f"""# Vibe-check summary

**TLDR:** Averaged across {n} PRs from ac-self-audit. V1/V2 jaccard
agreement = {avg('v1_v2_jaccard'):.2f} (1 = identical flagged sets).

## Per-arm averages

| arm | avg flagged | avg fixes | avg wall_time_s |
|---|---|---|---|
| V1 (mega-QA) | {avg_int('v1', 'critical_issues') + avg_int('v1', 'major_issues'):.2f} | {avg_int('v1', 'fixes_applied'):.2f} | {avg_int('v1', 'wall_time_s'):.1f} |
| V2 (single)  | {avg_int('v2', 'critical_issues') + avg_int('v2', 'major_issues'):.2f} | {avg_int('v2', 'fixes_applied'):.2f} | {avg_int('v2', 'wall_time_s'):.1f} |

## Pairwise agreement

- V1 vs V2 jaccard: {avg('v1_v2_jaccard'):.2f}
- V1 vs V3 jaccard: {avg('v1_v3_jaccard'):.2f}
- V2 vs V3 jaccard: {avg('v2_v3_jaccard'):.2f}

A jaccard near 1.0 with V1 doing 3x the work and producing the same flagged
set is the signal the paper warns about — extra cost, no extra information.

## Next steps

1. Open each `examples/example_NN.md` and fill in your A/B/T rating.
2. Run `python vibe_check.py --score-human --in OUT_DIR` to compute
   Brando-vs-auto-judge agreement.
3. If auto-judge agreement >= 80% across 10+ examples, future rounds can
   skip the human pass and trust the auto-judge.
"""
    (out_dir / "summary.md").write_text(summary)


def cmd_main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="in_dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--repo", type=Path,
                    default=Path.home() / "agents-config")
    ap.add_argument("--score-human", action="store_true",
                    help="Re-score Brando-vs-auto agreement (after rating).")
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    examples_dir = args.out / "examples"
    examples_dir.mkdir(exist_ok=True)

    records = load_results(args.in_dir)
    if not records:
        print(f"no results in {args.in_dir}", file=sys.stderr)
        return 1

    if args.score_human:
        return _score_human(args.out)

    records.sort(key=disagreement_score, reverse=True)
    top = records[:args.k]

    mapping = {}
    auto = {}
    for i, rec in enumerate(top, start=1):
        ab_swap = (hash(rec.get("id", "")) % 2 == 0)
        md = render_example(rec, i, ab_swap)
        (examples_dir / f"example_{i:02d}.md").write_text(md)
        mapping[f"example_{i:02d}"] = {
            "id": rec.get("id"),
            "ab_swap": ab_swap,
            "arm_A": "v2" if ab_swap else "v1",
            "arm_B": "v1" if ab_swap else "v2",
        }
        auto[f"example_{i:02d}"] = auto_judge(rec, ab_swap, args.repo)

    (args.out / "mapping.json").write_text(json.dumps(mapping, indent=2))
    (args.out / "auto_judge.json").write_text(json.dumps(auto, indent=2))
    write_summary(records, args.out)
    print(f"wrote {len(top)} examples to {examples_dir}/")
    print(f"summary at {args.out / 'summary.md'}")
    return 0


def _score_human(out: Path) -> int:
    """Read human ratings from each example_NN.md, compare to auto_judge.json."""
    auto = json.loads((out / "auto_judge.json").read_text())
    mapping = json.loads((out / "mapping.json").read_text())
    rows = []
    for name, judge in auto.items():
        path = out / "examples" / f"{name}.md"
        if not path.exists():
            continue
        text = path.read_text()
        human = _extract_human_rating(text)
        rows.append({"example": name, "human": human, "auto": judge["pick"],
                     "agree": human == judge["pick"]})
    rated = [r for r in rows if r["human"] != "unrated"
             and r["auto"] not in {"no_judge_available", "unparseable"}]
    if not rated:
        print("no rated examples to score", file=sys.stderr)
        return 1
    agree_pct = 100.0 * sum(r["agree"] for r in rated) / len(rated)
    (out / "agreement.json").write_text(json.dumps(
        {"per_example": rows, "agree_pct": agree_pct,
         "n_rated": len(rated)}, indent=2))
    print(f"Brando vs auto-judge agreement: {agree_pct:.0f}% across {len(rated)} examples")
    return 0


if __name__ == "__main__":
    sys.exit(cmd_main())
