<script setup>
import { computed } from 'vue'

const props = defineProps({
  entry: { type: Object, required: true },
  size: { type: String, default: 'w-4 h-4' },
})

const kind = computed(() => {
  const e = props.entry
  if (!e) return 'file'
  if (e.type === 'dir') return 'dir'
  if (e.type === 'symlink') return 'symlink'
  const name = (e.name || '').toLowerCase()
  const ext = name.includes('.') ? name.split('.').pop() : ''
  if (['md', 'markdown', 'mdx'].includes(ext)) return 'md'
  if (['json', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf'].includes(ext)) return 'config'
  if (['py', 'js', 'mjs', 'cjs', 'ts', 'tsx', 'jsx', 'vue', 'svelte', 'html', 'htm', 'css', 'scss', 'sass', 'less', 'go', 'rs', 'c', 'cc', 'cpp', 'h', 'hpp', 'java', 'sh', 'bash', 'zsh', 'rb', 'php', 'swift', 'kt', 'dart', 'lua', 'pl'].includes(ext)) return 'code'
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico', 'heic', 'heif', 'avif'].includes(ext)) return 'image'
  if (ext === 'pdf') return 'pdf'
  if (['mp4', 'mov', 'webm', 'avi', 'mkv', 'm4v', 'flv'].includes(ext)) return 'video'
  if (['mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac', 'opus'].includes(ext)) return 'audio'
  if (['zip', 'tar', 'gz', '7z', 'rar', 'bz2', 'xz', 'tgz'].includes(ext)) return 'archive'
  if (['txt', 'log', 'env', 'rst', 'csv', 'tsv'].includes(ext)) return 'text'
  return 'file'
})
</script>

<template>
  <span class="entry-icon shrink-0" :data-kind="kind">
    <!-- Folder -->
    <svg v-if="kind === 'dir'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
      <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75A2.25 2.25 0 014.5 4.5h4.19a2.25 2.25 0 011.59.659l1.06 1.06a2.25 2.25 0 001.59.659h6.56a2.25 2.25 0 012.25 2.25v8.25a2.25 2.25 0 01-2.25 2.25H4.5a2.25 2.25 0 01-2.25-2.25V6.75z"/>
    </svg>
    <!-- Symlink -->
    <svg v-else-if="kind === 'symlink'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.7">
      <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 016.364 6.364l-1.757 1.757a4.5 4.5 0 01-6.364 0m-1.414-9.9a4.5 4.5 0 00-6.364 0L2.44 8.666a4.5 4.5 0 006.364 6.364l1.757-1.757"/>
    </svg>
    <!-- Markdown: document with characteristic 'M' arrow -->
    <svg v-else-if="kind === 'md'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 13.5l-1.875-1.875M9.75 12v5.25m1.875-1.875L13.5 17.25M6.75 7.5h.75v.75h-.75V7.5zm0 3h.75v.75h-.75v-.75zm0 3h.75v.75h-.75v-.75zM8.25 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
    </svg>
    <!-- Code: bracket-square -->
    <svg v-else-if="kind === 'code'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
      <path stroke-linecap="round" stroke-linejoin="round" d="M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z"/>
    </svg>
    <!-- Config: braces -->
    <svg v-else-if="kind === 'config'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 8.25c2.25 0 2.25-2.25 4.5-2.25M3.75 8.25c2.25 0 2.25 2.25 4.5 2.25m-4.5-2.25v7.5M8.25 6c0-1.243-1.007-2.25-2.25-2.25H4.5M8.25 6V18m0 0c0 1.243-1.007 2.25-2.25 2.25H4.5M15.75 18c0 1.243 1.007 2.25 2.25 2.25h1.5m-3.75-2.25V6m0 12c2.25 0 2.25-2.25 4.5-2.25m-4.5 2.25c2.25 0 2.25 2.25 4.5 2.25m0-9.75v-7.5M15.75 6c0-1.243 1.007-2.25 2.25-2.25h1.5"/>
    </svg>
    <!-- Image: photo -->
    <svg v-else-if="kind === 'image'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
      <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"/>
    </svg>
    <!-- PDF: document with 'PDF' overlay-styled corner -->
    <svg v-else-if="kind === 'pdf'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
    </svg>
    <!-- Video: film -->
    <svg v-else-if="kind === 'video'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
      <path stroke-linecap="round" stroke-linejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 10.875v6.75m0-6.75v-1.5m0 1.5h7.5m0 0h1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125M19.5 12.75v3.75M12 18.375v-1.5m0 1.5h7.5m-7.5 0h-7.5"/>
    </svg>
    <!-- Audio: musical-note -->
    <svg v-else-if="kind === 'audio'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9 9l10.5-3m0 6.553v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 11-.99-3.467l2.31-.66a2.25 2.25 0 001.632-2.163zm0 0V2.25L9 5.25v10.303m0 0v3.75a2.25 2.25 0 01-1.632 2.163l-1.32.377a1.803 1.803 0 01-.99-3.467l2.31-.66A2.25 2.25 0 009 15.553z"/>
    </svg>
    <!-- Archive: archive-box -->
    <svg v-else-if="kind === 'archive'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
      <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"/>
    </svg>
    <!-- Text: document-text -->
    <svg v-else-if="kind === 'text'" :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
      <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
    </svg>
    <!-- File default: document -->
    <svg v-else :class="size" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.6">
      <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
    </svg>
  </span>
</template>

<style scoped>
.entry-icon { display: inline-flex; align-items: center; justify-content: center; }
.entry-icon[data-kind="dir"]     { color: var(--ai-accent); }
.entry-icon[data-kind="symlink"] { color: #7e6cd1; }
.entry-icon[data-kind="md"]      { color: #4f7ba0; }
.entry-icon[data-kind="code"]    { color: #7e6cd1; }
.entry-icon[data-kind="config"]  { color: #b97a2c; }
.entry-icon[data-kind="image"]   { color: #c47297; }
.entry-icon[data-kind="pdf"]     { color: #c64a4a; }
.entry-icon[data-kind="video"]   { color: #c64a4a; }
.entry-icon[data-kind="audio"]   { color: #4f7ba0; }
.entry-icon[data-kind="archive"] { color: #8a6a3d; }
.entry-icon[data-kind="text"]    { color: #6b7280; }
.entry-icon[data-kind="file"]    { color: #8a8a93; }
</style>
