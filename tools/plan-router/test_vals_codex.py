#!/usr/bin/env python3
"""Deterministic Vals guard checks, 2026-11-24; no provider requests."""
import copy,importlib.util,json,subprocess,time,unittest,fcntl
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('vals_guard',Path(__file__).with_name('vals-codex.py'))
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
class GuardTests(unittest.TestCase):
 def setUp(self):
  self.account={'type':'chatgpt','email':'brando@vals.ai','planType':'pro'}
  self.rates={'ordinaryUsageAllowed':True,'rateLimitsByLimitId':{'codex':{'credits':{'hasCredits':False,'unlimited':False},'primary':{'usedPercent':2,'windowDurationMins':10080,'resetsAt':time.time()+3600},'secondary':None}}}
 def check(self):return guard.validate(self.account,self.rates,time.time())
 def test_actual_weekly_only_shape(self):self.assertEqual(self.check()['usage']['primary']['usedPercent'],2)
 def test_account_missing(self):
  self.account=None
  with self.assertRaises(ValueError):self.check()
 def test_wrong_account(self):
  self.account['email']='other@example.com'
  with self.assertRaises(ValueError):self.check()
 def test_weekly_reserve(self):
  self.rates['rateLimitsByLimitId']['codex']['primary']['usedPercent']=80
  with self.assertRaises(ValueError):self.check()
 def test_extra_credit_block(self):
  self.rates['rateLimitsByLimitId']['codex']['credits']['hasCredits']=True
  with self.assertRaises(ValueError):self.check()
 def test_expired_or_nonfinite(self):
  for field,value in [('resetsAt',0),('usedPercent',float('nan'))]:
   with self.subTest(field=field):
    r=copy.deepcopy(self.rates);r['rateLimitsByLimitId']['codex']['primary'][field]=value
    with self.assertRaises(ValueError):guard.validate(self.account,r,time.time())
 def test_missing_weekly(self):
  self.rates['rateLimitsByLimitId']['codex']['primary']['windowDurationMins']=300
  with self.assertRaises(ValueError):self.check()
 def test_real_reply_required(self):
  for text,status,accept in [('OK',0,True),('wrong',0,False),('OK',1,False)]:
   with self.subTest(text=text,status=status):
    fake=SimpleNamespace(stdout=json.dumps({'type':'item.completed','item':{'type':'agent_message','text':text}})+'\n',returncode=status)
    with patch.object(guard.subprocess,'run',return_value=fake):
     if accept:guard.health_check(['codex','--model','gpt-6-astra'],{})
     else:
      with self.assertRaises(ValueError):guard.health_check(['codex','--model','gpt-6-astra'],{})
 def test_profile_serialization(self):
  p=Path.home()/'.local/state/plan-router/vals-codex.lock';p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('a') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   r=subprocess.run(['python3',str(Path(guard.__file__)),'--check'],capture_output=True,text=True,timeout=5)
   self.assertEqual(r.returncode,1);self.assertIn('blocked',r.stderr)
if __name__=='__main__':unittest.main()
