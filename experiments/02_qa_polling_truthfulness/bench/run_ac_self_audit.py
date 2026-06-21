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
    # V2-only fields. V1 reviewers won't emit these — left at default. Per
    # qa_v2_verifier_first.md "Logging requirements", verifier_ran is the key
    # slicing variable: rows where it's "none" / [] are where the paper's
    # argument applies most cleanly (no external grounding). citations is the
    # cite-or-defer evidence list.
    verifier_ran: list | str = field(default_factory=list)
    consensus_warning: bool = False
    citations: list = field(default_factory=list)


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
    detected = detect_verifier_names(repo)
    return {
        "files_changed": files,
        "additions": adds,
        "deletions": dels,
        "languages": sorted(langs),
        "has_runnable_verifier": bool(detected),
        "detected_verifiers": detected,
    }


def detect_verifier(repo: Path) -> bool:
    """Cheap detection: is there pytest / npm test / cargo / make test runnable?"""
    return bool(detect_verifier_names(repo))


def detect_verifier_names(repo: Path) -> list[str]:
    """Same checks as detect_verifier, but returns the list of detected
    verifier names (e.g. ["pytest", "npm-test"]) so V3 logging can record
    which ones were available. Empty list = none detected."""
    found: list[str] = []
    if (repo / "pytest.ini").exists() or (repo / "pyproject.toml").exists():
        rc, _, _ = run(["python", "-c", "import pytest"], timeout_s=10)
        if rc == 0:
            found.append("pytest")
    if (repo / "package.json").exists():
        try:
            pkg = json.loads((repo / "package.json").read_text())
            if (pkg.get("scripts") or {}).get("test"):
                found.append("npm-test")
        except Exception:
            pass
    if (repo / "Cargo.toml").exists():
        found.append("cargo-test")
    mk = repo / "Makefile"
    if mk.exists() and "test:" in mk.read_text():
        found.append("make-test")
    return found


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


