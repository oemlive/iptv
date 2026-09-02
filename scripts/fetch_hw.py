import base64
import codecs
import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config", "sources.json")
RAW_PATH = os.path.join(ROOT, "data", "raw_hw.json")


def load_json(path):
    with open(path, "rb") as f:
        data = f.read()
    return json.loads(decode_bytes(data))


def decode_bytes(data):
    if data.startswith(codecs.BOM_UTF8):
        data = data[len(codecs.BOM_UTF8):]
    for encoding in ("utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise UnicodeDecodeError("utf-8", data, 0, min(1, len(data)), "unsupported response encoding")


def response_json(resp):
    data = resp.read()
    text = decode_bytes(data).lstrip("\ufeff")
    return json.loads(text)


def decode_payload(value):
    if not isinstance(value, dict) or value.get("encoding") != "base64" or not value.get("content"):
        return value
    decoded = base64.b64decode(value["content"], validate=False)
    return json.loads(decode_bytes(decoded))


def get(url, timeout):
    req = Request(url, headers={
        "User-Agent": "IPTV-Auto-Backend/3.1",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
    })
    with urlopen(req, timeout=timeout) as resp:
        return decode_payload(response_json(resp))


def is_valid_payload(value):
    return isinstance(value, dict) and isinstance(value.get("lives"), list)


def main():
    config = load_json(CONFIG_PATH)
    urls = config.get("urls", [])
    timeout = int(config.get("timeout_seconds", 20))
    retries = max(1, int(config.get("retries", 3)))
    logs = []

    if not urls:
        print(json.dumps({"ok": 0, "logs": ["配置错误：urls 为空"]}, ensure_ascii=False))
        return 1

    for index, url in enumerate(urls, 1):
        for attempt in range(1, retries + 1):
            try:
                payload = get(url, timeout)
                if not is_valid_payload(payload):
                    raise ValueError("返回数据不是有效的 hw.json（缺少 lives 数组）")
                os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
                tmp = RAW_PATH + ".tmp"
                with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                os.replace(tmp, RAW_PATH)
                logs.append(f"✓ 源 {index} 获取成功，第 {attempt} 次")
                print(json.dumps({"ok": 1, "logs": logs}, ensure_ascii=False))
                return 0
            except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError, UnicodeError) as exc:
                logs.append(f"× 源 {index} 第 {attempt} 次失败：{type(exc).__name__}: {exc}")
                if attempt < retries:
                    time.sleep(min(attempt * 2, 5))
            except Exception as exc:
                logs.append(f"× 源 {index} 第 {attempt} 次失败：{type(exc).__name__}: {exc}")
                if attempt < retries:
                    time.sleep(min(attempt * 2, 5))

    print(json.dumps({"ok": 0, "logs": logs}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
