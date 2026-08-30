# Source Hunter Worker

用于 GitHub Pages 管理端的安全后端桥接。GitHub Token 只放在 Cloudflare Worker Secrets，不进入网页。

## 必填变量 / Secret

- `ADMIN_PASSWORD`：仅用于 `https://oemlive.github.io/iptv/` 管理端。
- `SESSION_SECRET`：随机长字符串，用于签发后台会话。
- `GITHUB_TOKEN`：Fine-grained PAT，仅授予 `oemlive/iptv` 所需的 Contents / Actions 权限。

## Variables

- `REPO_OWNER=oemlive`
- `REPO_NAME=iptv`
- `ALLOWED_ORIGIN=https://oemlive.github.io`
- `ROOT_CATALOG=https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json`

## 部署后

把 Worker URL 配置到 `admin/index.html`：

```js
window.SOURCE_HUNTER_API='https://你的-worker.workers.dev';
```

管理密码只用于 Pages 后台。它与 GitHub 账号密码完全独立。

会话使用 HttpOnly Cookie，默认 30 天；刷新页面不需要重新输入密码。

## API

- `POST /api/login`：后台密码登录，签发 30 天 HttpOnly 会话。
- `GET /api/session`：检查当前会话。
- `GET /api/discover`：直接读取 hw.json，解析 `lives[]` 为完整订阅地址列表，并保存 `output/subscriptions.json`。
- `POST /api/selection`：安全保存订阅/频道选择。
- `POST /api/pull`：触发 GitHub Actions 的 `channels` 阶段。
- `GET /api/run`：查询最新 Source Hunter Actions 状态。
- `GET /api/channels`：读取最新完整候选直播源。
