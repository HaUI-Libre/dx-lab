<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Me, Ticket } from '~/utils/helpdesk'

// Danh sách ticket. Data API tự lọc theo vai trò và cơ sở trong token: sinh viên thấy
// ticket của mình, kỹ thuật viên thấy việc được giao, trưởng phòng thấy cơ sở mình.
// Từ khoá gửi lên API (tham số q, tìm trên tiêu đề và toàn bộ mô tả); trạng thái và cơ sở
// lọc trên trình duyệt trong tối đa 100 phiếu mới nhất API trả về. Bộ lọc ghi lên URL.
const { data: me } = await useFetch<Me>('/gw/api/me', { key: 'global-me', retry: false })

const isManager = computed(() => hasRole(me.value, 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'))
const isTechnician = computed(() => hasRole(me.value, 'ROLE_TECHNICIAN'))

const heading = computed(() => {
  if (isManager.value) return me.value?.co_so ? `Hàng đợi ${me.value.co_so}` : 'Hàng đợi'
  if (isTechnician.value) return 'Việc của tôi'
  return 'Yêu cầu của tôi'
})
useHead({ title: heading })

// ---- Bộ lọc gắn với URL query ----
const route = useRoute()
const router = useRouter()
const one = (v: unknown) => (Array.isArray(v) ? v[0] : v) as string | undefined

// Từ khoá đã áp dụng (sau debounce 300ms); đổi giá trị này thì useFetch gọi lại API
const applied = ref((one(route.query.q) ?? '').trim())
const listUrl = computed(() => {
  const params = new URLSearchParams({ page_size: '100' })
  if (applied.value) params.set('q', applied.value)
  return `/gw/api/data/tickets?${params}`
})

// Chỉ giữ trường danh sách dùng tới, mô tả cắt 200 ký tự: HTML và payload SSR nhẹ hơn nhiều
const LIST_FIELDS = ['id', 'title', 'status', 'category', 'priority', 'co_so', 'created_by', 'assigned_to', 'updated_at'] as const
const { data, error, pending, refresh } = useFetch<{ items: Ticket[], total: number }>(listUrl, {
  key: 'tickets-list',
  lazy: true,
  transform: (res) => ({
    total: res.total,
    items: res.items.map((t) => ({
      ...Object.fromEntries(LIST_FIELDS.map((k) => [k, t[k]])),
      description: (t.description ?? '').slice(0, 200),
    }) as Ticket),
  }),
})

const status = ref(one(route.query.trang_thai) ?? 'ALL')
const coSo = ref(one(route.query.co_so) ?? '')
const q = ref(one(route.query.q) ?? '')
const view = ref<'bang' | 'the'>(one(route.query.xem) === 'the' ? 'the' : 'bang')

let typing: ReturnType<typeof setTimeout> | undefined
function syncUrl() {
  const query: Record<string, string> = {}
  if (status.value !== 'ALL') query.trang_thai = status.value
  if (coSo.value) query.co_so = coSo.value
  if (q.value.trim()) query.q = q.value.trim()
  if (view.value === 'the') query.xem = 'the'
  router.replace({ query })
}
watch([status, coSo, view], syncUrl)
watch(q, () => {
  clearTimeout(typing)
  typing = setTimeout(() => {
    applied.value = q.value.trim()
    syncUrl()
  }, 300)
})
// Ô tìm trên header đổi ?q= khi đang ở trang này
watch(() => route.query.q, (v) => { if ((one(v) ?? '') !== q.value.trim()) q.value = one(v) ?? '' })

// Màn hẹp vẫn dùng bảng; CSS hiển thị mỗi dòng thành một khối. Không đổi chế độ xem sau
// khi tải, vì đổi sẽ dựng lại cả danh sách (tác vụ dài, LCP trễ trên điện thoại).

function clearFilters() {
  status.value = 'ALL'
  coSo.value = ''
  q.value = ''
}

const items = computed(() => data.value?.items ?? [])
const campuses = computed(() => [...new Set(items.value.map((t) => t.co_so).filter((x): x is string => !!x))].sort())

// Đếm theo trạng thái sau khi lọc cơ sở; từ khoá đã lọc ở API nên số trên tab khớp kết quả
const base = computed(() => items.value.filter((t) => !coSo.value || t.co_so === coSo.value))
const shown = computed(() => base.value.filter((t) => status.value === 'ALL' || t.status === status.value))

// Dựng từng 30 phiếu; lọc và số đếm vẫn tính trên đủ dữ liệu đã tải
const PAGE = 30
const limit = ref(PAGE)
const visible = computed(() => shown.value.slice(0, limit.value))
watch([status, coSo, applied], () => { limit.value = PAGE })
async function showMore() {
  const first = limit.value
  limit.value += PAGE
  await nextTick()
  // Focus vào phiếu đầu tiên vừa hiện để người dùng bàn phím đọc tiếp từ đó
  document.querySelector<HTMLElement>(`[data-index="${first}"] .title-link`)?.focus()
}

const tabs = computed(() => [
  { value: 'ALL', label: 'Tất cả', count: base.value.length },
  ...Object.keys(STATUS_LABELS).map((s) => ({ value: s, label: STATUS_LABELS[s]!, count: base.value.filter((t) => t.status === s).length })),
])
const hasFilter = computed(() => status.value !== 'ALL' || !!coSo.value || !!applied.value)
</script>

<template>
  <div class="page">
    <header class="page-head reveal" style="--i: 0">
      <div>
        <span class="eyebrow">Phiếu báo hỏng</span>
        <h1>{{ heading }}</h1>
        <p class="lede">
          <template v-if="isManager">Phiếu thuộc cơ sở của bạn, kể cả bản nháp bạn tự tạo.</template>
          <template v-else-if="isTechnician">Phiếu được giao cho bạn tại cơ sở của bạn, và phiếu bạn tự báo.</template>
          <template v-else>Các phiếu bạn đã tạo.</template>
        </p>
      </div>
      <NuxtLink to="/tickets/new" class="btn">Báo hỏng thiết bị</NuxtLink>
    </header>

    <section class="card reveal" style="--i: 1" aria-label="Bộ lọc và danh sách phiếu">
      <div class="toolbar">
        <div class="search-field">
          <label class="visually-hidden" for="list-q">Tìm trong tiêu đề và mô tả</label>
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>
          <input id="list-q" v-model="q" class="input" type="search" placeholder="Tìm trong tiêu đề và mô tả" autocomplete="off">
        </div>
        <div v-if="campuses.length > 1" class="field-inline">
          <label for="list-coso">Cơ sở</label>
          <select id="list-coso" v-model="coSo" class="input">
            <option value="">Tất cả</option>
            <option v-for="c in campuses" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="view-switch" role="group" aria-label="Chế độ xem">
          <button type="button" :aria-pressed="view === 'bang'" title="Xem dạng bảng" @click="view = 'bang'">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
            <span>Bảng</span>
          </button>
          <button type="button" :aria-pressed="view === 'the'" title="Xem dạng thẻ" @click="view = 'the'">
            <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="7" height="7" rx="1.5" /><rect x="13" y="4" width="7" height="7" rx="1.5" /><rect x="4" y="13" width="7" height="7" rx="1.5" /><rect x="13" y="13" width="7" height="7" rx="1.5" /></svg>
            <span>Thẻ</span>
          </button>
        </div>
      </div>

      <UiTabs v-model="status" :items="tabs" label="Lọc theo trạng thái" />

      <!-- Đang tải: khung xương theo đúng hình hàng của bảng -->
      <div v-if="pending && !data" class="results" aria-busy="true" aria-label="Đang tải danh sách phiếu">
        <div v-for="n in 5" :key="n" class="skel-row">
          <span class="skeleton" style="width: 5.5rem; height: 1.5rem" />
          <span class="skeleton" style="flex: 1; height: 1rem" />
          <span class="skeleton" style="width: 9rem; height: 1.6rem" />
          <span class="skeleton skel-hide" style="width: 6rem; height: 1rem" />
        </div>
      </div>

      <div v-else-if="error" class="empty results" role="alert">
        <span class="empty-title">Không tải được danh sách</span>
        <p>{{ errorMessage(error) }}</p>
        <button class="btn secondary" type="button" :aria-busy="pending" @click="refresh()">Thử lại</button>
      </div>

      <div v-else-if="!items.length" class="empty results">
        <svg class="empty-icon" viewBox="0 0 48 48" aria-hidden="true"><rect x="8" y="10" width="32" height="28" rx="4" /><path d="M8 18h32M16 26h10M16 31h16" /></svg>
        <span class="empty-title">Chưa có phiếu nào</span>
        <p v-if="isTechnician && !isManager">Khi trưởng phòng giao việc cho bạn, phiếu sẽ hiện ở đây.</p>
        <p v-else>Khi thiết bị trong phòng lab gặp sự cố, tạo phiếu để kỹ thuật viên xử lý.</p>
        <NuxtLink to="/tickets/new" class="btn">Báo hỏng thiết bị</NuxtLink>
      </div>

      <div v-else-if="!shown.length" class="empty results">
        <span class="empty-title">Không có phiếu khớp bộ lọc</span>
        <p>Thử bỏ bớt điều kiện hoặc tìm bằng từ khác.</p>
        <button class="btn secondary" type="button" @click="clearFilters">Xoá bộ lọc</button>
      </div>

      <div v-else-if="view === 'bang'" class="table-wrap results">
        <!-- role tường minh: màn hẹp đổi display của bảng, trình duyệt có thể bỏ ngữ nghĩa bảng -->
        <table class="table stacked" role="table" aria-label="Danh sách phiếu">
          <thead role="rowgroup">
            <tr role="row">
              <th scope="col" role="columnheader">Mã</th>
              <th scope="col" role="columnheader">Tiêu đề</th>
              <th scope="col" role="columnheader">Trạng thái</th>
              <th scope="col" role="columnheader">Loại</th>
              <th scope="col" role="columnheader">Ưu tiên</th>
              <th scope="col" role="columnheader">Cơ sở</th>
              <th scope="col" role="columnheader">Cập nhật</th>
            </tr>
          </thead>
          <TransitionGroup tag="tbody" name="row" role="rowgroup">
            <tr v-for="(t, i) in visible" :key="t.id" role="row" :data-index="i">
              <td role="cell" data-label="Mã"><span class="code">{{ ticketCode(t.id) }}</span></td>
              <td role="cell" data-label="Tiêu đề"><NuxtLink :to="`/tickets/${t.id}`" class="title-link">{{ t.title }}</NuxtLink></td>
              <td role="cell" data-label="Trạng thái"><StatusStamp :status="t.status" /></td>
              <td role="cell" data-label="Loại">{{ t.category ? CATEGORY_LABELS[t.category] : '' }}</td>
              <td role="cell" data-label="Ưu tiên"><span class="priority" :data-priority="t.priority">{{ t.priority ? PRIORITY_LABELS[t.priority] : '' }}</span></td>
              <td role="cell" data-label="Cơ sở"><span v-if="t.co_so" class="code">{{ t.co_so }}</span></td>
              <td role="cell" data-label="Cập nhật" class="nowrap">{{ formatTime(t.updated_at) }}</td>
            </tr>
          </TransitionGroup>
        </table>
      </div>

      <TransitionGroup v-else tag="ul" name="row" class="cards results">
        <li v-for="(t, i) in visible" :key="t.id" class="ticket-card" :data-index="i">
          <div class="ticket-card-top">
            <span class="code">{{ ticketCode(t.id) }}</span>
            <StatusStamp :status="t.status" />
          </div>
          <NuxtLink :to="`/tickets/${t.id}`" class="title-link ticket-card-title">{{ t.title }}</NuxtLink>
          <dl class="ticket-meta">
            <div v-if="t.category"><dt>Loại</dt><dd>{{ CATEGORY_LABELS[t.category] }}</dd></div>
            <div v-if="t.priority"><dt>Ưu tiên</dt><dd class="priority" :data-priority="t.priority">{{ PRIORITY_LABELS[t.priority] }}</dd></div>
            <div v-if="t.co_so"><dt>Cơ sở</dt><dd><span class="code">{{ t.co_so }}</span></dd></div>
            <div><dt>Cập nhật</dt><dd>{{ formatTime(t.updated_at) }}</dd></div>
          </dl>
        </li>
      </TransitionGroup>

      <div v-if="shown.length > visible.length" class="more">
        <button class="btn secondary" type="button" @click="showMore">Hiện thêm {{ Math.min(PAGE, shown.length - visible.length) }}</button>
      </div>

      <p v-if="data" class="count" aria-live="polite">
        Đang hiện {{ visible.length }} trên {{ shown.length }} phiếu<template v-if="hasFilter"> khớp bộ lọc (đã tải {{ items.length }})</template>
        <template v-if="data.total > items.length">. Đang lọc trong {{ items.length }} phiếu mới nhất trên tổng {{ data.total }}.</template>
      </p>
    </section>
  </div>
</template>

<style scoped>
/* minmax(0, 1fr): cột không nở theo dải tab hay bảng cột bên trong, tránh tràn ngang */
.page { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-5); }

.page-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  gap: var(--space-4);
}

