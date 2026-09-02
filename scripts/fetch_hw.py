import base64,json,os,sys,time
from urllib.request import Request,urlopen
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); C=json.load(open(R+"/config/sources.json",encoding="utf8")); logs=[]
def get(u):
    raw=urlopen(Request(u,headers={"User-Agent":"IPTV-Auto/3.0","Accept":"application/json,text/plain,*/*"}),timeout=C["timeout_seconds"]).read().decode("utf8-sig")
    x=json.loads(raw)
    if isinstance(x,dict) and x.get("content") and x.get("encoding")=="base64": return json.loads(base64.b64decode(x["content"]).decode("utf8-sig"))
    return x
for i,u in enumerate(C["urls"],1):
    for a in range(1,C["retries"]+1):
        try:
            x=get(u); json.dump(x,open(R+"/data/raw_hw.json","w",encoding="utf8"),ensure_ascii=False,indent=2); logs.append(f"✓ 源 {i} 获取成功，第 {a} 次"); print(json.dumps({"ok":1,"logs":logs},ensure_ascii=False)); sys.exit(0)
        except Exception as e:
            logs.append(f"× 源 {i} 第 {a} 次失败：{type(e).__name__}: {e}"); time.sleep(min(a*2,5))
print(json.dumps({"ok":0,"logs":logs},ensure_ascii=False)); sys.exit(1)
