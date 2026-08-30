/* Source Hunter PRO - browser-side service configuration.
 * Set this to your deployed Worker URL, for example:
 * window.SOURCE_HUNTER_API = 'https://source-hunter-api.example.workers.dev';
 * Do NOT put a GitHub token here.
 */
// Leave empty to use the browser/local fallback. Set this to your deployed Worker URL to enable GitHub-backed management.
window.SOURCE_HUNTER_API = '';
window.SOURCE_HUNTER_ROOT_CATALOG = 'https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json';
// 无 Worker 模式：优先读取 GitHub Pages 同源的构建缓存 hw.json。
// 构建缓存由 .github/workflows/pages.yml 在部署时从下面的官方内置入口抓取，
// 因此浏览器不再直接请求 Gitee，避免 CORS/401 导致 Failed to fetch。
window.SOURCE_HUNTER_ENABLE_PUBLIC_FETCH_FALLBACK = true;
window.SOURCE_HUNTER_ROOT_CATALOG_FALLBACKS = [
  './hw.json',
  'https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json'
];

// 无 Worker 本地模式密码：仅用于前端入口门禁，不是安全认证。默认密码为 admin；可自行替换 SHA-256。
window.SOURCE_HUNTER_LOCAL_PASSWORD_HASH = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918';
