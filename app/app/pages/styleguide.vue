<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
// Bảng mẫu giao diện, bố cục tài liệu ba cột: mục lục trái, nội dung giữa, mục lục trang bên phải.
// Trang tĩnh, không gọi API. Các mẫu tương tác chỉ chạy trên trình duyệt, không gửi dữ liệu.
useHead({ title: 'Bảng mẫu giao diện' })

const SAMPLE = 'Thiết bị hỏng ở phòng A1-305, cơ sở Thượng Lý, kỹ thuật viên Nguyễn Thị Ánh'

const GROUPS = [
  { id: 'nen-tang', label: 'Nền tảng', sections: [
    { id: 'mau', label: 'Màu' },
    { id: 'chu', label: 'Chữ' },
    { id: 'nen-be-mat', label: 'Nền và bề mặt' },
    { id: 'hinh-khoi', label: 'Khoảng cách và hình khối' },
  ] },
  { id: 'thanh-phan', label: 'Thành phần', sections: [
    { id: 'nut', label: 'Nút' },
    { id: 'o-nhap', label: 'Ô nhập và kiểm tra' },
    { id: 'tab', label: 'Tab và bộ lọc' },
    { id: 'tem', label: 'Tem trạng thái' },
    { id: 'bang', label: 'Bảng' },
    { id: 'thong-bao', label: 'Thông báo' },
    { id: 'tai-trong', label: 'Đang tải và trống' },
  ] },
  { id: 'kiem-tra', label: 'Kiểm tra', sections: [
    { id: 'hai-che-do', label: 'Hai chế độ' },
    { id: 'tuong-phan', label: 'Tương phản' },
  ] },
]

const STATUSES = ['DRAFT', 'SUBMITTED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REJECTED']
const STAMP_SHAPES: Record<string, string> = {
  DRAFT: 'Viền đứt, ô vuông rỗng đứt',
  SUBMITTED: 'Viền đơn, vòng tròn rỗng',
  ASSIGNED: 'Viền kép, vòng tròn nửa đặc',
  IN_PROGRESS: 'Nền cam nhạt, hình thoi đặc',
  RESOLVED: 'Viền đơn, chấm tròn trong vòng',
  CLOSED: 'Tem đảo màu, ô vuông đặc',
  REJECTED: 'Dấu X, không có số bước',
}

const COLORS = [
  { token: '--bg', role: 'Nền trang' },
  { token: '--card', role: 'Thẻ' },
  { token: '--sunk', role: 'Ô trong thẻ, đầu bảng' },
  { token: '--ink', role: 'Chữ chính' },
  { token: '--ink-soft', role: 'Chữ phụ' },
  { token: '--line', role: 'Viền ô nhập' },
  { token: '--rule', role: 'Kẻ phân cách' },
  { token: '--brand', role: 'Cam chủ đạo' },
  { token: '--primary', role: 'Nền nút chính' },
  { token: '--brand-ink', role: 'Cam làm chữ' },
  { token: '--brand-wash', role: 'Nền cảnh báo' },
  { token: '--hero-bg', role: 'Hero tối' },
]

const TICKETS = [
  { id: '3f2a91c0-5b1e-4c7a-9d2e-1a2b3c4d5e6f', asset: 'HAUI-LT-0001', room: 'A1-305', title: 'Máy chiếu không lên hình', status: 'IN_PROGRESS', who: 'Nguyễn Thị Ánh' },
  { id: '8c1d77e2-0a4b-4f3e-8b21-6c5d4e3f2a10', asset: 'HAUI-PC-0217', room: 'A1-302', title: 'Không vào được mạng', status: 'ASSIGNED', who: 'Trần Quốc Việt' },
  { id: 'b4e019aa-77c2-4d1b-a0f3-9e8d7c6b5a49', asset: 'HAUI-PR-0033', room: 'B2-110', title: 'Máy in kẹt giấy liên tục', status: 'RESOLVED', who: 'Nguyễn Thị Ánh' },
  { id: '0d93c5f1-2e6a-4b8c-9f17-3a4b5c6d7e8f', asset: 'HAUI-PC-0198', room: 'A1-305', title: 'Thiếu phần mềm MATLAB', status: 'SUBMITTED', who: '' },
  { id: 'e71b2c34-9d8a-4e5f-b6c7-d8e9f0a1b2c3', asset: 'HAUI-LT-0009', room: 'C3-201', title: 'Bàn phím liệt phím Ư', status: 'CLOSED', who: 'Lê Đức Mạnh' },
  { id: '5a6b7c8d-1e2f-4a3b-8c4d-5e6f7a8b9c0d', asset: 'HAUI-PC-0101', room: 'A1-301', title: 'Báo trùng với phiếu khác', status: 'REJECTED', who: '' },
]

// ---- Mục lục: theo dõi mục đang xem, thanh cam trượt tới đúng mục ----
const active = ref('mau')
const activeGroup = computed(() => GROUPS.find((g) => g.sections.some((s) => s.id === active.value)) ?? GROUPS[0]!)
const sidenav = ref<HTMLElement>()
const indicator = ref<Record<string, string>>({})

