// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

import { randomUUID } from 'node:crypto'
import {
  DEFAULT_GUIDES,
  MANIFEST_FILE_PATH,
  getMetaFilePath,
  type GuideDocument,
} from '../../utils/portal'
import { getAccessToken } from '../../utils/oidc'

interface CreateDocumentPayload {
  title: string
  description: string
  category: 'GENERAL' | 'STUDENT' | 'TECHNICIAN' | 'MANAGER' | 'ADMIN'
  fileName: string
  filePath: string
  fileSize: string
  allowedRoles: string[]
  content?: string
}

const CATEGORY_LABELS: Record<string, string> = {
  GENERAL: 'Nội quy Chung',
  STUDENT: 'Hướng dẫn Sinh viên',
  TECHNICIAN: 'Kỹ thuật viên',
  MANAGER: 'Trưởng phòng Lab',
  ADMIN: 'Quản trị viên',
}

export default defineEventHandler(async (event) => {
  const token = await getAccessToken(event)
  if (!token) {
    throw createError({ statusCode: 401, message: 'Chưa đăng nhập' })
  }

  const gatewayUrl = useRuntimeConfig().gatewayUrl

  // Lấy vai trò và tên người dùng qua /api/me
  let username = 'Người dùng'
  let userRoles: string[] = []
  try {
    const meRes = await fetch(new URL('/api/me', gatewayUrl).href, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (meRes.ok) {
      const me = (await meRes.json()) as { username?: string, name?: string, roles?: string[] }
      username = me.name || me.username || 'Người dùng'
      userRoles = me.roles ?? []
    }
  }
  catch {
    throw createError({ statusCode: 503, message: 'Không thể xác thực quyền hạn người dùng' })
  }

  // Chỉ Kỹ thuật viên, Quản lý hoặc Admin mới được xuất bản tài liệu hướng dẫn
  const canPublish = userRoles.some(r =>
    ['ROLE_TECHNICIAN', 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'].includes(r),
  )
  if (!canPublish) {
    throw createError({ statusCode: 403, message: 'Chỉ Kỹ thuật viên, Trưởng phòng lab hoặc Quản trị viên mới có quyền đăng tài liệu' })
  }

  const body = await readBody<CreateDocumentPayload>(event)
  if (!body.title?.trim() || !body.filePath?.trim() || !body.fileName?.trim()) {
    throw createError({ statusCode: 400, message: 'Thiếu thông tin bắt buộc của tài liệu' })
  }

  const newDoc: GuideDocument = {
    id: `custom-${randomUUID().slice(0, 8)}`,
    title: body.title.trim(),
    description: body.description?.trim() || 'Tài liệu hướng dẫn bổ sung.',
    category: body.category || 'GENERAL',
    categoryLabel: CATEGORY_LABELS[body.category] || 'Tài liệu hướng dẫn',
    fileName: body.fileName.trim(),
    filePath: body.filePath.trim(),
    fileSize: body.fileSize || '1.0 KB',
    fileType: body.fileName.endsWith('.md') ? 'markdown' : 'text',
    allowedRoles: body.allowedRoles?.length
      ? body.allowedRoles
      : ['ROLE_STUDENT', 'ROLE_TECHNICIAN', 'ROLE_LAB_MANAGER', 'ROLE_ADMIN'],
    updatedAt: new Date().toISOString().slice(0, 10),
    uploadedBy: username,
    content: body.content || `# ${body.title.trim()}\n\n${body.description?.trim() || ''}\n`,
    isCustom: true,
  }

  const sidecarPath = getMetaFilePath(newDoc.filePath)

  // 1. Lưu nội dung tệp vào SeaweedFS nếu chưa có
  try {
    const contentUrl = new URL(`/api/files/${newDoc.filePath}`, gatewayUrl)
    await fetch(contentUrl.href, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'text/markdown; charset=utf-8',
      },
      body: newDoc.content,
    })
  }
  catch (err) {
    console.warn('Lưu nội dung tệp vào SeaweedFS:', (err as Error).message)
  }

  // 2. Lưu metadata sidecar (<filePath>.meta.json) bền vững vào SeaweedFS
  const metaPayload: GuideDocument = {
    ...newDoc,
    content: '',
  }
  try {
    const sidecarUrl = new URL(`/api/files/${sidecarPath}`, gatewayUrl)
    const sidecarRes = await fetch(sidecarUrl.href, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json; charset=utf-8',
      },
      body: JSON.stringify(metaPayload, null, 2),
    })
    if (!sidecarRes.ok && sidecarRes.status !== 201 && sidecarRes.status !== 204) {
      console.warn('Lỗi ghi sidecar metadata:', sidecarRes.status)
    }
  }
  catch (err) {
    throw createError({ statusCode: 502, message: `Lỗi ghi sidecar metadata vào SeaweedFS: ${(err as Error).message}` })
  }

  // 3. Cập nhật danh sách manifest portal/manifest.json trong SeaweedFS
  try {
    const manifestUrl = new URL(`/api/files/${MANIFEST_FILE_PATH}`, gatewayUrl)
    let manifestList: string[] = []
    const manifestRes = await fetch(manifestUrl.href, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (manifestRes.ok) {
      manifestList = (await manifestRes.json()) as string[]
      if (!Array.isArray(manifestList)) manifestList = []
    }
    else {
      manifestList = DEFAULT_GUIDES.map(g => getMetaFilePath(g.filePath))
    }

    if (!manifestList.includes(sidecarPath)) {
      manifestList.push(sidecarPath)
    }

    await fetch(manifestUrl.href, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json; charset=utf-8',
      },
      body: JSON.stringify(manifestList, null, 2),
    })
  }
  catch (err) {
    console.warn('Cập nhật manifest SeaweedFS:', (err as Error).message)
  }

  return newDoc
})
