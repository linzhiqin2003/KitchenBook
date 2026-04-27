<script setup>
const props = defineProps({
  modelValue: String,
  label: String,
  disabled: Boolean,
  isTarget: Boolean,
})

const emit = defineEmits(['update:modelValue'])

const sourceLanguages = [
  { code: 'en', name: 'English' },
  { code: 'zh', name: '中文' },
  { code: 'yue', name: '粤语' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
  { code: 'fr', name: 'Français' },
  { code: 'de', name: 'Deutsch' },
  { code: 'es', name: 'Español' },
  { code: 'pt', name: 'Português' },
  { code: 'ru', name: 'Русский' },
  { code: 'ar', name: 'العربية' },
  { code: 'it', name: 'Italiano' },
  { code: 'th', name: 'ไทย' },
  { code: 'vi', name: 'Tiếng Việt' },
  { code: 'id', name: 'Bahasa Indonesia' },
  { code: 'ms', name: 'Bahasa Melayu' },
  { code: 'tr', name: 'Türkçe' },
  { code: 'hi', name: 'हिन्दी' },
  { code: 'nl', name: 'Nederlands' },
  { code: 'pl', name: 'Polski' },
  { code: 'sv', name: 'Svenska' },
  { code: 'da', name: 'Dansk' },
  { code: 'fi', name: 'Suomi' },
  { code: 'cs', name: 'Čeština' },
  { code: 'el', name: 'Ελληνικά' },
  { code: 'hu', name: 'Magyar' },
  { code: 'ro', name: 'Română' },
  { code: 'fa', name: 'فارسی' },
  { code: 'fil', name: 'Filipino' },
  { code: 'mk', name: 'Македонски' },
]

const targetLanguages = [
  { code: 'Chinese', name: '中文' },
  { code: 'English', name: 'English' },
  { code: 'Cantonese', name: '粤语' },
  { code: 'Japanese', name: '日本語' },
  { code: 'Korean', name: '한국어' },
  { code: 'French', name: 'Français' },
  { code: 'German', name: 'Deutsch' },
  { code: 'Spanish', name: 'Español' },
  { code: 'Portuguese', name: 'Português' },
  { code: 'Russian', name: 'Русский' },
  { code: 'Arabic', name: 'العربية' },
  { code: 'Italian', name: 'Italiano' },
  { code: 'Thai', name: 'ไทย' },
  { code: 'Vietnamese', name: 'Tiếng Việt' },
  { code: 'Indonesian', name: 'Bahasa Indonesia' },
  { code: 'Malay', name: 'Bahasa Melayu' },
  { code: 'Turkish', name: 'Türkçe' },
  { code: 'Hindi', name: 'हिन्दी' },
  { code: 'Dutch', name: 'Nederlands' },
  { code: 'Polish', name: 'Polski' },
  { code: 'Swedish', name: 'Svenska' },
  { code: 'Danish', name: 'Dansk' },
  { code: 'Finnish', name: 'Suomi' },
  { code: 'Czech', name: 'Čeština' },
  { code: 'Greek', name: 'Ελληνικά' },
  { code: 'Hungarian', name: 'Magyar' },
  { code: 'Romanian', name: 'Română' },
  { code: 'Persian', name: 'فارسی' },
  { code: 'Filipino', name: 'Filipino' },
  { code: 'Macedonian', name: 'Македонски' },
]
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label class="text-[12px] font-medium ml-0.5" style="color: var(--theme-400);">
      {{ label }}
    </label>
    <div class="relative">
      <select
        :value="modelValue"
        @change="emit('update:modelValue', $event.target?.value || '')"
        :disabled="disabled"
        class="w-full appearance-none rounded-lg py-2 px-3 pr-9 focus:outline-none transition-colors disabled:opacity-50 text-[14px] font-medium"
        style="background: #fff; color: var(--theme-700); border: 1px solid var(--theme-200);"
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
      <div class="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" style="color: var(--theme-400);">
        <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>
  </div>
</template>
