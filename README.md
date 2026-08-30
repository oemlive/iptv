# WEB后台管理 · Worker 可选

本版采用双模式设计：

- **无 Worker 静态模式（默认）**：GitHub Pages 直接运行。无需 Cloudflare、无需后端。可读取公开入口订阅、读取浏览器允许跨域访问的订阅、频道筛选、本地保存选择、生成 M3U/TXT。
- **Worker 管理模式（可选）**：在 `admin/config.js` 设置 `window.SOURCE_HUNTER_API` 后启用。用于 GitHub-backed 登录、选择保存、Actions 拉取和仓库管理。

## GitHub Pages

保持现有 Pages 地址即可：

`https://oemlive.github.io/iptv/`

## 无 Worker 模式

默认 `admin/config.js`：

```js
window.SOURCE_HUNTER_API = '';
```

此时页面不会要求登录，直接进入 **WEB后台管理**。

注意：浏览器直接读取外部订阅时，目标服务器必须允许 CORS。若某个订阅不允许浏览器跨域访问，该订阅会被跳过并在页面提示；这不是前端代码能够绕过的限制。

## Worker 模式

将 `admin/config.js` 改为：

```js
window.SOURCE_HUNTER_API = 'https://你的-worker.workers.dev';
```

然后部署 `api/worker.js`。GitHub Token、管理员密码、Session Secret 仍必须作为 Worker Secrets 配置，不能写进前端。
