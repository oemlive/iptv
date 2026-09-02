import json,os,sys,time,base64,subprocess
from urllib.request import Request,urlopen
from datetime import datetime
R=os.path.dirname(os.path.dirname(__file__));C=json.load(open(os.path.join(R,'config/sources.json'),encoding='utf8'));logs=[];data=None;used=''
for i,u in enumerate(C['urls'],1):
 for a in range(1,C['retries']+1):
  try:
   q=Request(u,headers={'User-Agent':'IPTV-Auto-Backend/2.0','Accept':'application/json,text/plain,*/*'}); raw=urlopen(q,timeout=C['timeout_seconds']).read().decode('utf-8-sig'); obj=json.loads(raw)
   if isinstance(obj,dict) and obj.get('encoding')=='base64' and obj.get('content'): obj=json.loads(base64.b64decode(obj['content']).decode())
   if not isinstance(obj,dict): raise ValueError('返回不是 JSON 对象')
   data=obj;used=u;logs.append(f'✓ 获取成功：备用源 {i}，第 {a} 次');break
  except Exception as e:
   logs.append(f'× 源 {i} 第 {a} 次失败：{type(e).__name__}: {e}');time.sleep(min(a*2,5))
 if data is not None:break
now=datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z');out={'status':'failed' if data is None else 'success','meta':{'source_name':'hw.json','source_url':used or C['urls'][0],'finished_at':now,'schedule':'每 30 分钟自动执行'},'stats':{'total':0,'valid':0,'invalid':0},'steps':{},'logs':logs}
if data is not None:
 lives=data.get('lives',[]) if isinstance(data,dict) else []; valid=[x for x in lives if isinstance(x,dict) and str(x.get('name','')).strip() and str(x.get('url','')).startswith(('http://','https://'))]; out['stats']={'total':len(lives),'valid':len(valid),'invalid':len(lives)-len(valid)};out['steps']={'获取 hw.json':{'ok':1,'message':'成功'},'JSON 解析':{'ok':1,'message':'成功'},'数据标准化':{'ok':1,'message':f'{len(valid)} 条有效'},'地址检查':{'ok':1,'message':'基础 URL 检查'},'结果生成':{'ok':1,'message':'成功'},'发布完成':{'ok':1,'message':'GitHub Pages'}};out['lives']=valid;open(os.path.join(R,'data','raw_hw.json'),'w',encoding='utf8').write(json.dumps(data,ensure_ascii=False,indent=2))
else: out['steps']={'获取 hw.json':{'ok':0,'message':'全部备用源失败'}}
open(os.path.join(R,'data','latest.json'),'w',encoding='utf8').write(json.dumps(out,ensure_ascii=False,indent=2));sys.exit(0 if data is not None else 1)
