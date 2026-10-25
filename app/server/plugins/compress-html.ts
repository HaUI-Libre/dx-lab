// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Nén HTML do server render theo Accept-Encoding (brotli, rồi gzip). JS và CSS tĩnh đã được
// nén sẵn lúc build (nitro.compressPublicAssets); HTML của /tickets nhúng cả danh sách phiếu
// nên chưa nén là phần nặng nhất trên mạng chậm.
// Chỉ chạy ở hook render:response của trang Nuxt: proxy /gw (kể cả SSE) ghi thẳng ra
// response, không đi qua đây. Vẫn kiểm tra kiểu nội dung để không bao giờ nén event-stream.
import { brotliCompressSync, constants, gzipSync } from 'node:zlib'

const MIN_BYTES = 1024

export default defineNitroPlugin((nitroApp) => {
  nitroApp.hooks.hook('render:response', (response, { event }) => {
    const headers = (response.headers ??= {}) as Record<string, string>
    const type = String(headers['content-type'] ?? headers['Content-Type'] ?? 'text/html')
    if (!type.includes('text/html') || type.includes('text/event-stream')) return
    if (headers['content-encoding'] || headers['Content-Encoding']) return
    if (typeof response.body !== 'string') return
    const raw = Buffer.from(response.body)
    if (raw.length < MIN_BYTES) return

    // Cache trung gian phải tách bản nén và bản không nén
    headers.vary = headers.vary ? `${headers.vary}, Accept-Encoding` : 'Accept-Encoding'
    const accept = getRequestHeader(event, 'accept-encoding') ?? ''
    if (/\bbr\b/.test(accept)) {
      // Mức 5: đủ nhỏ, chỉ tốn vài mili giây cho trang ~100 KB
      response.body = brotliCompressSync(raw, { params: { [constants.BROTLI_PARAM_QUALITY]: 5 } }) as never
      headers['content-encoding'] = 'br'
    }
    else if (/\bgzip\b/.test(accept)) {
      response.body = gzipSync(raw, { level: 6 }) as never
      headers['content-encoding'] = 'gzip'
    }
    else {
      return
    }
    headers['content-length'] = String((response.body as unknown as Buffer).length)
  })
})
