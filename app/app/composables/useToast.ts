// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Thông báo góc màn hình. ToastHost trong app.vue hiển thị danh sách này.

export interface Toast {
  id: number
  kind: 'success' | 'error' | 'info'
  title: string
  body?: string
}

let nextId = 1
const timers = new Map<number, ReturnType<typeof setTimeout>>()

export function useToast() {
  const toasts = useState<Toast[]>('toasts', () => [])

  function dismiss(id: number) {
    clearTimeout(timers.get(id))
    timers.delete(id)
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  // Lỗi ở lại lâu hơn để kịp đọc
  function schedule(id: number, kind: Toast['kind']) {
    timers.set(id, setTimeout(() => dismiss(id), kind === 'error' ? 8000 : 5000))
  }

  function show(toast: Omit<Toast, 'id'>) {
    const id = nextId++
    toasts.value = [...toasts.value.slice(-3), { id, ...toast }]
    schedule(id, toast.kind)
    return id
  }

  // Giữ thông báo khi người dùng đang trỏ chuột hoặc focus vào nó
  function hold(id: number) {
    clearTimeout(timers.get(id))
  }

  function release(id: number) {
    const t = toasts.value.find((x) => x.id === id)
    if (t) schedule(id, t.kind)
  }

  return { toasts, show, dismiss, hold, release }
}
