from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from .models import ValidateRequest, SearchRequest, ExportRequest
from .parser import parse_text, dedupe
from .providers import search_public
from .validator import validate_many
from .db import all_sources, upsert, record_check
from .exporter import write_all
import asyncio

app=FastAPI(title="IPTV Advanced Source Manager")

@app.get("/")
def root(): return FileResponse("web/index.html")

@app.get("/api/health")
def health(): return {"ok":True,"sources":len(all_sources())}

@app.get("/api/sources")
def sources(): return all_sources()

@app.post("/api/import")
async def import_files(files:list[UploadFile]=File(...)):
    items=[]
    for f in files:
        raw=await f.read(); text=raw.decode("utf-8-sig","ignore")
        items.extend(parse_text(text,f.name))
    items=dedupe(items); upsert(items); return {"count":len(items)}

@app.post("/api/import-url")
async def import_url(payload:dict):
    import httpx
    url=str(payload.get("url","")).strip()
    if not url.startswith(("http://","https://")): raise HTTPException(400,"URL无效")
    async with httpx.AsyncClient(timeout=15,follow_redirects=True) as c:
        r=await c.get(url); r.raise_for_status(); items=parse_text(r.text,url)
    upsert(items); return {"count":len(items)}

@app.post("/api/search")
async def search(req:SearchRequest):
    items=await search_public(req.queries,req.providers); upsert(items); return {"count":len(items)}

@app.post("/api/validate")
async def validate(req:ValidateRequest):
    db={x.id:x for x in all_sources()}; items=[db[i] for i in req.ids if i in db]
    done=await validate_many(items); upsert(done)
    for x in done: record_check(x)
    return done

@app.post("/api/export")
def export(req:ExportRequest):
    db={x.id:x for x in all_sources()}; items=[db[i] for i in req.ids if i in db]
    if not any(x.valid for x in items): raise HTTPException(400,"没有有效源，请先验证")
    files=write_all(items); return {"count":sum(x.valid is True for x in items),"files":files}
