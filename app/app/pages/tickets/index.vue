<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Me, Ticket } from '~/utils/helpdesk'

// Danh sách ticket. Data API tự lọc theo vai trò và cơ sở trong token: sinh viên thấy
// ticket của mình, kỹ thuật viên thấy việc được giao, trưởng phòng thấy cơ sở mình.
const { data: me } = await useFetch<Me>('/gw/api/me', { key: 'global-me', retry: false })

const isManager = computed(() => hasRole(me.value, 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'))
const isTechnician = computed(() => hasRole(me.value, 'ROLE_TECHNICIAN'))

const heading = computed(() => {
  if (isManager.value) return me.value?.co_so ? `Hàng đợi ${me.value.co_so}` : 'Hàng đợi'
  if (isTechnician.value) return 'Việc của tôi'
  return 'Yêu cầu của tôi'
})

const status = ref<string>('')
const q = ref('')
const query = computed(() => {
  const params = new URLSearchParams({ page_size: '100' })
  if (status.value) params.set('status', status.value)
  if (q.value.trim()) params.set('q', q.value.trim())
  return params.toString()
})

const { data, error, pending, refresh } = await useFetch<{ items: Ticket[], total: number }>(
  () => `/gw/api/data/tickets?${query.value}`,
  { key: 'tickets-list', watch: false },
)
watch(status, () => refresh())
</script>

<template>
  <section class="card">
    <div class="head">
      <div>
        <h1>{{ heading }}</h1>
        <p class="muted">
          <template v-if="isManager">Ticket thuộc cơ sở của bạn, kể cả bản nháp bạn tự tạo.</template>
          <template v-else-if="isTechnician">Ticket được giao cho bạn tại cơ sở của bạn, và ticket bạn tự báo.</template>
          <template v-else>Các yêu cầu bạn đã tạo.</template>
        </p>
      </div>
      <NuxtLink to="/tickets/new" class="btn">Báo hỏng thiết bị</NuxtLink>
    </div>

    <form class="filters" @submit.prevent="refresh()">
      <label>
        Trạng thái
        <select v-model="status">
          <option value="">Tất cả</option>
          <option v-for="(label, code) in STATUS_LABELS" :key="code" :value="code">{{ label }}</option>
        </select>
      </label>
      <label class="grow">
        Tìm trong tiêu đề, mô tả
        <input v-model="q" type="search" placeholder="Ví dụ: PC-04, máy chiếu">
      </label>
      <button class="btn secondary" type="submit">Tìm</button>
    </form>

    <p v-if="pending" class="muted">Đang tải…</p>
    <p v-else-if="error" class="notice danger" role="alert">
      Không tải được danh sách: {{ errorMessage(error) }}
    </p>
    <p v-else-if="!data?.items.length" class="muted">Chưa có ticket nào.</p>
    <table v-else class="list">
      <thead>
        <tr>
          <th>Tiêu đề</th>
          <th>Trạng thái</th>
          <th>Loại</th>
          <th>Ưu tiên</th>
          <th>Cơ sở</th>
          <th>Cập nhật</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in data.items" :key="t.id">
          <td><NuxtLink :to="`/tickets/${t.id}`">{{ t.title }}</NuxtLink></td>
          <td><span class="status" :data-status="t.status">{{ STATUS_LABELS[t.status] ?? t.status }}</span></td>
          <td>{{ t.category ? CATEGORY_LABELS[t.category] : '' }}</td>
          <td>{{ t.priority ? PRIORITY_LABELS[t.priority] : '' }}</td>
          <td>{{ t.co_so ?? '' }}</td>
          <td class="nowrap">{{ formatTime(t.updated_at) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="data" class="muted small">{{ data.total }} ticket</p>
  </section>
</template>

<style scoped>
h1 { margin: 0 0 0.25rem; font-size: 1.5rem; }
.head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
.filters { display: flex; gap: 0.75rem; align-items: flex-end; flex-wrap: wrap; margin-bottom: 1rem; }
.filters label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.875rem; color: var(--muted); }
.filters .grow { flex: 1; min-width: 12rem; }
select, input { font: inherit; padding: 0.5rem; border: 1px solid var(--border); border-radius: 0.375rem; background: var(--surface); color: var(--text); }
.list { width: 100%; border-collapse: collapse; font-size: 0.9375rem; }
.list th, .list td { text-align: left; padding: 0.5rem; border-bottom: 1px solid var(--border); vertical-align: top; }
.list th { color: var(--muted); font-weight: 600; font-size: 0.8125rem; }
.list a { color: var(--accent); font-weight: 600; text-decoration: none; }
.nowrap { white-space: nowrap; }
.muted { color: var(--muted); }
.small { font-size: 0.875rem; }
.notice { padding: 0.75rem 1rem; border-radius: 0.375rem; }
.notice.danger { background: var(--danger-bg); color: var(--danger-text); }
.status { font-size: 0.8125rem; font-weight: 600; padding: 0.1rem 0.45rem; border-radius: 0.25rem; background: var(--bg); border: 1px solid var(--border); white-space: nowrap; }
.status[data-status="CLOSED"] { color: #107c41; }
.status[data-status="REJECTED"] { color: var(--danger-text); }
.status[data-status="RESOLVED"] { color: var(--warn-text); }
@media (max-width: 40rem) {
  .list thead { display: none; }
  .list tr { display: block; border-bottom: 1px solid var(--border); padding: 0.5rem 0; }
  .list td { display: inline-block; border: 0; padding: 0.125rem 0.5rem 0.125rem 0; }
  .list td:first-child { display: block; }
}
</style>
