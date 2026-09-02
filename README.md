# IPTV Auto Backend V3 PURE FIXED

## 工作方式

`hw.json` **不是最终直播源列表**，而是“直播源入口清单”。

后台每次运行按以下流程处理：

1. 从 `https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json` 拉取入口信息。
2. 读取 `lives[]` 中每一个 `url`。
3. 并发拉取这些入口实际返回的 TXT / M3U / JSON 内容。
4. 解析成真正的 `频道名称,播放地址`。
5. 自动去重、过滤无效格式。
6. 最终网页底部和下载功能 **只输出 TXT**，不会把 `hw.json` 的入口地址直接当成频道地址输出。

## TXT 格式

```text
CCTV1,http://example.com/live/cctv1.m3u8
CCTV2,http://example.com/live/cctv2.m3u8
```

## 自动运行

GitHub Actions 每 30 分钟执行一次，也支持手动运行；不需要 GitHub PAT。

## 兼容性修复

- 不再使用会触发环境异常的 `utf8-sig` codec 名称。
- 手动处理 UTF-8 BOM。
- UTF-8 / GB18030 兼容。
- Gitee API Base64 内容兼容。
- HTTP/网络错误分类处理。
- 只对临时网络错误进行重试。
- 原子写入状态文件。
- 并发抓取直播源入口，避免几十个入口串行等待导致 Actions 超时。
- 自动解析 M3U、TXT、常见 JSON 结构。
- 去除重复频道。
- 清理 Python 缓存文件。
