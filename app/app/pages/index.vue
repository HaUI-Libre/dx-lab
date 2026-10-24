<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
interface Me {
  sub: string
  username: string
  name?: string
  email?: string
  roles: string[]
  co_so?: string
}

interface GuideDoc {
  id: string
  title: string
  description: string
  category: string
  categoryLabel: string
  fileName: string
  filePath: string
  fileSize: string
  allowedRoles: string[]
}

const ROLE_LABELS: Record<string, string> = {
  ROLE_STUDENT: 'Sinh viên',
  ROLE_TECHNICIAN: 'Kỹ thuật viên',
  ROLE_LAB_MANAGER: 'Trưởng phòng lab',
  ROLE_ADMIN: 'Quản trị hệ thống',
}

const CAMPUS_LABELS: Record<string, string> = {
  CS1: 'Cơ sở 1',
  CS2: 'Cơ sở 2',
  CS3: 'Cơ sở 3',
}

const route = useRoute()
const loginFailed = computed(() => route.query.loi === 'dang-nhap')

// Thông tin người dùng lấy qua gateway: trình duyệt -> /gw -> APISIX /api/me
const { data: me, error, status } = await useFetch<Me>('/gw/api/me', {
  key: 'me',
  retry: false,
})

// Lấy danh sách tài liệu gợi ý theo quyền người dùng
const { data: quickDocs, pending: docsPending } = await useFetch<GuideDoc[]>('/api/portal/documents', {
  key: 'home-docs',
  lazy: true,
})

