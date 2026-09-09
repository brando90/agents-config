#!/usr/bin/env bash
# TLDR: fast-forward a shared checkout (the one open in Brando's editor) to origin/main after workers land their
# PRs, so the editor always shows what main actually contains -- and refuse, loudly and without touching anything,
# in every case where a fast-forward would not be honest.
#
# WHY: workers land with `git push origin <branch>:main` from their own worktrees. That advances origin/main and
# never touches the shared checkout, so ~/veribench silently falls behind -- 52 commits by 2026-09-09, which is how
# a file that was on main for half an hour was invisible in the editor. Nothing was pulling it back down.
#
# USAGE
#   scripts/sync_shared_checkout.sh                 # sync ~/veribench
#   scripts/sync_shared_checkout.sh ~/other-repo    # sync another checkout
#   DRY=1 scripts/sync_shared_checkout.sh           # say what it would do, change nothing
#   QUIET=1 scripts/sync_shared_checkout.sh         # only print when something happened or is wrong
#
# WHAT IT WILL NOT DO (each one is a real failure mode, not caution for its own sake):
#   - never rebase or merge across history: fast-forward only, so no history is rewritten under a live session;
#   - never touch a checkout that is ahead of origin: those commits are somebody's unpushed work, and the fix is to
#     branch and open a PR for them, which this script prints rather than doing;
#   - never overwrite a local file that an incoming commit would land on -- untracked, ignored, or locally modified,
#     and counting rename destinations, not just added paths: it names them and stops;
#   - never stash and never delete: tracked modifications belong to whichever session is writing them.
#
# THE ONE RACE IT CANNOT CLOSE, stated plainly because a reader will otherwise assume it is safe. Git's index lock
# does not lock ordinary file writes. Between the moment this script checks the tree and the moment the
# fast-forward replaces files, another agent can save a file, and if that same path also changed upstream the save
# is lost. The window is short and the checks below narrow it to paths the update actually touches, but it is real:
# run this in the checkout that belongs to the editor, not in one where agents are actively writing (agents belong
# in their own worktrees), and treat a report of lost work as this window until proven otherwise.
set -u

REPO="${1:-$HOME/veribench}"
BRANCH="${BRANCH:-main}"
DRY="${DRY:-0}"
QUIET="${QUIET:-0}"

say()  { [ "$QUIET" = "1" ] || printf '[sync] %s\n' "$*"; }
warn() { printf '[sync] %s\n' "$*" >&2; }
die()  { warn "$*"; exit 1; }

[ -d "$REPO/.git" ] || die "not a git checkout: $REPO"
cd "$REPO" || die "cannot enter $REPO"

# A held index means another git process is mid-operation here; skip rather than fight it. Only the lock file is
# checked: matching process command lines was tried first and was far too loose -- any command whose text merely
# contained "git" and the repo's name (this script's own shell included) made it skip a perfectly healthy checkout.
# Everything below is fetch and fast-forward, which fail cleanly and change nothing if git locks under us anyway.
if [ -f .git/index.lock ]; then
  say "skip: .git/index.lock exists, another git process is mid-operation in $REPO"
  exit 0
fi

cur="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
[ "$cur" = "$BRANCH" ] || { say "skip: $REPO is on '$cur', not '$BRANCH'"; exit 0; }

# An interrupted rebase, merge, cherry-pick, bisect or a detached HEAD means somebody is mid-operation here.
for m in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD BISECT_LOG; do
  [ -e ".git/$m" ] && { say "skip: $REPO has an operation in progress (.git/$m)"; exit 0; }
done

# `git fetch` writes objects and remote-tracking refs. It never touches the working tree, so it is safe here, but
# it is a write: say so rather than letting DRY=1 imply the repository was not touched at all. --no-write-fetch-head
# keeps FETCH_HEAD, which other tooling reads, from being clobbered by this background sync.
git fetch --quiet --no-write-fetch-head origin "$BRANCH" 2>/dev/null \
  || git fetch --quiet origin "$BRANCH" \
  || die "fetch failed in $REPO"

read -r ahead behind <<EOF
$(git rev-list --left-right --count "HEAD...origin/$BRANCH" | tr '\t' ' ')
EOF

