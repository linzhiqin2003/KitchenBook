import { defineStore } from "pinia";
import { computed, ref } from "vue";
import api from "../api/client";

export interface UserProfile {
  id: number;
  email: string;
  nickname: string;
  avatar_url: string;
  avatar_display: string;
}

export interface OrgInfo {
  id: string;
  name: string;
  member_count: number;
}

export const useAuthStore = defineStore("auth", () => {
  const accessToken = ref(localStorage.getItem("access_token") || "");
  const refreshToken = ref(localStorage.getItem("refresh_token") || "");
  const user = ref<UserProfile | null>(null);
  const activeOrgId = ref(localStorage.getItem("active_org_id") || "");
  const initialized = ref(false);

  const isLoggedIn = computed(() => !!accessToken.value);
  const isOrgMode = computed(() => !!activeOrgId.value);
  const displayName = computed(() => user.value?.nickname || user.value?.email || "");

  function setTokens(access: string, refresh: string) {
    accessToken.value = access;
    refreshToken.value = refresh;
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  }

  function clearTokens() {
    accessToken.value = "";
    refreshToken.value = "";
    user.value = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  async function login(email: string, password: string) {
    const { data } = await api.post("/auth/login/", { username: email, password });
    setTokens(data.access, data.refresh);
    await fetchProfile();
  }

  async function register(email: string, password: string, nickname: string) {
    await api.post("/auth/register/", { email, password, nickname });
  }

  function logout() {
    clearTokens();
    activeOrgId.value = "";
    localStorage.removeItem("active_org_id");
  }

  async function fetchProfile() {
    const { data } = await api.get("/auth/me/");
    user.value = data;
  }

  function switchOrg(orgId: string) {
    activeOrgId.value = orgId;
    if (orgId) {
      localStorage.setItem("active_org_id", orgId);
    } else {
      localStorage.removeItem("active_org_id");
    }
  }

  async function init() {
    initialized.value = false;
    try {
      if (!accessToken.value) return;
      await fetchProfile();
    } catch {
      clearTokens();
    } finally {
      initialized.value = true;
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    activeOrgId,
    initialized,
    isLoggedIn,
    isOrgMode,
    displayName,
    login,
    register,
    logout,
    fetchProfile,
    switchOrg,
    init,
    setTokens,
    clearTokens,
  };
});
