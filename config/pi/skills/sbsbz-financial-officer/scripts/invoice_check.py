#!/usr/bin/env python3
"""Check an instructor/vendor invoice against SBSBZ Financial Officer rules and draft the GrantEd packet.

Input: a JSON file of facts the agent extracted from the invoice and the chats (see
../references/invoice-facts.example.json). Output: a Markdown report with one line per check
(BLOCK = cannot be submitted as is, FIX = needs a correction, CHECK = a person must confirm,
OK = passed), then the field values an FO would type into GrantEd. Nothing is submitted.
Rule sources are in ../references/policy.md (KB = sse.frontkb.com/en/articles/<id>).

  invoice_check.py facts.json [--today YYYY-MM-DD] [--out report.md]
Exit code: 2 if any BLOCK, 1 if any FIX, else 0.
"""
import argparse
import datetime as dt
import json
import re
import sys

ORDER = {"BLOCK": 0, "FIX": 1, "CHECK": 2, "OK": 3}
PRIVATE_PAY = re.compile(r"venmo|zelle|paypal|cash ?app|apple cash|\bcash\b", re.I)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)
TRUNCATED_DOMAINS = {"gmail.co", "yahoo.co", "hotmail.co", "outlook.co", "icloud.co"}
INELIGIBLE = {"postdoc", "student", "staff", "faculty", "officer"}


def d(s):
    return dt.datetime.strptime(s, "%Y-%m-%d").date() if s else None


def check(f, today):
    out = []
    add = lambda level, msg: out.append((level, msg))
    payee, inv = f.get("payee", {}), f.get("invoice", {})
    agree, fund = f.get("agreement", {}), f.get("funding", {})
    ev, oop = f.get("evidence", {}), f.get("paid_out_of_pocket") or {}
    lines = inv.get("lines", [])

    # Payee identity, tax form and eligibility
    for key in ("name", "email"):
        if not payee.get(key):
            add("FIX", f"Payee {key} missing on the invoice.")
    email = payee.get("email", "")
    if email and (not EMAIL.match(email) or email.split("@")[-1].lower() in TRUNCATED_DOMAINS):
        add("FIX", f"Payee email `{email}` looks invalid or truncated (.co for .com?). GrantEd emails the W-9 "
                   "request to this address, so it must be right (KB 8112129).")
    if not payee.get("w9_on_file"):
        add("CHECK", "W-9 not yet on file. When the FO enters the payee's name and email in GrantEd, the payee is "
                     "emailed a W-9 request; payment waits for it (KB 8112065, 8112129).")
    aff = (payee.get("stanford_affiliation") or "unknown").lower()
    if aff in INELIGIBLE:
        add("BLOCK", f"Payee is a Stanford {aff}. GSC honoraria cannot pay postdocs, students, faculty or visiting "
                     "scholars, and officers may not be paid for normal club activities. Get written SSE guidance first.")
    elif aff == "unknown":
        add("CHECK", "Payee's Stanford affiliation unknown; confirm they are not a student, postdoc, staff member "
                     "or club officer.")
    else:
        add("OK", f"Payee affiliation recorded as `{aff}`.")
    if payee.get("ongoing_instructor") and not payee.get("nonstudent_registration_done"):
        add("FIX", "Recurring outside instructor: OSE requires the Non-Student Involvement Form (CardinalEngage), a "
                   "HireRight background check and Core 10 training for an ongoing coach/instructor (OSE non-student "
                   "framework). Start it now; it is separate from payment.")

    # Invoice content
    billed = inv.get("billed_to", "")
    if not re.search(r"sbsbz|5089|bachata sensual", billed, re.I):
        add("FIX", f"Billed-to does not name the club correctly (`{billed.strip()[:80]}`). Use "
                   "'Stanford Bachata Sensual & Brazilian Zouk (SBSBZ), VSO account 5089, Stanford University'.")
    if not inv.get("number"):
        add("FIX", "Invoice number missing.")
    if PRIVATE_PAY.search(inv.get("payment_instructions", "")):
        add("FIX", "Invoice asks for Venmo/Zelle/cash. Stanford pays outside payees by check (mail or pickup) after "
                   "the W-9, and peer-to-peer apps are not allowed for services (KB 8112129, 2852097). Remove the line.")
    total = sum(float(l.get("amount", 0)) for l in lines)
    for l in lines:
        if abs(float(l.get("qty", 1)) * float(l.get("rate", 0)) - float(l.get("amount", 0))) > 0.005:
            add("FIX", f"Line '{l.get('description', '')[:40]}': qty x rate != amount.")
    if inv.get("total") is not None and abs(total - float(inv["total"])) > 0.005:
        add("FIX", f"Line items sum to ${total:.2f} but the total says ${float(inv['total']):.2f}.")
    else:
        add("OK", f"Arithmetic consistent: ${total:.2f}.")
    if total >= 1000:
        add("CHECK", "Service payment of $1,000 or more needs OSE approval; $10,000+ needs a contract (KB 8112065).")
    dates = sorted({l.get("service_date") for l in lines if l.get("service_date")})
    if not dates:
        add("FIX", "No service date on any line.")
    elif len(dates) > 1:
        add("CHECK", f"{len(dates)} service dates on one invoice; the club's plan is one invoice per session.")

    # Agreement on the amount
    rate = agree.get("rate_per_session")
    if rate is None:
        add("CHECK", "No agreed rate on record. Agree the rate in writing before requesting funds.")
    else:
        for l in lines:
            if float(l.get("rate", 0)) != float(rate):
                add("CHECK", f"Invoice rate ${l.get('rate')} differs from agreed ${rate} ({agree.get('source', 'no source')}).")
    if not (agree.get("written_agreement") or agree.get("written_quote_and_acceptance")):
        add("FIX", "No written agreement on the amount to attach. GrantEd accepts an email or text agreeing on the "
                   "payment amount (KB 8112065); a screenshot of the chat where the rate was agreed works.")
    elif agree.get("rate_settled") is False:
        add("CHECK", "A written rate exists but the payee has since proposed a different rate; settle it in writing.")

    # Funding and timing
    status = (fund.get("status") or "none").lower()
    first = d(dates[0]) if dates else None
    if first and first <= today:
        if status == "approved":
            add("OK", f"Service on {first:%m-%d-%Y} is covered by approved funding ({fund.get('source')}). "
                      "Submit the payment request now that the service happened.")
        elif status == "allocation":
            add("CHECK", f"Service already happened ({first:%m-%d-%Y}). Payment requests without prior approval are "
                         f"rejected (KB 8755457); ask SSE whether the existing allocation ({fund.get('source')}) "
                         "counts as approval for this date.")
        else:
            add("BLOCK", f"Service already happened ({first:%m-%d-%Y}) with no approved funding. GSC does not fund "
                         "retroactively and unapproved payment requests are rejected (ASSU /206, KB 8755457).")
    elif first:
        days = (first - today).days
        need = 21 if total <= 500 else 28 if total <= 1000 else 35
        if status == "approved":
            add("OK", "Funding approved; pay only after the session is taught.")
        elif status == "requested":
            add("CHECK", f"Funding request pending ({fund.get('application_id') or fund.get('source') or 'id?'}); "
                         "payment waits for approval and for the session.")
        elif status == "allocation":
            add("CHECK", f"Confirm the existing allocation ({fund.get('source')}) covers this session and has posted.")
        elif days < 14:
            add("BLOCK", f"Session is {days} days away with no funding requested: the mandatory GSC Funding Calendar "
                         "listing (14 days) and one-month ASSU lead time cannot be met (ASSU /196, /206).")
        elif days < 30:
            add("CHECK", f"Session is {days} days away. ASSU asks for applications at least one month ahead "
                         f"(ASSU /196); GSC needs about {need // 7} weekly meetings for ${total:.0f} (ASSU /206). Request today.")
        else:
            add("OK", f"Session is {days} days away: enough time to request GSC funding now.")

    # Who already paid
    if oop.get("by"):
        method = (oop.get("method") or "").lower()
        msg = (f"{oop['by']} already paid the payee ({oop.get('amount') or 'amount not recorded'}"
               f"{', via ' + method if method else ''}). Do not also pay this invoice for the same session.")
        if PRIVATE_PAY.search(method):
            msg += " Peer-to-peer payments for services are not allowed, so expect no reimbursement (KB 8112129)."
        add("CHECK", msg)

    # Evidence
    att = ev.get("attendance_list")
    if not att:
        add("FIX", "No attendance list (names + emails). GSC cut a past grant in half for lacking one.")
    else:
        add("OK", f"Attendance evidence: {att}.")
    if ev.get("announcement_matches_instructor") is False:
        add("FIX", "The public announcement named a different instructor than the one who taught; "
                   "note the substitution in the request so the evidence is consistent.")
    return sorted(out, key=lambda x: ORDER[x[0]]), total, dates