.page-head h1 { margin-top: var(--space-1); }
.page-head .lede { margin: 0; font-size: var(--text-base); }

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
  margin-bottom: var(--space-3);
}

.search-field { position: relative; flex: 1 1 16rem; }
.search-field svg { position: absolute; left: var(--space-3); top: 50%; width: 1.1rem; height: 1.1rem; transform: translateY(-50%); fill: none; stroke: var(--ink-soft); stroke-width: 2; stroke-linecap: round; }
.search-field .input { padding-left: 2.5rem; }

.field-inline { display: flex; align-items: center; gap: var(--space-2); font-weight: 700; font-size: var(--text-sm); }
.field-inline .input { width: auto; min-width: 7rem; }

.view-switch { display: inline-flex; border: 1px solid var(--line); border-radius: var(--radius-control); overflow: hidden; }
.view-switch button {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  min-height: 2.75rem;
  padding: 0 var(--space-3);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--ink-soft);
  background: var(--card);
  border: 0;
  cursor: pointer;
  transition: color var(--dur-fast), background-color var(--dur-fast);
}
.view-switch button + button { border-left: 1px solid var(--line); }
.view-switch button[aria-pressed="true"] { color: var(--on-primary); background: var(--primary); }
.view-switch svg { width: 1rem; height: 1rem; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }

