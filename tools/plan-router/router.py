#!/usr/bin/env python3
"""Bounded subscription CLI jobs; private observations, audit logs and workspace locks."""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

UTC = dt.timezone.utc
SCRUB = re.compile(r'^(ANTHROPIC_|OPENAI_|AZURE_OPENAI_|GEMINI_|GOOGLE_|GROK_|XAI_|CURSOR_|CLAUDE_CODE_USE_|CLAUDE_CODE_OAUTH_TOKEN$|CLAUDE_CONFIG_DIR$|CODEX_HOME$|CODEX_API_KEY$|CODEX_CONFIG_|CLAUDE_CODE_API_|API_KEY$)')


def stamp():
    return dt.datetime.now(UTC).isoformat()


def epoch(value):
    value = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('timestamps must include a timezone')
    return value.timestamp()


def save(path, data):
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with open(tmp, 'x', encoding='utf-8') as stream:
        os.chmod(tmp, 0o600)
        json.dump(data, stream, indent=2)
        stream.write('\n')
    os.replace(tmp, path)


def private_dir(path, forbidden=None):
    path = Path(path).expanduser().resolve()
    if forbidden and (path == forbidden or forbidden in path.parents):
        raise ValueError('private state must be outside a Git checkout')
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.stat().st_uid != os.getuid():
        raise ValueError('private directory has another owner')
    os.chmod(path, 0o700)
    return path


@contextlib.contextmanager
def locked(path, nonblocking=False):
    with open(path, 'a', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0))
        except BlockingIOError:
            raise ValueError('workspace already has a plan-router writer') from None
        yield stream.fileno()


def config(path):
    data = json.loads(Path(path).expanduser().read_text())
    plans = data['plans']
    ids = [p['id'] for p in plans]
    if len(ids) != len(set(ids)) or not plans:
        raise ValueError('plan IDs must be unique and nonempty')
    for p in plans:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', p['id']):
            raise ValueError('invalid plan ID')
        if p['provider'] not in ('agy', 'claude', 'codex', 'cursor', 'grok'):
            raise ValueError('unsupported provider')
        if not p.get('model') or not isinstance(p.get('argv'), list) or not p['argv']:
            raise ValueError('each plan needs a pinned model and argv')
        if any(not isinstance(arg, str) for arg in p['argv']):
            raise ValueError('argv must contain strings')
        joined = ' '.join(p['argv'])
        if not any(arg in ('--model', '-m') and n + 1 < len(p['argv']) and p['argv'][n + 1] == p['model'] for n, arg in enumerate(p['argv'])):
            raise ValueError('argv must explicitly select the configured model')
        if any(x in joined for x in ('danger-full-access', 'bypass-approvals', 'skip-permissions', 'bypassPermissions', '--yolo', '--force', '--sandbox=off', '--sandbox=disabled')):
            raise ValueError('sandbox/approval bypass is not supported')
        if '--sandbox' in p['argv']:
            index = p['argv'].index('--sandbox')
            if index + 1 == len(p['argv']) or p['argv'][index + 1] not in ('read-only', 'workspace-write', 'enabled', 'workspace', 'strict'):
                raise ValueError('sandbox must stay enabled')
        if p['provider'] == 'codex' and ('forced_login_method=chatgpt' not in joined or '--sandbox' not in p['argv']):
            raise ValueError('Codex requires forced ChatGPT login and an explicit sandbox')
        if p['provider'] == 'claude' and '--bare' in p['argv']:
            raise ValueError('Claude bare mode does not use subscription login')
        if set(p.get('env', {})) - {'CODEX_HOME', 'CLAUDE_CONFIG_DIR'}:
            raise ValueError('env accepts only native account profile directories')
        if p.get('effort_flag') not in (None, '--effort'):
            raise ValueError('effort_flag must be --effort when the native client supports it')
        if p.get('allow_unknown_native') and (p['provider'] not in ('claude', 'codex', 'cursor', 'grok') or not p.get('auth', {}).get('argv')):
            raise ValueError('unknown native allowance requires a supported native authentication status command')
        if not math.isfinite(float(p.get('timeout_seconds', 180))) or not 0 < float(p.get('timeout_seconds', 180)) <= 14400:
            raise ValueError('timeout must be positive and at most four hours')
        catalog = p.get('models', [])
        if not isinstance(catalog, list) or len({m['id'] for m in catalog}) != len(catalog):
            raise ValueError('model catalog IDs must be unique within a plan')
        for model in catalog:
            if any(not isinstance(model.get(k), str) or not model[k] for k in ('id', 'label', 'family', 'effort', 'refresh_group', 'quota_group')):
                raise ValueError('catalog requires id, label, family, effort and quota pool names')
            if any(not isinstance(model.get(k), bool) for k in ('frontier', 'enabled', 'verified')):
                raise ValueError('catalog requires explicit frontier, enabled and verified booleans')
        if catalog and p['model'] not in {m['id'] for m in catalog}:
            raise ValueError('pinned model must exist in its catalog')
    if data.get('default_plan', ids[0]) not in ids:
        raise ValueError('default_plan is unknown')
    return data


