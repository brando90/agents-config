# Review fallback policy: implementation and review record

**TLDR:** Ordinary changes can use one disclosed, suitable smaller reviewer from the other company; critical acceptance still requires the strongest tier, and benchmark reference changes still require both families. The strongest-model review found one conflicting exception, which was fixed and checked; the smaller Claude attempt established availability but did not finish its advisory review.

**Status:** FIXED — zero unresolved critical or major findings; one quality assurance (QA) round, no re-review.
**Last updated:** 2026-09-10 17:02 PDT

## Scope and decision

Eight policy/cleanup files changed, plus this record. [Hard Rule 8](../../INDEX_RULES.md) governs defaults and acceptance; [the review workflow](../qa-correctness.md#review-fallback-and-acceptance) holds the single decision procedure. Entry points and setup guidance link to it. Obsolete launcher guidance is marked as such; the existing direct-dispatch workaround remains necessary, and no runtime launcher or global model setting was changed.

The design advice supported the ordinary/critical distinction. The implementation uses a stricter three-invocation stage limit: primary, at most one repair or smaller candidate, and one strongest-model substitute. It preserves the existing one-round default, manual-only expanded reviews, subscription-only model execution, explicit model requirements, and both-family reference-data acceptance. Company diversity is useful scrutiny, not a guarantee of independence or unchanged review quality.

## Model and attempt record

| Role | Model and effort | Evidence and outcome |
|---|---|---|
| Desktop builder/editor | `gpt-6-astra`, `xhigh` | Effective desktop task metadata, task `01a08d99-85c3-7350-8be0-df0b66578bd5`. |
| Requested design advisor | `gpt-6-astra`, `ultra` | Completed advice; model/effort verified in its local turn metadata. |
| Primary acceptance attempt | Requested `claude-fable-5-1`, `max` | Exit 1, `is_error: true`, usage-credit error, no model usage recorded; no review. This did not establish provider-wide exhaustion. |
| Optional cross-company critic | Actual `claude-opus-5`, requested/launch-verified `max` | Transcript confirms model responses and file/tool inspection. No verdict by the 15-minute limit; stopped at 17:00 PDT (approximately 16 minutes elapsed). Advisory attempt **incomplete**, not an acceptance pass. |
| Fresh acceptance reviewer | `gpt-6-astra`, `ultra` | Model/effort verified in turn metadata; original verdict FAIL, 0 critical / 1 major. Finding resolved below. |

The initial review brief described the desktop builder as `ultra`; later inspection established `xhigh`, corrected above. Both delegated Astra passes actually used the explicitly requested `ultra` setting. The reviewer's artifact coverage and selected effort were unaffected by this metadata correction.

All invocations used authenticated subscription command-line clients; no provider keys or extra paid credits were used. The advisor was a separate design task. The three review invocations belong to one review round. The acceptance reviewer saw the frozen patch without the advisor's conclusions or Opus findings. Opus reported no substantive finding before interruption; its transcript is retained, but its incomplete critique supplies no approval.

## Findings and resolution

| Finding | Resolution and verification |
|---|---|
| Astra: MAJOR — the retained exemption for any single-line configuration change could bypass critical review. | Narrowed to strictly nonbehavioral configuration edits. The exception now explicitly preserves behavior, critical-control, benchmark-reference and requested-review requirements. A one-line spending-cap or permission change still requires critical review. |
| Builder clarification — wording could suggest a failed invocation fills a review stage. | Stated explicitly that only a completed eligible review fulfills the stage. This aligns the wording with the already-reviewed stage rules. |

The two small fixes were applied and verified by the builder under Hard Rule 3. No new model-review round was launched. The original FAIL is retained here rather than represented as an unconditional reviewer PASS.

## Verification and provenance

- `git diff --check`: passed.
- Full staged-file secret scan: passed after inspecting the pre-existing `README.md:425` match; it quotes the literal environment-variable name `CLAUDE_CODE_OAUTH_TOKEN`, not a credential value.
- All 16 unique newly introduced local policy links and section anchors resolved.
- Hard Rules 3 and 9 and Trigger Rule 43 remained unchanged; a full index comparison confined changes to the four intended passages.
- The unconditional shell fallback examples and contradictory last-verdict/skip language were removed from the active review workflow.
- Reconstruction of the reviewed patch confirmed that only the two recorded post-review clarifications changed the policy afterward.
- Reviewed base: `878458fa66c7d50f8849cc9a58cf2690b0b7a709`.
- Reviewed patch SHA-256 (cryptographic fingerprint): `ff6ba04d285f7e3ece1c14e21f08ab5dfa4b8116e134f142b72eb40950f2d2e9`.
- Final policy-only patch fingerprint, excluding this record: `4b087480e6afb43806168d42efea7e12a6c76c65fffff24e6fe838d6c08a6918`.
- Local raw records: `/tmp/ac-review-fallback-artifacts-20260910/`; Astra acceptance task `01a08db6-4548-7b51-9837-d2fa63547c54`; Opus transcript `afd1498c-e736-479d-8047-7cd743638842`.

```text
VERDICT: FIXED
CRITICAL_ISSUES: 0
MAJOR_ISSUES: 0
FIXES_APPLIED: 2
STRUCTURAL: SKIP
SUMMARY: Required strongest-model review completed; findings resolved and checked. Opus availability was confirmed, but its advisory review was incomplete.
```
