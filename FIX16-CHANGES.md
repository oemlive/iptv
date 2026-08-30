FIX16: WEB后台管理 / Worker可选 / 无Worker静态模式
- 固定内置入口：https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json
- 即使 config.js 被清空，前端仍有内置入口，不再出现未配置入口订阅地址。
- 保留同源 ./hw.json 与原 Gitee 入口。
- 不包含任何密钥。
