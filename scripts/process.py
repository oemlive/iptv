import json,os,re,datetime
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); raw=json.load(open(R+"/data/raw_hw.json",encoding="utf8")); items=raw.get("lives",[]) if isinstance(raw,dict) else []; good=[]; bad=[]
for x in items:
    if isinstance(x,dict) and str(x.get("name","")).strip() and re.match(r"^https?://",str(x.get("url","")).strip(),re.I): good.append(x)
    else: bad.append(x)
txt="\n".join(f'{str(x.get("name","")).strip()},{str(x.get("url","")).strip()}' for x in good)+("\n" if good else "")
now=datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
steps={"获取 hw.json":{"ok":True,"message":"成功"},"JSON 解析":{"ok":True,"message":f"{len(items)} 条"},"数据标准化":{"ok":True,"message":f"{len(good)} 条有效"},"地址检查":{"ok":True,"message":"基础 URL 检查"},"TXT 生成":{"ok":True,"message":f"{len(good)} 行"},"发布完成":{"ok":True,"message":"完成"}}
out={"status":"success","meta":{"source_name":"hw.json","source_url":"https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json","finished_at":now,"schedule":"每 30 分钟自动执行"},"stats":{"total":len(items),"valid":len(good),"invalid":len(bad)},"steps":steps,"logs":[f"{now} ✓ 获取 hw.json",f"{now} ✓ 解析 {len(items)} 条",f"{now} ✓ 有效 {len(good)} / 异常 {len(bad)}",f"{now} ✓ 生成 TXT {len(good)} 行",f"{now} ✓ 发布完成"],"txt":txt,"lives":good}
json.dump(out,open(R+"/data/latest.json","w",encoding="utf8"),ensure_ascii=False,indent=2)
