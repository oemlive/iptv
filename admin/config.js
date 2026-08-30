/* Source Hunter PRO - browser-side service configuration.
 * Set this to your deployed Worker URL, for example:
 * window.SOURCE_HUNTER_API = 'https://source-hunter-api.example.workers.dev';
 * Do NOT put a GitHub token here.
 */
// Leave empty to use the browser/local fallback. Set this to your deployed Worker URL to enable GitHub-backed management.
window.SOURCE_HUNTER_API = '';
window.SOURCE_HUNTER_ROOT_CATALOG = '';
// 无 Worker 模式：优先读取 GitHub Pages 同源的构建缓存 hw.json。
// 构建缓存由 .github/workflows/pages.yml 在部署时从下面的官方内置入口抓取，
// 因此浏览器不再直接请求 Gitee，避免 CORS/401 导致 Failed to fetch。
window.SOURCE_HUNTER_ENABLE_PUBLIC_FETCH_FALLBACK = true;
window.SOURCE_HUNTER_ROOT_CATALOG_FALLBACKS = [
  './hw.json',
  'https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json'
];
