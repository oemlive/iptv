from urllib.parse import urljoin
import json,re,xml.etree.ElementTree as ET

def norm_url(base,u):
    u=str(u or '').strip().strip('"\'')
    if not u:return ''
    if re.match(r'^(https?|rtmp|rtsp|udp|p2p|webview)://',u,re.I):return u
    return urljoin(base,u)

def item(name,url,obj=None,base=''):
    if not name or not url:return None
    obj=obj or {}
    return {'name':str(name).strip(),'url':norm_url(base,url),'group':str(obj.get('group') or obj.get('group_name') or ''),'logo':str(obj.get('logo') or obj.get('tvg-logo') or ''),'tvg_id':str(obj.get('tvg_id') or obj.get('id') or '')}

def parse_m3u(text,base):
    out=[]; pending=None
    for line in text.replace('\ufeff','').splitlines():
        line=line.strip()
        if not line:continue
        if line.upper().startswith('#EXTINF'):
            attrs={k:v for k,v in re.findall(r'([\w-]+)="([^"]*)"',line)}
            name=line.split(',',1)[1].strip() if ',' in line else attrs.get('tvg-name','UNKNOWN')
            pending={'name':name,'group':attrs.get('group-title',''),'logo':attrs.get('tvg-logo',''),'tvg_id':attrs.get('tvg-id','')}
        elif not line.startswith('#'):
            if pending:
                x=item(pending['name'],line,pending,base); pending=None
            else:
                p=[x.strip() for x in line.split(',',1)]; x=item(p[0],p[1] if len(p)>1 else p[0],{},base)
            if x:out.append(x)
    return out

def walk_json(obj,base,out,default=''):
    if isinstance(obj,list):
        for x in obj:walk_json(x,base,out,default)
    elif isinstance(obj,dict):
        name=obj.get('name') or obj.get('title') or obj.get('channel_name') or default
        url=obj.get('url') or obj.get('stream_url') or obj.get('streamUrl') or obj.get('play_url') or obj.get('playUrl') or obj.get('m3u8') or obj.get('source')
        if isinstance(url,str) and url:
            x=item(name or 'UNKNOWN',url,obj,base)
            if x:out.append(x)
        for k in ('channels','lives','items','data','list','streams','programs','results','rows'):
            if k in obj:walk_json(obj[k],base,out,default)
        if not url:
            for k,v in obj.items():
                if isinstance(v,str) and re.match(r'^(https?|webview)://',v,re.I):
                    x=item(k,v,obj,base)
                    if x:out.append(x)
                elif isinstance(v,list):
                    for u in v:
                        if isinstance(u,str) and re.match(r'^(https?|webview)://',u,re.I):
                            x=item(k,u,obj,base)
                            if x:out.append(x)

def parse_json(text,base):
    out=[];walk_json(json.loads(text),base,out);return out

def parse_xml(text,base):
    out=[];root=ET.fromstring(text)
    for el in root.iter():
        tag=el.tag.lower().split('}')[-1]
        if tag in ('channel','item','stream','programme'):
            a={k.split('}')[-1]:v for k,v in el.attrib.items()};name=a.get('name') or a.get('title') or a.get('id');url=a.get('url') or a.get('src') or a.get('stream')
            if not url:
                for c in el:
                    if c.tag.lower().split('}')[-1] in ('url','source','playurl'):url=(c.text or '').strip()
            x=item(name or 'UNKNOWN',url or '',a,base)
            if x:out.append(x)
    return out

def parse_text(text,base,content_type=''):
    s=text.lstrip('\ufeff \r\n\t');ct=(content_type or '').lower()
    if s.startswith('#EXTM3U') or '#EXTINF' in s[:10000] or 'mpegurl' in ct:return parse_m3u(text,base)
    if s.startswith(('{','[')) or 'json' in ct:return parse_json(text,base)
    if s.startswith('<') or 'xml' in ct:return parse_xml(text,base)
    return parse_m3u(text,base)