function placeIndicator() {
  const link = sidenav.value?.querySelector<HTMLElement>(`[data-section="${active.value}"]`)
  if (!link) return
  indicator.value = { '--iy': `${link.offsetTop}px`, '--ih': `${link.offsetHeight}` }
}

watch(active, () => nextTick(placeIndicator))

let observer: IntersectionObserver | undefined
onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
    if (visible[0]) active.value = visible[0].target.id
  }, { rootMargin: '-20% 0px -65% 0px' })
  document.querySelectorAll('.doc-section').forEach((el) => observer!.observe(el))
  placeIndicator()
  document.fonts?.ready.then(placeIndicator)
  measure()
})
onBeforeUnmount(() => observer?.disconnect())

// ---- Nút đang xử lý ----
const busy = ref(false)
function fakeSave() {
  if (busy.value) return
  busy.value = true
  setTimeout(() => { busy.value = false }, 1600)
}

// ---- Ô nhập: kiểm tra khi rời ô, gửi thử hiện mã phiếu mới ----
const form = reactive({ room: '', desc: '' })
const touched = reactive({ room: false, desc: false })
const ROOM = /^[A-Z]\d{0,2}-\d{3}$/
const errors = computed(() => ({
  room: !form.room ? 'Chưa nhập phòng.' : !ROOM.test(form.room.trim().toUpperCase()) ? 'Phòng có dạng A1-305.' : '',
  desc: form.desc.trim().length < 15 ? 'Mô tả ít nhất 15 ký tự để kỹ thuật viên hiểu sự cố.' : '',
}))
const created = ref('')
const sending = ref(false)
const { show } = useToast()

function submitDemo() {
  touched.room = true
  touched.desc = true
  if (errors.value.room || errors.value.desc) {
    show({ kind: 'error', title: 'Chưa gửi được', body: 'Sửa các ô đang báo lỗi rồi gửi lại.' })
    return
  }
  sending.value = true
  setTimeout(() => {
    sending.value = false
    created.value = crypto.randomUUID()
    show({ kind: 'success', title: 'Đã tạo phiếu mẫu', body: `Mã ${ticketCode(created.value)}. Đây là mẫu, không có dữ liệu nào được gửi.` })
  }, 900)
}

const copied = ref(false)
async function copyCode() {
  try {
    await navigator.clipboard.writeText(created.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1800)
  }
  catch {
    show({ kind: 'error', title: 'Không sao chép được', body: 'Trình duyệt chặn bộ nhớ tạm. Chọn mã và sao chép thủ công.' })
  }
}

// ---- Tab và bộ lọc trên dữ liệu mẫu ----
const filter = ref('ALL')
const filterTabs = computed(() => [
  { value: 'ALL', label: 'Tất cả', count: TICKETS.length },
  ...['SUBMITTED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED'].map((s) => ({
    value: s, label: STATUS_LABELS[s]!, count: TICKETS.filter((t) => t.status === s).length,
  })),
])
const filtered = computed(() => TICKETS.filter((t) => filter.value === 'ALL' || t.status === filter.value))

// ---- Tem đổi trạng thái để xem hiệu ứng đóng dấu ----
const demoStatus = ref('SUBMITTED')
function nextStatus() {
  const flow = ['SUBMITTED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED']
  demoStatus.value = flow[(flow.indexOf(demoStatus.value) + 1) % flow.length]!
}

// ---- Đang tải ----
const loadingDemo = ref(true)

// ---- Đo tương phản từ giá trị token thật trong từng chế độ ----
type RGBA = [number, number, number, number]
function parse(value: string): RGBA | null {
  const v = value.trim()
  if (v.startsWith('#')) {
    const h = v.slice(1)
    return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)).concat(1) as RGBA
  }
  const m = v.match(/rgba?\(([^)]+)\)/)
  if (!m) return null
  const parts = m[1]!.split(/[\s,/]+/).filter(Boolean).map(Number)
  return [parts[0]!, parts[1]!, parts[2]!, parts[3] ?? 1]
}
function over(top: RGBA, under: RGBA): RGBA {
  const a = top[3]
  return [0, 1, 2].map((i) => top[i]! * a + under[i]! * (1 - a)).concat(1) as RGBA
}
function luminance(c: RGBA) {
  const [r, g, b] = c.slice(0, 3).map((x) => x / 255).map((x) => (x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!
}
function ratio(a: RGBA, b: RGBA) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi! + 0.05) / (lo! + 0.05)
}

