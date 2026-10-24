# SBSBZ finance sources

**Doc link:** <https://github.com/brando90/agents-config/blob/main/config/pi/skills/sbsbz-financial-officer/references/sources.md>

**TLDR:** Where each financial fact lives. The Google Drive files are access-controlled; read them with the Drive connector (`read_file_content` with the ID). Their contents (balances, payees, receipts) stay out of this public repository.

| Source | Drive ID or location | Use it for |
|---|---|---|
| Onboarding FO (Financial Officer), Lorena, 02-2026 | `1kyxm6J_28wgZreomZn2FR88lxKgTb4THZwDoe622jfQ` | FO duties, training, GSC Quick Grant walk-through, pre-written answers. Payment screenshots are images; open the doc to see them. |
| Monthly meeting agenda (FO meeting 05-03-2026 and earlier) | `1Qgkj4RJfC7jVfNkHUs_s4jkXVLVWOu9Vq_GcEVVfFHc` | Payment workflow (quote → acceptance → Service Payment), monthly <$1,000 strategy, assuepay steps for outside payers. The 05-03 meeting has a Fathom recording; pull the verbatim transcript if a step is unclear. |
| VSO account statement export (02-04-2026) | `1fFJSlSSQkgQDdWeUkkNEIaub_pDK_nSQ` | Official account lines and every past funding/payment description (templates). Stale; ask the FO for a fresh export from GrantEd. |
| Accounting (club cash ledger) | `1PqVZQtfMzTWpx7RxNWxNGsXHmuDjWlD9llgDK7Rde7s` | Out-of-pocket and cash/Venmo history. Has `#REF!` cells and mixed date formats; append rows, do not rewrite history. |
| SBSBZ — Team responsibilities & next steps (09-13-2026) | `1ENOiPhiavd7RLFnDDcqmJkcJRsvVZWmtst_vVhKxi4g` | Who the officers are and the FO's open tasks. |
| SBSBZ constitution | `1an7OtMuhlXnpJe6X_ESOOhW1rOcfPuoTYLZwuhWFBTk` | FO is an elected officer (President, VP, FO). |
| Financial Officer roles & tips (2024) | `1EPeOk8cGtrUkGJ7uH93tgvmlocybncJ_OoiU-fSonKI` | Older notes; GSC Sunday 5 PM deadline. |
| Transition Planner (Dan, 09-2026) | `1AluJjlK204Xi0ehbdKHNXitXNRfTUBmrmy-a7muNuOA` | Tango Club advice: university rules on outside payments. |
| Arts grant draft | repo `docs/funding/bachata-arts-grant-draft.md` | Non-GSC grant routes and budget-worksheet rules. |
| WhatsApp | local desktop data via `scripts/wa_finance_find.py` | Invoices, rate sheets and FO updates: "SBSZ Official Officers Chat", the FO's 1:1 chat, and per-instructor groups named `Awesome <Name> Bachata Teacher (…)`. |
| Email | Gmail / Stanford Outlook connectors | GrantEd notifications, `banking@sse.stanford.edu`, GSC replies, emailed quotes. |
| Official rules | GrantEd Help Center <https://sse.frontkb.com/en>; GSC grants <https://www.assu.stanford.edu/206/Graduate-VSO-Grants>; ASSU funding <https://www.assu.stanford.edu/196/ASSU-Funding> | Authoritative policy; see `policy.md`. |
| Community payments | <https://assuepay.stanford.edu/> (payer → make a payment → club name or group ID) | How outside members pay the club officially. The payer does this; agents never pay. |