.results { margin-top: var(--space-4); }

.skel-row { display: flex; gap: var(--space-4); align-items: center; padding: var(--space-3) var(--space-2); border-top: 1px solid var(--rule); }
.skel-row:first-child { border-top: 0; }
.empty-icon { width: 3rem; height: 3rem; fill: none; stroke: var(--brand-ink); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

.title-link { font-weight: 700; color: var(--ink); text-decoration: none; }
.title-link:hover { color: var(--brand-ink); text-decoration: underline; }
.nowrap { white-space: nowrap; }
.priority[data-priority="URGENT"],
.priority[data-priority="HIGH"] { font-weight: 800; color: var(--brand-ink); }

.cards { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(17rem, 1fr)); gap: var(--space-3); }
.ticket-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--card);
  border: 1px solid var(--rule);
  border-radius: var(--radius-card);
  transition: border-color var(--dur-fast), transform var(--dur-fast) var(--ease-out);
}
.ticket-card:hover { border-color: color-mix(in srgb, var(--brand) 45%, var(--rule)); transform: translateY(-2px); }
.ticket-card-top { display: flex; justify-content: space-between; align-items: center; gap: var(--space-2); flex-wrap: wrap; }
.ticket-card-title { font-size: var(--text-lg); line-height: 1.35; }
.ticket-meta { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2) var(--space-4); margin: var(--space-1) 0 0; font-size: var(--text-sm); }
.ticket-meta dt { color: var(--ink-soft); font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.ticket-meta dd { margin: 0; }

.count { margin: var(--space-4) 0 0; font-size: var(--text-sm); color: var(--ink-soft); }
.more { display: flex; justify-content: center; margin-top: var(--space-4); }

/* Dòng thêm hoặc bớt khi lọc. Bảng không dùng position absolute lúc rời để giữ cột thẳng. */
.row-enter-active { transition: opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-out); }
.row-leave-active { transition: opacity var(--dur-fast) var(--ease-out); }
.row-enter-from { opacity: 0; transform: translateY(-6px); }
.row-leave-to { opacity: 0; }
.row-move { transition: transform var(--dur) var(--ease-out); }

