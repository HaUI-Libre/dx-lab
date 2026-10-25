<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
// Số đếm lên khi tải. Server render đúng giá trị cuối, nên không có JavaScript vẫn đọc được;
// trình đọc màn hình đọc giá trị cuối qua aria-label, không đọc từng bước đếm.
const props = withDefaults(defineProps<{ value: number | null, decimals?: number, duration?: number }>(), {
  decimals: 0,
  duration: 700,
})

const shown = ref(props.value ?? 0)
const text = computed(() => (props.value == null ? '–' : shown.value.toLocaleString('vi-VN', { minimumFractionDigits: props.decimals, maximumFractionDigits: props.decimals })))
const final = computed(() => (props.value == null ? 'chưa có' : props.value.toLocaleString('vi-VN', { maximumFractionDigits: props.decimals })))

let frame = 0
function run(to: number | null) {
  cancelAnimationFrame(frame)
  if (to == null) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    shown.value = to
    return
  }
  const start = performance.now()
  const tick = (now: number) => {
    const t = Math.min(1, (now - start) / props.duration)
    shown.value = to * (1 - (1 - t) ** 3)
    if (t < 1) frame = requestAnimationFrame(tick)
  }
  shown.value = 0
  frame = requestAnimationFrame(tick)
}

onMounted(() => run(props.value))
watch(() => props.value, run)
onBeforeUnmount(() => cancelAnimationFrame(frame))
</script>

<template>
  <span class="count-up" :aria-label="final"><span aria-hidden="true">{{ text }}</span></span>
</template>

<style scoped>
.count-up { font-variant-numeric: tabular-nums; }
</style>
