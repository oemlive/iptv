# 2.1 全面自检报告

## 通过项目

- Python `compileall`: PASS
- Pytest: PASS (8 tests)
- JavaScript `node --check`: PASS
- GitHub Actions YAML 解析: PASS
- `config/settings.json` JSON 解析: PASS
- GitHub Actions 控制台 API 路由检查: PASS
- Token 示例/源码扫描: PASS（无硬编码 PAT）
- 运行时产物清理: PASS（无 `.pyc` / `.db` / `.pytest_cache`）

## 本版修复

1. Pages 控制台增加真实 GitHub Actions `workflow_dispatch`。
2. 使用 workflow-scoped Actions Runs API，避免读到其他 workflow 的任务。
3. 增加任务取消与失败步骤重跑。
4. 增加运行状态轮询。
5. PAT 只存当前页面内存，不进入 localStorage、URL、源码或仓库。
6. 调度配置写入 `config/settings.json`，Actions 每 15 分钟唤醒后按时区和 HH:MM 判断是否执行。
7. 手动运行绕过调度时间。
8. 调度配置提交不会触发爬虫 push-loop；爬虫只在 schedule / workflow_dispatch 运行。
9. 输出增加每频道最大源数限制。
10. 增加调度单元测试和输出限额测试。
11. 清理所有 Python 编译缓存与测试缓存。

## 已知设计边界

- GitHub Pages 是静态站点，因此“真正执行”发生在 GitHub Actions，而不是浏览器。
- 浏览器要操作私有 GitHub API，必须由用户主动输入具有最小权限的 Fine-grained PAT；源码不提供任何默认 Token。
- GitHub scheduled workflow 可能存在平台调度延迟；15 分钟唤醒机制用于支持任意配置时间，而不是承诺精确到秒。
- 直播源稳定性检测只有在 `stability_seconds > 0` 时启用；这会增加运行时间和资源消耗。
