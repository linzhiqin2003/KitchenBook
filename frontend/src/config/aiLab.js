import API_BASE_URL from './api'

const normalizeHost = (host) =>
  host.replace(/^https?:\/\//, '').replace(/^wss?:\/\//, '')

export const getAiLabApiBase = () => API_BASE_URL || ''

export const getAiLabWsHost = () => {
  const envHost = import.meta.env.VITE_WS_HOST
  if (envHost) {
    return normalizeHost(envHost)
  }

  if (API_BASE_URL) {
    try {
      return new URL(API_BASE_URL).host
    } catch (error) {
      // Ignore invalid URL and fall back to window host.
    }
  }

  return window.location.host
}

export const getAiLabWsBaseUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${protocol}://${getAiLabWsHost()}`
}
