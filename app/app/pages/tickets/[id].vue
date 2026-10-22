<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Attachment, Me, Technician, Ticket, TicketEvent } from '~/utils/helpdesk'

// Chi tiết ticket và các bước của quy trình BPMN (kịch bản 2–5 và 7). Nút chỉ hiện cho
// người được phép; Data API vẫn kiểm tra lại vai trò, cơ sở và trạng thái ở mỗi bước.
const route = useRoute()
const id = route.params.id as string

const { data: me } = await useFetch<Me>('/gw/api/me', { key: 'global-me', retry: false })
const { data: ticket, error, refresh: refreshTicket } = await useFetch<Ticket>(`/gw/api/data/tickets/${id}`, { key: `ticket-${id}` })
const { data: events, refresh: refreshEvents } = await useFetch<TicketEvent[]>(`/gw/api/data/tickets/${id}/events`, { key: `events-${id}`, default: () => [] })
const { data: attachments } = await useFetch<Attachment[]>(`/gw/api/data/tickets/${id}/attachments`, { key: `attachments-${id}`, default: () => [] })

const isCreator = computed(() => !!ticket.value && ticket.value.created_by === me.value?.sub)
const isManager = computed(() => !!ticket.value && isManagerOf(me.value, ticket.value))
const isAssignedTechnician = computed(() => !!ticket.value && hasRole(me.value, 'ROLE_TECHNICIAN')
  && ticket.value.assigned_to === me.value?.sub)
// Ở SUBMITTED, quy trình có hai bước liên tiếp của trưởng phòng: tiếp nhận rồi phân công
const accepted = computed(() => {
  const list = events.value ?? []
  const lastSubmit = list.map(e => e.action).lastIndexOf('SUBMIT')
  return list.slice(lastSubmit + 1).some(e => e.action === 'ACCEPT')
})

const technicians = ref<Technician[]>([])
const form = reactive({ reason: '', technician_sub: '', priority: '', resolution_summary: '', rating: 5 })
const busy = ref(false)
const message = ref<string | null>(null)

watch(() => [ticket.value?.status, accepted.value], async () => {
  if (ticket.value?.status === 'SUBMITTED' && accepted.value && isManager.value && !technicians.value.length) {
    try {
      const site = hasRole(me.value, 'ROLE_ADMIN') ? `?co_so=${ticket.value.co_so}` : ''
      technicians.value = await dataApi<Technician[]>(`/technicians${site}`)
    }
    catch (e) {
      message.value = `Không tải được danh sách kỹ thuật viên: ${errorMessage(e)}`
    }
  }
  if (ticket.value?.priority && !form.priority) form.priority = ticket.value.priority
}, { immediate: true })

async function act(action: string, body: Record<string, unknown> = {}) {
  message.value = null
  busy.value = true
  try {
    await dataApi(`/tickets/${id}/actions/${action}`, { method: 'POST', body })
    form.reason = ''
    form.resolution_summary = ''
    await Promise.all([refreshTicket(), refreshEvents()])
  }
  catch (e) {
    message.value = errorMessage(e)
  }
  finally {
    busy.value = false
  }
}

function requireText(value: string, label: string) {
  if (value.trim()) return true
  message.value = `Cần nhập ${label}.`
  return false
}

const reject = () => requireText(form.reason, 'lý do từ chối') && act('reject', { reason: form.reason })
const reopen = () => requireText(form.reason, 'lý do mở lại') && act('reopen', { reason: form.reason })
const resolve = () => requireText(form.resolution_summary, 'biên bản xử lý')
  && act('resolve', { resolution_summary: form.resolution_summary })
const assign = () => form.technician_sub
  ? act('assign', { technician_sub: form.technician_sub, priority: form.priority || undefined })
  : (message.value = 'Chọn kỹ thuật viên.')

async function rate() {
  message.value = null
  try {
    await dataApi(`/tickets/${id}/rating`, { method: 'PUT', body: { rating: form.rating } })
    await Promise.all([refreshTicket(), refreshEvents()])
  }
  catch (e) {
    message.value = errorMessage(e)
  }
}

async function removeDraft() {
  try {
    await dataApi(`/tickets/${id}`, { method: 'DELETE' })
    await navigateTo('/tickets')
  }
  catch (e) {
    message.value = errorMessage(e)
  }
}

