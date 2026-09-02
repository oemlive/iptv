import hashlib,json,re
from urllib.parse import urlparse
from .models import Source
from .classifier import classify,normalize_name
URL_RE=re.compile(r'''https?://[^\s"'<>]+''',re.I)
ATTR_RE=re.compile(r'''([\w:-]+)=(?:"([^"]*)"|'([^']*)')''')
def clean_url(u): return u.strip().rstrip(',;|)')
def source_id(name,url): return hashlib.sha256((normalize_name(name)+'|'+clean_url(url).lower()).encode()).hexdigest()[:20]
def parse_m3u(text,origin='manual'):
    out=[];name='';attrs={}
    for raw in text.replace('\r','').split('\n'):
        line=raw.strip()
        if not line: continue
        if line.upper().startswith('#EXTINF'):
            name=line.split(',',1)[1].strip() if ',' in line else '未命名'
            attrs={k:(a or b or '') for k,a,b in ATTR_RE.findall(line)}
        elif not line.startswith('#'):
            m=URL_RE.match(line)
            if not m: continue
            url=clean_url(m.group(0)); n=normalize_name(name or urlparse(url).path.rsplit('/',1)[-1]); g,s=classify(n,url)
            if attrs.get('group-title'): g,s=classify(attrs['group-title']+' '+n,url)
            out.append(Source(id=source_id(n,url),name=n,url=url,group=g,subgroup=s,origin=origin,discovered_at=origin))
            name='';attrs={}
    return out
def from_json(obj,origin='manual'):
    out=[]
    if isinstance(obj,dict):
        for key in ('data','items','list','channels','streams','results'):
            if key in obj and isinstance(obj[key],(list,dict)): return from_json(obj[key],origin)
        url=next((obj.get(k) for k in ('url','play_url','stream_url','playUrl','m3u8') if obj.get(k)),None)
        if url:
            name=str(next((obj.get(k) for k in ('name','title','channel','channel_name') if obj.get(k)),'未命名'));n=normalize_name(name);g,s=classify(n,str(url));out.append(Source(id=source_id(n,str(url)),name=n,url=clean_url(str(url)),group=g,subgroup=s,origin=origin,discovered_at=origin))
    elif isinstance(obj,list):
        for x in obj: out.extend(from_json(x,origin))
    return out
def parse_text(text,origin='manual'):
    t=text.lstrip('\ufeff \t\r\n')
    if '#EXTINF' in t[:20000] or t.upper().startswith('#EXTM3U'): return dedupe(parse_m3u(text,origin))
    try:
        got=from_json(json.loads(text),origin)
        if got:return dedupe(got)
    except Exception: pass
    out=[]
    for raw in text.replace('\r','').split('\n'):
        line=raw.strip()
        if not line or line.startswith('#'):continue
        if ',' in line:
            name,url=line.split(',',1);url=clean_url(url)
            if URL_RE.match(url):
                n=normalize_name(name);g,s=classify(n,url);out.append(Source(id=source_id(n,url),name=n,url=url,group=g,subgroup=s,origin=origin,discovered_at=origin))
        else:
            m=URL_RE.search(line)
            if m:
                url=clean_url(m.group(0));n=normalize_name(urlparse(url).path.rsplit('/',1)[-1]);g,s=classify(n,url);out.append(Source(id=source_id(n,url),name=n,url=url,group=g,subgroup=s,origin=origin,discovered_at=origin))
    return dedupe(out)
def dedupe(items):
    seen=set();out=[]
    for x in items:
        k=clean_url(x.url).lower()
        if k and k not in seen:seen.add(k);out.append(x)
    return out
