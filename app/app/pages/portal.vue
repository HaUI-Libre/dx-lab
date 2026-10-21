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
  fileType: string
  allowedRoles: string[]
  updatedAt: string
  uploadedBy?: string
  isCustom?: boolean
}

interface CampusUnit {
  id: string
  code: string
  name: string
  location: string
  hotline: string
  email: string
  scope: string
  manager: string
  technicians: string[]
}

interface RoleGroup {
  id: string
  role: string
  roleLabel: string
  name: string
  description: string
  duties: string[]
  workflowPermissions: string[]
}

interface GroupsResponse {
  campusUnits: CampusUnit[]
  roleGroups: RoleGroup[]
  userContext: {
    currentCoSo?: string
    currentRoles: string[]
    matchedUnit?: CampusUnit
    matchedRoles: RoleGroup[]
  }
}

const ROLE_LABELS: Record<string, string> = {
  ROLE_STUDENT: 'Sinh viên',
  ROLE_TECHNICIAN: 'Kỹ thuật viên',
  ROLE_LAB_MANAGER: 'Trưởng phòng lab',
  ROLE_ADMIN: 'Quản trị hệ thống',
}

const CAMPUS_LABELS: Record<string, string> = {
  CS1: 'Cơ sở 1 (Khu A & B – Bắc Từ Liêm)',
  CS2: 'Cơ sở 2 (Tây Tựu – Bắc Từ Liêm)',
  CS3: 'Cơ sở 3 (Phủ Lý – Hà Nam)',
}

const route = useRoute()
const activeTab = ref<'profile' | 'groups' | 'documents'>('profile')

// Kiểm tra query/hash để chuyển tab nếu có
onMounted(() => {
  if (route.query.tab === 'documents' || route.hash === '#documents') activeTab.value = 'documents'
  else if (route.query.tab === 'groups' || route.hash === '#groups') activeTab.value = 'groups'
  else activeTab.value = 'profile'
})

// Thông tin người dùng hiện tại từ Gateway
const { data: me, error: meError, refresh: refreshMe } = await useFetch<Me>('/gw/api/me', {
  key: 'portal-me',
  retry: false,
})

// Chuyển hướng nếu chưa đăng nhập
if (meError.value?.statusCode === 401) {
  navigateTo('/auth/login')
}

