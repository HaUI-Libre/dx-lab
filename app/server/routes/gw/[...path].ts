// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Chuyển tiếp /gw/api/** sang APISIX, gắn Bearer token của phiên đăng nhập.
// Phân quyền vẫn do gateway và dịch vụ phía sau quyết định; ở đây chỉ gắn token.
export default defineEventHandler(async (event) => {
  const rawPath = event.context.params?.path ?? ''
  // Chuẩn hoá đường dẫn trước khi kiểm tra, chống path traversal qua .. hoặc %2e
  const target = new URL(`/${rawPath}`, useRuntimeConfig().gatewayUrl)
  if (!target.pathname.startsWith('/api/')) {
    throw createError({ statusCode: 404, message: 'Chỉ chuyển tiếp /gw/api/**' })
  }

  const token = await getAccessToken(event)
  if (!token) {
    // A browser User-Agent would render the Nuxt error page and redirect to
    // /auth/login; API callers need a stable JSON 401 instead.
    setResponseStatus(event, 401)
    return { error: true, message: 'Chưa đăng nhập' }
  }

  target.search = getRequestURL(event).search

  // Không dùng proxyRequest vì hàm đó luôn chép cookie của trình duyệt sang;
  // cookie phiên của app không được đi tới gateway và dịch vụ phía sau.
  const headers = getProxyRequestHeaders(event)
  delete headers.cookie
  headers.authorization = `Bearer ${token}`

  // Thân request (tệp đính kèm tới 20 MB) được stream thẳng, không đọc vào bộ nhớ
  const hasBody = event.method !== 'GET' && event.method !== 'HEAD'
  return sendProxy(event, target.href, {
    fetchOptions: {
      method: event.method,
      headers,
      ...(hasBody ? { body: getRequestWebStream(event), duplex: 'half' } : {}),
    },
  })
})
