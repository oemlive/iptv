from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse,PlainTextResponse
from pathlib import Path
import yaml,json
from app.store import Store
from app.parser import fetch,parse_text
from app.classifier import classify
from app.scanner import Scanner
from app.exporter import selected_rows,write_exports
from app.configstore import load_subscriptions,save_subscriptions
from app.health import load_history,update_history

BASE=Path(__file__).resolve().parent.parent
CFG=yaml.safe_load((BASE/'config/config.yaml').read_text(encoding='utf-8'))
SUBCFG=BASE/'config/subscriptions.yaml'; HISTORY=BASE/'output/health-history.json'
STORE=Store(BASE/'data/source_hunter.db',BASE/'config/selection.json')
app=FastAPI(title='Source Hunter PRO',version='11.1.0')

def sync_subscriptions():
    configured=load_subscriptions(SUBCFG)
    for x in configured: STORE.add_sub(x['name'],x['url'],x.get('enabled',True))
    return STORE.subs()

def selected_subs():
    sync_subscriptions(); sel=STORE.load_selection(); urls=set(sel.get('selected_subscription_urls',[])); ids=set(sel.get('selected_subscriptions',[])); return [s for s in STORE.subs() if s['enabled'] and (not urls and not ids or s['url'] in urls or s['id'] in ids)]

@app.get('/',response_class=HTMLResponse)
def home(): return (BASE/'web/index.html').read_text(encoding='utf-8')
@app.get('/api/health')
def health(): return {'ok':True,'version':'11.1.0','mode':'github-actions-first'}
@app.get('/api/stats')
def stats(): return STORE.stats()
@app.get('/api/subscriptions')
def subscriptions(): return STORE.subs()
@app.post('/api/subscriptions')
def add_subscription(p:dict):
    name=(p.get('name') or '').strip(); url=(p.get('url') or '').strip()
    if not name or not url: raise HTTPException(400,'name/url required')
    items=[x for x in load_subscriptions(SUBCFG) if x.get('url')!=url]; items.append({'name':name,'url':url,'enabled':bool(p.get('enabled',True))}); save_subscriptions(SUBCFG,items); sync_subscriptions(); return {'ok':True}
@app.delete('/api/subscriptions/{sub_id}')
def delete_subscription(sub_id:int):
    s=next((x for x in STORE.subs() if x['id']==sub_id),None)
    if not s: raise HTTPException(404,'subscription not found')
    save_subscriptions(SUBCFG,[x for x in load_subscriptions(SUBCFG) if x.get('url')!=s['url']]); STORE.remove_sub(sub_id); return {'ok':True}
@app.post('/api/subscriptions/select')
def select_subscriptions(p:dict):
    sync_subscriptions(); ids=[int(x) for x in p.get('ids',[])]; subs=STORE.subs(); urls=[s['url'] for s in subs if s['id'] in ids]; sel=STORE.load_selection(); sel['selected_subscriptions']=ids; sel['selected_subscription_urls']=urls; return STORE.save_selection(sel)
@app.get('/api/selection')
def get_selection(): return STORE.load_selection()
@app.post('/api/selection')
def save_selection(p:dict):
    sync_subscriptions(); ids=[int(x) for x in p.get('selected_subscriptions',[])]; urls=p.get('selected_subscription_urls'); urls=urls if urls is not None else [s['url'] for s in STORE.subs() if s['id'] in ids]
    return STORE.save_selection({'selected_subscriptions':ids,'selected_subscription_urls':urls,'selected_channels':{str(k):bool(v) for k,v in p.get('selected_channels',{}).items()},'excluded_channels':{str(k):bool(v) for k,v in p.get('excluded_channels',{}).items()},'default_selected':bool(p.get('default_selected',True))})

@app.post('/api/pull')
async def pull():
    subs=selected_subs()
    if not subs: raise HTTPException(400,'请先勾选订阅源')
    total=0; errors=[]
    rules=yaml.safe_load((BASE/'config/rules.yaml').read_text(encoding='utf-8')) if (BASE/'config/rules.yaml').exists() else {}
    for s in subs:
        try:
            text,ct,final=await fetch(s['url'],float(CFG['scanner'].get('subscription_timeout_seconds',15)))
            items=parse_text(text,final,ct); STORE.clear_subscription_sources(s['id']); total+=STORE.import_sources(items,s['id']); STORE.touch_fetch(s['id'])
            for row in STORE.sources([s['id']]):
                cat=classify(row['name'],row.get('group_name',''),row['url'],rules.get('rules')); STORE.set_categories({row['url']:cat})
        except Exception as e: STORE.touch_fetch(s['id'],str(e)[:300]); errors.append({'subscription':s['name'],'error':str(e)[:300]})
    return {'ok':True,'parsed':total,'subscriptions':len(subs),'errors':errors}

@app.get('/api/channels')
def channels():
    subs=selected_subs(); ids=[s['id'] for s in subs]; sel=STORE.load_selection(); rows=STORE.sources(ids); latest={r['url']:r for r in STORE.latest_all(ids)}; chosen=sel.get('selected_channels',{}); excluded=sel.get('excluded_channels',{}); out=[]
    hist=load_history(HISTORY)
    for s in rows:
        r={**s,**latest.get(s['url'],{})}; key=s.get('channel_key') or r['url']; r['category']=s.get('category') or classify(s['name'],s.get('group_name',''),s['url']); r['selected']=False if (excluded.get(key) or excluded.get(r['url'])) else chosen.get(key,chosen.get(r['url'],sel.get('default_selected',True))); h=hist.get('sources',{}).get(r['url'],{}); r['lifecycle']=h.get('lifecycle',r.get('lifecycle','new')); out.append(r)
    return {'channels':out,'selection':sel}

@app.post('/api/scan')
async def scan():
    subs=selected_subs(); ids=[s['id'] for s in subs]; sources=STORE.sources(ids)
    if not sources: raise HTTPException(400,'没有可扫描节目，请先拉取选中的订阅')
    hist=load_history(HISTORY); rs=await Scanner(STORE,CFG['scanner'],hist).scan(sources); hist=update_history(HISTORY,rs,int(CFG.get('health',{}).get('keep_runs',90))); return {'total':len(rs),'alive':sum(r['status']=='alive' for r in rs),'dead':sum(r['status']!='alive' for r in rs),'results':rs,'history':hist.get('runs',[])[-1]}

@app.post('/api/export')
def export():
    ids=[s['id'] for s in selected_subs()]; sel=STORE.load_selection(); rows=selected_rows(STORE.latest(ids),sel); return write_exports(rows,BASE/CFG.get('github',{}).get('output_dir','output'),{'version':'11.1.0','selected_channels':len(rows)},CFG.get('export',{}).get('mode','all'))
@app.get('/api/export/m3u',response_class=PlainTextResponse)
def m3u():
    p=BASE/CFG.get('github',{}).get('output_dir','output')/'channels.m3u'; return p.read_text(encoding='utf-8') if p.exists() else '#EXTM3U\n'
if __name__=='__main__':
 import uvicorn; uvicorn.run(app,host=CFG['server']['host'],port=CFG['server']['port'])