// Dữ liệu nhóm & đơn vị
const { data: groupsData, refresh: refreshGroups } = await useFetch<GroupsResponse>('/api/portal/groups', {
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

// Tìm kiếm & lọc tài liệu
const searchQuery = ref('')
const selectedCategory = ref('ALL')

const filteredDocuments = computed(() => {
  let list = documents.value ?? []
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
    await refreshDocs()

    setTimeout(() => {
      showUploadModal.value = false
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
          <span class="tab-icon">👤</span>
          <span class="tab-label">Hồ sơ cá nhân</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'groups' }"
          type="button"
          @click="activeTab = 'groups'"
        >
          <span class="tab-icon">🏢</span>
          <span class="tab-label">Nhóm & Đơn vị</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'documents' }"
          type="button"
          @click="activeTab = 'documents'"
        >
          <span class="tab-icon">📚</span>
          <span class="tab-label">Tài liệu hướng dẫn</span>
          <span v-if="documents?.length" class="badge-count">{{ documents.length }}</span>
        </button>
      </nav>
    </header>

    <!-- TAB 1: HỒ SƠ CÁ NHÂN -->
    <section v-if="activeTab === 'profile'" class="tab-pane" aria-labelledby="profile-heading">
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

    <!-- TAB 2: NHÓM & ĐƠN VỊ -->
    <section v-if="activeTab === 'groups'" class="tab-pane" aria-labelledby="groups-heading">
      <!-- Cơ sở trực thuộc của người dùng -->
      <div v-if="groupsData?.userContext?.matchedUnit" class="card highlight-card">
        <div class="highlight-badge">Đơn vị trực thuộc của bạn</div>
        <div class="unit-banner-content">
          <div>
            <h2>{{ groupsData.userContext.matchedUnit.name }} ({{ groupsData.userContext.matchedUnit.code }})</h2>
            <p class="unit-location">📍 {{ groupsData.userContext.matchedUnit.location }}</p>
            <p class="unit-scope">{{ groupsData.userContext.matchedUnit.scope }}</p>
          </div>
          <div class="contact-box">
            <div>📞 <strong>Hotline:</strong> {{ groupsData.userContext.matchedUnit.hotline }}</div>
            <div>✉️ <strong>Email:</strong> {{ groupsData.userContext.matchedUnit.email }}</div>
            <div>👤 <strong>Trưởng phòng phụ trách:</strong> {{ groupsData.userContext.matchedUnit.manager }}</div>
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
          <p class="unit-loc">📍 {{ unit.location }}</p>
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

    <!-- TAB 3: TÀI LIỆU HƯỚNG DẪN -->
    <section v-if="activeTab === 'documents'" class="tab-pane" aria-labelledby="documents-heading">
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
            @click="showUploadModal = true"
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
            <span class="doc-type-icon">📄</span>
            <span class="doc-category-tag" :class="`cat-${doc.category.toLowerCase()}`">
              {{ doc.categoryLabel }}
            </span>
            <span v-if="doc.isCustom" class="badge custom-tag">Mới thêm</span>
          </div>

          <h3 class="doc-title">{{ doc.title }}</h3>
          <p class="doc-desc">{{ doc.description }}</p>

          <div class="doc-meta">
            <div class="meta-item">📁 <code>{{ doc.fileName }}</code></div>
            <div class="meta-row">
              <span>⚖️ {{ doc.fileSize }}</span>
              <span>📅 {{ doc.updatedAt }}</span>
            </div>
            <div v-if="doc.uploadedBy" class="meta-uploader">
              Tác giả: {{ doc.uploadedBy }}
            </div>
          </div>

          <div class="doc-card-actions">
            <button class="btn secondary btn-sm" type="button" @click="openPreview(doc)">
              👁️ Xem nội dung
            </button>
            <button class="btn btn-sm" type="button" @click="downloadFile(doc)">
              ⬇️ Tải về
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
        <span>ℹ️ Tệp tài liệu được lưu trữ phân tán trên <strong>SeaweedFS</strong> (bucket <code>documents</code>) và truy xuất qua tuyến <code>/api/files</code> của Apache APISIX.</span>
      </div>
    </section>

    <!-- MODAL XEM TRƯỚC TÀI LIỆU -->
    <div v-if="previewDoc" class="modal-backdrop" @click.self="closePreview">
      <div class="modal-dialog modal-lg" role="dialog" aria-modal="true">
        <header class="modal-header">
          <div>
            <span class="badge role-badge">{{ previewDoc.categoryLabel }}</span>
            <h3 class="modal-title">{{ previewDoc.title }}</h3>
            <p class="modal-subtitle">Đường dẫn: <code>/api/files/{{ previewDoc.filePath }}</code></p>
          </div>
          <button class="close-btn" type="button" aria-label="Đóng" @click="closePreview">×</button>
        </header>

        <div class="modal-body">
          <div v-if="previewLoading" class="preview-loading">
            <p>Đang nạp tài liệu từ SeaweedFS qua API Gateway…</p>
          </div>
          <div v-else-if="previewError" class="notice danger">
            <p>{{ previewError }}</p>
          </div>
          <pre v-else class="preview-text">{{ previewContent }}</pre>
        </div>

        <footer class="modal-footer">
          <button class="btn secondary" type="button" @click="closePreview">Đóng</button>
          <button class="btn" type="button" @click="downloadFile(previewDoc)">⬇️ Tải tệp về máy</button>
        </footer>
      </div>
    </div>

    <!-- MODAL TẢI LÊN TÀI LIỆU MỚI -->
    <div v-if="showUploadModal" class="modal-backdrop" @click.self="showUploadModal = false">
      <div class="modal-dialog" role="dialog" aria-modal="true">
        <header class="modal-header">
          <h3 class="modal-title">Tải lên Tài liệu Hướng dẫn Mới</h3>
          <button class="close-btn" type="button" aria-label="Đóng" @click="showUploadModal = false">×</button>
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
            <button class="btn secondary" type="button" :disabled="uploadLoading" @click="showUploadModal = false">
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

/* Grids */
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

/* Profile Card */
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

/* Permissions card */
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

/* Units & Groups tab */
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

/* Documents tab */
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

.doc-type-icon {
  font-size: 1.25rem;
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

/* Modals */
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

.modal-dialog.modal-lg {
  max-width: 50rem;
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

.modal-subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.75rem;
  color: var(--muted);
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

.preview-text {
  background: var(--bg);
  padding: 1rem;
  border-radius: 0.375rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  margin: 0;
}

.preview-loading {
  padding: 2rem;
  text-align: center;
  color: var(--muted);
}

/* Forms */
.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  font-size: 0.8125rem;
  font-weight: 600;
  margin-bottom: 0.375rem;
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