function who(sub: string) {
  if (sub === me.value?.sub) return 'Bạn'
  const tech = technicians.value.find(t => t.sub === sub)
  return tech ? tech.name : `${sub.slice(0, 8)}…`
}

function eventNote(e: TicketEvent) {
  const d = e.details ?? {}
  return (d.reason ?? d.resolution_summary ?? d.file_name ?? '') as string
}
</script>

<template>
  <section v-if="error" class="card">
    <h1>Không mở được ticket</h1>
    <p class="notice danger" role="alert">{{ errorMessage(error) }}</p>
    <NuxtLink to="/tickets" class="btn secondary">Về danh sách</NuxtLink>
  </section>

  <div v-else-if="ticket" class="layout">
    <section class="card">
      <p class="crumbs"><NuxtLink to="/tickets">Danh sách</NuxtLink></p>
      <div class="head">
        <h1>{{ ticket.title }}</h1>
        <span class="status" :data-status="ticket.status">{{ STATUS_LABELS[ticket.status] ?? ticket.status }}</span>
      </div>
      <p class="description">{{ ticket.description }}</p>

      <dl class="info">
        <dt>Loại</dt><dd>{{ ticket.category ? CATEGORY_LABELS[ticket.category] : '' }}</dd>
        <dt>Ưu tiên</dt><dd>{{ ticket.priority ? PRIORITY_LABELS[ticket.priority] : '' }}</dd>
        <dt>Cơ sở</dt><dd>{{ ticket.co_so ?? 'Xác định khi gửi' }}</dd>
        <dt>Mã tài sản (ID)</dt><dd>{{ ticket.asset_id ?? 'Không có, báo theo vị trí' }}</dd>
        <dt>Tạo lúc</dt><dd>{{ formatTime(ticket.created_at) }}</dd>
        <template v-if="ticket.resolution_summary">
          <dt>Biên bản</dt><dd>{{ ticket.resolution_summary }}</dd>
        </template>
        <template v-if="ticket.rejection_reason">
          <dt>Lý do từ chối</dt><dd>{{ ticket.rejection_reason }}</dd>
        </template>
        <template v-if="ticket.satisfaction_rating">
          <dt>Đánh giá</dt><dd>{{ ticket.satisfaction_rating }}/5</dd>
        </template>
      </dl>

      <div v-if="attachments?.length" class="attachments">
        <a v-for="a in attachments" :key="a.id" :href="`/gw/api/files/${a.storage_key}`" target="_blank" rel="noopener">
          <img :src="`/gw/api/files/${a.storage_key}`" :alt="a.file_name" loading="lazy">
          <span class="small">{{ a.file_name }}</span>
        </a>
      </div>

      <div class="actions" aria-live="polite">
        <p v-if="message" class="notice danger" role="alert">{{ message }}</p>

        <template v-if="ticket.status === 'DRAFT' && isCreator">
          <button class="btn" :disabled="busy" @click="act('submit')">Gửi yêu cầu</button>
          <button class="btn secondary" :disabled="busy" @click="removeDraft">Xoá bản nháp</button>
        </template>

        <template v-else-if="ticket.status === 'SUBMITTED' && isManager && !accepted">
          <button class="btn" :disabled="busy" @click="act('accept')">Tiếp nhận</button>
          <label>Lý do từ chối <textarea v-model="form.reason" rows="2" /></label>
          <button class="btn secondary" :disabled="busy" @click="reject">Từ chối</button>
        </template>

        <template v-else-if="ticket.status === 'SUBMITTED' && isManager">
          <label>
            Kỹ thuật viên cùng cơ sở {{ ticket.co_so }}
            <select v-model="form.technician_sub">
              <option value="" disabled>Chọn kỹ thuật viên</option>
              <option v-for="t in technicians" :key="t.sub" :value="t.sub">{{ t.name }} ({{ t.username }})</option>
            </select>
          </label>
          <label>
            Mức ưu tiên
            <select v-model="form.priority">
              <option v-for="(label, code) in PRIORITY_LABELS" :key="code" :value="code">{{ label }}</option>
            </select>
          </label>
          <button class="btn" :disabled="busy" @click="assign">Phân công</button>
        </template>

        <template v-else-if="ticket.status === 'ASSIGNED' && isAssignedTechnician">
          <button class="btn" :disabled="busy" @click="act('start')">Nhận việc</button>
        </template>

        <template v-else-if="ticket.status === 'IN_PROGRESS' && isAssignedTechnician">
          <label>Biên bản xử lý <textarea v-model="form.resolution_summary" rows="3" placeholder="Đã kiểm tra, thay thế gì" /></label>
          <button class="btn" :disabled="busy" @click="resolve">Đánh dấu hoàn thành</button>
        </template>

        <template v-else-if="ticket.status === 'RESOLVED' && isManager">
          <button class="btn" :disabled="busy" @click="act('close')">Nghiệm thu và đóng</button>
          <label>Lý do mở lại <textarea v-model="form.reason" rows="2" /></label>
          <button class="btn secondary" :disabled="busy" @click="reopen">Mở lại</button>
        </template>

        <template v-else-if="ticket.status === 'CLOSED' && isCreator && !ticket.satisfaction_rating">
          <label>
            Mức độ hài lòng
            <select v-model.number="form.rating">
              <option v-for="n in [5, 4, 3, 2, 1]" :key="n" :value="n">{{ n }}/5</option>
            </select>
          </label>
          <button class="btn" @click="rate">Gửi đánh giá</button>
        </template>
      </div>
    </section>

    <section class="card">
      <h2>Lịch sử</h2>
      <ol class="history">
        <li v-for="e in events" :key="e.id" :data-action="e.action">
          <span class="time">{{ formatTime(e.occurred_at) }}</span>
          <strong>{{ EVENT_LABELS[e.action] ?? e.action }}</strong>
          <span v-if="e.to_status && e.from_status !== e.to_status" class="muted small">
            → {{ STATUS_LABELS[e.to_status] ?? e.to_status }}
          </span>
          <span class="muted small">· {{ who(e.actor_sub) }}</span>
          <p v-if="eventNote(e)" class="note">{{ eventNote(e) }}</p>
        </li>
      </ol>
    </section>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 1rem; align-items: start; }