def prune_stale_worktrees(repo: Path) -> None:
    """Remove worktree metadata for /tmp/qapoll_* that disappeared (script
    killed mid-run). Safe to call on every startup; no-ops when nothing
    stale. Without this, repeated crashes leak `git worktree list` entries."""
    run(["git", "-C", str(repo), "worktree", "prune"], timeout_s=30)


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
    """V3: routed — markdown-only OR no-verifier source -> V2; else -> V1.
    Edge cases: empty diff (languages=[]) → all([])==True → text_only → V2
    (the cheaper failure mode, per the V3 prompt). Missing
    has_runnable_verifier defaults to False → also routes to V2.
    Output shape matches qa_v3_verifier_routed.md "Logging requirements":
    route_decision / route_reason / detected_verifiers + V1- or V2-shaped
    sub-payload."""
    languages = summary.get("languages") or []
    text_only = all(
        ext in {"md", "txt", "rst", "json", "yml", "yaml", "toml", "tex", "_none"}
        for ext in languages
    )
    detected = list(summary.get("detected_verifiers") or [])
    if text_only or not detected:
        reason = "markdown_only" if text_only else "source_no_verifier"
        result = dispatch_v2(wt, prompts_dir / "qa_v2_verifier_first.md")
        return {"route_decision": "V2", "route_reason": reason,
                "detected_verifiers": detected, "stage": asdict(result)}
    stages = dispatch_v1(wt, prompts_dir / "qa_v1_polling_baseline.md")
    return {"route_decision": "V1", "route_reason": "verifier_present",
            "detected_verifiers": detected,
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


_TEXT_FIELDS = {
    "VERDICT": "verdict",
    "CRITICAL_ISSUES": "critical_issues",
    "MAJOR_ISSUES": "major_issues",
    "FIXES_APPLIED": "fixes_applied",
    "STRUCTURAL": "structural",
    "SUMMARY": "summary",
}
_INT_FIELDS = {"critical_issues", "major_issues", "fixes_applied"}


def _apply_text_line(res: StageResult, line: str) -> None:
    """Match one VERDICT-block line against the known fields and set on res."""
    for key, attr in _TEXT_FIELDS.items():
        if not line.startswith(f"{key}:"):
            continue
        value = line.split(":", 1)[1].strip()
        if attr not in _INT_FIELDS:
            setattr(res, attr, value)
            return
        try:
            setattr(res, attr, int(value.split()[0]))
        except (ValueError, IndexError):
            pass
        return
    if line.startswith("VERIFIER_RAN:"):
        res.verifier_ran = line.split(":", 1)[1].strip()
    elif line.startswith("CONSENSUS_WARNING:"):
        v = line.split(":", 1)[1].strip().lower()
        res.consensus_warning = v in {"yes", "true", "y"}


def _apply_sidecar(res: StageResult, sidecar: dict) -> None:
    """Overlay structured fields from a JSON sidecar onto res. The sidecar
    overrides the text VERDICT lines for the V2 fields (verifier_ran,
    consensus_warning, citations) so structured forms win when present."""
    flags = sidecar.get("flagged_issues")
    if isinstance(flags, list):
        res.flagged_issues = flags
    for k in ("tokens_in", "tokens_out"):
        v = sidecar.get(k)
        if isinstance(v, int):
            setattr(res, k, v)
    vr = sidecar.get("verifier_ran")
    if isinstance(vr, (list, str)):
        res.verifier_ran = vr
    cw = sidecar.get("consensus_warning")
    if isinstance(cw, bool):
        res.consensus_warning = cw
    cites = sidecar.get("citations")
    if isinstance(cites, list):
        res.citations = cites


def _parse_verdict(reviewer: str, rc: int, out: str, err: str, dt: float) -> StageResult:
    """Parse the VERDICT block + JSON sidecar (if present) out of stdout.
    Tolerant — missing fields default to ERROR/0. The text VERDICT lines
    populate scalar fields; a fenced ```json sidecar populates richer fields
    (flagged_issues, tokens_in, tokens_out, V2's verifier_ran / citations)."""
    res = StageResult(reviewer=reviewer, wall_time_s=dt,
                      raw_stdout_tail=out[-2000:])
    for line in out.splitlines():
        _apply_text_line(res, line)
    sidecar = _extract_json_sidecar(out, err)
    if sidecar:
        _apply_sidecar(res, sidecar)
    if rc != 0 and res.verdict == "ERROR":
        res.summary = (res.summary + f" | exit={rc}").strip(" |")
    return res


def _extract_json_sidecar(out: str, err: str) -> dict | None:
    """Find the first fenced ```json block in stdout/stderr that parses to a
    dict containing 'flagged_issues' (the V1/V2 logging schema). Returns None
    if not found or unparseable. Reviewers may emit it on stderr (per the V1
    prompt) or inline in stdout."""
    for stream in (err, out):
        if not stream:
            continue
        idx = 0
        while True:
            open_fence = stream.find("```json", idx)
            if open_fence < 0:
                break
            body_start = open_fence + len("```json")
            close_fence = stream.find("```", body_start)
            if close_fence < 0:
                break
            body = stream[body_start:close_fence].strip()
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                idx = close_fence + 3
                continue
            if isinstance(parsed, dict) and "flagged_issues" in parsed:
                return parsed
            idx = close_fence + 3
    return None


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


def _audit_one_pr(repo: Path, pr: dict, prompts_dir: Path,
                  out_path: Path) -> None:
    """Run V1+V2+V3 on one PR and write the per-PR result file."""
    sha = pr["sha"]
    summary = diff_summary(repo, sha)
    wt = build_worktree(repo, sha)
    try:
        v1_stages = dispatch_v1(wt, prompts_dir / "qa_v1_polling_baseline.md")
        v2_result = dispatch_v2(wt, prompts_dir / "qa_v2_verifier_first.md")
        v3_result = dispatch_v3(wt, summary, prompts_dir)
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
    prune_stale_worktrees(repo)

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
        _audit_one_pr(repo, pr, args.prompts_dir, out_path)
        print(f"wrote {out_path}", file=sys.stderr)

    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"manifest at {args.out / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
