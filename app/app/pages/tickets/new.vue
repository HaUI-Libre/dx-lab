<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

<script setup lang="ts">
import type { Asset, SiteLocation, Suggestion, Ticket } from '~/utils/helpdesk'

// Báo hỏng (kịch bản 1 và 7 của docs/usecases.md). Thiết bị lấy từ hệ thống tài sản
// của khách hàng qua /api/assets (#72); khi dịch vụ đó chưa chạy hoặc profile
// integration tắt, người báo chọn vị trí bằng tay và ticket vẫn gửi được.
const MAX_FILES = 3
const MAX_BYTES = 20 * 1024 * 1024
const IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/webp']

const { data: locations } = await useFetch<SiteLocation[]>('/gw/api/data/locations', { key: 'locations' })
const { data: myAssets, error: assetsError } = await useFetch<Asset[]>('/gw/api/assets/me', {
  key: 'assets-me', retry: false, lazy: true,
})

const form = reactive({
  title: '',
  description: '',
  category: 'HARDWARE',
  priority: 'MEDIUM',
  location_id: null as number | null,
  asset_id: null as number | null,
})
const assetTag = ref('')
const tagResult = ref<string | null>(null)
const files = ref<File[]>([])
const message = ref<string | null>(null)
const busy = ref(false)

// Gợi ý phân loại (kịch bản 6): chỉ điền khi người dùng bấm "Dùng gợi ý"; mức ưu tiên
// cuối cùng do trưởng phòng chốt khi phân công. Dịch vụ lỗi thì form vẫn gửi bình thường.
const suggestion = ref<Suggestion | null>(null)
const suggestionState = ref<'idle' | 'loading' | 'ready' | 'unavailable'>('idle')
let suggestTimer: ReturnType<typeof setTimeout> | undefined
let suggestSeq = 0

watch(() => [form.title, form.description], () => {
  clearTimeout(suggestTimer)
  if (form.description.trim().length < 15) {
    suggestion.value = null
    suggestionState.value = 'idle'
    return
  }
  suggestTimer = setTimeout(suggest, 700)
})

async function suggest() {
  const seq = ++suggestSeq
  suggestionState.value = 'loading'
  try {
    const result = await $fetch<Suggestion>('/gw/api/ai/classify', {
      method: 'POST',
      body: { title: form.title.trim(), description: form.description.trim() },
    })
    if (seq !== suggestSeq) return
    const valid = result && result.category in CATEGORY_LABELS && result.priority in PRIORITY_LABELS
    suggestion.value = valid ? result : null
    suggestionState.value = valid ? 'ready' : 'unavailable'
  }
  catch {
    if (seq !== suggestSeq) return
    suggestion.value = null
    suggestionState.value = 'unavailable'
  }
}

function useSuggestion() {
  if (!suggestion.value) return
  form.category = suggestion.value.category
  form.priority = suggestion.value.priority
}

const assetsAvailable = computed(() => !assetsError.value && Array.isArray(myAssets.value))

function pickAsset(asset: Asset) {
  form.asset_id = asset.id
  if (asset.location_id) form.location_id = asset.location_id
  assetTag.value = asset.asset_tag
  tagResult.value = `${asset.asset_tag}${asset.name ? ` – ${asset.name}` : ''}`
}

async function lookupTag() {
  const tag = assetTag.value.trim()
  if (!tag) return
  try {
    pickAsset(await $fetch<Asset>(`/gw/api/assets/bytag/${encodeURIComponent(tag)}`))
  }
  catch {
    form.asset_id = null
    tagResult.value = null
    message.value = 'Không tra được mã tài sản trên hệ thống tài sản. Chọn vị trí bên dưới; mã bạn nhập sẽ được ghi vào mô tả.'
  }
}

function onFiles(event: Event) {
  const picked = Array.from((event.target as HTMLInputElement).files ?? [])
  const bad = picked.find(f => !IMAGE_TYPES.includes(f.type) || f.size > MAX_BYTES)
  if (bad) {
    message.value = `Tệp "${bad.name}" không hợp lệ: chỉ nhận PNG, JPEG, WebP tới 20 MB.`
    return
  }
  files.value = picked.slice(0, MAX_FILES)
}

