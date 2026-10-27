<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Me } from '~/utils/helpdesk'
import type { GroupsResponse } from '~/utils/portal'
import { ROLE_LABELS, CAMPUS_LABELS } from '~/utils/portal'

defineProps<{
  me: Me | null
  groupsData: GroupsResponse | null
}>()
</script>

<template>
  <section class="tab-pane" aria-labelledby="profile-heading">
    <div class="grid-2col">
      <!-- Thông tin người dùng -->
      <div class="card profile-card">
        <div class="profile-header">
          <div class="avatar-large">
            {{ (me?.name || me?.username || 'U').charAt(0).toUpperCase() }}
          </div>
          <div class="profile-title-area">
            <h2>{{ me?.name || me?.username }}</h2>
            <div class="badge-row">
              <span v-for="role in (me?.roles ?? [])" :key="role" class="badge role-badge">
                {{ ROLE_LABELS[role] || role }}
              </span>
              <span v-if="me?.co_so" class="badge campus-badge">
                {{ me.co_so }}
              </span>
            </div>
          </div>
        </div>

        <dl class="details-list">
          <div class="detail-item">
            <dt>Tài khoản (Username)</dt>
            <dd><code>{{ me?.username }}</code></dd>
          </div>
          <div class="detail-item">
            <dt>Họ và tên</dt>
            <dd>{{ me?.name || 'Chưa cập nhật họ tên' }}</dd>
          </div>
          <div class="detail-item">
            <dt>Hộp thư điện tử (Email)</dt>
            <dd>{{ me?.email || 'Chưa cấu hình email' }}</dd>
          </div>
          <div class="detail-item">
            <dt>Cơ sở công tác (co_so claim)</dt>
            <dd>
              <strong v-if="me?.co_so">{{ CAMPUS_LABELS[me.co_so] || me.co_so }}</strong>
              <span v-else class="text-muted">Chưa gán cơ sở làm việc</span>
            </dd>
          </div>
          <div class="detail-item">
            <dt>Định danh người dùng (sub)</dt>
            <dd class="small-code"><code>{{ me?.sub }}</code></dd>
          </div>
          <div class="detail-item">
            <dt>Phương thức xác thực</dt>
            <dd>Keycloak SSO (OpenID Connect PKCE / Authorization Code)</dd>
          </div>
        </dl>

        <div class="card-footer">
          <p class="muted-note">
            ✓ Dữ liệu được xác thực trực tiếp qua <code>GET /api/me</code> của API Gateway với JWT Token có chữ ký JWKS.
          </p>
        </div>
      </div>

      <!-- Trách nhiệm & Quyền hạn hệ thống -->
      <div class="card permissions-card">
        <h3>Trách nhiệm & Quyền hạn theo Vai trò</h3>
        <p class="desc-text">
          Các vai trò được quy định trong đặc tả nghiệp vụ DX-Helpdesk và phân quyền trực tiếp tại API Gateway và Flowable BPMN:
        </p>

        <div v-for="rg in groupsData?.userContext?.matchedRoles" :key="rg.id" class="role-scope-box">
          <div class="scope-header">
            <span class="role-tag">{{ rg.roleLabel }}</span>
            <span class="group-name">{{ rg.name }}</span>
          </div>
          <p class="role-desc">{{ rg.description }}</p>

          <h4 class="subhead">Nhiệm vụ chính:</h4>
          <ul class="task-list">
            <li v-for="(duty, i) in rg.duties" :key="i">{{ duty }}</li>
          </ul>

          <h4 class="subhead">Quyền hạn luồng nghiệp vụ:</h4>
          <div class="pill-group">
            <span v-for="(perm, j) in rg.workflowPermissions" :key="j" class="perm-pill">
              ✓ {{ perm }}
            </span>
          </div>
        </div>

        <div class="info-alert">
          <strong>Nguyên tắc bảo mật:</strong> Quyền hạn được kiểm tra ở cấp Gateway APISIX (plugin <code>dxlab-roles</code>) và Data API, giao diện không tự quyết định quyền nghiệp vụ.
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 50rem) {
  .grid-2col {
    grid-template-columns: 1fr;
  }
}

.profile-card {
  display: flex;
  flex-direction: column;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.25rem;
}

.avatar-large {
  width: 4.5rem;
  height: 4.5rem;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), #2b88d8);
  color: #fff;
  font-size: 2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(11, 92, 173, 0.25);
}

.profile-title-area h2 {
  margin: 0 0 0.5rem;
  font-size: 1.375rem;
}

.badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  border-radius: 0.25rem;
}

.role-badge {
  background: rgba(11, 92, 173, 0.12);
  color: var(--accent);
}

.campus-badge {
  background: #107c411f;
  color: #107c41;
}

.details-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 0 0 1.25rem;
}

.detail-item dt {
  font-size: 0.8125rem;
  color: var(--muted);
  margin-bottom: 0.125rem;
}

.detail-item dd {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 500;
  word-break: break-all;
}

.small-code code {
  font-size: 0.8125rem;
  background: var(--bg);
  padding: 0.2rem 0.375rem;
  border-radius: 0.25rem;
}

.muted-note {
  font-size: 0.8125rem;
  color: var(--muted);
  margin: 0;
}

.permissions-card h3 {
  margin-top: 0;
  font-size: 1.125rem;
}

.desc-text {
  color: var(--muted);
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

.role-scope-box {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.scope-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.role-tag {
  background: var(--accent);
  color: var(--accent-text);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
}

.group-name {
  font-weight: 700;
  font-size: 0.9375rem;
}

.role-desc {
  font-size: 0.875rem;
  color: var(--muted);
  margin: 0 0 0.75rem;
}

.subhead {
  font-size: 0.8125rem;
  margin: 0.5rem 0 0.25rem;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.task-list {
  margin: 0 0 0.75rem;
  padding-left: 1.25rem;
  font-size: 0.875rem;
  line-height: 1.5;
}

.pill-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.perm-pill {
  font-size: 0.75rem;
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
}

.info-alert {
  font-size: 0.8125rem;
  padding: 0.75rem;
  border-radius: 0.375rem;
  background: var(--warn-bg);
  color: var(--warn-text);
  line-height: 1.4;
}
</style>
