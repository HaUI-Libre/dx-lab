<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Me, Technician, Ticket, TicketEvent } from '~/utils/helpdesk'

// Bảng cột theo trạng thái, kéo thả để đổi trạng thái. Mỗi lần thả gọi đúng action của
// Data API (/tickets/{id}/actions/{action}), tức là đi qua Flowable như nút bấm; không có
// endpoint đổi trạng thái trực tiếp. Giao diện chỉ gợi ý cột hợp lệ theo BPMN và vai trò;
// gateway và Data API vẫn quyết định. Thao tác tương đương bằng bàn phím qua nút "Chuyển".
const props = defineProps<{ tickets: Ticket[], me: Me | null | undefined }>()
const emit = defineEmits<{ changed: [] }>()
const { show } = useToast()

type Need = 'reason' | 'resolution' | 'technician' | null
interface Move { to: string, action: string, label: string, need: Need, allowed: (t: Ticket) => boolean }

const mine = (t: Ticket) => t.created_by === props.me?.sub
const manager = (t: Ticket) => isManagerOf(props.me, t)
const assignedTech = (t: Ticket) => hasRole(props.me, 'ROLE_TECHNICIAN') && t.assigned_to === props.me?.sub

// Chuyển hợp lệ theo core/workflow/helpdesk.bpmn20.xml; từ chối chỉ ở bước tiếp nhận, mở lại chỉ ở bước nghiệm thu
const MOVES: Record<string, Move[]> = {
  DRAFT: [{ to: 'SUBMITTED', action: 'submit', label: 'Gửi yêu cầu', need: null, allowed: mine }],
  SUBMITTED: [
    { to: 'ASSIGNED', action: 'assign', label: 'Tiếp nhận và phân công', need: 'technician', allowed: manager },
    { to: 'REJECTED', action: 'reject', label: 'Từ chối', need: 'reason', allowed: manager },
  ],
  ASSIGNED: [{ to: 'IN_PROGRESS', action: 'start', label: 'Nhận việc', need: null, allowed: assignedTech }],
  IN_PROGRESS: [{ to: 'RESOLVED', action: 'resolve', label: 'Đánh dấu hoàn thành', need: 'resolution', allowed: assignedTech }],
  RESOLVED: [
    { to: 'CLOSED', action: 'close', label: 'Nghiệm thu và đóng', need: null, allowed: manager },
    { to: 'IN_PROGRESS', action: 'reopen', label: 'Mở lại', need: 'reason', allowed: manager },
  ],
}
const movesFor = (t: Ticket) => (MOVES[t.status] ?? []).filter(m => m.allowed(t))

const columns = computed(() => {
  const order = ['DRAFT', 'SUBMITTED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REJECTED']
  return order
    .filter(s => s !== 'DRAFT' || props.tickets.some(t => t.status === 'DRAFT'))
    .map(s => ({ status: s, items: props.tickets.filter(t => t.status === s) }))
})

// ---- Kéo thả bằng Pointer Events ----
const board = ref<HTMLElement>()
const drag = ref<{ ticket: Ticket, x: number, y: number, ox: number, oy: number, w: number } | null>(null)
const over = ref<string | null>(null)
const returning = ref(false)
const announce = ref('')
let start: { x: number, y: number, ticket: Ticket, el: HTMLElement, id: number } | null = null

const validTargets = computed(() => new Set(drag.value ? movesFor(drag.value.ticket).map(m => m.to) : []))

function onPointerDown(e: PointerEvent, t: Ticket) {
  if (e.button !== 0 || busy.value || !movesFor(t).length) return
  const el = (e.currentTarget as HTMLElement).closest<HTMLElement>('.board-card')!
  start = { x: e.clientX, y: e.clientY, ticket: t, el, id: e.pointerId }
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}

function onPointerMove(e: PointerEvent) {
  if (!start || e.pointerId !== start.id) return
  if (!drag.value) {
    if (Math.hypot(e.clientX - start.x, e.clientY - start.y) < 6) return
    const r = start.el.getBoundingClientRect()
    drag.value = { ticket: start.ticket, x: r.left, y: r.top, ox: start.x - r.left, oy: start.y - r.top, w: r.width }
    announce.value = `Đang kéo phiếu ${ticketCode(start.ticket.id)}. Thả vào cột được đánh dấu.`
  }
  drag.value.x = e.clientX - drag.value.ox
  drag.value.y = e.clientY - drag.value.oy
  const col = document.elementFromPoint(e.clientX, e.clientY)?.closest<HTMLElement>('[data-col]')
  over.value = col?.dataset.col ?? null
}

