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

// Header thu thấp và đậm nền khi đã cuộn
const scrolled = ref(false)
let frame = 0
function onScroll() {
  if (frame) return
  frame = requestAnimationFrame(() => {
    frame = 0
    scrolled.value = window.scrollY > 12
  })
}

// Menu trên điện thoại; đóng khi chuyển trang
const menuOpen = ref(false)
const route = useRoute()
watch(() => route.fullPath, () => { menuOpen.value = false })

// Ô tìm trên header: dán UUID phiếu thì mở thẳng phiếu đó, còn lại tìm trong danh sách.
// Ctrl+K hoặc Cmd+K mở bảng lệnh.
const search = ref<HTMLInputElement>()
const query = ref('')
const paletteOpen = ref(false)
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
function onShortcut(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k' && me.value) {
    e.preventDefault()
    paletteOpen.value = !paletteOpen.value
  }
}
function submitSearch() {
  const q = query.value.trim()
  if (!q) return
  navigateTo(UUID.test(q) ? `/tickets/${q}` : { path: '/tickets', query: { q } })
  query.value = ''
  search.value?.blur()
}

onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('keydown', onShortcut)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('keydown', onShortcut)
})
</script>

<template>
  <div class="shell">
    <a class="skip-link" href="#noi-dung">Bỏ qua thanh điều hướng</a>

    <header class="topbar" :class="{ 'is-scrolled': scrolled }">
      <div class="topbar-inner">
        <NuxtLink to="/" class="brand-link" aria-label="DX-Helpdesk, về trang tổng quan">
          <svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
            <rect x="2" y="2" width="28" height="28" rx="8" />
            <path d="M10 9h6.5a7 7 0 0 1 0 14H10Z" />
            <path d="M19 16h4" />
          </svg>
          <span class="brand">DX-Helpdesk</span>
        </NuxtLink>

        <form v-if="me" class="search" role="search" @submit.prevent="submitSearch">
          <label class="visually-hidden" for="header-search">Tìm phiếu hoặc mở phiếu theo mã</label>
          <svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>
          <input id="header-search" ref="search" v-model="query" class="search-input" type="search" placeholder="Tìm phiếu, dán mã phiếu" autocomplete="off">
          <button class="search-kbd" type="button" title="Mở bảng lệnh" @click="paletteOpen = true">Ctrl K</button>
        </form>

        <div class="topbar-right">
          <ThemeToggle />
          <template v-if="me">
            <div class="user-pill">
              <span class="user-avatar" aria-hidden="true">{{ (me.name || me.username || 'U').charAt(0).toUpperCase() }}</span>
              <span class="user-text">
                <span class="user-name">{{ me.name || me.username }}</span>
                <span class="user-meta">{{ primaryRole }}<template v-if="me.co_so"> · <span class="code">{{ me.co_so }}</span></template></span>
              </span>
            </div>
            <form method="post" action="/auth/logout">
              <button class="btn secondary btn-sm" type="submit">Đăng xuất</button>
            </form>
            <button
              class="menu-btn btn quiet icon" type="button" :aria-expanded="menuOpen" aria-controls="main-nav"
              :aria-label="menuOpen ? 'Đóng menu' : 'Mở menu'" @click="menuOpen = !menuOpen"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true"><path :d="menuOpen ? 'M6 6l12 12M18 6 6 18' : 'M4 7h16M4 12h16M4 17h16'" /></svg>
            </button>
          </template>
        </div>
      </div>

      <nav v-if="me" id="main-nav" class="nav" :class="{ open: menuOpen }" aria-label="Điều hướng chính">
        <NuxtLink to="/" class="nav-link" exact-active-class="active">Tổng quan</NuxtLink>
        <NuxtLink to="/tickets" class="nav-link" exact-active-class="active">Yêu cầu</NuxtLink>
        <NuxtLink to="/tickets/new" class="nav-link" exact-active-class="active">Báo hỏng</NuxtLink>
        <NuxtLink
          v-if="me.roles.includes('ROLE_LAB_MANAGER') || me.roles.includes('ROLE_ADMIN')"
          to="/dashboard" class="nav-link" active-class="active"
        >
          Thống kê
        </NuxtLink>
        <NuxtLink to="/portal" class="nav-link" active-class="active">Không gian [H] Portal</NuxtLink>
        <form class="nav-logout" method="post" action="/auth/logout">
          <button class="btn secondary btn-sm" type="submit">Đăng xuất</button>
        </form>
      </nav>
    </header>

    <main id="noi-dung" class="content" tabindex="-1">
      <NuxtPage />
    </main>

    <ToastHost />
    <CommandPalette v-if="me" v-model="paletteOpen" :me="me" />
  </div>
</template>

<style>
.skip-link {
  position: fixed;
  left: var(--space-4);
  top: var(--space-2);
  z-index: 70;
  padding: var(--space-2) var(--space-4);
  color: var(--on-primary);
  background: var(--primary);
  border-radius: var(--radius-control);
  transform: translateY(-150%);
}

.skip-link:focus { transform: none; }

/* Header kính mờ. Thu thấp bằng transform: cả thanh dịch lên, nội dung dịch xuống
   một nửa để vẫn nằm giữa phần còn thấy; nền đậm hơn bằng lớp ::before đổi opacity. */
.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  isolation: isolate;
  background: var(--header);
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  backdrop-filter: blur(14px) saturate(140%);
  border-bottom: 1px solid var(--rule);
  transition: transform var(--dur) var(--ease-out);
}

