<template>
  <div v-if="!appReady" class="app-loading">
    <div class="app-loading__spinner"></div>
  </div>
  <template v-else-if="route.meta.public">
    <router-view :key="$route.fullPath" />
  </template>
  <template v-else>
    <div class="app-shell" :class="{ 'sidebar-collapsed': collapsed }">
      <Sidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />
      <main class="main-content">
        <Topbar />
        <router-view :key="$route.fullPath" />
      </main>
    </div>
  </template>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import Sidebar from "./components/Sidebar.vue";
import Topbar from "./components/Topbar.vue";
import { useAuthStore } from "./stores/auth";

const route = useRoute();
const collapsed = ref(false);
const authStore = useAuthStore();
const appReady = ref(false);

onMounted(async () => {
  await authStore.init();
  appReady.value = true;
});
</script>

<style scoped>
.app-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
}

.app-loading__spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top-color: rgba(59, 130, 246, 0.8);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
