#!/usr/bin/env python3
"""plan-rr: run one bounded job on Brando's own AI accounts via the plan router, in priority order (2026-11-23, AT-3397; was round robin 2026-11-21).
Order 2026-11-24 (AT-3448, Brando 09:58): vals-codex, vals-claude-opus, stanford-codex, stanford-claude, STAIR Claude, Sundial (writing only), Koyejo lab key, Cursor, Grok, then Vals key, STAIR/Stanford gateway sol, personal Codex, personal Claude, Allen, Google plan last. Was (Brando, Nov 23 17:25: "always start with vals and stanford first before my personal accounts"): Vals and Stanford routes, then personal Codex and Claude, then Cursor/Grok, Allen's key, and the Google plan last. A route is skipped only when gated, off, or low (router gate, 20% left).
Flags: --experiment (marks a real experiment run; the Google plan stays eligible, Brando 2026-11-25 09:45), --order (print the order and exit).
2026-11-24 (AT-3455; Brando 10:25 "we should be using vals or rotating better, look my personal codex is so low already" and 11:09 "balance btw that percentage and difficulty of task"):
--difficulty light|medium|heavy (default medium) and --urgent.
  light: small lanes first (Cursor, Grok, keys, Stanford gateway), then Vals and Stanford; never a personal lane.
  medium: the order above. A personal lane only when no Vals or Stanford lane returns within 3 hours (or --urgent), and not once that personal lane is 50% used (unless --urgent).
  heavy: Vals and Stanford lanes (Codex, Claude, STAIR Claude), then Cursor and Grok (Brando 11:28: heavy is allowed there, native CLIs, light quota use, 80% reserve); a personal lane only with --urgent.
A job that would fall to a personal lane while a Vals or Stanford lane returns in time is queued, not run: exit 5, a line "plan-rr: WAIT until <time> for <lane>", and a queue file. `plan-rr --queue` lists the queue, `plan-rr --resume <id>` runs it again (--force skips the wait). Exit 3 = no route.
The router itself gates both personal lanes at 80% used (reads the account's own usage before each launch).
Use: plan-rr --prompt-file /abs/job.md --workspace /abs/dir [--skip personal-agy,...] [--difficulty light|medium|heavy] [--urgent]
Prompts go to every account as plain precise prompts (Brando 2026-11-24 11:31: no 'MY VOICE REQUEST' header or voice text to agy, Cursor or Grok; no timing tricks).
Google plan (agy): last in the order; any job may use it, real experiment runs and heavy jobs included (Brando 2026-11-25 09:45); at most 10 a day (my cap, not his). Skips gated or limited plans, moves to the next.
Uses configured subscriptions and explicitly bounded Pi provider routes; never buys credits. Foreground only."""
import argparse, fcntl, hashlib, json, os, subprocess, sys, time, datetime as dt
H = os.path.expanduser('~')
ROUTER = [sys.executable, H + '/.local/lib/plan-router/router.py', '--config', H + '/.config/plan-router/config.json']
STATE_DIR = H + '/.local/state/plan-router'
QUEUE = STATE_DIR + '/queue'
ROT = [('vals-codex', None), ('vals-claude-opus', 'claude-opus-5-5'), ('stanford-codex', None), ('stanford-claude', None),
       ('pi:stanford-stair-bm', 'claude-opus-5-5'),  # STAIR Claude: Brando's TODO, key change waits for Zeyu's approval (2026-11-24)
       ('sundial', None),  # writing jobs only (--writing): a skill, not a model lane
       ('pi:koyejolab-openai-bm', 'gpt-6.1-sol'), ('native:cursor', 'grok-4.7-high'), ('native:grok', 'grok-4.7'),
       ('pi:vals-openai-bm', 'gpt-6.1-sol'), ('pi:stanford-stair-bm', 'gpt-6.1-sol'),
       ('personal-codex', None), ('personal-claude', None), ('pi:allen-google-veribench', 'gemini-4-argon'),
       ('personal-agy', 'gemini-4-argon-high'), ('personal-agy', 'gemini-4-carbon-medium'), ('personal-agy', 'claude-opus-5-5-high'), ('personal-agy', 'gemini-pro-orchestrator-argon')]
