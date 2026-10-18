<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import ProductCard from '../components/ProductCard.vue'
import LoadingState from '../components/LoadingState.vue'
import type { Product, Category, PageResult } from '../types'
import { api } from '../services/api'
const categories = ref<Category[]>([]); const products = ref<Product[]>([]); const loading = ref(true); const error = ref('')
const categoryIcons = ['▣','◇','⌂','✳','↗','◎']
onMounted(async () => { try { const result = await Promise.all([api.get<Category[]>('/api/v1/categories'), api.get<PageResult<Product>>('/api/v1/products?page=1&page_size=8&sort=popular')]); categories.value = result[0]; products.value = result[1].items } catch(e) { error.value = e instanceof Error ? e.message : 'Gagal memuat toko' } finally { loading.value = false } })
</script>
<template>
  <section class="hero-banner"><div class="hero-content"><p class="eyebrow">PILIHAN UNTUK SETIAP HARI</p><h1>Belanja lebih nyaman.<br />Pilihan lebih baik.</h1><p>Temukan produk pilihan dengan kualitas terpercaya dan harga yang bersahabat.</p><RouterLink to="/products" class="button-primary">Jelajahi produk <span>→</span></RouterLink><div class="trust-inline"><span>✓ Produk pilihan</span><span>✓ Pembayaran aman</span><span>✓ Dukungan pelanggan</span></div></div><div class="hero-art"><div class="hero-circle"></div><div class="hero-product-visual"><span>NM</span><small>GOOD THINGS, EVERY DAY</small></div><div class="hero-float">Pilihan tepat<br/>untuk keseharianmu</div><div class="leaf leaf-one"></div><div class="leaf leaf-two"></div></div></section>
  <section class="section"><div class="section-heading"><div><p class="eyebrow">TEMUKAN FAVORITMU</p><h2>Kategori populer</h2></div><RouterLink to="/products" class="text-link">Lihat semua →</RouterLink></div><div v-if="categories.length" class="category-grid"><RouterLink v-for="(category,i) in categories" :key="category.id" :to="{name:'products',query:{category:category.slug}}" class="category-tile" :class="`tone-${(i%6)+1}`"><span class="category-icon">{{ categoryIcons[i%6] }}</span><strong>{{ category.name }}</strong><small>{{ category.product_count ?? 0 }} produk</small></RouterLink></div><LoadingState v-else-if="loading" label="Memuat kategori…"/><div v-else class="muted">Kategori belum tersedia.</div></section>
  <section class="section"><div class="section-heading"><div><p class="eyebrow">DIKURASI UNTUKMU</p><h2>Produk pilihan</h2></div><RouterLink to="/products" class="text-link">Jelajahi katalog →</RouterLink></div><p v-if="error" class="error-banner">{{ error }}</p><LoadingState v-else-if="loading"/><div v-else-if="products.length" class="product-grid"><ProductCard v-for="p in products" :key="p.id" :product="p"/></div><div v-else class="empty-state"><h3>Belum ada produk</h3><p>Produk akan tampil setelah katalog tersedia.</p></div></section>
  <section class="benefit-strip"><div><span>♢</span><strong>Belanja praktis</strong><small>Temukan kebutuhan dalam satu tempat</small></div><div><span>◇</span><strong>Pilihan berkualitas</strong><small>Katalog pilihan untuk kegiatan harian</small></div><div><span>↗</span><strong>Status transparan</strong><small>Riwayat pesanan bisa dipantau</small></div><div><span>♡</span><strong>Responsif</strong><small>Nyaman dibuka di laptop maupun ponsel</small></div></section>
</template>