function onPointerUp(e: PointerEvent) {
  if (!start || e.pointerId !== start.id) return
  const s = start
  start = null
  if (!drag.value) return
  const target = over.value
  const move = movesFor(drag.value.ticket).find(m => m.to === target)
  if (move) {
    const t = drag.value.ticket
    drag.value = null
    over.value = null
    perform(t, move)
    return
  }
  // Thả ngoài cột hợp lệ: phiếu trượt về chỗ cũ
  const r = s.el.getBoundingClientRect()
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduce) { drag.value = null; over.value = null; return }
  returning.value = true
  drag.value.x = r.left
  drag.value.y = r.top
  over.value = null
  setTimeout(() => { drag.value = null; returning.value = false }, 220)
  if (target) show({ kind: 'error', title: 'Không chuyển được', body: `Phiếu ${ticketCode(s.ticket.id)} không thể chuyển sang ${STATUS_LABELS[target]} ở bước này.` })
}

function onKeyCancel(e: KeyboardEvent) {
  if (e.key === 'Escape' && drag.value) {
    start = null
    drag.value = null
    over.value = null
  }
}
onMounted(() => window.addEventListener('keydown', onKeyCancel))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeyCancel))

// ---- Thực hiện chuyển, hỏi thêm dữ liệu khi bước cần ----
const busy = ref<string | null>(null)
const menuFor = ref<string | null>(null)
const dialog = ref<HTMLDialogElement>()
const pending = ref<{ ticket: Ticket, move: Move } | null>(null)
const form = reactive({ text: '', technician: '', error: '' })
const technicians = ref<Technician[]>([])

async function perform(t: Ticket, move: Move) {
  menuFor.value = null
  if (move.need) {
    pending.value = { ticket: t, move }
    form.text = ''
    form.technician = ''
    form.error = ''
    if (move.need === 'technician') {
      try {
        const site = hasRole(props.me, 'ROLE_ADMIN') ? `?co_so=${t.co_so}` : ''
        technicians.value = await dataApi<Technician[]>(`/technicians${site}`)
      }
      catch (e) {
        show({ kind: 'error', title: 'Không tải được kỹ thuật viên', body: errorMessage(e) })
        return
      }
    }
    await nextTick()
    dialog.value?.showModal()
    return
  }
  await run(t, move, {})
}

async function confirmDialog() {
  if (!pending.value) return
  const { ticket, move } = pending.value
  if (move.need === 'technician' && !form.technician) { form.error = 'Chọn kỹ thuật viên.'; return }
  if ((move.need === 'reason' || move.need === 'resolution') && !form.text.trim()) {
    form.error = move.need === 'reason' ? 'Cần nhập lý do.' : 'Cần nhập biên bản xử lý.'
    return
  }
  const body = move.need === 'technician' ? { technician_sub: form.technician }
    : move.need === 'reason' ? { reason: form.text.trim() }
      : { resolution_summary: form.text.trim() }
  dialog.value?.close()
  await run(ticket, move, body)
  pending.value = null
}

async function run(t: Ticket, move: Move, body: Record<string, unknown>) {
  busy.value = t.id
  try {
    // Phân công cần trưởng phòng tiếp nhận trước (hai bước liên tiếp trong BPMN)
    if (move.action === 'assign') {
      const events = await dataApi<TicketEvent[]>(`/tickets/${t.id}/events`)
      const lastSubmit = events.map(e => e.action).lastIndexOf('SUBMIT')
      if (!events.slice(lastSubmit + 1).some(e => e.action === 'ACCEPT')) {
        await dataApi(`/tickets/${t.id}/actions/accept`, { method: 'POST', body: {} })
      }
    }
    await dataApi(`/tickets/${t.id}/actions/${move.action}`, { method: 'POST', body })
    show({ kind: 'success', title: move.label, body: `Phiếu ${ticketCode(t.id)} sang ${STATUS_LABELS[move.to]}.` })
    announce.value = `Đã chuyển phiếu ${ticketCode(t.id)} sang ${STATUS_LABELS[move.to]}.`
  }
  catch (e) {
    show({ kind: 'error', title: 'Không chuyển được', body: errorMessage(e) })
    announce.value = `Không chuyển được phiếu ${ticketCode(t.id)}.`
  }
  finally {
    busy.value = null
    emit('changed')
  }
}
</script>

