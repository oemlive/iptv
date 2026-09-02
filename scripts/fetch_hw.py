import base64
import codecs
import json
import os
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config", "sources.json")
RAW = os.path.join(ROOT, "data", "raw_hw.json")


def decode_bytes(data: bytes) -> str:
    if data.startswith(codecs.BOM_UTF8):
        data = data[len(codecs.BOM_UTF8):]
    for enc in ("utf-8", "gb18030"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def get_json(url: str, timeout: int):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "IPTV-Auto-Backend/3.1",
            "Accept": "application/json,text/plain,*/*",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = decode_bytes(resp.read())
    obj = json.loads(text)
    if isinstance(obj, dict) and obj.get("content") and obj.get("encoding") == "base64":
        payload = base64.b64decode("".join(str(obj["content"]).split()))
        obj = json.loads(decode_bytes(payload))
    if not isinstance(obj, dict) or not isinstance(obj.get("lives"), list):
        raise ValueError("hw.json 格式错误：缺少 lives 数组")
    return obj


def main():
    with open(CONFIG, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    urls = cfg.get("urls", [])
    timeout = int(cfg.get("timeout_seconds", 20))
    retries = max(1, int(cfg.get("retries", 3)))
    logs = []
    transient = (urllib.error.URLError, TimeoutError, ConnectionError)

    for index, url in enumerate(urls, 1):
        for attempt in range(1, retries + 1):
            try:
                obj = get_json(url, timeout)
                tmp = RAW + ".tmp"
                with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(obj, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                os.replace(tmp, RAW)
                logs.append(f"✓ hw.json 获取成功：入口 {index}，第 {attempt} 次")
                print(json.dumps({"ok": 1, "logs": logs, "count": len(obj["lives"])}, ensure_ascii=False))
                return 0
            except urllib.error.HTTPError as e:
                logs.append(f"× 入口 {index} 第 {attempt} 次：HTTP {e.code}")
                if e.code not in (408, 425, 429) and not (500 <= e.code <= 599):
                    break
            except transient as e:
                logs.append(f"× 入口 {index} 第 {attempt} 次：{type(e).__name__}: {e}")
            except (json.JSONDecodeError, ValueError, UnicodeError) as e:
                logs.append(f"× 入口 {index} 第 {attempt} 次：数据错误：{e}")
                break
            except Exception as e:
                logs.append(f"× 入口 {index} 第 {attempt} 次：{type(e).__name__}: {e}")
                break
            if attempt < retries:
                time.sleep(min(attempt * 2, 5))

    print(json.dumps({"ok": 0, "logs": logs}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