interface Pair { use: string; fg: string; bg: string; min: number }
const PAIRS: Pair[] = [
  { use: 'Chữ trên nền trang', fg: '--ink', bg: '--bg', min: 4.5 },
  { use: 'Chữ trên thẻ', fg: '--ink', bg: '--card', min: 4.5 },
  { use: 'Chữ ở đầu bảng, ô lõm', fg: '--ink', bg: '--sunk', min: 4.5 },
  { use: 'Chữ phụ trên nền trang', fg: '--ink-soft', bg: '--bg', min: 4.5 },
  { use: 'Chữ phụ ở ô lõm', fg: '--ink-soft', bg: '--sunk', min: 4.5 },
  { use: 'Chữ trên nút chính', fg: '--on-primary', bg: '--primary', min: 4.5 },
  { use: 'Cam làm chữ trên thẻ', fg: '--brand-ink', bg: '--card', min: 4.5 },
  { use: 'Cam làm chữ trên nền cảnh báo', fg: '--brand-ink', bg: '--brand-wash', min: 4.5 },
  { use: 'Tem đã đóng', fg: '--card', bg: '--ink', min: 4.5 },
  { use: 'Chữ phụ trên hero tối', fg: '--hero-soft', bg: '--hero-bg', min: 4.5 },
  { use: 'Viền ô nhập trên thẻ', fg: '--line', bg: '--card', min: 3 },
  { use: 'Ranh giới nút chính trên nền', fg: '--primary', bg: '--bg', min: 3 },
  { use: 'Vòng focus trên nền', fg: '--focus', bg: '--bg', min: 3 },
  { use: 'Vòng focus trên thẻ', fg: '--focus', bg: '--card', min: 3 },
]
// Chữ trên header kính và trên thẻ 94%, khi bên dưới là quầng cam đậm nhất (--glow-1)
const LAYERED = [
  { use: 'Chữ trên header kính, trên quầng cam', fg: '--ink', layer: '--header', min: 4.5 },
  { use: 'Chữ phụ trên header kính, trên quầng cam', fg: '--ink-soft', layer: '--header', min: 4.5 },
  { use: 'Chữ phụ trên thẻ, trên quầng cam', fg: '--ink-soft', layer: '--card-glass', min: 4.5 },
]

const modes = ref<HTMLElement>()
const tokens = ref<Record<string, Record<string, string>>>({})
function measure() {
  const names = new Set(['--glow-1', '--header', '--card-glass', ...COLORS.map((c) => c.token), ...PAIRS.flatMap((p) => [p.fg, p.bg])])
  for (const mode of ['light', 'dark']) {
    const el = modes.value?.querySelector(`[data-theme="${mode}"]`)
    if (!el) continue
    const s = getComputedStyle(el)
    tokens.value[mode] = Object.fromEntries([...names].map((n) => [n, s.getPropertyValue(n).trim()]))
  }
}

const contrast = computed(() => {
  const rows: { use: string; pair: string; min: number; light: number | null; dark: number | null }[] = []
  const get = (mode: string, name: string) => parse(tokens.value[mode]?.[name] ?? '')
  for (const p of PAIRS) {
    const row = { use: p.use, pair: `${p.fg} / ${p.bg}`, min: p.min, light: null as number | null, dark: null as number | null }
    for (const mode of ['light', 'dark'] as const) {
      const f = get(mode, p.fg), b = get(mode, p.bg)
      if (f && b) row[mode] = ratio(f, b)
    }
    rows.push(row)
  }
  for (const l of LAYERED) {
    const row = { use: l.use, pair: `${l.fg} / ${l.layer} trên --glow-1`, min: l.min, light: null as number | null, dark: null as number | null }
    for (const mode of ['light', 'dark'] as const) {
      const f = get(mode, l.fg), layer = get(mode, l.layer), glow = get(mode, '--glow-1'), bg = get(mode, '--bg')
      if (f && layer && glow && bg) row[mode] = ratio(f, over(layer, over(glow, bg)))
    }
    rows.push(row)
  }
  return rows
})
const passCount = computed(() => contrast.value.reduce((n, r) => n + Number((r.light ?? 0) >= r.min) + Number((r.dark ?? 0) >= r.min), 0))
</script>

