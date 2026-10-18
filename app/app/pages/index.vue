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

const notLoggedIn = computed(() => error.value?.statusCode === 401)
const roleNames = computed(() => (me.value?.roles ?? []).map(r => ROLE_LABELS[r] ?? r))
const campus = computed(() => {
  const code = me.value?.co_so
  return code ? `${CAMPUS_LABELS[code] ?? code} (${code})` : null
})
</script>

<template>
  <section class="card" aria-live="polite">
    <p v-if="status === 'pending'" class="muted">Đang tải thông tin tài khoản…</p>

    <template v-else-if="me">
      <h1>Xin chào, {{ me.name || me.username }}</h1>
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
      <form method="post" action="/auth/logout">
        <button class="btn secondary" type="submit">Đăng xuất</button>
      </form>
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
</template>

<style scoped>
h1 { margin: 0 0 1rem; font-size: 1.375rem; }

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

@media (max-width: 30rem) {
  .info { grid-template-columns: 1fr; gap: 0.125rem; }
  .info dd { margin-bottom: 0.5rem; }
}
</style>
