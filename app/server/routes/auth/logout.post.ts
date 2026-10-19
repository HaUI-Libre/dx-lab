// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

import * as oidc from 'openid-client'

// Xoá phiên ở app rồi chuyển sang Keycloak để kết thúc phiên SSO.
// Dùng POST để trang khác không đăng xuất người dùng bằng một thẻ <img>.
export default defineEventHandler(async (event) => {
  const tokens = await endSession(event)
  const url = oidc.buildEndSessionUrl(await getOidcConfig(), {
    post_logout_redirect_uri: `${useRuntimeConfig().appUrl}/`,
    ...(tokens?.idToken ? { id_token_hint: tokens.idToken } : {}),
  })
  return sendRedirect(event, url.href, 303)
})