<template>
  <div class="doc">
    <header class="doc-head reveal" style="--i: 0">
      <span class="eyebrow">Bảng mẫu · phiên bản B</span>
      <h1>Bảng mẫu giao diện</h1>
      <p class="lede">Token, chữ và thành phần của DX-Helpdesk. Mọi trang lấy màu, chữ và chuyển động từ đây.</p>
    </header>

    <!-- Cột trái: mục lục. Trên điện thoại thu gọn thành một khối mở được. -->
    <aside class="doc-left reveal" style="--i: 1">
      <details class="toc-mobile">
        <summary>Mục lục <span class="code">{{ activeGroup.label }}</span></summary>
        <nav aria-label="Mục lục bảng mẫu (điện thoại)">
          <template v-for="g in GROUPS" :key="g.id">
            <span class="eyebrow">{{ g.label }}</span>
            <a v-for="s in g.sections" :key="s.id" :href="`#${s.id}`">{{ s.label }}</a>
          </template>
        </nav>
      </details>

      <nav ref="sidenav" class="sidenav card" aria-label="Mục lục bảng mẫu" :style="indicator">
        <div class="card-head"><h2>Chủ đề</h2></div>
        <template v-for="g in GROUPS" :key="g.id">
          <span class="eyebrow sidenav-group">{{ g.label }}</span>
          <a
            v-for="s in g.sections" :key="s.id" :href="`#${s.id}`" class="sidenav-link" :data-section="s.id"
            :aria-current="active === s.id ? 'location' : undefined"
          >
            {{ s.label }}
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg>
          </a>
        </template>
        <span class="sidenav-indicator" aria-hidden="true" />
      </nav>
    </aside>

    <div class="doc-main">
      <section id="mau" class="doc-section card reveal" style="--i: 2" aria-labelledby="h-mau">
        <div class="card-head"><h2 id="h-mau">Màu</h2><span class="code">tokens.css</span></div>
        <p class="note">Một màu chủ đạo là cam. Nền ngà ấm ở chế độ sáng, than xanh ở chế độ tối. Cam đậm cho nút để chữ trắng đạt AA.</p>
        <ul class="swatches">
          <li v-for="c in COLORS" :key="c.token">
            <span class="chip" :style="{ background: `var(${c.token})` }" />
            <code class="code">{{ c.token }}</code>
            <span class="swatch-role">{{ c.role }}</span>
          </li>
        </ul>
      </section>

      <section id="chu" class="doc-section card reveal" style="--i: 3" aria-labelledby="h-chu">
        <div class="card-head"><h2 id="h-chu">Chữ</h2></div>
        <div class="specimen">
          <span class="eyebrow">Tiêu đề · Be Vietnam Pro 800, chữ mảnh Nunito 200</span>
          <p class="sp-display">Báo hỏng thiết bị</p>
          <p class="sp-thin">{{ SAMPLE }}</p>
        </div>
        <div class="specimen">
          <span class="eyebrow">Nội dung · Nunito 200 / 400 / 800</span>
          <p class="w200">{{ SAMPLE }}</p>
          <p>{{ SAMPLE }}</p>
          <p class="w800">{{ SAMPLE }}</p>
        </div>
        <div class="specimen">
          <span class="eyebrow">Mã · JetBrains Mono</span>
          <p class="mono">{{ SAMPLE }}</p>
          <p>Phiếu <span class="code">{{ ticketCode(TICKETS[0]!.id) }}</span>, tài sản <span class="code">HAUI-LT-0001</span>, phòng <span class="code">A1-305</span></p>
        </div>
        <table class="scale">
          <tbody>
            <tr><th><code class="code">--text-display</code></th><td class="sc-display">Aa Ấ</td></tr>
            <tr><th><code class="code">--text-2xl</code></th><td style="font-size: var(--text-2xl)">Aa Ấ</td></tr>
            <tr><th><code class="code">--text-xl</code></th><td style="font-size: var(--text-xl)">Aa Ấ</td></tr>
            <tr><th><code class="code">--text-lg</code></th><td style="font-size: var(--text-lg)">Aa Ấ</td></tr>
            <tr><th><code class="code">--text-base</code></th><td>Aa Ấ</td></tr>
            <tr><th><code class="code">--text-sm</code></th><td style="font-size: var(--text-sm)">Aa Ấ</td></tr>
          </tbody>
        </table>
      </section>

      <section id="nen-be-mat" class="doc-section card reveal" style="--i: 4" aria-labelledby="h-nen">
        <div class="card-head"><h2 id="h-nen">Nền và bề mặt</h2></div>
        <p class="note">Ba lớp từ sau ra trước. Chữ dày luôn nằm trên lớp đặc.</p>
        <div class="layers">
          <div class="layer layer-bg">
            <span class="eyebrow">Lớp 1 · Nền</span>
            <p>Ngà ấm, quầng cam và hồng đào trôi chậm, lưới chấm 24px mờ dần, hạt nhiễu 4%.</p>
          </div>
          <div class="layer card">
            <span class="eyebrow">Lớp 2 · Thẻ</span>
            <p>Nền đặc 94%, viền gradient cam sang trong suốt. Rê chuột để thấy vệt sáng.</p>
          </div>
          <div class="layer table-wrap">
            <table class="table mini">
              <thead><tr><th>Lớp 3 · Dữ liệu</th><th>Nền</th></tr></thead>
              <tbody>
                <tr><td>Bảng, form</td><td>Đặc 100%</td></tr>
                <tr><td>Đầu bảng</td><td><code class="code">--sunk</code></td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="hero" data-parallax>
          <span class="hero-glow" aria-hidden="true" />
          <span class="eyebrow hero-eyebrow">Hero trang chủ</span>
          <p class="hero-title">Báo hỏng trong một phút.</p>
          <p>Dải tối ngay trong chế độ sáng làm điểm nhấn. Quầng cam lệch theo con trỏ, tối đa 20px.</p>
        </div>
      </section>

      <section id="hinh-khoi" class="doc-section card reveal" style="--i: 5" aria-labelledby="h-hk">
        <div class="card-head"><h2 id="h-hk">Khoảng cách và hình khối</h2></div>
        <div class="metrics">
          <ul class="spaces">
            <li v-for="n in 8" :key="n"><code class="code">--space-{{ n }}</code><span class="space-bar" :style="{ width: `var(--space-${n})` }" /></li>
          </ul>
          <div class="boxes">
            <div class="box" style="border-radius: var(--radius-card)"><code class="code">--radius-card</code> 10px</div>
            <div class="box" style="border-radius: var(--radius-control)"><code class="code">--radius-control</code> 5px</div>
            <div class="box" style="box-shadow: var(--shadow)"><code class="code">--shadow</code></div>
            <div class="box" style="box-shadow: var(--shadow-lift)"><code class="code">--shadow-lift</code></div>
          </div>
          <ul class="durations">
            <li><code class="code">--dur-fast</code> 150ms, nút và hover</li>
            <li><code class="code">--dur</code> 250ms, tab, thẻ, header</li>
            <li><code class="code">--dur-slow</code> 400ms, khối hiện khi tải trang</li>
            <li><code class="code">--stagger</code> 60ms giữa hai khối</li>
          </ul>
        </div>
      </section>

      <section id="nut" class="doc-section card reveal" style="--i: 6" aria-labelledby="h-nut">
        <div class="card-head"><h2 id="h-nut">Nút</h2></div>
        <div class="row">
          <button class="btn" type="button">Gửi báo hỏng</button>
          <button class="btn secondary" type="button">Lưu bản nháp</button>
          <button class="btn quiet" type="button">Huỷ</button>
          <button class="btn btn-sm" type="button">Nhận việc</button>
          <button class="btn" type="button" :aria-busy="busy" @click="fakeSave">{{ busy ? 'Đang lưu' : 'Bấm để thử trạng thái đang lưu' }}</button>
          <button class="btn" type="button" disabled>Chưa đủ thông tin</button>
        </div>
        <p class="note">Hover: lớp sáng lướt qua, nút nổi 2px. Bấm: lún xuống. Đang lưu: spinner, không bấm lặp được.</p>
      </section>

      <section id="o-nhap" class="doc-section card reveal" style="--i: 7" aria-labelledby="h-input">
        <div class="card-head"><h2 id="h-input">Ô nhập và kiểm tra</h2><span class="eyebrow">Mẫu, không gửi dữ liệu</span></div>
        <form class="fields" novalidate @submit.prevent="submitDemo">
          <div class="field">
            <label class="field-label" for="sg-asset">Mã tài sản</label>
            <input id="sg-asset" class="input mono" value="HAUI-LT-0001" readonly>
            <span class="field-help">Lấy từ hệ thống tài sản, không sửa được.</span>
          </div>
          <div class="field">
            <label class="field-label" for="sg-cat">Loại sự cố</label>
            <select id="sg-cat" class="input">
              <option v-for="(label, code) in CATEGORY_LABELS" :key="code">{{ label }}</option>
            </select>
          </div>
          <div class="field">
            <label class="field-label" for="sg-room">Phòng</label>
            <input
              id="sg-room" v-model="form.room" class="input mono" placeholder="A1-305" autocomplete="off"
              :aria-invalid="touched.room && !!errors.room" aria-describedby="sg-room-msg" @blur="touched.room = true"
            >
            <Transition name="field-msg">
              <span v-if="touched.room && errors.room" id="sg-room-msg" class="field-error">{{ errors.room }}</span>
            </Transition>
          </div>
          <div class="field field-wide">
            <label class="field-label" for="sg-desc">Mô tả</label>
            <textarea
              id="sg-desc" v-model="form.desc" class="input" :placeholder="SAMPLE"
              :aria-invalid="touched.desc && !!errors.desc" aria-describedby="sg-desc-msg" @blur="touched.desc = true"
            />
            <Transition name="field-msg">
              <span v-if="touched.desc && errors.desc" id="sg-desc-msg" class="field-error">{{ errors.desc }}</span>
            </Transition>
          </div>
          <div class="field-wide row">
            <button class="btn" type="submit" :aria-busy="sending">Gửi thử</button>
          </div>
        </form>
        <Transition name="field-msg">
          <div v-if="created" class="created" role="status">
            <span class="eyebrow">Phiếu mẫu vừa tạo</span>
            <span class="created-code">{{ ticketCode(created) }}</span>
            <button class="btn secondary btn-sm" type="button" @click="copyCode">{{ copied ? 'Đã sao chép' : 'Sao chép mã đầy đủ' }}</button>
          </div>
        </Transition>
      </section>

      <section id="tab" class="doc-section card reveal" style="--i: 8" aria-labelledby="h-tab">
        <div class="card-head"><h2 id="h-tab">Tab và bộ lọc</h2></div>
        <UiTabs v-model="filter" :items="filterTabs" label="Lọc phiếu mẫu theo trạng thái" />
        <TransitionGroup tag="ul" name="list" class="mini-list">
          <li v-for="t in filtered" :key="t.id">
            <span class="code">{{ ticketCode(t.id) }}</span>
            <span class="mini-title">{{ t.title }}</span>
            <StatusStamp :status="t.status" />
          </li>
        </TransitionGroup>
      </section>

      <section id="tem" class="doc-section card reveal" style="--i: 9" aria-labelledby="h-tem">
        <div class="card-head"><h2 id="h-tem">Tem trạng thái</h2></div>
        <p class="note">Bảy trạng thái thật. Mỗi tem khác nhau ở chữ, số bước và hình, không chỉ ở màu.</p>
        <ul class="stamps">
          <li v-for="s in STATUSES" :key="s">
            <StatusStamp :status="s" />
            <span class="stamp-meta"><code class="code">{{ s }}</code> {{ STAMP_SHAPES[s] }}</span>
          </li>
        </ul>
        <div class="row stamp-demo">
          <StatusStamp :status="demoStatus" />
          <button class="btn secondary btn-sm" type="button" @click="nextStatus">Chuyển bước tiếp theo</button>
        </div>
      </section>

      <section id="bang" class="doc-section card reveal" style="--i: 10" aria-labelledby="h-bang">
        <div class="card-head"><h2 id="h-bang">Bảng</h2></div>
        <div class="table-wrap">
          <table class="table">
            <thead><tr><th>Mã phiếu</th><th>Thiết bị</th><th>Phòng</th><th>Sự cố</th><th>Trạng thái</th><th>Kỹ thuật viên</th></tr></thead>
            <tbody>
              <tr v-for="t in TICKETS" :key="t.id">
                <td><span class="code">{{ ticketCode(t.id) }}</span></td>
                <td><span class="code">{{ t.asset }}</span></td>
                <td><span class="code">{{ t.room }}</span></td>
                <td>{{ t.title }}</td>
                <td><StatusStamp :status="t.status" /></td>
                <td>{{ t.who || 'Chưa phân công' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section id="thong-bao" class="doc-section card reveal" style="--i: 11" aria-labelledby="h-tb">
        <div class="card-head"><h2 id="h-tb">Thông báo</h2></div>
        <div class="row">
          <button class="btn secondary" type="button" @click="show({ kind: 'success', title: 'Đã nhận việc', body: 'Phiếu chuyển sang Đang xử lý.' })">Thông báo thành công</button>
          <button class="btn secondary" type="button" @click="show({ kind: 'error', title: 'Không lưu được', body: 'Mất kết nối tới máy chủ. Thử lại sau ít phút.' })">Thông báo lỗi</button>
          <button class="btn secondary" type="button" @click="show({ kind: 'info', title: 'Có phiếu mới', body: 'Phòng A1-305 vừa báo hỏng máy chiếu.' })">Thông báo thường</button>
        </div>
        <p class="note">Góc dưới phải, tự ẩn sau 5 giây (lỗi 8 giây), dừng đếm khi trỏ chuột hoặc focus. Esc hoặc nút Đóng để tắt.</p>
      </section>

      <section id="tai-trong" class="doc-section card reveal" style="--i: 12" aria-labelledby="h-tt">
        <div class="card-head">
          <h2 id="h-tt">Đang tải và trống</h2>
          <button class="btn quiet btn-sm" type="button" @click="loadingDemo = !loadingDemo">{{ loadingDemo ? 'Xem trạng thái trống' : 'Xem đang tải' }}</button>
        </div>
        <div v-if="loadingDemo" class="table-wrap" aria-busy="true" aria-label="Đang tải danh sách phiếu">
          <div v-for="n in 4" :key="n" class="skel-row">
            <span class="skeleton" style="width: 5.5rem; height: 1.4rem" />
            <span class="skeleton" style="width: 6.5rem; height: 1.4rem" />
            <span class="skeleton" style="flex: 1; height: 1rem" />
            <span class="skeleton" style="width: 8rem; height: 1.5rem" />
          </div>
        </div>
        <div v-else class="empty">
          <svg class="empty-icon" viewBox="0 0 48 48" aria-hidden="true"><rect x="8" y="10" width="32" height="28" rx="4" /><path d="M8 18h32M16 26h10M16 31h16" /></svg>
          <span class="empty-title">Chưa có phiếu nào</span>
          <p>Khi thiết bị trong phòng lab gặp sự cố, tạo phiếu báo hỏng để kỹ thuật viên xử lý.</p>
          <button class="btn" type="button">Báo hỏng thiết bị</button>
        </div>
      </section>

      <section id="hai-che-do" class="doc-section card reveal" style="--i: 13" aria-labelledby="h-mode">
        <div class="card-head"><h2 id="h-mode">Hai chế độ</h2></div>
        <div ref="modes" class="modes">
          <div v-for="mode in ['light', 'dark']" :key="mode" class="mode-panel" :data-theme="mode">
            <span class="eyebrow">{{ mode === 'light' ? 'Sáng · ngà ấm' : 'Tối · than xanh' }}</span>
            <div class="card mode-card">
              <p class="mode-title">Phiếu <span class="code">{{ ticketCode(TICKETS[0]!.id) }}</span></p>
              <p>{{ SAMPLE }}</p>
              <div class="row">
                <StatusStamp status="IN_PROGRESS" />
                <StatusStamp status="RESOLVED" />
                <StatusStamp status="CLOSED" />
              </div>
              <div class="row">
                <button class="btn btn-sm" type="button">Nghiệm thu</button>
                <button class="btn secondary btn-sm" type="button">Mở lại</button>
              </div>
              <span class="field-error">Phải nhập lý do khi mở lại.</span>
            </div>
          </div>
        </div>
      </section>

      <section id="tuong-phan" class="doc-section card reveal" style="--i: 14" aria-labelledby="h-tp">
        <div class="card-head"><h2 id="h-tp">Tương phản</h2><span class="code">{{ passCount }} / {{ contrast.length * 2 }} đạt</span></div>
        <p class="note">Đo lúc chạy từ token thật. Chữ thường cần 4.5:1, viền và vòng focus cần 3:1. Ba dòng cuối tính cả lớp kính đè lên quầng cam.</p>
        <div class="table-wrap">
          <table class="table">
            <thead><tr><th>Dùng cho</th><th>Cặp token</th><th>Cần</th><th>Sáng</th><th>Tối</th></tr></thead>
            <tbody>
              <tr v-for="r in contrast" :key="r.use">
                <td>{{ r.use }}</td>
                <td><span class="code">{{ r.pair }}</span></td>
                <td class="mono">{{ r.min }}:1</td>
                <td v-for="m in ['light', 'dark'] as const" :key="m" class="mono">
                  <template v-if="r[m] != null">
                    {{ r[m]!.toFixed(2) }}:1
                    <strong :class="r[m]! >= r.min ? 'pass' : 'fail'">{{ r[m]! >= r.min ? 'Đạt' : 'Không đạt' }}</strong>
                  </template>
                  <template v-else>chưa đo</template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <aside class="doc-right reveal" style="--i: 2" aria-label="Trên trang này">
      <span class="eyebrow">Trên trang này · {{ activeGroup.label }}</span>
      <ul>
        <li v-for="s in activeGroup.sections" :key="s.id">
          <a :href="`#${s.id}`" :aria-current="active === s.id ? 'location' : undefined">{{ s.label }}</a>
        </li>
      </ul>
    </aside>
  </div>
</template>

<style scoped>
.doc {
  display: grid;
  grid-template-columns: 17rem minmax(0, 1fr) 12rem;
  grid-template-areas: "head head head" "left main right";
  gap: var(--space-5);
  align-items: start;
}

.doc-head { grid-area: head; padding-top: var(--space-4); }
.doc-head h1 { font-size: var(--text-display); letter-spacing: -0.025em; margin-top: var(--space-2); }

.doc-left { grid-area: left; position: sticky; top: calc(var(--header-h) + var(--space-3)); }
/* minmax(0, 1fr): cột không nở theo bề rộng tối thiểu của bảng bên trong */
.doc-main { grid-area: main; display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-5); min-width: 0; }
.doc-right { grid-area: right; position: sticky; top: calc(var(--header-h) + var(--space-3)); }

.sidenav { position: relative; display: grid; padding-top: var(--space-5); padding-bottom: var(--space-4); }
.sidenav .card-head h2 { font-size: var(--text-lg); }
.sidenav-group { margin: var(--space-3) 0 var(--space-1); }

.sidenav-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-2) var(--space-2) var(--space-3);
  font-weight: 600;
  color: var(--ink);
  text-decoration: none;
  border-radius: var(--radius-control);
  transition: color var(--dur-fast), background-color var(--dur-fast);
}

