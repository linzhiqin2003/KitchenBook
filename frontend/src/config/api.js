// API 基础地址配置
// 生产环境使用相对路径（Nginx 会代理 /api 到后端）
// 开发环境使用本地开发服务器地址
const API_BASE_URL = import.meta.env.PROD 
  ? '' // 生产环境：相对路径
  : 'http://127.0.0.1:8000'; // 开发环境：本地后端地址

export default API_BASE_URL;

