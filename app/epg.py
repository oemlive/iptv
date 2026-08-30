import httpx
from pathlib import Path
from xml.etree import ElementTree as ET

async def fetch_epg(urls, out):
    if not urls: return {'ok':True,'sources':0,'programmes':0}
    roots=[]; channels={}; programmes=[]
    for url in urls:
        try:
            async with httpx.AsyncClient(follow_redirects=True,timeout=20,headers={'User-Agent':'Source-Hunter-PRO/9.5'}) as c:
                r=await c.get(url); r.raise_for_status(); root=ET.fromstring(r.content)
            for e in root.findall('channel'):
                cid=e.get('id');
                if cid and cid not in channels: channels[cid]=e
            programmes.extend(list(root.findall('programme')))
        except Exception as e:
            print('EPG FAIL',url,e)
    root=ET.Element('tv',{'generator-info-name':'Source Hunter PRO'})
    for e in channels.values(): root.append(e)
    for e in programmes: root.append(e)
    ET.ElementTree(root).write(out,encoding='utf-8',xml_declaration=True)
    return {'ok':True,'sources':len(urls),'programmes':len(programmes)}
