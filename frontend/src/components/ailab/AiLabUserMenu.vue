<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth'
import API_BASE_URL from '../../config/api'

const router = useRouter()
const authStore = useAuthStore()

const open = ref(false)
const me = ref(null)
const wrapperRef = ref(null)

const headers = () => {
  const t = localStorage.getItem('access_token') || ''
  const h = { 'Content-Type': 'application/json' }
  if (t) h['Authorization'] = `Bearer ${t}`
  return h
}

const fetchMe = async () => {
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/me/`, { headers: headers() })
    if (r.ok) me.value = await r.json()
  } catch { /* silent */ }
}

const initials = computed(() => {
  const name = me.value?.nickname || me.value?.username || me.value?.email || '?'
  // 中文取第一个字、英文取首字母
  const ch = name.trim().charAt(0)
  return ch.toUpperCase()
})

const displayName = computed(() => me.value?.nickname || me.value?.email || me.value?.username || '')

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const goInvites = () => {
  open.value = false
  router.push('/ai-lab/admin/invites')
}

const handleOutsideClick = (e) => {
  if (!wrapperRef.value) return
  if (!wrapperRef.value.contains(e.target)) open.value = false
}

defineExpose({ refresh: fetchMe, me })

onMounted(() => {
  fetchMe()
  document.addEventListener('click', handleOutsideClick)
})
onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<template>
  <div ref="wrapperRef" class="relative inline-block">
    <button
      @click.stop="open = !open"
      class="w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer relative overflow-hidden"
      :style="open
        ? 'background: var(--theme-200); color: var(--theme-700);'
        : 'background: var(--theme-100); color: var(--theme-600);'"
      :title="displayName"
    >
      <img v-if="me?.avatar_url" :src="me.avatar_url" class="w-full h-full object-cover" />
      <span v-else class="text-[12px] font-semibold tracking-tight">{{ initials }}</span>
      <span
        v-if="me?.is_owner"
        class="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full"
        style="background: var(--ai-accent, #3d7cc9); border: 1.5px solid var(--theme-50);"
        title="Owner"
      ></span>
    </button>

    <Transition name="panel">
      <div
        v-if="open"
        class="absolute right-0 top-full mt-1.5 w-[260px] rounded-xl shadow-lg overflow-hidden z-50"
        style="background: var(--theme-50); border: 1px solid var(--theme-200);"
        @click.stop
      >
        <!-- 身份头部 -->
        <div class="px-4 pt-3 pb-2.5" style="border-bottom: 1px solid var(--theme-100);">
          <div class="flex items-center gap-2.5">
            <div
              class="w-9 h-9 rounded-full flex items-center justify-center overflow-hidden shrink-0"
              style="background: var(--theme-100);"
            >
              <img v-if="me?.avatar_url" :src="me.avatar_url" class="w-full h-full object-cover" />
              <span v-else class="text-[14px] font-semibold" style="color: var(--theme-600);">{{ initials }}</span>
            </div>
            <div class="min-w-0">
              <div class="text-[14px] font-semibold truncate" style="color: var(--theme-700);">
                {{ displayName }}
              </div>
              <div class="flex items-center gap-1.5 mt-0.5">
                <span
                  v-if="me?.is_owner"
                  class="text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide"
                  style="background: var(--ai-accent, #3d7cc9); color: #fff;"
                >Owner</span>
                <span
                  v-else-if="me?.ai_lab_enabled"
                  class="text-[10px] font-medium px-1.5 py-0.5 rounded"
                  style="background: var(--theme-100); color: var(--theme-500);"
                >已开通</span>
                <span
                  v-else
                  class="text-[10px] font-medium px-1.5 py-0.5 rounded"
                  style="background: #fff4e0; color: #b45309;"
                >未开通</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 菜单项 -->
        <div class="py-1">
          <button
            v-if="me?.is_owner"
            @click="goInvites"
            class="w-full px-4 py-2 flex items-center gap-2 text-left text-[13px] cursor-pointer transition-colors hover:bg-[var(--theme-100)]"
            style="color: var(--theme-600);"
          >
            <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/>
            </svg>
            邀请码管理
          </button>
          <button
            @click="handleLogout"
            class="w-full px-4 py-2 flex items-center gap-2 text-left text-[13px] cursor-pointer transition-colors hover:bg-[var(--theme-100)]"
            style="color: var(--theme-600);"
          >
            <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9"/>
            </svg>
            退出登录
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.panel-enter-active, .panel-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; transform: translateY(-4px); }
.panel-enter-to, .panel-leave-from { opacity: 1; transform: translateY(0); }
</style>
