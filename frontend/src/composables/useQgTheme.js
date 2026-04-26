import { ref, computed, onMounted, onBeforeUnmount, watchEffect } from 'vue';

/**
 * Theme controller for the QuestionGen surface.
 * Persists preference (`qg_theme` in localStorage) and reflects to
 * `<html data-qg-theme="...">` so design tokens swap synchronously.
 *
 * Three modes:
 *   - 'light'  : force light
 *   - 'dark'   : force dark
 *   - 'system' : follow prefers-color-scheme (default)
 */
const STORAGE_KEY = 'qg_theme';

const mode = ref(/** @type {'light'|'dark'|'system'} */ ('system'));
const systemDark = ref(false);

function readMode() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === 'light' || saved === 'dark') return saved;
  return 'system';
}

function applyTheme(resolvedTheme) {
  document.documentElement.setAttribute('data-qg-theme', resolvedTheme);
}

let mql = null;

export function useQgTheme() {
  const resolved = computed(() => {
    if (mode.value === 'system') return systemDark.value ? 'dark' : 'light';
    return mode.value;
  });

  function setMode(next) {
    mode.value = next;
    if (next === 'system') localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, next);
  }

  function cycle() {
    // light → dark → system → light
    setMode(mode.value === 'light' ? 'dark' : mode.value === 'dark' ? 'system' : 'light');
  }

  onMounted(() => {
    mode.value = readMode();
    if (window.matchMedia) {
      mql = window.matchMedia('(prefers-color-scheme: dark)');
      systemDark.value = mql.matches;
      const handler = (e) => { systemDark.value = e.matches; };
      mql.addEventListener?.('change', handler);
      onBeforeUnmount(() => mql.removeEventListener?.('change', handler));
    }
  });

  watchEffect(() => applyTheme(resolved.value));

  return { mode, resolved, setMode, cycle };
}
