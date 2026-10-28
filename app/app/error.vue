<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{
  error: NuxtError
}>()

if (props.error.statusCode === 401) {
  await navigateTo('/auth/login', { external: true })
}

const handleError = () => clearError({ redirect: '/' })
</script>

<template>
  <div class="error-page container">
    <div class="card error-card">
      <div class="error-code">{{ error.statusCode }}</div>
      <h1 class="error-title">
        {{ error.statusCode === 404 ? 'Không tìm thấy trang' : 'Đã có lỗi xảy ra' }}
      </h1>
      <p class="error-message">{{ error.message || 'Hệ thống không thể xử lý yêu cầu.' }}</p>
      <div class="error-actions">
        <button class="btn btn-primary" @click="handleError">Về trang chủ</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
  padding: 2rem;
}
.error-card {
  max-width: 480px;
  width: 100%;
  text-align: center;
  padding: 2.5rem;
}
.error-code {
  font-size: 4rem;
  font-weight: 800;
  color: var(--color-primary, #1e40af);
  line-height: 1;
  margin-bottom: 1rem;
}
.error-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}
.error-message {
  color: var(--color-text-muted, #6b7280);
  margin-bottom: 1.5rem;
}
.error-actions {
  display: flex;
  justify-content: center;
}
</style>
