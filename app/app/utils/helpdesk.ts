// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

// Kiểu dữ liệu và nhãn hiển thị dùng chung cho các trang ticket. Mọi lời gọi đi qua
// /gw/api/** của server Nuxt rồi tới APISIX; quyền do Data API và gateway quyết định.

export interface Me {
  sub: string
  username: string
  name?: string
  email?: string
  roles: string[]
  co_so?: string
}

export interface Ticket {
  id: string
  title: string
  description: string
  category: string | null
  priority: string | null
  status: string
  location_id: number | null
  asset_id: number | null
  co_so: string | null
  created_by: string
  assigned_to: string | null
  resolution_summary: string | null
  rejection_reason: string | null
  satisfaction_rating: number | null
  submitted_at: string | null
  resolved_at: string | null
  closed_at: string | null
  created_at: string
  updated_at: string
}

export interface TicketEvent {
  id: number
  action: string
  actor_sub: string
  from_status: string | null
  to_status: string | null
  details: Record<string, unknown>
  occurred_at: string
}

export interface Attachment {
  id: string
  storage_key: string
  file_name: string
  content_type: string
  size_bytes: number
  created_at: string
}

export interface SiteLocation {
  location_id: number
  code: string
  co_so: string
}

export interface Technician {
  sub: string
  username: string
  name: string
  co_so: string
}

// Hình dạng thiết bị mà giao diện chờ từ dịch vụ tích hợp tài sản (#72)
export interface Asset {
  id: number
  asset_tag: string
  name?: string
  location_id?: number | null
  location?: string | null
  co_so?: string | null
}

// Hình dạng thống kê giao diện chờ từ GET /api/data/stats (openapi.yaml TicketStats, #22);
// by_co_so và reopen_count là phần #22 thêm theo đầu ra của Issue
export interface TicketStats {
  total: number
  by_status: Record<string, number>
  by_category: Record<string, number>
  by_co_so?: Record<string, number>
  average_resolution_hours: number | null
  overdue_count: number
  reopen_count?: number | null
}

// Hình dạng gợi ý giao diện chờ từ dịch vụ phân loại POST /api/ai/classify (#28, #30, #31)
export interface Suggestion {
  category: string
  priority: string
  keywords?: string[]
  source?: 'model' | 'rules' | string
  confidence?: number | null
}

export const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Bản nháp',
  SUBMITTED: 'Chờ tiếp nhận',
  ASSIGNED: 'Đã phân công',
  IN_PROGRESS: 'Đang xử lý',
  RESOLVED: 'Chờ nghiệm thu',
  CLOSED: 'Đã đóng',
  REJECTED: 'Bị từ chối',
}

export const CATEGORY_LABELS: Record<string, string> = {
  HARDWARE: 'Phần cứng',
  SOFTWARE_ENVIRONMENT: 'Phần mềm và môi trường',
  NETWORK_ACCOUNT: 'Mạng và tài khoản',
  LAB_ASSET: 'Tài sản và đặt phòng',
}

export const PRIORITY_LABELS: Record<string, string> = {
  URGENT: 'Khẩn cấp',
  HIGH: 'Cao',
  MEDIUM: 'Trung bình',
  LOW: 'Thấp',
}

export const EVENT_LABELS: Record<string, string> = {
  CREATE_DRAFT: 'Tạo bản nháp',
  EDIT: 'Sửa bản nháp',
  DELETE: 'Xoá bản nháp',
  ATTACH: 'Đính kèm tệp',
  SUBMIT: 'Gửi yêu cầu',
  ACCEPT: 'Tiếp nhận',
  REJECT: 'Từ chối',
  ASSIGN: 'Phân công',
  START_PROGRESS: 'Kỹ thuật viên nhận việc',
  RESOLVE: 'Hoàn thành, lập biên bản',
  REOPEN: 'Mở lại',
  CLOSE: 'Nghiệm thu và đóng',
  RATE: 'Đánh giá',
  ASSET_STATUS_UPDATE_PENDING: 'Chờ cập nhật trạng thái tài sản',
  ASSET_STATUS_UPDATE_QUEUED: 'Đã chuyển cập nhật tài sản vào hàng đợi',
  ASSET_STATUS_UPDATE_SUCCEEDED: 'Đã cập nhật trạng thái tài sản',
  ASSET_STATUS_UPDATE_FAILED: 'Chưa cập nhật được trạng thái tài sản',
}

export function hasRole(me: Me | null | undefined, ...roles: string[]) {
  return !!me && roles.some(r => me.roles.includes(r))
}

export function isManagerOf(me: Me | null | undefined, ticket: Ticket) {
  return hasRole(me, 'ROLE_ADMIN') || (hasRole(me, 'ROLE_LAB_MANAGER') && me!.co_so === ticket.co_so)
}

export function formatTime(value: string | null | undefined) {
  if (!value) return ''
  return new Date(value).toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Asia/Ho_Chi_Minh' })
}

// Gọi Data API qua gateway; lỗi trả về câu báo đọc được thay vì đối tượng lỗi
export async function dataApi<T>(path: string, options: Parameters<typeof $fetch>[1] = {}) {
  try {
    return await $fetch<T>(`/gw/api/data${path}`, options as never)
  }
  catch (error) {
    throw new Error(errorMessage(error))
  }
}

export function errorMessage(error: unknown) {
  const e = error as { data?: { detail?: unknown, message?: string, error?: string }, statusCode?: number, message?: string }
  const detail = e?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return 'Dữ liệu chưa hợp lệ, kiểm tra lại các trường bắt buộc'
  return e?.data?.message || e?.data?.error || e?.message || `Lỗi ${e?.statusCode ?? 'không rõ'}`
}

// Mã phiếu hiển thị: 8 ký tự đầu của UUID, in hoa, đọc được qua điện thoại.
// Chỉ để hiển thị; mọi lời gọi API vẫn dùng UUID đầy đủ.
export function ticketCode(id: string) {
  return id.slice(0, 8).toUpperCase()
}
