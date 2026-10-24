<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
// Số thứ tự theo vòng đời, in trên tem như số hiệu bước kiểm định.
// REJECTED là nhánh kết thúc ở bước tiếp nhận nên không có số.
const STEP: Record<string, string> = {
  DRAFT: '01',
  SUBMITTED: '02',
  ASSIGNED: '03',
  IN_PROGRESS: '04',
  RESOLVED: '05',
  CLOSED: '06',
  REJECTED: 'X',
}

const props = defineProps<{ status: string }>()

// Chỉ đóng dấu khi trạng thái đổi, không chạy lúc tải trang
const stamping = ref(false)
watch(() => props.status, () => {
  stamping.value = false
  requestAnimationFrame(() => { stamping.value = true })
})
</script>

<template>
  <span
    class="stamp" :class="{ 'is-stamping': stamping }" :data-status="props.status"
    @animationend="stamping = false"
  >
    <span class="stamp-no" aria-hidden="true">{{ STEP[props.status] ?? '--' }}</span>
    {{ STATUS_LABELS[props.status] ?? props.status }}
  </span>
</template>
