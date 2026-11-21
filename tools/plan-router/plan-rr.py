#!/usr/bin/env python3
"""plan-rr: round-robin one bounded job across Brando's own AI accounts via the plan router (2026-11-21).
Use: plan-rr --prompt-file /abs/job.md --workspace /abs/dir [--skip personal-agy,...]
Google-plan (agy) jobs need the prompt file to start with 'MY VOICE REQUEST' (Brando's format: a request in his voice,
then the precise prompt in triple quotes); other accounts take any prompt. Skips gated or limited plans, moves to the next.
Uses configured subscriptions and explicitly bounded Pi provider routes; never buys credits. Foreground only."""
import argparse, json, os, subprocess, sys, time, datetime as dt
H = os.path.expanduser('~')
ROUTER = [sys.executable, H + '/.local/lib/plan-router/router.py', '--config', H + '/.config/plan-router/config.json']
STATE = H + '/.local/state/plan-router/rr-counter'
ROT = [('personal-agy', 'gemini-4-argon-high'), ('personal-codex', None), ('personal-agy', 'gemini-4-carbon-medium'), ('personal-claude', None), ('personal-agy', 'claude-opus-5-5-high'), ('native:cursor', 'grok-4.7-high'), ('personal-agy', 'gemini-pro-orchestrator-argon'), ('native:grok', 'grok-4.7'), ('pi:koyejolab-openai-bm', 'gpt-6.1-sol'), ('pi:vals-openai-bm', 'gpt-6.1-sol'), ('pi:allen-google-veribench', 'gemini-4-hydrogen'), ('stanford-codex', None), ('stanford-claude', None)]
ROT += [('vals-claude-opus', 'claude-opus-5-5'), ('pi:stanford-stair-bm', 'claude-opus-5-5'), ('pi:stanford-stair-bm', 'gpt-6.1-sol')]
PI_PATH = '/dfs/scratch0/brando9/bin'
ap = argparse.ArgumentParser(); ap.add_argument('--prompt-file', required=True); ap.add_argument('--workspace', required=True)
ap.add_argument('--skip', default='')
a = ap.parse_args()
voice = open(a.prompt_file).read().lstrip().startswith('MY VOICE REQUEST')
skip = set(filter(None, a.skip.split(',')))
try: n = int(open(STATE).read())
except Exception: n = 0
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
    if plan.startswith('native:'):
        # Same quota refresh, entitlement and read-only clamp as direct router jobs.
        plan = {'native:cursor': 'personal-cursor', 'native:grok': 'personal-grok'}[plan]
    if plan == 'pi:stanford-stair-bm':
        r = subprocess.run([H + '/.local/bin/stair-bm-run', '--prompt-file', a.prompt_file, '--model', model], capture_output=True, text=True, cwd=a.workspace)
        if r.returncode == 3:
            print(r.stderr, file=sys.stderr); continue
        open(STATE, 'w').write(str((n + i + 1) % len(ROT)))
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
        r = subprocess.run(['pi', '--provider', plan[3:], '--model', model, '-p', open(a.prompt_file).read()], capture_output=True, text=True, cwd=a.workspace, env=env, timeout=240)
        if r.returncode or not r.stdout.strip():
            print('plan-rr: skipped', plan, model, r.stderr.strip()[:200], file=sys.stderr); continue
        open(STATE, 'w').write(str((n + i + 1) % len(ROT)))
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
    open(STATE, 'w').write(str((n + i + 1) % len(ROT)))
    print('plan-rr: ran', plan, model or '(plan default)', file=sys.stderr)
    sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); sys.exit(r.returncode)
print('plan-rr: no route ran', file=sys.stderr); sys.exit(3)
