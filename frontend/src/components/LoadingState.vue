<script setup lang="ts">defineProps<{ label?: string }>()</script>
<template><div class="loading-state"><span class="spinner"></span><span>{{ label ?? 'Memuat data…' }}</span></div></template>
