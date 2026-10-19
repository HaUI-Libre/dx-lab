// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Dùng cho healthcheck của compose; không phụ thuộc Keycloak để app vẫn lên
// được và hiện thông báo lỗi khi Keycloak chưa sẵn sàng.
export default defineEventHandler(() => ({ status: 'ok' }))