.sidenav-link svg { width: 1rem; height: 1rem; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; opacity: 0.5; transition: transform var(--dur) var(--ease-out); }
.sidenav-link:hover { background: var(--sunk); }
.sidenav-link:hover svg { transform: translateX(3px); }
.sidenav-link[aria-current] { color: var(--brand-ink); }

/* Thanh cam trượt bằng transform giữa các mục, không nhảy */
.sidenav-indicator {
  position: absolute;
  left: 0;
  top: 0;
  width: 3px;
  height: 1px;
  background: var(--brand);
  border-radius: 0 3px 3px 0;
  transform-origin: top;
  transform: translateY(var(--iy, 0)) scaleY(var(--ih, 0));
  transition: transform var(--dur-slow) var(--ease-out);
}

.toc-mobile { display: none; }

.doc-right ul { list-style: none; margin: var(--space-2) 0 0; padding: 0; border-left: 1px solid var(--rule); }
.doc-right a {
  display: block;
  margin-left: -1px;
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-sm);
  color: var(--ink-soft);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: color var(--dur-fast), border-color var(--dur-fast);
}
.doc-right a:hover { color: var(--ink); }
.doc-right a[aria-current] { color: var(--ink); font-weight: 700; border-left-color: var(--brand); }

.note { color: var(--ink-soft); max-width: 46rem; }
.mono { font-family: var(--font-mono); }
.row { display: flex; flex-wrap: wrap; gap: var(--space-3); align-items: center; }

