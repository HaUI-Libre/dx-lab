// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Tài khoản demo trong realm (core/identity/realm-dxlab.json). Chỉ dùng để điền sẵn tên
// đăng nhập trên trang Keycloak qua login_hint; mật khẩu không bao giờ đi qua ứng dụng.
export const DEMO_USERS = [
  'sinhvien', 'kythuatvien', 'truongphong', 'quantri',
  'sinhvien_cs2', 'kythuatvien_cs2', 'truongphong_cs2',
  'sinhvien_cs3', 'kythuatvien_cs3', 'truongphong_cs3',
] as const

// Tên lạ hoặc cờ tắt thì trả null, luồng đăng nhập giữ nguyên như không có gợi ý
export function demoLoginHint(value: unknown): string | null {
  if (!useRuntimeConfig().public.demoLogin) return null
  return typeof value === 'string' && (DEMO_USERS as readonly string[]).includes(value) ? value : null
}
