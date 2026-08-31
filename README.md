# WebTV Backend Manager V1

一个从零设计的 IPTV/WebTV 订阅处理后台：输入订阅源 → 服务端拉取 → 解析 → 分类/筛选 → 生成固定输出地址 → 可按每天指定时间自动更新。

## 启动
Python 3.9+：`python server.py`
Windows：双击 `start.bat`。
打开 `http://127.0.0.1:8787/`。

浏览器只访问本机服务，不直接请求远程 IPTV 地址，因此不依赖浏览器 CORS。

## 功能
- 多订阅源：M3U、TXT、JSON、XML 基础解析
- 服务端拉取、逐源结果、错误明细
- 频道搜索、分类、勾选
- 包含/排除关键词规则；规则在下一次更新时自动应用
- 多源合并与 URL 去重
- 固定输出 `output/webtv.m3u`
- 手动立即更新
- 每日指定时间自动更新
- 更新完成后自动按规则重新筛选并生成输出
- 状态、日志、最后更新时间
- 配置与数据保存在 data/，无需数据库/Node/Worker

## 设计边界
本项目不依赖 Cloudflare Worker。若部署到 VPS/NAS/电脑，直接运行 Python 服务即可。GitHub Pages 只能作为静态展示，不能承担定时抓取任务。
