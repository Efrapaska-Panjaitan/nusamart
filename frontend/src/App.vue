<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useCartStore } from './stores/cart'
const auth = useAuthStore(); const cart = useCartStore(); const route = useRoute()
const showHeader = computed(() => !['login', 'register'].includes(String(route.name)))
function submitSearch(event: Event) { const form = event.target as HTMLFormElement; const input = form.elements.namedItem('search') as HTMLInputElement | null; const value = input?.value.trim() ?? ''; routerPush(value) }
function routerPush(search: string) { window.location.href = search ? `/products?search=${encodeURIComponent(search)}` : '/products' }
onMounted(async () => { if (auth.isAuthenticated) { try { await cart.fetch() } catch { auth.logout(); cart.reset() } } })
watch(() => auth.isAuthenticated, async loggedIn => { if (loggedIn) { try { await cart.fetch() } catch { auth.logout(); cart.reset() } } else cart.reset() })
function logout() { auth.logout(); cart.reset(); location.href = '/' }
</script>
<template>
  <div class="app-root">
    <div v-if="showHeader" class="announcement">Gratis ongkir untuk pesanan minimal Rp200.000 · Belanja nyaman di NusaMart</div>
    <header v-if="showHeader" class="site-header wrap">
      <RouterLink to="/" class="brand">Nusa<span>Mart</span></RouterLink>
      <form class="header-search" @submit.prevent="submitSearch">
        <input name="search" placeholder="Cari produk, kategori, atau merek..." aria-label="Cari produk" />
        <button aria-label="Cari">⌕</button>
      </form>
      <nav class="header-actions">
        <RouterLink to="/products">Katalog</RouterLink>
        <RouterLink v-if="auth.isAuthenticated" to="/wishlist">♡ Wishlist</RouterLink>
        <RouterLink v-if="auth.isAuthenticated" to="/cart" class="cart-link">Keranjang <span class="cart-count">{{ cart.count }}</span></RouterLink>
        <RouterLink v-if="auth.isAuthenticated" to="/orders">Pesanan</RouterLink>
        <RouterLink v-if="auth.isAdmin" to="/admin">Admin</RouterLink>
        <RouterLink v-if="!auth.isAuthenticated" to="/login" class="login-link">Masuk</RouterLink>
        <button v-else class="link-button" @click="logout">Keluar</button>
      </nav>
    </header>
    <main :class="showHeader ? 'main-content wrap' : 'main-content auth-background'"><RouterView /></main>
    <footer v-if="showHeader" class="site-footer"><div class="wrap footer-inner"><div><RouterLink to="/" class="brand">Nusa<span>Mart</span></RouterLink><p>Belanja lebih nyaman, setiap hari.</p></div><div class="footer-links"><RouterLink to="/products">Katalog</RouterLink><RouterLink to="/orders">Pesanan</RouterLink><RouterLink to="/profile">Akun</RouterLink></div><small>© 2026 NusaMart · Portfolio project</small></div></footer>
  </div>
</template>
