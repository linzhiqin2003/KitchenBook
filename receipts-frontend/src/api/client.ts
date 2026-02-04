import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || `${import.meta.env.BASE_URL}api`;
const APP_BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
const LOGIN_PATH = `${APP_BASE}/login`;

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000
});

// Request interceptor: inject Authorization + X-Active-Org
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const orgId = localStorage.getItem("active_org_id");
  if (orgId) {
    config.headers["X-Active-Org"] = orgId;
  }
  return config;
});

// Response interceptor: auto refresh on 401
let isRefreshing = false;
let refreshQueue: Array<{ resolve: (token: string) => void; reject: (err: any) => void }> = [];

function processQueue(error: any, token: string | null) {
  refreshQueue.forEach((p) => {
    if (error) {
      p.reject(error);
    } else {
      p.resolve(token!);
    }
  });
  refreshQueue = [];
}

async function getAuthStore() {
  const { useAuthStore } = await import("../stores/auth");
  return useAuthStore();
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Skip refresh for auth endpoints
    if (
      !error.response ||
      error.response.status !== 401 ||
      originalRequest._retry ||
      originalRequest.url?.includes("/auth/login") ||
      originalRequest.url?.includes("/auth/token/refresh") ||
      originalRequest.url?.includes("/auth/register")
    ) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({
          resolve: (token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          },
          reject,
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) {
      isRefreshing = false;
      try { (await getAuthStore()).clearTokens(); } catch { /* store not ready */ }
      window.location.href = LOGIN_PATH;
      return Promise.reject(error);
    }

    try {
      const { data } = await axios.post(
        `${api.defaults.baseURL}/auth/token/refresh/`,
        { refresh: refreshToken }
      );
      const newAccess = data.access;
      const newRefresh = data.refresh || refreshToken;
      localStorage.setItem("access_token", newAccess);
      localStorage.setItem("refresh_token", newRefresh);
      try { (await getAuthStore()).setTokens(newAccess, newRefresh); } catch { /* store not ready */ }
      originalRequest.headers.Authorization = `Bearer ${newAccess}`;
      processQueue(null, newAccess);
      return api(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      try { (await getAuthStore()).clearTokens(); } catch { /* store not ready */ }
      window.location.href = LOGIN_PATH;
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default api;
