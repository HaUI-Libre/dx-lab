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
useHead({ title: computed(() => ticket.value ? `${ticketCode(ticket.value.id)} · ${ticket.value.title}` : 'Phiếu') })

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

// ---- Dòng thời gian vòng đời ----
// Nhánh chính 6 bước; REJECTED thay các bước sau SUBMITTED vì từ chối kết thúc quy trình.
const FLOW = ['DRAFT', 'SUBMITTED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']
const steps = computed(() => {
  const status = ticket.value?.status ?? 'DRAFT'
  const flow = status === 'REJECTED' ? ['DRAFT', 'SUBMITTED', 'REJECTED'] : FLOW
  const at = flow.indexOf(status)
  return flow.map((s, i) => ({ status: s, state: i < at ? 'done' : i === at ? 'current' : 'todo' }))
})
const reopenCount = computed(() => (events.value ?? []).filter(e => e.action === 'REOPEN').length)

const technicians = ref<Technician[]>([])
const form = reactive({ reason: '', technician_sub: '', priority: '', resolution_summary: '', rating: 5 })
const busy = ref<string | null>(null)
const message = ref<string | null>(null)
const fieldError = reactive({ reason: '', resolution: '', technician: '' })
const { show } = useToast()

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

const DONE: Record<string, string> = {
  submit: 'Đã gửi yêu cầu', accept: 'Đã tiếp nhận', reject: 'Đã từ chối phiếu', assign: 'Đã phân công',
  start: 'Đã nhận việc', resolve: 'Đã báo hoàn thành', close: 'Đã nghiệm thu và đóng', reopen: 'Đã mở lại phiếu',
}

async function act(action: string, body: Record<string, unknown> = {}) {
  if (busy.value) return
  message.value = null
  busy.value = action
  try {
    await dataApi(`/tickets/${id}/actions/${action}`, { method: 'POST', body })
    form.reason = ''
    form.resolution_summary = ''
    await Promise.all([refreshTicket(), refreshEvents()])
    show({ kind: 'success', title: DONE[action] ?? 'Đã cập nhật', body: `Phiếu ${ticketCode(id)}: ${STATUS_LABELS[ticket.value?.status ?? ''] ?? ''}.` })
  }
  catch (e) {
    message.value = errorMessage(e)
    show({ kind: 'error', title: 'Chưa thực hiện được', body: message.value })
  }
  finally {
    busy.value = null
  }
}

// Kiểm tra khi rời ô và khi bấm; lỗi hiện ngay dưới ô
function check(field: 'reason' | 'resolution', value: string, label: string) {
  fieldError[field] = value.trim() ? '' : `Cần nhập ${label}.`
  return !fieldError[field]
}

const reject = () => check('reason', form.reason, 'lý do từ chối') && act('reject', { reason: form.reason })
const reopen = () => check('reason', form.reason, 'lý do mở lại') && act('reopen', { reason: form.reason })
const resolve = () => check('resolution', form.resolution_summary, 'biên bản xử lý')
  && act('resolve', { resolution_summary: form.resolution_summary })
function assign() {
  fieldError.technician = form.technician_sub ? '' : 'Chọn kỹ thuật viên.'
  if (!fieldError.technician) act('assign', { technician_sub: form.technician_sub, priority: form.priority || undefined })
}

async function rate() {
  message.value = null
  busy.value = 'rate'
  try {
    await dataApi(`/tickets/${id}/rating`, { method: 'PUT', body: { rating: form.rating } })
    await Promise.all([refreshTicket(), refreshEvents()])
    show({ kind: 'success', title: 'Đã gửi đánh giá', body: 'Cảm ơn bạn đã phản hồi.' })
  }
  catch (e) {
    message.value = errorMessage(e)
  }
  finally {
    busy.value = null
  }
}

async function removeDraft() {
  busy.value = 'delete'
  try {
    await dataApi(`/tickets/${id}`, { method: 'DELETE' })
    show({ kind: 'info', title: 'Đã xoá bản nháp' })
    await navigateTo('/tickets')
  }
  catch (e) {
    message.value = errorMessage(e)
  }
  finally {
    busy.value = null
  }
}

const copied = ref(false)
async function copyId() {
  try {
    await navigator.clipboard.writeText(id)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1800)
  }
  catch {
    show({ kind: 'error', title: 'Không sao chép được', body: 'Trình duyệt chặn bộ nhớ tạm.' })
  }
}

