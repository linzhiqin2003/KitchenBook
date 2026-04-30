<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import AiLabTokenUsage from './AiLabTokenUsage.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  isLoading: { type: Boolean, default: false },
  isRecording: { type: Boolean, default: false },
  isTranscribing: { type: Boolean, default: false },
  isOcrProcessing: { type: Boolean, default: false },
  recordingDuration: { type: Number, default: 0 },
  hasImage: { type: Boolean, default: false },
  fileAttachment: { type: Object, default: null },
  floating: { type: Boolean, default: true },
  selectedModel: { type: String, default: '' },
  modelOptions: { type: Array, default: () => [] },
  sessionTokens: {
    type: Object,
    default: () => ({
      promptTokens: 0,
      completionTokens: 0,
      totalPromptTokens: 0,
      totalCompletionTokens: 0,
      turnCount: 0,
    }),
  },
  contextLimit: { type: Number, default: 1_000_000 },
  showScrollBottom: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:modelValue', 'update:selectedModel', 'send', 'stop', 'image-click', 'voice-click', 'paste', 'remove-file', 'scroll-bottom'
])

const localValue = ref(props.modelValue)
const textareaRef = ref(null)
const modelMenuRef = ref(null)
const isModelMenuOpen = ref(false)

// 输入框最大高度 — 单行 24px 行高 × ~9 行 ≈ 220px。超出后内部滚动。
const TEXTAREA_MAX_HEIGHT = 220

const autoResize = () => {
  const el = textareaRef.value
  if (!el) return
  // 先 reset 到 auto 让 scrollHeight 反映"自然"高度，再 clamp 到上限
  el.style.height = 'auto'
  const next = Math.min(el.scrollHeight, TEXTAREA_MAX_HEIGHT)
  el.style.height = `${next}px`
  el.style.overflowY = el.scrollHeight > TEXTAREA_MAX_HEIGHT ? 'auto' : 'hidden'
}

watch(() => props.modelValue, (val) => {
  localValue.value = val
  // 外部清空（发送后）后高度也要回缩
  nextTick(autoResize)
})
watch(localValue, (val) => {
  emit('update:modelValue', val)
  nextTick(autoResize)
})

onMounted(() => { autoResize() })

const handleModelMenuOutsideClick = (event) => {
  if (!modelMenuRef.value?.contains(event.target)) {
    isModelMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleModelMenuOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleModelMenuOutsideClick)
})

const composing = ref(false)
const onCompositionStart = () => { composing.value = true }
const onCompositionEnd = () => {
  requestAnimationFrame(() => { composing.value = false })
}

const handleKeydown = (e) => {
  if (composing.value || e.isComposing || e.keyCode === 229) return
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    emit('send')
    return
  }
  // Shift+Enter / 普通输入：让 textarea 立刻按当前内容撑高
  if (e.key === 'Enter' && e.shiftKey) {
    nextTick(autoResize)
  }
}

const handlePaste = (e) => { emit('paste', e) }

const hasAttachment = computed(() => !!props.fileAttachment)

const fileSizeLabel = computed(() => {
  const size = props.fileAttachment?.size || 0
  if (!size) return ''
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  return `${Math.max(1, Math.round(size / 1024))} KB`
})

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const shouldShowModelSwitcher = computed(() => props.modelOptions.length > 1)
const selectedModelOption = computed(() => (
  props.modelOptions.find(option => option.value === props.selectedModel) || props.modelOptions[0] || null
))

const toggleModelMenu = () => {
  if (!shouldShowModelSwitcher.value) return
  isModelMenuOpen.value = !isModelMenuOpen.value
}

const selectModel = (value) => {
  emit('update:selectedModel', value)
  isModelMenuOpen.value = false
}
</script>