h1 { margin: 0; font-size: 1.375rem; }
h2 { margin: 0 0 0.75rem; font-size: 1.125rem; }
.crumbs { margin: 0 0 0.5rem; font-size: 0.875rem; }
.crumbs a { color: var(--accent); text-decoration: none; }
.head { display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.75rem; }
.description { white-space: pre-line; }
.info { display: grid; grid-template-columns: max-content 1fr; gap: 0.375rem 1rem; margin: 1rem 0; }
.info dt { color: var(--muted); }
.info dd { margin: 0; overflow-wrap: anywhere; }
.attachments { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem; }
.attachments a { display: flex; flex-direction: column; gap: 0.25rem; color: var(--muted); text-decoration: none; width: 9rem; }
.attachments img { width: 9rem; height: 6.5rem; object-fit: cover; border: 1px solid var(--border); border-radius: 0.375rem; background: var(--bg); }
.actions { display: flex; flex-direction: column; gap: 0.625rem; align-items: flex-start; padding-top: 1rem; border-top: 1px solid var(--border); }
.actions label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.875rem; color: var(--muted); width: 100%; max-width: 32rem; }
select, textarea { font: inherit; padding: 0.5rem; border: 1px solid var(--border); border-radius: 0.375rem; background: var(--surface); color: var(--text); }
.history { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.625rem; }
.history li { border-left: 3px solid var(--border); padding-left: 0.625rem; }
.history li[data-action="REOPEN"], .history li[data-action="REJECT"] { border-left-color: var(--danger-text); }
.history li[data-action="CLOSE"] { border-left-color: #107c41; }
.time { display: block; font-size: 0.75rem; color: var(--muted); }
.note { margin: 0.25rem 0 0; font-size: 0.875rem; white-space: pre-line; }
.muted { color: var(--muted); }
.small { font-size: 0.8125rem; }
.notice { padding: 0.75rem 1rem; border-radius: 0.375rem; margin: 0; }
.notice.danger { background: var(--danger-bg); color: var(--danger-text); }
.status { font-size: 0.8125rem; font-weight: 600; padding: 0.1rem 0.45rem; border-radius: 0.25rem; background: var(--bg); border: 1px solid var(--border); }
.status[data-status="CLOSED"] { color: #107c41; }
.status[data-status="REJECTED"] { color: var(--danger-text); }
@media (max-width: 48rem) { .layout { grid-template-columns: 1fr; } }
</style>
