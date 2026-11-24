/** Refresh a stale Grok browser reading and launch one native Cursor/Grok job (2026-11-24).
 * Run in functions.exec with this task's page/screen/tool tools. Load this file with
 * exec_command, then: await new Function(source + '; return xaiAutoLaunch;')()(tools, options).
 * options: {plan: 'personal-cursor'|'personal-grok', prompt: 'scratch/<task>/prompt.md',
 *           reading: 'scratch/<task>/reading.json', out: 'scratch/<task>/result.json'}.
 * Requires a Screen Work run and the existing grok_weekly_read / xai_plan_launch helpers.
 * No timer, background process, credentials, billing change or alternate API.
 */
async function xaiAutoLaunch(tools, options) {
  const {plan, prompt, reading, out} = options;
  if (!['personal-cursor','personal-grok'].includes(plan)) throw Error('unsupported native plan');
  for (const p of [prompt, reading, out]) {
    if (typeof p !== 'string' || !/^scratch\/[A-Za-z0-9_-]+\/[A-Za-z0-9_.-]+$/.test(p)) throw Error('task-owned scratch file required');
  }
  function succeeded(r, label) {
    if (!r || r.isError) throw Error(label + ': ' + JSON.stringify(r));
    return r;
  }
  async function inspect() {
    const cmd = "python3 - <<'XAI_INSPECT'\nimport datetime as dt,json,math\nfrom pathlib import Path\np=Path("+JSON.stringify(reading)+")\ntry:\n d=json.loads(p.read_text()); now=dt.datetime.now(dt.timezone.utc); ts=[dt.datetime.fromisoformat(d[k].replace('Z','+00:00')) for k in ('observed_at','expires_at','reset_at')]; seen,expiry,reset=ts; used=d['used_percent']\n valid=(d.get('schema')=='xai-weekly-v1' and d.get('status')=='ready' and d.get('url')=='https://grok.com/dashboard' and all(t.tzinfo for t in ts) and dt.timedelta(0)<now-seen<dt.timedelta(minutes=10) and now+dt.timedelta(minutes=1)<expiry<=min(seen+dt.timedelta(minutes=10),reset) and isinstance(used,(int,float)) and not isinstance(used,bool) and math.isfinite(used) and 0<=used<=100)\n print(json.dumps({'fresh':valid,'used_percent':used,'observed_at':d.get('observed_at'),'expires_at':d.get('expires_at')}))\nexcept Exception as e: print(json.dumps({'fresh':False,'reason':str(e)}))\nXAI_INSPECT";
    const r = await tools.exec_command({cmd, workdir:'/var/lib/agent', max_output_tokens:1000});
    if (r.exit_code !== 0) throw Error('reading inspection failed');
    return JSON.parse(r.output);
  }
  const before = await inspect();
  let refreshed = false;
  if (!before.fresh) {
    succeeded(await tools.mcp__page__page_goto({url:'https://grok.com/dashboard'}), 'open dashboard');
    succeeded(await tools.mcp__screen__screen_script({path:'notes/tools/grok_weekly_read.py',args:['--out',reading]}), 'capture dashboard');
    refreshed = true;
  }
  const after = await inspect();
  if (!after.fresh) throw Error('refresh did not produce a usable reading; no job launched');
  if (after.used_percent >= 80) throw Error('shared weekly usage at or above 80%; no job launched');
  const launch = succeeded(await tools.mcp__tools__tool_script({path:'notes/tools/xai_plan_launch.py',args:['--reading',reading,'--plan',plan,'--prompt',prompt,'--out',out]}), 'native launch');
  const verified = await xaiVerifyResult(tools, out, plan);
  return {plan, refreshed, before, after, out, verified, launch};
}

async function xaiVerifyResult(tools, out, plan) {
  if (!/^scratch\/[A-Za-z0-9_-]+\/[A-Za-z0-9_.-]+$/.test(out) || !['personal-cursor','personal-grok'].includes(plan)) throw Error('invalid receipt input');
  const cmd = "python3 - <<'XAI_VERIFY'\nimport json,re\nfrom pathlib import Path\np=Path("+JSON.stringify(out)+")\nr=json.loads(p.read_text())\nassert r.get('isError') is False, 'SSH failed'\nc=r['content']; assert len(c)==1 and c[0]['type']=='text', 'unexpected SSH response shape'\nm=re.fullmatch(r'exit ([-0-9]+)\\n--- stdout ---\\n(.*?)\\n\\n--- stderr ---\\n(.*)', c[0]['text'], re.S)\nassert m and int(m[1])==0, 'SSH response changed or command failed'\nd=json.loads(m[2]); assert d['returncode']==0, 'native launcher failed'\njob=json.loads(d['stdout'])\nassert job['plan']=="+JSON.stringify(plan)+" and job['status']=='completed' and job['returncode']==0, 'native job did not complete on requested plan'\np.with_suffix('.verified.json').write_text(json.dumps(job,indent=2))\nprint(json.dumps({'plan':job['plan'],'model':job['model'],'status':job['status'],'finished_at':job['finished_at']}))\nXAI_VERIFY";
  const r = await tools.exec_command({cmd,workdir:'/var/lib/agent',max_output_tokens:1000});
  if (r.exit_code !== 0) throw Error('native receipt validation failed: '+r.output);
  return JSON.parse(r.output);
}
