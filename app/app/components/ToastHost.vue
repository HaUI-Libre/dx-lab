<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
// Thông báo không lấy focus của người dùng. Lỗi đọc ngay (assertive), còn lại đọc khi rảnh.
// Esc đóng thông báo đang được focus; nút Đóng dùng được bằng Tab.
const { toasts, dismiss, hold, release } = useToast()
const polite = computed(() => toasts.value.filter((t) => t.kind !== 'error'))
const urgent = computed(() => toasts.value.filter((t) => t.kind === 'error'))
const all = computed(() => toasts.value)
</script>

<template>
  <div>
    <!-- Hai vùng aria-live luôn có mặt trong DOM để trình đọc màn hình bắt được nội dung mới -->
    <div class="visually-hidden" aria-live="polite">
      <p v-for="t in polite" :key="t.id">{{ t.title }}. {{ t.body }}</p>
    </div>
    <div class="visually-hidden" aria-live="assertive">
      <p v-for="t in urgent" :key="t.id">{{ t.title }}. {{ t.body }}</p>
    </div>

    <TransitionGroup tag="ul" name="toast" class="toasts" aria-label="Thông báo">
      <li
        v-for="t in all" :key="t.id" class="toast" :data-kind="t.kind"
        @mouseenter="hold(t.id)" @mouseleave="release(t.id)"
        @focusin="hold(t.id)" @focusout="release(t.id)"
        @keydown.esc="dismiss(t.id)"
      >
        <svg class="toast-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path v-if="t.kind === 'success'" d="M5 12.5l4.5 4.5L19 7.5" />
          <path v-else-if="t.kind === 'error'" d="M12 7v6M12 16.5v.5M10.3 3.9 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
          <path v-else d="M12 11v6M12 7.5v.5M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z" />
        </svg>
        <div>
          <div class="toast-title">{{ t.title }}</div>
          <p v-if="t.body" class="toast-body">{{ t.body }}</p>
        </div>
        <button class="btn quiet btn-sm toast-close" type="button" :aria-label="`Đóng thông báo: ${t.title}`" @click="dismiss(t.id)">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      </li>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-icon,
.toast-close svg {
  width: 1.25rem;
  height: 1.25rem;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.toast-icon { margin-top: 0.2rem; }
.toast[data-kind="error"] .toast-icon { color: var(--brand-ink); }
.toast-close { min-height: 2rem; width: 2rem; padding: 0; }
</style>