const notLoggedIn = computed(() => error.value?.statusCode === 401)
const roleNames = computed(() => (me.value?.roles ?? []).map(r => ROLE_LABELS[r] ?? r))
const campus = computed(() => {
  const code = me.value?.co_so
  return code ? `${CAMPUS_LABELS[code] ?? code} (${code})` : null
})
const canSeeStats = computed(() => hasRole(me.value as never, 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'))

// Vào thử theo vai trò khi bật chế độ demo: chỉ điền sẵn tên đăng nhập trên Keycloak
const demoLogin = useRuntimeConfig().public.demoLogin
const DEMO_ROLES = [
  { user: 'sinhvien', label: 'Sinh viên', note: 'Báo hỏng, theo dõi phiếu' },
  { user: 'truongphong', label: 'Trưởng phòng lab', note: 'Tiếp nhận, phân công, nghiệm thu' },
  { user: 'kythuatvien', label: 'Kỹ thuật viên', note: 'Nhận việc, lập biên bản' },
  { user: 'quantri', label: 'Quản trị', note: 'Cả ba cơ sở' },
]
useHead({ title: 'DX-Helpdesk' })
</script>

<template>
  <div class="home">
    <p v-if="status === 'pending'" class="hint">Đang tải thông tin tài khoản…</p>

    <template v-else-if="me">
      <!-- Hero tối ngay trong chế độ sáng làm điểm nhấn; quầng cam lệch theo con trỏ -->
      <section class="hero reveal" style="--i: 0" data-parallax>
        <span class="hero-glow" aria-hidden="true" />
        <span class="eyebrow hero-eyebrow">Báo hỏng và sửa chữa thiết bị CNTT · HaUI</span>
        <h1>Xin chào, {{ me.name || me.username }}</h1>
        <p class="hero-lede">Hệ thống Tiếp nhận Báo hỏng và Quản lý Sửa chữa Thiết bị CNTT HaUI</p>
        <div class="hero-actions">
          <NuxtLink to="/tickets/new" class="btn">Báo hỏng thiết bị</NuxtLink>
          <NuxtLink to="/tickets" class="btn hero-secondary">Yêu cầu và hàng đợi</NuxtLink>
        </div>
      </section>

      <div class="grid">
        <section class="card account reveal" style="--i: 1" aria-labelledby="h-account">
          <div class="card-head"><h2 id="h-account">Tài khoản</h2></div>
          <dl class="info">
            <div><dt>Tài khoản</dt><dd><span class="code">{{ me.username }}</span></dd></div>
            <div><dt>Vai trò</dt><dd>{{ roleNames.length ? roleNames.join(', ') : 'Chưa có vai trò DX-Helpdesk' }}</dd></div>
            <div><dt>Cơ sở</dt><dd><template v-if="campus">{{ campus }}</template><span v-else class="hint">Chưa gán cơ sở</span></dd></div>
            <div v-if="me.email"><dt>Email</dt><dd>{{ me.email }}</dd></div>
          </dl>
          <p class="hint small">Thông tin lấy từ <code class="code">GET /api/me</code> qua API Gateway.</p>
        </section>

        <nav class="shortcuts" aria-label="Lối tắt">
          <NuxtLink to="/tickets/new" class="card shortcut reveal" style="--i: 2">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L4 17v3h3l5.3-5.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4Z" /></svg>
            <span class="shortcut-title">Báo hỏng</span>
            <span class="shortcut-text">Chọn thiết bị của bạn, mô tả sự cố, gửi kèm ảnh.</span>
          </NuxtLink>
          <NuxtLink to="/tickets" class="card shortcut reveal" style="--i: 3">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01" /></svg>
            <span class="shortcut-title">Theo dõi phiếu</span>
            <span class="shortcut-text">Lọc theo trạng thái, cơ sở; xem dòng thời gian xử lý.</span>
          </NuxtLink>
          <NuxtLink v-if="canSeeStats" to="/dashboard" class="card shortcut reveal" style="--i: 4">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></svg>
            <span class="shortcut-title">Thống kê</span>
            <span class="shortcut-text">Số phiếu, thời gian xử lý, quá hạn theo cơ sở.</span>
          </NuxtLink>
        </nav>
      </div>

      <!-- Khối năng lực Không gian Con người số [H] -->
      <section class="reveal" style="--i: 5" aria-labelledby="h-portal">
        <div class="section-head">
          <h2 id="h-portal">Không gian Con người số [H]</h2>
          <NuxtLink to="/portal" class="more">Cổng thông tin [H]</NuxtLink>
        </div>
        <div class="features">
          <NuxtLink to="/portal?tab=profile" class="card feature">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></svg>
            <div>
              <h3>Hồ sơ cá nhân</h3>
              <p>Xem thông tin định danh SSO, vai trò và phạm vi quyền hạn trong quy trình.</p>
            </div>
          </NuxtLink>
          <NuxtLink to="/portal?tab=groups" class="card feature">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6" /></svg>
            <div>
              <h3>Nhóm và đơn vị</h3>
              <p>Thông tin tổ kỹ thuật trực tại cơ sở 1, 2, 3 và danh bạ liên hệ hỗ trợ.</p>
            </div>
          </NuxtLink>
          <NuxtLink to="/portal?tab=documents" class="card feature">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5a2 2 0 0 1 2-2h9l5 5v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" /><path d="M14 3v5h5M8 13h8M8 17h5" /></svg>
            <div>
              <h3>Tài liệu hướng dẫn</h3>
              <p>Tải lên, xem trực tiếp và tải về tài liệu kỹ thuật qua <code class="code">/api/files</code> SeaweedFS.</p>
            </div>
          </NuxtLink>
        </div>
      </section>

      <!-- Khối tài liệu nổi bật -->
      <section class="card reveal" style="--i: 6" aria-labelledby="h-docs">
        <div class="card-head">
          <h2 id="h-docs">Tài liệu hướng dẫn dành cho bạn</h2>
          <NuxtLink v-if="quickDocs?.length" to="/portal?tab=documents" class="more">Xem tất cả ({{ quickDocs.length }})</NuxtLink>
        </div>
        <div v-if="docsPending && !quickDocs" class="docs" aria-busy="true" aria-label="Đang tải tài liệu">
          <span v-for="n in 3" :key="n" class="skeleton" style="height: 3.5rem" />
        </div>
        <ul v-else-if="quickDocs?.length" class="docs">
          <li v-for="doc in quickDocs.slice(0, 3)" :key="doc.id" class="doc">
            <div>
              <strong>{{ doc.title }}</strong>
              <p>{{ doc.description }}</p>
            </div>
            <NuxtLink to="/portal?tab=documents" class="btn secondary btn-sm">Xem tài liệu</NuxtLink>
          </li>
        </ul>
        <p v-else class="hint">Chưa có tài liệu nào cho vai trò của bạn.</p>
      </section>
    </template>

    <section v-else-if="notLoggedIn" class="hero login reveal" data-parallax>
      <span class="hero-glow" aria-hidden="true" />
      <span class="eyebrow hero-eyebrow">DX-Helpdesk · HaUI</span>
      <h1>Báo hỏng trong một phút.</h1>
      <p v-if="loginFailed" class="hero-alert" role="alert">Đăng nhập không thành công. Vui lòng thử lại.</p>
      <p class="hero-lede">Dùng tài khoản HaUI (SSO) để báo hỏng thiết bị và theo dõi yêu cầu.</p>
      <div class="hero-actions">
        <a class="btn" href="/auth/login">Đăng nhập bằng SSO</a>
      </div>
      <div v-if="demoLogin" class="demo">
        <span class="eyebrow hero-eyebrow">Vào thử theo vai trò</span>
        <ul class="demo-list">
          <li v-for="r in DEMO_ROLES" :key="r.user">
            <a class="demo-link" :href="`/auth/login?hint=${r.user}`">
              <span class="demo-role">{{ r.label }}</span>
              <span class="code">{{ r.user }}</span>
              <span class="demo-note">{{ r.note }}</span>
            </a>
          </li>
        </ul>
        <p class="demo-help">Tên đăng nhập được điền sẵn trên trang Keycloak. Mật khẩu demo do người trình diễn cung cấp.</p>
      </div>
    </section>

    <section v-else class="card empty reveal">
      <span class="empty-title">Không kết nối được</span>
      <p role="alert">
        Không lấy được thông tin tài khoản (mã lỗi {{ error?.statusCode ?? 'không rõ' }}).
        Kiểm tra Keycloak và API Gateway đã chạy, rồi tải lại trang.
      </p>
      <a class="btn secondary" href="/">Tải lại</a>
    </section>
  </div>
</template>

<style scoped>
.home { display: grid; gap: var(--space-5); }
.hint { color: var(--ink-soft); margin: 0; }
.small { font-size: var(--text-sm); }

.hero { padding: var(--space-8) var(--space-7); }
.hero h1 { margin: var(--space-3) 0 var(--space-3); max-width: 18ch; }
.hero-eyebrow { color: var(--hero-soft); }
.hero-lede { font-family: var(--font-display); font-weight: var(--weight-thin); font-size: var(--text-lg); color: var(--hero-soft); max-width: 38rem; margin: 0 0 var(--space-5); }
.hero-actions { display: flex; flex-wrap: wrap; gap: var(--space-3); }
/* Nút phụ trên nền tối: viền sáng, chữ sáng */
.hero-secondary { color: var(--hero-ink); background: rgb(255 255 255 / 0.06); border-color: rgb(255 255 255 / 0.35); }
.hero-secondary:hover { background: rgb(255 255 255 / 0.12); border-color: rgb(255 255 255 / 0.6); }
.hero-alert { display: inline-block; margin: 0 0 var(--space-3); padding: var(--space-2) var(--space-3); color: var(--hero-ink); background: rgb(255 85 0 / 0.25); border-left: 3px solid #ff8a4c; border-radius: var(--radius-control); font-weight: 700; }
.login { min-height: 26rem; display: grid; align-content: center; }

.demo { margin-top: var(--space-6); padding-top: var(--space-5); border-top: 1px solid rgb(255 255 255 / 0.15); }
.demo-list { list-style: none; margin: var(--space-3) 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: var(--space-3); }
.demo-link {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  color: var(--hero-ink);
  text-decoration: none;
  background: rgb(255 255 255 / 0.06);
  border: 1px solid rgb(255 255 255 / 0.2);
  border-radius: var(--radius-control);
  transition: transform var(--dur-fast) var(--ease-out), border-color var(--dur-fast);
}
.demo-link:hover { transform: translateY(-2px); border-color: #ff8a4c; }
.demo-link .code { justify-self: start; color: var(--hero-ink); background: rgb(255 255 255 / 0.1); border-color: rgb(255 255 255 / 0.2); }
.demo-role { font-family: var(--font-display); font-weight: var(--weight-heavy); }
.demo-note, .demo-help { font-size: var(--text-sm); color: var(--hero-soft); }
.demo-help { margin: 0; }

.grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr); gap: var(--space-5); align-items: stretch; }

.info { display: grid; gap: var(--space-3); margin: 0 0 var(--space-4); }
.info dt { font-size: var(--text-xs); font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; color: var(--ink-soft); }
.info dd { margin: 0; font-weight: 600; overflow-wrap: anywhere; }

.shortcuts { display: grid; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); gap: var(--space-4); }
.shortcut { display: grid; align-content: start; gap: var(--space-2); color: var(--ink); text-decoration: none; transition: transform var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast); }
.shortcut:hover { transform: translateY(-3px); box-shadow: var(--shadow-lift); }
.shortcut svg,
.feature svg { width: 2rem; height: 2rem; fill: none; stroke: var(--brand-ink); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.shortcut-title { font-family: var(--font-display); font-weight: var(--weight-heavy); font-size: var(--text-lg); }
.shortcut-text { font-size: var(--text-sm); color: var(--ink-soft); }

.section-head { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-3); margin-bottom: var(--space-3); }
.section-head h2 { margin: 0; }
.more { font-weight: 700; font-size: var(--text-sm); }

.features { display: grid; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); gap: var(--space-4); }
.feature { display: flex; gap: var(--space-3); align-items: flex-start; color: var(--ink); text-decoration: none; transition: transform var(--dur-fast) var(--ease-out); }
.feature:hover { transform: translateY(-2px); }
.feature h3 { margin: 0 0 var(--space-1); font-size: var(--text-base); font-weight: 700; }
.feature p { margin: 0; font-size: var(--text-sm); color: var(--ink-soft); line-height: 1.5; }
.feature svg { flex: none; }

.docs { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-2); }
.doc { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-3) var(--space-4); background: var(--sunk); border-radius: var(--radius-control); }
.doc > div { flex: 1; min-width: 0; }
.doc strong { display: block; }
.doc p { margin: 0; font-size: var(--text-sm); color: var(--ink-soft); }

@media (max-width: 56rem) {
  .grid { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 40rem) {
  .hero { padding: var(--space-7) var(--space-4); }
  .hero-actions .btn { flex: 1 1 100%; }
  .doc { flex-wrap: wrap; }
}
</style>
