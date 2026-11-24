"""Import a fresh browser usage read and run one bounded Cursor/Grok job (2026-11-21).
Prefer notes/tools/xai_auto_launch.js in functions.exec for automatic freshness and capture.
This lower-level helper runs through tool_script immediately after grok_weekly_read.py through screen_script.
Needs a task-owned signed-in dashboard for that first step, SSH access to skampere1,
and the installed plan router. No browser login, credential or billing changes.
Example: xai_plan_launch.py --reading scratch/AT-3269/auto-reading.json --plan personal-cursor --prompt scratch/AT-3269/prompt.md --out scratch/AT-3269/cursor-result.json
--round-robin selects only that native entry through plan-rr, for checking its guard.
"""
import argparse, datetime as dt, json, shlex, uuid
from pathlib import Path
import toollib

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reading',required=True);ap.add_argument('--plan',choices=['personal-cursor','personal-grok'],required=True)
    ap.add_argument('--prompt',required=True);ap.add_argument('--out',required=True);ap.add_argument('--round-robin',action='store_true');a=ap.parse_args()
    reading=Path(a.reading).read_text();data=json.loads(reading);prompt=Path(a.prompt).read_text()
    if len(prompt)>20000:raise ValueError('bounded job prompt exceeds 20,000 characters')
    # Always replace the remote input, including producer errors; never reuse an old success.
    tag=uuid.uuid4().hex;remote='~/.cache/plan-router/screen-jobs/'+tag
    command="python3 - <<'XAI_LAUNCH_PY'\nimport json,os,pathlib,subprocess,sys\nh=pathlib.Path.home()\np=h/'.local/state/plan-router/xai-weekly-reading.json'\np.parent.mkdir(parents=True,exist_ok=True)\ntmp=p.with_name('xai-weekly-reading.'+"+repr(tag)+"+'.tmp')\ntmp.write_text("+repr(reading)+")\ntmp.chmod(0o600)\nos.replace(tmp,p)\nw=h/'.cache/plan-router/screen-jobs'/"+repr(tag)+"\nw.mkdir(parents=True,mode=0o700)\nf=w/'prompt.md'\nf.write_text("+repr(prompt)+")\n"
    if a.round_robin:
        # Every non-target route is excluded: this test cannot silently consume another plan.
        skip=['vals-codex','sundial','personal-agy','personal-codex','personal-claude','pi:koyejolab-openai-bm','pi:vals-openai-bm','pi:allen-google-veribench','stanford-codex','stanford-claude','vals-claude-opus','pi:stanford-stair-bm', 'native:grok' if a.plan=='personal-cursor' else 'native:cursor']
        command+="cmd=[sys.executable,str(h/'.local/bin/plan-rr'),'--prompt-file',str(f),'--workspace',str(w),'--skip',"+repr(','.join(skip))+"]\n"
    else:
        command+="cmd=[sys.executable,str(h/'.local/lib/plan-router/router.py'),'--config',str(h/'.config/plan-router/config.json'),'run','--plan',"+repr(a.plan)+",'--prompt-file',str(f),'--workspace',str(w)]\n"
    command+="env=dict(os.environ,PATH='/dfs/scratch0/brando9/bin:'+str(h/'.local/bin')+':'+os.environ.get('PATH',''))\nr=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=210)\nprint(json.dumps({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'reading':json.loads(p.read_text())}))\nsys.exit(r.returncode)\nXAI_LAUNCH_PY"
    result=toollib.call('mcp__ssh__ssh_run',{'host':'skampere1.stanford.edu','command':command,'timeout':230},whole=True)
    Path(a.out).write_text(json.dumps(result,indent=2) if not isinstance(result,str) else result)
    print(result)
if __name__=='__main__':main()
