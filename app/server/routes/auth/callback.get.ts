// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

import * as oidc from 'openid-client'

// Keycloak chuyển về đây kèm code; server đổi code lấy token qua backchannel
export default defineEventHandler(async (event) => {
  const session = await appSession(event)
  const pending = session.data.pending
  if (!pending) {
    // Mở lại link callback cũ hoặc cookie đã mất: bắt đầu đăng nhập lại
    return sendRedirect(event, '/auth/login')
  }

  // Ghép lại URL đúng như trình duyệt đã gọi để thư viện so redirect_uri và state
  const current = new URL(callbackUrl())
  current.search = getRequestURL(event).search

  try {
    const tokens = await oidc.authorizationCodeGrant(await getOidcConfig(), current, {
      pkceCodeVerifier: pending.codeVerifier,
      expectedState: pending.state,
      expectedNonce: pending.nonce,
      idTokenExpected: true,
    })
    await startSession(event, toStoredTokens(tokens))
  }
  catch (err) {
    await session.update({ pending: undefined })
    console.warn('Đăng nhập thất bại:', (err as Error).message)
    return sendRedirect(event, '/?loi=dang-nhap')
  }
  return sendRedirect(event, '/')
})
