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
const { data: quickDocs } = await useFetch<GuideDoc[]>('/api/portal/documents', {
  key: 'home-docs',
  lazy: true,
})

const notLoggedIn = computed(() => error.value?.statusCode === 401)
const roleNames = computed(() => (me.value?.roles ?? []).map(r => ROLE_LABELS[r] ?? r))
const campus = computed(() => {
  const code = me.value?.co_so
  return code ? `${CAMPUS_LABELS[code] ?? code} (${code})` : null
})
</script>

<template>
  <div class="home-container">
    <section class="card main-card" aria-live="polite">
      <p v-if="status === 'pending'" class="muted">Đang tải thông tin tài khoản…</p>

      <template v-else-if="me">
        <div class="welcome-header">
          <div>
            <h1>Xin chào, {{ me.name || me.username }}</h1>
            <p class="subtitle">Hệ thống Tiếp nhận Báo hỏng và Quản lý Sửa chữa Thiết bị CNTT HaUI</p>
          </div>
          <div class="header-actions">
            <NuxtLink to="/tickets/new" class="btn">Báo hỏng thiết bị</NuxtLink>
            <NuxtLink to="/tickets" class="btn secondary">Yêu cầu và hàng đợi</NuxtLink>
            <NuxtLink to="/portal" class="btn secondary">Cổng thông tin [H]</NuxtLink>
          </div>
        </div>

        <dl class="info">
          <dt>Tài khoản</dt>
          <dd>{{ me.username }}</dd>
          <dt>Vai trò</dt>
          <dd>{{ roleNames.length ? roleNames.join(', ') : 'Chưa có vai trò DX-Helpdesk' }}</dd>
          <dt>Cơ sở</dt>
          <dd>
            <template v-if="campus">{{ campus }}</template>
            <span v-else class="muted">Chưa gán cơ sở</span>
          </dd>
          <template v-if="me.email">
            <dt>Email</dt>
            <dd>{{ me.email }}</dd>
          </template>
        </dl>
        <p class="muted small">Thông tin lấy từ <code>GET /api/me</code> qua API Gateway.</p>

        <!-- Khối năng lực Không gian Con người số [H] -->
        <div class="portal-feature-grid">
          <NuxtLink to="/portal?tab=profile" class="feature-card">
            <div class="feature-icon">👤</div>
            <div class="feature-body">
              <h3>Hồ sơ cá nhân</h3>
              <p>Xem thông tin định danh SSO, vai trò và phạm vi quyền hạn trong quy trình.</p>
            </div>
            <span class="feature-arrow">→</span>
          </NuxtLink>

          <NuxtLink to="/portal?tab=groups" class="feature-card">
            <div class="feature-icon">🏢</div>
            <div class="feature-body">
              <h3>Nhóm & Đơn vị</h3>
              <p>Thông tin tổ kỹ thuật trực tại cơ sở 1, 2, 3 và danh bạ liên hệ hỗ trợ.</p>
            </div>
            <span class="feature-arrow">→</span>
          </NuxtLink>

          <NuxtLink to="/portal?tab=documents" class="feature-card highlight">
            <div class="feature-icon">📚</div>
            <div class="feature-body">
              <h3>Tài liệu hướng dẫn</h3>
              <p>Tải lên, xem trực tiếp và tải về tài liệu kỹ thuật qua <code>/api/files</code> SeaweedFS.</p>
            </div>
            <span class="feature-arrow">→</span>
          </NuxtLink>
        </div>

        <!-- Khối tài liệu nổi bật -->
        <div v-if="quickDocs?.length" class="quick-docs-section">
          <div class="section-header">
            <h3>Tài liệu Hướng dẫn dành cho bạn</h3>
            <NuxtLink to="/portal?tab=documents" class="text-link">Xem tất cả ({{ quickDocs.length }}) →</NuxtLink>
          </div>
          <div class="quick-doc-list">
            <div v-for="doc in quickDocs.slice(0, 3)" :key="doc.id" class="quick-doc-item">
              <span class="doc-icon">📄</span>
              <div class="quick-doc-info">
                <strong>{{ doc.title }}</strong>
                <p>{{ doc.description }}</p>
              </div>
              <NuxtLink to="/portal?tab=documents" class="btn secondary btn-sm">Xem tài liệu</NuxtLink>
            </div>
          </div>
        </div>

        <div class="home-footer">
          <form method="post" action="/auth/logout">
            <button class="btn secondary" type="submit">Đăng xuất</button>
          </form>
        </div>
      </template>

      <template v-else-if="notLoggedIn">
        <h1>Đăng nhập</h1>
        <p v-if="loginFailed" class="notice danger" role="alert">
          Đăng nhập không thành công. Vui lòng thử lại.
        </p>
        <p>Dùng tài khoản HaUI (SSO) để báo hỏng thiết bị và theo dõi yêu cầu.</p>
        <a class="btn" href="/auth/login">Đăng nhập bằng SSO</a>
      </template>

      <template v-else>
        <h1>Không kết nối được</h1>
        <p class="notice warn" role="alert">
          Không lấy được thông tin tài khoản (mã lỗi {{ error?.statusCode ?? 'không rõ' }}).
          Kiểm tra Keycloak và API Gateway đã chạy, rồi tải lại trang.
        </p>
        <a class="btn secondary" href="/">Tải lại</a>
      </template>
    </section>
  </div>
