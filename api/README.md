# Source Hunter PRO API Worker

This Worker is the server-side bridge for the GitHub Pages admin. It keeps the GitHub token in a Cloudflare Worker secret and never sends it to the browser.

## Required Worker secrets

- `ADMIN_PASSWORD`
- `SESSION_SECRET`
- `GITHUB_TOKEN`

## GitHub Actions deployment (optional)

The repository includes `.github/workflows/deploy-worker.yml`. Add these GitHub Actions secrets before enabling automatic Worker deployment:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

Then run the workflow manually or push a change under `api/`.

## Pages configuration

After the Worker is deployed, copy its `*.workers.dev` URL into `admin/config.js`:

```js
window.SOURCE_HUNTER_API = 'https://source-hunter-api.<your-subdomain>.workers.dev';
```

The repaired admin also works without a Worker for the **获取全部订阅** operation: when `SOURCE_HUNTER_API` is empty it directly reads `SOURCE_HUNTER_ROOT_CATALOG` in browser/local mode. GitHub-backed selection, Actions dispatch, and generated-channel retrieval still require the Worker.

Never put `GITHUB_TOKEN` in `admin/config.js`.


FIX13: 本地模式退出后不再自动重新进入；公开目录直连失败时可选尝试只读跨域备用通道。