def report(f, today):
    results, total, dates = check(f, today)
    payee, inv, fund = f.get("payee", {}), f.get("invoice", {}), f.get("funding", {})
    counts = {k: sum(1 for r in results if r[0] == k) for k in ORDER}
    status = (fund.get("status") or "none").lower()
    verdict = ("NOT READY" if counts["BLOCK"] or counts["FIX"] else
               "READY FOR FO REVIEW" if status == "approved" else
               "WAITING FOR FUNDING APPROVAL" if status in ("requested", "allocation") else
               "READY FOR A FUNDING REQUEST (payment waits for approval)")
    md = [f"# Invoice check: {payee.get('name', '?')} — {inv.get('number', 'no number')}",
          "", f"Checked {today:%m-%d-%Y}. Verdict: **{verdict}** "
          f"({counts['BLOCK']} block, {counts['FIX']} fix, {counts['CHECK']} check, {counts['OK']} ok).", "",
          "| Level | Finding |", "|---|---|"]
    md += [f"| {lvl} | {msg} |" for lvl, msg in results]
    md += ["", "## GrantEd payment request draft (the FO types and submits this; nothing was submitted)", "",
           "| Field | Value |", "|---|---|",
           "| Request type | Service Payment |",
           f"| Vendor / payee | {payee.get('name', '?')}, {payee.get('email') or 'email?'} (GrantEd emails the W-9 request) |",
           f"| Service date(s) | {', '.join(f'{d(x):%m-%d-%Y}' for x in dates) or '?'} |",
           f"| Amount | ${total:.2f} |",
           f"| Account | {fund.get('account') or 'The approved funding line (service payments book to Honoraria)'} |",
           f"| Funding line / application | {fund.get('application_id') or fund.get('source') or 'none approved yet'} |",
           f"| Description | {f.get('description') or 'Guest dance instruction, SBSBZ weekly Bachata class'} |",
           "| Payment method | Check, mail or pickup (direct deposit needs Axess, so students only) |",
           "| Attachments | Itemized invoice PDF; written agreement on the amount; attendance list |"]
    return "\n".join(md) + "\n", results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("facts")
    ap.add_argument("--today", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    today = d(a.today) if a.today else dt.date.today()
    with open(a.facts) as fh:
        facts = json.load(fh)
    text, results = report(facts, today)
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(text)
    print(text)
    levels = {r[0] for r in results}
    sys.exit(2 if "BLOCK" in levels else 1 if "FIX" in levels else 0)


if __name__ == "__main__":
    main()
