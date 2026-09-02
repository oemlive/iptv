import asyncio,json,shutil,subprocess,time
from datetime import datetime,timezone
from .config import settings
from .stability import stability_probe

def probe(url):
    ffprobe=shutil.which('ffprobe')
    if not ffprobe:return None,'ffprobe未安装',None
    cmd=[ffprobe,'-v','error','-rw_timeout',str(int(settings.validate_timeout*1_000_000)),'-show_entries','format=duration:stream=index,codec_type,codec_name,width,height,bit_rate','-of','json',url]
    t=time.perf_counter()
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=settings.validate_timeout+1.5);ms=int((time.perf_counter()-t)*1000)
        if p.returncode!=0:return None,(p.stderr or 'ffprobe失败').strip()[-600:],ms
        try:return json.loads(p.stdout or '{}'),None,ms
        except json.JSONDecodeError:return None,'ffprobe返回非JSON',ms
    except subprocess.TimeoutExpired:return None,f'超过{settings.validate_timeout:g}s',int((time.perf_counter()-t)*1000)
    except Exception as e:return None,str(e),int((time.perf_counter()-t)*1000)

def calc_score(x):
    if not x.valid:return 0
    score=35
    if x.width and x.height:score+=25 if x.width>=3840 and x.height>=2160 else 22 if x.width>=1920 and x.height>=1080 else 17 if x.width>=1280 and x.height>=720 else 0
    if x.audio_codec:score+=12
    if x.video_codec:score+=8
    if x.latency_ms is not None:score+=10 if x.latency_ms<300 else 7 if x.latency_ms<800 else 3 if x.latency_ms<1500 else 0
    if x.first_frame_ms is not None:score+=10 if x.first_frame_ms<1500 else 6 if x.first_frame_ms<3000 else 2
    if x.stability is not None:score+=10 if x.stability>=90 else 5 if x.stability>=70 else 0
    return min(100,score)

async def validate_one(x):
    data=err=lat=None
    for attempt in range(settings.retry_count+1):
        data,err,lat=await asyncio.to_thread(probe,x.url);x.latency_ms=lat
        if data is not None:break
        if attempt<settings.retry_count:await asyncio.sleep(min(2**attempt,4))
    x.checked_at=datetime.now(timezone.utc).isoformat()
    if data is None:x.valid=False;x.status='失败';x.last_error=err;x.score=0;return x
    streams=data.get('streams',[]);vids=[s for s in streams if s.get('codec_type')=='video'];auds=[s for s in streams if s.get('codec_type')=='audio']
    if not vids:x.valid=False;x.status='无视频';x.last_error='未检测到视频流';x.score=0;return x
    v=max(vids,key=lambda s:(s.get('width') or 0)*(s.get('height') or 0));x.width=v.get('width');x.height=v.get('height');x.video_codec=v.get('codec_name');x.bitrate=v.get('bit_rate');x.audio_codec=auds[0].get('codec_name') if auds else None
    if not x.width or not x.height:x.valid=False;x.status='分辨率未知';x.last_error='无法确认分辨率';x.score=0;return x
    if x.width<settings.min_width or x.height<settings.min_height:x.valid=False;x.status='低于最低分辨率';x.last_error=f'{x.width}x{x.height}';x.score=0;return x
    x.valid=True;x.status='有效';x.last_error=None
    if settings.stability_seconds>0:
        st=await stability_probe(x.url,settings.stability_seconds);x.stability=100 if st.get('ok') else 0
        if not st.get('ok'):x.valid=False;x.status='稳定性失败';x.last_error=st.get('message') or '连续流检测失败'
    x.score=calc_score(x);return x

async def validate_many(items):
    sem=asyncio.Semaphore(settings.max_concurrency)
    async def run(x):
        async with sem:return await validate_one(x)
    return await asyncio.gather(*(run(x) for x in items))
