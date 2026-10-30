<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Me } from '~/utils/helpdesk'
import type { GuideDoc, GroupsResponse } from '~/utils/portal'

const route = useRoute()
const activeTab = ref<'profile' | 'groups' | 'documents'>('profile')

// Kiểm tra query/hash để chuyển tab nếu có
onMounted(() => {
  if (route.query.tab === 'documents' || route.hash === '#documents') activeTab.value = 'documents'
  else if (route.query.tab === 'groups' || route.hash === '#groups') activeTab.value = 'groups'
  else activeTab.value = 'profile'
})

// Thông tin người dùng hiện tại từ Gateway
const { data: me, error: meError } = await useFetch<Me>('/gw/api/me', {
  key: 'portal-me',
  retry: false,
})

// Chuyển hướng nếu chưa đăng nhập
if (meError.value?.statusCode === 401) {
  navigateTo('/auth/login')
}

// Dữ liệu nhóm & đơn vị
const { data: groupsData } = await useFetch<GroupsResponse>('/api/portal/groups', {
  key: 'portal-groups',
  lazy: true,
})

// Dữ liệu danh sách tài liệu hướng dẫn
const { data: documents, status: docsStatus, refresh: refreshDocs } = await useFetch<GuideDoc[]>('/api/portal/documents', {
  key: 'portal-docs',
  lazy: true,
})

const userRoles = computed(() => me.value?.roles ?? [])
const isManagerOrAdmin = computed(() =>
  userRoles.value.some(r => ['ROLE_LAB_MANAGER', 'ROLE_ADMIN'].includes(r)),
)

// Trạng thái modal xem trước tài liệu
const previewDoc = ref<GuideDoc | null>(null)
const previewContent = ref<string>('')
const previewLoading = ref(false)
const previewError = ref<string | null>(null)

async function openPreview(doc: GuideDoc) {
  previewDoc.value = doc
  previewContent.value = ''
  previewError.value = null
  previewLoading.value = true

  try {
    // Đọc tệp trực tiếp từ APISIX gateway qua /gw/api/files/...
    const res = await $fetch<string>(`/gw/api/files/${doc.filePath}`, {
      responseType: 'text',
      headers: {
        Accept: 'text/markdown, text/plain, */*',
      },
    })
    previewContent.value = res
  }
  catch (err: any) {
    if (err?.statusCode === 403 || err?.status === 403) {
      previewError.value = 'Bạn không có quyền truy cập tài liệu này (403 Forbidden). Quyền xem được gateway kiểm soát theo cấp bậc vai trò.'
    }
    else {
      previewError.value = `Không thể tải nội dung tệp (Mã lỗi: ${err?.statusCode ?? 'không xác định'}). Kiểm tra kết nối SeaweedFS qua gateway.`
    }
  }
  finally {
    previewLoading.value = false
  }
}

function closePreview() {
  previewDoc.value = null
  previewContent.value = ''
  previewError.value = null
}

// Trạng thái modal tải lên tài liệu mới
const showUploadModal = ref(false)

// Tải file về máy
function downloadFile(doc: GuideDoc) {
  const link = document.createElement('a')
  link.href = `/gw/api/files/${doc.filePath}`
  link.download = doc.fileName
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<template>
  <div class="portal-wrapper">
    <!-- Header Không gian Con người số [H] -->
    <header class="portal-hero">
      <div class="hero-badge">Không gian Con người số [H]</div>
      <h1 class="hero-title">Cổng thông tin & Tài liệu Người dùng</h1>
      <p class="hero-desc">
        Quản lý hồ sơ định danh Single Sign-On (SSO), thuộc tính cơ sở làm việc, thông tin tổ kỹ thuật và danh sách tài liệu hướng dẫn nghiệp vụ DX-Helpdesk.
      </p>

      <!-- Tab Navigation -->
      <nav class="portal-tabs" aria-label="Các mục portal">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'profile' }"
          type="button"
          @click="activeTab = 'profile'"
        >
          <span class="tab-label">Hồ sơ cá nhân</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'groups' }"
          type="button"
          @click="activeTab = 'groups'"
        >
          <span class="tab-label">Nhóm & Đơn vị</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'documents' }"
          type="button"
          @click="activeTab = 'documents'"
        >
          <span class="tab-label">Tài liệu hướng dẫn</span>
          <span v-if="documents?.length" class="badge-count">{{ documents.length }}</span>
        </button>
      </nav>
    </header>

    <!-- TAB 1: HỒ SƠ CÁ NHÂN -->
    <PortalProfile
      v-if="activeTab === 'profile'"
      :me="me"
      :groups-data="groupsData"
    />

    <!-- TAB 2: NHÓM & ĐƠN VỊ -->
    <PortalGroups
      v-if="activeTab === 'groups'"
      :me="me"
      :groups-data="groupsData"
    />

    <!-- TAB 3: TÀI LIỆU HƯỚNG DẪN -->
    <PortalDocuments
      v-if="activeTab === 'documents'"
      :documents="documents"
      :docs-status="docsStatus"
      :is-manager-or-admin="isManagerOrAdmin"
      @preview="openPreview"
      @download="downloadFile"
      @open-upload="showUploadModal = true"
    />

    <!-- MODAL XEM TRƯỚC TÀI LIỆU -->
    <PortalDocViewerModal
      v-if="previewDoc"
      :doc="previewDoc"
      :content="previewContent"
      :loading="previewLoading"
      :error="previewError"
      @close="closePreview"
      @download="downloadFile"
    />

    <!-- MODAL TẢI LÊN TÀI LIỆU MỚI -->
    <PortalDocUploadModal
      v-if="showUploadModal"
      @close="showUploadModal = false"
      @uploaded="refreshDocs"
    />
  </div>
</template>

<style scoped>
.portal-wrapper {
  max-width: 68rem;
  margin: 1.5rem auto 3rem;
  padding: 0 1rem;
}

/* Hero section */
.portal-hero {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.hero-badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  background: var(--accent);
  color: var(--accent-text);
  margin-bottom: 0.75rem;
}

.hero-title {
  margin: 0 0 0.5rem;
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text);
}

.hero-desc {
  margin: 0 0 1.5rem;
  color: var(--muted);
  max-width: 50rem;
  line-height: 1.6;
}

/* Tabs */
.portal-tabs {
  display: flex;
  gap: 0.5rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.25rem;
  overflow-x: auto;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--muted);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--text);
  background: var(--bg);
  border-radius: 0.375rem 0.375rem 0 0;
}

.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  background: transparent;
}

.badge-count {
  display: inline-block;
  font-size: 0.75rem;
  background: var(--border);
  color: var(--text);
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}
</style>
