// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Cập nhật trạng thái phiếu thời gian thực qua SSE (GET /api/data/events/stream).
// Một kết nối EventSource cho cả ứng dụng; trang đăng ký onStatus để nạp lại dữ liệu.
// Đi qua /gw để server Nuxt gắn token; Data API chỉ gửi sự kiện của phiếu người xem được mở.
// Mất kết nối (NATS tắt, token hết hạn, mạng rớt) thì thử lại với thời gian chờ tăng dần.

export interface TicketStatusEvent {
  ticket_id: string
  action: string
  from_status: string | null
  to_status: string
  co_so: string | null
  actor_sub: string
  occurred_at: string
  title: string
}

type Listener = (e: TicketStatusEvent) => void
const listeners = new Set<Listener>()
let source: EventSource | null = null
let retryTimer: ReturnType<typeof setTimeout> | undefined
let delay = 2000

export function useTicketEvents() {
  // idle: chưa bắt đầu; live: đang nhận; down: mất kết nối, đang thử lại
  const state = useState<'idle' | 'live' | 'down'>('ticket-events-state', () => 'idle')

  function schedule() {
    clearTimeout(retryTimer)
    retryTimer = setTimeout(connect, delay)
    delay = Math.min(delay * 2, 30000)
  }

  function connect() {
    if (import.meta.server || source) return
    const es = new EventSource('/gw/api/data/events/stream')
    source = es
    es.onopen = () => {
      state.value = 'live'
      delay = 2000
    }
    es.addEventListener('status', (msg) => {
      try {
        const data = JSON.parse((msg as MessageEvent).data) as TicketStatusEvent
        listeners.forEach(fn => fn(data))
      }
      catch { /* bỏ qua khung hỏng */ }
    })
    // Máy chủ chủ động đóng: token hết hạn hoặc NATS mất; mở lại kết nối mới
    const reopen = () => {
      es.close()
      source = null
      state.value = 'down'
      schedule()
    }
    es.addEventListener('expired', () => {
      es.close()
      source = null
      delay = 500
      schedule()
    })
    es.addEventListener('bus-down', reopen)
    es.onerror = () => {
      // Trình duyệt tự nối lại khi readyState là CONNECTING; CLOSED (ví dụ 503) thì tự lo
      state.value = 'down'
      if (es.readyState === EventSource.CLOSED) reopen()
    }
  }

  function stop() {
    clearTimeout(retryTimer)
    source?.close()
    source = null
    state.value = 'idle'
  }

  function onStatus(fn: Listener) {
    listeners.add(fn)
    onBeforeUnmount(() => listeners.delete(fn))
  }

  return { state, connect, stop, onStatus }
}
