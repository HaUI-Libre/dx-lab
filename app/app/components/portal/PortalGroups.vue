<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Me } from '~/utils/helpdesk'
import type { GroupsResponse } from '~/utils/portal'

defineProps<{
  me: Me | null
  groupsData: GroupsResponse | null
}>()
</script>

<template>
  <section class="tab-pane" aria-labelledby="groups-heading">
    <!-- Cơ sở trực thuộc của người dùng -->
    <div v-if="groupsData?.userContext?.matchedUnit" class="card highlight-card">
      <div class="highlight-badge">Đơn vị trực thuộc của bạn</div>
      <div class="unit-banner-content">
        <div>
          <h2>{{ groupsData.userContext.matchedUnit.name }} ({{ groupsData.userContext.matchedUnit.code }})</h2>
          <p class="unit-location">Địa điểm: {{ groupsData.userContext.matchedUnit.location }}</p>
          <p class="unit-scope">{{ groupsData.userContext.matchedUnit.scope }}</p>
        </div>
        <div class="contact-box">
          <div><strong>Hotline:</strong> {{ groupsData.userContext.matchedUnit.hotline }}</div>
          <div><strong>Email:</strong> {{ groupsData.userContext.matchedUnit.email }}</div>
          <div><strong>Trưởng phòng phụ trách:</strong> {{ groupsData.userContext.matchedUnit.manager }}</div>
        </div>
      </div>
    </div>

    <!-- Danh sách các cơ sở đào tạo HaUI -->
    <h3 class="section-title">Các Đơn vị Cơ sở & Tổ Kỹ thuật Hỗ trợ HaUI</h3>
    <div class="unit-grid">
      <div
        v-for="unit in groupsData?.campusUnits"
        :key="unit.id"
        class="card unit-card"
        :class="{ 'is-current': unit.code === me?.co_so }"
      >
        <div class="unit-head">
          <span class="unit-code-badge">{{ unit.code }}</span>
          <span v-if="unit.code === me?.co_so" class="current-tag">Cơ sở của bạn</span>
        </div>
        <h4>{{ unit.name }}</h4>
        <p class="unit-loc">Địa điểm: {{ unit.location }}</p>
        <p class="unit-summary">{{ unit.scope }}</p>

        <dl class="unit-meta">
          <dt>Hotline nội bộ:</dt>
          <dd>{{ unit.hotline }}</dd>
          <dt>Email hỗ trợ:</dt>
          <dd>{{ unit.email }}</dd>
          <dt>Trưởng phòng:</dt>
          <dd>{{ unit.manager }}</dd>
          <dt>Kỹ thuật viên:</dt>
          <dd>{{ unit.technicians.join(', ') }}</dd>
        </dl>
      </div>
    </div>

    <!-- Khối các nhóm vai trò nghiệp vụ -->
    <h3 class="section-title mt-4">Các Nhóm Vai trò Chuyên môn trong Nền tảng</h3>
    <div class="role-grid">
      <div v-for="group in groupsData?.roleGroups" :key="group.id" class="card role-item-card">
        <div class="role-top">
          <span class="role-badge-small">{{ group.roleLabel }}</span>
          <span class="role-code">{{ group.role }}</span>
        </div>
        <h4>{{ group.name }}</h4>
        <p class="desc">{{ group.description }}</p>
        <div class="role-perms-summary">
          <strong>Trách nhiệm:</strong>
          <ul>
            <li v-for="(duty, idx) in group.duties.slice(0, 3)" :key="idx">{{ duty }}</li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.highlight-card {
  border-left: 4px solid var(--accent);
  background: var(--surface);
  margin-bottom: 1.5rem;
}

.highlight-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent);
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.unit-banner-content {
  display: flex;
  justify-content: space-between;
  gap: 2rem;
  flex-wrap: wrap;
}

.unit-banner-content h2 {
  margin: 0 0 0.375rem;
  font-size: 1.25rem;
}

.unit-location {
  color: var(--muted);
  font-size: 0.9375rem;
  margin: 0 0 0.25rem;
}

.unit-scope {
  font-size: 0.875rem;
  margin: 0;
}

.contact-box {
  background: var(--bg);
  padding: 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.section-title {
  font-size: 1.125rem;
  margin: 1.5rem 0 1rem;
}

.mt-4 {
  margin-top: 1.25rem;
}

.unit-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
  gap: 1.25rem;
}

.unit-card {
  position: relative;
  display: flex;
  flex-direction: column;
}

.unit-card.is-current {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(11, 92, 173, 0.2);
}

.unit-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.unit-code-badge {
  font-weight: 800;
  font-size: 1rem;
  color: var(--accent);
}

.current-tag {
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--accent);
  color: var(--accent-text);
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.unit-card h4 {
  margin: 0 0 0.25rem;
  font-size: 1rem;
}

.unit-loc {
  font-size: 0.8125rem;
  color: var(--muted);
  margin: 0 0 0.5rem;
}

.unit-summary {
  font-size: 0.875rem;
  margin: 0 0 1rem;
}

.unit-meta {
  margin: auto 0 0;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border);
  font-size: 0.8125rem;
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.25rem 0.75rem;
}

.unit-meta dt {
  color: var(--muted);
}

.unit-meta dd {
  margin: 0;
  font-weight: 500;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 1.25rem;
}

.role-item-card h4 {
  margin: 0.5rem 0 0.25rem;
  font-size: 1rem;
}

.role-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.role-badge-small {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent);
}

.role-code {
  font-size: 0.75rem;
  color: var(--muted);
  font-family: monospace;
}

.role-item-card .desc {
  font-size: 0.8125rem;
  color: var(--muted);
  margin: 0 0 0.75rem;
}

.role-perms-summary {
  font-size: 0.8125rem;
}

.role-perms-summary ul {
  margin: 0.25rem 0 0;
  padding-left: 1.25rem;
}
</style>
