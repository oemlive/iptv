# IPTV Advanced · GitHub Actions Console

用于 `https://oemlive.github.io/iptv/` 的直播源采集、清洗、验证、评分和自动发布。

## 2.1 核心架构

```text
GitHub Pages 控制台
        │
        ├── workflow_dispatch ──→ GitHub Actions
        ├── 查询 Actions runs ──→ 运行状态
        └── 保存 config/settings.json ──→ 调度配置
                                      │
                           每 15 分钟唤醒一次
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

## 自检

```bash
python -m compileall -q app tests scripts
python -m pytest -q
```

## 部署

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
