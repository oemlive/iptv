import asyncio, json, os, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from app.config import settings
from app.providers import search_public
from app.parser import dedupe, parse_text
from app.validator import validate_many
from app.db import upsert, record_check
from app.exporter import write_all

DEFAULT_QUERIES=["iptv m3u","直播源 m3u","tv.m3u","live.m3u","playlist m3u","电视直播"]

def load_manual():
    items=[]; p=Path("config/subscriptions")
    if not p.exists(): return items
    for f in p.iterdir():
        if f.suffix.lower() in {".txt",".m3u",".m3u8",".json"}:
            try: items.extend(parse_text(f.read_text(encoding="utf-8-sig",errors="ignore"),f"manual:{f.name}"))
            except Exception as e: print(f"manual error {f}: {e}")
    return items

def load_settings():
    try: return json.loads(Path(settings.settings_file).read_text(encoding='utf-8'))
    except Exception: return {}

def scheduled_due(cfg):
    sch=cfg.get('schedule',{})
    if not sch.get('enabled',True): return False
    try: now=datetime.now(ZoneInfo(str(sch.get('timezone','UTC'))))
    except Exception: now=datetime.now(timezone.utc)
    weekdays=sch.get('weekdays',list(range(7)))
    times={str(x)[:5] for x in sch.get('times',['02:17'])}
    return now.weekday() in weekdays and now.strftime('%H:%M') in times

def write_status(state, **extra):
    p=Path(settings.data_dir); p.mkdir(parents=True,exist_ok=True)
    payload={'state':state,'updated_at':datetime.now(timezone.utc).isoformat(),**extra}
    (p/'status.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

async def main():
    manual=os.getenv('MANUAL_RUN','0')=='1' or os.getenv('GITHUB_EVENT_NAME')=='workflow_dispatch'
    cfg=load_settings()
    if not manual and not scheduled_due(cfg):
        write_status('idle', reason='not_due')
        print('Scheduled tick: not due.')
        return 0
    write_status('running', stage='discovery')
    providers=[]
    src=cfg.get('sources',{})
    if src.get('github',True): providers.append('github')
    if src.get('gitee',True): providers.append('gitee')
    items=load_manual() if src.get('manual',True) else []
    try: items.extend(await search_public(DEFAULT_QUERIES,providers))
    except Exception as e: print('search error:',e)
    items=dedupe(items); print('discovered:',len(items)); upsert(items)
    write_status('running',stage='validation',discovered=len(items))
    done=await validate_many(items)
    upsert(done)
    for x in done: record_check(x)
    valid=sum(x.valid is True for x in done)
    write_status('running',stage='export',discovered=len(items),validated=len(done),valid=valid)
    files=write_all(done)
    summary={'discovered':len(items),'validated':len(done),'valid':valid,'invalid':len(done)-valid,'generated_files':files,'completed_at':datetime.now(timezone.utc).isoformat()}
    Path(settings.data_dir).mkdir(parents=True,exist_ok=True)
    (Path(settings.data_dir)/'run-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write_status('success',stage='done',**summary)
    print('generated:',len(files),files)
    return 0

if __name__=='__main__':
    try: raise SystemExit(asyncio.run(main()))
    except Exception as e:
        write_status('failed',error=str(e))
        traceback.print_exc(); raise
