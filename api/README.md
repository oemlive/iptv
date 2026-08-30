# Source Hunter PRO API Worker

This Worker is the server-side bridge for the GitHub Pages admin. It keeps the GitHub token in a Cloudflare Worker secret and never sends it to the browser.

## Required secrets

- `ADMIN_PASSWORD` — password used only by `https://oemlive.github.io/iptv/`
- `SESSION_SECRET` — long random secret used to sign the HttpOnly session cookie
- `GITHUB_TOKEN` — fine-grained PAT for the `oemlive/iptv` repository; never place this in `admin/config.js`

## Deploy

1. Install Wrangler and authenticate with Cloudflare.
2. From this directory run `wrangler deploy`.
3. Set the three secrets with `wrangler secret put ...`.
4. Put the deployed Worker URL into `admin/config.js` as `window.SOURCE_HUNTER_API`.
5. Publish `admin/` with the GitHub Pages workflow.

The Worker only accepts requests whose Origin matches `ALLOWED_ORIGIN`.
