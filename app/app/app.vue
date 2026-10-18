<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<template>
  <div class="shell">
    <header class="topbar">
      <span class="brand">DX-Helpdesk</span>
      <span class="tagline">Báo hỏng và sửa chữa thiết bị CNTT – HaUI</span>
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
  align-items: baseline;
  gap: 0.25rem 1rem;
  padding: 0.875rem 1rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.brand { font-weight: 700; font-size: 1.125rem; }
.tagline { color: var(--muted); font-size: 0.9375rem; }

.content {
  max-width: 40rem;
  margin: 2rem auto;
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
}

.btn.secondary {
  background: transparent;
  color: var(--accent);
}

.btn:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 2px;
}
</style>
