<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'uploaded'): void
}>()

const uploadForm = ref({
  title: '',
  description: '',
  category: 'GENERAL' as 'GENERAL' | 'STUDENT' | 'TECHNICIAN' | 'MANAGER' | 'ADMIN',
  fileName: '',
  fileContent: '',
  allowedRoles: ['ROLE_STUDENT', 'ROLE_TECHNICIAN', 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'],
})
const uploadFileSelected = ref<File | null>(null)
const uploadLoading = ref(false)
const uploadError = ref<string | null>(null)
const uploadSuccess = ref<string | null>(null)

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    uploadFileSelected.value = file
    if (!uploadForm.value.title) {
      uploadForm.value.title = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ')
    }
    // Tự động chuẩn hóa tên tệp theo quy chuẩn APISIX (/api/files/<đoạn-hợp-lệ>)
    const cleanName = file.name
      .toLowerCase()
      .replace(/[^a-z0-9._-]/g, '-')
      .replace(/-+/g, '-')
    uploadForm.value.fileName = cleanName
  }
}

async function handleUpload() {
  uploadError.value = null
  uploadSuccess.value = null

  if (!uploadForm.value.title.trim()) {
    uploadError.value = 'Vui lòng nhập tiêu đề tài liệu.'
    return
  }

  let finalFileName = uploadForm.value.fileName.trim()
  if (!finalFileName) {
    finalFileName = uploadForm.value.title
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036F]/g, '')
      .replace(/đ/g, 'd')
      .replace(/[^a-z0-9._-]/g, '-')
      .replace(/-+/g, '-')
      + '.md'
  }

  // Đảm bảo đuôi tệp
  if (!finalFileName.includes('.')) {
    finalFileName += '.md'
  }

  let dir = 'guides/public'
  if (uploadForm.value.category === 'ADMIN') dir = 'guides/admin'
  else if (uploadForm.value.category === 'TECHNICIAN' || uploadForm.value.category === 'MANAGER') dir = 'guides/technician'

  const filePath = `${dir}/${finalFileName}`

  uploadLoading.value = true
  try {
    let payload: Blob | string = uploadForm.value.fileContent
    let fileSizeStr = '1.0 KB'

    if (uploadFileSelected.value) {
      payload = uploadFileSelected.value
      fileSizeStr = `${(uploadFileSelected.value.size / 1024).toFixed(1)} KB`
    }
    else if (!uploadForm.value.fileContent.trim()) {
      uploadError.value = 'Vui lòng chọn tệp đính kèm hoặc soạn nội dung văn bản.'
      uploadLoading.value = false
      return
    }

    // 1. Tải tệp lên SeaweedFS qua gateway: PUT /gw/api/files/...
    await $fetch(`/gw/api/files/${filePath}`, {
      method: 'PUT',
      headers: {
        'Content-Type': finalFileName.endsWith('.md') ? 'text/markdown; charset=utf-8' : 'text/plain; charset=utf-8',
      },
      body: payload,
    })

    // 2. Lưu metadata tài liệu vào server portal index
    await $fetch('/api/portal/documents', {
      method: 'POST',
      body: {
        title: uploadForm.value.title.trim(),
        description: uploadForm.value.description.trim() || 'Tài liệu hướng dẫn bổ sung.',
        category: uploadForm.value.category,
        fileName: finalFileName,
        filePath,
        fileSize: fileSizeStr,
        allowedRoles: uploadForm.value.allowedRoles,
      },
    })

    uploadSuccess.value = 'Tải lên tài liệu và đồng bộ SeaweedFS thành công!'
    emit('uploaded')

    setTimeout(() => {
      emit('close')
      uploadSuccess.value = null
      uploadForm.value = {
        title: '',
        description: '',
        category: 'GENERAL',
        fileName: '',
        fileContent: '',
        allowedRoles: ['ROLE_STUDENT', 'ROLE_TECHNICIAN', 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'],
      }
      uploadFileSelected.value = null
    }, 1200)
  }
  catch (err: any) {
    if (err?.statusCode === 403 || err?.status === 403) {
      uploadError.value = 'Bạn không có quyền tải lên tài liệu (403 Forbidden). Chỉ Trưởng phòng lab và Quản trị viên mới được ghi.'
    }
    else {
      uploadError.value = `Lỗi tải lên: ${err?.data?.message || err?.message || 'Không thể lưu tệp qua gateway'}`
    }
  }
  finally {
    uploadLoading.value = false
  }
}
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-dialog" role="dialog" aria-modal="true">
      <header class="modal-header">
        <h3 class="modal-title">Tải lên Tài liệu Hướng dẫn Mới</h3>
        <button class="close-btn" type="button" aria-label="Đóng" @click="$emit('close')">×</button>
      </header>

      <form class="modal-body" @submit.prevent="handleUpload">
        <div v-if="uploadError" class="notice danger mb-3">{{ uploadError }}</div>
        <div v-if="uploadSuccess" class="notice success mb-3">{{ uploadSuccess }}</div>

        <div class="form-group">
          <label class="form-label" for="doc-title">Tiêu đề tài liệu <span class="req">*</span></label>
          <input
            id="doc-title"
            v-model="uploadForm.title"
            type="text"
            class="form-input"
            placeholder="VD: Quy trình kiểm tra card mạng switch CS1"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="doc-desc">Mô tả tóm tắt</label>
          <textarea
            id="doc-desc"
            v-model="uploadForm.description"
            class="form-input"
            rows="2"
            placeholder="Mô tả ngắn gọn nội dung và đối tượng áp dụng"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label" for="doc-cat">Danh mục tài liệu</label>
            <select id="doc-cat" v-model="uploadForm.category" class="form-select">
              <option value="GENERAL">Nội quy Chung</option>
              <option value="STUDENT">Hướng dẫn Sinh viên</option>
              <option value="TECHNICIAN">Kỹ thuật viên</option>
              <option value="MANAGER">Trưởng phòng Lab</option>
              <option value="ADMIN">Quản trị viên</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label" for="doc-filename">Tên tệp SeaweedFS</label>
            <input
              id="doc-filename"
              v-model="uploadForm.fileName"
              type="text"
              class="form-input"
              placeholder="VD: kiem-tra-switch-cs1.md"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="doc-file">Chọn tệp đính kèm (.md, .txt, .pdf)</label>
          <input
            id="doc-file"
            type="file"
            class="form-file"
            accept=".md,.txt,.pdf,.png,.jpg"
            @change="onFileChange"
          />
        </div>

        <div v-if="!uploadFileSelected" class="form-group">
          <label class="form-label" for="doc-content">Hoặc soạn nội dung văn bản trực tiếp:</label>
          <textarea
            id="doc-content"
            v-model="uploadForm.fileContent"
            class="form-input font-mono"
            rows="5"
            placeholder="# Tiêu đề tài liệu&#10;&#10;Nội dung hướng dẫn chi tiết..."
          />
        </div>

        <footer class="modal-footer mt-4">
          <button class="btn secondary" type="button" :disabled="uploadLoading" @click="$emit('close')">
            Hủy
          </button>
          <button class="btn" type="submit" :disabled="uploadLoading">
            <span v-if="uploadLoading">Đang tải lên SeaweedFS…</span>
            <span v-else>Tải lên & Công bố</span>
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-dialog {
  background: var(--surface);
  border-radius: 0.5rem;
  width: 100%;
  max-width: 32rem;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.modal-header {
  padding: 1.25rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.modal-title {
  margin: 0.25rem 0 0;
  font-size: 1.125rem;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: var(--muted);
}

.close-btn:hover {
  color: var(--text);
}

.modal-body {
  padding: 1.25rem;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  font-size: 0.8125rem;
  font-weight: 600;
  margin-bottom: 0.375rem;
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-file {
  width: 100%;
}

.font-mono {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}

.req {
  color: var(--danger-text);
}

.mb-3 { margin-bottom: 0.75rem; }
.mt-4 { margin-top: 1.25rem; }

.notice.success {
  background: #e8f5e9;
  color: #1b5e20;
  padding: 0.75rem 1rem;
  border-radius: 0.375rem;
}
</style>