def predict_difficulty(prompt):
    """Transparent local routing hint, not an estimate of model quality."""
    text = prompt.lower()
    rules = [('multistep', r'\b(multi[- ]step|end[- ]to[- ]end|across (?:multiple |several )?(?:files|repos)|implement.*(?:test|deploy))\b'),
             ('hard', r'\b(prove|theorem|formal verification|architecture|complex|root cause|research|optimi[sz]e)\b'),
             ('easy', r'\b(typo|spelling|format(?:ting)?|rename|simple|summari[sz]e|translate)\b')]
    for difficulty, pattern in rules:
        found = re.search(pattern, text, re.S)
        if found:
            return difficulty, 'local keyword heuristic: ' + found.group(0)
    return 'medium', 'local keyword heuristic: medium default'


def model_copy(plan, model):
    selected = dict(plan, model=model['id'], effort=model['effort'],
                    refresh_group=model['refresh_group'], quota_group=model['quota_group'],
                    model_frontier=model['frontier'])
    selected['argv'] = list(plan['argv'])
    for index, arg in enumerate(selected['argv'][:-1]):
        if arg in ('--model', '-m'):
            selected['argv'][index + 1] = model['id']
    if '--effort' in selected['argv']:
        selected['argv'][selected['argv'].index('--effort') + 1] = model['effort']
    elif plan.get('effort_flag'):
        selected['argv'] += [plan['effort_flag'], model['effort']]
    return selected


def select_model(plan, args, data, prompt):
    """Explicit plans and scientific jobs keep their pin absent a model override."""
    catalog = plan.get('models', [])
    requested, effort = args.model, args.effort
    difficulty, reason = None, 'configured plan/model pin'
    automatic = args.generic and not args.plan and not requested and not effort
    if args.difficulty != 'auto' and (not args.generic or args.plan):
        raise ValueError('--difficulty requires --generic without --plan; explicit plans stay pinned')
    if automatic:
        difficulty, reason = predict_difficulty(prompt) if args.difficulty == 'auto' else (args.difficulty, 'explicit difficulty')
        mapping_key = 'frontier_difficulty_defaults' if args.frontier_only else 'difficulty_defaults'
        mapping = plan.get(mapping_key, data.get(mapping_key, {})) if catalog else {}
        requested = mapping.get(difficulty)
        if requested:
            reason += '; configured difficulty default'
    elif requested or effort:
        reason = 'explicit model/effort override'
    if not catalog:
        if requested and requested != plan['model'] or effort:
            raise ValueError('model/effort override requires a matching verified catalog entry')
        if args.frontier_only and not (plan.get('frontier') is True and plan.get('model_verified') is True):
            raise ValueError('frontier-only requires verified frontier model metadata')
        return dict(plan, difficulty=difficulty, selection_reason=reason)
    exact = next((m for m in catalog if m['id'] == (requested or plan['model'])), None)
    if exact and not effort:
        model = exact
    else:
        family = exact['family'] if exact else (requested or next(m['family'] for m in catalog if m['id'] == plan['model']))
        wanted_effort = effort or 'medium'
        matches = [m for m in catalog if m['family'] == family and m['effort'] == wanted_effort]
        if len(matches) != 1:
            raise ValueError('unsupported or ambiguous model/effort: ' + family + '/' + wanted_effort)
        model = matches[0]
    if not model['enabled'] or not model['verified']:
        raise ValueError('selected model disabled or unverified: ' + model['id'])
    if args.frontier_only and not model['frontier']:
        raise ValueError('selected model is not frontier: ' + model['id'])
    return dict(model_copy(plan, model), difficulty=difficulty, selection_reason=reason)


