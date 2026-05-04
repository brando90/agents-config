#!/usr/bin/env python3
"""
run_ac_self_audit.py — Replay recent agents-config PRs through V1 / V2 / V3
QA prompts, log per-PR JSON results.

TLDR: Sample N most-recent merged PRs, recreate the diff in a temp worktree,
dispatch each QA arm against it, log results for vibe_check.py.

Usage:
    python run_ac_self_audit.py --n 10 --repo ~/agents-config --out OUT_DIR

Notes:
    - Reviewer CLIs (codex, clauded, gemini) must be on $PATH and authed.
    - If a CLI is missing or fails, the arm is recorded as
      reviewer_unavailable=true and skipped. Other arms still run.
    - Results are written to OUT_DIR/pr_<num>.json (one file per PR) plus
      OUT_DIR/manifest.json listing all PRs and their result files.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

PROMPTS_DIR = (
    Path(__file__).resolve().parent.parent / "prompts"
)


@dataclass
class StageResult:
    reviewer: str
    verdict: str = "ERROR"
    critical_issues: int = 0
    major_issues: int = 0
    fixes_applied: int = 0
    structural: str = "SKIP"
    summary: str = ""
    flagged_issues: list = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    wall_time_s: float = 0.0
    reviewer_unavailable: bool = False
    raw_stdout_tail: str = ""


def run(cmd: list[str], cwd: Path | None = None, timeout_s: int = 1800) -> tuple[int, str, str]:
    """Run a subprocess, return (rc, stdout, stderr). Captures stderr separately."""
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def list_recent_prs(repo: Path, n: int) -> list[dict]:
    """Approximate "recent PR" by listing merges first; fall back to recent
    commits on main whose subject ends in `(#NN)` (squash-merged PRs);
    final fallback: last N commits on main, period.

    The diff for each item is `sha^1..sha`, so squash-merge commits work
    too — their parent is the pre-merge main tip."""
    candidates = [
        ["git", "-C", str(repo), "log", "--merges", "--first-parent",
         "main", f"-n{n}", "--pretty=format:%H%x09%s"],
        ["git", "-C", str(repo), "log", "main", f"-n{n * 4}",
         "--grep=(#[0-9]+)$", "-E", "--pretty=format:%H%x09%s"],
        ["git", "-C", str(repo), "log", "main", f"-n{n}",
         "--pretty=format:%H%x09%s"],
    ]
    for cmd in candidates:
        rc, out, _ = run(cmd)
        if rc != 0:
            continue
        prs = []
        for line in out.strip().splitlines():
            if not line:
                continue
            sha, subject = line.split("\t", 1)
            prs.append({"sha": sha, "subject": subject})
        if prs:
            return prs[:n]
    return []


def diff_for_merge(repo: Path, sha: str) -> str:
    """Return the diff that the merge commit introduced (vs its first parent)."""
    rc, out, _ = run(
        ["git", "-C", str(repo), "diff", f"{sha}^1..{sha}"],
    )
    return out if rc == 0 else ""


def diff_summary(repo: Path, sha: str) -> dict:
    rc, out, _ = run(
        ["git", "-C", str(repo), "diff", "--numstat", f"{sha}^1..{sha}"],
    )
    files, adds, dels, langs = 0, 0, 0, set()
    if rc == 0:
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            a, d, fn = parts
            files += 1
            try:
                adds += int(a)
                dels += int(d)
            except ValueError:
                pass
            ext = Path(fn).suffix.lstrip(".") or "_none"
            langs.add(ext)
    return {
        "files_changed": files,
        "additions": adds,
        "deletions": dels,
        "languages": sorted(langs),
        "has_runnable_verifier": detect_verifier(repo),
    }


def detect_verifier(repo: Path) -> bool:
    """Cheap detection: is there pytest / npm test / cargo / make test runnable?"""
    if (repo / "pytest.ini").exists() or (repo / "pyproject.toml").exists():
        rc, _, _ = run(["python", "-c", "import pytest"], timeout_s=10)
        if rc == 0:
            return True
    if (repo / "package.json").exists():
        try:
            pkg = json.loads((repo / "package.json").read_text())
            if (pkg.get("scripts") or {}).get("test"):
                return True
        except Exception:
            pass
    if (repo / "Cargo.toml").exists():
        return True
    mk = repo / "Makefile"
    if mk.exists() and "test:" in mk.read_text():
        return True
    return False


def build_worktree(repo: Path, sha: str) -> Path:
    """Create a throwaway worktree at the merge commit so reviewers see the
    state as it landed. Caller must delete when done."""
    wt = Path(tempfile.mkdtemp(prefix="qapoll_"))
    rc, _, err = run(
        ["git", "-C", str(repo), "worktree", "add", "--detach", str(wt), sha],
    )
    if rc != 0:
        shutil.rmtree(wt, ignore_errors=True)
        raise RuntimeError(f"worktree add failed: {err}")
    return wt


def cleanup_worktree(repo: Path, wt: Path) -> None:
    run(["git", "-C", str(repo), "worktree", "remove", "--force", str(wt)])
    shutil.rmtree(wt, ignore_errors=True)


def cli_available(name: str) -> bool:
    return shutil.which(name) is not None


def dispatch_v1(wt: Path, prompt_path: Path) -> list[StageResult]:
    """V1 mega-QA: Codex -> CC -> Gemini sequential."""
    chain = [
        ("codex", ["codex", "exec", "--full-auto", _read_v1_stage_prompt(prompt_path)]),
        ("cc",    ["clauded", "-p", _read_v1_stage_prompt(prompt_path)]),
        ("gemini",["gemini", "-p", _read_v1_stage_prompt(prompt_path)]),
    ]
    results = []
    for reviewer, cmd in chain:
        if not cli_available(cmd[0]):
            results.append(StageResult(reviewer=reviewer, reviewer_unavailable=True,
                                       summary="CLI not on PATH"))
            continue
        t0 = time.monotonic()
        try:
            rc, out, err = run(cmd, cwd=wt, timeout_s=1800)
        except subprocess.TimeoutExpired:
            results.append(StageResult(reviewer=reviewer, verdict="ERROR",
                                       summary="timeout", wall_time_s=1800))
            continue
        dt = time.monotonic() - t0
        results.append(_parse_verdict(reviewer, rc, out, err, dt))
    return results


def dispatch_v2(wt: Path, prompt_path: Path) -> StageResult:
    """V2: single best-model + verifier-first."""
    prompt = _read_v2_prompt(prompt_path)
    candidates = [
        ("cc",     ["clauded", "-p", prompt]),
        ("codex",  ["codex", "exec", "--full-auto", prompt]),
        ("gemini", ["gemini", "-p", prompt]),
    ]
    for reviewer, cmd in candidates:
        if cli_available(cmd[0]):
            t0 = time.monotonic()
            try:
                rc, out, err = run(cmd, cwd=wt, timeout_s=2400)
            except subprocess.TimeoutExpired:
                return StageResult(reviewer=reviewer, verdict="ERROR",
                                   summary="timeout", wall_time_s=2400)
            return _parse_verdict(reviewer, rc, out, err,
                                  time.monotonic() - t0)
    return StageResult(reviewer="none", reviewer_unavailable=True,
                       summary="no reviewer CLI available")


def dispatch_v3(wt: Path, summary: dict, prompts_dir: Path) -> dict:
    """V3: routed — markdown-only OR no-verifier source -> V2; else -> V1."""
    text_only = all(
        ext in {"md", "txt", "rst", "json", "yml", "yaml", "toml", "tex", "_none"}
        for ext in summary["languages"]
    )
    if text_only or not summary["has_runnable_verifier"]:
        route, reason = "V2", "markdown_only" if text_only else "source_no_verifier"
        result = dispatch_v2(wt, prompts_dir / "qa_v2_verifier_first.md")
        return {"route_decision": route, "route_reason": reason,
                "stage": asdict(result)}
    route, reason = "V1", "verifier_present"
    stages = dispatch_v1(wt, prompts_dir / "qa_v1_polling_baseline.md")
    return {"route_decision": route, "route_reason": reason,
            "stages": [asdict(s) for s in stages]}


_V1_RE_BLOCK = "Per-stage prompt"
_V2_RE_BLOCK = "Per-run prompt"


def _read_v1_stage_prompt(path: Path) -> str:
    """Pull the verbatim block from prompts/qa_v1_polling_baseline.md."""
    return _extract_code_block(path, "Per-stage prompt")


def _read_v2_prompt(path: Path) -> str:
    return _extract_code_block(path, "Per-run prompt")


def _extract_code_block(path: Path, header_substr: str) -> str:
    text = path.read_text()
    parts = text.split(header_substr, 1)
    if len(parts) < 2:
        raise RuntimeError(f"header '{header_substr}' not found in {path}")
    after = parts[1]
    fence_open = after.find("```")
    if fence_open < 0:
        raise RuntimeError(f"no code fence after '{header_substr}' in {path}")
    fence_close = after.find("```", fence_open + 3)
    if fence_close < 0:
        raise RuntimeError(f"unterminated code fence after '{header_substr}' in {path}")
    block = after[fence_open + 3:fence_close]
    if "\n" in block:
        block = block.split("\n", 1)[1]
    return block.strip()


def _parse_verdict(reviewer: str, rc: int, out: str, err: str, dt: float) -> StageResult:
    """Parse the VERDICT block out of stdout. Tolerant — missing fields
    default to ERROR/0."""
    res = StageResult(reviewer=reviewer, wall_time_s=dt,
                      raw_stdout_tail=out[-2000:])
    fields = {
        "VERDICT": "verdict",
        "CRITICAL_ISSUES": "critical_issues",
        "MAJOR_ISSUES": "major_issues",
        "FIXES_APPLIED": "fixes_applied",
        "STRUCTURAL": "structural",
        "SUMMARY": "summary",
    }
    for line in out.splitlines():
        for key, attr in fields.items():
            if line.startswith(f"{key}:"):
                value = line.split(":", 1)[1].strip()
                if attr in {"critical_issues", "major_issues", "fixes_applied"}:
                    try:
                        setattr(res, attr, int(value.split()[0]))
                    except (ValueError, IndexError):
                        pass
                else:
                    setattr(res, attr, value)
    if rc != 0 and res.verdict == "ERROR":
        res.summary = (res.summary + f" | exit={rc}").strip(" |")
    return res


def jaccard(a: list, b: list, line_window: int = 10) -> float:
    """Tolerant Jaccard: a flag in A matches a flag in B iff same file and
    |line_a - line_b| <= line_window (default 10). Avoids the
    fixed-bucket-boundary problem where lines 47 and 51 map to different
    buckets despite being adjacent."""
    if not a and not b:
        return 1.0
    matched_b = set()
    matches = 0
    for fa in a:
        for j, fb in enumerate(b):
            if j in matched_b:
                continue
            if fa.get("file") != fb.get("file"):
                continue
            la = fa.get("line") or 0
            lb = fb.get("line") or 0
            if abs(la - lb) <= line_window:
                matched_b.add(j)
                matches += 1
                break
    union = len(a) + len(b) - matches
    return matches / max(1, union)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=10, help="number of recent PRs")
    ap.add_argument("--repo", type=Path,
                    default=Path.home() / "agents-config")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--prompts-dir", type=Path, default=PROMPTS_DIR)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    repo = args.repo.expanduser().resolve()

    prs = list_recent_prs(repo, args.n)
    if not prs:
        print("no PRs found", file=sys.stderr)
        return 1

    manifest = []
    for pr in prs:
        sha = pr["sha"]
        out_path = args.out / f"pr_{sha[:10]}.json"
        manifest.append({"sha": sha, "subject": pr["subject"],
                         "result_file": out_path.name})
        if out_path.exists():
            print(f"skip {sha[:10]} (cached)", file=sys.stderr)
            continue

        summary = diff_summary(repo, sha)
        wt = build_worktree(repo, sha)
        try:
            v1_stages = dispatch_v1(wt, args.prompts_dir / "qa_v1_polling_baseline.md")
            v2_result = dispatch_v2(wt, args.prompts_dir / "qa_v2_verifier_first.md")
            v3_result = dispatch_v3(wt, summary, args.prompts_dir)
        finally:
            cleanup_worktree(repo, wt)

        v1_flags = [f for s in v1_stages for f in s.flagged_issues]
        v2_flags = list(v2_result.flagged_issues)
        v3_flags = (v3_result.get("stage", {}).get("flagged_issues")
                    or [f for s in v3_result.get("stages", [])
                        for f in s.get("flagged_issues", [])])

        record = {
            "id": sha,
            "subject": pr["subject"],
            "diff_summary": summary,
            "v1": {"stages": [asdict(s) for s in v1_stages]},
            "v2": asdict(v2_result),
            "v3": v3_result,
            "agreement": {
                "v1_v2_jaccard": jaccard(v1_flags, v2_flags),
                "v1_v3_jaccard": jaccard(v1_flags, v3_flags),
                "v2_v3_jaccard": jaccard(v2_flags, v3_flags),
            },
        }
        out_path.write_text(json.dumps(record, indent=2))
        print(f"wrote {out_path}", file=sys.stderr)

    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"manifest at {args.out / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
