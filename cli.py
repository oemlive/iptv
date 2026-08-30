import argparse, asyncio, json, yaml
from pathlib import Path
from app.store import Store
from app.parser import fetch,parse_text,parse_subscription_catalog
from app.classifier import classify
from app.scanner import Scanner
from app.health import load_history,update_history
from app.exporter import selected_rows,write_exports
from app.subscriptions import load_catalog,save_catalog
BASE=Path(__file__).resolve().parent
CFG=yaml.safe_load((BASE/'config/config.yaml').read_text(encoding='utf-8'))
SUB=BASE/'config/subscriptions.yaml'; SEL=BASE/'config/selection.json'; HIST=BASE/'output/health-history.json'
db=Store(BASE/'data/source_hunter.db',SEL)

def load_subs():
 d=yaml.safe_load(SUB.read_text(encoding='utf-8')) or {}; return d.get('subscriptions',[])

def selected_catalog():
 sel=db.load_selection(); urls=set(sel.get('selected_subscription_urls',[]) or [])
 cat=load_catalog(BASE).get('sources',[])
 # Empty selection means nothing is selected for stage=channels. The admin
 # deliberately creates the selection file after the discovery stage.
 if not urls: return []
 return [x for x in cat if x.get('enabled',True) and x.get('url') in urls]

async def discover():
 roots=[x for x in load_subs() if x.get('enabled',True)]
 found=[]; errors=[]
 for root in roots:
  try:
   text,ct,final=await fetch(root['url'],CFG['scanner'].get('subscription_timeout_seconds',20))
   items=parse_subscription_catalog(text,final)
   for x in items:
    x['root_name']=root.get('name',''); x['root_url']=root.get('url','')
   found.extend(items)
  except Exception as e:
   errors.append({'subscription':root.get('name',''),'error':str(e)[:300]})
 payload=save_catalog(BASE,found)
 print(json.dumps({'stage':'discover','root_subscriptions':len(roots),'discovered_subscriptions':payload['count'],'errors':errors},ensure_ascii=False))
 return payload

async def pull_selected():
 selected=selected_catalog()
 if not selected:
  print(json.dumps({'stage':'channels','selected_subscriptions':0,'parsed':0,'message':'请先在管理端选择订阅地址'},ensure_ascii=False)); return 0
 rules=(yaml.safe_load((BASE/'config/rules.yaml').read_text(encoding='utf-8')) or {}).get('rules',[])
 total=0
 for s in selected:
  db.add_sub(s['name'],s['url'],True)
  row=next(x for x in db.subs() if x['url']==s['url'])
  try:
   text,ct,final=await fetch(s['url'],CFG['scanner'].get('subscription_timeout_seconds',20),s.get('headers') or {})
   items=parse_text(text,final,ct); db.clear_subscription_sources(row['id']); total+=db.import_sources(items,row['id']); db.touch_fetch(row['id'])
   for src in db.sources([row['id']]): db.set_categories({src['url']:classify(src['name'],src.get('group_name',''),src['url'],rules)})
  except Exception as e:
   db.touch_fetch(row['id'],str(e)[:300]); print('PULL ERROR',s['name'],e)
 print(json.dumps({'stage':'channels','selected_subscriptions':len(selected),'parsed':total},ensure_ascii=False))
 return total

async def scan_selected():
 sel=selected_catalog(); ids=[x['id'] for x in db.subs() if x['url'] in {s['url'] for s in sel}]
 sources=db.sources(ids)
 if not sources:
  print(json.dumps({'stage':'scan','scanned':0,'alive':0,'dead':0},ensure_ascii=False)); return
 hist=load_history(HIST); rs=await Scanner(db,CFG['scanner'],hist).scan(sources); update_history(HIST,rs,CFG['health']['keep_runs'])
 print(json.dumps({'stage':'scan','scanned':len(rs),'alive':sum(x['status']=='alive' for x in rs),'dead':sum(x['status']!='alive' for x in rs)},ensure_ascii=False))

def export_candidates():
    sel=db.load_selection(); cat=load_catalog(BASE).get('sources',[])
    urls={x.get('url') for x in cat if x.get('url') in set(sel.get('selected_subscription_urls',[]) or [])}
    ids=[x['id'] for x in db.subs() if x['url'] in urls]
    rows=db.sources(ids)
    meta={'version':'11.1.0','selected_channels':len(rows),'selected_subscriptions':len(urls),'total_channels':len(rows),'candidate_mode':True}
    return write_exports(rows,BASE/'output',meta,'candidates',('m3u','txt'),'channels')

def export_selected():
 sel=db.load_selection(); cat=load_catalog(BASE).get('sources',[]); urls={x.get('url') for x in cat if x.get('url') in set(sel.get('selected_subscription_urls',[]) or [])}
 ids=[x['id'] for x in db.subs() if x['url'] in urls]
 rows=selected_rows(db.sources(ids),sel)
 return write_exports(rows,BASE/'output',{'version':'11.1.0','selected_channels':len(rows),'selected_subscriptions':len(urls),'total_channels':len(db.sources(ids))},'all',('m3u','txt'),'channels')

async def main(a):
 stage=a.stage
 if stage in ('discover','auto') and (stage=='discover' or not (db.load_selection().get('selected_subscription_urls') or [])):
  await discover(); return
 if stage in ('channels','auto'):
  await pull_selected()
  export_selected()
 if stage=='scan':
  await scan_selected(); export_selected()
 if stage=='export':
  export_selected()

if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--stage',choices=['auto','discover','channels','scan','export'],default='auto'); p.add_argument('--pull',action='store_true'); p.add_argument('--scan',action='store_true'); p.add_argument('--export',action='store_true'); a=p.parse_args()
 # Backward compatibility: old --pull --scan --export invocation now follows the two-stage workflow.
 # Legacy --pull/--scan/--export flags are accepted, but the new default
 # workflow is two-stage and does not scan/淘汰 sources unless stage=scan is explicit.
 asyncio.run(main(a))
