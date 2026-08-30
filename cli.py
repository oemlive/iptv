import argparse, asyncio, json, yaml
from pathlib import Path
from app.store import Store
from app.parser import fetch,parse_text
from app.classifier import classify
from app.scanner import Scanner
from app.health import load_history,update_history
from app.exporter import selected_rows,write_exports
BASE=Path(__file__).resolve().parent; CFG=yaml.safe_load((BASE/'config/config.yaml').read_text(encoding='utf-8'))
SUB=BASE/'config/subscriptions.yaml'; SEL=BASE/'config/selection.json'; HIST=BASE/'output/health-history.json'; db=Store(BASE/'data/source_hunter.db',SEL)

def load_subs():
 d=yaml.safe_load(SUB.read_text(encoding='utf-8')) or {}; return d.get('subscriptions',[])
async def main(a):
 subs=load_subs(); sel=db.load_selection(); selected_urls=set(sel.get('selected_subscription_urls',[])); active=[x for x in subs if x.get('enabled',True) and (not selected_urls or x.get('url') in selected_urls)]; total=0
 if a.pull:
  for i,s in enumerate(active,1):
   try:
    text,ct,final=await fetch(s['url'],CFG['scanner'].get('subscription_timeout_seconds',20)); items=parse_text(text,final,ct)
    db.add_sub(s['name'],s['url'],True); row=next(x for x in db.subs() if x['url']==s['url']); db.clear_subscription_sources(row['id']); total+=db.import_sources(items,row['id'])
    rules=(yaml.safe_load((BASE/'config/rules.yaml').read_text(encoding='utf-8')) or {}).get('rules',[])
    for src in db.sources([row['id']]): db.set_categories({src['url']:classify(src['name'],src.get('group_name',''),src['url'],rules)})
   except Exception as e: print('PULL ERROR',s['name'],e)
 if a.scan:
  ids=[x['id'] for x in db.subs() if x['url'] in [s['url'] for s in active]]; sources=db.sources(ids); hist=load_history(HIST); rs=await Scanner(db,CFG['scanner'],hist).scan(sources); update_history(HIST,rs,CFG['health']['keep_runs']); print(json.dumps({'scanned':len(rs),'alive':sum(x['status']=='alive' for x in rs),'dead':sum(x['status']!='alive' for x in rs)},ensure_ascii=False))
 if a.export:
  ids=[x['id'] for x in db.subs() if x['url'] in [s['url'] for s in active]]; sel=db.load_selection(); rows=selected_rows(db.latest(ids),sel); print(write_exports(rows,BASE/'output',{'version':'11.1.0','selected_channels':len(rows)}))
if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--pull',action='store_true'); p.add_argument('--scan',action='store_true'); p.add_argument('--export',action='store_true'); asyncio.run(main(p.parse_args()))
