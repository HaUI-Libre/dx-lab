// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

import { CAMPUS_UNITS, ROLE_GROUPS } from '../../utils/portal'
import { getAccessToken } from '../../utils/oidc'

export default defineEventHandler(async (event) => {
  const token = await getAccessToken(event)
  if (!token) {
    throw createError({ statusCode: 401, message: 'Chưa đăng nhập' })
  }

  const gatewayUrl = useRuntimeConfig().gatewayUrl

  let currentCoSo: string | undefined
  let currentRoles: string[] = []
  try {
    const meRes = await fetch(new URL('/api/me', gatewayUrl).href, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (meRes.ok) {
      const me = (await meRes.json()) as { co_so?: string, roles?: string[] }
      currentCoSo = me.co_so
      currentRoles = me.roles ?? []
    }
  }
  catch {
    // Không kết nối được me, vẫn trả danh sách nhóm
  }

  return {
    campusUnits: CAMPUS_UNITS,
    roleGroups: ROLE_GROUPS,
    userContext: {
      currentCoSo,
      currentRoles,
      matchedUnit: CAMPUS_UNITS.find(u => u.code === currentCoSo),
      matchedRoles: ROLE_GROUPS.filter(g => currentRoles.includes(g.role)),
    },
  }
})