// Người khác đổi trạng thái phiếu này: nạp lại để tem đóng dấu và dòng thời gian cập nhật
const { onStatus } = useTicketEvents()
onStatus(async (e) => {
  if (e.ticket_id !== id || busy.value) return
  await Promise.all([refreshTicket(), refreshEvents()])
  if (e.actor_sub !== me.value?.sub) {
    show({ kind: 'info', title: 'Phiếu vừa được cập nhật', body: `${ticketCode(id)}: ${STATUS_LABELS[e.to_status] ?? e.to_status}.` })
  }
})

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
  <section v-if="error" class="card empty reveal">
    <span class="empty-title">Không mở được phiếu</span>
    <p role="alert">{{ errorMessage(error) }}</p>
    <NuxtLink to="/tickets" class="btn secondary">Về danh sách</NuxtLink>
  </section>

  <div v-else-if="ticket" class="page">
    <header class="page-head reveal" style="--i: 0">
      <NuxtLink to="/tickets" class="crumb">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 6-6 6 6 6" /></svg>
        Danh sách
      </NuxtLink>
      <div class="code-row">
        <span class="eyebrow">Phiếu</span>
        <span class="ticket-code">{{ ticketCode(ticket.id) }}</span>
        <button class="btn quiet btn-sm" type="button" :title="ticket.id" @click="copyId">{{ copied ? 'Đã sao chép' : 'Sao chép mã' }}</button>
      </div>
      <div class="title-row">
        <h1>{{ ticket.title }}</h1>
        <StatusStamp :status="ticket.status" />
      </div>
    </header>

    <!-- Dòng thời gian 7 trạng thái; các bước đã qua hiện lần lượt -->
    <section class="card lifecycle reveal" style="--i: 1" aria-label="Vòng đời phiếu">
      <ol class="steps">
        <li v-for="(s, i) in steps" :key="s.status" class="step" :data-state="s.state" :data-status="s.status" :style="{ '--i': i }">
          <span class="step-dot" aria-hidden="true" />
          <span class="step-no">{{ s.status === 'REJECTED' ? 'X' : String(i + 1).padStart(2, '0') }}</span>
          <span class="step-label">{{ STATUS_LABELS[s.status] }}</span>
          <span v-if="s.status === 'IN_PROGRESS' && reopenCount" class="step-extra">Mở lại {{ reopenCount }} lần</span>
          <span class="visually-hidden">{{ s.state === 'done' ? 'đã qua' : s.state === 'current' ? 'bước hiện tại' : 'chưa tới' }}</span>
        </li>
      </ol>
    </section>

    <div class="layout">
      <section class="card reveal" style="--i: 2">
        <p class="description">{{ ticket.description }}</p>

        <dl class="info">
          <div><dt>Loại</dt><dd>{{ ticket.category ? CATEGORY_LABELS[ticket.category] : 'Chưa phân loại' }}</dd></div>
          <div><dt>Ưu tiên</dt><dd class="priority" :data-priority="ticket.priority">{{ ticket.priority ? PRIORITY_LABELS[ticket.priority] : 'Chưa đặt' }}</dd></div>
          <div><dt>Cơ sở</dt><dd><span v-if="ticket.co_so" class="code">{{ ticket.co_so }}</span><template v-else>Xác định khi gửi</template></dd></div>
          <div><dt>Mã tài sản (ID)</dt><dd><span v-if="ticket.asset_id" class="code">{{ ticket.asset_id }}</span><template v-else>Không có, báo theo vị trí</template></dd></div>
          <div><dt>Tạo lúc</dt><dd>{{ formatTime(ticket.created_at) }}</dd></div>
          <div><dt>Cập nhật</dt><dd>{{ formatTime(ticket.updated_at) }}</dd></div>
          <div v-if="ticket.resolution_summary" class="wide"><dt>Biên bản</dt><dd>{{ ticket.resolution_summary }}</dd></div>
          <div v-if="ticket.rejection_reason" class="wide"><dt>Lý do từ chối</dt><dd>{{ ticket.rejection_reason }}</dd></div>
          <div v-if="ticket.satisfaction_rating"><dt>Đánh giá</dt><dd>{{ ticket.satisfaction_rating }}/5</dd></div>
        </dl>

        <div v-if="attachments?.length" class="attachments">
          <a v-for="a in attachments" :key="a.id" :href="`/gw/api/files/${a.storage_key}`" target="_blank" rel="noopener">
            <img :src="`/gw/api/files/${a.storage_key}`" :alt="a.file_name" loading="lazy">
            <span>{{ a.file_name }}</span>
          </a>
        </div>

        <div class="actions">
          <Transition name="field-msg">
            <p v-if="message" class="notice" role="alert">{{ message }}</p>
          </Transition>

          <template v-if="ticket.status === 'DRAFT' && isCreator">
            <div class="row">
              <button class="btn" :aria-busy="busy === 'submit'" :disabled="!!busy && busy !== 'submit'" @click="act('submit')">Gửi yêu cầu</button>
              <button class="btn secondary" :aria-busy="busy === 'delete'" :disabled="!!busy && busy !== 'delete'" @click="removeDraft">Xoá bản nháp</button>
            </div>
          </template>

          <template v-else-if="ticket.status === 'SUBMITTED' && isManager && !accepted">
            <button class="btn" :aria-busy="busy === 'accept'" :disabled="!!busy && busy !== 'accept'" @click="act('accept')">Tiếp nhận</button>
            <div class="field">
              <label class="field-label" for="f-reason">Lý do từ chối</label>
              <textarea id="f-reason" v-model="form.reason" class="input" rows="2" :aria-invalid="!!fieldError.reason" aria-describedby="f-reason-err" @blur="fieldError.reason && check('reason', form.reason, 'lý do từ chối')" />
              <Transition name="field-msg"><span v-if="fieldError.reason" id="f-reason-err" class="field-error">{{ fieldError.reason }}</span></Transition>
            </div>
            <button class="btn secondary" :aria-busy="busy === 'reject'" :disabled="!!busy && busy !== 'reject'" @click="reject">Từ chối</button>
          </template>

          <template v-else-if="ticket.status === 'SUBMITTED' && isManager">
            <div class="field">
              <label class="field-label" for="f-tech">Kỹ thuật viên cùng cơ sở {{ ticket.co_so }}</label>
              <select id="f-tech" v-model="form.technician_sub" class="input" :aria-invalid="!!fieldError.technician" aria-describedby="f-tech-err">
                <option value="" disabled>Chọn kỹ thuật viên</option>
                <option v-for="t in technicians" :key="t.sub" :value="t.sub">{{ t.name }} ({{ t.username }})</option>
              </select>
              <Transition name="field-msg"><span v-if="fieldError.technician" id="f-tech-err" class="field-error">{{ fieldError.technician }}</span></Transition>
            </div>
            <div class="field">
              <label class="field-label" for="f-prio">Mức ưu tiên</label>
              <select id="f-prio" v-model="form.priority" class="input">
                <option v-for="(label, code) in PRIORITY_LABELS" :key="code" :value="code">{{ label }}</option>
              </select>
            </div>
            <button class="btn" :aria-busy="busy === 'assign'" :disabled="!!busy && busy !== 'assign'" @click="assign">Phân công</button>
          </template>

          <template v-else-if="ticket.status === 'ASSIGNED' && isAssignedTechnician">
            <button class="btn" :aria-busy="busy === 'start'" :disabled="!!busy && busy !== 'start'" @click="act('start')">Nhận việc</button>
          </template>

          <template v-else-if="ticket.status === 'IN_PROGRESS' && isAssignedTechnician">
            <div class="field">
              <label class="field-label" for="f-res">Biên bản xử lý</label>
              <textarea id="f-res" v-model="form.resolution_summary" class="input" rows="3" placeholder="Đã kiểm tra, thay thế gì" :aria-invalid="!!fieldError.resolution" aria-describedby="f-res-err" @blur="fieldError.resolution && check('resolution', form.resolution_summary, 'biên bản xử lý')" />
              <Transition name="field-msg"><span v-if="fieldError.resolution" id="f-res-err" class="field-error">{{ fieldError.resolution }}</span></Transition>
            </div>
            <button class="btn" :aria-busy="busy === 'resolve'" :disabled="!!busy && busy !== 'resolve'" @click="resolve">Đánh dấu hoàn thành</button>
          </template>

          <template v-else-if="ticket.status === 'RESOLVED' && isManager">
            <button class="btn" :aria-busy="busy === 'close'" :disabled="!!busy && busy !== 'close'" @click="act('close')">Nghiệm thu và đóng</button>
            <div class="field">
              <label class="field-label" for="f-reopen">Lý do mở lại</label>
              <textarea id="f-reopen" v-model="form.reason" class="input" rows="2" :aria-invalid="!!fieldError.reason" aria-describedby="f-reopen-err" @blur="fieldError.reason && check('reason', form.reason, 'lý do mở lại')" />
              <Transition name="field-msg"><span v-if="fieldError.reason" id="f-reopen-err" class="field-error">{{ fieldError.reason }}</span></Transition>
            </div>
            <button class="btn secondary" :aria-busy="busy === 'reopen'" :disabled="!!busy && busy !== 'reopen'" @click="reopen">Mở lại</button>
          </template>

          <template v-else-if="ticket.status === 'CLOSED' && isCreator && !ticket.satisfaction_rating">
            <div class="field">
              <label class="field-label" for="f-rate">Mức độ hài lòng</label>
              <select id="f-rate" v-model.number="form.rating" class="input">
                <option v-for="n in [5, 4, 3, 2, 1]" :key="n" :value="n">{{ n }}/5</option>
              </select>
            </div>
            <button class="btn" :aria-busy="busy === 'rate'" @click="rate">Gửi đánh giá</button>
          </template>

          <p v-else class="no-action">Không có thao tác nào cho bạn ở bước này.</p>
        </div>
      </section>

      <section class="card history-card reveal" style="--i: 3" aria-labelledby="h-history">
        <div class="card-head"><h2 id="h-history">Lịch sử</h2><span class="code">{{ events?.length ?? 0 }}</span></div>
        <TransitionGroup tag="ol" name="row" class="history">
          <li v-for="(e, i) in events" :key="e.id" :data-action="e.action" :style="{ '--i': i }">
            <span class="time">{{ formatTime(e.occurred_at) }}</span>
            <strong>{{ EVENT_LABELS[e.action] ?? e.action }}</strong>
            <span v-if="e.to_status && e.from_status !== e.to_status" class="to">
              sang {{ STATUS_LABELS[e.to_status] ?? e.to_status }}
            </span>
            <span class="by">· {{ who(e.actor_sub) }}</span>
            <p v-if="eventNote(e)" class="note">{{ eventNote(e) }}</p>
          </li>
        </TransitionGroup>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page { display: grid; gap: var(--space-5); }

