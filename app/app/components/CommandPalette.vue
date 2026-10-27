<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Me, Ticket } from '~/utils/helpdesk'

// Bảng lệnh Ctrl+K: chuyển trang, đổi chế độ, mở phiếu theo mã hoặc tiêu đề.
// Chỉ liệt kê mục hợp với vai trò hiện tại để gọn; quyền thật vẫn do gateway và Data API kiểm tra.
const props = defineProps<{ me: Me | null | undefined }>()
const open = defineModel<boolean>({ required: true })

interface Command { id: string, group: string, label: string, hint?: string, code?: string, run: () => void }

const { toggle, current } = useTheme()
const query = ref('')
const active = ref(0)
const input = ref<HTMLInputElement>()
const tickets = ref<Ticket[] | null>(null)
const loading = ref(false)
const lookupError = ref('')
let opener: HTMLElement | null = null

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const CODE = /^DXL-[0-9]{4,}$/i
const isManager = computed(() => hasRole(props.me, 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'))
const isTechnician = computed(() => hasRole(props.me, 'ROLE_TECHNICIAN'))

function go(path: string) {
  open.value = false
  navigateTo(path)
}

async function goByCode(code: string) {
  lookupError.value = ''
  try {
    const ticket = await dataApi<Ticket>(`/tickets/by-code/${encodeURIComponent(code.toUpperCase())}`)
    go(`/tickets/${ticket.id}`)
  }
  catch { lookupError.value = 'Không tìm thấy phiếu hoặc bạn không có quyền xem.' }
}

const pages = computed<Command[]>(() => {
  const list: Command[] = [
    { id: 'home', group: 'Trang', label: 'Tổng quan', run: () => go('/') },
    { id: 'list', group: 'Trang', label: isManager.value ? 'Hàng đợi' : isTechnician.value ? 'Việc của tôi' : 'Yêu cầu của tôi', run: () => go('/tickets') },
    { id: 'new', group: 'Trang', label: 'Báo hỏng thiết bị', run: () => go('/tickets/new') },
  ]
  if (isManager.value) list.push({ id: 'stats', group: 'Trang', label: 'Thống kê', run: () => go('/dashboard') })
  list.push(
    { id: 'portal', group: 'Trang', label: 'Không gian [H] Portal', run: () => go('/portal') },
    { id: 'theme', group: 'Lệnh', label: current.value === 'dark' ? 'Chuyển sang chế độ sáng' : 'Chuyển sang chế độ tối', run: () => { open.value = false; toggle() } },
  )
  for (const s of ['SUBMITTED', 'IN_PROGRESS', 'RESOLVED']) {
    list.push({ id: `filter-${s}`, group: 'Lọc phiếu', label: `Phiếu ${STATUS_LABELS[s]!.toLowerCase()}`, run: () => go(`/tickets?trang_thai=${s}`) })
  }
  return list
})

const needle = computed(() => query.value.trim().toLocaleLowerCase('vi'))
const results = computed<Command[]>(() => {
  const q = needle.value
  const out: Command[] = []
  if (UUID.test(query.value.trim())) {
    const id = query.value.trim()
    out.push({ id: `uuid-${id}`, group: 'Phiếu', label: 'Mở phiếu theo UUID', code: id, run: () => go(`/tickets/${id}`) })
  }
  if (CODE.test(query.value.trim())) {
    const code = query.value.trim()
    out.push({ id: `code-${code}`, group: 'Phiếu', label: 'Tra mã phiếu', code: code.toUpperCase(), run: () => { void goByCode(code) } })
  }
  out.push(...pages.value.filter(c => !q || c.label.toLocaleLowerCase('vi').includes(q)))
  const found = (tickets.value ?? []).filter(t => q && `${ticketCode(t)} ${t.title}`.toLocaleLowerCase('vi').includes(q)).slice(0, 6)
  out.push(...found.map(t => ({ id: t.id, group: 'Phiếu', label: t.title, code: ticketCode(t), hint: STATUS_LABELS[t.status], run: () => go(`/tickets/${t.id}`) })))
  return out
})

const groups = computed(() => {
  const map = new Map<string, { cmd: Command, index: number }[]>()
  results.value.forEach((cmd, index) => {
    if (!map.has(cmd.group)) map.set(cmd.group, [])
    map.get(cmd.group)!.push({ cmd, index })
  })
  return [...map.entries()]
})

watch(results, () => { active.value = 0; lookupError.value = '' })

// Tải danh sách gần đây để gợi ý; tra mã đầy đủ dùng API toàn bộ dữ liệu.
watch(open, async (value) => {
  if (value) {
    opener = document.activeElement as HTMLElement | null
    query.value = ''
    await nextTick()
    input.value?.focus()
    if (!tickets.value && !loading.value && props.me) {
      loading.value = true
      try { tickets.value = (await dataApi<{ items: Ticket[] }>('/tickets?page_size=100')).items }
      catch { tickets.value = [] }
      finally { loading.value = false }
    }
  }
  else {
    opener?.focus?.()
  }
})

function onKey(e: KeyboardEvent) {
  const n = results.value.length
  if (e.key === 'ArrowDown') { e.preventDefault(); active.value = n ? (active.value + 1) % n : 0 }
  else if (e.key === 'ArrowUp') { e.preventDefault(); active.value = n ? (active.value - 1 + n) % n : 0 }
  else if (e.key === 'Enter') { e.preventDefault(); results.value[active.value]?.run() }
  else if (e.key === 'Escape') { e.preventDefault(); open.value = false }
  else if (e.key === 'Tab') { e.preventDefault() } // giữ focus trong hộp thoại; điều hướng bằng mũi tên
}

watch(active, () => nextTick(() => document.getElementById(`cmd-${active.value}`)?.scrollIntoView({ block: 'nearest' })))
</script>

<template>
  <Teleport to="body">
    <Transition name="palette">
      <div v-if="open" class="palette-backdrop" @mousedown.self="open = false">
        <div class="palette" role="dialog" aria-modal="true" aria-label="Bảng lệnh">
          <div class="palette-search">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>
            <input
              ref="input" v-model="query" class="palette-input" type="text" role="combobox" autocomplete="off"
              aria-expanded="true" aria-controls="cmd-list" :aria-activedescendant="results.length ? `cmd-${active}` : undefined"
              placeholder="Gõ tên trang, tiêu đề hoặc mã phiếu" aria-label="Tìm lệnh" @keydown="onKey"
            >
            <kbd>Esc</kbd>
          </div>
          <div id="cmd-list" class="palette-list" role="listbox" aria-label="Kết quả">
            <template v-for="[group, items] in groups" :key="group">
              <div class="palette-group" role="presentation">{{ group }}</div>
              <div
                v-for="{ cmd, index } in items" :id="`cmd-${index}`" :key="cmd.id" role="option"
                class="palette-item" :aria-selected="index === active"
                @mousemove="active = index" @click="cmd.run()"
              >
                <span v-if="cmd.code" class="code">{{ cmd.code }}</span>
                <span class="palette-label">{{ cmd.label }}</span>
                <span v-if="cmd.hint" class="palette-hint">{{ cmd.hint }}</span>
              </div>
            </template>
            <p v-if="lookupError" class="palette-empty" role="alert">{{ lookupError }}</p>
            <p v-if="!results.length" class="palette-empty">
              {{ loading ? 'Đang tải danh sách phiếu…' : 'Không có kết quả. Nhập mã DXL-NNNN để tra phiếu.' }}
            </p>
          </div>
          <p class="palette-foot"><kbd>↑</kbd><kbd>↓</kbd> chọn · <kbd>Enter</kbd> mở · Quyền thật do máy chủ kiểm tra</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.palette-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  justify-items: center;
  align-items: start;
  padding: 12vh var(--space-4) var(--space-4);
  background: rgb(10 11 14 / 0.45);
}

.palette {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  width: min(36rem, 100%);
  max-height: 70vh;
  overflow: hidden;
  background: var(--card);
  border: 1px solid var(--rule);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-lift);
}

