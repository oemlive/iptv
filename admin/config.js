/* Source Hunter PRO - browser-side service configuration.
 * Set this to your deployed Worker URL, for example:
 * window.SOURCE_HUNTER_API = 'https://source-hunter-api.example.workers.dev';
 * Do NOT put a GitHub token here.
 */
// Leave empty to use the browser/local fallback. Set this to your deployed Worker URL to enable GitHub-backed management.
window.SOURCE_HUNTER_API = '';
window.SOURCE_HUNTER_ROOT_CATALOG = 'https://raw.giteeusercontent.com/oemive/iptv/raw/master/hw.json';
// 无 Worker 模式：浏览器会先直连，遇到 CORS/网络拦截时自动尝试公共只读跨域通道。
window.SOURCE_HUNTER_ENABLE_PUBLIC_FETCH_FALLBACK = true;
