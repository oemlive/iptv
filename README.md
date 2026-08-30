# WEB后台管理 · Worker 可选 · 无 Worker 静态模式

## 默认运行方式

直接部署到 GitHub Pages：

`https://oemlive.github.io/iptv/`

默认不依赖 Cloudflare Worker。入口目录已经随源码内置为 `hw.json`，Pages 发布时使用同源文件：

`https://oemlive.github.io/iptv/hw.json`

原始上游入口保持不变：

`https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json`

GitHub Actions 会定期尝试刷新仓库内的 `hw.json`；上游暂时不可用时继续使用最后一次有效缓存，不会因此把 Pages 部署搞成 404。

## 无 Worker 模式

- 登录页面名称：**WEB后台管理**
- 默认本地门禁密码：`admin`
- 可在 `admin/config.js` 修改 `SOURCE_HUNTER_LOCAL_PASSWORD_HASH`。
- 这是浏览器端门禁，不是安全的服务器认证；真正的管理认证请启用 Worker。
- 订阅目录优先读取同源 `./hw.json`，不再依赖浏览器直接访问 Gitee。
- 可以保存本机订阅/频道选择并生成 M3U/TXT。
- 某些二级订阅本身禁止 CORS 时，浏览器无法直接拉取，这是浏览器限制；启用 Worker 后可由后端代取。

## Worker 模式

在 `admin/config.js` 设置：

```js
window.SOURCE_HUNTER_API = 'https://你的-worker.workers.dev';
```

再按 `api/README.md` 配置 Worker Secrets。

## 退出行为

退出会清除本地会话并返回登录页，不刷新页面，也不会自动重新进入。

## FIX18
- 无 Worker 静态模式不再要求或保存任何前端密码；打开页面即可进入后台。
- 配置 Worker 后才启用真正的服务端管理员登录。
- 继续使用 Pages 同源 `hw.json`，Gitee 仅作为上游入口。
