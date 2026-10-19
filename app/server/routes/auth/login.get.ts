// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

import * as oidc from 'openid-client'

// Chuyển người dùng sang trang đăng nhập Keycloak (authorization code + PKCE S256)
export default defineEventHandler(async (event) => {
  const config = await getOidcConfig()
  const codeVerifier = oidc.randomPKCECodeVerifier()
  const state = oidc.randomState()
  const nonce = oidc.randomNonce()

  const session = await appSession(event)
  await session.update({ pending: { state, nonce, codeVerifier } })

  const url = oidc.buildAuthorizationUrl(config, {
    redirect_uri: callbackUrl(),
    scope: 'openid profile email',
    code_challenge: await oidc.calculatePKCECodeChallenge(codeVerifier),
    code_challenge_method: 'S256',
    state,
    nonce,
  })
  return sendRedirect(event, url.href)
})
