import datetime
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(ROOT, "data", "raw_hw.json")
OUT_PATH = os.path.join(ROOT, "data", "latest.json")
SOURCE_URL = "https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json"
URL_RE = re.compile(r"^https?://\S+$", re.I)


def main():
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    items = raw.get("lives", []) if isinstance(raw, dict) else []
    if not isinstance(items, list):
        raise ValueError("lives 不是数组")

    good, bad, seen = [], [], set()
    for item in items:
        if not isinstance(item, dict):
            bad.append(item)
            continue
        name = str(item.get("name", "")).strip()
        url = str(item.get("url", "")).strip()
        key = (name, url)
        if not name or not URL_RE.match(url):
            bad.append(item)
        elif key not in seen:
            seen.add(key)
            good.append({**item, "name": name, "url": url})

    txt = "".join(f"{item['name']},{item['url']}\n" for item in good)
    now = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    steps = {
        "获取 hw.json": {"ok": True, "message": "成功"},
        "JSON 解析": {"ok": True, "message": f"{len(items)} 条"},
        "数据标准化": {"ok": True, "message": f"{len(good)} 条有效"},
        "地址检查": {"ok": True, "message": "HTTP/HTTPS URL 格式检查"},
        "TXT 生成": {"ok": True, "message": f"{len(good)} 行"},
        "发布完成": {"ok": True, "message": "完成"},
    }
    out = {
        "status": "success",
        "meta": {"source_name": "hw.json", "source_url": SOURCE_URL, "finished_at": now, "schedule": "每 30 分钟自动执行"},
        "stats": {"total": len(items), "valid": len(good), "invalid": len(bad), "duplicates_removed": len(items) - len(good) - len(bad)},
        "steps": steps,
        "logs": [
            f"{now} ✓ 获取 hw.json",
            f"{now} ✓ 解析 {len(items)} 条",
            f"{now} ✓ 有效 {len(good)} / 异常 {len(bad)}",
            f"{now} ✓ 生成 TXT {len(good)} 行",
            f"{now} ✓ 发布完成",
        ],
        "txt": txt,
        "lives": good,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
