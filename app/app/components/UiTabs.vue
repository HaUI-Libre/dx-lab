<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
// Tab hoặc bộ lọc với gạch chân trượt. Mũi tên trái/phải, Home, End chuyển tab theo mẫu WAI-ARIA.
interface Item { value: string; label: string; count?: number }

const props = defineProps<{ items: Item[]; label: string }>()
const model = defineModel<string>({ required: true })

const list = ref<HTMLElement>()
const style = ref<Record<string, string>>({})

function place() {
  const el = list.value?.querySelector<HTMLElement>('[aria-selected="true"]')
  if (!el) return
  style.value = { '--ix': `${el.offsetLeft}px`, '--iw': `${el.offsetWidth}` }
}

function select(value: string, focus = false) {
  model.value = value
  if (focus) nextTick(() => list.value?.querySelector<HTMLElement>('[aria-selected="true"]')?.focus())
}

function onKey(e: KeyboardEvent) {
  const i = props.items.findIndex((x) => x.value === model.value)
  const last = props.items.length - 1
  const next = { ArrowRight: i === last ? 0 : i + 1, ArrowLeft: i === 0 ? last : i - 1, Home: 0, End: last }[e.key]
  if (next === undefined) return
  e.preventDefault()
  select(props.items[next]!.value, true)
}

watch(model, () => nextTick(place))
onMounted(() => {
  place()
  // Phông tải xong có thể đổi bề rộng chữ
  document.fonts?.ready.then(place)
  window.addEventListener('resize', place, { passive: true })
})
onBeforeUnmount(() => window.removeEventListener('resize', place))
</script>

<template>
  <div ref="list" class="tabs" role="tablist" :aria-label="label" :style="style" @keydown="onKey">
    <button
      v-for="item in items" :key="item.value" class="tab" type="button" role="tab"
      :aria-selected="item.value === model" :tabindex="item.value === model ? 0 : -1"
      @click="select(item.value)"
    >
      {{ item.label }}<span v-if="item.count != null" class="tab-count">{{ item.count }}</span>
    </button>
    <span class="tabs-indicator" aria-hidden="true" />
  </div>
</template>
