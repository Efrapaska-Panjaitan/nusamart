<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, currency } from '../services/api'
interface Wish { id:string;variant_id:string;price:number|string;sku:string;product:{id:string;name:string;slug:string;image_url:string} }
const items=ref<Wish[]>([]);const loading=ref(true);const error=ref('')
async function load(){try{items.value=await api.get<Wish[]>('/api/v1/wishlist')}catch(e){error.value=e instanceof Error?e.message:'Gagal memuat wishlist'}finally{loading.value=false}}
async function remove(id:string){try{await api.delete('/api/v1/wishlist/'+id);items.value=items.value.filter(x=>x.variant_id!==id)}catch(e){error.value=e instanceof Error?e.message:'Gagal menghapus'}}
onMounted(load)
</script>
<template><section class="page-intro"><p class="eyebrow">SIMPAN FAVORIT</p><h1>Wishlist</h1><p>Produk yang kamu simpan untuk dipertimbangkan nanti.</p></section><p v-if="error" class="error-banner">{{ error }}</p><div v-if="loading" class="loading-state">Memuat wishlist…</div><div v-else-if="items.length" class="product-grid"> <article v-for="item in items" :key="item.id" class="product-card"><RouterLink :to="{name:'product-detail',params:{slug:item.product.slug}}" class="product-image-wrap"><img :src="item.product.image_url" :alt="item.product.name"/></RouterLink><div class="product-info"><RouterLink :to="{name:'product-detail',params:{slug:item.product.slug}}" class="product-name">{{ item.product.name }}</RouterLink><div class="product-price">{{ currency(item.price) }}</div><button class="button-secondary full-button" @click="remove(item.variant_id)">Hapus dari wishlist</button></div></article></div><div v-else-if="!loading" class="empty-state"><h3>Wishlist masih kosong</h3><p>Simpan produk favorit dari halaman detail atau katalog.</p><RouterLink to="/products" class="button-primary">Jelajahi produk</RouterLink></div></template>
