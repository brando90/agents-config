from pathlib import Path
import re,json,hashlib,subprocess
# One-time migration receipt: compare this change with its recorded Git baseline.
root=Path(__file__).resolve().parents[2]
d=json.loads((root/'docs/instruction-audit/rule-migration.json').read_text())
source=subprocess.check_output(['git','show',d['source_commit']+':INDEX_RULES.md'],cwd=root,text=True)
markers={'hard':('## Hard Rules (every response, never skip)\n','\n## Trigger Rules'),'trigger':('## Trigger Rules (mandatory when triggered)\n','\n## Abbreviations'),'guideline':('## Guidelines (best practices)\n','\n## SNAP watcher')}
blocks={}
for kind,(start,end) in markers.items():
 text=source.split(start,1)[1].split(end,1)[0]
 starts=list(re.finditer(r'(?m)^(\d+)\. \*\*',text))
 for i,m in enumerate(starts):
  b=text[m.start():starts[i+1].start() if i+1<len(starts) else len(text)].strip();b=re.sub(r'\n+---\s*$','',b).rstrip();blocks[f'{kind}-{m[1]}']=b
for rule in d['rules']:
 text=blocks[rule['id']]
 assert hashlib.sha256(text.encode()).hexdigest()==rule['source_sha256'],rule['id']
 for e in d['clarifications']:
  if e['rule']==rule['id']:
   assert text.count(e['old'])==1
   text=text.replace(e['old'],e['new'])
 def rebase(m):
  return m[0] if re.match(r'^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|/|~|#)',m[1]) else ']('+ '../'+m[1]+')'
 text=re.sub(r'\]\(([^\s)]+)\)',rebase,text)
 destination=(root/rule['path']).read_text()
 kind,number=rule['id'].split('-')
 section=destination.split(f'## {kind.title()} Rule {number}\n',1)[1].split('\n## ',1)[0]
 assert text.strip()==section.strip(),rule['id']
print(f'PASS: {len(d["rules"])} of {len(blocks)} complete rule bodies retained after link rebasing and {len(d["clarifications"])} recorded wording clarifications.')

for entry in d.get('entrypoint_preservation',[]):
 old=subprocess.check_output(['git','show',d['source_commit']+':'+entry['source_file']],cwd=root,text=True)
 paragraph=next(line for line in old.splitlines() if line.startswith(entry['prefix']))
 assert hashlib.sha256(paragraph.encode()).hexdigest()==entry['source_sha256']
 relocated=re.sub(r'\]\(([^\s)]+)\)',rebase,paragraph)
 assert relocated in (root/entry['destination']).read_text(),entry['prefix']
print(f"PASS: {len(d.get('entrypoint_preservation',[]))} unique entry-point paragraphs preserved.")
