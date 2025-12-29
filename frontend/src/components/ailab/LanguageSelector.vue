<script setup>
const props = defineProps({
  modelValue: String,
  label: String,
  disabled: Boolean,
  isTarget: Boolean,
})

const emit = defineEmits(['update:modelValue'])

// Source languages
const sourceLanguages = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
  { code: 'yue', name: '粤语' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
  { code: 'de', name: 'Deutsch' },
  { code: 'fr', name: 'Français' },
  { code: 'es', name: 'Español' },
  { code: 'ru', name: 'Русский' },
]

// Target languages
const targetLanguages = [
  { code: 'Chinese', name: '中文' },
  { code: 'English', name: 'English' },
  { code: 'Japanese', name: '日本語' },
  { code: 'Korean', name: '한국어' },
  { code: 'German', name: 'Deutsch' },
  { code: 'French', name: 'Français' },
  { code: 'Spanish', name: 'Español' },
  { code: 'Russian', name: 'Русский' },
]
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="text-[13px] font-medium text-ios-gray ml-1">
      {{ label }}
    </label>
    <div class="relative group">
      <select
        :value="modelValue"
        @change="emit('update:modelValue', $event.target?.value || '')"
        :disabled="disabled"
        class="w-full appearance-none bg-ios-card2 text-white border border-transparent rounded-xl py-3 px-4 pr-10
               focus:outline-none focus:border-ios-blue transition-colors disabled:opacity-50
               text-[15px] font-medium"
      >
        <template v-if="isTarget">
          <option v-for="lang in targetLanguages" :key="lang.code" :value="lang.code">
            {{ lang.name }}
          </option>
        </template>
        <template v-else>
          <option v-for="lang in sourceLanguages" :key="lang.code" :value="lang.code">
            {{ lang.name }}
          </option>
        </template>
      </select>
      
      <!-- Custom Arrow -->
      <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-ios-gray">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>
  </div>
</template>
