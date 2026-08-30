from dataclasses import dataclass
from urllib.parse import urljoin
import json,re,xml.etree.ElementTree as ET
import httpx

@dataclass
class Item:
    name:str; url:str; group:str=''; logo:str=''; tvg_id:str=''; category:str=''; headers:dict=None

def _norm_url(base,u):
    u=str(u or '').strip().strip('"\'')
    if not u:return ''
    if u.startswith(('http://','https://','rtmp://','rtsp://','udp://','p2p://','webview://')):return u
    return urljoin(base,u)

def _item(name,url,obj=None,base=''):
    if not name or not url:return None
    o=obj or {}; headers=o.get('headers') if isinstance(o,dict) else None
    return Item(str(name).strip(),_norm_url(base,url),str(o.get('group','') or o.get('group_name','') or ''),str(o.get('logo','') or o.get('tvg-logo','') or ''),str(o.get('tvg_id','') or o.get('id','') or ''),'',headers or {})

def parse_m3u(text,base):
    out=[]; pending={}
    lines=text.replace('\ufeff','').splitlines()
    for i,line in enumerate(lines):
        line=line.strip()
        if not line:continue
        if line.upper().startswith('#EXTINF'):
            attrs={k:v for k,v in re.findall(r'([\w-]+)="([^"]*)"',line)}
            name=line.split(',',1)[1].strip() if ',' in line else attrs.get('tvg-name','UNKNOWN')
            pending={'name':name,'group':attrs.get('group-title',''),'logo':attrs.get('tvg-logo',''),'tvg_id':attrs.get('tvg-id','')}
        elif line.startswith('#KODIPROP:'):
            if pending: pending.setdefault('headers',{})
        elif not line.startswith('#'):
            if pending:
                x=_item(pending['name'],line,pending,base); pending={}
            else:
                parts=[x.strip() for x in line.split(',',1)]; x=_item(parts[0],parts[1] if len(parts)>1 else parts[0],{},base)
            if x:out.append(x)
    return out

def _walk_json(obj,base,out,default_name=''):
    if isinstance(obj,list):
        for x in obj:_walk_json(x,base,out,default_name)
        return
    if not isinstance(obj,dict):return
    # Common direct object forms.
    name=obj.get('name') or obj.get('title') or obj.get('channel_name') or obj.get('channelName') or default_name
    url=obj.get('url') or obj.get('stream_url') or obj.get('streamUrl') or obj.get('play_url') or obj.get('playUrl') or obj.get('m3u8') or obj.get('source')
    if isinstance(url,str) and url:
        x=_item(name or 'UNKNOWN',url,obj,base)
        if x:out.append(x)
    # name -> URL dictionaries.
    if not url and name and isinstance(obj.get('value'),str):
        x=_item(name,obj['value'],obj,base)
        if x:out.append(x)
    for key in ('channels','lives','items','data','list','streams','programs','results','rows'):
        if key in obj:_walk_json(obj[key],base,out,default_name)
    # Dictionary mapping channel names to URL(s).
    if not url:
        for k,v in obj.items():
            if isinstance(v,str) and v.startswith(('http://','https://','webview://')):
                x=_item(k,v,obj,base)
                if x:out.append(x)
            elif isinstance(v,list):
                for u in v:
                    if isinstance(u,str):
                        x=_item(k,u,obj,base)
                        if x:out.append(x)

def parse_json(text,base):
    out=[]; _walk_json(json.loads(text),base,out); return out

def parse_subscription_catalog(text,base):
    """Extract the second-level subscription URLs from a catalog JSON such as hw.json.
    It intentionally does not treat lives[] entries as channels.  Each lives item is a
    selectable source that will be fetched in the second stage.
    """
    obj=json.loads(text); out=[]
    if isinstance(obj,dict) and isinstance(obj.get('lives'),list):
        for item in obj['lives']:
            if not isinstance(item,dict): continue
            u=_norm_url(base,item.get('url',''))
            if not u: continue
            headers=item.get('headers') or {}
            if item.get('ua') and 'User-Agent' not in headers: headers={**headers,'User-Agent':item['ua']}
            out.append({
                'name':str(item.get('name') or u).strip(), 'url':u, 'enabled':True,
                'headers':headers, 'source_name':str(item.get('name') or '').strip(),
                'player_type':item.get('playerType'), 'epg':item.get('epg') or '',
                'logo':item.get('logo') or ''})
        seen=set(); unique=[]
        for item in out:
            u=item.get('url','')
            if u and u not in seen:
                seen.add(u); unique.append(item)
        return unique
    # Generic fallback: recursively collect named URL objects only when there is no lives[] catalog.
    def walk(x,default=''):
        if isinstance(x,list):
            for y in x: walk(y,default)
        elif isinstance(x,dict):
            name=x.get('name') or x.get('title') or default
            u=x.get('url') or x.get('source')
            if isinstance(u,str) and u.startswith(('http://','https://')):
                out.append({'name':str(name or u),'url':_norm_url(base,u),'enabled':True,'headers':x.get('headers') or {},'source_name':str(name or ''),'player_type':x.get('playerType'),'epg':x.get('epg') or '','logo':x.get('logo') or ''})
            else:
                for k,v in x.items():
                    if k not in ('headers','proxy','hosts','ads'): walk(v,name if isinstance(v,str) else default)
    walk(obj)
    seen=set(); unique=[]
    for item in out:
        u=item.get('url','')
        if u and u not in seen:
            seen.add(u); unique.append(item)
    return unique

def parse_xml(text,base):
    out=[]; root=ET.fromstring(text)
    for el in root.iter():
        if el.tag.lower().split('}')[-1] in ('channel','item','stream','programme'):
            a={k.split('}')[-1]:v for k,v in el.attrib.items()}; name=a.get('name') or a.get('title') or a.get('id')
            url=a.get('url') or a.get('src') or a.get('stream')
            if not url:
                for c in el:
                    if c.tag.lower().split('}')[-1] in ('url','source','playurl'): url=(c.text or '').strip()
            x=_item(name or 'UNKNOWN',url or '',a,base)
            if x:out.append(x)
    return out

def parse_text(text,base,content_type=''):
    s=text.lstrip('\ufeff \r\n\t'); ct=(content_type or '').lower()
    if s.startswith('#EXTM3U') or '#EXTINF' in s[:10000] or 'mpegurl' in ct:return parse_m3u(text,base)
    if s.startswith(('{','[')) or 'json' in ct:return parse_json(text,base)
    if s.startswith('<') or 'xml' in ct:return parse_xml(text,base)
    return parse_m3u(text,base) if any(',' in x and re.search(r'https?://',x) for x in s.splitlines()[:50]) else parse_json(text,base) if s[:1] in '[{' else parse_m3u(text,base)

async def fetch_text(url,timeout=15,headers=None):
    h={'User-Agent':'Source-Hunter-PRO/11.1','Accept':'*/*'}; h.update(headers or {})
    async with httpx.AsyncClient(follow_redirects=True,timeout=timeout,headers=h) as c:
        r=await c.get(url); r.raise_for_status(); return r.text

async def fetch(url,timeout=15,headers=None):
    h={'User-Agent':'Source-Hunter-PRO/11.1','Accept':'*/*'}; h.update(headers or {})
    async with httpx.AsyncClient(follow_redirects=True,timeout=timeout,headers=h) as c:
        r=await c.get(url); r.raise_for_status(); return r.text, r.headers.get('content-type',''), str(r.url)
