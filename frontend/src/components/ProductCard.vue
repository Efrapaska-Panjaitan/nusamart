<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import type { Product } from '../types'
import { api, currency } from '../services/api'
import { useAuthStore } from '../stores/auth'
import { useCartStore } from '../stores/cart'
const props = defineProps<{ product: Product }>()
const router = useRouter(); const auth = useAuthStore(); const cart = useCartStore(); const busy = ref(false); const message = ref('')
const variant = computed(() => props.product.variants.find(v => v.is_active && v.stock_available > 0) ?? props.product.variants.find(v => v.is_active))
async function addToCart() {
  if (!auth.isAuthenticated) { router.push({name:'login',query:{redirect:'/cart'}}); return }
  if (!variant.value || !props.product.in_stock) { message.value = 'Stok habis'; return }
  busy.value = true; message.value = ''
  try { await cart.add(variant.value.id, 1); message.value = 'Ditambahkan' }
  catch (e) { message.value = e instanceof Error ? e.message : 'Gagal menambahkan produk' }
  finally { busy.value = false; window.setTimeout(() => message.value = '', 2400) }
}
async function toggleWishlist() {
  if (!auth.isAuthenticated) { router.push({name:'login'}); return }
  if (!variant.value) return
  try { await api.post(`/api/v1/wishlist/${variant.value.id}`); message.value = 'Disimpan ke wishlist'; window.setTimeout(() => message.value = '', 2000) }
  catch (e) { message.value = e instanceof Error ? e.message : 'Gagal menyimpan' }
}
</script>
<template>
  <article class="product-card">
    <div class="product-image-wrap"><RouterLink :to="{name:'product-detail', params:{slug: product.slug}}"><img :src="product.image_url" :alt="product.name" loading="lazy" @error="($event.target as HTMLImageElement).src='https://placehold.co/600x500/e6efea/137c70?text=NusaMart'" /></RouterLink><button class="heart-button" aria-label="Simpan ke wishlist" @click="toggleWishlist">♡</button><span v-if="!product.in_stock" class="sold-out-tag">Stok habis</span></div>
    <div class="product-info"><RouterLink :to="{name:'product-detail', params:{slug: product.slug}}" class="product-name">{{ product.name }}</RouterLink><div class="product-rating"><span>★ {{ product.average_rating.toFixed(1) }}</span><span class="muted">({{ product.review_count }})</span></div><div class="product-price">{{ currency(product.min_price) }}<span v-if="Number(product.max_price) > Number(product.min_price)" class="price-range"> – {{ currency(product.max_price) }}</span></div><button class="button-primary full-button" :disabled="busy || !product.in_stock" @click="addToCart">{{ busy ? 'Menambahkan…' : product.in_stock ? '+ Keranjang' : 'Stok Habis' }}</button><p v-if="message" class="inline-message">{{ message }}</p></div>
  </article>
</template>
