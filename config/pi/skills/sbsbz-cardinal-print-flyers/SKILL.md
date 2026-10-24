---
name: sbsbz-cardinal-print-flyers
description: Print Stanford Bachata Sensual & Brazilian Zouk (SBSBZ) club flyers on Stanford Cardinal Print from Brando's Mac. Use when Brando asks to print, reprint or "print again" SBSBZ flyers, posters or handouts (for example "print all 3, 25 each"). Submits color, one-sided, Letter jobs through the installed CardinalPrint driver, verifies them, records a private receipt and tells Brando how to release them.
---

# Skill: print SBSBZ flyers on Cardinal Print

**Doc link:** <https://github.com/brando90/agents-config/blob/main/config/pi/skills/sbsbz-cardinal-print-flyers/SKILL.md>

**TLDR:** When Brando asks for SBSBZ flyers to be printed, submit the current print-ready PDFs to Stanford Cardinal Print with `scripts/print_flyers.sh` (default 25 color, one-sided Letter copies per design), confirm every job reached Stanford's server, and tell him the job numbers so he can release them at any Cardinal Print device within 48 hours.

Google Drive copy: the "Agent skills and prompts" folder in the club's shared Marketing folder, <https://drive.google.com/drive/folders/1U3EmA7i5W0O1hrDmYw37QiYi9aDxEG05>. agents-config is the canonical skill source; update the Drive guide when this procedure changes. Installed copies for local agents live in `~/.claude/skills/sbsbz-cardinal-print-flyers/` (Claude Code) and `~/.codex/skills/sbsbz-cardinal-print-flyers/` (Codex and the ChatGPT desktop agent); these are managed links to the canonical agents-config skill, not independent copies.

## Brando's standing preferences

- **"Print" means print now.** He has already approved the spend. Do not stop to ask whether he is sure, and do not refuse because an earlier batch is still waiting on the server. Submit, then mention any earlier unreleased jobs in the report so he can release only the ones he wants. (On 10-09-2026 an agent declined a reprint because the 13:31 batch was still queued; Brando answered "Again duh".)
- **Default quantity:** 25 copies of each current design unless he names another number.
- **Brazilian Zouk always appears on the flyer**, even when its schedule is tentative ("Schedule tentative - stay tuned"). Never invent a Zouk day, time, room or instructor.
- Remove panels for events whose date has passed before printing.
- No email, social post or WhatsApp message is part of printing. Printing does not authorize advertising.

## Procedure

1. **Find the current print set.** Use the newest one-page Letter PDFs Brando or the last print task approved. As of 10-09-2026 these are the three designs in `~/sbsbz/events/10-09-2026-three-flyer-print/assets/`:
   - `A-Campus-Casual-Bachata-and-Zouk-10-09-2026.pdf`
   - `B-Your-First-Class-Bachata-and-Zouk-10-09-2026.pdf`
   - `C-Just-Come-Dance-Bachata-and-Zouk-10-09-2026.pdf`

   If a newer `events/*print*/assets/` or `events/*flyer*/` folder exists, check its `DISPATCH-REPORT.md` and use the newer set. Previous receipts are in `events/*/private/print-receipt*.json` and `lpstat -W completed -o CardinalPrint | head`.
2. **Check the files are current and correct** (stale-artifact guard). Each PDF must be one Letter page. Confirm the Zouk wording with `pdftotext FILE - | grep -i zouk`, and look at the matching PNG preview if a flyer changed since the last print. If a flyer needs an edit, rebuild it with the event folder's `build_flyers.py` and check the rendered page before printing.
3. **Dry run, then submit** from any directory:

   ```bash
   # the script ships in this skill's folder; use whichever installed copy exists
   S=$(ls ~/agents-config/config/pi/skills/sbsbz-cardinal-print-flyers/scripts/print_flyers.sh \
         ~/.claude/skills/sbsbz-cardinal-print-flyers/scripts/print_flyers.sh \
         ~/.codex/skills/sbsbz-cardinal-print-flyers/scripts/print_flyers.sh 2>/dev/null | head -1)
   A=~/sbsbz/events/10-09-2026-three-flyer-print/assets
   $S --dry-run "$A"/A-*.pdf "$A"/B-*.pdf "$A"/C-*.pdf
   $S --copies 25 --receipt ~/sbsbz/events/MM-DD-YYYY-flyer-print/private/print-receipt.json \
      "$A"/A-*.pdf "$A"/B-*.pdf "$A"/C-*.pdf
   ```

   The script passes every option explicitly because the installed driver defaults to **monochrome and duplex**: `-o media=Letter -o sides=one-sided -o CNColorMode=color -o ColorModel=RGB -o CNDuplex=None -o fit-to-page`.
4. **Verify.** The script waits for the local queue to drain and checks each job's state, copies, color mode and the CUPS (Common Unix Printing System) error log. It prints `VERIFIED` and exits 0 only if every job is `completed`, in color, with no error-log lines. Re-check any job later with `$S --verify JOBID ...`.
   - `popup - failed to obtain popup information` in the error log means Stanford's sign-in popup did not answer and the job was cancelled (job 856 on 10-08-2026). Resubmit that file once. If it fails again, report it; the fallback is uploading the PDF at <https://cardinalprintcenter.stanford.edu> (color, one-sided, copies set there).
   - "Completed" means Stanford's server accepted the job. Nothing on the Mac can confirm paper came out; say so.
5. **Record.** Keep the receipt under the event folder's `private/` directory. Do not commit receipts or job attributes: this repository is public.
6. **Report to Brando** in a few lines: job numbers with design names and copies, color and one-sided, any earlier jobs still waiting, and how to release.

## Releasing the jobs (tell Brando)

At any Cardinal Print device, scan a Stanford ID card, use Mobile Key, or log in with the SUNet ID. Jobs are held for 48 hours, then deleted automatically ([Cardinal Print FAQ](https://uit.stanford.edu/service/cardinal-print/faq), [student instructions](https://uit.stanford.edu/service/cardinal-print/students)).

## Copy-paste prompt (Claude, Codex or ChatGPT agent on Brando's Mac)

> Print the current Stanford Bachata Sensual & Brazilian Zouk (SBSBZ) flyers on Stanford Cardinal Print. Brando approves the print job and its cost; do not ask again. Default: 25 copies of each current design, color, one-sided, US Letter. Read `~/agents-config/config/pi/skills/sbsbz-cardinal-print-flyers/SKILL.md`; use `~/sbsbz` as the work repository and follow it. If that file is missing, use the newest one-page Letter PDFs under `~/sbsbz/events/*print*/assets/` (as of 10-09-2026: the A Campus Casual, B Your First Class and C Just Come Dance designs). Make sure Brazilian Zouk appears on each flyer, marked "Schedule tentative - stay tuned" if no schedule is confirmed, and never invent Zouk times. Submit each PDF with `lp -d CardinalPrint -n 25 -o media=Letter -o sides=one-sided -o CNColorMode=color -o ColorModel=RGB -o CNDuplex=None -o fit-to-page FILE.pdf`; the driver defaults to black-and-white duplex, so keep every option. Then confirm each job left the local queue with state "completed", in color, and with no `[Job N]` lines in `/var/log/cups/error_log`. Resubmit a file once if its job was cancelled with "failed to obtain popup information". Save a private receipt in the event folder's `private/` directory and do not commit it. Do not send emails, social posts or WhatsApp messages. Report the job numbers, designs and copies, any earlier jobs still waiting, and that jobs are released at any Cardinal Print device with a Stanford ID, Mobile Key or SUNet login within 48 hours. No external rules file exists for this prompt; everything you need is above.
