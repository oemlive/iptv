from pathlib import Path
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
import httpx
from app.parser import parse_text
from fastapi.staticfiles import StaticFiles

BASE=Path(__file__).resolve().parent
ADMIN=BASE/'index.html'
CATALOG=BASE/'data'/'hw.json'
STATE=BASE/'data'/'state.json'
app=FastAPI(title='WEB后台管理',version='1.0.0')
app.mount('/data', StaticFiles(directory=BASE/'data'), name='data')

class State(BaseModel):
    subscriptions:list[dict]=Field(default_factory=list)
    selected_urls:list[str]=Field(default_factory=list)
    channels:list[dict]=Field(default_factory=list)

@app.get('/')
def index(): return FileResponse(ADMIN)
@app.get('/config.js')
def config(): return FileResponse(BASE/'config.js',media_type='application/javascript')
@app.get('/api/catalog')
def catalog(): return json.loads(CATALOG.read_text(encoding='utf-8'))
@app.get('/api/state')
def get_state():
    if not STATE.exists(): return {'subscriptions':[],'selected_urls':[],'channels':[]}
    try:return json.loads(STATE.read_text(encoding='utf-8'))
    except:return {'subscriptions':[],'selected_urls':[],'channels':[]}
@app.post('/api/state')
def save_state(state:State):
    STATE.write_text(json.dumps(state.model_dump(),ensure_ascii=False,indent=2),encoding='utf-8'); return {'ok':True}

@app.post('/api/pull')
async def pull(payload:dict):
    urls=payload.get('urls') or []
    if not urls: raise HTTPException(400,'没有选择订阅源')
    by_url={x.get('url'):x for x in json.loads(CATALOG.read_text(encoding='utf-8')).get('lives',[]) if x.get('url')}
    channels=[]; errors=[]
    async with httpx.AsyncClient(follow_redirects=True,timeout=20,headers={'User-Agent':'WEB-Admin/1.0','Accept':'*/*'}) as client:
        for url in urls:
            item=by_url.get(url,{})
            try:
                headers={}
                if item.get('ua'): headers['User-Agent']=item['ua']
                r=await client.get(url,headers=headers); r.raise_for_status()
                rows=parse_text(r.text,str(r.url),r.headers.get('content-type',''))
                for x in rows:
                    channels.append({'name':x.name,'url':x.url,'group':x.group,'logo':x.logo,'tvg_id':x.tvg_id,'source':item.get('name') or url})
            except Exception as e:
                errors.append({'name':item.get('name') or url,'url':url,'error':str(e)[:300]})
    return {'ok':True,'channels':channels,'errors':errors}

@app.post('/api/export',response_class=PlainTextResponse)
def export(payload:dict):
    rows=payload.get('channels') or []
    lines=['#EXTM3U']
    for r in rows:
        group=r.get('group') or '其他'; name=r.get('name') or 'UNKNOWN'; url=r.get('url') or ''
        lines.append(f'#EXTINF:-1 group-title="{group}",{name}'); lines.append(url)
    return '\n'.join(lines)+'\n'
