# Authentication recovery and existing-credit policy review

**TLDR:** The strongest available independent reviewer found four major issues in the first draft. All four were repaired and checked deterministically; the final policy permits routine supported login recovery and authorized existing balances while preserving account identity, spending controls, scientific pins and acceptance requirements.

Last updated: 2026-09-13T19:00:52+00:00
Base policy: b58a38d2cf515941729a831a03d4db4a15777a15
Builder: Codex root recovery coordinator, gpt-6-astra / ultra.
Reviewer: fresh Codex gpt-6-astra / ultra, read-only, 600-second bound; finished September 13 at 18:48:33 UTC, exit 0. Both available Claude account routes were blocked before review (personal allowance; Vals administrator limit), so the eligible strongest same-family fallback was used. No cross-company acceptance is claimed. This is a shared policy change, not benchmark-reference acceptance.
Original reviewed patch SHA-256: 1380ba82981ff42a06c5b7027729d321528fd6001dc8a75a5b48346b713d47b4
Original verdict: FAIL; CRITICAL_ISSUES: 0; MAJOR_ISSUES: 4. The original immutable review and patch remain in the coordinator's protected local review record; this reconciliation does not replace the original verdict.

| Original finding | Applied fix and verification |
|---|---|
| Existing automatic purchases could bypass the no-new-spending restriction | Existing recharge, on-demand and postpaid routes are explicitly checked before use; unknown protection makes that route ineligible without changing billing. |
| SNAP guidance still instructed agents to copy active Mac credentials | Replaced the operative copy/re-copy recipe with supported unattended grants or independently authenticated owned profiles. |
| Wrong account could be authorized before the later identity check | Account, organization, client and requested access must match before grant approval; target verification remains afterward. |
| Global and review credit rules contradicted the user authorization | Hard Rules 8/9 and the canonical review workflow now consistently distinguish existing approved balances from new purchases. |

Final builder reconciliation: FIXED; CRITICAL_ISSUES: 0; MAJOR_ISSUES: 0; FIXES_APPLIED: 4.
Validation: original reviewer findings reconciled against the final diff; eight policy assertions passed; changed local links/anchors resolved; git diff --check passed; staged content/name secret scan passed before commit. No second model review was launched. This is a documentation policy; it does not itself install clients, a watchdog or universally renewable authentication.

Source verification: [OpenAI authentication](https://learn.chatgpt.com/docs/auth), [Cursor authentication](https://cursor.com/docs/cli/reference/authentication), [Antigravity installation/authentication](https://antigravity.google/docs/cli/install/), [OpenAI credits](https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-pluspro), [Cursor overages](https://cursor.com/help/account-and-billing/overages).
