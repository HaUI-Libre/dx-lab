<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { GuideDoc } from '~/utils/portal'

defineProps<{
  doc: GuideDoc | null
  content: string
  loading: boolean
  error: string | null
}>()

defineEmits<{
  (e: 'close'): void
  (e: 'download', doc: GuideDoc): void
}>()
</script>

<template>
  <div v-if="doc" class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-dialog modal-lg" role="dialog" aria-modal="true">
      <header class="modal-header">
        <div>
          <span class="badge role-badge">{{ doc.categoryLabel }}</span>
          <h3 class="modal-title">{{ doc.title }}</h3>
          <p class="modal-subtitle">Đường dẫn: <code>/api/files/{{ doc.filePath }}</code></p>
        </div>
        <button class="close-btn" type="button" aria-label="Đóng" @click="$emit('close')">×</button>
      </header>

      <div class="modal-body">
        <div v-if="loading" class="preview-loading">
          <p>Đang nạp tài liệu từ SeaweedFS qua API Gateway…</p>
        </div>
        <div v-else-if="error" class="notice danger">
          <p>{{ error }}</p>
        </div>
        <pre v-else class="preview-text">{{ content }}</pre>
      </div>

      <footer class="modal-footer">
        <button class="btn secondary" type="button" @click="$emit('close')">Đóng</button>
        <button class="btn" type="button" @click="$emit('download', doc)">⬇️ Tải tệp về máy</button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-dialog {
  background: var(--surface);
  border-radius: 0.5rem;
  width: 100%;
  max-width: 32rem;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.modal-dialog.modal-lg {
  max-width: 50rem;
}

.modal-header {
  padding: 1.25rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.modal-title {
  margin: 0.25rem 0 0;
  font-size: 1.125rem;
}

.modal-subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.75rem;
  color: var(--muted);
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: var(--muted);
}

.close-btn:hover {
  color: var(--text);
}

.modal-body {
  padding: 1.25rem;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  border-radius: 0.25rem;
}

.role-badge {
  background: rgba(11, 92, 173, 0.12);
  color: var(--accent);
}

.preview-text {
  background: var(--bg);
  padding: 1rem;
  border-radius: 0.375rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  margin: 0;
}

.preview-loading {
  padding: 2rem;
  text-align: center;
  color: var(--muted);
}
</style>