<template>
  <div ref="board" class="board" :class="{ dragging: !!drag }" @pointermove="onPointerMove" @pointerup="onPointerUp" @pointercancel="onPointerUp">
    <p class="visually-hidden" aria-live="assertive">{{ announce }}</p>
    <section
      v-for="col in columns" :key="col.status" class="col" :data-col="col.status"
      :data-valid="validTargets.has(col.status) || undefined" :data-over="(over === col.status && validTargets.has(col.status)) || undefined"
      :aria-label="`${STATUS_LABELS[col.status]}, ${col.items.length} phiếu`"
    >
      <header class="col-head">
        <StatusStamp :status="col.status" />
        <span class="col-count">{{ col.items.length }}</span>
      </header>
      <TransitionGroup tag="ul" name="card" class="col-list">
        <li
          v-for="t in col.items" :key="t.id" class="board-card"
          :class="{ lifted: drag?.ticket.id === t.id, busy: busy === t.id }" :aria-busy="busy === t.id"
        >
          <div class="card-row">
            <button
              v-if="movesFor(t).length" class="grip" type="button" tabindex="-1" aria-hidden="true"
              @pointerdown="onPointerDown($event, t)"
            >
              <svg viewBox="0 0 24 24"><path d="M9 6h.01M15 6h.01M9 12h.01M15 12h.01M9 18h.01M15 18h.01" /></svg>
            </button>
            <span class="code">{{ ticketCode(t.id) }}</span>
            <span v-if="t.priority === 'URGENT' || t.priority === 'HIGH'" class="prio">{{ PRIORITY_LABELS[t.priority] }}</span>
          </div>
          <NuxtLink :to="`/tickets/${t.id}`" class="card-title">{{ t.title }}</NuxtLink>
          <div v-if="movesFor(t).length" class="move">
            <button
              class="btn quiet btn-sm" type="button" :aria-expanded="menuFor === t.id" :aria-controls="`move-${t.id}`"
              @click="menuFor = menuFor === t.id ? null : t.id"
            >
              Chuyển
            </button>
            <ul v-if="menuFor === t.id" :id="`move-${t.id}`" class="move-menu">
              <li v-for="m in movesFor(t)" :key="m.action">
                <button class="btn secondary btn-sm" type="button" @click="perform(t, m)">{{ m.label }}</button>
              </li>
            </ul>
          </div>
        </li>
      </TransitionGroup>
      <p v-if="!col.items.length" class="col-empty">Trống</p>
    </section>

    <!-- Bóng của phiếu đang kéo, chỉ đổi transform -->
    <div
      v-if="drag" class="ghost" :class="{ returning }" aria-hidden="true"
      :style="{ width: `${drag.w}px`, transform: `translate3d(${drag.x}px, ${drag.y}px, 0) rotate(${returning ? 0 : 2}deg)` }"
    >
      <span class="code">{{ ticketCode(drag.ticket.id) }}</span>
      <span class="card-title">{{ drag.ticket.title }}</span>
    </div>

    <dialog ref="dialog" class="dlg" @close="pending = null">
      <form v-if="pending" method="dialog" @submit.prevent="confirmDialog">
        <h2>{{ pending.move.label }}</h2>
        <p class="dlg-sub"><span class="code">{{ ticketCode(pending.ticket.id) }}</span> {{ pending.ticket.title }}</p>
        <div v-if="pending.move.need === 'technician'" class="field">
          <label class="field-label" for="dlg-tech">Kỹ thuật viên cùng cơ sở {{ pending.ticket.co_so }}</label>
          <select id="dlg-tech" v-model="form.technician" class="input" :aria-invalid="!!form.error" aria-describedby="dlg-err">
            <option value="" disabled>Chọn kỹ thuật viên</option>
            <option v-for="tech in technicians" :key="tech.sub" :value="tech.sub">{{ tech.name }} ({{ tech.username }})</option>
          </select>
        </div>
        <div v-else class="field">
          <label class="field-label" for="dlg-text">{{ pending.move.need === 'resolution' ? 'Biên bản xử lý' : pending.move.action === 'reject' ? 'Lý do từ chối' : 'Lý do mở lại' }}</label>
          <textarea id="dlg-text" v-model="form.text" class="input" rows="3" :aria-invalid="!!form.error" aria-describedby="dlg-err" />
        </div>
        <Transition name="field-msg"><span v-if="form.error" id="dlg-err" class="field-error">{{ form.error }}</span></Transition>
        <div class="dlg-actions">
          <button class="btn" type="submit">{{ pending.move.label }}</button>
          <button class="btn quiet" type="button" @click="dialog?.close()">Huỷ</button>
        </div>
      </form>
    </dialog>
  </div>
