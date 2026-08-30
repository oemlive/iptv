# Source Hunter PRO API bridge

Cloudflare Worker only. It is **not** a GitHub login service.

The admin password is used only for `https://oemlive.github.io/iptv/` and is stored as the Worker secret `ADMIN_PASSWORD`. GitHub authentication remains separate: `GITHUB_TOKEN` is a Worker-only secret and is never sent to the browser.

Required Worker secrets:
- `ADMIN_PASSWORD`
- `SESSION_SECRET`
- `GITHUB_TOKEN` (fine-grained token limited to `oemlive/iptv`)

Variables in `wrangler.toml` fix the repository to `oemlive/iptv` and the browser origin to `https://oemlive.github.io`.

After deployment, set the Worker URL as `API_BASE` in `admin/index.html`. The browser then uses the Worker for authentication, GitHub-backed selection persistence, Actions dispatch, and remote channel data. Without it, the page remains usable in local-browser mode.
