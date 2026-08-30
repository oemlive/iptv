import asyncio, subprocess, json, time, shutil, re
from datetime import datetime, timezone
import httpx
from app.classifier import classify,protocol
from app.health import reliability, load_history

class Scanner:
    def __init__(self,store,cfg,history=None):
        self.db=store; self.cfg=cfg; self.history=history or {'sources':{}}
        self.sem=asyncio.Semaphore(int(cfg.get('concurrency',24)))
    async def scan(self,sources):
        tasks=[asyncio.create_task(self.one(s)) for s in sources]
        return await asyncio.gather(*tasks)
    async def one(self,s):
        async with self.sem:
            return await self._one(s)
    async def _one(self,s):
        started=time.perf_counter(); url=s['url']; p=protocol(url); timeout=float(self.cfg.get('timeout_seconds',6))
        h=self.history.get('sources',{}).get(url,{})
        r={'source_id':s['id'],'name':s['name'],'url':url,'category':s.get('category') or classify(s['name'],s.get('group_name',''),url),
           'status':'dead','http_status':None,'latency_ms':None,'probe_ms':None,'first_frame_ms':None,
           'protocol':p,'width':None,'height':None,'fps':None,'video_codec':None,'audio_codec':None,
           'score':0,'stability_pct':reliability(self.history,url,30),'stability_7d':reliability(self.history,url,7),
           'stability_30d':reliability(self.history,url,30),'stability_90d':reliability(self.history,url,90),
           'consecutive_failures':h.get('consecutive_failures',0),'lifecycle':h.get('lifecycle','new'),
           'error':None,'scanned_at':datetime.now(timezone.utc).isoformat()}
        try:
            if p=='web':
                async with httpx.AsyncClient(follow_redirects=True,timeout=timeout,headers={'User-Agent':self.cfg.get('user_agent','Source-Hunter-PRO')}) as c:
                    x=await c.get(url.replace('webview://','https://')); r['http_status']=x.status_code
                r['latency_ms']=round((time.perf_counter()-started)*1000,1); r['status']='alive' if x.status_code<400 else 'dead'
            elif self.cfg.get('ffprobe_enabled',True) and shutil.which('ffprobe'):
                r.update(await self.probe(url,timeout)); r['probe_ms']=round((time.perf_counter()-started)*1000,1); r['latency_ms']=r['probe_ms']
                r['status']='alive' if (r.get('video_codec') or r.get('audio_codec')) else 'dead'
            else:
                async with httpx.AsyncClient(follow_redirects=True,timeout=timeout,headers={'User-Agent':self.cfg.get('user_agent','Source-Hunter-PRO')}) as c:
                    x=await c.get(url,headers={'Range':'bytes=0-65535','Accept':'*/*'}); r['http_status']=x.status_code
                r['latency_ms']=round((time.perf_counter()-started)*1000,1); r['status']='alive' if x.status_code<400 else 'dead'
            r['score']=self.score(r) if r['status']=='alive' else 0
            if r['status']!='alive' and not r['error']: r['error']='stream probe failed'
        except (asyncio.TimeoutError, TimeoutError, subprocess.TimeoutExpired):
            r['status']='timeout'; r['error']=f'timeout > {timeout:.0f}s'
        except Exception as e: r['error']=str(e)[:300]
        if (time.perf_counter()-started)>timeout+0.5 and r['status']!='alive': r['status']='timeout'; r['error']=f'over {timeout:.0f}s limit'
        self.db.save_scan(r); return r
    async def probe(self,url,timeout):
        def run():
            args=['ffprobe','-v','error','-rw_timeout',str(int(timeout*1_000_000)),'-analyzeduration','2500000','-probesize','2500000','-show_streams','-show_format','-of','json',url]
            p=subprocess.run(args,capture_output=True,text=True,timeout=timeout+0.7)
            d=json.loads(p.stdout or '{}'); d['_rc']=p.returncode; return d
        d=await asyncio.to_thread(run); ss=d.get('streams',[])
        v=next((x for x in ss if x.get('codec_type')=='video'),{}); a=next((x for x in ss if x.get('codec_type')=='audio'),{})
        fps=None; rr=str(v.get('r_frame_rate',''))
        if '/' in rr:
            q,w=rr.split('/',1)
            try: fps=round(float(q)/float(w),2) if float(w) else None
            except Exception: pass
        first=await self.first_frame(url,timeout)
        return {'http_status':200,'width':v.get('width'),'height':v.get('height'),'fps':fps,'video_codec':v.get('codec_name'),'audio_codec':a.get('codec_name'),'first_frame_ms':first}
    async def first_frame(self,url,timeout):
        def run():
            args=['ffprobe','-v','error','-rw_timeout',str(int(timeout*1_000_000)),'-read_intervals','%+3','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','csv=p=0',url]
            t=time.perf_counter(); p=subprocess.run(args,capture_output=True,text=True,timeout=min(timeout,3)+0.5); elapsed=(time.perf_counter()-t)*1000
            vals=[]
            for line in (p.stdout or '').splitlines():
                try: vals.append(float(line.strip()))
                except: pass
            if vals and vals[0]>=0: return round(max(0,vals[0])*1000,1)
            return round(elapsed,1) if p.returncode==0 else None
        return await asyncio.to_thread(run)
    def score(self,r):
        s=20.0
        if r.get('width') and r.get('height'): s+=15
        if r.get('height') and r['height']>=720: s+=10
        if r.get('fps') and r['fps']>=24: s+=8
        lat=r.get('latency_ms')
        if lat is not None: s+=15 if lat<1000 else 8 if lat<2500 else 3
        ff=r.get('first_frame_ms')
        if ff is not None: s+=20 if ff<1500 else 14 if ff<3000 else 7 if ff<5000 else 0
        if r.get('video_codec'): s+=4
        if r.get('audio_codec'): s+=4
        stab=r.get('stability_30d')
        if stab is not None: s+=4*(stab/100)
        return round(min(100,s),1)