.swatches { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(7.5rem, 1fr)); gap: var(--space-3); }
.swatches li { display: grid; gap: var(--space-1); padding: var(--space-2); background: var(--card); border: 1px solid var(--rule); border-radius: var(--radius-control); }
.chip { height: 3.25rem; border-radius: var(--radius-control); border: 1px solid var(--rule); }
.swatch-role { font-size: var(--text-sm); color: var(--ink-soft); }

.specimen { padding: var(--space-4); margin-bottom: var(--space-4); background: var(--sunk); border-radius: var(--radius-control); }
.specimen p { margin: var(--space-2) 0 0; font-size: var(--text-lg); }
.specimen .sp-display { font-family: var(--font-display); font-weight: 800; font-size: var(--text-display); line-height: 1.05; letter-spacing: -0.025em; }
.specimen .sp-thin { font-family: var(--font-body); font-weight: 200; font-size: var(--text-xl); }
.w200 { font-weight: 200; }
.w800 { font-weight: 800; }

.scale { border-collapse: collapse; }
.scale th { text-align: left; font-weight: 400; padding: var(--space-1) var(--space-4) var(--space-1) 0; }
.scale td { font-family: var(--font-display); font-weight: 800; line-height: 1.2; }
.sc-display { font-size: var(--text-display); }

