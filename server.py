#!/usr/bin/env python3
import json,re,threading,time,traceback,urllib.request,urllib.error,xml.etree.ElementTree as ET
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,unquote,urljoin
from datetime import datetime
from email.utils import parsedate_to_datetime
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; OUT=ROOT/'output'; WEB=ROOT/'web'; LOCK=threading.RLock(); RUNNING=False

def now(): return datetime.now().astimezone().isoformat(timespec='seconds')
def readj(p,d):
    with LOCK:
        try:return json.loads(p.read_text('utf8'))
        except:return d

def writej(p,o):
    DATA.mkdir(exist_ok=True); tmp=p.with_suffix('.tmp'); tmp.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf8'); tmp.replace(p)
def cfg(): return readj(DATA/'config.json',{})
def channels(): return readj(DATA/'channels.json',{'channels':[]})
def source_cache(): return readj(DATA/'source_cache.json',{})
def status(): return readj(DATA/'status.json',{'running':False,'last_run':None,'last_error':None,'last_result':None})
def norm(u):
    u=str(u or '').strip()
    p=urlparse(u)
    if p.scheme not in ('http','https') or not p.netloc: raise ValueError('只允许 http:// 或 https:// 订阅地址')
    return u

def fetch(u,timeout,ua):
    req=urllib.request.Request(norm(u),headers={'User-Agent':ua,'Accept':'*/*'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read(32*1024*1024); ct=r.headers.get('Content-Type',''); enc=r.headers.get_content_charset() or 'utf-8'; final=r.geturl()
    return raw.decode(enc,errors='replace'),ct,final

def item(name,url,group='',logo='',tvg=''):
    u=str(url or '').strip(); n=str(name or '').strip()
    if not n or not u:return None
    return {'name':n,'url':u,'group':str(group or '其他').strip() or '其他','logo':str(logo or ''),'tvg_id':str(tvg or '')}
def parse_m3u(text):
    out=[]; pending=None
    for raw in text.replace('\r','').split('\n'):
        line=raw.strip()
        if not line:continue
        if line.upper().startswith('#EXTINF'):
            attrs=dict(re.findall(r'([\w-]+)="([^"]*)"',line)); name=line.split(',',1)[1].strip() if ',' in line else attrs.get('tvg-name','')
            pending=(name,attrs.get('group-title') or attrs.get('group') or '其他',attrs.get('tvg-logo',''),attrs.get('tvg-id','')); continue
        if line.startswith('#'):continue
        if pending:
            x=item(pending[0],line,pending[1],pending[2],pending[3]); pending=None
        elif ',' in line:
            n,u=line.split(',',1); x=item(n,u)
        else:x=None
        if x:out.append(x)
    return out

def walk_json(o,out,default_group='其他'):
    if isinstance(o,list):
        for x in o:walk_json(x,out,default_group)
    elif isinstance(o,dict):
        n=o.get('name') or o.get('title') or o.get('channel_name') or o.get('channelName'); u=o.get('url') or o.get('play_url') or o.get('playUrl') or o.get('m3u8') or o.get('source') or o.get('stream_url')
        g=o.get('group') or o.get('group_name') or o.get('category') or default_group
        if isinstance(u,str) and u and n:
            x=item(n,u,g,o.get('logo') or o.get('tvg-logo',''),o.get('tvg_id') or o.get('id','')); x and out.append(x)
        for k in ('channels','lives','items','data','list','streams','results','rows','programs'):
            if k in o:walk_json(o[k],out,g)
        if not u:
            for k,v in o.items():
                if isinstance(v,str) and v.startswith(('http://','https://')):
                    x=item(k,v,g); x and out.append(x)
                elif isinstance(v,list):
                    for z in v:
                        if isinstance(z,str) and z.startswith(('http://','https://')):
                            x=item(k,z,g); x and out.append(x)

def parse_xml(text):
    out=[]; root=ET.fromstring(text)
    for e in root.iter():
        tag=e.tag.lower().split('}')[-1]
        if tag in ('channel','item','stream'):
            a={k.split('}')[-1]:v for k,v in e.attrib.items()}; n=a.get('name') or a.get('title') or a.get('id'); u=a.get('url') or a.get('src') or a.get('stream')
            if not u:
                for c in e:
                    if c.tag.lower().split('}')[-1] in ('url','source','playurl'):u=(c.text or '').strip()
            x=item(n,u,a.get('group') or a.get('category') or '其他',a.get('logo') or a.get('tvg-logo',''),a.get('tvg-id') or a.get('id','')); x and out.append(x)
    return out

def parse(text,ct=''):
    s=text.lstrip('\ufeff \r\n\t'); low=ct.lower()
    if s.startswith('#EXTM3U') or '#EXTINF' in s[:10000] or 'mpegurl' in low:return parse_m3u(text)
    if s[:1] in '[{' or 'json' in low:
        o=json.loads(text); out=[]; walk_json(o,out); return out
    if s.startswith('<') or 'xml' in low:return parse_xml(text)
    return parse_m3u(text)

def category(ch,rules):
    n=(ch['name']+' '+ch.get('group','')).lower(); kw=rules.get('category_keywords',{})
    for cat,words in kw.items():
        if any(str(w).lower() in n for w in words):return cat
    g=ch.get('group','').strip()
    return g if g and g!='其他' else '其他'

def apply(chs,cfg):
    rules=cfg.get('rules',{}); inc=[x.lower() for x in rules.get('include_keywords',[]) if x]; exc=[x.lower() for x in rules.get('exclude_keywords',[]) if x]; out=[]
    for ch in chs:
        ch=dict(ch); ch['category']=category(ch,rules); text=(ch['name']+' '+ch.get('group','')+' '+ch['url']).lower()
        if exc and any(x in text for x in exc): ch['selected']=False; continue
        if inc and not any(x in text for x in inc): ch['selected']=False; continue
        ch['selected']=ch.get('selected',True); out.append(ch)
    return out

def stable_id(name,url):
    import hashlib
    return hashlib.sha1((str(name)+'\0'+str(url)).encode()).hexdigest()[:16]

def rebuild_from_cache(c, previous=None):
    cache=source_cache(); merged=[]
    for s in c.get('subscriptions',[]):
        if s.get('enabled') is False: continue
        entry=cache.get(s.get('url'),{})
        for x in entry.get('items',[]):
            y=dict(x); y['source']=s.get('url'); merged.append(y)
    d={}
    for x in merged:d.setdefault((x['name'].strip().lower(),x['url'].strip()),x)
    arr=apply(list(d.values()),c)
    oldsel={x.get('id'):x.get('selected',True) for x in (previous or channels()).get('channels',[])}
    for x in arr:
        x['id']=stable_id(x['name'],x['url']); x['selected']=oldsel.get(x['id'],True)
    writej(DATA/'channels.json',{'updated_at':now(),'channels':arr})
    return arr, len(merged)

def generate_only(x,c):
    OUT.mkdir(exist_ok=True); fn=c.get('output',{}).get('filename','webtv.m3u'); path=OUT/fn; lines=['#EXTM3U']
    for ch in x.get('channels',[]):
        if ch.get('selected'):
            attrs=f'tvg-id="{ch.get("tvg_id","")}" group-title="{ch.get("category") or ch.get("group") or "其他"}"'
            if ch.get('logo'): attrs+=f' tvg-logo="{ch["logo"]}"'
            lines += [f'#EXTINF:-1 {attrs},{ch["name"]}',ch['url']]
    path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    return {'output':str(path.relative_to(ROOT)),'selected':sum(1 for ch in x.get('channels',[]) if ch.get('selected'))}

def run(only=None):
    global RUNNING
    with LOCK:
        if RUNNING:return {'ok':False,'error':'已有更新任务正在运行'}
        RUNNING=True
    c=cfg(); st=status(); st.update({'running':True,'last_error':None}); writej(DATA/'status.json',st); results=[]
    try:
        subs=c.get('subscriptions',[]); indexes=[only] if only is not None else list(range(len(subs))); cache=source_cache()
        for i in indexes:
            if i<0 or i>=len(subs):continue
            s=subs[i]
            if s.get('enabled') is False:continue
            try:
                text,ct,final=fetch(s['url'],int(c.get('settings',{}).get('timeout',20)),c.get('settings',{}).get('user_agent','WebTV-Backend-Manager/1.0')); items=parse(text,ct)
                for x in items:x['source']=s['url']
                cache[s['url']]={'items':items,'updated_at':now(),'final_url':final,'error':None}; s['last_count']=len(items); s['last_error']=None; s['last_updated']=now(); results.append({'name':s.get('name',s['url']),'url':s['url'],'ok':True,'count':len(items),'final_url':final})
            except Exception as e:
                prev=cache.get(s['url'],{}); cache[s['url']]=prev; s['last_error']=str(e)[:500]; results.append({'name':s.get('name',s['url']),'url':s['url'],'ok':False,'error':str(e)[:500],'using_cache':bool(prev.get('items'))})
        writej(DATA/'source_cache.json',cache); arr,raw_count=rebuild_from_cache(c); gen=generate_only({'channels':arr},c)
        ok=bool(results) and all(r['ok'] for r in results); result={'ok':ok,'updated_at':now(),'sources':results,'raw_count':raw_count,'unique_count':len(arr),'selected_count':gen['selected'],'output':gen['output']}
        st.update({'running':False,'last_run':now(),'last_result':result,'last_error':None if ok else '一个或多个订阅源获取失败（已有缓存时仍保留旧数据）'}); writej(DATA/'status.json',st); writej(DATA/'config.json',c); return result
    except Exception as e:
        st.update({'running':False,'last_run':now(),'last_error':str(e),'last_result':{'trace':traceback.format_exc()}}); writej(DATA/'status.json',st); return {'ok':False,'error':str(e)}
    finally: RUNNING=False

def scheduler():
    while True:
        try:
            c=cfg(); sc=c.get('schedule',{}); nowd=datetime.now()
            if sc.get('enabled') and nowd.strftime('%H:%M')==sc.get('time','03:00'):
                st=status(); last=st.get('last_run',''); key=nowd.strftime('%Y-%m-%d')
                if not str(last).startswith(key):run()
        except:pass
        time.sleep(20)
threading.Thread(target=scheduler,daemon=True).start()
class H(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*a):pass
    def sendj(self,code,o):
        b=json.dumps(o,ensure_ascii=False).encode(); self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(b)
    def body(self):
        n=int(self.headers.get('Content-Length','0') or 0); return json.loads(self.rfile.read(n).decode()) if n else {}
    def do_GET(self):
        p=unquote(urlparse(self.path).path)
        if p=='/api/config':return self.sendj(200,{'config':cfg()})
        if p=='/api/channels':return self.sendj(200,channels())
        if p=='/api/status':return self.sendj(200,{'status':status()})
        if p=='/api/health':return self.sendj(200,{'ok':True,'service':'webtv-backend-manager','version':1})
        if p.startswith('/output/'):
            f=Path(p[len('/output/'):]).name; path=OUT/f
            if not path.exists():return self.sendj(404,{'error':'输出文件不存在，请先更新'})
            b=path.read_bytes();self.send_response(200);self.send_header('Content-Type','audio/x-mpegurl; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        if p in ('/','/index.html'):
            b=(WEB/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        return self.sendj(404,{'error':'Not Found'})
    def do_POST(self):
        p=unquote(urlparse(self.path).path)
        try:
            d=self.body(); c=cfg()
            if p=='/api/subscriptions':
                u=norm(d.get('url')); c.setdefault('subscriptions',[]).append({'name':str(d.get('name') or u),'url':u,'enabled':True});writej(DATA/'config.json',c);return self.sendj(200,{'ok':True,'config':c})
            if p=='/api/run':return self.sendj(200,run(d.get('only')))
            if p=='/api/channels/select':
                x=channels(); found=False
                for ch in x['channels']:
                    if ch.get('id')==d.get('id'):ch['selected']=bool(d.get('selected'));found=True;break
                if not found:raise ValueError('频道不存在')
                writej(DATA/'channels.json',x); run_result=generate_only(x,c); return self.sendj(200,{'ok':True,'channel':d.get('id'),'result':run_result})
            if p=='/api/channels/batch':
                x=channels(); ids=set(d.get('ids',[]))
                for ch in x['channels']:
                    if ch.get('id') in ids:ch['selected']=bool(d.get('selected'))
                writej(DATA/'channels.json',x);generate_only(x,c);return self.sendj(200,{'ok':True,'count':len(ids)})
            if p=='/api/rules':
                c['rules']={'include_keywords':[str(x).strip() for x in d.get('include_keywords',[]) if str(x).strip()],'exclude_keywords':[str(x).strip() for x in d.get('exclude_keywords',[]) if str(x).strip()],'category_keywords':d.get('category_keywords',{})};writej(DATA/'config.json',c);arr,_=rebuild_from_cache(c);generate_only({'channels':arr},c);return self.sendj(200,{'ok':True,'count':len(arr)})
            if p=='/api/schedule':
                t=str(d.get('time','03:00')); 
                if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',t):raise ValueError('时间格式错误')
                c['schedule']={'enabled':bool(d.get('enabled')),'time':t};writej(DATA/'config.json',c);return self.sendj(200,{'ok':True,'schedule':c['schedule']})
            if p=='/api/output':
                fn=Path(str(d.get('filename','webtv.m3u'))).name
                if not fn.lower().endswith('.m3u'):fn+='.m3u'
                c['output']={'filename':fn,'base_url':str(d.get('base_url','')).rstrip('/'),'path':'/output/'+fn};writej(DATA/'config.json',c);generate_only(channels(),c);return self.sendj(200,{'ok':True,'output':c['output']})
            return self.sendj(404,{'error':'Not Found'})
        except urllib.error.HTTPError as e:return self.sendj(400,{'error':f'上游 HTTP {e.code}: {e.reason}'})
        except Exception as e:return self.sendj(400,{'error':str(e)})
    def do_PATCH(self):
        p=unquote(urlparse(self.path).path)
        try:
            c=cfg();m=re.fullmatch(r'/api/subscriptions/(\d+)',p)
            if not m:return self.sendj(404,{'error':'Not Found'})
            i=int(m.group(1)); d=self.body(); c['subscriptions'][i].update(d);writej(DATA/'config.json',c);return self.sendj(200,{'ok':True})
        except Exception as e:return self.sendj(400,{'error':str(e)})
    def do_DELETE(self):
        p=unquote(urlparse(self.path).path)
        try:
            m=re.fullmatch(r'/api/subscriptions/(\d+)',p)
            if not m:return self.sendj(404,{'error':'Not Found'})
            c=cfg();del c['subscriptions'][int(m.group(1))];writej(DATA/'config.json',c);return self.sendj(200,{'ok':True})
        except Exception as e:return self.sendj(400,{'error':str(e)})

if __name__=='__main__':
    DATA.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True);print('WEB后台管理: http://127.0.0.1:8787/');ThreadingHTTPServer(('0.0.0.0',int(cfg().get('port',8787))),H).serve_forever()
