const normalizeHost = (host) =>
  host.replace(/^https?:\/\//, "").replace(/^wss?:\/\//, "")

export const getWsHost = () => {
  const envHost = import.meta.env.VITE_WS_HOST
  if (envHost) {
    return normalizeHost(envHost)
  }
  return window.location.host
}

export const getWsBaseUrl = () => {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws"
  return `${protocol}://${getWsHost()}`
}

