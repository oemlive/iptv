# WEB后台管理 1.0

纯静态优先版本。GitHub Pages 打开后不请求 Gitee、GitHub Raw、CORS Proxy 或 Cloudflare Worker；内置订阅目录直接打包在 config.js。

## GitHub Pages
将本目录内容推送到仓库并启用 Pages。页面可直接访问，无需密码。

## 本机抓取
python -m pip install -r requirements.txt
python server.py
然后打开 http://127.0.0.1:8000/。

原始上游入口保留在 config.js：
https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json
该地址只作为上游更新来源，不参与网页启动。
