// API 基础地址配置
// 生产环境使用相对路径（Nginx 会代理 /api 到后端）
// 开发环境使用本地开发服务器地址
const API_BASE_URL = import.meta.env.PROD
  ? '' // 生产环境：相对路径
  : 'http://127.0.0.1:8000'; // 开发环境：本地后端地址

export default API_BASE_URL;

// Hermes Agent API — 动态获取，基于当前用户
// 生产环境：前端从 /api/ai/me/ 获取 hermes_path（如 /hermes/u1），
//           Nginx 按路径路由到对应用户的 Docker 容器
// 开发环境：直接连本地单实例 Hermes

let _hermesPath = null;

export function setHermesPath(path) {
  _hermesPath = path;
}

export function getHermesApiUrl() {
  if (_hermesPath) return _hermesPath;
  if (!import.meta.env.PROD) return 'http://127.0.0.1:8642';
  return '/hermes'; // 生产环境兜底（未获取到 hermes_path 时）
}

export const HERMES_API_KEY = 'ailab-hermes-2026';
