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

const { data: me } = await useFetch<Me>('/gw/api/me', {
  key: 'global-me',
  retry: false,
})

const primaryRole = computed(() => {
  const r = me.value?.roles?.[0]
  return r ? (ROLE_LABELS[r] ?? r) : null
})
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <div class="topbar-left">
        <NuxtLink to="/" class="brand-link">
          <span class="brand">DX-Helpdesk</span>
        </NuxtLink>
        <span class="tagline">Báo hỏng và sửa chữa thiết bị CNTT – HaUI</span>

        <nav v-if="me" class="nav-links">
          <NuxtLink to="/" class="nav-link" active-class="active">Tổng quan</NuxtLink>
          <NuxtLink to="/portal" class="nav-link" active-class="active">Không gian [H] Portal</NuxtLink>
        </nav>
      </div>

      <div v-if="me" class="topbar-right">
        <div class="user-pill">
          <span class="user-avatar">{{ (me.name || me.username || 'U').charAt(0).toUpperCase() }}</span>
          <span class="user-name">{{ me.name || me.username }}</span>
          <span v-if="primaryRole" class="badge-role">{{ primaryRole }}</span>
          <span v-if="me.co_so" class="badge-campus">{{ me.co_so }}</span>
        </div>
        <form method="post" action="/auth/logout">
          <button class="btn-logout" type="submit" title="Đăng xuất">Đăng xuất</button>
        </form>
      </div>
    </header>

    <main class="content">
      <NuxtPage />
    </main>
  </div>
</template>

<style>
:root {
  --bg: #f5f6f8;
  --surface: #ffffff;
  --text: #1c2430;
  --muted: #5a6573;
  --border: #d8dde3;
  --accent: #0b5cad;
  --accent-text: #ffffff;
  --danger-bg: #fdecec;
  --danger-text: #8a1c1c;
  --warn-bg: #fff6e0;
  --warn-text: #6b4a00;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #12161c;
    --surface: #1b2129;
    --text: #e6eaef;
    --muted: #a3adb9;
    --border: #2e3742;
    --accent: #5aa2f0;
    --accent-text: #0b1520;
    --danger-bg: #3a1a1a;
    --danger-text: #f3b4b4;
    --warn-bg: #3a2e12;
    --warn-text: #f1d48c;
  }
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif;
  line-height: 1.5;
}

.topbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem 1.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.topbar-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
}

.brand-link {
  text-decoration: none;
  color: inherit;
}

.brand { font-weight: 800; font-size: 1.25rem; color: var(--accent); }
.tagline { color: var(--muted); font-size: 0.875rem; border-left: 1px solid var(--border); padding-left: 0.75rem; }

.nav-links {
  display: flex;
  gap: 0.5rem;
  margin-left: 1rem;
}

.nav-link {
  color: var(--muted);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: var(--text);
  background: var(--bg);
}

.nav-link.active {
  color: var(--accent);
  background: rgba(11, 92, 173, 0.08);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.625rem;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 9999px;
  font-size: 0.8125rem;
}

.user-avatar {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
}

.user-name {
  font-weight: 600;
}

.badge-role {
  background: rgba(11, 92, 173, 0.15);
  color: var(--accent);
  padding: 0.1rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-campus {
  background: #107c4120;
  color: #107c41;
  padding: 0.1rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 700;
}

.btn-logout {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
  font: inherit;
  font-size: 0.8125rem;
  padding: 0.35rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-logout:hover {
  background: var(--danger-bg);
  color: var(--danger-text);
  border-color: var(--danger-text);
}

.content {
  max-width: 72rem;
  margin: 1.5rem auto;
  padding: 0 1rem;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.btn {
  display: inline-block;
  padding: 0.625rem 1.125rem;
  border: 1px solid var(--accent);
  border-radius: 0.375rem;
  background: var(--accent);
  color: var(--accent-text);
  font: inherit;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  text-align: center;
}

.btn.secondary {
  background: transparent;
  color: var(--accent);
}

.btn:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 2px;
}

@media (max-width: 48rem) {
  .tagline { display: none; }
  .topbar { padding: 0.75rem 1rem; }
}
</style>