.layers { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: var(--space-4); margin-bottom: var(--space-5); }
.layer { min-height: 9rem; }
.layer-bg { padding: var(--space-5); border: 1px dashed var(--line); border-radius: var(--radius-card); background: transparent; }
.layer p { margin: var(--space-2) 0 0; font-size: var(--text-sm); }
.table.mini { min-width: 0; }

.hero-eyebrow { color: var(--hero-soft); }
.hero .hero-title { font-family: var(--font-display); font-weight: 800; font-size: var(--text-display); line-height: 1.02; letter-spacing: -0.025em; color: var(--hero-ink); max-width: 12ch; margin: var(--space-2) 0 var(--space-4); }

.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: var(--space-5); }
.spaces, .durations { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-2); }
.spaces li { display: grid; grid-template-columns: 6.5rem 1fr; gap: var(--space-2); align-items: center; }
.space-bar { height: 0.6rem; border-radius: 3px; background: var(--brand); }
.boxes { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.box { padding: var(--space-4) var(--space-2); text-align: center; font-size: var(--text-sm); background: var(--card); border: 1px solid var(--rule); }

.fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: var(--space-4) var(--space-5); }
.field-wide { grid-column: 1 / -1; }

.created {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-4);
  margin-top: var(--space-5);
  padding: var(--space-4);
  background: var(--sunk);
  border-left: 3px solid var(--brand);
  border-radius: var(--radius-control);
}