PERSONAL = ('personal-codex', 'personal-claude')
AGY_DAILY_CAP = 10  # Google-plan jobs a day (Brando 11:31: keep it to normal use)
STRONG = ('vals-codex', 'vals-claude-opus', 'stanford-codex', 'stanford-claude')  # the Vals and Stanford subscription lanes whose return time we can read
SMALL = [('native:cursor', 'grok-4.7-high'), ('native:grok', 'grok-4.7'), ('pi:koyejolab-openai-bm', 'gpt-6.1-sol'), ('pi:vals-openai-bm', 'gpt-6.1-sol'), ('pi:stanford-stair-bm', 'gpt-6.1-sol'), ('pi:allen-google-veribench', 'gemini-4-argon')]
WAIT_HOURS = 3
PERSONAL_SPARE = 50  # medium jobs leave a personal lane alone once it is this % used (Brando 11:09: balance the share left against the job)
PI_PATH = '/dfs/scratch0/brando9/bin'


def order_for(difficulty, writing):
    """The lane list for a difficulty tag (light, medium, heavy)."""
    if difficulty == 'light':
        rest = [x for x in ROT if x not in SMALL and x[0] not in PERSONAL]
        return SMALL + rest
    if difficulty == 'heavy':
        return [x for x in ROT if x[0] in STRONG or x == ('pi:stanford-stair-bm', 'claude-opus-5-5') or x[0] in ('sundial', 'native:cursor', 'native:grok')] + [x for x in ROT if x[0] in PERSONAL]
    return list(ROT)


def lane_state(plan):
    """(percent used or None, blocked_until epoch or None) for one plan, from the router's own observations and the account's usage read. Read only."""
    now = time.time()
    used, until = None, None
    try: obs = json.load(open(STATE_DIR + '/observations.json'))
    except Exception: obs = {}
    for kind, item in (obs.get(plan, {}).get('limit_events') or {}).items():
        u = item.get('utilization')
        if isinstance(u, (int, float)): used = max(used or 0, u * 100 if u <= 1 else u)
        b = item.get('blocked_until')
        if b:
            t = dt.datetime.fromisoformat(b).timestamp()
            if t > now: until = max(until or 0, t)
    if plan in ('vals-codex', 'stanford-codex', 'personal-codex'):
        home = {'vals-codex': '.codex-vals-skampere1', 'stanford-codex': '.codex-stanford', 'personal-codex': '.codex'}[plan]
        cache = STATE_DIR + '/codex-usage-cache.json'
        try: c = json.load(open(cache))
        except Exception: c = {}
        if not c.get(plan) or now - c[plan]['read_at'] > 300:
            try:
                r = subprocess.run([sys.executable, H + '/.local/bin/codex-usage.py', '--home', H + '/' + home], capture_output=True, text=True, timeout=30)
                c[plan] = dict(json.loads(r.stdout.strip().splitlines()[-1]), read_at=now)
                json.dump(c, open(cache, 'w'))
            except Exception: c[plan] = None
        d = c.get(plan)
        if d:
            used = None
            for w in ('primary', 'secondary'):
                row = d.get(w)
                if row:
                    used = max(used or 0, row['usedPercent'])
                    if row['usedPercent'] >= 80 and row['resetsAt'] > now: until = max(until or 0, row['resetsAt'])
            if d.get('ordinaryUsageAllowed') is False or d.get('rateLimitReachedType'):
                until = max(until or 0, *[d[w]['resetsAt'] for w in ('primary', 'secondary') if d.get(w)] or [now + 3600])
    return used, until


def vals_codex_busy():
    """The Vals Codex profile runs one job at a time (vals-codex.lock); True while another job holds it."""
    try:
        with open(STATE_DIR + '/vals-codex.lock', 'a') as f:
            try: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB); fcntl.flock(f, fcntl.LOCK_UN); return False
            except BlockingIOError: return True
    except OSError: return False


def lane_returns():
    """Vals and Stanford lanes that are paused or over the 80% reserve and come back: {lane: epoch}."""
    out = {}
    for lane in STRONG:
        used, until = lane_state(lane)
        if lane == 'vals-codex' and not until and vals_codex_busy(): until = time.time() + 240  # one job at a time: busy, back in minutes
        if until: out[lane] = until
    return out


def fmt(t):
    return dt.datetime.fromtimestamp(t).strftime('%a %b %d %H:%M %Z').strip()


def decide_personal(plan, a):
    """None = a personal lane may run now; else (lane, epoch) or (None, None) = queue / stop."""
    if a.urgent or a.force: return None
    if a.difficulty == 'light': return (None, None)
    returns = lane_returns()
    now = time.time()
    soon = {k: v for k, v in returns.items() if v - now <= WAIT_HOURS * 3600}
    if a.difficulty == 'heavy':
        if returns: lane = min(returns, key=returns.get); return (lane, returns[lane])
        return (None, None)
    if soon:
        lane = min(soon, key=soon.get); return (lane, soon[lane])
    if plan in ('personal-codex', 'personal-claude'):
        used, _ = lane_state(plan)
        if used is not None and used >= PERSONAL_SPARE: return 'skip'
    return None