<template>
  <div
    :class="floating ? 'absolute bottom-0 left-0 right-0 pt-4 pb-3 px-4' : 'relative w-full'"
    :style="floating ? 'background: linear-gradient(to top, var(--theme-50) 70%, transparent); font-family: var(--ai-font-body);' : 'font-family: var(--ai-font-body);'"
  >
    <div class="max-w-4xl mx-auto relative">
      <Transition name="fade-up">
        <div v-if="floating && showScrollBottom" class="scroll-bottom-wrap">
          <button
            @click="emit('scroll-bottom')"
            class="scroll-bottom-btn cursor-pointer flex items-center gap-1"
            title="回到底部"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
            </svg>
            回到底部
          </button>
        </div>
      </Transition>

      <div class="input-shell transition-all">
        <div v-if="hasAttachment" class="attachment-row">
          <div
            class="attachment-card"
            :class="{ 'is-pdf': fileAttachment.type !== 'image' }"
            :title="fileAttachment.name + (fileSizeLabel ? ' · ' + fileSizeLabel : '')"
          >
            <!-- 图片：直接铺满 -->
            <img
              v-if="fileAttachment.type === 'image' && fileAttachment.preview"
              :src="fileAttachment.preview"
              class="attachment-card__img"
              alt=""
            />
            <!-- PDF：页面 + 角标 -->
            <template v-else>
              <div class="attachment-card__pdf-page">
                <svg class="attachment-card__pdf-glyph" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
                </svg>
                <div class="attachment-card__pdf-name">{{ fileAttachment.name }}</div>
              </div>
              <span class="attachment-card__pdf-badge">PDF</span>
            </template>
            <!-- hover 关闭按钮 -->
            <button
              @click="emit('remove-file')"
              :disabled="isLoading || isOcrProcessing"
              class="attachment-card__remove"
              title="移除文件"
            >
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
            <!-- OCR 处理时的 loading 遮罩 -->
            <div v-if="isOcrProcessing" class="attachment-card__loading">
              <svg class="w-4 h-4 attachment-card__spin" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/>
              </svg>
            </div>
          </div>
        </div>

        <div class="input-main-row">
          <!-- 左侧工具按钮 -->
          <div class="flex items-center gap-1 shrink-0">
            <button
              @click="emit('image-click')"
              :disabled="isLoading || isOcrProcessing || isRecording"
              class="input-icon-button input-add-button"
              :class="{ active: hasAttachment }"
              title="上传图片或 PDF"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14"/>
              </svg>
            </button>
            <span v-if="hasAttachment" class="attachment-count">1</span>
          </div>

          <!-- 输入框 -->
          <textarea
            ref="textareaRef"
            v-model="localValue"
            @keydown="handleKeydown"
            @input="autoResize"
            @compositionstart="onCompositionStart"
            @compositionend="onCompositionEnd"
            @paste="handlePaste"
            :disabled="isLoading || isRecording || isOcrProcessing"
            :placeholder="isOcrProcessing ? '正在处理文件…' : isRecording ? '录音中…' : '继续对话…'"
            class="input-textarea"
            rows="1"
          ></textarea>

          <!-- 右侧操作 -->
          <div class="input-actions">
            <button
              @click="emit('voice-click')"
              :disabled="isLoading || isOcrProcessing || isTranscribing"
              class="input-icon-button input-voice-button"
              :class="{ recording: isRecording }"
              :title="isRecording ? '停止录音' : '语音输入'"
            >
              <svg v-if="isTranscribing || isOcrProcessing" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              <svg v-else-if="isRecording" class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <rect x="7" y="7" width="10" height="10" rx="1.5"/>
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"/>
              </svg>
            </button>
            <span v-if="isRecording" class="recording-time">
              {{ formatDuration(recordingDuration) }}
            </span>

            <button v-if="isLoading" @click="emit('stop')"
              class="input-send-button input-stop-button"
              title="停止生成">
              <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2"/>
              </svg>
            </button>
            <button v-else @click="emit('send')" :disabled="(!localValue.trim() && !hasAttachment) || isOcrProcessing"
               class="input-send-button"
               title="发送">
               <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.2">
                 <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"/>
               </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 底部状态栏：模型切换 + token 用量 -->
      <div
        v-if="shouldShowModelSwitcher || floating"
        class="input-footer"
        :class="{ 'input-footer--floating': floating, 'input-footer--compact': !floating }"
      >
        <div
          v-if="shouldShowModelSwitcher"
          ref="modelMenuRef"
          class="model-select"
        >
          <button
            type="button"
            class="model-select__trigger"
            :class="{ 'is-open': isModelMenuOpen }"
            :aria-expanded="isModelMenuOpen ? 'true' : 'false'"
            aria-haspopup="listbox"
            :title="selectedModelOption?.title || selectedModelOption?.label || '选择 Hermes 基座模型'"
            @click.stop="toggleModelMenu"
          >
            <span class="model-select__label">{{ selectedModelOption?.label || '选择模型' }}</span>
            <svg class="model-select__chevron" :class="{ 'is-open': isModelMenuOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>

          <Transition name="fade-up">
            <div
              v-if="isModelMenuOpen"
              class="model-select__menu"
              role="listbox"
              aria-label="选择 Hermes 基座模型"
            >
              <button
                v-for="option in modelOptions"
                :key="option.value"
                type="button"
                class="model-select__option"
                :class="{ 'is-active': selectedModel === option.value }"
                :title="option.title || option.label"
                @click="selectModel(option.value)"
              >
                <span class="model-select__option-body">
                  <span class="model-select__option-label">{{ option.label }}</span>
                  <span v-if="option.title && option.title !== option.label" class="model-select__option-meta">
                    {{ option.title }}
                  </span>
                </span>
                <svg
                  v-if="selectedModel === option.value"
                  class="model-select__option-check"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.4"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </button>
            </div>
          </Transition>
        </div>

        <template v-if="floating">
          <span v-if="shouldShowModelSwitcher" class="input-footer__separator">·</span>
          <AiLabTokenUsage
            :prompt-tokens="sessionTokens.promptTokens"
            :completion-tokens="sessionTokens.completionTokens"
            :total-prompt-tokens="sessionTokens.totalPromptTokens"
            :total-completion-tokens="sessionTokens.totalCompletionTokens"
            :turn-count="sessionTokens.turnCount"
            :context-limit="contextLimit"
            :breakdown="sessionTokens.breakdown"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scroll-bottom-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}
