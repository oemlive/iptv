# WEB后台管理（重构版）

这是重新设计后的极简后台，不依赖 Cloudflare Worker，也不在浏览器运行时请求 Gitee 入口。

## GitHub Pages

直接将整个项目发布到 GitHub Pages 即可。

页面首次打开使用仓库内置的 `data/hw.json` 快照，因此不会因为 Gitee CORS、401 或临时网络问题导致后台无法打开。

GitHub Actions 会在每次部署时尝试更新 `data/hw.json`：
- 上游可访问：验证 `lives[]` 后更新快照。
- 上游不可访问：保留仓库里最后一次有效快照，页面仍然可用。

原始上游入口固定为：
`https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json`

## 静态模式

- 无登录、无假密码。
- 订阅列表来自内置快照。
- 选择、增加、删除、导入、导出全部保存在当前浏览器 LocalStorage。
- 浏览器不会直接请求外部入口。
- 不需要 Cloudflare Worker。

## 本机完整抓取模式

如果需要实际从已选订阅地址抓取 M3U/JSON/XML 频道，使用项目自带的 Python 服务：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

然后打开：
`http://127.0.0.1:8000/`

本机服务只负责实际抓取和解析，不需要 Cloudflare Worker。

## 文件说明

- `index.html` / `config.js`：WEB后台页面
- `data/hw.json`：内置入口快照
- `server.py`：可选的本机抓取服务
- `app/parser.py`：M3U/JSON/XML 解析器
- `.github/workflows/pages.yml`：GitHub Pages 部署及快照更新
- `requirements.txt`：本机服务必须依赖

没有 node_modules、Python 缓存、数据库、日志、测试产物或密钥。
