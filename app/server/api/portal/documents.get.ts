// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

import { DEFAULT_GUIDES, type GuideDocument } from '../../utils/portal'
import { getAccessToken } from '../../utils/oidc'

let hasSeededSeaweed = false

async function seedDefaultGuides(gatewayUrl: string, token: string) {
  if (hasSeededSeaweed) return
  try {
    for (const guide of DEFAULT_GUIDES) {
      const url = new URL(`/api/files/${guide.filePath}`, gatewayUrl)
      // Kiểm tra tệp đã có chưa
      const checkRes = await fetch(url.href, {
        method: 'HEAD',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!checkRes.ok && checkRes.status === 404) {
        // Tải nội dung mặc định lên SeaweedFS qua gateway
        await fetch(url.href, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'text/markdown; charset=utf-8',
          },
          body: guide.content,
        })
      }
    }
    hasSeededSeaweed = true
  }
  catch (err) {
    console.warn('Khởi tạo tệp mẫu SeaweedFS:', (err as Error).message)
  }
}

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

  // Tự động bảo đảm các tài liệu mẫu đã được đồng bộ vào SeaweedFS
  await seedDefaultGuides(gatewayUrl, token)

  // Đọc thêm tài liệu do người dùng tải lên được lưu trong storage
  const customDocs = (await useStorage<GuideDocument[]>('dxlab-portal').getItem('custom-docs')) ?? []

  const allDocs = [...DEFAULT_GUIDES, ...customDocs]

  // Lọc tài liệu theo quyền của vai trò hiện tại
  const isSuper = userRoles.includes('ROLE_ADMIN')
  const visibleDocs = allDocs.filter((doc) => {
    if (isSuper) return true
    return doc.allowedRoles.some(r => userRoles.includes(r))
  })

  // Không trả trường content dài trong danh sách tóm tắt
  return visibleDocs.map(({ content, ...rest }) => rest)
})
