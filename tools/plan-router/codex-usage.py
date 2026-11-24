#!/usr/bin/env python3
"""codex-usage: read-only 5-hour and weekly usage of one Codex account (2026-11-24, AT-3455).

Asks `codex app-server` for account/read and account/rateLimits/read; never starts inference, never prints keys.
Example: python3 codex_usage.py --home ~/.codex
Prints one JSON line: account, plan, primary/secondary usedPercent, windowDurationMins, resetsAt (epoch and ISO), credits, observed_at.
--gate 80 [--expect brandojazz@gmail.com]: router pre-launch check. Prints "Logged in using ChatGPT; ..." and exits 0 only when the account matches,
ordinary included usage is allowed, no credits exist, and every window is under the reserve (percent used) and not past its reset; else exits 1 with the reason on stderr.
"""
import argparse, datetime as dt, json, os, select, signal, subprocess, time
ap = argparse.ArgumentParser(); ap.add_argument('--home', default=os.path.expanduser('~/.codex')); ap.add_argument('--gate', type=float); ap.add_argument('--expect'); a = ap.parse_args()
env = dict(os.environ, CODEX_HOME=os.path.expanduser(a.home)); env.pop('OPENAI_API_KEY', None)
p = subprocess.Popen(['codex', 'app-server', '--stdio'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env, start_new_session=True)
rep = {}
def send(v): p.stdin.write(json.dumps(v) + '\n'); p.stdin.flush()
try:
    send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'codex_usage', 'title': 'Codex usage', 'version': '1.0'}}})
    end = time.monotonic() + 14
    pending = b''
    while time.monotonic() < end and len(rep) < 2:
        if not select.select([p.stdout], [], [], .2)[0]: continue
        chunk = os.read(p.stdout.fileno(), 65536)  # raw reads: replies that arrive together are all seen
        if not chunk: break
        pending += chunk
        while b'\n' in pending:
            line, pending = pending.split(b'\n', 1)
            v = json.loads(line)
            if v.get('id') == 1:
                send({'method': 'initialized', 'params': {}}); send({'id': 2, 'method': 'account/read', 'params': {}}); send({'id': 3, 'method': 'account/rateLimits/read', 'params': {}})
            if v.get('id') in (2, 3): rep[v['id']] = v
    acct = rep[2]['result']['account']; res = rep[3]['result']; r = res['rateLimitsByLimitId']['codex']
    out = {'account': acct.get('email'), 'plan': acct.get('planType'), 'credits': r.get('credits'), 'ordinaryUsageAllowed': res.get('ordinaryUsageAllowed'),
           'rateLimitReachedType': r.get('rateLimitReachedType'), 'observed_at': dt.datetime.now(dt.timezone.utc).isoformat()}
    for w in ('primary', 'secondary'):
        row = r.get(w)
        if row: out[w] = {'usedPercent': row['usedPercent'], 'windowDurationMins': row.get('windowDurationMins'), 'resetsAt': row['resetsAt'],
                          'resetsAtISO': dt.datetime.fromtimestamp(row['resetsAt'], dt.timezone.utc).isoformat()}
    if a.gate is not None:
        why = None
        if a.expect and acct.get('email') != a.expect: why = 'unexpected account'
        elif out['ordinaryUsageAllowed'] is False or out['rateLimitReachedType']: why = 'included usage reached (' + str(out['rateLimitReachedType']) + ')'
        elif not isinstance(out['credits'], dict) or out['credits'].get('hasCredits') is not False or out['credits'].get('unlimited') is not False: why = 'cannot rule out usage credits'
        else:
            for w in ('primary', 'secondary'):
                if w in out and (out[w]['usedPercent'] >= a.gate or out[w]['resetsAt'] <= time.time()): why = w + ' window ' + str(out[w]['usedPercent']) + '% used, reserve ' + str(a.gate) + '%'
        if why:
            import sys; print('Codex usage gate blocked: ' + why, file=sys.stderr); raise SystemExit(1)
        print('Logged in using ChatGPT; included-usage reserve passed: ' + ', '.join(w + ' ' + str(out[w]['usedPercent']) + '% used' for w in ('primary', 'secondary') if w in out))
    else:
        print(json.dumps(out))
finally:
    try: os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    p.wait(timeout=3)
