---
name: sbsbz-financial-officer
description: Prepare the Stanford Bachata Sensual & Brazilian Zouk (SBSBZ) Financial Officer (FO) work so a human FO only reviews and clicks submit. Use when Brando or the FO mentions an instructor, DJ or food invoice or quote, paying an instructor, a reimbursement, GSC/ASSU funding or a GrantEd request, the club budget, balance or ledger, or "do the FO tasks". Finds the documents (a given path, Downloads, WhatsApp, Gmail, Drive), checks them against Stanford funding rules, and writes GrantEd-ready packets, corrected-invoice requests and ledger rows in a private folder.
---

# Skill: SBSBZ Financial Officer prep agent

**Doc link:** <https://github.com/brando90/agents-config/blob/main/skills/sbsbz-financial-officer/SKILL.md>

**TLDR:** Turn invoices, quotes and funding needs into packets an FO can submit in GrantEd (Stanford's student-group funding system) in minutes. The agent finds and copies the source files, extracts the facts, runs `scripts/invoice_check.py`, drafts the GrantEd fields, attachments, messages and ledger rows, and reports what blocks payment. The FO signs in and submits; nothing in this skill pays anyone.

Copies: agents-config/skills is canonical. Put a Drive copy in the Marketing folder's "Agent skills and prompts" folder (<https://drive.google.com/drive/folders/1U3EmA7i5W0O1hrDmYw37QiYi9aDxEG05>). Installed copies live in `~/.claude/skills/sbsbz-financial-officer/` and `~/.codex/skills/sbsbz-financial-officer/`; these are managed links to the canonical agents-config skill, not independent copies.

## Limits that bind
- **The FO submits.** GrantEd needs the FO's own SUNet login and completed training, so agents prepare exact field values and attachments and stop there. Agents never sign in with someone's credentials. They never submit GrantEd funding or payment requests or assuepay payments, and never send money (Venmo, Zelle, bank). Brando or the FO does those steps.
- **Messages are drafts until Brando says "send".** When he does, follow the club email copy rule in `CLAUDE.md` (BCC `brandojazz@gmail.com` and `brando9@stanford.edu`).
- **The repository is public.** Invoices, chat extracts, payee contact or tax details, statements, balances and receipts go in `events/MM-DD-YYYY-fo-<task>/private/`. Give that folder a `.gitignore` containing `private/`, and confirm it with `git check-ignore`. Commit only skill or process changes.
- **Chats are personal.** Extract finance facts only (date, chat name, amount, who taught, who paid), never surrounding conversation.

## Current state (re-verify every run)
As of 10-09-2026 the FO role is in transition. Read the newest "Team responsibilities" doc and the officers chat before naming the FO. Lorena's guide says the President cannot be the FO; check with Stanford Student Enterprises (SSE) before Brando takes the role. Balances in old exports are stale: ask the FO for a fresh GrantEd statement before quoting any number.

## Finding the inputs
1. **A path Brando gives, or `~/Downloads`** (`ls -t ~/Downloads | head`). The same invoice often also sits in WhatsApp. Compare `shasum -a 256` and keep one copy.
2. **WhatsApp desktop data**, read-only:
   ```bash
   W=$(ls ~/agents-config/skills/sbsbz-financial-officer/scripts/wa_finance_find.py ~/.claude/skills/sbsbz-financial-officer/scripts/wa_finance_find.py ~/.codex/skills/sbsbz-financial-officer/scripts/wa_finance_find.py 2>/dev/null | head -1)
   python3 $W --list-chats "<payee first name>"
   python3 $W --chat "Awesome <Name>" --chat "<Name> 1:1 chat name" --since YYYY-MM-DD --copy-to ~/sbsbz/events/MM-DD-YYYY-fo-<payee>/private/source
   ```
   It queries a temporary copy of `ChatStorage.sqlite`, prints only attachments and finance keyword hits, copies the media and writes `manifest.json` with SHA-256 hashes. If a file "is not downloaded on this Mac", open that chat in the WhatsApp app through background computer use (`net.whatsapp.WhatsApp`) and download it. Useful chats: "SBSZ Official Officers Chat", the FO's 1:1 chat, and per-instructor groups named `Awesome <Name> Bachata Teacher (…)`. Captions matter: an instructor's rate can sit in the caption of a rate-sheet image rather than in the image.
3. **Email:** Gmail and Stanford Outlook connectors. Search `invoice`, `quote`, `GrantEd`, `GSC funding`, `banking@sse.stanford.edu`.
4. **Drive:** see `references/sources.md` for the onboarding guide, the statement export and the Accounting sheet.

## Workflow A: an invoice or quote arrives (most common)
1. Make `events/MM-DD-YYYY-fo-<payee>/` with the `.gitignore`, then copy the sources into `private/source/` (step above).
2. Read the invoice: run `pdftotext -layout`, render it with `pdftoppm -r 70 -png -singlefile` and look at the page; open images directly.
3. From the chats and the FO, collect: the agreed rate and the message it came from, each date taught, who actually taught (announcements are sometimes wrong), what was already paid and by whom, and the funding status.
4. Write `private/<payee>-<MM-DD-YYYY>-facts.json` following `references/invoice-facts.example.json`. Unknown values stay `null`; never guess.
5. Run `python3 scripts/invoice_check.py private/<facts>.json --out private/<payee>-check-report.md`. Exit 2 means blocked, 1 means fixes needed, 0 means no fixes. The verdict also says whether the next step is a funding request, waiting for approval, or FO review of the payment.
6. Write `private/packet.md` containing:
   - the verdict and findings
   - the GrantEd draft
   - the status of each attachment
   - a drafted corrected-invoice request to the payee
   - a drafted handoff to the FO
   - the Accounting-sheet rows to add
   - questions only Brando can answer
7. Report to Brando in a few lines: the verdict, the fixes, the decisions he owns, and the drafts awaiting his "send".

**A submittable invoice has:**

- the payee's legal name, a working email and a phone number
- an invoice number and an invoice date
- "Billed to: Stanford Bachata Sensual & Brazilian Zouk (SBSBZ), VSO account 5089, Stanford University"
- **one session per invoice** with its service date, a description ("Guest dance instruction, SBSBZ weekly Bachata class, MM-DD-YYYY") and the agreed rate
- no Venmo, Zelle or cash instructions: Stanford pays outside payees by check (mail or pickup) after they return the W-9 that GrantEd emails them
- PDF format

Ask for future sessions' invoices at least a month ahead. A recurring outside instructor also needs OSE's non-student registration: the Non-Student Involvement Form, a HireRight background check and Core 10 training (policy P9). Start it with the first invoice.

## Workflow B: GSC Quick Grant packet (monthly)
Build it from the class plan (dates × instructor × agreed rate) and any social quotes:

- One funding line per session or expense, each in the right account.
- Keep each application under $1,000; split by month.
- Submit at least one month ahead (ASSU). GSC itself needs 3 weekly meetings for ≤$500 and 4 for ≤$1,000.
- GSC's weekly cutoff is Sunday 5 PM.
- List every session on the GSC Funding Calendar at least 14 days ahead (mandatory).
- Fill the answers from `references/gsc-quick-grant-answers.md` with measured attendance.
- Plan a sign-in sheet with names and emails at every session.

Output: `private/grant-packet-<month>.md`, ready to paste.

## Workflow C: payment request after the session
Before paying, all of these must hold:

- approved funding covering that date, since unapproved payment requests are rejected
- a written agreement on the amount (an email or text thread)
- a corrected, itemized invoice
- the attendance list
- the payee's correct email (for the W-9 request), and OSE registration if they teach regularly

The `invoice_check.py` draft holds the field values: Service Payment, vendor, service date, amount, account, description, attachments. After the FO submits, confirm with the payee that payment arrived and add the ledger row.

## Workflow D: someone paid out of pocket
Collect itemized receipts and proof of payment, and match each to an approved funding line. Without prior approval, expect rejection: say so. Paying a person for a service by Venmo, Zelle or Apple Cash is not allowed, so those payments are not reimbursable (policy P3). Never let Stanford pay a vendor whom an organizer already paid for the same session.

## Workflow E: ledger and status digest (monthly, or when asked)
Compare the newest GrantEd statement export with the Accounting sheet. List:

- open applications and their status
- approved but unspent allocations, which are taken back after June 30
- pending payments
- money owed to organizers
- the next deadlines

Write `private/status-MM-DD-YYYY.md` and send Brando or the FO a five-line summary.

## Rules
`references/policy.md` lists each rule with its source and whether it is official or from club notes. Cite the source when a rule decides an outcome.

## Lessons
- 10-09-2026, first test on a guest instructor's invoice for a 10-01-2026 class: five fixes and five checks.

  The fixes:
  - email truncated to `.co`, which would misroute the W-9 request
  - club named "SBKZ"
  - Venmo/Zelle payment instructions
  - no OSE registration for a recurring instructor
  - no attendance list

  The session had passed with no approved funding, and the organizer had already paid by Venmo, which cannot be reimbursed. Ask instructors for one invoice per future session at least a month ahead, using the template above.
- 09-2026: GSC approved only half of a request because a photo is not an attendee list.
- 09-23-2026: a $1,000 request for a 10-02-2026 party, sent nine days ahead, was not decided in time.
- 06-30-2025: GSC took back unspent allocations at fiscal-year end.

## Copy-paste prompt (Claude, Codex or ChatGPT agent on Brando's Mac)

> Act as the prep agent for the Stanford Bachata Sensual & Brazilian Zouk (SBSBZ) Financial Officer. Read `~/agents-config/skills/sbsbz-financial-officer/SKILL.md`; use `~/sbsbz` as the work repository and follow it for: [the invoice/quote/funding task]. Find the source files (a path I give, `~/Downloads`, WhatsApp via `scripts/wa_finance_find.py`, email, Drive) and copy them into `events/MM-DD-YYYY-fo-<task>/private/`, which is gitignored. Extract the facts, run `scripts/invoice_check.py`, and write `private/packet.md` with the GrantEd field values, attachments, drafted messages and ledger rows. The FO signs in to GrantEd and submits; you never sign in, submit, pay or send messages unless I say send. Keep chat content and payee details out of git. Report the verdict, the fixes and the decisions I need to make.
