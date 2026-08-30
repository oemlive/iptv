import re
DEFAULT_RULES=[
 {'keyword':'CCTV','category':'央视','priority':100},{'keyword':'央视','category':'央视','priority':100},
 {'keyword':'卫视','category':'卫视','priority':90},{'keyword':'TVB','category':'港台','priority':90},{'keyword':'凤凰','category':'港台','priority':90}]

def classify(name, group='', url='', rules=None):
    s=f'{name} {group}'.upper(); u=url.lower()
    if u.startswith('webview://') or any(x in u for x in ('tv.cctv.com','yangshipin.cn')) or re.search(r'央视频|央视网|WEBVIEW|网页',s): return '网页'
    rr=rules or DEFAULT_RULES
    for r in sorted(rr,key=lambda x:int(x.get('priority',0)),reverse=True):
        if str(r.get('keyword','')).strip() and str(r.get('keyword')).upper() in s: return r.get('category','其他')
    if re.search(r'凤凰|TVB|NOW|翡翠|明珠|港台|香港|澳门|台湾|中天|东森|三立|民视|港剧|卫视中文|ViuTV',s): return '港台'
    if re.search(r'\bCCTV\s*[- ]?\d|CCTV|央视|中央电视台',s): return '央视'
    if re.search(r'卫视|湖南|浙江|江苏|东方|北京|广东|深圳|安徽|山东|湖北|四川|河南|河北|江西|辽宁|黑龙江|吉林|陕西|广西|贵州|云南|重庆|天津|东南|厦门|金鹰|海南|甘肃|宁夏|青海|内蒙古|新疆|西藏',s): return '卫视'
    return '其他'

def protocol(url):
    u=url.lower()
    if u.startswith('webview://') or any(x in u for x in ('tv.cctv.com','yangshipin')): return 'web'
    if '.m3u8' in u:return 'hls'
    if u.endswith('.ts') or '/ts' in u:return 'mpegts'
    if u.endswith('.flv') or '.flv?' in u:return 'flv'
    return 'http'
