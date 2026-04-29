<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import API_BASE_URL from '../config/api'

const router = useRouter()
const authStore = useAuthStore()

const code = ref('')
const submitting = ref(false)
const error = ref('')
const success = ref(false)
const checking = ref(true)

const headers = () => {
  const t = localStorage.getItem('access_token') || ''
  const h = { 'Content-Type': 'application/json' }
  if (t) h['Authorization'] = `Bearer ${t}`
  return h
}

// 已经激活就不该停在这页 —— 直接送回 /ai-lab
const checkAccess = async () => {
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/me/`, { headers: headers() })
    if (r.ok) {
      const me = await r.json()
      if (me.is_owner || me.ai_lab_enabled) {
        router.replace('/ai-lab')
        return
      }
    }
  } catch { /* silent */ }
  checking.value = false
}

const submit = async () => {
  if (!code.value.trim()) {
    error.value = '请输入邀请码'
    return
  }
  error.value = ''
  submitting.value = true
  try {
    const r = await fetch(`${API_BASE_URL}/api/ai/invites/redeem/`, {
      method: 'POST', headers: headers(),
      body: JSON.stringify({ code: code.value.trim() })
    })
    const data = await r.json()
    if (!r.ok) {
      error.value = data.error || `激活失败 (${r.status})`
      return
    }
    success.value = true
    setTimeout(() => router.replace('/ai-lab'), 800)
  } catch (e) {
    error.value = e.message || '网络错误'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  if (!authStore.isLoggedIn) {
    router.replace({ path: '/login', query: { redirect: '/ai-lab' } })
    return
  }
  checkAccess()
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4" style="background: var(--theme-50, #f8f8f6);">
    <div v-if="checking" class="text-[13px]" style="color: var(--theme-400);">正在检查访问权限…</div>

    <div v-else class="w-full max-w-md">
      <!-- Logo + 标题 -->
      <div class="flex flex-col items-center mb-8">
        <svg class="w-12 h-12 mb-3" viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round" style="color: #2c2c30;">
          <circle cx="19" cy="4" r="1.1" fill="currentColor" opacity="0.55"/>
          <circle cx="12" cy="9" r="3.4" fill="var(--ai-accent, #3d7cc9)"/>
          <path d="M5 20.5c0-3.6 3.1-6 7-6s7 2.4 7 6" stroke="currentColor" stroke-width="1.8"/>
        </svg>
        <h1 class="text-[22px] font-semibold tracking-tight" style="color: var(--theme-700);">申请使用 MyAgent</h1>
        <p class="text-[13px] mt-2 text-center max-w-xs" style="color: var(--theme-500);">
          MyAgent 是站长的私人 AI 助手项目，跑一次 agent 开销不小，所以采用邀请制。<br/>
          已经有邀请码？输入下面解锁访问。
        </p>
      </div>

      <!-- 表单 -->
      <div class="rounded-2xl px-6 py-6" style="background: #fff; border: 1px solid var(--theme-200);">
        <label class="block text-[12px] font-medium mb-2" style="color: var(--theme-500);">邀请码</label>
        <input
          v-model="code"
          type="text"
          placeholder="例如 abc-XYZ-123"
          @keyup.enter="submit"
          :disabled="submitting || success"
          class="w-full px-3 py-2 rounded-lg outline-none transition-colors"
          style="border: 1px solid var(--theme-200); background: var(--theme-50); font-size: 14px; font-family: var(--ai-font-mono, ui-monospace, monospace); color: var(--theme-700);"
        />
        <div v-if="error" class="mt-2 text-[12px]" style="color: #b91c1c;">{{ error }}</div>
        <div v-if="success" class="mt-2 text-[12px]" style="color: #15803d;">✓ 激活成功，正在跳转…</div>

        <button
          @click="submit"
          :disabled="submitting || success"
          class="mt-4 w-full px-4 py-2 rounded-lg text-[14px] font-medium transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          style="background: var(--theme-700); color: var(--theme-50);"
        >
          {{ submitting ? '验证中…' : success ? '✓ 已激活' : '激活' }}
        </button>
      </div>

      <p class="text-[12px] mt-6 text-center" style="color: var(--theme-400);">
        没有邀请码？联系站长取得后再来。
      </p>
    </div>
  </div>
</template>
