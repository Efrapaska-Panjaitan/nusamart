import { defineStore } from 'pinia'
import { api } from '../services/api'
import type { Cart } from '../types'
export const useCartStore = defineStore('cart', {
  state: () => ({ cart: null as Cart | null, loading: false }),
  getters: { count: (state) => state.cart?.item_count ?? 0, subtotal: (state) => Number(state.cart?.subtotal ?? 0) },
  actions: {
    async fetch() { this.loading = true; try { this.cart = await api.get<Cart>('/api/v1/cart'); return this.cart } finally { this.loading = false } },
    async add(variant_id: string, quantity = 1) { this.cart = await api.post<Cart>('/api/v1/cart/items', { variant_id, quantity }); return this.cart },
    async update(item_id: string, quantity: number) { this.cart = await api.patch<Cart>(`/api/v1/cart/items/${item_id}`, { quantity }); return this.cart },
    async remove(item_id: string) { await api.delete(`/api/v1/cart/items/${item_id}`); await this.fetch() },
    async clear() { await api.delete('/api/v1/cart'); this.cart = { id: '', items: [], item_count: 0, subtotal: 0 } },
    reset() { this.cart = null },
  },
})
