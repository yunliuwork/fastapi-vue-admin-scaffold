import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { message } from 'ant-design-vue'

interface Envelope<T> {
  code: number
  message: string
  data: T
}

const http = axios.create({ baseURL: '/api/v1', timeout: 15000 })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshing: Promise<string> | null = null

function refreshAccess() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    return Promise.reject(new Error('未登录或登录已过期'))
  }
  if (!refreshing) {
    refreshing = axios
      .post<Envelope<{ access_token: string; refresh_token: string }>>('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      })
      .then((response) => {
        if (response.data.code !== 0) {
          throw new Error(response.data.message)
        }
        localStorage.setItem('access_token', response.data.data.access_token)
        localStorage.setItem('refresh_token', response.data.data.refresh_token)
        return response.data.data.access_token
      })
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

http.interceptors.response.use(
  (response) => response.data.data,
  async (error: AxiosError<Envelope<null>>) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    const status = error.response?.status
    const url = original?.url ?? ''
    const text = error.response?.data?.message || '请求失败'
    if (
      status === 401 &&
      original &&
      !original._retry &&
      !url.includes('/auth/login') &&
      !url.includes('/auth/refresh')
    ) {
      original._retry = true
      try {
        const token = await refreshAccess()
        original.headers.Authorization = `Bearer ${token}`
        return await http(original)
      } catch {
        message.error('登录已过期')
        clearSession()
        if (!window.location.pathname.startsWith('/login')) {
          window.location.assign('/login')
        }
        return Promise.reject(new Error('登录已过期'))
      }
    }
    message.error(text)
    return Promise.reject(new Error(text))
  },
)

export function getJson<T>(url: string, params?: object): Promise<T> {
  return http.get(url, { params }) as Promise<T>
}

export function postJson<T>(url: string, body?: unknown): Promise<T> {
  return http.post(url, body) as Promise<T>
}

export function putJson<T>(url: string, body?: unknown): Promise<T> {
  return http.put(url, body) as Promise<T>
}

export function patchJson<T>(url: string, body?: unknown): Promise<T> {
  return http.patch(url, body) as Promise<T>
}

export function deleteJson<T>(url: string): Promise<T> {
  return http.delete(url) as Promise<T>
}
