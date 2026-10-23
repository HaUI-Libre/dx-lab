<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Me, TicketStats } from '~/utils/helpdesk'

// Không gian Dữ liệu số: số liệu tổng hợp theo cơ sở (#27). Data API lọc theo claim
// co_so: trưởng phòng chỉ nhận cơ sở mình, admin chọn cơ sở hoặc xem cả ba.
const { data: me } = await useFetch<Me>('/gw/api/me', { key: 'global-me', retry: false })
const isAdmin = computed(() => hasRole(me.value, 'ROLE_ADMIN'))
const allowed = computed(() => hasRole(me.value, 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'))

const site = ref('')
const query = computed(() => (isAdmin.value && site.value ? `?co_so=${site.value}` : ''))
const { data: stats, error, pending, refresh } = await useFetch<TicketStats>(
  () => `/gw/api/data/stats${query.value}`,
  { key: 'stats', watch: false, immediate: allowed.value },
)
watch(site, () => refresh())

// Biểu đồ thanh vẽ bằng CSS: số liệu ít, không cần thêm thư viện biểu đồ
function bars(counts: Record<string, number> | undefined, labels: Record<string, string>) {
  const entries = Object.entries(counts ?? {}).filter(([, n]) => n > 0)
  const max = Math.max(1, ...entries.map(([, n]) => n))
  return entries.sort((a, b) => b[1] - a[1])
    .map(([code, n]) => ({ code, label: labels[code] ?? code, n, width: `${Math.round((n / max) * 100)}%` }))
}
const SITE_LABELS: Record<string, string> = { CS1: 'Cơ sở 1', CS2: 'Cơ sở 2', CS3: 'Cơ sở 3' }
const statusBars = computed(() => bars(stats.value?.by_status, STATUS_LABELS))
const categoryBars = computed(() => bars(stats.value?.by_category, CATEGORY_LABELS))
const siteBars = computed(() => bars(stats.value?.by_co_so, SITE_LABELS))
const notImplemented = computed(() => [404, 405, 501, 502, 503].includes(error.value?.statusCode ?? 0))
</script>

<template>
  <section class="card">
    <div class="head">
      <div>
        <h1>Thống kê {{ isAdmin ? (site ? SITE_LABELS[site] : 'toàn trường') : (me?.co_so ? SITE_LABELS[me.co_so] : '') }}</h1>
        <p class="muted">Số ticket theo trạng thái, loại và cơ sở; thời gian xử lý trung bình; số quá hạn và số lần mở lại.</p>
      </div>
      <div class="tools">
        <label v-if="isAdmin">
          Cơ sở
          <select v-model="site">
            <option value="">Cả ba cơ sở</option>
            <option v-for="(label, code) in SITE_LABELS" :key="code" :value="code">{{ label }}</option>
          </select>
        </label>
        <button v-if="allowed" class="btn secondary" type="button" @click="refresh()">Làm mới</button>
      </div>
    </div>

    <p v-if="!allowed" class="notice warn" role="alert">
      Chỉ trưởng phòng lab và quản trị hệ thống xem được thống kê.
    </p>
    <p v-else-if="pending" class="muted">Đang tải…</p>
    <p v-else-if="notImplemented" class="notice warn" role="status">
      Chưa có API thống kê (<code>GET /api/data/stats</code>, #22). Trang sẽ hiện số liệu khi Data API trả về.
    </p>
    <p v-else-if="error" class="notice danger" role="alert">Không tải được thống kê: {{ errorMessage(error) }}</p>

    <template v-else-if="stats">
      <div class="kpis">
        <div class="kpi"><span class="value">{{ stats.total }}</span><span class="muted small">Tổng ticket</span></div>
        <div class="kpi">
          <span class="value">{{ stats.average_resolution_hours == null ? '–' : stats.average_resolution_hours.toFixed(1) }}</span>
          <span class="muted small">Giờ xử lý trung bình (gửi tới hoàn thành)</span>
        </div>
        <div class="kpi" :class="{ alert: stats.overdue_count > 0 }">
          <span class="value">{{ stats.overdue_count }}</span><span class="muted small">Quá hạn SLA, chưa đóng</span>
        </div>
        <div v-if="stats.reopen_count != null" class="kpi">
          <span class="value">{{ stats.reopen_count }}</span><span class="muted small">Lần mở lại</span>
        </div>
      </div>

      <div class="charts">
        <figure>
          <figcaption>Theo trạng thái</figcaption>
          <ul class="bars">
            <li v-for="b in statusBars" :key="b.code">
              <span class="label">{{ b.label }}</span>
              <span class="bar" :style="{ width: b.width }" :data-status="b.code" />
              <span class="n">{{ b.n }}</span>
            </li>
          </ul>
        </figure>
        <figure>
          <figcaption>Theo loại sự cố</figcaption>
          <ul class="bars">
            <li v-for="b in categoryBars" :key="b.code">
              <span class="label">{{ b.label }}</span><span class="bar" :style="{ width: b.width }" /><span class="n">{{ b.n }}</span>
            </li>
          </ul>
        </figure>
        <figure v-if="siteBars.length">
          <figcaption>Theo cơ sở</figcaption>
          <ul class="bars">
            <li v-for="b in siteBars" :key="b.code">
              <span class="label">{{ b.label }}</span><span class="bar" :style="{ width: b.width }" /><span class="n">{{ b.n }}</span>
            </li>
          </ul>
        </figure>
      </div>
      <p class="muted small">Số liệu từ <code>GET /api/data/stats</code> qua API Gateway.</p>
    </template>
  </section>
</template>

<style scoped>
h1 { margin: 0 0 0.25rem; font-size: 1.5rem; }
.head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
.tools { display: flex; gap: 0.5rem; align-items: flex-end; flex-wrap: wrap; }
.tools label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.875rem; color: var(--muted); }
select { font: inherit; padding: 0.5rem; border: 1px solid var(--border); border-radius: 0.375rem; background: var(--surface); color: var(--text); }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem; }
.kpi { display: flex; flex-direction: column; gap: 0.25rem; padding: 0.875rem; border: 1px solid var(--border); border-radius: 0.5rem; background: var(--bg); }
.kpi .value { font-size: 1.75rem; font-weight: 700; }
.kpi.alert .value { color: var(--danger-text); }
.charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 1rem; }
figure { margin: 0; padding: 0.875rem; border: 1px solid var(--border); border-radius: 0.5rem; }
figcaption { font-weight: 700; margin-bottom: 0.5rem; }
.bars { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.375rem; }
.bars li { display: grid; grid-template-columns: 9rem 1fr 2.5rem; align-items: center; gap: 0.5rem; font-size: 0.875rem; }
.bar { height: 0.75rem; border-radius: 0.25rem; background: var(--accent); min-width: 2px; }
.bar[data-status="REJECTED"] { background: var(--danger-text); }
.bar[data-status="CLOSED"] { background: #107c41; }
.n { text-align: right; font-variant-numeric: tabular-nums; }
.muted { color: var(--muted); }
.small { font-size: 0.8125rem; }
.notice { padding: 0.75rem 1rem; border-radius: 0.375rem; }
.notice.danger { background: var(--danger-bg); color: var(--danger-text); }
.notice.warn { background: var(--warn-bg); color: var(--warn-text); }
</style>
