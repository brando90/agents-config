#!/usr/bin/env python3
"""plan-attest-auto: renew the Stanford Claude lane's subscription-only attestation by itself, from a fresh native read (2026-11-24, AT-3467).
Use: plan-attest-auto [--plan stanford-claude] [--renew-within-hours 6] [--hours 24] [--force] [--dry-run]
plan-rr calls it before each job. When the attestation has under --renew-within-hours left (or is expired), it makes one tiny native Claude Code call on the lane
(stream-json --verbose, same argv as the router's config, API keys scrubbed) and renews only if Claude's own rate_limit_event says status allowed, overage rejected
(overageStatus rejected, isUsingOverage false) and the window is under 80% used. Otherwise it leaves the old attestation to lapse and prints why. Never enables a plan,
never touches paid fallback, never prints keys. Exit 0 = valid (renewed or still fresh), 1 = could not renew."""
import argparse, contextlib, datetime as dt, fcntl, importlib.util, json, os, re, subprocess, sys, tempfile, time
H = os.path.expanduser('~')
CONFIG = H + '/.config/plan-router/config.json'
ROUTER_PY = os.environ.get('PLAN_ROUTER_PY', H + '/.local/lib/plan-router/router.py')
LOG = os.environ.get('PLAN_ATTEST_LOG', H + '/.local/state/plan-router/attest-auto.jsonl')
PRIOR = {'stanford-claude': 'Stanford Claude Education Enterprise seat, one-year setup-token lane.',
         'vals-claude-opus': 'Vals first-party OAuth wrapper (claude-opus-5-5), org overage disabled until Nov 30 4:00 PM PST; set up in AT-3413.'}
SCRUB = re.compile(r'(API_KEY|AUTH_TOKEN|OAUTH_TOKEN|_SECRET|PASSWORD)', re.I)


def log(row):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    open(LOG, 'a').write(json.dumps({'at': dt.datetime.now(dt.timezone.utc).isoformat(), **row}) + '\n')


def recent_failure(plan, seconds):
    with contextlib.suppress(OSError, ValueError):
        row = json.loads(open(LOG).read().strip().splitlines()[-1])
        return row.get('plan') == plan and row.get('renewed') is False and time.time() - dt.datetime.fromisoformat(row['at']).timestamp() < seconds
    return False


def load_router():
    spec = importlib.util.spec_from_file_location('plan_router', ROUTER_PY)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def seconds_left(plan):
    exp = plan.get('subscription_only', {}).get('expires_at')
    if not exp: return -1
    return dt.datetime.fromisoformat(exp.replace('Z', '+00:00')).timestamp() - time.time()


def native_read(plan, router):
    """One tiny native call; returns (verdict ok?, evidence or reason)."""
    argv = [a.replace('{prompt}', 'Reply with the single word OK.') for a in plan['argv']]
    if '--max-turns' in argv: argv[argv.index('--max-turns') + 1] = '1'
    env = {k: v for k, v in os.environ.items() if not SCRUB.match(k)}
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'stdout')
        try:
            with open(out, 'w') as o:
                r = subprocess.run(argv, input='Reply with the single word OK.', stdout=o, stderr=subprocess.DEVNULL, text=True, cwd=d, env=env, timeout=120)
        except (subprocess.TimeoutExpired, OSError) as e:
            return False, 'native call failed: ' + type(e).__name__
        from pathlib import Path
        found = router.limit_status(Path(out))
        results = [e for e in router.stream_events(Path(out)) if e.get('type') == 'result']
    if r.returncode != 0 or not results or results[-1].get('is_error'):
        return False, 'native call did not complete (exit %s)' % r.returncode
    if not found:
        return False, 'no rate_limit_event in the native call'
    bits = []
    for kind, i in found.items():
        used = i['utilization']
        pct = None if used is None else (used if used > 1 else used * 100)
        if i['status'] != 'allowed': return False, 'window %s status %s' % (kind, i['status'])
        if i['is_using_overage']: return False, 'overage in use on %s' % kind
        if i['overage_status'] != 'rejected': return False, 'overage status %r on %s, not rejected' % (i['overage_status'], kind)
        if pct is None or pct >= 80: return False, 'window %s utilization %r not under 80%%' % (kind, pct)
        bits.append('%s %.0f%% used' % (kind, pct))
    return True, ('%s native read (claude -p, stream-json): rate_limit_event status allowed, %s, overageStatus rejected, isUsingOverage false; auto-renewed by plan-attest-auto; API keys scrubbed. Prior evidence: %s'
                  % (dt.datetime.now().strftime('%Y-%m-%d %H:%M %Z'), ', '.join(bits), PRIOR.get(plan['id'], 'lane first set up with its own native read.')))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan', default='stanford-claude'); ap.add_argument('--renew-within-hours', type=float, default=6)
    ap.add_argument('--hours', type=float, default=24); ap.add_argument('--force', action='store_true'); ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--config', default=CONFIG)
    a = ap.parse_args()
    lock = open(a.config + '.attest.lock', 'w'); fcntl.flock(lock, fcntl.LOCK_EX)
    c = json.load(open(a.config)); plan = next(x for x in c['plans'] if x['id'] == a.plan)
    if plan.get('enabled') is not True:
        print('plan-attest-auto:', a.plan, 'is disabled; not renewing'); return 1
    left = seconds_left(plan)
    if left > a.renew_within_hours * 3600 and not a.force:
        print('plan-attest-auto: %s attestation has %.1f h left; no renewal needed' % (a.plan, left / 3600)); return 0
    if not a.force and recent_failure(a.plan, 600):
        print('plan-attest-auto: a renewal for %s failed under 10 minutes ago; not trying again yet' % a.plan, file=sys.stderr); return 1 if left <= 0 else 0
    router = load_router()
    ok, why = native_read(plan, router)
    if not ok:
        log({'plan': a.plan, 'renewed': False, 'reason': why}); print('plan-attest-auto: NOT renewed:', why, file=sys.stderr); return 1 if left <= 0 else 0
    if a.dry_run:
        print('plan-attest-auto: dry run, would renew:', why); return 0
    c = json.load(open(a.config)); plan = next(x for x in c['plans'] if x['id'] == a.plan)  # reread: edit only this plan's proof
    exp = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=a.hours)).isoformat()
    plan['subscription_only'] = {'verified': True, 'evidence': why, 'expires_at': exp}
    st = os.stat(a.config); fd, tmp = tempfile.mkstemp(dir=os.path.dirname(a.config))
    with os.fdopen(fd, 'w') as f: json.dump(c, f, indent=2)
    os.chmod(tmp, st.st_mode & 0o777); os.replace(tmp, a.config)
    log({'plan': a.plan, 'renewed': True, 'expires_at': exp}); print('plan-attest-auto: renewed', a.plan, 'to', exp); return 0


if __name__ == '__main__':
    sys.exit(main())
