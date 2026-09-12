import axios from 'axios'

export const ACCESS_TOKEN_KEY = 'mindtrace_access_token'

export function getAccessToken(): string | null {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  return token && token.trim() ? token : null
}

export function authHeaders(): Record<string, string> {
  const token = getAccessToken()

  return token
    ? { Authorization: `Bearer ${token}` }
    : {}
}

export function clearAccessToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
}

export const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ??
    'http://localhost:8000/api',
})

api.interceptors.request.use((config) => {
  const authorization = config.headers?.Authorization

  if (
    typeof authorization === 'string' &&
    authorization.trim().toLowerCase() === 'bearer null'
  ) {
    delete config.headers.Authorization
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAccessToken()
    }

    return Promise.reject(error)
  },
)