def queue_job(a, lane, t):
    os.makedirs(QUEUE, exist_ok=True)
    key = hashlib.sha256((os.path.abspath(a.prompt_file) + os.path.abspath(a.workspace)).encode()).hexdigest()[:10]
    rec = {'id': key, 'prompt_file': os.path.abspath(a.prompt_file), 'workspace': os.path.abspath(a.workspace), 'difficulty': a.difficulty, 'skip': a.skip,
           'experiment': a.experiment, 'writing': a.writing, 'not_before': t, 'not_before_local': fmt(t) if t else None, 'lane': lane,
           'queued_at': dt.datetime.now().isoformat(timespec='seconds')}
    json.dump(rec, open(QUEUE + '/' + key + '.json', 'w'))
    return key


ap = argparse.ArgumentParser(); ap.add_argument('--prompt-file'); ap.add_argument('--workspace')
ap.add_argument('--skip', default='')
ap.add_argument('--experiment', action='store_true')
ap.add_argument('--order', action='store_true')
ap.add_argument('--writing', action='store_true')  # scientific-writing job: the Sundial slot is live
ap.add_argument('--difficulty', choices=['light', 'medium', 'heavy'], default='medium')
ap.add_argument('--urgent', action='store_true')
ap.add_argument('--queue', action='store_true'); ap.add_argument('--resume'); ap.add_argument('--force', action='store_true')
a = ap.parse_args()
if a.queue:
    for f in sorted(os.listdir(QUEUE)) if os.path.isdir(QUEUE) else []:
        r = json.load(open(QUEUE + '/' + f)); print(r['id'], 'not before', r.get('not_before_local'), 'lane', r.get('lane'), r['difficulty'], r['prompt_file'])
    sys.exit(0)
if a.resume:
    r = json.load(open(QUEUE + '/' + a.resume + '.json'))
    a.prompt_file, a.workspace, a.difficulty, a.skip, a.experiment, a.writing = r['prompt_file'], r['workspace'], r['difficulty'], r['skip'], r['experiment'], r['writing']
    if r.get('not_before') and r['not_before'] > time.time() and not a.force and not a.urgent:
        print('plan-rr: WAIT until', r['not_before_local'], 'for', r.get('lane'), '(still queued: ' + a.resume + ')', file=sys.stderr); sys.exit(5)
if not a.order and not (a.prompt_file and a.workspace): ap.error('--prompt-file and --workspace are required')
skip = set(filter(None, a.skip.split(',')))
LIST = order_for(a.difficulty, a.writing)
if a.order:
    print('difficulty', a.difficulty, '(wait rule: personal lanes only when no Vals/Stanford lane returns within %dh, or --urgent)' % WAIT_HOURS)
    print('\n'.join(p + ' ' + (m or '') + (' (skipped)' if p in skip else '') for p, m in LIST)); sys.exit(0)
def agy_ready():
    r = subprocess.run(ROUTER + ['refresh', '--plan', 'personal-agy'], capture_output=True, text=True)
    if r.returncode: return False
    exp = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
    subprocess.run(ROUTER + ['observe', '--plan', 'personal-agy', '--window', 'auth', '--status', 'ready', '--expires-at', exp,
                             '--source', 'native agy /usage answered'], capture_output=True, text=True)
    return True
for _ap in ('stanford-claude', 'vals-claude-opus'):
    if _ap in skip: continue
    # AT-3467/AT-3415: the Claude lanes' attestations lapse every 24 h; renew each from a fresh native read (overage rejected, under 80% used) when under 6 h are left.
    try: subprocess.run([sys.executable, H + '/.local/bin/plan-attest-auto', '--plan', _ap], stdout=sys.stderr, stderr=sys.stderr, timeout=150)
    except Exception as e: print('plan-rr: attest-auto skipped:', _ap, type(e).__name__, file=sys.stderr)