def environment(plan):
    env = {k: v for k, v in os.environ.items() if not SCRUB.match(k)}
    for key, value in plan.get('env', {}).items():
        env[key] = os.path.expanduser(value)
    return env


def observations(state):
    path = state / 'observations.json'
    return json.loads(path.read_text()) if path.exists() else {}


def fresh(item, now):
    return bool(item and epoch(item['observed_at']) <= now < epoch(item['expires_at']))


def gate(plan, obs, now):
    if plan.get('enabled', True) is not True:
        return 'plan disabled'
    model = next((m for m in plan.get('models', []) if m['id'] == plan['model']), None)
    if model and (not model['enabled'] or not model['verified']):
        return 'selected model disabled or unverified'
    proof = plan.get('subscription_only', {})
    if proof.get('verified') is not True or not proof.get('evidence') or epoch(proof.get('expires_at', '1970-01-01T00:00:00Z')) <= now:
        return 'subscription entitlement / no-extra-usage verification missing or expired'
    group = plan.get('quota_group', plan['id'])
    for window, ceiling in [('weekly', 80), ('short', 100)]:
        item = obs.get(group, {}).get(window)
        if not fresh(item, now) or epoch(item['reset_at']) <= now:
            if plan.get('allow_unknown_native'):
                continue  # Explicitly approved native subscription; quota remains unknown.
            availability = obs.get(plan['id'], {}).get('availability')
            if plan.get('allow_unknown_once') and fresh(availability, now) and availability['status'] == 'ready' and not availability.get('consumed'):
                continue
            return window + ' quota unknown or stale'
        if item['status'] != 'ready' or item['used_percent'] >= ceiling:
            return window + ' quota threshold reached'
    return None


