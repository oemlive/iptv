from pathlib import Path
import json
from .config import settings
from .models import Source

def limit_per_channel(items):
    try:
        import json
        from pathlib import Path
        cfg=json.loads(Path("config/settings.json").read_text(encoding="utf-8"))
        limit=max(1,min(20,int(cfg.get("output",{}).get("max_per_channel",5))))
    except Exception:
        limit=5
    buckets={}
    for x in sorted(items,key=lambda x: (x.name.lower(), -(x.score or 0), x.latency_ms if x.latency_ms is not None else 10**9, x.url)):
        buckets.setdefault(x.name,[]).append(x)
    return [x for name in sorted(buckets) for x in buckets[name][:limit]]


def valid(items): return [x for x in items if x.valid is True]

def txt(items): return "\n".join(f"{x.name},{x.url}" for x in items)+"\n"

def m3u(items):
    lines=["#EXTM3U"]
    for x in items: lines += [f'#EXTINF:-1 group-title="{x.group}/{x.subgroup}",{x.name}',x.url]
    return "\n".join(lines)+"\n"

def write_all(items):
    out=Path(settings.output_dir); data=Path(settings.data_dir); out.mkdir(exist_ok=True); data.mkdir(exist_ok=True)
    items=limit_per_channel(valid(items))
    files={"live.txt":txt(items),"live.m3u":m3u(items)}
    groups={"cctv":lambda x:x.group=="央卫","hk_tw":lambda x:x.group=="港台","other":lambda x:x.group=="其他","movie":lambda x:x.subgroup=="影视","kids":lambda x:x.subgroup=="少儿","sports":lambda x:x.subgroup=="体育","foreign":lambda x:x.subgroup=="国外","4k":lambda x:x.subgroup=="4K"}
    for name,pred in groups.items():
        xs=[x for x in items if pred(x)]
        files[f"{name}.txt"]=txt(xs); files[f"{name}.m3u"]=m3u(xs)
    for n,c in files.items(): (out/n).write_text(c,encoding="utf-8")
    payload={"total":len(items),"sources":[x.model_dump() for x in items]}
    (data/"index.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    return list(files)