checked = False
personal_cleared = False
for plan, model in LIST:
    if plan in skip: continue
    if plan == 'sundial':
        if not a.writing: continue
        print('plan-rr: sundial slot reached: do this scientific-writing pass with the Sundial skill (curl -fsSL https://www.sundial.md/start); no model lane ran', file=sys.stderr); sys.exit(4)
    if plan in PERSONAL:
        verdict = decide_personal(plan, a)
        if verdict == 'skip':
            print('plan-rr: skipped', plan, 'over the %d%% spare line for a medium job (use --urgent)' % PERSONAL_SPARE, file=sys.stderr); continue
        if verdict is not None:
            lane, t = verdict
            if lane:
                key = queue_job(a, lane, t)
                print('plan-rr: WAIT until', fmt(t), 'for', lane, '(queued ' + key + '; run: plan-rr --resume ' + key + '). Personal lanes are kept for urgent jobs or when no Vals/Stanford lane returns within %dh.' % WAIT_HOURS, file=sys.stderr)
                sys.exit(5)
            print('plan-rr: no Vals or Stanford lane is back soon and this job is', a.difficulty + '; a personal lane is not used without --urgent', file=sys.stderr); sys.exit(3)
    if plan == 'vals-codex' and a.difficulty != 'light':
        for _ in range(24):  # the Vals Codex profile takes one job at a time: wait up to 2 minutes for it before using a lower lane
            if not vals_codex_busy(): break
            time.sleep(5)
    if plan.startswith('native:'):
        # Same quota refresh, entitlement and read-only clamp as direct router jobs.
        plan = {'native:cursor': 'personal-cursor', 'native:grok': 'personal-grok'}[plan]
    if plan == 'pi:stanford-stair-bm':
        r = subprocess.run([H + '/.local/bin/stair-bm-run', '--prompt-file', a.prompt_file, '--model', model], capture_output=True, text=True, cwd=a.workspace)
        if r.returncode == 3:
            print(r.stderr, file=sys.stderr); continue
        pass
        print('plan-rr: ran', plan, model, file=sys.stderr)
        sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); sys.exit(r.returncode)
    if plan.startswith('pi:'):
        LOG = H + '/.local/state/plan-router/pi-spend-log.jsonl'
        today = dt.date.today().isoformat()
        used = sum(1 for l in (open(LOG) if os.path.exists(LOG) else []) if json.loads(l)['day'] == today and json.loads(l)['plan'] == plan)
        if used >= 6 or len(open(a.prompt_file).read()) > 20000:  # paid keys: small jobs, 6 a day each until Brando sets a cap
            print('plan-rr: skipped', plan, 'pay-per-call cap (6 jobs a day, 20k characters)', file=sys.stderr); continue
        env = dict(os.environ, PATH=PI_PATH + ':' + os.environ.get('PATH', ''))
        # 2026-11-21 (AT-3285): Allen's key runs Argon at high effort; on a 503 or no answer, 3.1 Pro high. Carbon is not used (times out).
        tries = [(model, ['--thinking', 'high']), ('gemini-3.1-pro-preview', ['--thinking', 'high'])] if plan == 'pi:allen-google-veribench' else [(model, [])]
        for model, extra in tries:
            try: r = subprocess.run(['pi', '--provider', plan[3:], '--model', model] + extra + ['-p', open(a.prompt_file).read()], capture_output=True, text=True, cwd=a.workspace, env=env, timeout=240)
            except subprocess.TimeoutExpired: r = subprocess.CompletedProcess([], 1, '', 'timeout')
            if not r.returncode and r.stdout.strip(): break
        if r.returncode or not r.stdout.strip():
            print('plan-rr: skipped', plan, model, r.stderr.strip()[:200], file=sys.stderr); continue
        pass
        open(LOG, 'a').write(json.dumps({'day': today, 'plan': plan, 'model': model, 'prompt_chars': len(open(a.prompt_file).read()), 'out_chars': len(r.stdout)}) + '\n')
        print('plan-rr: ran', plan, model, file=sys.stderr); sys.stdout.write(r.stdout); sys.exit(0)
    if plan == 'personal-agy':
        AGY_LOG = STATE_DIR + '/agy-log.jsonl'
        today = dt.date.today().isoformat()
        used = sum(1 for l in (open(AGY_LOG) if os.path.exists(AGY_LOG) else []) if json.loads(l)['day'] == today)
        if used >= AGY_DAILY_CAP:
            print('plan-rr: skipped personal-agy', 'daily cap of %d jobs reached' % AGY_DAILY_CAP, file=sys.stderr); skip.add(plan); continue
        if not checked: checked = agy_ready()
        if not checked: skip.add(plan); continue
    cmd = ROUTER + ['run', '--plan', plan, '--prompt-file', a.prompt_file, '--workspace', a.workspace]
    if model: cmd += ['--model', model]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout + r.stderr
    if '"skipped"' in out or 'no eligible plan' in out:
        print('plan-rr: skipped', plan, model or '', out.strip()[:200], file=sys.stderr); continue
    pass
    if plan == 'personal-agy': open(STATE_DIR + '/agy-log.jsonl', 'a').write(json.dumps({'day': dt.date.today().isoformat(), 'model': model}) + '\n')
    print('plan-rr: ran', plan, model or '(plan default)', 'difficulty', a.difficulty, file=sys.stderr)
    sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); sys.exit(r.returncode)
print('plan-rr: no route ran', file=sys.stderr); sys.exit(3)
