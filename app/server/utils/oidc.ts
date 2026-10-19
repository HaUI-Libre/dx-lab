// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Đăng nhập theo mô hình BFF: server Nuxt chạy luồng authorization code + PKCE
// với client confidential `dxlab-app`, giữ token ở phía server. Trình duyệt chỉ
// có cookie phiên httpOnly chứa mã phiên, không bao giờ thấy token.

import { randomUUID } from 'node:crypto'
import type { H3Event } from 'h3'
import * as oidc from 'openid-client'

export interface StoredTokens {
  accessToken: string
  refreshToken?: string
  idToken?: string
  // Mốc hết hạn của access token, tính bằng mili giây
  expiresAt: number
}

interface SessionData {
  sid?: string
  // Chỉ có trong lúc chờ Keycloak chuyển về /auth/callback
  pending?: { state: string, nonce: string, codeVerifier: string }
}

// Làm mới token sớm hơn hạn một chút để request không hết hạn giữa đường
const REFRESH_MARGIN_MS = 30_000

let configPromise: Promise<oidc.Configuration> | undefined

// Discovery đọc qua địa chỉ nội bộ (keycloak:8080 trong compose). Keycloak ghim
// issuer là http://localhost:8080 và vẫn trả token endpoint nội bộ, nên không
// dùng oidc.discovery() vì hàm đó đòi issuer trùng URL vừa gọi.
export function getOidcConfig(): Promise<oidc.Configuration> {
  configPromise ??= (async () => {
    const rc = useRuntimeConfig()
    const res = await fetch(`${rc.oidcIssuerInternal}/.well-known/openid-configuration`)
    if (!res.ok) {
      throw new Error(`Không đọc được OIDC discovery: HTTP ${res.status}`)
    }
    const metadata = (await res.json()) as oidc.ServerMetadata
    const config = new oidc.Configuration(metadata, rc.oidcClientId, rc.oidcClientSecret)
    if (metadata.token_endpoint?.startsWith('http://')) {
      // Lab chạy HTTP trong mạng compose (Keycloak ở chế độ start-dev)
      oidc.allowInsecureRequests(config)
    }
    return config
  })().catch((err) => {
    // Cho phép thử lại ở request sau, ví dụ khi Keycloak khởi động chậm hơn app
    configPromise = undefined
    throw err
  })
  return configPromise
}

export function callbackUrl(): string {
  return `${useRuntimeConfig().appUrl}/auth/callback`
}

export function appSession(event: H3Event) {
  const password = useRuntimeConfig().sessionPassword
  if (!password || password.length < 32) {
    throw createError({ statusCode: 500, message: 'NUXT_SESSION_PASSWORD phải có ít nhất 32 ký tự' })
  }
  return useSession<SessionData>(event, {
    name: 'dxlab_session',
    password,
    maxAge: 8 * 60 * 60,
    cookie: {
      httpOnly: true,
      sameSite: 'lax',
      secure: useRuntimeConfig().appUrl.startsWith('https://'),
      path: '/',
    },
  })
}

// Token lưu trong bộ nhớ server, khoá theo mã phiên. Khởi động lại container
// thì người dùng đăng nhập lại; đủ cho lab và tránh cookie vượt 4 KB.
function tokenStore() {
  return useStorage<StoredTokens>('dxlab-sessions')
}

export function toStoredTokens(tokens: oidc.TokenEndpointResponse): StoredTokens {
  return {
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
    idToken: tokens.id_token,
    expiresAt: Date.now() + (tokens.expires_in ?? 60) * 1000,
  }
}

export async function startSession(event: H3Event, tokens: StoredTokens): Promise<void> {
  const session = await appSession(event)
  const sid = randomUUID()
  await tokenStore().setItem(sid, tokens)
  await session.update({ sid, pending: undefined })
}

export async function readTokens(event: H3Event): Promise<StoredTokens | null> {
  const { data } = await appSession(event)
  return data.sid ? await tokenStore().getItem(data.sid) : null
}

export async function endSession(event: H3Event): Promise<StoredTokens | null> {
  const session = await appSession(event)
  const sid = session.data.sid
  const tokens = sid ? await tokenStore().getItem(sid) : null
  if (sid) await tokenStore().removeItem(sid)
  await session.clear()
  return tokens
}

// Trả access token còn hạn, tự làm mới bằng refresh token khi sắp hết hạn.
// Trả null khi chưa đăng nhập hoặc phiên Keycloak đã hết.
export async function getAccessToken(event: H3Event): Promise<string | null> {
  const session = await appSession(event)
  const sid = session.data.sid
  if (!sid) return null
  const tokens = await tokenStore().getItem(sid)
  if (!tokens) return null
  if (tokens.expiresAt - REFRESH_MARGIN_MS > Date.now()) return tokens.accessToken
  if (!tokens.refreshToken) {
    await endSession(event)
    return null
  }
  try {
    const refreshed = await oidc.refreshTokenGrant(await getOidcConfig(), tokens.refreshToken)
    const next = toStoredTokens(refreshed)
    // Keycloak có thể không trả id_token mới; giữ bản cũ để đăng xuất được
    next.idToken ??= tokens.idToken
    next.refreshToken ??= tokens.refreshToken
    await tokenStore().setItem(sid, next)
    return next.accessToken
  }
  catch (err) {
    console.warn('Làm mới token thất bại, kết thúc phiên:', (err as Error).message)
    await endSession(event)
    return null
  }
}