if [ "${ahead:-0}" -gt 0 ]; then
  warn "STOP: $REPO has $ahead commit(s) that are not on origin/$BRANCH. They are somebody's unpushed work."
  git log --oneline "origin/$BRANCH..HEAD" | sed 's/^/       /' >&2
  warn "       Publish them first, then re-run:"
  warn "         cd $REPO && git branch -f <topic-branch> HEAD && git push -u origin <topic-branch>"
  warn "         gh pr create --base $BRANCH --head <topic-branch>"
  exit 2
fi

if [ "${behind:-0}" -eq 0 ]; then
  say "already current: $REPO is at origin/$BRANCH ($(git rev-parse --short HEAD))"
  exit 0
fi

# Which paths does the update actually write? Added paths and rename DESTINATIONS both create files, so filtering
# on "A" alone missed a rename landing on a local file. -z keeps filenames with spaces, quotes or newlines intact,
# and for R/C entries git emits source and destination as two extra NUL-separated fields, so the destination is
# read explicitly rather than guessed.
incoming="$(git diff -z --name-status --find-renames "HEAD..origin/$BRANCH" 2>/dev/null | python3 -c '
import sys
parts = sys.stdin.buffer.read().split(b"\0")
i, out = 0, []
while i < len(parts) and parts[i]:
    st = parts[i].decode("utf-8", "surrogateescape"); i += 1
    if st[:1] in ("R", "C"):        # status, source, destination
        i += 1
        if i < len(parts): out.append(parts[i].decode("utf-8", "surrogateescape")); i += 1
    else:
        if i < len(parts):
            p = parts[i].decode("utf-8", "surrogateescape"); i += 1
            if st[:1] in ("A", "M", "T"): out.append(p)
print("\n".join(out))' 2>/dev/null)"

# A local file sitting on one of those paths loses its content when the update lands. Untracked and IGNORED files
# are both at risk -- git refuses to clobber an untracked file but will happily overwrite an ignored one -- and a
# tracked file with local modifications is at risk too. -e misses a broken symlink, so -L is tested as well.
clobber=""
modified=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  if [ -e "$f" ] || [ -L "$f" ]; then
    if git ls-files --error-unmatch -- "$f" >/dev/null 2>&1; then
      git diff --quiet -- "$f" 2>/dev/null || modified="$modified$f
"
    else
      clobber="$clobber$f
"
    fi
  fi
done <<EOF
$incoming
EOF

if [ -n "$clobber" ] || [ -n "$modified" ]; then
  warn "STOP: the update would write over local content in $REPO. Nothing was changed."
  [ -n "$clobber" ]  && { warn "       untracked or ignored files on incoming paths:"; printf '%s' "$clobber" | sed 's/^/         /' >&2; }
  [ -n "$modified" ] && { warn "       tracked files with local modifications on incoming paths:"; printf '%s' "$modified" | sed 's/^/         /' >&2; }
  warn "       Commit, move or delete them, then re-run."
  exit 3
fi

if [ "$DRY" = "1" ]; then
  say "DRY: would fast-forward $REPO from $(git rev-parse --short HEAD) to $(git rev-parse --short "origin/$BRANCH") ($behind commit(s))"
  exit 0
fi

before="$(git rev-parse --short HEAD)"
err="$(git merge --ff-only "origin/$BRANCH" 2>&1 >/dev/null)"; rc=$?
if [ "$rc" -eq 0 ]; then
  say "fast-forwarded $REPO: $before -> $(git rev-parse --short HEAD) ($behind commit(s))"
  git log --oneline "$before..HEAD" | head -5 | sed 's/^/       /'
  [ "$behind" -gt 5 ] && say "       ... and $((behind - 5)) more"
  exit 0
fi

# Do NOT claim nothing changed: git updates ORIG_HEAD, and can update working files and the index, before it
# updates the branch, so a failed fast-forward can leave the tree partly moved. Print git's own words and say
# what to look at.
warn "STOP: fast-forward failed in $REPO (git exit $rc). The tree may be partly updated -- inspect it."
printf '%s\n' "$err" | sed 's/^/       git: /' >&2
warn "       state now: HEAD $(git rev-parse --short HEAD 2>/dev/null), was $before"
git status --short 2>/dev/null | head -8 | sed 's/^/       /' >&2
exit 4
