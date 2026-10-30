<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { GuideDoc } from '~/utils/portal'

const props = defineProps<{
  documents: GuideDoc[] | null
  docsStatus: string
  isManagerOrAdmin: boolean
}>()

defineEmits<{
  (e: 'preview', doc: GuideDoc): void
  (e: 'download', doc: GuideDoc): void
  (e: 'openUpload'): void
}>()

const searchQuery = ref('')
const selectedCategory = ref('ALL')

const filteredDocuments = computed(() => {
  let list = props.documents ?? []
  if (selectedCategory.value !== 'ALL') {
    list = list.filter(d => d.category === selectedCategory.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(d =>
      d.title.toLowerCase().includes(q)
      || d.description.toLowerCase().includes(q)
      || d.fileName.toLowerCase().includes(q),
    )
  }
  return list
})
</script>

<template>
  <section class="tab-pane" aria-labelledby="documents-heading">
    <div class="doc-toolbar">
      <div class="search-filter-row">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Tìm kiếm tài liệu hướng dẫn..."
            class="form-input"
          />
        </div>
        <div class="category-filter">
          <select v-model="selectedCategory" class="form-select">
            <option value="ALL">Tất cả danh mục</option>
            <option value="GENERAL">Nội quy Chung</option>
            <option value="STUDENT">Hướng dẫn Sinh viên</option>
            <option value="TECHNICIAN">Kỹ thuật viên</option>
            <option value="MANAGER">Trưởng phòng Lab</option>
            <option value="ADMIN">Quản trị viên</option>
          </select>
        </div>
      </div>

      <div class="action-btn-row">
        <button
          v-if="isManagerOrAdmin"
          class="btn"
          type="button"
          @click="$emit('openUpload')"
        >
          + Tải lên tài liệu mới
        </button>
      </div>
    </div>

    <!-- Trạng thái tải danh sách -->
    <div v-if="docsStatus === 'pending'" class="card notice">
      <p>Đang tải danh sách tài liệu hướng dẫn từ hệ thống lưu trữ…</p>
    </div>

    <!-- Danh sách tài liệu -->
    <div v-else-if="filteredDocuments.length" class="doc-grid">
      <article
        v-for="doc in filteredDocuments"
        :key="doc.id"
        class="card doc-card"
      >
        <div class="doc-card-top">
          <span class="doc-category-tag" :class="`cat-${doc.category.toLowerCase()}`">
            {{ doc.categoryLabel }}
          </span>
          <span v-if="doc.isCustom" class="badge custom-tag">Mới thêm</span>
        </div>

        <h3 class="doc-title">{{ doc.title }}</h3>
        <p class="doc-desc">{{ doc.description }}</p>

        <div class="doc-meta">
          <div class="meta-item">Tệp: <code>{{ doc.fileName }}</code></div>
          <div class="meta-row">
            <span>Dung lượng: {{ doc.fileSize }}</span>
            <span>Cập nhật: {{ doc.updatedAt }}</span>
          </div>
          <div v-if="doc.uploadedBy" class="meta-uploader">
            Tác giả: {{ doc.uploadedBy }}
          </div>
        </div>

        <div class="doc-card-actions">
          <button class="btn secondary btn-sm" type="button" @click="$emit('preview', doc)">
            Xem nội dung
          </button>
          <button class="btn btn-sm" type="button" @click="$emit('download', doc)">
            Tải về
          </button>
        </div>
      </article>
    </div>

    <!-- Khi không tìm thấy tài liệu nào -->
    <div v-else class="card notice warn">
      <p>Không tìm thấy tài liệu phù hợp với tìm kiếm hoặc vai trò của bạn.</p>
      <button class="btn secondary btn-sm" type="button" @click="searchQuery = ''; selectedCategory = 'ALL'">
        Xóa bộ lọc
      </button>
    </div>

    <div class="storage-notice">
      <span>Tệp tài liệu được lưu trữ phân tán trên <strong>SeaweedFS</strong> (bucket <code>documents</code>) và truy xuất qua tuyến <code>/api/files</code> của Apache APISIX.</span>
    </div>
  </section>
</template>

<style scoped>
.doc-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}

.search-filter-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  flex: 1;
}

.search-box {
  min-width: 15rem;
  flex: 1;
}

.form-input, .form-select {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--border);
  border-radius: 0.375rem;
  background: var(--surface);
  color: var(--text);
  font: inherit;
}

.form-input:focus, .form-select:focus {
  outline: 2px solid var(--accent);
}

.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr));
  gap: 1.25rem;
}

.doc-card {
  display: flex;
  flex-direction: column;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.doc-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.doc-card-top {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.doc-category-tag {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  background: var(--bg);
  border: 1px solid var(--border);
}

.doc-category-tag.cat-student { background: #e3f2fd; color: #0d47a1; border-color: #bbdefb; }
.doc-category-tag.cat-technician { background: #e8f5e9; color: #1b5e20; border-color: #c8e6c9; }
.doc-category-tag.cat-manager { background: #fff3e0; color: #e65100; border-color: #ffe0b2; }
.doc-category-tag.cat-admin { background: #f3e5f5; color: #4a148c; border-color: #e1bee7; }
.doc-category-tag.cat-general { background: #f5f5f5; color: #333; border-color: #e0e0e0; }

.badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  border-radius: 0.25rem;
}

.custom-tag {
  background: var(--accent);
  color: #fff;
  font-size: 0.6875rem;
}

.doc-title {
  margin: 0 0 0.5rem;
  font-size: 1.0625rem;
  line-height: 1.4;
}

.doc-desc {
  font-size: 0.875rem;
  color: var(--muted);
  line-height: 1.5;
  margin: 0 0 1rem;
}

.doc-meta {
  margin-top: auto;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border);
  font-size: 0.75rem;
  color: var(--muted);
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-row {
  display: flex;
  justify-content: space-between;
}

.meta-item code {
  font-size: 0.75rem;
  background: var(--bg);
  padding: 0.1rem 0.25rem;
  border-radius: 0.2rem;
}

.meta-uploader {
  font-size: 0.75rem;
  color: var(--muted);
}

.doc-card-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
  flex: 1;
  text-align: center;
}

.storage-notice {
  margin-top: 2rem;
  padding: 0.875rem 1rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  color: var(--muted);
}
</style>
