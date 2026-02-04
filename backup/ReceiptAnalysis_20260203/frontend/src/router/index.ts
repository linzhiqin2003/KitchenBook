import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "../views/DashboardView.vue";
import UploadView from "../views/UploadView.vue";
import ReceiptsView from "../views/ReceiptsView.vue";
import ReceiptDetailView from "../views/ReceiptDetailView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import InviteAcceptView from "../views/InviteAcceptView.vue";
import OrgSettingsView from "../views/OrgSettingsView.vue";
import { useAuthStore } from "../stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "dashboard", component: DashboardView },
    { path: "/upload", name: "upload", component: UploadView },
    { path: "/receipts", name: "receipts", component: ReceiptsView },
    { path: "/receipts/:id", name: "receipt-detail", component: ReceiptDetailView },
    { path: "/login", name: "login", component: LoginView, meta: { public: true } },
    { path: "/register", name: "register", component: RegisterView, meta: { public: true } },
    { path: "/invite/:id", name: "invite-accept", component: InviteAcceptView, meta: { public: true } },
    { path: "/org-settings", name: "org-settings", component: OrgSettingsView },
  ]
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  // Wait for auth initialization to complete
  if (!authStore.initialized) {
    await new Promise<void>((resolve) => {
      const stop = authStore.$subscribe(() => {
        if (authStore.initialized) {
          stop();
          resolve();
        }
      });
      // In case it was already set between the check and subscribe
      if (authStore.initialized) {
        stop();
        resolve();
      }
    });
  }

  if (!to.meta.public && !authStore.isLoggedIn) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if ((to.name === "login" || to.name === "register") && authStore.isLoggedIn) {
    return { name: "dashboard" };
  }
});

export default router;
