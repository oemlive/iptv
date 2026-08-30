import json
from pathlib import Path
from datetime import datetime, timezone

def load_history(path):
    p=Path(path)
    if not p.exists(): return {'version':2,'runs':[],'sources':{}}
    try:
        d=json.loads(p.read_text(encoding='utf-8'))
        if isinstance(d,list): d={'version':2,'runs':d,'sources':{}}
        d.setdefault('version',2); d.setdefault('runs',[]); d.setdefault('sources',{})
        return d
    except Exception: return {'version':2,'runs':[],'sources':{}}

def _window(history_list, days):
    return history_list[-days:] if days else history_list

def reliability(history,url,days=None):
    h=(history.get('sources') or {}).get(url,{})
    hist=h.get('history') or []
    if days: hist=_window(hist,days)
    if not hist: return None
    return round(100*sum(x.get('status')=='alive' for x in hist)/len(hist),1)

def lifecycle(h):
    failures=int(h.get('consecutive_failures',0)); status=h.get('last_status')
    if status=='alive': return 'recovered' if h.get('ever_failed') else 'alive'
    if failures>=5: return 'suspended'
    if failures>=2: return 'failed'
    return 'degraded'

def update_history(path, results, keep_runs=90):
    p=Path(path); d=load_history(p); ts=datetime.now(timezone.utc).isoformat()
    alive=sum(x.get('status')=='alive' for x in results)
    run={'timestamp':ts,'scanned':len(results),'alive':alive,'dead':len(results)-alive,
         'timeouts':sum(x.get('status')=='timeout' for x in results)}
    d['runs']=(d.get('runs') or [])[-(keep_runs-1):]+[run]
    sources=d.setdefault('sources',{})
    for r in results:
        key=r.get('url') or str(r.get('source_id'))
        h=sources.setdefault(key,{'runs':0,'alive':0,'failures':0,'consecutive_failures':0,'ever_failed':False,'last_status':None,'last_seen':None,'history':[]})
        ok=r.get('status')=='alive'; h['runs']+=1; h['alive']+=int(ok); h['failures']+=int(not ok)
        h['consecutive_failures']=0 if ok else int(h.get('consecutive_failures',0))+1
        h['ever_failed']=bool(h.get('ever_failed')) or not ok; h['last_status']=r.get('status'); h['last_seen']=ts
        h['history']=(h.get('history') or [])[-(keep_runs-1):]+[{'timestamp':ts,'status':r.get('status'),'score':r.get('score',0),'latency_ms':r.get('latency_ms'),'first_frame_ms':r.get('first_frame_ms')}]
        h['stability_7d']=reliability(d,key,7); h['stability_30d']=reliability(d,key,30); h['stability_90d']=reliability(d,key,90); h['lifecycle']=lifecycle(h)
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8'); return d
