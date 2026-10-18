import { defineStore } from 'pinia'
import { api } from '../services/api'
import type { User } from '../types'
interface AuthResponse { access_token: string; token_type: string; expires_in: number; user: User }
export const useAuthStore = defineStore('auth', {
  state: () => ({ token: localStorage.getItem('nusamart_access_token') ?? '', user: JSON.parse(localStorage.getItem('nusamart_user') ?? 'null') as User | null, busy: false }),
  getters: { isAuthenticated: (state) => Boolean(state.token && state.user), isAdmin: (state) => state.user?.role === 'admin' },
  actions: {
    saveSession(data: AuthResponse) { this.token = data.access_token; this.user = data.user; localStorage.setItem('nusamart_access_token', data.access_token); localStorage.setItem('nusamart_user', JSON.stringify(data.user)) },
    async login(email: string, password: string) { this.busy = true; try { const data = await api.post<AuthResponse>('/api/v1/auth/login', { email, password }); this.saveSession(data); return data.user } finally { this.busy = false } },
    async register(email: string, full_name: string, password: string) { this.busy = true; try { await api.post('/api/v1/auth/register', { email, full_name, password }); return await this.login(email, password) } finally { this.busy = false } },
    async refreshMe() { if (!this.token) return null; try { const user = await api.get<User>('/api/v1/auth/me'); this.user = user; localStorage.setItem('nusamart_user', JSON.stringify(user)); return user } catch { this.logout(); return null } },
    logout() { this.token = ''; this.user = null; localStorage.removeItem('nusamart_access_token'); localStorage.removeItem('nusamart_user') },
  },
})