.palette-search { position: relative; display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--rule); }
.palette-search svg { width: 1.2rem; height: 1.2rem; flex: none; fill: none; stroke: var(--ink-soft); stroke-width: 2; stroke-linecap: round; }
.palette-input { flex: 1; min-width: 0; min-height: 2.5rem; font: inherit; font-size: var(--text-lg); color: var(--ink); background: transparent; border: 0; }
.palette-input:focus-visible { outline: none; }
.palette-search:focus-within { box-shadow: inset 0 -2px 0 var(--focus); }

kbd { padding: 0 0.35rem; font-family: var(--font-mono); font-size: 0.75rem; color: var(--ink-soft); background: var(--sunk); border: 1px solid var(--rule); border-radius: var(--radius-control); }

.palette-list { overflow-y: auto; padding: var(--space-2); }
.palette-group { padding: var(--space-2) var(--space-3) var(--space-1); font-size: var(--text-xs); font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-soft); }
.palette-item { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-3); border-radius: var(--radius-control); cursor: pointer; }
.palette-item[aria-selected="true"] { background: var(--brand-wash); box-shadow: inset 3px 0 0 var(--brand); }
.palette-label { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.palette-hint { font-size: var(--text-sm); color: var(--ink-soft); white-space: nowrap; }
.palette-empty { margin: 0; padding: var(--space-4); color: var(--ink-soft); text-align: center; }
.palette-foot { margin: 0; padding: var(--space-2) var(--space-4); font-size: var(--text-xs); color: var(--ink-soft); border-top: 1px solid var(--rule); display: flex; gap: var(--space-1); align-items: center; flex-wrap: wrap; }

.palette-enter-active, .palette-leave-active { transition: opacity var(--dur-fast) var(--ease-out); }
.palette-enter-active .palette, .palette-leave-active .palette { transition: transform var(--dur) var(--ease-spring), opacity var(--dur-fast); }
.palette-enter-from, .palette-leave-to { opacity: 0; }
.palette-enter-from .palette { transform: translateY(-8px) scale(0.98); }
.palette-leave-to .palette { transform: scale(0.98); opacity: 0; }
</style>
