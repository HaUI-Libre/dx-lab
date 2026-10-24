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

const SITE_LABELS: Record<string, string> = { CS1: 'Cơ sở 1', CS2: 'Cơ sở 2', CS3: 'Cơ sở 3' }
const scope = computed(() => (isAdmin.value ? (site.value ? SITE_LABELS[site.value] : 'toàn trường') : (me.value?.co_so ? SITE_LABELS[me.value.co_so] : '')))
useHead({ title: computed(() => `Thống kê ${scope.value}`) })

// Giữ thứ tự vòng đời cho trạng thái; loại và cơ sở xếp theo số lượng
function series(counts: Record<string, number> | undefined, labels: Record<string, string>, order?: string[]) {
  const entries = Object.entries(counts ?? {}).filter(([, n]) => n > 0)
  const sorted = order ? entries.sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0])) : entries.sort((a, b) => b[1] - a[1])
  return sorted.map(([code, n]) => ({ code, label: labels[code] ?? code, n }))
}
const statusSeries = computed(() => series(stats.value?.by_status, STATUS_LABELS, Object.keys(STATUS_LABELS)))
const categorySeries = computed(() => series(stats.value?.by_category, CATEGORY_LABELS))
const siteSeries = computed(() => series(stats.value?.by_co_so, SITE_LABELS, Object.keys(SITE_LABELS)))
const open = computed(() => ['SUBMITTED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED'].reduce((n, s) => n + (stats.value?.by_status?.[s] ?? 0), 0))
const notImplemented = computed(() => [404, 405, 501, 502, 503].includes(error.value?.statusCode ?? 0))
</script>

<template>
  <div class="page">
    <header class="page-head reveal" style="--i: 0">
      <div>
        <span class="eyebrow">Dữ liệu số</span>
        <h1>Thống kê {{ scope }}</h1>
        <p class="lede">Số phiếu theo trạng thái, loại và cơ sở; thời gian xử lý trung bình; số quá hạn và số lần mở lại.</p>
      </div>
      <div class="tools">
        <div v-if="isAdmin" class="field-inline">
          <label for="d-site">Cơ sở</label>
          <select id="d-site" v-model="site" class="input">
            <option value="">Cả ba cơ sở</option>
            <option v-for="(label, code) in SITE_LABELS" :key="code" :value="code">{{ label }}</option>
          </select>
        </div>
        <button v-if="allowed" class="btn secondary" type="button" :aria-busy="pending" @click="refresh()">Làm mới</button>
      </div>
    </header>

    <section v-if="!allowed" class="card empty reveal" style="--i: 1" role="alert">
      <span class="empty-title">Không có quyền xem</span>
      <p>Chỉ trưởng phòng lab và quản trị hệ thống xem được thống kê.</p>
      <NuxtLink to="/tickets" class="btn secondary">Về danh sách phiếu</NuxtLink>
    </section>

    <div v-else-if="pending && !stats" class="kpis" aria-busy="true" aria-label="Đang tải thống kê">
      <div v-for="n in 4" :key="n" class="card kpi"><span class="skeleton" style="width: 4rem; height: 2.5rem" /><span class="skeleton" style="width: 9rem; height: 0.9rem" /></div>
    </div>

    <section v-else-if="notImplemented" class="card empty reveal" style="--i: 1" role="status">
      <span class="empty-title">Chưa có API thống kê</span>
      <p>Trang sẽ hiện số liệu khi Data API trả về <code class="code">GET /api/data/stats</code> (#22).</p>
    </section>

    <section v-else-if="error" class="card empty reveal" style="--i: 1" role="alert">
      <span class="empty-title">Không tải được thống kê</span>
      <p>{{ errorMessage(error) }}</p>
      <button class="btn secondary" type="button" :aria-busy="pending" @click="refresh()">Thử lại</button>
    </section>

    <template v-else-if="stats">
      <div class="kpis">
        <div class="card kpi reveal" style="--i: 1">
          <span class="kpi-value"><CountUp :value="stats.total" /></span>
          <span class="kpi-label">Tổng phiếu</span>
        </div>
        <div class="card kpi reveal" style="--i: 2">
          <span class="kpi-value"><CountUp :value="open" /></span>
          <span class="kpi-label">Đang mở (chờ tiếp nhận tới chờ nghiệm thu)</span>
        </div>
        <div class="card kpi reveal" style="--i: 3">
          <span class="kpi-value"><CountUp :value="stats.average_resolution_hours" :decimals="1" /><small v-if="stats.average_resolution_hours != null"> giờ</small></span>
          <span class="kpi-label">Xử lý trung bình, từ gửi tới hoàn thành</span>
        </div>
        <div class="card kpi reveal" :class="{ alert: stats.overdue_count > 0 }" style="--i: 4">
          <span class="kpi-value"><CountUp :value="stats.overdue_count" /></span>
          <span class="kpi-label">Quá hạn SLA, chưa đóng</span>
        </div>
        <div v-if="stats.reopen_count != null" class="card kpi reveal" style="--i: 5">
          <span class="kpi-value"><CountUp :value="stats.reopen_count" /></span>
          <span class="kpi-label">Lần mở lại</span>
        </div>
      </div>

      <div class="charts">
        <section class="card reveal" style="--i: 5">
          <BarChart v-if="statusSeries.length" :items="statusSeries" title="Theo trạng thái" :highlight="['IN_PROGRESS']" />
          <p v-else class="hint">Chưa có phiếu nào.</p>
        </section>
        <section class="card reveal" style="--i: 6">
          <BarChart v-if="categorySeries.length" :items="categorySeries" title="Theo loại sự cố" />
          <p v-else class="hint">Chưa có phiếu nào được phân loại.</p>
        </section>
        <section v-if="siteSeries.length" class="card reveal" style="--i: 7">
          <BarChart :items="siteSeries" title="Theo cơ sở" />
        </section>
      </div>
      <p class="source">Số liệu từ <code class="code">GET /api/data/stats</code> qua API Gateway.</p>
    </template>
  </div>
</template>

<style scoped>
.page { display: grid; gap: var(--space-5); }
.page-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-end; gap: var(--space-4); }
.page-head h1 { margin-top: var(--space-1); }
.page-head .lede { margin: 0; font-size: var(--text-base); }
.tools { display: flex; flex-wrap: wrap; gap: var(--space-3); align-items: center; }
.field-inline { display: flex; align-items: center; gap: var(--space-2); font-weight: 700; font-size: var(--text-sm); }
.field-inline .input { width: auto; }

.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: var(--space-4); }
.kpi { display: grid; gap: var(--space-2); align-content: start; }
.kpi-value { font-family: var(--font-display); font-weight: var(--weight-heavy); font-size: 2.75rem; line-height: 1; letter-spacing: -0.02em; }
.kpi-value small { font-size: var(--text-base); font-weight: 600; color: var(--ink-soft); }
.kpi-label { font-size: var(--text-sm); color: var(--ink-soft); }
.kpi.alert { box-shadow: inset 4px 0 0 var(--brand-ink), var(--shadow); }
.kpi.alert .kpi-value { color: var(--brand-ink); }

.charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr)); gap: var(--space-4); }
.hint { margin: 0; color: var(--ink-soft); }
.source { margin: 0; font-size: var(--text-sm); color: var(--ink-soft); }
</style>
