// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Chế độ sáng/tối: 'light' | 'dark' do người dùng chọn, null là theo hệ điều hành.
// Lựa chọn lưu trong localStorage; script trong nuxt.config đặt data-theme trước khi vẽ
// để không chớp màu. localStorage có thể bị chặn (chế độ riêng tư), nên luôn bọc try/catch.

export type Theme = 'light' | 'dark'
const KEY = 'dxlab-theme'

function systemTheme(): Theme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function useTheme() {
  const chosen = useState<Theme | null>('theme-choice', () => null)
  const current = useState<Theme>('theme-current', () => 'light')

  function read() {
    let saved: string | null = null
    try { saved = localStorage.getItem(KEY) } catch { /* bộ nhớ bị chặn: theo hệ điều hành */ }
    chosen.value = saved === 'light' || saved === 'dark' ? saved : null
    current.value = chosen.value ?? systemTheme()
  }

  function apply(theme: Theme) {
    chosen.value = theme
    current.value = theme
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem(KEY, theme) } catch { /* không lưu được thì chỉ áp dụng cho phiên này */ }
  }

  function set(theme: Theme) {
    if (theme === current.value) return
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const doc = document as Document & { startViewTransition?: (cb: () => void) => unknown }
    if (doc.startViewTransition && !reduce) {
      doc.startViewTransition(() => apply(theme))
      return
    }
    // Trình duyệt chưa có View Transitions: chuyển màu bằng transition trong 300ms
    const root = document.documentElement
    if (!reduce) root.classList.add('theme-fading')
    apply(theme)
    window.setTimeout(() => root.classList.remove('theme-fading'), 320)
  }

  function toggle() {
    set(current.value === 'dark' ? 'light' : 'dark')
  }

  return { chosen, current, read, set, toggle }
}
