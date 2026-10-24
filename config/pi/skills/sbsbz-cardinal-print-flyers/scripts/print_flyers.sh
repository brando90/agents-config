#!/bin/bash
# print_flyers.sh - submit SBSBZ flyer PDFs to Stanford Cardinal Print and verify them.
#
#   print_flyers.sh [--copies N] [--receipt PATH] [--dry-run] FILE.pdf [FILE.pdf ...]
#   print_flyers.sh --verify JOBID [JOBID ...]
#
# Defaults: 25 copies per file, color, one-sided, US Letter, fit to page.
# The installed CardinalPrint driver defaults to monochrome and duplex, so every
# option below is passed explicitly. Jobs wait on Stanford's server for 48 hours
# until released at a Cardinal Print device (Stanford ID, Mobile Key or SUNet login).
set -euo pipefail

PRINTER="CardinalPrint"
COPIES=25
RECEIPT=""
DRY=0
MODE="submit"
OPTS=(-o media=Letter -o sides=one-sided -o CNColorMode=color -o ColorModel=RGB -o CNDuplex=None -o fit-to-page)

die() { echo "ERROR: $*" >&2; exit 1; }

job_attrs() {  # prints copies / sides / color / state / printer message for one job
  local j="$1"
  ipptool -t "ipp://localhost/printers/$PRINTER" /dev/stdin 2>/dev/null <<IPP | grep -E 'job-state |copies \(|sides \(|CNColorMode|job-printer-state-message' | tr -s ' ' | sed 's/^ //'
{ OPERATION Get-Job-Attributes
  GROUP operation-attributes-tag
  ATTR charset attributes-charset utf-8
  ATTR naturalLanguage attributes-natural-language en
  ATTR uri printer-uri \$uri
  ATTR integer job-id $j
  ATTR name requesting-user-name $USER
  ATTR keyword requested-attributes all
  DISPLAY job-state DISPLAY copies DISPLAY sides DISPLAY CNColorMode DISPLAY job-printer-state-message }
IPP
}

verify_jobs() {  # waits for the local queue to drain, then checks each job; exit 1 on any problem
  local ids=("$@") bad=0 waited=0
  while lpstat -o "$PRINTER" 2>/dev/null | grep -qE "$PRINTER-($(IFS='|'; echo "${ids[*]}"))\b"; do
    [ "$waited" -ge 180 ] && { echo "WARN: jobs still in the local queue after 180 s"; bad=1; break; }
    sleep 5; waited=$((waited + 5))
  done
  for j in "${ids[@]}"; do
    local a; a="$(job_attrs "$j")"
    echo "job $j: $(echo "$a" | tr '\n' ';' | sed 's/;$//')"
    echo "$a" | grep -q 'job-state (enum) = completed' || { echo "  PROBLEM: job $j is not completed"; bad=1; }
    echo "$a" | grep -q 'CNColorMode (nameWithoutLanguage) = color' || { echo "  PROBLEM: job $j is not color"; bad=1; }
    if grep -E "\[Job $j\]" /var/log/cups/error_log 2>/dev/null | grep -q .; then
      echo "  PROBLEM: CUPS error_log lines for job $j:"; grep -E "\[Job $j\]" /var/log/cups/error_log | sed 's/^/    /'; bad=1
    fi
  done
  [ "$bad" -eq 0 ] && echo "VERIFIED: all jobs reached Stanford's print server; release them at a Cardinal Print device within 48 hours."
  return "$bad"
}

FILES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --copies) COPIES="$2"; shift 2 ;;
    --receipt) RECEIPT="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    --verify) MODE="verify"; shift ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) FILES+=("$1"); shift ;;
  esac
done
[ "${#FILES[@]}" -gt 0 ] || die "give at least one PDF (or job id with --verify)"

if [ "$MODE" = "verify" ]; then verify_jobs "${FILES[@]}"; exit $?; fi

[[ "$COPIES" =~ ^[0-9]+$ ]] && [ "$COPIES" -ge 1 ] || die "--copies must be a positive integer"
lpstat -p "$PRINTER" >/dev/null 2>&1 || die "printer $PRINTER is not installed (install the Cardinal Print driver, or upload at https://cardinalprintcenter.stanford.edu)"

echo "Preflight (printer $PRINTER, $COPIES copies each):"
for f in "${FILES[@]}"; do
  [ -f "$f" ] || die "missing file: $f"
  pages="$(pdfinfo "$f" 2>/dev/null | awk '/^Pages:/{print $2}')"
  [ -n "$pages" ] || die "not a readable PDF: $f"
  size="$(pdfinfo "$f" 2>/dev/null | awk -F': *' '/^Page size:/{print $2}')"
  echo "  $(basename "$f"): pages=$pages size=[$size] sha256=$(shasum -a 256 "$f" | cut -c1-12) modified=$(stat -f '%Sm' -t '%m-%d-%Y %H:%M' "$f")"
done

if [ "$DRY" -eq 1 ]; then
  for f in "${FILES[@]}"; do printf 'lp -d %s -n %s %s -t %q %q\n' "$PRINTER" "$COPIES" "${OPTS[*]}" "$(basename "${f%.pdf}")" "$f"; done
  echo "DRY RUN: nothing submitted."; exit 0
fi

IDS=()
for f in "${FILES[@]}"; do
  out="$(lp -d "$PRINTER" -n "$COPIES" "${OPTS[@]}" -t "$(basename "${f%.pdf}")" "$f")"
  echo "$out"
  id="$(echo "$out" | sed -nE "s/.*$PRINTER-([0-9]+).*/\1/p")"
  [ -n "$id" ] || die "could not read a job id for $f"
  IDS+=("$id")
done

status=0; verify_jobs "${IDS[@]}" || status=$?

if [ -n "$RECEIPT" ]; then
  mkdir -p "$(dirname "$RECEIPT")"
  python3 -I - "$RECEIPT" "$COPIES" "$status" "${#FILES[@]}" "${FILES[@]}" "${IDS[@]}" <<'PY'
import hashlib, json, sys, datetime
out, copies, status, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
files, ids = sys.argv[5:5 + n], sys.argv[5 + n:]
jobs = [{"job_id": int(i), "file": f, "copies": copies,
         "sha256": hashlib.sha256(open(f, "rb").read()).hexdigest()} for f, i in zip(files, ids)]
json.dump({"submitted_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "printer": "CardinalPrint", "options": "color, one-sided, Letter, fit-to-page",
           "jobs": jobs, "total_copies": copies * len(jobs), "verified": status == 0,
           "physical_release_verified": False}, open(out, "w"), indent=2)
print("receipt:", out)
PY
fi
exit "$status"