.crumb { display: inline-flex; align-items: center; gap: var(--space-1); font-weight: 700; font-size: var(--text-sm); color: var(--ink-soft); text-decoration: none; }
.crumb:hover { color: var(--ink); }
.crumb svg { width: 1rem; height: 1rem; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

.code-row { display: flex; align-items: center; gap: var(--space-3); margin-top: var(--space-3); }
.ticket-code { font-family: var(--font-mono); font-weight: 700; font-size: var(--text-lg); letter-spacing: 0.08em; }
.title-row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); margin-top: var(--space-1); }
.title-row h1 { margin: 0; }

/* ---- Vòng đời ---- */
.lifecycle { padding-block: var(--space-4); }
.steps { list-style: none; margin: 0; padding: 0; display: flex; }

.step {
  position: relative;
  flex: 1;
  display: grid;
  justify-items: center;
  gap: 0.15rem;
  padding-top: 1.6rem;
  text-align: center;
  color: var(--ink-soft);
}

/* Đường nối giữa hai bước, vẽ dần từ trái với bước đã qua */
.step::before {
  content: "";
  position: absolute;
  top: 0.6rem;
  left: calc(-50% + 0.7rem);
  right: calc(50% + 0.7rem);
  height: 2px;
  background: var(--rule);
}
.step:first-child::before { display: none; }
.step::after {
  content: "";
  position: absolute;
  top: 0.6rem;
  left: calc(-50% + 0.7rem);
  right: calc(50% + 0.7rem);
  height: 2px;
  background: var(--brand);
  transform: scaleX(0);
  transform-origin: left;
}
.step:first-child::after { display: none; }
.step[data-state="done"]::after,
.step[data-state="current"]::after { animation: draw-line var(--dur-slow) var(--ease-out) both; animation-delay: calc(var(--i) * 90ms + 150ms); }