function extension(file: File) {
  return { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp' }[file.type] ?? 'bin'
}

async function save(send: boolean) {
  message.value = null
  if (!form.title.trim() || !form.description.trim() || !form.location_id) {
    message.value = 'Cần tiêu đề, mô tả và vị trí.'
    return
  }
  busy.value = true
  try {
    const tag = assetTag.value.trim()
    const description = !form.asset_id && tag && !form.description.includes(tag)
      ? `${form.description.trim()}\n\nMã tài sản: ${tag}`
      : form.description.trim()
    const ticket = await dataApi<Ticket>('/tickets', {
      method: 'POST',
      body: { ...form, title: form.title.trim(), description, asset_id: form.asset_id ?? undefined },
    })
    // Tải ảnh lên bucket trước, rồi đăng ký metadata để Data API kiểm tra tệp đã có
    for (const file of files.value) {
      const key = `tickets/${ticket.id}/${crypto.randomUUID()}.${extension(file)}`
      await $fetch(`/gw/api/files/${key}`, { method: 'PUT', body: file, headers: { 'Content-Type': file.type } })
      await dataApi(`/tickets/${ticket.id}/attachments`, {
        method: 'POST',
        body: { storage_key: key, file_name: file.name, content_type: file.type, size_bytes: file.size },
      })
    }
    if (send) {
      await dataApi(`/tickets/${ticket.id}/actions/submit`, { method: 'POST', body: {} })
    }
    await navigateTo(`/tickets/${ticket.id}`)
  }
  catch (error) {
    message.value = errorMessage(error)
  }
  finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="card">
    <h1>Báo hỏng thiết bị</h1>

    <fieldset>
      <legend>Thiết bị</legend>
      <template v-if="assetsAvailable">
        <p v-if="!myAssets?.length" class="muted">Hệ thống tài sản chưa ghi thiết bị nào giao cho bạn.</p>
        <div v-else class="assets">
          <button
            v-for="a in myAssets" :key="a.id" type="button" class="asset"
            :class="{ chosen: form.asset_id === a.id }" @click="pickAsset(a)"
          >
            <strong>{{ a.asset_tag }}</strong>
            <span>{{ a.name }}</span>
            <span class="muted small">{{ a.location }}</span>
          </button>
        </div>
      </template>
      <p v-else class="notice warn" role="status">
        Chưa kết nối được hệ thống tài sản, nên chưa lấy được thiết bị của bạn.
        Bạn vẫn báo hỏng được: nhập mã dán trên máy (nếu có) và chọn vị trí.
      </p>

      <label>
        Mã tài sản dán trên máy phòng thực hành
        <span class="row">
          <input v-model="assetTag" placeholder="Ví dụ: HAUI-CS1-PC04" @keydown.enter.prevent="lookupTag">
          <button type="button" class="btn secondary" :disabled="!assetTag.trim()" @click="lookupTag">Tra cứu</button>
        </span>
      </label>
      <p v-if="tagResult" class="muted small">Đã chọn: {{ tagResult }}</p>

      <label>
        Vị trí
        <select v-model.number="form.location_id" required>
          <option :value="null" disabled>Chọn phòng hoặc tòa nhà</option>
          <option v-for="l in locations" :key="l.location_id" :value="l.location_id">{{ l.co_so }} · {{ l.code }}</option>
        </select>
      </label>
    </fieldset>

    <fieldset>
      <legend>Mô tả sự cố</legend>
      <label>
        Tiêu đề
        <input v-model="form.title" maxlength="200" placeholder="Máy PC-04 phòng C401 không khởi động được" required>
      </label>
      <label>
        Mô tả
        <textarea v-model="form.description" rows="4" placeholder="Hiện tượng, thời điểm, đã thử gì" required />
      </label>
      <div class="suggestion" aria-live="polite">
        <strong>Gợi ý phân loại</strong>
        <span v-if="suggestionState === 'idle'" class="muted small">Nhập mô tả (từ 15 ký tự) để nhận gợi ý loại sự cố và mức ưu tiên.</span>
        <span v-else-if="suggestionState === 'loading'" class="muted small">Đang phân tích mô tả…</span>
        <span v-else-if="suggestionState === 'unavailable'" class="muted small">
          Chưa có gợi ý: dịch vụ phân loại chưa sẵn sàng. Bạn tự chọn loại và mức ưu tiên bên dưới.
        </span>
        <template v-else-if="suggestion">
          <span>
            {{ CATEGORY_LABELS[suggestion.category] }} · {{ PRIORITY_LABELS[suggestion.priority] }}
            <span class="muted small">
              ({{ suggestion.source === 'rules' ? 'theo luật từ khoá' : 'theo mô hình' }}<template v-if="suggestion.keywords?.length">; từ khoá: {{ suggestion.keywords.join(', ') }}</template>)
            </span>
          </span>
          <button
            type="button" class="btn secondary btn-sm"
            :disabled="form.category === suggestion.category && form.priority === suggestion.priority"
            @click="useSuggestion"
          >
            Dùng gợi ý
          </button>
        </template>
      </div>
      <div class="row">
        <label>
          Loại sự cố
          <select v-model="form.category">
            <option v-for="(label, code) in CATEGORY_LABELS" :key="code" :value="code">{{ label }}</option>
          </select>
        </label>
        <label>
          Mức ưu tiên đề xuất
          <select v-model="form.priority">
            <option v-for="(label, code) in PRIORITY_LABELS" :key="code" :value="code">{{ label }}</option>
          </select>
        </label>
      </div>
      <p class="muted small">Trưởng phòng lab có thể chỉnh mức ưu tiên khi phân công.</p>
      <label>
        Ảnh lỗi (tối đa {{ MAX_FILES }} ảnh PNG, JPEG, WebP, mỗi ảnh tới 20 MB)
        <input type="file" accept="image/png,image/jpeg,image/webp" multiple @change="onFiles">
      </label>
      <ul v-if="files.length" class="muted small">
        <li v-for="f in files" :key="f.name">{{ f.name }} ({{ Math.ceil(f.size / 1024) }} KB)</li>
      </ul>
    </fieldset>

    <p v-if="message" class="notice danger" role="alert">{{ message }}</p>
    <div class="actions">
      <button class="btn" type="button" :disabled="busy" @click="save(true)">Gửi yêu cầu</button>
      <button class="btn secondary" type="button" :disabled="busy" @click="save(false)">Lưu nháp</button>
      <NuxtLink to="/tickets" class="btn secondary">Huỷ</NuxtLink>
    </div>
  </section>
</template>

<style scoped>
h1 { margin: 0 0 1rem; font-size: 1.5rem; }
fieldset { border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; margin: 0 0 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
legend { font-weight: 700; padding: 0 0.25rem; }
label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.875rem; color: var(--muted); }
input, select, textarea { font: inherit; padding: 0.5rem; border: 1px solid var(--border); border-radius: 0.375rem; background: var(--surface); color: var(--text); }
.row { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.row > label { flex: 1; min-width: 12rem; }
.row > input { flex: 1; }
.assets { display: grid; grid-template-columns: repeat(auto-fill, minmax(12rem, 1fr)); gap: 0.5rem; }
.asset { display: flex; flex-direction: column; align-items: flex-start; gap: 0.125rem; padding: 0.625rem; border: 1px solid var(--border); border-radius: 0.375rem; background: var(--bg); color: var(--text); font: inherit; cursor: pointer; text-align: left; }
.asset.chosen { border-color: var(--accent); outline: 2px solid var(--accent); }
.actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.suggestion { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem 0.75rem; padding: 0.625rem 0.75rem; border: 1px dashed var(--border); border-radius: 0.375rem; background: var(--bg); }
.btn-sm { padding: 0.3rem 0.7rem; font-size: 0.8125rem; }
.muted { color: var(--muted); }
.small { font-size: 0.8125rem; }
.notice { padding: 0.75rem 1rem; border-radius: 0.375rem; margin: 0; }
.notice.danger { background: var(--danger-bg); color: var(--danger-text); }
.notice.warn { background: var(--warn-bg); color: var(--warn-text); }
</style>
