from pathlib import Path
import subprocess, tempfile, shutil
from .config import settings


def render_txt(items):
    return "\n".join(f"{x.name},{x.url}" for x in items)+"\n"


def render_m3u(items):
    lines=["#EXTM3U"]
    for x in items:
        lines.append(f'#EXTINF:-1 group-title="{x.group}",{x.name}')
        lines.append(x.url)
    return "\n".join(lines)+"\n"


def export_local(items, formats):
    out=Path(settings.output_dir); out.mkdir(parents=True,exist_ok=True)
    paths=[]
    if "txt" in formats:
        p=out/"live.txt"; p.write_text(render_txt(items),encoding="utf-8"); paths.append(str(p))
    if "m3u" in formats:
        p=out/"live.m3u"; p.write_text(render_m3u(items),encoding="utf-8"); paths.append(str(p))
    return paths


def push_repo(items, formats):
    # This legacy helper intentionally delegates to local output unless an explicit
    # repository URL is provided through the environment. No config attribute is assumed.
    output_repo_url = __import__('os').getenv('OUTPUT_REPO_URL','').strip()
    output_branch = __import__('os').getenv('OUTPUT_BRANCH','main').strip() or 'main'
    if not output_repo_url:
        return {"pushed":False,"message":"未配置 OUTPUT_REPO_URL，已仅生成本地文件","paths":export_local(items,formats)}
    tmp=Path(tempfile.mkdtemp(prefix='live-output-'))
    try:
        subprocess.run(["git","clone","--depth","1","--branch",output_branch,output_repo_url,str(tmp)],check=True,capture_output=True,text=True,timeout=60)
        if "txt" in formats: (tmp/"live.txt").write_text(render_txt(items),encoding="utf-8")
        if "m3u" in formats: (tmp/"live.m3u").write_text(render_m3u(items),encoding="utf-8")
        subprocess.run(["git","-C",str(tmp),"config","user.name","live-source-bot"],check=True)
        subprocess.run(["git","-C",str(tmp),"config","user.email","live-source-bot@localhost"],check=True)
        subprocess.run(["git","-C",str(tmp),"add","live.txt","live.m3u"],check=False)
        p=subprocess.run(["git","-C",str(tmp),"commit","-m","auto: update validated live sources"],capture_output=True,text=True)
        if p.returncode==0:
            subprocess.run(["git","-C",str(tmp),"push","origin",output_branch],check=True,capture_output=True,text=True,timeout=60)
            return {"pushed":True,"message":"已推送到仓库"}
        return {"pushed":False,"message":"内容未变化，无需提交"}
    except Exception as e:
        return {"pushed":False,"message":str(e)}
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
