#!/usr/bin/env python3
"""plan-rr: run one bounded job on Brando's own AI accounts via the plan router, in priority order (2026-11-23, AT-3397; was round robin 2026-11-21).
Order 2026-11-24 (Brando 09:58): vals-codex, vals-claude-opus, stanford-codex, stanford-claude, STAIR Claude, Sundial (writing only), Koyejo lab key, Cursor, Grok, then Vals key, STAIR/Stanford gateway sol, personal Codex, personal Claude, Allen, Google plan last. Was (Brando, Nov 23 17:25: "always start with vals and stanford first before my personal accounts"): Vals and Stanford routes, then personal Codex and Claude, then Cursor/Grok, Allen's key, and the Google plan last. A route is skipped only when gated, off, or low (router gate, 20% left).
Flags: --experiment (real experiment runs: never the Google plan, Brando Nov 23 12:10), --order (print the order and exit).
Use: plan-rr --prompt-file /abs/job.md --workspace /abs/dir [--skip personal-agy,...]
Google-plan (agy) jobs need the prompt file to start with 'MY VOICE REQUEST' (Brando's format: a request in his voice,
then the precise prompt in triple quotes); other accounts take any prompt. Skips gated or limited plans, moves to the next.
Uses configured subscriptions and explicitly bounded Pi provider routes; never buys credits. Foreground only."""
import argparse, json, os, subprocess, sys, time, datetime as dt
H = os.path.expanduser('~')
ROUTER = [sys.executable, H + '/.local/lib/plan-router/router.py', '--config', H + '/.config/plan-router/config.json']
STATE = H + '/.local/state/plan-router/rr-counter'
ROT = [('vals-codex', None), ('vals-claude-opus', 'claude-opus-5-5'), ('stanford-codex', None), ('stanford-claude', None),
       ('pi:stanford-stair-bm', 'claude-opus-5-5'),  # STAIR Claude: Brando's TODO, key change waits for Zeyu's approval (2026-11-24)
       ('sundial', None),  # writing jobs only (--writing): a skill, not a model lane
       ('pi:koyejolab-openai-bm', 'gpt-6.1-sol'), ('native:cursor', 'grok-4.7-high'), ('native:grok', 'grok-4.7'),
       ('pi:vals-openai-bm', 'gpt-6.1-sol'), ('pi:stanford-stair-bm', 'gpt-6.1-sol'),
       ('personal-codex', None), ('personal-claude', None), ('pi:allen-google-veribench', 'gemini-4-argon'),
       ('personal-agy', 'gemini-4-argon-high'), ('personal-agy', 'gemini-4-carbon-medium'), ('personal-agy', 'claude-opus-5-5-high'), ('personal-agy', 'gemini-pro-orchestrator-argon')]
PI_PATH = '/dfs/scratch0/brando9/bin'
ap = argparse.ArgumentParser(); ap.add_argument('--prompt-file', required=True); ap.add_argument('--workspace', required=True)
ap.add_argument('--skip', default='')
ap.add_argument('--experiment', action='store_true')
ap.add_argument('--order', action='store_true')
ap.add_argument('--writing', action='store_true')  # scientific-writing job: the Sundial slot is live
a = ap.parse_args()
voice = open(a.prompt_file).read().lstrip().startswith('MY VOICE REQUEST')
skip = set(filter(None, a.skip.split(',')))
if a.experiment: skip.add('personal-agy')
if a.order:
    print('\n'.join(p + ' ' + (m or '') + (' (skipped)' if p in skip else '') for p, m in ROT)); sys.exit(0)
n = 0  # priority order: always start at the top (no rotating counter)
def agy_ready():
    r = subprocess.run(ROUTER + ['refresh', '--plan', 'personal-agy'], capture_output=True, text=True)
    if r.returncode: return False
    exp = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
    subprocess.run(ROUTER + ['observe', '--plan', 'personal-agy', '--window', 'auth', '--status', 'ready', '--expires-at', exp,
                             '--source', 'native agy /usage answered'], capture_output=True, text=True)
    return True
checked = False
for i in range(len(ROT)):
    plan, model = ROT[(n + i) % len(ROT)]
    if plan in skip: continue
    if plan == 'sundial':
        if not a.writing: continue
        print('plan-rr: sundial slot reached: do this scientific-writing pass with the Sundial skill (curl -fsSL https://www.sundial.md/start); no model lane ran', file=sys.stderr); sys.exit(4)
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
        if plan == 'pi:allen-google-veribench' and not voice: continue
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
        if not voice: continue
        if not checked: checked = agy_ready()
        if not checked: skip.add(plan); continue
    cmd = ROUTER + ['run', '--plan', plan, '--prompt-file', a.prompt_file, '--workspace', a.workspace]
    if model: cmd += ['--model', model]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout + r.stderr
    if '"skipped"' in out or 'no eligible plan' in out:
        print('plan-rr: skipped', plan, model or '', out.strip()[:200], file=sys.stderr); continue
    pass
    print('plan-rr: ran', plan, model or '(plan default)', file=sys.stderr)
    sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); sys.exit(r.returncode)
print('plan-rr: no route ran', file=sys.stderr); sys.exit(3)
