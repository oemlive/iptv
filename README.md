# IPTV Auto Backend V2

后台自动运行版。网页只展示状态，不要求 GitHub PAT。

## 自动流程

每 30 分钟由 GitHub Actions 执行：获取 hw.json → 重试/备用源 → JSON 解析 → 标准化 → 基础 URL 检查 → 生成 latest.json → 提交结果。

## 部署

1. 将本目录上传到 GitHub 仓库。
2. 开启 GitHub Pages，选择从仓库/Actions 部署静态页面。
3. Actions 中首次手动 Run workflow。
4. 后续每 30 分钟自动执行。

网页可关闭，不影响后台任务。
