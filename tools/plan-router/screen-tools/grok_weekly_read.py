"""Refresh the signed-in Grok dashboard and save its shared weekly allowance (2026-11-21).
Run through screen_script before a Cursor/Grok routed job; needs a task-owned Chrome
window already on https://grok.com/dashboard. Never reads cookies or credentials.
Example: grok_weekly_read.py --out scratch/AT-3269/reading.json
On any failure replaces the output with an error, so an earlier reading cannot pass.
"""
import argparse, datetime as dt, json, math, re, time
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import screenlib


def stamp(): return dt.datetime.now(dt.timezone.utc).isoformat()
def parse(text, now, exact=None):
    card=re.search(r'\bPremium\s+Renews[^\n]*\n(?:Upgrade\s+)?(\d+(?:\.\d+)?)%\s+used\s+Resets ([A-Z][a-z]{2}) (\d{1,2})\b',text)
    if not card or 'Weekly included usage' not in text or 'Welcome, Brando.' not in text:
        raise ValueError('signed-in Premium weekly card missing or changed')
    used=float(card[1])
    if exact is not None:
        exact=float(exact)
        if not math.isfinite(exact) or not 0<=exact<=100:raise ValueError('invalid accessible weekly percentage')
        used=max(used,exact)
    if not math.isfinite(used) or not 0<=used<=100:raise ValueError('invalid weekly percentage')
    local=now.astimezone(ZoneInfo('America/Los_Angeles'))
    reset=dt.datetime.strptime(f'{local.year} {card[2]} {card[3]}','%Y %b %d').replace(tzinfo=local.tzinfo)
    if reset<=local: reset=reset.replace(year=reset.year+1)
    if not dt.timedelta(0)<reset-local<=dt.timedelta(days=8):raise ValueError('weekly reset is not within eight days')
    credit=re.search(r'Additional usage\s+(?:Auto top-up\s+Buy credits\s+)?\$(\d[\d,]*\.\d{2})\s+used this month.*?Credit balance\s+\$(\d[\d,]*\.\d{2})',text,re.S)
    if not credit:raise ValueError('credit card missing or changed')
    return {'schema':'xai-weekly-v1','status':'ready','url':'https://grok.com/dashboard','observed_at':now.isoformat(),
            'expires_at':(now+dt.timedelta(minutes=10)).isoformat(),'reset_at':reset.isoformat(),
            'used_percent':used,'displayed_percent':float(card[1]),'additional_usd':float(credit[1].replace(',','')),
            'credit_balance_usd':float(credit[2].replace(',','')),'reset_note':'Date-only reset interpreted at local midnight, conservatively.'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'schema':'xai-weekly-v1','status':'error','observed_at':stamp(),'error':'refresh not completed'}))
    try:
        wins=[w for w in screenlib.list_windows()['windows'] if 'Grok Dashboard' in w['title']]
        if len(wins)!=1:raise ValueError('exactly one task-owned Grok dashboard window required')
        w=wins[0];kw={'pid':w['pid'],'window_id':w['window_id']};act=dict(kw,delivery_mode='foreground')
        # Read Chrome's address bar through its normal copy action; never read browser storage.
        screenlib.hotkey(**act,keys=['ctrl','l']);screenlib.hotkey(**act,keys=['ctrl','c'])
        url=screenlib.clipboard_read(include_text=True)['text'];u=urlparse(url if '://' in url else 'https://'+url)
        if u.scheme!='https' or u.netloc!='grok.com' or u.path.rstrip('/')!='/dashboard':raise ValueError('dashboard URL required')
        screenlib.press_key(**act,key='escape')
        # First navigate away so a previous document cannot be stamped as a new reading.
        screenlib.hotkey(**act,keys=['ctrl','l']);screenlib.type_text(**act,text='about:blank');screenlib.press_key(**act,key='enter')
        screenlib.wait(0.5)
        blank=screenlib.get_window_state(**kw,include_screenshot=False,max_elements=150,timeout_ms=3000,tree_format='elements')
        if any(e.get('label')=='Weekly included usage' for e in blank.get('elements',[])):raise ValueError('old document did not clear')
        screenlib.hotkey(**act,keys=['ctrl','l']);screenlib.type_text(**act,text='https://grok.com/dashboard');screenlib.press_key(**act,key='enter')
        started=time.monotonic()
        while time.monotonic()-started<35:
            screenlib.wait(0.7)
            s=screenlib.get_window_state(**kw,include_screenshot=False,max_elements=160,timeout_ms=3000,tree_format='elements')
            bars=[e for e in s.get('elements',[]) if e.get('label')=='Weekly included usage' and e.get('role')=='level bar']
            if len(bars)!=1:continue
            headings=[e for e in s['elements'] if e.get('label')=='Welcome, Brando.']
            if len(headings)!=1:continue
            screenlib.click(**act,element_token=headings[0]['element_token'])
            screenlib.hotkey(**act,keys=['ctrl','a']);screenlib.hotkey(**act,keys=['ctrl','c'])
            body=screenlib.clipboard_read(include_text=True)['text']
            out.with_suffix('.txt').write_text(body)
            try:result=parse(body,dt.datetime.now(dt.timezone.utc),bars[0].get('value'))
            except ValueError:continue
            # Selection affects no account state. Keep raw text and screenshot as local evidence.
            screenlib.press_key(**act,key='escape')
            shot=screenlib.get_window_state(**kw,include_accessibility_tree=False)
            result['screenshot']=shot.get('screenshot_png_file')
            out.with_suffix('.txt').write_text(body)
            out.write_text(json.dumps(result,indent=2))
            print(json.dumps(result));return
        raise ValueError('dashboard did not supply a readable weekly card within 35 seconds')
    except Exception as e:
        out.write_text(json.dumps({'schema':'xai-weekly-v1','status':'error','observed_at':stamp(),'error':str(e)}))
        raise
if __name__=='__main__':main()