.step-dot {
  position: absolute;
  top: 0.15rem;
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  background: var(--card);
  border: 2px solid var(--line);
}

.step[data-state="done"] { color: var(--ink); }
.step[data-state="done"] .step-dot { background: var(--brand); border-color: var(--brand); animation: pop var(--dur) var(--ease-spring) both; animation-delay: calc(var(--i) * 90ms + 150ms); }
.step[data-state="current"] { color: var(--ink); }
.step[data-state="current"] .step-dot { border-color: var(--brand); box-shadow: 0 0 0 4px color-mix(in srgb, var(--brand) 25%, transparent); animation: pop var(--dur) var(--ease-spring) both; animation-delay: calc(var(--i) * 90ms + 150ms); }
.step[data-state="current"] .step-label { font-weight: 800; color: var(--brand-ink); }
.step[data-status="REJECTED"][data-state="current"] .step-dot { background: var(--brand-ink); border-color: var(--brand-ink); }

.step-no { font-family: var(--font-mono); font-size: 0.75rem; font-weight: 600; }
.step-label { font-size: var(--text-sm); font-weight: 600; line-height: 1.3; }
.step-extra { font-size: var(--text-xs); font-weight: 700; color: var(--brand-ink); }

@keyframes draw-line { to { transform: scaleX(1); } }
@keyframes pop { from { transform: scale(0.4); opacity: 0; } to { transform: none; opacity: 1; } }

