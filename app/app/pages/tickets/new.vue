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
useHead({ title: 'Báo hỏng thiết bị' })

const { data: locations } = await useFetch<SiteLocation[]>('/gw/api/data/locations', { key: 'locations' })
const { data: myAssets, error: assetsError, pending: assetsPending } = await useFetch<Asset[]>('/gw/api/assets/me', {
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
const tagBusy = ref(false)
const files = ref<{ file: File, url: string }[]>([])
const message = ref<string | null>(null)
const busy = ref<'send' | 'draft' | null>(null)
const created = ref<{ id: string, sent: boolean } | null>(null)
const { show } = useToast()

// ---- Kiểm tra từng trường khi rời ô ----
const touched = reactive({ title: false, description: false, location: false })
const errors = computed(() => ({
  title: !form.title.trim() ? 'Cần tiêu đề ngắn, ví dụ "PC-04 phòng C401 không lên nguồn".' : '',
  description: !form.description.trim() ? 'Cần mô tả hiện tượng để kỹ thuật viên chuẩn bị.' : '',
  location: !form.location_id ? 'Chọn phòng hoặc tòa nhà.' : '',
}))
const show_ = (f: keyof typeof touched) => touched[f] && !!errors.value[f]

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
  tagBusy.value = true
  try {
    pickAsset(await $fetch<Asset>(`/gw/api/assets/bytag/${encodeURIComponent(tag)}`))
  }
  catch {
    form.asset_id = null
    tagResult.value = null
    message.value = 'Không tra được mã tài sản trên hệ thống tài sản. Chọn vị trí bên dưới; mã bạn nhập sẽ được ghi vào mô tả.'
  }
  finally {
    tagBusy.value = false
  }
}

function onFiles(event: Event) {
  const input = event.target as HTMLInputElement
  const picked = Array.from(input.files ?? [])
  input.value = ''
  const bad = picked.find(f => !IMAGE_TYPES.includes(f.type) || f.size > MAX_BYTES)
  if (bad) {
    message.value = `Tệp "${bad.name}" không hợp lệ: chỉ nhận PNG, JPEG, WebP tới 20 MB.`
    return
  }
  const room = MAX_FILES - files.value.length
  files.value = [...files.value, ...picked.slice(0, room).map(file => ({ file, url: URL.createObjectURL(file) }))]
  if (picked.length > room) message.value = `Chỉ giữ ${MAX_FILES} ảnh đầu tiên.`
}

function removeFile(i: number) {
  URL.revokeObjectURL(files.value[i]!.url)
  files.value = files.value.filter((_, k) => k !== i)
}
onBeforeUnmount(() => files.value.forEach(f => URL.revokeObjectURL(f.url)))

function extension(file: File) {
  return { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp' }[file.type] ?? 'bin'
}

async function save(send: boolean) {
  if (busy.value) return
  message.value = null
  touched.title = touched.description = touched.location = true
  if (errors.value.title || errors.value.description || errors.value.location) {
    message.value = 'Còn ô chưa điền, xem các dòng báo lỗi bên dưới mỗi ô.'
    return
  }
  busy.value = send ? 'send' : 'draft'
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
    for (const { file } of files.value) {
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
    created.value = { id: ticket.id, sent: send }
    show({ kind: 'success', title: send ? 'Đã gửi yêu cầu' : 'Đã lưu bản nháp', body: `Mã phiếu ${ticketCode(ticket.id)}.` })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  catch (error) {
    message.value = errorMessage(error)
    show({ kind: 'error', title: 'Chưa gửi được', body: message.value })
  }
  finally {
    busy.value = null
  }
}

const copied = ref(false)
async function copyId() {
  if (!created.value) return
  try {
    await navigator.clipboard.writeText(created.value.id)
    copied.value = true
    setTimeout(() => { copied.value = false }, 1800)
  }
  catch {
    show({ kind: 'error', title: 'Không sao chép được', body: 'Trình duyệt chặn bộ nhớ tạm. Chọn mã và sao chép thủ công.' })
  }
}

function startOver() {
  created.value = null
  Object.assign(form, { title: '', description: '', category: 'HARDWARE', priority: 'MEDIUM', location_id: null, asset_id: null })
  assetTag.value = ''
  tagResult.value = null
  files.value.forEach(f => URL.revokeObjectURL(f.url))
  files.value = []
  touched.title = touched.description = touched.location = false
}
</script>

<template>
  <div class="page">
    <header class="page-head reveal" style="--i: 0">
      <NuxtLink to="/tickets" class="crumb">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 6-6 6 6 6" /></svg>
        Danh sách
      </NuxtLink>
      <h1>Báo hỏng thiết bị</h1>
      <p class="lede">Chọn thiết bị, mô tả sự cố, thêm ảnh nếu có. Phiếu tự chuyển tới trưởng phòng lab của cơ sở.</p>
    </header>

    <Transition name="swap" mode="out-in">
      <!-- Gửi xong: hiện mã phiếu mới bằng phông mono, có nút sao chép -->
      <section v-if="created" key="done" class="card done" role="status">
        <svg class="done-icon" viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="20" /><path d="m15 24.5 6.5 6.5L33 18" /></svg>
        <span class="eyebrow">{{ created.sent ? 'Đã gửi yêu cầu' : 'Đã lưu bản nháp' }}</span>
        <span class="done-code">{{ ticketCode(created.id) }}</span>
        <p>{{ created.sent ? 'Trưởng phòng lab sẽ tiếp nhận và phân công. Theo dõi trạng thái trong danh sách phiếu.' : 'Bản nháp chưa gửi đi. Mở phiếu để gửi khi sẵn sàng.' }}</p>
        <div class="row">
          <button class="btn secondary" type="button" @click="copyId">{{ copied ? 'Đã sao chép mã' : 'Sao chép mã phiếu' }}</button>
          <NuxtLink class="btn" :to="`/tickets/${created.id}`">Xem phiếu</NuxtLink>
          <button class="btn quiet" type="button" @click="startOver">Báo hỏng thiết bị khác</button>
        </div>
      </section>

      <form v-else key="form" class="form" novalidate @submit.prevent="save(true)">
        <!-- 1. Thiết bị -->
        <fieldset class="card block reveal" style="--i: 1">
          <legend class="block-title"><span class="block-no">1</span> Thiết bị</legend>

          <div v-if="assetsPending && !myAssets && !assetsError" class="assets" aria-busy="true" aria-label="Đang tải thiết bị của bạn">
            <span v-for="n in 3" :key="n" class="skeleton" style="height: 4.75rem" />
          </div>
          <template v-else-if="assetsAvailable">
            <p v-if="!myAssets?.length" class="hint">Hệ thống tài sản chưa ghi thiết bị nào giao cho bạn.</p>
            <div v-else class="assets" role="group" aria-label="Thiết bị của bạn">
              <button
                v-for="a in myAssets" :key="a.id" type="button" class="asset"
                :aria-pressed="form.asset_id === a.id" @click="pickAsset(a)"
              >
                <span class="code">{{ a.asset_tag }}</span>
                <span class="asset-name">{{ a.name }}</span>
                <span class="asset-loc">{{ a.location }}</span>
              </button>
            </div>
          </template>
          <p v-else class="notice" role="status">
            Chưa kết nối được hệ thống tài sản, nên chưa lấy được thiết bị của bạn.
            Bạn vẫn báo hỏng được: nhập mã dán trên máy (nếu có) và chọn vị trí.
          </p>

          <div class="field">
            <label class="field-label" for="f-tag">Mã tài sản dán trên máy phòng thực hành</label>
            <div class="inline">
              <input id="f-tag" v-model="assetTag" class="input mono" placeholder="Ví dụ: HAUI-CS1-PC04" autocomplete="off" @keydown.enter.prevent="lookupTag">
              <button type="button" class="btn secondary" :aria-busy="tagBusy" :disabled="!assetTag.trim()" @click="lookupTag">Tra cứu</button>
            </div>
            <Transition name="field-msg"><span v-if="tagResult" class="field-help">Đã chọn: <span class="code">{{ tagResult }}</span></span></Transition>
          </div>

          <div class="field">
            <label class="field-label" for="f-loc">Vị trí</label>
            <select
              id="f-loc" v-model.number="form.location_id" class="input" required
              :aria-invalid="show_('location')" aria-describedby="f-loc-err" @blur="touched.location = true"
            >
              <option :value="null" disabled>Chọn phòng hoặc tòa nhà</option>
              <option v-for="l in locations" :key="l.location_id" :value="l.location_id">{{ l.co_so }} · {{ l.code }}</option>
            </select>
            <Transition name="field-msg"><span v-if="show_('location')" id="f-loc-err" class="field-error">{{ errors.location }}</span></Transition>
          </div>
        </fieldset>

        <!-- 2. Mô tả sự cố -->
        <fieldset class="card block reveal" style="--i: 2">
          <legend class="block-title"><span class="block-no">2</span> Mô tả sự cố</legend>
          <div class="field">
            <label class="field-label" for="f-title">Tiêu đề</label>
            <input
              id="f-title" v-model="form.title" class="input" maxlength="200" placeholder="Máy PC-04 phòng C401 không khởi động được" required
              :aria-invalid="show_('title')" aria-describedby="f-title-err" @blur="touched.title = true"
            >
            <Transition name="field-msg"><span v-if="show_('title')" id="f-title-err" class="field-error">{{ errors.title }}</span></Transition>
          </div>
          <div class="field">
            <label class="field-label" for="f-desc">Mô tả</label>
            <textarea
              id="f-desc" v-model="form.description" class="input" rows="4" placeholder="Hiện tượng, thời điểm, đã thử gì" required
              :aria-invalid="show_('description')" aria-describedby="f-desc-err" @blur="touched.description = true"
            />
            <Transition name="field-msg"><span v-if="show_('description')" id="f-desc-err" class="field-error">{{ errors.description }}</span></Transition>
          </div>

          <div class="suggestion" :data-state="suggestionState" aria-live="polite">
            <strong>Gợi ý phân loại</strong>
            <span v-if="suggestionState === 'idle'" class="hint">Nhập mô tả (từ 15 ký tự) để nhận gợi ý loại sự cố và mức ưu tiên.</span>
            <span v-else-if="suggestionState === 'loading'" class="suggest-loading">
              <span class="skeleton" style="width: 9rem; height: 1rem" />
              <span class="visually-hidden">Đang phân tích mô tả</span>
            </span>
            <span v-else-if="suggestionState === 'unavailable'" class="hint">
              Chưa có gợi ý: dịch vụ phân loại chưa sẵn sàng. Bạn tự chọn loại và mức ưu tiên bên dưới.
            </span>
            <template v-else-if="suggestion">
              <span>
                <strong class="suggest-value">{{ CATEGORY_LABELS[suggestion.category] }} · {{ PRIORITY_LABELS[suggestion.priority] }}</strong>
                <span class="hint">
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

          <div class="two">
            <div class="field">
              <label class="field-label" for="f-cat">Loại sự cố</label>
              <select id="f-cat" v-model="form.category" class="input">
                <option v-for="(label, code) in CATEGORY_LABELS" :key="code" :value="code">{{ label }}</option>
              </select>
            </div>
            <div class="field">
              <label class="field-label" for="f-prio">Mức ưu tiên đề xuất</label>
              <select id="f-prio" v-model="form.priority" class="input">
                <option v-for="(label, code) in PRIORITY_LABELS" :key="code" :value="code">{{ label }}</option>
              </select>
            </div>
          </div>
          <p class="hint">Trưởng phòng lab có thể chỉnh mức ưu tiên khi phân công.</p>
        </fieldset>

        <!-- 3. Ảnh -->
        <fieldset class="card block reveal" style="--i: 3">
          <legend class="block-title"><span class="block-no">3</span> Ảnh lỗi</legend>
          <label class="drop" :class="{ full: files.length >= MAX_FILES }">
            <input class="visually-hidden" type="file" accept="image/png,image/jpeg,image/webp" multiple :disabled="files.length >= MAX_FILES" @change="onFiles">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 16V5M7.5 9.5 12 5l4.5 4.5M5 19h14" /></svg>
            <span>Ảnh lỗi (tối đa {{ MAX_FILES }} ảnh PNG, JPEG, WebP, mỗi ảnh tới 20 MB)</span>
            <span class="hint">{{ files.length >= MAX_FILES ? 'Đã đủ số ảnh.' : 'Bấm để chọn ảnh hoặc chụp bằng điện thoại.' }}</span>
          </label>
          <TransitionGroup tag="ul" name="row" class="thumbs">
            <li v-for="(f, i) in files" :key="f.url">
              <img :src="f.url" :alt="f.file.name">
              <span class="thumb-name">{{ f.file.name }} ({{ Math.ceil(f.file.size / 1024) }} KB)</span>
              <button type="button" class="btn quiet btn-sm" :aria-label="`Bỏ ảnh ${f.file.name}`" @click="removeFile(i)">Bỏ</button>
            </li>
          </TransitionGroup>
        </fieldset>

        <Transition name="field-msg">
          <p v-if="message" class="notice" role="alert">{{ message }}</p>
        </Transition>
        <div class="actions reveal" style="--i: 4">
          <button class="btn" type="submit" :aria-busy="busy === 'send'" :disabled="busy === 'draft'">Gửi yêu cầu</button>
          <button class="btn secondary" type="button" :aria-busy="busy === 'draft'" :disabled="busy === 'send'" @click="save(false)">Lưu nháp</button>
          <NuxtLink to="/tickets" class="btn quiet">Huỷ</NuxtLink>
        </div>
      </form>
    </Transition>
  </div>
</template>

<style scoped>
.page { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-5); max-width: 52rem; }
.crumb { display: inline-flex; align-items: center; gap: var(--space-1); font-weight: 700; font-size: var(--text-sm); color: var(--ink-soft); text-decoration: none; }
.crumb:hover { color: var(--ink); }
.crumb svg { width: 1rem; height: 1rem; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.page-head h1 { margin: var(--space-3) 0 var(--space-2); }
.page-head .lede { margin: 0; font-size: var(--text-base); }

.form { display: grid; gap: var(--space-4); }
.block { display: grid; gap: var(--space-4); margin: 0; min-width: 0; }
.block-title { display: flex; align-items: center; gap: var(--space-2); float: left; width: 100%; padding: 0; font-family: var(--font-display); font-weight: 600; font-size: var(--text-lg); }
.block-title + * { clear: both; }
.block-no { display: grid; place-items: center; width: 1.75rem; height: 1.75rem; font-family: var(--font-mono); font-size: var(--text-sm); font-weight: 700; color: var(--on-primary); background: var(--primary); border-radius: var(--radius-pill); }

.hint { font-size: var(--text-sm); color: var(--ink-soft); margin: 0; }
.mono { font-family: var(--font-mono); }
.inline { display: flex; gap: var(--space-2); }
.inline .input { flex: 1; min-width: 0; }
.two { display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: var(--space-4); }
.row { display: flex; flex-wrap: wrap; gap: var(--space-3); justify-content: center; }

.assets { display: grid; grid-template-columns: repeat(auto-fill, minmax(13rem, 1fr)); gap: var(--space-3); }
.asset {
  display: grid;
  justify-items: start;
  gap: var(--space-1);
  padding: var(--space-3);
  font: inherit;
  text-align: left;
  color: var(--ink);
  background: var(--card);
  border: 1px solid var(--rule);
  border-radius: var(--radius-control);
  cursor: pointer;
  transition: border-color var(--dur-fast), transform var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast);
}
.asset:hover { border-color: var(--line); transform: translateY(-1px); }
.asset[aria-pressed="true"] { border-color: var(--brand); box-shadow: inset 0 0 0 1px var(--brand), var(--shadow); }
.asset-name { font-weight: 700; }
.asset-loc { font-size: var(--text-sm); color: var(--ink-soft); }

.suggestion {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--sunk);
  border: 1px dashed var(--line);
  border-radius: var(--radius-control);
  transition: border-color var(--dur);
}
.suggestion[data-state="ready"] { border-style: solid; border-color: var(--brand); }
.suggest-value { color: var(--brand-ink); margin-right: var(--space-1); }
.suggest-loading { display: inline-flex; }

.drop {
  display: grid;
  justify-items: center;
  gap: var(--space-1);
  padding: var(--space-5);
  text-align: center;
  font-weight: 700;
  background: var(--sunk);
  border: 1.5px dashed var(--line);
  border-radius: var(--radius-card);
  cursor: pointer;
  transition: border-color var(--dur-fast), background-color var(--dur-fast);
}
.drop:hover { border-color: var(--brand); }
.drop:focus-within { outline: 3px solid var(--focus); outline-offset: 2px; }
.drop.full { cursor: default; opacity: 0.75; }
.drop svg { width: 1.75rem; height: 1.75rem; fill: none; stroke: var(--brand-ink); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

.thumbs { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(9rem, 1fr)); gap: var(--space-3); }
.thumbs li { display: grid; gap: var(--space-1); font-size: var(--text-sm); }
.thumbs img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; border-radius: var(--radius-control); border: 1px solid var(--rule); }
.thumb-name { overflow-wrap: anywhere; color: var(--ink-soft); }

