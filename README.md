# IPTV Advanced · GitHub Actions Console

用于 `https://oemlive.github.io/iptv/` 的直播源采集、清洗、验证、评分和自动发布。

## 2.3 核心架构

```text
GitHub Pages 控制台
        │
        ├── workflow_dispatch ──→ GitHub Actions
        ├── 查询 Actions runs ──→ 运行状态
        └── 保存 config/settings.json ──→ 调度配置
                                      │
                           每 5 分钟唤醒一次
                                      │
                    爬取 → 解析 → 验证 → 评分 → 输出
                                      │
                              Pages 自动发布
```

前端不会内置 Token。手动连接时 Token 只存于当前 JS 内存，刷新页面即清除。

## 功能

- GitHub / Gitee 公开源发现
- TXT / M3U / M3U8 / JSON 解析
- HTTP/HLS/ffprobe 视频与音频检测
- 分辨率、延迟、评分
- 去重与分类输出
- GitHub Actions 手动 `workflow_dispatch`
- GitHub Actions 实时任务状态查询
- 运行任务取消
- 网页配置验证并发、稳定检测时间
- 网页保存自动调度配置到仓库
- 任务取消与失败步骤重跑
- 网页修改自动调度时间、时区、启用状态
- 每 15 分钟调度唤醒，由 `config/settings.json` 决定是否真正执行
- 自动生成 TXT / M3U / JSON
- Pages 静态发布

## GitHub PAT 权限

推荐 Fine-grained PAT，仅授权目标仓库：

- Actions: Read and write
- Contents: Read and write（仅当需要网页保存调度配置时）

Token 不要写进源码、workflow、URL、localStorage 或提交记录。

## 2.3 关键稳定性修复

- Pages artifact 同时发布 `web/`、`data/`、`output/`、`config/`，保证网页能读取调度配置。
- 调度检查改为每 5 分钟一次，配置时间必须使用 5 分钟粒度，避免原来 `02:17` 这类时间永远无法命中的问题。
- Actions 失败时也会尝试提交 `data/status.json`，避免失败状态只存在 Runner。
- 网页连接 GitHub 时同时验证仓库和指定 Workflow 是否存在且处于 active。
- 手动运行前检测已有 queued/in_progress 任务，减少重复触发。
- 运行状态增加当前 Job/Step 展示。
- 调度配置保存增加时间、星期、5 分钟粒度校验。
- 修复旧版 `repository.py` 对不存在的 `settings.output_repo_url` 的运行时引用。

## 自检

```bash
python -m compileall -q app tests scripts
python -m pytest -q
```

## 部署

> **重要：压缩包解压后，必须把本目录内的文件直接放到目标仓库根目录。不要把 `advanced_live_source_v2` 这个目录再套一层。仓库根目录必须直接看到 `.github/`、`web/`、`config/`、`data/`。**


1. 将源码放入目标仓库。
2. Pages 使用 GitHub Actions 发布。
3. 首次在 Actions 手动运行一次，确认权限。
4. 打开 Pages → GitHub 设置 → 输入仓库信息和 PAT。
5. 使用“立即运行”验证 `workflow_dispatch`。
6. 在“自动调度”设置时区和时间。

### 关于调度

GitHub Actions 每 15 分钟触发一次检查。真正执行时间由 `config/settings.json` 的 `schedule` 控制，避免为了支持任意指定时间而频繁修改 workflow。GitHub scheduled workflow 可能受到平台负载影响，因此实际开始时间可能有少量延迟。

## 输出

```text
output/live.txt
output/live.m3u
output/cctv.*
output/hk_tw.*
output/other.*
output/movie.*
output/kids.*
output/sports.*
output/foreign.*
output/4k.*
data/status.json
data/run-summary.json
```

## GitHub Pages 部署路径

本项目面向仓库 `oemlive/iptv` 的 Project Pages 地址 `https://oemlive.github.io/iptv/`。
Pages artifact 的根目录必须直接包含 `index.html`；不能把站点再次放入 `_site/iptv/`，否则最终地址会变成 `/iptv/iptv/`，访问 `/iptv/` 会出现 404。
