import re

MAINLAND = ["cctv", "央视", "中央电视台", "卫视", "湖南", "浙江", "江苏", "东方", "北京卫视", "广东卫视", "深圳卫视", "山东卫视", "河南卫视", "湖北卫视", "安徽卫视", "四川卫视", "辽宁卫视", "黑龙江卫视", "江西卫视", "广西卫视", "云南卫视", "贵州卫视", "陕西卫视", "甘肃卫视", "青海卫视", "宁夏卫视", "新疆卫视", "海南卫视", "重庆卫视", "天津卫视", "河北卫视", "山西卫视", "内蒙古卫视", "吉林卫视", "福建卫视"]
HK_TW = ["香港", "香港", "hk", "tvb", "翡翠", "明珠", "凤凰", "nowtv", "viu", "有线", "台湾", "台灣", "taiwan", "twn"]
SUBGROUPS = {
    "影视": ["电影", "影院", "影视", "剧场", "电视剧", "动作", "电影频道"],
    "少儿": ["少儿", "儿童", "卡通", "动画", "动漫", "kids"],
    "体育": ["体育", "sports", "espn", "足球", "篮球", "网球", "nba", "cctv5"],
    "新闻": ["新闻", "资讯", "news", "凤凰资讯"],
    "财经": ["财经", "finance", "business"],
    "音乐": ["音乐", "music", "mtv"],
    "教育": ["教育", "科教", "课堂", "education"],
    "国外": ["美国", "英国", "法国", "德国", "日本", "韩国", "俄", "海外", "international", "usa", "uk", "japan", "korea"],
    "4K": ["4k", "uhd", "2160p"],
    "纪实": ["纪实", "纪录", "documentary"],
}

def classify(name: str, url: str = "") -> tuple[str, str]:
    s = (name + " " + url).lower()
    if any(x.lower() in s for x in HK_TW):
        return "港台", next((k for k,v in SUBGROUPS.items() if any(x.lower() in s for x in v)), "其他")
    if any(x.lower() in s for x in MAINLAND):
        return "央卫", "央视" if "cctv" in s or "央视" in s else "卫视"
    for group, words in SUBGROUPS.items():
        if any(x.lower() in s for x in words):
            return "其他", group
    return "其他", "其他"

def normalize_name(name: str) -> str:
    s = re.sub(r"[【\[（(].*?[】\]）)]", "", name)
    s = re.sub(r"\s+", " ", s).strip()
    aliases = {"cctv1":"CCTV-1", "cctv 1":"CCTV-1", "cctv-1高清":"CCTV-1", "cctv5":"CCTV-5", "cctv 5":"CCTV-5"}
    return aliases.get(s.lower(), s or "未命名")