def execute(argv, prompt, workspace, env, timeout, stdout, stderr, lock_fd=None):
    """Own the entire process group; never leave grandchildren after completion/timeout."""
    with open(stdout, 'wb') as out, open(stderr, 'wb') as err:
        os.chmod(stdout, 0o600)
        os.chmod(stderr, 0o600)
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                cwd=workspace, env=env, start_new_session=True,
                                pass_fds=(() if lock_fd is None else (lock_fd,)))
        timed_out = False
        try:
            proc.communicate(prompt.encode(), timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            timed_out = True
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
        finally:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
    return proc.returncode, timed_out


def auth_ok(plan, path):
    text = path.read_text(errors='replace')[:100000]
    if plan['provider'] != 'claude':
        text += path.with_suffix('.stderr').read_text(errors='replace')[:100000]
    if re.search(r'not (?:logged in|signed in|authenticated)|unauthenticated|(?:login|authentication) required|unable to fetch user details|invalid (?:session|token)', text, re.I):
        return False
    if plan['provider'] == 'claude':
        try:
            data = json.loads(text)
            return data.get('loggedIn') is True and data.get('apiProvider') == 'firstParty' and data.get('authMethod') in ('claude.ai', 'oauth_token')
        except ValueError:
            return False
    if plan['provider'] == 'codex':
        return bool(re.search(r'Logged in using ChatGPT', text, re.I))
    pattern = plan.get('auth', {}).get('match')
    return bool(pattern and re.search(pattern, text, re.I))


def result_error(path):
    """Some native clients return process exit 0 for a structured failed turn."""
    text = path.read_text(errors='replace')
    try:
        events = [json.loads(text)]
    except ValueError:
        events = []
        for line in text.splitlines():
            with contextlib.suppress(ValueError):
                events.append(json.loads(line))
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get('is_error') is True or event.get('type') == 'turn.failed' or str(event.get('status', '')).upper() in ('ERROR', 'FAILED', 'FAILURE', 'CANCELLED', 'TIMEOUT') or event.get('terminal_reason') in ('api_error', 'max_turns'):
            return True
        if event.get('type') == 'result' and str(event.get('subtype', '')).startswith('error'):
            return True
        if isinstance(event.get('error'), (str, dict)) and event['error']:
            return True
    return False


def token_usage(path):
    """Only structured counters, never guess from text or list-price estimates."""
    text = path.read_text(errors='replace')
    try:
        events = [json.loads(text)]
    except ValueError:
        events = []
        for line in text.splitlines():
            with contextlib.suppress(ValueError):
                events.append(json.loads(line))
    # Claude result usage is authoritative; Codex emits per-turn usage. Do not
    # recursively count nested message usage and double count an aggregate.
    found = []
    for event in events:
        if not isinstance(event, dict):
            continue
        result = event.get('result')
        usage = event.get('usage') or (result.get('usage') if isinstance(result, dict) else None)
        if not isinstance(usage, dict):
            continue
        # Cursor's native result uses camelCase. Normalize its aggregate once;
        # never add the same aggregate again from per-model metadata.
        usage = dict(usage)
        for native, canonical in [('inputTokens', 'input_tokens'),
                                  ('outputTokens', 'output_tokens'),
                                  ('cacheReadTokens', 'cache_read_input_tokens'),
                                  ('cacheWriteTokens', 'cache_creation_input_tokens')]:
            if native in usage and canonical not in usage:
                usage[canonical] = usage[native]
        counters = {k: v for k, v in usage.items() if k.endswith('tokens') and isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0}
        if counters:
            found.append(counters)
    return {k: sum(row.get(k, 0) for row in found) for k in {k for row in found for k in row}} or None


def refresh(plan, state):
    if not plan.get('refresh_argv'):
        return False
    folder = state / ('refresh-' + uuid.uuid4().hex)
    folder.mkdir(mode=0o700)
    rc, timeout = execute(plan['refresh_argv'], '', str(state), environment(plan), 20,
                          folder / 'stdout', folder / 'stderr')
    if timeout or rc:
        raise ValueError(plan['id'] + ': quota refresh failed; no inference started')
    now, found = time.time(), {}
    for line in (folder / 'stdout').read_text().splitlines():
        parts = line.split('\t')
        if len(parts) != 4 or parts[0] != plan.get('refresh_group', 'Gemini Models'):
            continue
        window = {'Weekly Limit Remaining': 'weekly', 'Five Hour Limit Remaining': 'short'}.get(parts[1])
        if not window:
            continue
        remaining = float(parts[2].rstrip('%'))
        reset = epoch(parts[3])
        if not math.isfinite(remaining) or not 0 <= remaining <= 100 or reset <= now:
            raise ValueError('invalid native quota observation')
        found[window] = {'observed_at': stamp(), 'expires_at': dt.datetime.fromtimestamp(min(now + 900, reset), UTC).isoformat(), 'reset_at': parts[3], 'used_percent': 100 - remaining, 'status': 'ready', 'source': 'native CLI /usage; ' + parts[0]}
    if set(found) != {'weekly', 'short'}:
        raise ValueError('native usage did not return both matching quota windows')
    with locked(state / 'state.lock'):
        obs = observations(state)
        obs.setdefault(plan.get('quota_group', plan['id']), {}).update(found)
        save(state / 'observations.json', obs)
    return True


def admit(plan, state):
    with locked(state / 'state.lock'):
        obs = observations(state)
        reason = gate(plan, obs, time.time())
        if reason:
            raise ValueError(reason)
        windows = obs.get(plan.get('quota_group', plan['id']), {})
        if not plan.get('allow_unknown_native') and any(not fresh(windows.get(w), time.time()) or epoch(windows[w]['reset_at']) <= time.time() for w in ('weekly', 'short')):
            obs[plan['id']]['availability']['consumed'] = True
            save(state / 'observations.json', obs)


def observe(args, plans, state):
    plan = next((p for p in plans if p['id'] == args.plan), None)
    if not plan:
        raise ValueError('unknown plan')
    now = time.time()
    if not now < epoch(args.expires_at):
        raise ValueError('observation must expire in the future')
    item = {'observed_at': stamp(), 'expires_at': args.expires_at, 'status': args.status, 'source': args.source}
    if args.window in ('weekly', 'short'):
        if args.used_percent is None or not math.isfinite(args.used_percent) or not 0 <= args.used_percent <= 100 or not args.reset_at:
            raise ValueError('quota requires 0..100 used-percent and reset-at')
        if epoch(args.reset_at) <= now or epoch(args.expires_at) > epoch(args.reset_at):
            raise ValueError('expiry must be at or before a future reset')
        item.update(used_percent=args.used_percent, reset_at=args.reset_at)
    group = args.plan if args.window in ('auth', 'availability') else plan.get('quota_group', args.plan)
    with locked(state / 'state.lock'):
        obs = observations(state)
        obs.setdefault(group, {})[args.window] = item
        save(state / 'observations.json', obs)
    print(json.dumps({'plan': args.plan, 'window': args.window, **item}))


def status(plans, state):
    obs, now = observations(state), time.time()
    all_jobs = [json.loads(p.read_text()) for p in (state / 'jobs').glob('*/receipt.json')]
    for plan in plans:
        windows = {}
        for window in ('weekly', 'short'):
            item = obs.get(plan.get('quota_group', plan['id']), {}).get(window)
            windows[window] = {**(item or {}), 'freshness': 'fresh' if fresh(item, now) and epoch(item['reset_at']) > now else ('stale' if item else 'unknown')}
        jobs = [j for j in all_jobs if j['plan'] == plan['id']]
        per_model = []
        for model_id in sorted({m['id'] for m in plan.get('models', [])} | {j['model'] for j in jobs} | {plan['model']}):
            model = next((m for m in plan.get('models', []) if m['id'] == model_id), None)
            item = {'model': model_id, **job_summary([j for j in jobs if j['model'] == model_id])}
            if model:
                item.update(effort=model['effort'], quota_group=model['quota_group'],
                            windows={w: {**obs.get(model['quota_group'], {}).get(w, {}),
                                         'freshness': 'fresh' if fresh(obs.get(model['quota_group'], {}).get(w), now) and epoch(obs[model['quota_group']][w]['reset_at']) > now else ('stale' if obs.get(model['quota_group'], {}).get(w) else 'unknown')}
                                     for w in ('weekly', 'short')})
            per_model.append(item)
        print(json.dumps({'plan': plan['id'], 'model': plan['model'], 'note': plan.get('status_note'), 'gate': gate(plan, obs, now) or 'eligible; authentication checked at launch', 'windows': windows, 'availability': obs.get(plan['id'], {}).get('availability'), **job_summary(jobs), 'models': per_model, 'usage_note': 'reported JSON tokens only; not subscription allowance or billing'}))


def job_summary(jobs):
    tokens = {}
    for job in jobs:
        for key, value in (job.get('tokens') or {}).items():
            tokens[key] = tokens.get(key, 0) + value
    return {'jobs': len(jobs), 'completed': sum(j['status'] == 'completed' for j in jobs), 'tokens': tokens or None}


def list_models(plans, plan_id=None):
    if plan_id and plan_id not in {p['id'] for p in plans}:
        raise ValueError('unknown plan')
    for plan in plans:
        if not plan_id or plan['id'] == plan_id:
            for model in plan.get('models', []):
                print(json.dumps({'plan': plan['id'], **model, 'pinned_default': model['id'] == plan['model']}))


def run(args, data, state):
    plans = data['plans']
    selected = args.plan or data.get('default_plan', plans[0]['id'])
    primary = next((p for p in plans if p['id'] == selected), None)
    if not primary:
        raise ValueError('unknown plan')
    if args.allow_fallback and not args.generic:
        raise ValueError('fallback requires --generic; scientific jobs stay pinned')
    candidates = [primary]
    if args.allow_fallback:
        candidates += [p for p in plans if p['id'] != selected and p.get('generic_fallback', False)]
    workspace = Path(args.workspace).expanduser().resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError('workspace must be a directory')
    prompt = Path(args.prompt_file).expanduser().read_text()
    primary = select_model(primary, args, data, prompt)
    candidates[0] = primary
    locks = private_dir(Path('/tmp') / ('plan-router-' + str(os.getuid())))
    key = hashlib.sha256(str(workspace).encode()).hexdigest()
    if state == workspace or workspace in state.parents:
        raise ValueError('private state must be outside the job workspace')
    with locked(locks / (key + '.lock'), nonblocking=True) as lock_fd:
        for index, plan in enumerate(candidates):
            if index:
                try:
                    fallback_args = argparse.Namespace(**vars(args))
                    fallback_args.plan, fallback_args.difficulty = plan['id'], 'auto'
                    plan = select_model(plan, fallback_args, data, prompt)
                    plan['difficulty'] = primary['difficulty']
                    plan['selection_reason'] = 'explicitly permitted preflight fallback; ' + plan['selection_reason']
                except ValueError as error:
                    print(json.dumps({'plan': plan['id'], 'skipped': str(error)}), file=sys.stderr)
                    continue
            if plan.get('enabled', True) is not True:
                print(json.dumps({'plan': plan['id'], 'skipped': 'plan disabled'}), file=sys.stderr)
                continue
            if plan.get('refresh_argv'):
                refresh(plan, state)
            reason = gate(plan, observations(state), time.time())
            if reason:
                print(json.dumps({'plan': plan['id'], 'skipped': reason}), file=sys.stderr)
                continue
            job = state / 'jobs' / (dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:10])
            job.mkdir(mode=0o700, parents=True)
            auth = plan.get('auth', {})
            if auth.get('argv'):
                try:
                    rc, timeout = execute(auth['argv'], '', workspace, environment(plan), 20, job / 'auth.stdout', job / 'auth.stderr', lock_fd)
                except FileNotFoundError:
                    print(json.dumps({'plan': plan['id'], 'skipped': 'client missing'}), file=sys.stderr)
                    continue
                if timeout:
                    raise ValueError('authentication check timed out; no fallback attempted')
                if rc or not auth_ok(plan, job / 'auth.stdout'):
                    print(json.dumps({'plan': plan['id'], 'skipped': 'subscription authentication unconfirmed'}), file=sys.stderr)
                    continue
            elif not fresh(observations(state).get(plan['id'], {}).get('auth'), time.time()) or observations(state)[plan['id']]['auth']['status'] != 'ready':
                print(json.dumps({'plan': plan['id'], 'skipped': 'authentication observation missing or stale'}), file=sys.stderr)
                continue
            admit(plan, state)
            argv = [arg.replace('{prompt}', prompt).replace('{workspace}', str(workspace)) for arg in plan['argv']]
            receipt = {'plan': plan['id'], 'model': plan['model'], 'effort': plan.get('effort'), 'difficulty': plan.get('difficulty'), 'selection_reason': plan['selection_reason'], 'workspace': str(workspace), 'started_at': stamp(), 'status': 'running', 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
            save(job / 'receipt.json', receipt)
            try:
                rc, timeout = execute(argv, '' if any('{prompt}' in x for x in plan['argv']) else prompt, workspace, environment(plan), float(plan.get('timeout_seconds', 180)), job / 'stdout', job / 'stderr', lock_fd)
                receipt.update(status='timeout' if timeout else ('completed' if rc == 0 and not result_error(job / 'stdout') else 'failed'), returncode=rc, tokens=token_usage(job / 'stdout'))
            except OSError as error:
                receipt.update(status='failed', error=str(error), tokens=None)
            receipt['finished_at'] = stamp()
            save(job / 'receipt.json', receipt)
            if receipt['status'] == 'completed' and plan.get('allow_unknown_once') and plan.get('renew_availability_on_success'):
                # A successful native request can admit the next bounded job. A
                # failure leaves the previous one-shot observation consumed.
                now = time.time()
                expires = min(now + 900, epoch(plan['subscription_only']['expires_at']))
                with locked(state / 'state.lock'):
                    obs = observations(state)
                    obs.setdefault(plan['id'], {})['availability'] = {
                        'observed_at': stamp(),
                        'expires_at': dt.datetime.fromtimestamp(expires, UTC).isoformat(),
                        'status': 'ready', 'source': 'native CLI completed job; remaining allowance unknown'}
                    save(state / 'observations.json', obs)
            print(json.dumps({**receipt, 'logs': str(job)}))
            return 0 if receipt['status'] == 'completed' else 1
    raise ValueError('no eligible plan; no inference command started')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--state-dir', default='~/.local/state/plan-router')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status').add_argument('--refresh', action='store_true')
    sub.add_parser('refresh').add_argument('--plan')
    sub.add_parser('models').add_argument('--plan')
    p = sub.add_parser('observe')
    p.add_argument('--plan', required=True)
    p.add_argument('--window', choices=['weekly', 'short', 'auth', 'availability'], required=True)
    p.add_argument('--status', choices=['ready', 'limited', 'unavailable'], default='ready')
    p.add_argument('--used-percent', type=float)
    p.add_argument('--reset-at')
    p.add_argument('--expires-at', required=True)
    p.add_argument('--source', required=True)
    p = sub.add_parser('run')
    p.add_argument('--plan')
    p.add_argument('--prompt-file', required=True)
    p.add_argument('--workspace', required=True)
    p.add_argument('--generic', action='store_true')
    p.add_argument('--allow-fallback', action='store_true')
    p.add_argument('--model')
    p.add_argument('--effort')
    p.add_argument('--difficulty', choices=['auto', 'easy', 'medium', 'hard', 'multistep'], default='auto')
    p.add_argument('--frontier-only', action='store_true')
    args = parser.parse_args()
    try:
        repo = next((p for p in Path(__file__).resolve().parents if (p / '.git').exists()), None)
        data, state = config(args.config), private_dir(args.state_dir, repo)
        if args.command == 'refresh' or (args.command == 'status' and args.refresh):
            refreshed = set()
            for plan in data['plans']:
                if plan.get('enabled', True) is True and (not getattr(args, 'plan', None) or plan['id'] == args.plan):
                    selections = [plan] + [model_copy(plan, m) for m in plan.get('models', [])
                                           if m['enabled'] and m['verified']]
                    for selected in selections:
                        key = (tuple(selected.get('refresh_argv', [])), selected.get('refresh_group'),
                               selected.get('quota_group', selected['id']))
                        if key not in refreshed:
                            refresh(selected, state)
                            refreshed.add(key)
        if args.command in ('status', 'refresh'):
            status(data['plans'], state)
        elif args.command == 'observe':
            observe(args, data['plans'], state)
        elif args.command == 'models':
            list_models(data['plans'], args.plan)
        else:
            return run(args, data, state)
        return 0
    except (ValueError, KeyError, OSError) as error:
        print('plan-router: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    sys.exit(main())
