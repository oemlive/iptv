from pathlib import Path
import json
from collections import defaultdict

def selected_rows(rows,selection):
    chosen=selection.get('selected_channels',{}) or {}; excluded=selection.get('excluded_channels',{}) or {}; default=bool(selection.get('default_selected',True)); out=[]
    for r in rows:
        key=r.get('channel_key') or r.get('url')
        if excluded.get(key) or excluded.get(r.get('url')): continue
        if key in chosen and not chosen[key]: continue
        if r.get('url') in chosen and not chosen[r.get('url')]: continue
        if key not in chosen and r.get('url') not in chosen and not default: continue
        out.append(r)
    return out

def line_rank(x): return (-float(x.get('score') or 0),-float(x.get('stability_30d') or x.get('stability_pct') or 0),float(x.get('first_frame_ms') or 999999),float(x.get('latency_ms') or 999999),x.get('url',''))
def grouped(rows):
    g=defaultdict(list)
    for r in rows:g[r.get('channel_key') or r.get('url')].append(r)
    return g
def best_lines(rows): return sorted([sorted(v,key=line_rank)[0] for v in grouped(rows).values()],key=lambda x:(x.get('category','其他'),x.get('name','')))
def backup_lines(rows,n=1):
    out=[]
    for v in grouped(rows).values():
        s=sorted(v,key=line_rank)
        out.extend(s[n:n+1])
    return sorted(out,key=lambda x:(x.get('category','其他'),x.get('name','')))

def write_exports(rows,outdir,meta=None,mode='all'):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True); original=list(rows); rows=best_lines(rows) if mode=='best' else rows
    files=[]
    def write_m3u(items,path):
        m=['#EXTM3U']
        for r in items:
            attrs=[]
            if r.get('tvg_id'):attrs.append(f'tvg-id="{r["tvg_id"]}"')
            if r.get('logo'):attrs.append(f'tvg-logo="{r["logo"]}"')
            attrs.append(f'group-title="{r.get("category") or "其他"}"')
            m.append('#EXTINF:-1 '+' '.join(attrs)+','+str(r.get('name') or 'UNKNOWN'));m.append(str(r.get('url') or ''))
        path.write_text('\n'.join(m)+'\n',encoding='utf-8')
    for name,items in [('channels.m3u',rows),('best.m3u',best_lines(original)),('backup.m3u',backup_lines(original))]:write_m3u(items,out/name);files.append(name)
    (out/'channels.txt').write_text('\n'.join(f'{r.get("name","UNKNOWN")},{r.get("url","")}' for r in rows)+'\n',encoding='utf-8');files.append('channels.txt')
    payload={'meta':meta or {},'channels':rows,'best_channels':best_lines(original),'backup_channels':backup_lines(original)}
    (out/'channels.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');files.append('channels.json')
    cats={'央视':'cctv','卫视':'satellite','港台':'hk-tw','其他':'other','网页':'web'}
    for cat,safe in cats.items():
        items=[r for r in rows if r.get('category')==cat];write_m3u(items,out/f'{safe}.m3u');write_m3u(best_lines(items),out/f'{safe}-best.m3u');files += [f'{safe}.m3u',f'{safe}-best.m3u']
    (out/'health.json').write_text(json.dumps({'generated':meta or {},'channels':rows},ensure_ascii=False,indent=2),encoding='utf-8');files.append('health.json')
    (out/'run-summary.json').write_text(json.dumps({'generated':meta or {},'count':len(rows),'best_count':len(best_lines(original)),'backup_count':len(backup_lines(original))},ensure_ascii=False,indent=2),encoding='utf-8');files.append('run-summary.json')
    return {'count':len(rows),'files':files,'mode':mode}