</template>

<style scoped>
.board { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(15rem, 1fr); gap: var(--space-3); overflow-x: auto; padding-bottom: var(--space-2); }
.board.dragging { user-select: none; cursor: grabbing; }

.col {
  display: grid;
  grid-template-rows: auto 1fr;
  align-content: start;
  min-height: 14rem;
  padding: var(--space-3);
  background: var(--sunk);
  border: 1px dashed transparent;
  border-radius: var(--radius-card);
  transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}
.col[data-valid] { border-color: var(--brand); }
.col[data-over] { box-shadow: inset 0 0 0 2px var(--brand); }
.col-head { display: flex; justify-content: space-between; align-items: center; gap: var(--space-2); margin-bottom: var(--space-3); }
.col-count { font-family: var(--font-mono); font-weight: 700; color: var(--ink-soft); }
.col-list { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-2); align-content: start; position: relative; }
.col-empty { margin: 0; text-align: center; font-size: var(--text-sm); color: var(--ink-soft); }

.board-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--card);
  border: 1px solid var(--rule);
  border-radius: var(--radius-control);
  box-shadow: var(--shadow);
  transition: opacity var(--dur-fast), transform var(--dur-fast) var(--ease-out);
}
.board-card.lifted { opacity: 0.35; }
.board-card.busy { opacity: 0.6; }
.card-row { display: flex; align-items: center; gap: var(--space-2); }
.grip { display: grid; place-items: center; width: 1.75rem; height: 1.75rem; padding: 0; color: var(--ink-soft); background: none; border: 0; border-radius: var(--radius-control); cursor: grab; touch-action: none; }
.grip:hover { background: var(--sunk); color: var(--ink); }
.grip svg { width: 1.1rem; height: 1.1rem; fill: none; stroke: currentColor; stroke-width: 3; stroke-linecap: round; }
.prio { margin-left: auto; font-size: var(--text-xs); font-weight: 800; color: var(--brand-ink); }
.card-title { font-weight: 700; color: var(--ink); text-decoration: none; line-height: 1.35; }
.card-title:hover { color: var(--brand-ink); text-decoration: underline; }

.move { position: relative; justify-self: start; }
.move-menu { list-style: none; margin: var(--space-1) 0 0; padding: 0; display: grid; gap: var(--space-1); }

.ghost {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 90;
  display: grid;
  gap: var(--space-1);
  padding: var(--space-3);
  background: var(--card);
  border: 1px solid var(--brand);
  border-radius: var(--radius-control);
  box-shadow: var(--shadow-lift);
  pointer-events: none;
}
.ghost.returning { transition: transform 200ms var(--ease-out); }

.card-enter-active { transition: opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-spring); }
.card-leave-active { transition: opacity var(--dur-fast); position: absolute; left: 0; right: 0; }
.card-enter-from { opacity: 0; transform: scale(0.96); }
.card-leave-to { opacity: 0; }
.card-move { transition: transform var(--dur) var(--ease-out); }

.dlg { width: min(30rem, calc(100vw - 2rem)); padding: var(--space-5); color: var(--ink); background: var(--card); border: 1px solid var(--rule); border-radius: var(--radius-card); box-shadow: var(--shadow-lift); }
.dlg::backdrop { background: rgb(10 11 14 / 0.45); }
.dlg form { display: grid; gap: var(--space-3); }
.dlg h2 { margin: 0; }
.dlg-sub { margin: 0; color: var(--ink-soft); }
.dlg-actions { display: flex; gap: var(--space-2); flex-wrap: wrap; }
</style>
