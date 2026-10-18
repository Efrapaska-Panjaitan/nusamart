const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'
export class ApiError extends Error {
  status: number
  detail: unknown
  constructor(message: string, status: number, detail?: unknown) { super(message); this.name = 'ApiError'; this.status = status; this.detail = detail }
}
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (!(options.body instanceof FormData) && options.body !== undefined) headers.set('Content-Type', 'application/json')
  const token = localStorage.getItem('nusamart_access_token')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (response.status === 204) return undefined as T
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = payload?.detail ?? payload?.error?.message ?? `Request gagal (${response.status})`
    const message = typeof detail === 'string' ? detail : `Request gagal (${response.status})`
    if (response.status === 401) {
      localStorage.removeItem('nusamart_access_token')
      localStorage.removeItem('nusamart_user')
    }
    throw new ApiError(message, response.status, detail)
  }
  return payload as T
}
export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown, extraHeaders?: Record<string, string>) => request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body), headers: extraHeaders }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
export const currency = (value: number | string) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(Number(value || 0))
export const formatDate = (value: string) => new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
