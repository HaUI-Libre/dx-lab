<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
// Biểu đồ cột SVG tự vẽ, không thư viện. Cột mọc lên lần lượt khi tải; hover hoặc Tab vào cột
// hiện tooltip với giá trị chính xác. Có bảng ẩn cho trình đọc màn hình.
interface Item { code: string, label: string, n: number }
const props = defineProps<{ items: Item[], title: string, highlight?: string[] }>()

const W = 320
const H = 180
const PAD = { top: 16, bottom: 4, side: 8 }
const max = computed(() => Math.max(1, ...props.items.map(i => i.n)))
const bars = computed(() => {
  const n = Math.max(1, props.items.length)
  const slot = (W - PAD.side * 2) / n
  const width = Math.min(44, slot * 0.62)
  return props.items.map((item, i) => {
    const h = Math.max(2, ((H - PAD.top - PAD.bottom) * item.n) / max.value)
    return { ...item, x: PAD.side + slot * i + (slot - width) / 2, y: H - PAD.bottom - h, w: width, h, cx: PAD.side + slot * (i + 0.5) }
  })
})
// Ba vạch lưới ngang ở 1/3, 2/3 và đỉnh
const grid = computed(() => [1, 2, 3].map(k => ({ y: H - PAD.bottom - ((H - PAD.top - PAD.bottom) * k) / 3, v: Math.round((max.value * k) / 3) })))

const tip = ref<{ x: number, y: number, label: string, n: number } | null>(null)
function showTip(b: (typeof bars.value)[number]) {
  tip.value = { x: (b.cx / W) * 100, y: (b.y / H) * 100, label: b.label, n: b.n }
}
</script>

<template>
  <figure class="chart">
    <figcaption>{{ title }}</figcaption>
    <div class="plot" @mouseleave="tip = null">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="`${title}: ${items.map(i => `${i.label} ${i.n}`).join(', ')}`" preserveAspectRatio="none">
        <g class="grid" aria-hidden="true">
          <line v-for="g in grid" :key="g.y" :x1="0" :x2="W" :y1="g.y" :y2="g.y" />
          <line :x1="0" :x2="W" :y1="H - PAD.bottom" :y2="H - PAD.bottom" class="base" />
        </g>
        <g
          v-for="(b, i) in bars" :key="b.code" class="bar" :class="{ hot: highlight?.includes(b.code) }"
          :style="{ '--i': i, transformOrigin: `${b.cx}px ${H - PAD.bottom}px` }"
          tabindex="0" :aria-label="`${b.label}: ${b.n}`"
          @mouseenter="showTip(b)" @focus="showTip(b)" @blur="tip = null"
        >
          <rect class="hit" :x="b.cx - (W / Math.max(1, items.length)) / 2" :y="0" :width="W / Math.max(1, items.length)" :height="H" />
          <rect class="col" :x="b.x" :y="b.y" :width="b.w" :height="b.h" rx="4" />
        </g>
      </svg>
      <Transition name="tip">
        <div v-if="tip" class="tip" :style="{ left: `${tip.x}%`, top: `${tip.y}%` }" aria-hidden="true">
          <strong>{{ tip.n }}</strong> {{ tip.label }}
        </div>
      </Transition>
    </div>
    <ol class="legend" aria-hidden="true">
      <li v-for="b in bars" :key="b.code"><span class="legend-n">{{ b.n }}</span>{{ b.label }}</li>
    </ol>
  </figure>
</template>

<style scoped>
.chart { margin: 0; display: grid; gap: var(--space-3); min-width: 0; }
figcaption { font-family: var(--font-display); font-weight: 600; font-size: var(--text-lg); }
.plot { position: relative; height: 12rem; }
svg { display: block; width: 100%; height: 100%; overflow: visible; }
.grid line { stroke: var(--rule); stroke-width: 1; vector-effect: non-scaling-stroke; }
.grid .base { stroke: var(--line); }

.bar { cursor: default; outline: none; }
.bar .hit { fill: transparent; }
.col {
  fill: color-mix(in srgb, var(--brand) 55%, var(--card));
  transition: fill var(--dur-fast);
}
.bar.hot .col { fill: var(--brand); }
.bar:hover .col,
.bar:focus-visible .col { fill: var(--primary); }
.bar:focus-visible .hit { fill: color-mix(in srgb, var(--brand) 10%, transparent); stroke: var(--focus); stroke-width: 2; vector-effect: non-scaling-stroke; }

/* Cột mọc lên từ trục đáy, lần lượt */
.bar { animation: grow var(--dur-slow) var(--ease-out) both; animation-delay: calc(var(--i) * 70ms + 120ms); }
@keyframes grow { from { transform: scaleY(0); } to { transform: scaleY(1); } }

.tip {
  position: absolute;
  z-index: 2;
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-sm);
  white-space: nowrap;
  color: var(--card);
  background: var(--ink);
  border-radius: var(--radius-control);
  pointer-events: none;
  transform: translate(-50%, calc(-100% - 8px));
}
.tip strong { font-family: var(--font-mono); }
.tip-enter-active, .tip-leave-active { transition: opacity var(--dur-fast); }
.tip-enter-from, .tip-leave-to { opacity: 0; }

.legend { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-4); font-size: var(--text-sm); color: var(--ink-soft); }
.legend-n { font-family: var(--font-mono); font-weight: 700; color: var(--ink); margin-right: var(--space-1); }
</style>