/* ---- Nội dung ---- */
.layout { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: var(--space-5); align-items: start; }
.description { white-space: pre-line; font-size: var(--text-lg); margin-bottom: var(--space-5); }

.info { display: grid; grid-template-columns: repeat(auto-fill, minmax(11rem, 1fr)); gap: var(--space-3) var(--space-5); margin: 0 0 var(--space-5); padding: var(--space-4); background: var(--sunk); border-radius: var(--radius-control); }
.info .wide { grid-column: 1 / -1; }
.info dt { font-size: var(--text-xs); font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; color: var(--ink-soft); }
.info dd { margin: 0; overflow-wrap: anywhere; }
.priority[data-priority="URGENT"],
.priority[data-priority="HIGH"] { font-weight: 800; color: var(--brand-ink); }

.attachments { display: flex; gap: var(--space-3); flex-wrap: wrap; margin-bottom: var(--space-5); }
.attachments a { display: grid; gap: var(--space-1); width: 9rem; font-size: var(--text-sm); color: var(--ink-soft); text-decoration: none; }
.attachments img { width: 9rem; height: 6.5rem; object-fit: cover; border: 1px solid var(--rule); border-radius: var(--radius-control); background: var(--sunk); transition: transform var(--dur) var(--ease-out); }
.attachments a:hover img { transform: scale(1.03); }

.actions { display: grid; gap: var(--space-3); justify-items: start; padding-top: var(--space-4); border-top: 1px solid var(--rule); }
.actions .field { width: 100%; max-width: 34rem; }
.row { display: flex; flex-wrap: wrap; gap: var(--space-3); }
.notice { margin: 0; padding: var(--space-3) var(--space-4); color: var(--brand-ink); background: var(--brand-wash); border-left: 3px solid var(--brand-ink); border-radius: var(--radius-control); font-weight: 700; }
.no-action { margin: 0; color: var(--ink-soft); font-size: var(--text-sm); }

/* ---- Lịch sử ---- */
.history { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-3); }
.history li {
  position: relative;
  padding-left: var(--space-5);
  animation: rise-in var(--dur-slow) var(--ease-out) both;
  animation-delay: calc(var(--i) * 50ms + 200ms);
}
.history li::before {
  content: "";
  position: absolute;
  left: 0.2rem;
  top: 0.45rem;
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 50%;
  border: 2px solid var(--line);
  background: var(--card);
}
.history li::after { content: ""; position: absolute; left: calc(0.2rem + 0.3rem); top: 1.3rem; bottom: calc(var(--space-3) * -1); width: 1px; background: var(--rule); }
.history li:last-child::after { display: none; }
.history li[data-action="REOPEN"]::before,
.history li[data-action="REJECT"]::before { border-color: var(--brand-ink); background: var(--brand-wash); }
.history li[data-action="CLOSE"]::before { border-color: var(--ink); background: var(--ink); }
.time { display: block; font-size: var(--text-xs); color: var(--ink-soft); font-family: var(--font-mono); }
.to, .by { font-size: var(--text-sm); color: var(--ink-soft); }
.note { margin: var(--space-1) 0 0; font-size: var(--text-sm); white-space: pre-line; padding: var(--space-2) var(--space-3); background: var(--sunk); border-radius: var(--radius-control); }

.row-enter-active { transition: opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-out); }
.row-enter-from { opacity: 0; transform: translateY(-6px); }
.row-move { transition: transform var(--dur) var(--ease-out); }

@media (max-width: 56rem) {
  .layout { grid-template-columns: minmax(0, 1fr); }
}

/* Điện thoại: dòng thời gian xếp dọc */
@media (max-width: 40rem) {
  .steps { flex-direction: column; gap: var(--space-2); }
  .step { justify-items: start; grid-template-columns: auto 1fr; column-gap: var(--space-3); padding: 0 0 0 1.75rem; text-align: left; }
  .step-dot { left: 0; top: 0.2rem; }
  .step::before, .step::after { top: calc(-1 * var(--space-2) - 0.2rem); bottom: auto; left: 0.45rem; right: auto; width: 2px; height: calc(var(--space-2) + 0.4rem); }
  .step::after { transform: scaleY(0); transform-origin: top; animation-name: draw-line-y !important; }
  .step-extra { grid-column: 2; }
}

@keyframes draw-line-y { to { transform: scaleY(1); } }
</style>
