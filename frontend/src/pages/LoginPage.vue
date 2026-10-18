<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
const auth=useAuthStore();const route=useRoute();const router=useRouter();const email=ref('');const password=ref('');const error=ref('')
async function submit(){error.value='';try{await auth.login(email.value,password.value);router.push(String(route.query.redirect??'/'))}catch(e){error.value=e instanceof Error?e.message:'Login gagal'}}
</script>
<template><section class="auth-card"><RouterLink to="/" class="brand auth-brand">Nusa<span>Mart</span></RouterLink><p class="eyebrow">SELAMAT DATANG KEMBALI</p><h1>Masuk ke akunmu</h1><p class="auth-subtitle">Lanjutkan belanja dan pantau pesananmu.</p><form class="form-stack" @submit.prevent="submit"><label class="field-label">Email<input v-model="email" type="email" autocomplete="email" placeholder="nama@email.com" required /></label><label class="field-label">Password<input v-model="password" type="password" autocomplete="current-password" placeholder="Masukkan password" required minlength="8" /></label><p v-if="error" class="error-banner">{{ error }}</p><button class="button-primary full-button" :disabled="auth.busy">{{ auth.busy?'Memproses…':'Masuk' }}</button></form><p class="auth-switch">Belum punya akun? <RouterLink to="/register">Daftar sekarang</RouterLink></p><p class="demo-hint">Admin demo lokal: admin@nusamart.local · Admin1234!</p></section></template>