@media (max-width: 48rem) {
  /* Bảng thành khối: mỗi dòng một khối, nhãn cột lấy từ data-label. Đầu bảng ẩn bằng kỹ thuật
     visually-hidden để trình đọc màn hình vẫn có tên cột cho từng ô. */
  .table.stacked { min-width: 0; }
  .table.stacked thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .table.stacked,
  .table.stacked tbody,
  .table.stacked tr,
  .table.stacked td { display: block; }
  .table.stacked tr { padding: var(--space-3) var(--space-4); border-top: 1px solid var(--rule); }
  .table.stacked tbody tr:first-child { border-top: 0; }
  .table.stacked td { display: grid; grid-template-columns: 6.5rem minmax(0, 1fr); gap: var(--space-2); align-items: center; padding: var(--space-1) 0; border: 0; }
  .table.stacked td:empty { display: none; }
  /* Chuỗi alt rỗng sau dấu "/": nhãn chỉ để nhìn, trình đọc màn hình đã có tên cột */
  .table.stacked td::before { content: attr(data-label); content: attr(data-label) / ""; font-size: var(--text-xs); font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; color: var(--ink-soft); }
  .table.stacked td.nowrap { white-space: normal; }
  .view-switch span { display: none; }
  .skel-hide { display: none; }
  .field-inline { flex: 1 1 auto; }
  .field-inline .input { flex: 1; }
}
</style>
