// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Hiệu ứng theo con trỏ, chỉ trên thiết bị có chuột:
// - .card: cập nhật --x, --y cho vệt sáng và viền sáng.
// - [data-parallax]: cập nhật --px, --py, lệch tối đa 20px quanh tâm phần tử.
// Một listener ủy quyền cho cả trang, gộp theo requestAnimationFrame.
// Đồng thời đánh dấu html.is-hidden khi tab bị ẩn để dừng chuyển động nền.

const PARALLAX_MAX = 20

export default defineNuxtPlugin(() => {
  const root = document.documentElement
  const onVisibility = () => root.classList.toggle('is-hidden', document.hidden)
  document.addEventListener('visibilitychange', onVisibility)
  onVisibility()

  const fine = window.matchMedia('(hover: hover) and (pointer: fine)')
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)')
  let frame = 0
  let last: PointerEvent | null = null

  function update() {
    frame = 0
    const e = last
    if (!e || !(e.target instanceof Element)) return

    const card = e.target.closest<HTMLElement>('.card')
    if (card) {
      const r = card.getBoundingClientRect()
      card.style.setProperty('--x', `${e.clientX - r.left}px`)
      card.style.setProperty('--y', `${e.clientY - r.top}px`)
    }

    if (reduce.matches) return
    const scene = e.target.closest<HTMLElement>('[data-parallax]')
    if (scene) {
      const r = scene.getBoundingClientRect()
      const dx = (e.clientX - r.left) / r.width - 0.5
      const dy = (e.clientY - r.top) / r.height - 0.5
      scene.style.setProperty('--px', `${(dx * 2 * PARALLAX_MAX).toFixed(1)}px`)
      scene.style.setProperty('--py', `${(dy * 2 * PARALLAX_MAX).toFixed(1)}px`)
    }
  }

  document.addEventListener('pointermove', (e) => {
    if (!fine.matches || e.pointerType !== 'mouse') return
    last = e
    if (!frame) frame = requestAnimationFrame(update)
  }, { passive: true })

  // Rời khỏi vùng parallax thì quầng trở về giữa
  document.addEventListener('pointerout', (e) => {
    if (!(e.target instanceof Element)) return
    const scene = e.target.closest<HTMLElement>('[data-parallax]')
    if (scene && !(e.relatedTarget instanceof Node && scene.contains(e.relatedTarget))) {
      scene.style.setProperty('--px', '0px')
      scene.style.setProperty('--py', '0px')
    }
  }, { passive: true })
})
