# QA Prompt v3 — Verifier-Routed (Adaptive Arm)

**TLDR:** Inspect the diff first; route to V1 (mega-QA) when an external
verifier exists and is runnable, otherwise to V2 (single-judge +
cite-or-defer). The hypothesis is that mega-QA pays off only in the
verifier-anchored regime, so the optimal default is to spend the cross-model
budget there and not on prose.

---

## Routing rule

Run this routing check **before** dispatching any reviewer. The routing
decision and its reason go in the final report.

```
def route(diff) -> "V1" | "V2":
    # 1. If diff touches no source code (markdown / config / docs only) → V2.
    if all(f.suffix in {".md", ".txt", ".rst", ".json", ".yml", ".yaml",
                        ".toml", ".tex"} for f in diff.files_changed):
        return "V2"  # no verifier possible — paper applies → single + cite

    # 2. If diff touches source code AND a runnable verifier exists in repo
    #    (pytest / npm test / cargo / etc.) → V1.
    if has_runnable_verifier(repo) and diff.touches_source():
        return "V1"  # verifier-anchored → mega-QA budget pays off

    # 3. Mixed or no-verifier source code → V2 with structural metrics as
    #    partial verifier (radon / lint / type-check) + citations.
    return "V2"
```

`has_runnable_verifier(repo)` is true if **any** of:
- `pytest --collect-only -q` exits 0 with non-zero collected count
- `package.json` has a `test` script and `npm test --silent --listTests`
  reports tests
- `Cargo.toml` exists and `cargo test --no-run` succeeds
- `go test ./... -run XXXXX` (filter to none) exits 0
- A `Makefile` has a `test` target that exits 0 on `make -n test`

Detection should not actually run the suite, just verify it's runnable. The
selected reviewer (V1 or V2) actually runs it.

---

## When V3 sends to V1

Use the V1 prompt and chain (`prompts/qa_v1_polling_baseline.md`) verbatim,
**plus** prepend this preamble:

```
ROUTING NOTE: This diff was routed to V1 (mega-QA chain) because a runnable
external verifier exists in this repo: <list of verifiers>. Each stage MUST
run at least one of these verifiers before producing a verdict. Stages that
skip verification are downgraded to DEFER.
```

The "skip → DEFER" rule is the only behavior change V3 introduces to V1; it
closes V1's main weakness (skipped tests).

---

## When V3 sends to V2

Use V2 (`prompts/qa_v2_verifier_first.md`) verbatim — no preamble change.
V2's "verifier first; cite or defer" already covers this case.

---

## Logging requirements

```json
{
  "route_decision": "V1" | "V2",
  "route_reason": "markdown_only" | "verifier_present" | "source_no_verifier",
  "detected_verifiers": ["pytest", "npm-test", ...] | [],
  ...                  # plus the V1- or V2-shaped fields per the chosen path
}
```

---

## Why this is not just "always run V1"

The paper's argument: in the verifier-absent regime, paying 3× compute for 3
correlated judges does not buy verification — it buys ratifications. So for
markdown/config/prose diffs (a large fraction of agents-config PRs), V3
saves ⅔ the cost while plausibly preserving the marginal value of the
extra stages (which the paper says is small in this regime).

In the verifier-present regime, the extra stages each get to *use* the
verifier independently, so their compute does buy real additional checks.
That's where V3 keeps V1.

The routing decision can be wrong in either direction; both errors are
recoverable:
- **Routed to V2 but should have been V1:** Brando catches a missed bug in
  review and re-runs as `mega-qa` explicitly.
- **Routed to V1 but should have been V2:** the only cost is ~2× extra
  tokens and time. No quality loss.

So the routing rule is conservative: when in doubt about whether a verifier
exists, prefer V2 (the cheaper failure mode).

---

## Open question

Do we want a third tier "DEEP" for high-stakes diffs (security-sensitive,
schema migrations, evaluation-metric changes) that runs V1 *and* V2 and
escalates on disagreement? Worth considering after Tier 1 results land. For
now, V3's two-way routing is the minimum viable adaptive policy.
