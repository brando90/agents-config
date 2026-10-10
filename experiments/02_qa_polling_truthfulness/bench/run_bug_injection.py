#!/usr/bin/env python3
"""
run_bug_injection.py — Validate H3 (correlated blind spots): inject one
planted issue into each of N already-merged PRs, then run V1 and V2 against
the modified diff. Measure detection rate per arm and how often all 3 V1
stages miss the same case.

TLDR: Take real PR + plant a known bug + see if QA arms catch it. The
miss-rate of V1's full chain is the H3 falsifier.

Usage:
    python run_bug_injection.py --n 20 --repo ~/agents-config --out OUT_DIR
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_ac_self_audit import (  # noqa: E402
    build_worktree, cleanup_worktree,
    dispatch_v1, dispatch_v2,
    list_recent_prs, prune_stale_worktrees,
)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


# Each injector returns (modified_text, plant_description) or None if N/A.
def inject_path_typo(text: str) -> tuple[str, str] | None:
    if "scratch0" in text:
        return text.replace("scratch0", "scratch1", 1), \
               "path typo: scratch0 -> scratch1 (would break DFS resolution)"
    return None


def inject_inverted_bool(text: str) -> tuple[str, str] | None:
    m = re.search(r"\bif\s+not\s+(\w+)\s*:", text)
    if m:
        modified = text[:m.start()] + f"if {m.group(1)}:" + text[m.end():]
        return modified, f"inverted boolean: 'if not {m.group(1)}:' -> 'if {m.group(1)}:'"
    return None


def inject_off_by_factor(text: str) -> tuple[str, str] | None:
    m = re.search(r"every\s+(\d+)\s*h", text)
    if m:
        bad = str(int(m.group(1)) * 10)
        modified = text[:m.start()] + f"every {bad}h" + text[m.end():]
        return modified, f"off-by-factor: '{m.group(0)}' -> 'every {bad}h'"
    return None


def inject_bad_link(text: str) -> tuple[str, str] | None:
    m = re.search(r"\]\((https?://[^\)]+)\)", text)
    if m:
        bad = m.group(1)[:-3] + "_BROKEN"
        modified = text.replace(m.group(0), f"]({bad})", 1)
        return modified, f"broken link: {m.group(1)} -> {bad}"
    return None


def inject_wrong_citation(text: str) -> tuple[str, str] | None:
    m = re.search(r"arXiv:(\d{4}\.\d{4,5})", text)
    if m:
        bad = "9999.99999"
        modified = text.replace(m.group(0), f"arXiv:{bad}", 1)
        return modified, f"plausible-but-fake citation: {m.group(0)} -> arXiv:{bad}"
    return None


INJECTORS = [
    inject_path_typo,
    inject_inverted_bool,
    inject_off_by_factor,
    inject_bad_link,
    inject_wrong_citation,
]


def plant_in_worktree(wt: Path, rng: random.Random) -> dict | None:
    """Pick a tracked text file in wt and try injectors in random order until one fits."""
    files = []
    for ext in ("*.md", "*.py", "*.sh", "*.txt"):
        files.extend(wt.rglob(ext))
    rng.shuffle(files)
    injs = list(INJECTORS)
    rng.shuffle(injs)

    for f in files:
        if any(part.startswith(".") for part in f.parts):
            continue
        try:
            txt = f.read_text()
        except UnicodeDecodeError:
            continue
        for inj in injs:
            res = inj(txt)
            if res is None:
                continue
            new_txt, desc = res
            f.write_text(new_txt)
            return {"file": str(f.relative_to(wt)), "description": desc}
    return None


def detect_plant_in_flags(plant: dict, flags: list) -> bool:
    """A flag 'detects' the plant if it cites the same file (line-agnostic).
    Match is on path equality after normalization OR on whole-segment suffix
    (e.g., flag 'a/b/foo.py' matches plant 'b/foo.py' but NOT 'oo.py' and
    NOT plant 'foo.py' alone — the boundary char must be '/' or start)."""
    plant_path = plant["file"].lstrip("./")
    for flag in flags:
        flag_path = (flag.get("file") or "").lstrip("./")
        if not flag_path:
            continue
        if flag_path == plant_path:
            return True
        # Whole-segment suffix: flag must end with "/<plant_path>" so we don't
        # match e.g. "foo.py" inside "barfoo.py".
        if flag_path.endswith("/" + plant_path):
            return True
        # And the reverse: plant might be the longer normalized path while the
        # reviewer cited just the basename or sub-path.
        if plant_path.endswith("/" + flag_path):
            return True
    return False


def _process_pr(repo: Path, pr: dict, rng: random.Random,
                out_dir: Path) -> dict | None:
    """Run one PR through plant + V1 + V2; return record dict or None if no
    injector fit. Side-effect: writes plant_<sha>.json to out_dir."""
    sha = pr["sha"]
    wt = build_worktree(repo, sha)
    try:
        plant = plant_in_worktree(wt, rng)
        if plant is None:
            return None
        v1_stages = dispatch_v1(wt, PROMPTS_DIR / "qa_v1_polling_baseline.md")
        v2_result = dispatch_v2(wt, PROMPTS_DIR / "qa_v2_verifier_first.md")
    finally:
        cleanup_worktree(repo, wt)

    v1_flags_per_stage = [list(s.flagged_issues) for s in v1_stages]
    v1_per_stage_detected = [detect_plant_in_flags(plant, ff)
                             for ff in v1_flags_per_stage]
    record = {
        "id": sha,
        "subject": pr["subject"],
        "plant": plant,
        "v1_chain_detected": any(v1_per_stage_detected),
        "v1_per_stage_detected": v1_per_stage_detected,
        "v2_detected": detect_plant_in_flags(plant, v2_result.flagged_issues),
        "v1": {"stages": [asdict(s) for s in v1_stages]},
        "v2": asdict(v2_result),
    }
    (out_dir / f"plant_{sha[:10]}.json").write_text(json.dumps(record, indent=2))
    return record


def _write_summary(rows: list[dict], out_dir: Path) -> None:
    """Compute aggregate detection rates + write summary.md + print TLDR."""
    n = len(rows)
    v1_chain_rate = sum(r["v1_chain_detected"] for r in rows) / n
    v2_rate = sum(r["v2_detected"] for r in rows) / n
    all_miss = sum(1 for r in rows
                   if not any(r["v1_per_stage_detected"])
                   and not r["v2_detected"]) / n
    h3_status = "**FALSIFIED**" if all_miss < 0.30 else "**SUPPORTED**"
    summary_md = (
        f"# Bug-injection results\n\n"
        f"**TLDR:** N={n} PRs each given one planted issue. V1 chain "
        f"detection rate: {v1_chain_rate:.0%}. V2 detection rate: "
        f"{v2_rate:.0%}. Both arms missed: {all_miss:.0%}.\n\n"
        f'H3 ("correlated blind spots: ≥30% of plants missed by all 3 '
        f'reviewers") is {h3_status} by these data.\n'
    )
    (out_dir / "summary.md").write_text(summary_md)
    print(summary_md)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--repo", type=Path,
                    default=Path.home() / "agents-config")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    repo = args.repo.expanduser().resolve()
    prune_stale_worktrees(repo)
    rng = random.Random(args.seed)

    prs = list_recent_prs(repo, args.n * 2)  # over-sample; some lack plantable text
    summary_rows = []
    for pr in prs:
        if len(summary_rows) >= args.n:
            break
        record = _process_pr(repo, pr, rng, args.out)
        if record is None:
            continue
        summary_rows.append(record)
        sha = pr["sha"]
        print(f"[{len(summary_rows)}/{args.n}] {sha[:10]}  "
              f"v1_chain={record['v1_chain_detected']}  "
              f"v2={record['v2_detected']}", file=sys.stderr)

    if not summary_rows:
        print("no PRs accepted a plant; try --n larger", file=sys.stderr)
        return 1
    _write_summary(summary_rows, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