.created-code { font-family: var(--font-mono); font-weight: 700; font-size: var(--text-xl); letter-spacing: 0.08em; }

.mini-list { list-style: none; margin: var(--space-4) 0 0; padding: 0; display: grid; gap: var(--space-2); position: relative; }
.mini-list li { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-3); background: var(--card); border: 1px solid var(--rule); border-radius: var(--radius-control); }
.mini-title { flex: 1 1 10rem; min-width: 0; }

.list-enter-active,
.list-leave-active { transition: opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-out); }
.list-enter-from { opacity: 0; transform: translateY(-8px); }
.list-leave-to { opacity: 0; transform: translateX(16px); }
.list-leave-active { position: absolute; left: 0; right: 0; }
.list-move { transition: transform var(--dur) var(--ease-out); }

.stamps { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-3); }
.stamps li { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2) var(--space-4); }
.stamps .stamp { min-width: 12rem; }
.stamp-meta { font-size: var(--text-sm); color: var(--ink-soft); }
.stamp-demo { margin-top: var(--space-5); padding-top: var(--space-4); border-top: 1px solid var(--rule); }

.skel-row { display: flex; gap: var(--space-4); align-items: center; padding: var(--space-3) var(--space-4); border-top: 1px solid var(--rule); }
.skel-row:first-child { border-top: 0; }
.empty-icon { width: 3rem; height: 3rem; fill: none; stroke: var(--brand-ink); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

.modes { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: var(--space-4); }
.mode-panel { display: grid; gap: var(--space-3); padding: var(--space-4); color: var(--ink); background: var(--bg); border-radius: var(--radius-card); border: 1px solid var(--rule); }
.mode-card { display: grid; gap: var(--space-3); }
.mode-card p { margin: 0; }
.mode-title { font-family: var(--font-display); font-weight: 800; font-size: var(--text-xl); }

.pass, .fail { margin-left: var(--space-2); font-family: var(--font-body); }
.fail { color: var(--brand-ink); text-decoration: underline wavy; }

@media (max-width: 80rem) {
  .doc { grid-template-columns: 16rem minmax(0, 1fr); grid-template-areas: "head head" "left main"; }
  .doc-right { display: none; }
}

@media (max-width: 56rem) {
  .doc { grid-template-columns: minmax(0, 1fr); grid-template-areas: "head" "left" "main"; }
  .doc-left { position: static; }
  .sidenav { display: none; }
  .toc-mobile { display: block; }
  .toc-mobile summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-3) var(--space-4);
    font-weight: 800;
    background: var(--card);
    border: 1px solid var(--rule);
    border-radius: var(--radius-control);
    cursor: pointer;
  }
  .toc-mobile nav { display: grid; gap: var(--space-1); padding: var(--space-3) var(--space-4); background: var(--card); border: 1px solid var(--rule); border-top: 0; }
  .toc-mobile nav a { padding: var(--space-2) 0; color: var(--ink); }
  .stamps .stamp { min-width: 0; }
  .hero { padding: var(--space-7) var(--space-4); }
}
</style>
