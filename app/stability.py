import asyncio, shutil, subprocess
from .config import settings

async def stability_probe(url: str, seconds: int = 0):
    if seconds <= 0: return {"enabled":False,"ok":None,"errors":0}
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg: return {"enabled":True,"ok":False,"errors":1,"message":"ffmpeg未安装"}
    cmd=[ffmpeg,"-hide_banner","-loglevel","error","-rw_timeout",str(int(settings.validate_timeout*1_000_000)),"-i",url,"-t",str(seconds),"-f","null","-"]
    try:
        p=await asyncio.to_thread(subprocess.run,cmd,capture_output=True,text=True,timeout=settings.validate_timeout+seconds+2)
        errors=len((p.stderr or "").splitlines())
        return {"enabled":True,"ok":p.returncode==0 and errors==0,"errors":errors}
    except Exception as e: return {"enabled":True,"ok":False,"errors":1,"message":str(e)}
