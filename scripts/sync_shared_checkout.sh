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
#   - never rebase or merge: fast-forward only, so a conflict is impossible and no history is rewritten under a
#     live session;
#   - never run while another git process holds the repo (that is what produced "fatal: Cannot autostash");
#   - never touch a checkout that is ahead of origin: those commits are somebody's unpushed work, and the fix is to
#     branch and open a PR for them, which this script prints rather than doing;
#   - never delete or overwrite an untracked file that an incoming commit would clobber: it names them and stops;
#   - never stash: tracked modifications belong to whichever session is writing them, and a fast-forward that would
#     overwrite a modified file aborts on git's own check anyway.
# It is therefore safe to run on a timer while agents are working: the worst case is that it prints why it skipped.
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

git fetch --quiet origin "$BRANCH" || die "fetch failed in $REPO"

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

# An untracked file that an incoming commit also adds would be clobbered; git refuses, so name them first.
clobber="$(git diff --name-only --diff-filter=A "HEAD..origin/$BRANCH" 2>/dev/null | while read -r f; do
  [ -e "$f" ] && ! git ls-files --error-unmatch "$f" >/dev/null 2>&1 && printf '%s\n' "$f"
done)"
if [ -n "$clobber" ]; then
  warn "STOP: these untracked files in $REPO would be overwritten by incoming commits:"
  printf '%s\n' "$clobber" | sed 's/^/       /' >&2
  warn "       Move or delete them, then re-run. Nothing was changed."
  exit 3
fi

if [ "$DRY" = "1" ]; then
  say "DRY: would fast-forward $REPO from $(git rev-parse --short HEAD) to $(git rev-parse --short "origin/$BRANCH") ($behind commit(s))"
  exit 0
fi

before="$(git rev-parse --short HEAD)"
if git merge --ff-only "origin/$BRANCH" >/dev/null 2>&1; then
  say "fast-forwarded $REPO: $before -> $(git rev-parse --short HEAD) ($behind commit(s))"
  git log --oneline "$before..HEAD" | head -5 | sed 's/^/       /'
  [ "$behind" -gt 5 ] && say "       ... and $((behind - 5)) more"
  exit 0
fi

warn "STOP: fast-forward refused in $REPO (a tracked file is modified in the way, most likely). Nothing was changed."
git status --short | head -8 >&2
exit 4