.notice { margin: 0; padding: var(--space-3) var(--space-4); color: var(--brand-ink); background: var(--brand-wash); border-left: 3px solid var(--brand-ink); border-radius: var(--radius-control); font-weight: 700; }
.actions { display: flex; flex-wrap: wrap; gap: var(--space-3); }

.done { display: grid; justify-items: center; gap: var(--space-3); padding: var(--space-7) var(--space-5); text-align: center; }
.done p { margin: 0; max-width: 32rem; color: var(--ink-soft); }
.done-icon { width: 3.5rem; height: 3.5rem; fill: none; stroke: var(--brand); stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; animation: stamp-in 400ms var(--ease-spring) both; }
.done-code { font-family: var(--font-mono); font-weight: 700; font-size: clamp(2rem, 1.4rem + 3vw, 3rem); letter-spacing: 0.1em; animation: rise-in var(--dur-slow) var(--ease-out) 120ms both; }

.swap-enter-active,
.swap-leave-active { transition: opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-out); }
.swap-enter-from { opacity: 0; transform: translateY(10px); }
.swap-leave-to { opacity: 0; transform: translateY(-6px); }

.row-enter-active { transition: opacity var(--dur) var(--ease-out), transform var(--dur) var(--ease-spring); }
.row-leave-active { transition: opacity var(--dur-fast); }
.row-enter-from { opacity: 0; transform: scale(0.94); }
.row-leave-to { opacity: 0; }

/* Điện thoại 360px: nút chính trải hết chiều ngang để dễ bấm */
@media (max-width: 30rem) {
  .actions .btn { flex: 1 1 100%; }
  .inline { flex-wrap: wrap; }
  .inline .btn { flex: 1 1 100%; }
}
</style>
