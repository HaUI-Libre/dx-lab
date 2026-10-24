<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Me, Ticket } from '~/utils/helpdesk'

// Danh sách ticket. Data API tự lọc theo vai trò và cơ sở trong token: sinh viên thấy
// ticket của mình, kỹ thuật viên thấy việc được giao, trưởng phòng thấy cơ sở mình.
// Bộ lọc trạng thái, cơ sở, từ khoá chạy trên trình duyệt trong tối đa 100 phiếu mới nhất
// mà API trả về; bộ lọc ghi lên URL để chia sẻ được.
const { data: me } = await useFetch<Me>('/gw/api/me', { key: 'global-me', retry: false })

const isManager = computed(() => hasRole(me.value, 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'))
const isTechnician = computed(() => hasRole(me.value, 'ROLE_TECHNICIAN'))

const heading = computed(() => {
  if (isManager.value) return me.value?.co_so ? `Hàng đợi ${me.value.co_so}` : 'Hàng đợi'
  if (isTechnician.value) return 'Việc của tôi'
  return 'Yêu cầu của tôi'
})
useHead({ title: heading })

const { data, error, pending, refresh } = useFetch<{ items: Ticket[], total: number }>(
  '/gw/api/data/tickets?page_size=100',
  { key: 'tickets-list', lazy: true },
)

// ---- Bộ lọc gắn với URL query ----
const route = useRoute()
const router = useRouter()
const one = (v: unknown) => (Array.isArray(v) ? v[0] : v) as string | undefined

const status = ref(one(route.query.trang_thai) ?? 'ALL')
const coSo = ref(one(route.query.co_so) ?? '')
const q = ref(one(route.query.q) ?? '')
const VIEWS = ['bang', 'the', 'cot'] as const
const view = ref<(typeof VIEWS)[number]>((VIEWS as readonly string[]).includes(one(route.query.xem) ?? '') ? one(route.query.xem) as (typeof VIEWS)[number] : 'bang')

let typing: ReturnType<typeof setTimeout> | undefined
function syncUrl() {
  const query: Record<string, string> = {}
  if (status.value !== 'ALL') query.trang_thai = status.value
  if (coSo.value) query.co_so = coSo.value
  if (q.value.trim()) query.q = q.value.trim()
  if (view.value !== 'bang') query.xem = view.value
  router.replace({ query })
}
watch([status, coSo, view], syncUrl)
watch(q, () => {
  clearTimeout(typing)
  typing = setTimeout(syncUrl, 300)
})
// Ô tìm trên header đổi ?q= khi đang ở trang này
watch(() => route.query.q, (v) => { if ((one(v) ?? '') !== q.value.trim()) q.value = one(v) ?? '' })

// Màn hình hẹp chưa chọn chế độ xem thì dùng thẻ
onMounted(() => {
  if (!route.query.xem && window.matchMedia('(max-width: 48rem)').matches) view.value = 'the'
})

function clearFilters() {
  status.value = 'ALL'
  coSo.value = ''
  q.value = ''
}

const items = computed(() => data.value?.items ?? [])
const campuses = computed(() => [...new Set(items.value.map((t) => t.co_so).filter((x): x is string => !!x))].sort())

// Đếm theo trạng thái sau khi đã lọc cơ sở và từ khoá, để số trên tab khớp với kết quả
const needle = computed(() => q.value.trim().toLocaleLowerCase('vi'))
const base = computed(() => items.value.filter((t) =>
  (!coSo.value || t.co_so === coSo.value)
  && (!needle.value || `${t.title} ${t.description} ${ticketCode(t.id)}`.toLocaleLowerCase('vi').includes(needle.value)),
))
const shown = computed(() => base.value.filter((t) => status.value === 'ALL' || t.status === status.value))

const tabs = computed(() => [
  { value: 'ALL', label: 'Tất cả', count: base.value.length },
  ...Object.keys(STATUS_LABELS).map((s) => ({ value: s, label: STATUS_LABELS[s]!, count: base.value.filter((t) => t.status === s).length })),
])
const hasFilter = computed(() => status.value !== 'ALL' || !!coSo.value || !!needle.value)

// Cập nhật thời gian thực: nạp lại danh sách (gộp các sự kiện sát nhau), đánh dấu dòng vừa đổi
const { onStatus } = useTicketEvents()
const { show } = useToast()
const fresh = ref(new Set<string>())
let reloadTimer: ReturnType<typeof setTimeout> | undefined
onStatus((e) => {
  fresh.value = new Set([...fresh.value, e.ticket_id])
  setTimeout(() => { fresh.value.delete(e.ticket_id); fresh.value = new Set(fresh.value) }, 2400)
  clearTimeout(reloadTimer)
  reloadTimer = setTimeout(() => refresh(), 250)
  if (isManager.value && e.to_status === 'SUBMITTED' && e.actor_sub !== me.value?.sub) {
    show({ kind: 'info', title: 'Có phiếu mới', body: e.title })
  }
})
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
          <label class="visually-hidden" for="list-q">Tìm theo tiêu đề, mô tả hoặc mã phiếu</label>
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>
          <input id="list-q" v-model="q" class="input" type="search" placeholder="Tìm tiêu đề, mô tả, mã phiếu" autocomplete="off">
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
          <button type="button" :aria-pressed="view === 'cot'" title="Xem theo cột trạng thái, kéo thả để chuyển" @click="view = 'cot'">
            <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="5" height="16" rx="1.5" /><rect x="10" y="4" width="5" height="10" rx="1.5" /><rect x="17" y="4" width="4" height="13" rx="1.5" /></svg>
            <span>Cột</span>
          </button>
        </div>
      </div>

      <UiTabs v-if="view !== 'cot'" v-model="status" :items="tabs" label="Lọc theo trạng thái" />

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

      <div v-else-if="view === 'cot'" class="results">
        <p class="hint">Kéo phiếu bằng tay nắm sang cột được đánh dấu, hoặc dùng nút Chuyển. Mỗi lần chuyển đi qua quy trình như nút trên trang chi tiết.</p>
        <TicketBoard :tickets="base" :me="me" @changed="refresh()" />
      </div>

      <div v-else-if="!shown.length" class="empty results">
        <span class="empty-title">Không có phiếu khớp bộ lọc</span>
        <p>Thử bỏ bớt điều kiện hoặc tìm bằng từ khác.</p>
        <button class="btn secondary" type="button" @click="clearFilters">Xoá bộ lọc</button>
      </div>

      <div v-else-if="view === 'bang'" class="table-wrap results">
        <table class="table">
          <thead>
            <tr>
              <th scope="col">Mã</th>
              <th scope="col">Tiêu đề</th>
              <th scope="col">Trạng thái</th>
              <th scope="col">Loại</th>
              <th scope="col">Ưu tiên</th>
              <th scope="col">Cơ sở</th>
              <th scope="col">Cập nhật</th>
            </tr>
          </thead>
          <TransitionGroup tag="tbody" name="row">
            <tr v-for="t in shown" :key="t.id" :class="{ 'is-fresh': fresh.has(t.id) }">
              <td><span class="code">{{ ticketCode(t.id) }}</span></td>
              <td><NuxtLink :to="`/tickets/${t.id}`" class="title-link">{{ t.title }}</NuxtLink></td>
              <td><StatusStamp :status="t.status" /></td>
              <td>{{ t.category ? CATEGORY_LABELS[t.category] : '' }}</td>
              <td><span class="priority" :data-priority="t.priority">{{ t.priority ? PRIORITY_LABELS[t.priority] : '' }}</span></td>
              <td><span v-if="t.co_so" class="code">{{ t.co_so }}</span></td>
              <td class="nowrap">{{ formatTime(t.updated_at) }}</td>
            </tr>
          </TransitionGroup>
        </table>
      </div>

      <TransitionGroup v-else tag="ul" name="row" class="cards results">
        <li v-for="t in shown" :key="t.id" class="ticket-card" :class="{ 'is-fresh': fresh.has(t.id) }">
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

      <p v-if="data" class="count" aria-live="polite">
        <template v-if="hasFilter">{{ shown.length }} trong {{ items.length }} phiếu</template>
        <template v-else>{{ items.length }} phiếu</template>
        <template v-if="data.total > items.length">. Đang lọc trong {{ items.length }} phiếu mới nhất trên tổng {{ data.total }}.</template>
      </p>
    </section>
  </div>
</template>

<style scoped>
.page { display: grid; gap: var(--space-5); }

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

/* Dòng vừa đổi qua cập nhật thời gian thực: vệt cam mờ dần */
/* Lớp phủ đổi opacity, nằm dưới chữ nhờ isolation, nên không đụng tương phản của chữ */
.is-fresh td,
.ticket-card.is-fresh { position: relative; isolation: isolate; }
.is-fresh td:first-child,
.ticket-card.is-fresh { box-shadow: inset 3px 0 0 var(--brand); }
.is-fresh td::after,
.ticket-card.is-fresh::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  border-radius: inherit;
  background: var(--brand-wash);
  pointer-events: none;
  animation: fresh-fade 2.4s var(--ease-out) both;
}
@keyframes fresh-fade { from { opacity: 1; } to { opacity: 0; } }

.hint { margin: 0 0 var(--space-3); font-size: var(--text-sm); color: var(--ink-soft); }

.count { margin: var(--space-4) 0 0; font-size: var(--text-sm); color: var(--ink-soft); }

/* Dòng thêm hoặc bớt khi lọc. Bảng không dùng position absolute lúc rời để giữ cột thẳng. */
.row-enter-active { transition: opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-out); }
.row-leave-active { transition: opacity var(--dur-fast) var(--ease-out); }
.row-enter-from { opacity: 0; transform: translateY(-6px); }
.row-leave-to { opacity: 0; }
.row-move { transition: transform var(--dur) var(--ease-out); }

@media (max-width: 48rem) {
  .view-switch span { display: none; }
  .skel-hide { display: none; }
  .field-inline { flex: 1 1 auto; }
  .field-inline .input { flex: 1; }
}
</style>
