// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

import { DEFAULT_GUIDES, MANIFEST_FILE_PATH, type GuideDocument } from '../../utils/portal'
import { getAccessToken } from '../../utils/oidc'

export default defineEventHandler(async (event) => {
  const token = await getAccessToken(event)
  if (!token) {
    throw createError({ statusCode: 401, message: 'Chưa đăng nhập' })
  }

  const gatewayUrl = useRuntimeConfig().gatewayUrl

  // Lấy thông tin vai trò người dùng từ /api/me qua APISIX
  let userRoles: string[] = []
  try {
    const meRes = await fetch(new URL('/api/me', gatewayUrl).href, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (meRes.ok) {
      const me = (await meRes.json()) as { roles?: string[] }
      userRoles = me.roles ?? []
    }
  }
  catch {
    userRoles = []
  }

  // Đọc danh mục tệp từ manifest và các sidecar .meta.json trong SeaweedFS
  let docs: GuideDocument[] = []
  try {
    const manifestUrl = new URL(`/api/files/${MANIFEST_FILE_PATH}`, gatewayUrl)
    const manifestRes = await fetch(manifestUrl.href, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (manifestRes.ok) {
      const metaPaths = (await manifestRes.json()) as string[]
      if (Array.isArray(metaPaths) && metaPaths.length > 0) {
        const metaPromises = metaPaths.map(async (metaPath) => {
          try {
            const metaUrl = new URL(`/api/files/${metaPath}`, gatewayUrl)
            const metaRes = await fetch(metaUrl.href, {
              headers: { Authorization: `Bearer ${token}` },
            })
            if (metaRes.ok) {
              return (await metaRes.json()) as GuideDocument
            }
          }
          catch {
            // Bỏ qua lỗi đọc từng tệp metadata riêng lẻ
          }
          return null
        })
        const results = await Promise.all(metaPromises)
        docs = results.filter((d): d is GuideDocument => d !== null)
      }
    }
  }
  catch (err) {
    console.warn('Lỗi đọc manifest SeaweedFS:', (err as Error).message)
  }

  // Nếu SeaweedFS chưa có manifest (chưa seed), dùng danh sách mặc định để không gián đoạn UI
  if (docs.length === 0) {
    docs = [...DEFAULT_GUIDES]
  }

  // Lọc tài liệu theo quyền của vai trò hiện tại
  const isSuper = userRoles.includes('ROLE_ADMIN')
  const visibleDocs = docs.filter((doc) => {
    if (isSuper) return true
    return doc.allowedRoles?.some(r => userRoles.includes(r))
  })

  // Không trả trường content dài trong danh sách tóm tắt
  return visibleDocs.map(({ content, ...rest }) => rest)
})
