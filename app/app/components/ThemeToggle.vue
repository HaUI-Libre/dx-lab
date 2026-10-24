<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
const { current, read, toggle } = useTheme()
onMounted(read)

const label = computed(() => (current.value === 'dark' ? 'Chuyển sang chế độ sáng' : 'Chuyển sang chế độ tối'))
</script>

<template>
  <button class="theme-toggle" type="button" :aria-label="label" :title="label" :data-mode="current" @click="toggle">
    <!-- Mặt trời và mặt trăng tự vẽ; xoay chéo nhau khi đổi -->
    <svg class="sun" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="4.2" />
      <path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6" />
    </svg>
    <svg class="moon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 14.6A8.2 8.2 0 0 1 9.4 4a8.2 8.2 0 1 0 10.6 10.6Z" />
    </svg>
  </button>
</template>

<style scoped>
.theme-toggle {
  position: relative;
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  padding: 0;
  color: var(--ink);
  background: var(--card);
  border: 1px solid var(--rule);
  border-radius: var(--radius-pill);
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform var(--dur-fast) var(--ease-out);
}

.theme-toggle:hover { transform: translateY(-1px); }
.theme-toggle:active { transform: scale(0.94); }

svg {
  grid-area: 1 / 1;
  width: 1.25rem;
  height: 1.25rem;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: transform var(--dur-slow) var(--ease-spring), opacity var(--dur) var(--ease-out);
}

/* Đang sáng thì hiện mặt trăng (bấm để sang tối), và ngược lại */
.sun { opacity: 0; transform: rotate(-90deg) scale(0.5); }
.moon { fill: currentColor; stroke: none; }
[data-mode="dark"] .sun { opacity: 1; transform: none; }
[data-mode="dark"] .moon { opacity: 0; transform: rotate(90deg) scale(0.5); }
</style>
