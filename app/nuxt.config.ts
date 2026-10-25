// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Mọi giá trị trong runtimeConfig được ghi đè lúc chạy bằng biến NUXT_*,
// docker-compose.yml lấy chúng từ .env. Giá trị dưới đây dùng khi chạy
// `npm run dev` trên máy host, cạnh stack `make up`.
export default defineNuxtConfig({
  compatibilityDate: '2026-08-01',
  devtools: { enabled: false },
  telemetry: false,
  // Phông tự host để demo chạy được khi không có mạng; fonts.css chỉ khai báo subset dùng tới
  css: [
    '~/assets/css/fonts.css',
    '~/assets/css/tokens.css',
    '~/assets/css/base.css',
  ],
  app: {
    head: {
      htmlAttrs: { lang: 'vi' },
      title: 'DX-Helpdesk',
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
      // Đặt chế độ màu đã lưu trước khi trang vẽ để không chớp màu (xem composables/useTheme.ts)
      script: [{
        innerHTML: "try{var t=localStorage.getItem('dxlab-theme');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t}catch(e){}",
        tagPosition: 'head',
      }],
    },
    // Chuyển trang: mờ dần và trượt ngắn, định nghĩa ở assets/css/base.css
    pageTransition: { name: 'page', mode: 'out-in' },
  },
  // Nén sẵn JS, CSS (brotli, gzip); Nitro trả bản nén theo Accept-Encoding
  nitro: { compressPublicAssets: true },
  runtimeConfig: {
    // Địa chỉ ứng dụng mà trình duyệt thấy; dùng để tạo redirect_uri
    appUrl: 'http://localhost:3000',
    // Server Nuxt đọc discovery và đổi code lấy token qua địa chỉ này
    oidcIssuerInternal: 'http://localhost:8080/realms/dxlab',
    oidcClientId: 'dxlab-app',
    oidcClientSecret: '',
    // Mọi lời gọi API từ ứng dụng đi qua APISIX
    gatewayUrl: 'http://localhost:9080',
    // Khoá mã hoá cookie phiên, ít nhất 32 ký tự
    sessionPassword: '',
  },
})