</template>

<style scoped>
.home-container {
  max-width: 56rem;
  margin: 0 auto;
}

h1 { margin: 0 0 0.25rem; font-size: 1.5rem; }
.subtitle { margin: 0 0 1.25rem; color: var(--muted); font-size: 0.9375rem; }

.welcome-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.25rem;
}

.header-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }

.info {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.5rem 1.25rem;
  margin: 0 0 1.25rem;
}

.info dt { color: var(--muted); }
.info dd { margin: 0; font-weight: 600; overflow-wrap: anywhere; }

.muted { color: var(--muted); }
.small { font-size: 0.875rem; }

.notice {
  padding: 0.75rem 1rem;
  border-radius: 0.375rem;
}
.notice.danger { background: var(--danger-bg); color: var(--danger-text); }
.notice.warn { background: var(--warn-bg); color: var(--warn-text); }

/* Feature Cards Grid */
.portal-feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
  gap: 1rem;
  margin: 1.5rem 0;
}

.feature-card {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  background: var(--bg);
  text-decoration: none;
  color: inherit;
  transition: all 0.2s ease;
}

.feature-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.feature-card.highlight {
  border-color: rgba(11, 92, 173, 0.4);
  background: rgba(11, 92, 173, 0.03);
}

.feature-icon {
  font-size: 1.75rem;
  flex-shrink: 0;
}

.feature-body h3 {
  margin: 0 0 0.25rem;
  font-size: 0.9375rem;
  color: var(--text);
}

.feature-body p {
  margin: 0;
  font-size: 0.75rem;
  color: var(--muted);
  line-height: 1.4;
}

.feature-arrow {
  margin-left: auto;
  font-size: 1.125rem;
  color: var(--muted);
  font-weight: 700;
}

/* Quick docs section */
.quick-docs-section {
  margin: 1.5rem 0;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.section-header h3 {
  margin: 0;
  font-size: 1.0625rem;
}

.text-link {
  color: var(--accent);
  text-decoration: none;
  font-size: 0.8125rem;
  font-weight: 600;
}

.quick-doc-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.quick-doc-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 0.375rem;
}

.doc-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.quick-doc-info {
  flex: 1;
}

.quick-doc-info strong {
  display: block;
  font-size: 0.875rem;
  margin-bottom: 0.125rem;
}

.quick-doc-info p {
  margin: 0;
  font-size: 0.75rem;
  color: var(--muted);
}

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
  white-space: nowrap;
}

.home-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

@media (max-width: 30rem) {
  .info { grid-template-columns: 1fr; gap: 0.125rem; }
  .info dd { margin-bottom: 0.5rem; }
  .welcome-header { flex-direction: column; }
}
</style>