.scroll-bottom-btn {
  border: none;
  background: rgba(248, 248, 246, 0.92);
  color: var(--theme-400, #8a8a82);
  font-size: 12px;
  line-height: 1;
  padding: 6px 10px;
  border-radius: 999px;
  box-shadow:
    0 8px 22px rgba(15, 23, 42, 0.08),
    0 1px 3px rgba(15, 23, 42, 0.06);
  transition: color 0.15s ease, transform 0.15s ease, background 0.15s ease;
}
.scroll-bottom-btn:hover {
  color: var(--theme-600, #5a5a52);
  background: rgba(255, 255, 255, 0.98);
  transform: translateY(-1px);
}
.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 0.2s ease;
}
.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
.input-footer {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin-top: 0.5rem;
  color: var(--theme-400);
}
.input-footer--floating {
  /* 浮动条同时挂着 token 用量等信息，居中显得平衡 */
  justify-content: center;
  font-size: 13px;
}
.input-footer--compact {
  /* Welcome 视图只剩孤零零一个模型 pill；居中会让它看起来很突兀。
     右对齐 + 更克制的留白，让它收敛到输入框的尾端做附属说明 */
  justify-content: flex-end;
  font-size: 12px;
  margin-top: 0.4rem;
  padding-right: 0.25rem;
}
.input-footer--compact .model-select__trigger {
  min-width: 0;
  height: 26px;
  padding: 0 0.55rem;
  font-size: 11.5px;
  background: transparent;
  border-color: rgba(15, 23, 42, 0.06);
  box-shadow: none;
}
.input-footer--compact .model-select__trigger:hover,
.input-footer--compact .model-select__trigger.is-open {
  background: rgba(255, 255, 255, 0.6);
  border-color: rgba(15, 23, 42, 0.12);
}
.input-footer--compact .model-select__chevron {
  width: 11px;
  height: 11px;
}
.input-footer__separator {
  color: var(--theme-300);
}
.model-select {
  position: relative;
}
.model-select__trigger {
  min-width: 108px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
  padding: 0 0.75rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--theme-500, #6b7280);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.96);
  transition: border-color 0.16s ease, color 0.16s ease, background 0.16s ease;
  cursor: pointer;
}
.model-select__trigger:hover,
.model-select__trigger.is-open {
  border-color: rgba(15, 23, 42, 0.14);
  color: var(--theme-700, #2d2d28);
  background: rgba(255, 255, 255, 0.95);
}
.model-select__label {
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}
.model-select__chevron {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  transition: transform 0.16s ease;
}
.model-select__chevron.is-open {
  transform: rotate(180deg);
}
.model-select__menu {
  position: absolute;
  left: 0;
  bottom: calc(100% + 6px);
  min-width: 220px;
  display: flex;
  flex-direction: column;
  padding: 4px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: rgba(255, 255, 255, 0.98);
  box-shadow:
    0 12px 32px rgba(15, 23, 42, 0.10),
    0 2px 6px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(12px);
  z-index: 20;
  overflow: hidden;
}
.model-select__option {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
}
.model-select__option + .model-select__option {
  margin-top: 1px;
}
.model-select__option:hover {
  background: rgba(15, 23, 42, 0.045);
}
.model-select__option.is-active {
  background: rgba(15, 23, 42, 0.05);
  color: var(--theme-700, #2d2d28);
}
.model-select__option-body {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
  flex: 1;
}
.model-select__option-label {
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.2;
  color: var(--theme-700, #2d2d28);
  white-space: nowrap;
}
.model-select__option-meta {
  font-size: 11px;
  line-height: 1.2;
  color: var(--theme-400, #9a9a92);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.model-select__option-check {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
  color: var(--ai-accent, #3d7cc9);
}
.input-shell {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(15, 23, 42, 0.11);
  border-radius: 28px;
  padding: 6px;
  box-shadow:
    0 18px 42px rgba(15, 23, 42, 0.08),
    0 2px 7px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
}
.input-shell:focus-within {
  border-color: rgba(45, 45, 40, 0.22);
  box-shadow:
    0 18px 42px rgba(15, 23, 42, 0.08),
    0 2px 7px rgba(15, 23, 42, 0.08),
    0 0 0 3px rgba(45, 45, 40, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
}
.input-main-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 4px 0 8px;
}
.input-textarea {
  flex: 1;
  min-width: 0;
  align-self: center;
  resize: none;
  border: 0;
  outline: none;
  background: transparent;
  color: #111827;
  font-size: 16px;
  line-height: 24px;
  min-height: 26px;
  /* JS 端 autoResize 会精确控制高度（最高约 220px ≈ 9 行）。
     这里 max-height 兜底，避免极端情况撑爆容器 */
  max-height: 220px;
  padding: 1px 0;
  overflow-y: hidden;
}
.input-textarea::-webkit-scrollbar {
  width: 4px;
}
.input-textarea::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.18);
  border-radius: 2px;
}
.input-textarea::placeholder {
  color: #9ca3af;
}
.input-textarea:disabled {
  opacity: 0.62;
  cursor: not-allowed;
}
.input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.input-icon-button {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 999px;
  color: #111827;
  background: transparent;
  transition: background 0.16s ease, color 0.16s ease, transform 0.16s ease;
  cursor: pointer;
}
.input-icon-button:hover:not(:disabled) {
  background: rgba(15, 23, 42, 0.06);
}
.input-icon-button:active:not(:disabled) {
  transform: scale(0.94);
}
.input-icon-button:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}
.input-add-button.active {
  color: var(--theme-700);
  background: var(--theme-100);
}
.input-voice-button.recording {
  color: #c53030;
  background: #fff5f5;
}
.attachment-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  margin-left: -10px;
  margin-right: 2px;
  border-radius: 999px;
  background: var(--theme-700);
  color: white;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}
.recording-time {
  min-width: 36px;
  color: #c53030;
  font-family: var(--ai-font-mono);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.input-send-button {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--theme-700);
  color: white;
  box-shadow: 0 6px 14px rgba(45, 45, 40, 0.18);
  transition: transform 0.16s ease, background 0.16s ease, opacity 0.16s ease;
  cursor: pointer;
}
.input-send-button:hover:not(:disabled) {
  background: var(--theme-600);
  transform: translateY(-1px);
}
.input-send-button:active:not(:disabled) {
  transform: scale(0.94);
}
.input-send-button:disabled {
  opacity: 0.42;
  cursor: not-allowed;
  box-shadow: none;
}
.input-stop-button {
  background: #e5e7eb;
  color: #374151;
  box-shadow: none;
}
.attachment-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 4px 2px 8px;
  padding: 0 6px;
}
.attachment-card {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--theme-100, #f5f4f1);
  border: 1px solid var(--theme-200, #e6e4dd);
  flex-shrink: 0;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.attachment-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
.attachment-card__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* PDF 卡片：模拟一页文档 */
.attachment-card.is-pdf {
  background: #fff;
}
.attachment-card__pdf-page {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 6px 18px;
  gap: 4px;
}
.attachment-card__pdf-glyph {
  width: 22px;
  height: 22px;
  color: var(--theme-400, #b3b1a6);
  flex-shrink: 0;
}
.attachment-card__pdf-name {
  font-size: 9px;
  line-height: 1.2;
  color: var(--theme-500, #888578);
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
  max-width: 100%;
}
.attachment-card__pdf-badge {
  position: absolute;
  bottom: 4px;
  left: 4px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 2px 5px;
  border-radius: 4px;
  background: #dc2626;
  color: #fff;
  line-height: 1;
}

/* 关闭按钮 — hover 才显示 */
.attachment-card__remove {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transform: scale(0.85);
  transition: opacity 0.12s ease, transform 0.12s ease;
  border: none;
  padding: 0;
}
.attachment-card:hover .attachment-card__remove {
  opacity: 1;
  transform: scale(1);
}
.attachment-card__remove:hover {
  background: rgba(0, 0, 0, 0.8);
}
.attachment-card__remove:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

/* OCR 处理 loading 遮罩 */
.attachment-card__loading {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--theme-600);
}
.attachment-card__spin {
  animation: attachment-spin 0.9s linear infinite;
}
@keyframes attachment-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