.topbar::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  background: var(--header-scrolled);
  opacity: 0;
  transition: opacity var(--dur) var(--ease-out);
}

.topbar.is-scrolled { transform: translateY(-0.75rem); box-shadow: var(--shadow); }
.topbar.is-scrolled::before { opacity: 1; }
.topbar.is-scrolled .topbar-inner { transform: translateY(0.375rem); }
.topbar.is-scrolled .brand-link { transform: scale(0.92); }

.topbar-inner {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  max-width: 81rem;
  min-height: var(--header-h);
  margin: 0 auto;
  padding: var(--space-3) var(--space-5) var(--space-2);
  transition: transform var(--dur) var(--ease-out);
}

.brand-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--ink);
  text-decoration: none;
  transform-origin: left center;
  transition: transform var(--dur) var(--ease-out);
}

.brand-mark { width: 2.25rem; height: 2.25rem; }
.brand-mark rect { fill: var(--brand); }
.brand-mark path { fill: none; stroke: #fff; stroke-width: 2.6; stroke-linecap: round; stroke-linejoin: round; }
.brand { font-family: var(--font-display); font-weight: var(--weight-heavy); font-size: 1.25rem; letter-spacing: -0.01em; }

/* Ô tìm rộng ra khi focus. Transition width ở đây là ngoại lệ duy nhất của quy tắc
   chỉ animate transform và opacity; chỉ áp cho đúng ô này. */
.search {
  position: relative;
  flex: none;
  display: flex;
  align-items: center;
  width: 18rem;
  max-width: 40vw;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  box-shadow: var(--shadow);
  transition: width var(--dur) var(--ease-out), border-color var(--dur-fast);
}

.search:focus-within { width: 26rem; border-color: var(--focus); }

.search-icon {
  position: absolute;
  left: var(--space-3);
  width: 1.1rem;
  height: 1.1rem;
  fill: none;
  stroke: var(--ink-soft);
  stroke-width: 2;
  stroke-linecap: round;
}

.search-input {
  position: relative;
  width: 100%;
  min-height: 2.5rem;
  padding: 0 4.5rem 0 2.5rem;
  font: inherit;
  font-size: var(--text-sm);
  color: var(--ink);
  background: transparent;
  border: 0;
}

.search-input::placeholder { color: var(--ink-soft); }
.search-input:focus-visible { outline: none; }
.search:focus-within { outline: 3px solid var(--focus); outline-offset: 2px; border-radius: var(--radius-control); }

.search-kbd {
  position: absolute;
  cursor: pointer;
  right: var(--space-2);
  /* Vùng bấm tối thiểu 24x24px (WCAG 2.5.8) */
  display: inline-flex;
  align-items: center;
  min-height: 1.75rem;
  min-width: 1.75rem;
  padding: 0 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--ink-soft);
  background: var(--sunk);
  border: 1px solid var(--rule);
  border-radius: var(--radius-control);
  transition: opacity var(--dur-fast);
}

.search:focus-within .search-kbd { opacity: 0; }

.topbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-left: auto;
}

.user-pill { display: flex; align-items: center; gap: var(--space-2); }

.user-avatar {
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  font-family: var(--font-display);
  font-weight: var(--weight-heavy);
  color: var(--on-primary);
  background: var(--primary);
  border-radius: var(--radius-pill);
}

.user-text { display: grid; line-height: 1.25; }
.user-name { font-weight: 800; font-size: var(--text-sm); }
.user-meta { font-size: var(--text-xs); color: var(--ink-soft); }

.menu-btn { display: none; }
.menu-btn svg { width: 1.4rem; height: 1.4rem; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }

.nav {
  display: flex;
  gap: var(--space-1);
  max-width: 81rem;
  margin: 0 auto;
  padding: 0 var(--space-5);
  overflow-x: auto;
}

.nav-link {
  position: relative;
  padding: var(--space-2) var(--space-3) var(--space-3);
  font-weight: 700;
  font-size: var(--text-sm);
  color: var(--ink-soft);
  text-decoration: none;
  white-space: nowrap;
  transition: color var(--dur-fast);
}

.nav-link::after {
  content: "";
  position: absolute;
  left: var(--space-3);
  right: var(--space-3);
  bottom: 0;
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: var(--brand);
  transform: scaleX(0);
  transition: transform var(--dur) var(--ease-out);
}

.nav-logout { display: none; }

.nav-link:hover { color: var(--ink); }
.nav-link.active { color: var(--ink); }
.nav-link.active::after { transform: scaleX(1); }

.content {
  max-width: 81rem;
  margin: var(--space-6) auto var(--space-8);
  padding: 0 var(--space-5);
}

.content:focus { outline: none; }

@media (max-width: 64rem) {
  .user-text { display: none; }
}

@media (max-width: 48rem) {
  .topbar-inner { padding-inline: var(--space-4); gap: var(--space-2); }
  .search,
  .user-pill,
  .topbar-right form { display: none; }
  .nav-logout { display: block; margin-top: var(--space-2); }
  .menu-btn { display: inline-flex; }
  .nav { display: none; flex-direction: column; padding: 0 var(--space-4) var(--space-3); }
  .nav.open { display: flex; }
  .nav-link::after { left: 0; right: auto; top: 20%; bottom: 20%; width: 3px; height: auto; transform: scaleY(0); }
  .nav-link.active::after { transform: scaleY(1); }
  .content { padding: 0 var(--space-4); margin-top: var(--space-5); }
}
</style>
