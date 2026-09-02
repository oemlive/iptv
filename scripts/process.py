import datetime
import json
import os
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(ROOT, "data", "raw_hw.json")
OUT_PATH = os.path.join(ROOT, "data", "latest.json")
SOURCE_URL = "https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json"
URL_RE = re.compile(r"^https?://\S+$", re.I)


def decode_bytes(data):
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    for enc in ("utf-8", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def fetch_text(url, timeout, ua="IPTV-Auto-Backend/3.1"):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*", "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return decode_bytes(r.read())


def clean_name(name):
    return re.sub(r"\s+", " ", str(name or "").strip())


def clean_url(url, base=""):
    url = str(url or "").strip().strip('"\'')
    if base and not re.match(r"^https?://", url, re.I):
        url = urljoin(base, url)
    return url


def parse_m3u(text, base):
    result = []
    pending = None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#EXTINF"):
            title = s.rsplit(",", 1)[-1].strip() if "," in s else ""
            attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', s))
            pending = clean_name(title or attrs.get("tvg-name") or attrs.get("tvg-id"))
        elif not s.startswith("#") and pending:
            u = clean_url(s, base)
            if URL_RE.match(u):
                result.append({"name": pending, "url": u})
            pending = None
    return result


def parse_txt(text, base):
    result = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("//"):
            continue
        if "," in s:
            name, url = s.split(",", 1)
        elif "，" in s:
            name, url = s.split("，", 1)
        else:
            continue
        name, url = clean_name(name), clean_url(url, base)
        if name and URL_RE.match(url):
            result.append({"name": name, "url": url})
    return result


def parse_json(text, base):
    try:
        obj = json.loads(text.lstrip("\ufeff"))
    except Exception:
        return []
    if isinstance(obj, dict):
        items = obj.get("lives") or obj.get("channels") or obj.get("data") or []
    else:
        items = obj
    if not isinstance(items, list):
        return []
    result = []
    for x in items:
        if not isinstance(x, dict):
            continue
        name = clean_name(x.get("name") or x.get("title") or x.get("channel"))
        url = clean_url(x.get("url") or x.get("playUrl") or x.get("play_url"), base)
        if name and URL_RE.match(url):
            result.append({"name": name, "url": url, **({"ua": x["ua"]} if x.get("ua") else {})})
    return result


def parse_source(text, url):
    stripped = text.lstrip("\ufeff \r\n")
    if stripped.startswith("#EXTM3U") or "#EXTINF:" in stripped[:10000]:
        return parse_m3u(text, url), "M3U"
    if stripped.startswith("{") or stripped.startswith("["):
        rows = parse_json(text, url)
        if rows:
            return rows, "JSON"
    return parse_txt(text, url), "TXT"


def main():
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    sources = raw.get("lives", []) if isinstance(raw, dict) else []
    if not isinstance(sources, list):
        raise ValueError("hw.json 的 lives 不是数组")

    timeout = 12
    valid_sources, bad_sources = [], []
    for source in sources:
        if not isinstance(source, dict):
            bad_sources.append("非对象")
            continue
        name = clean_name(source.get("name"))
        url = clean_url(source.get("url"))
        if not name or not URL_RE.match(url):
            bad_sources.append(name or "未命名")
            continue
        valid_sources.append((name, url, source.get("ua") or "IPTV-Auto-Backend/3.1"))

    def worker(item):
        name, url, ua = item
        try:
            text = fetch_text(url, timeout, ua)
            rows, fmt = parse_source(text, url)
            return name, True, fmt, rows, ""
        except urllib.error.HTTPError as e:
            return name, False, "", [], f"HTTP {e.code}"
        except Exception as e:
            return name, False, "", [], f"{type(e).__name__}: {e}"

    all_channels, logs = [], []
    format_count = {"M3U": 0, "TXT": 0, "JSON": 0}
    seen = set()
    parsed_total = 0
    source_ok = 0
    max_workers = min(8, max(1, len(valid_sources)))

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(worker, item) for item in valid_sources]
        for future in as_completed(futures):
            name, ok, fmt, rows, error = future.result()
            if not ok:
                bad_sources.append(name)
                logs.append(f"× {name}: {error}")
                continue
            source_ok += 1
            format_count[fmt] += 1
            parsed_total += len(rows)
            added = 0
            for row in rows:
                key = (row["name"].casefold(), row["url"])
                if key in seen:
                    continue
                seen.add(key)
                all_channels.append(row)
                added += 1
            logs.append(f"✓ {name}: {fmt}，解析 {len(rows)}，新增 {added}")

    txt = "".join(f"{x['name']},{x['url']}\n" for x in all_channels)
    now = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    status = "success" if all_channels else "failed"
    steps = {
        "获取 hw.json": {"ok": True, "message": f"入口信息 {len(sources)} 条"},
        "JSON 解析": {"ok": True, "message": f"发现 {len(valid_sources)} 个直播源入口"},
        "数据标准化": {"ok": bool(all_channels), "message": f"实际频道 {len(all_channels)} 条"},
        "地址检查": {"ok": source_ok > 0, "message": f"入口成功 {source_ok}/{len(valid_sources)}"},
        "TXT 生成": {"ok": True, "message": f"{len(all_channels)} 行"},
        "发布完成": {"ok": True, "message": "仅输出 TXT 结果"},
    }
    out = {
        "status": status,
        "meta": {"source_name": "hw.json（直播源入口清单）", "source_url": SOURCE_URL, "finished_at": now, "schedule": "每 30 分钟自动执行"},
        "stats": {
            "source_entries": len(sources), "sources_valid": source_ok, "sources_failed": len(bad_sources),
            "total": len(all_channels), "valid": len(all_channels), "invalid": len(bad_sources),
            "parsed_before_dedup": parsed_total, "duplicates_removed": max(0, parsed_total - len(all_channels)), "formats": format_count,
        },
        "steps": steps,
        "logs": [f"{now} {x}" for x in logs[-100:]] or [f"{now} 无可用直播源"],
        "txt": txt,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    return 0 if all_channels else 1


if __name__ == "__main__":
    raise SystemExit(main())
