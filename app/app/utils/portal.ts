// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

export interface GuideDoc {
  id: string
  title: string
  description: string
  category: string
  categoryLabel: string
  fileName: string
  filePath: string
  fileSize: string
  fileType: string
  allowedRoles: string[]
  updatedAt: string
  uploadedBy?: string
  isCustom?: boolean
}

export interface CampusUnit {
  id: string
  code: string
  name: string
  location: string
  hotline: string
  email: string
  scope: string
  manager: string
  technicians: string[]
}

export interface RoleGroup {
  id: string
  role: string
  roleLabel: string
  name: string
  description: string
  duties: string[]
  workflowPermissions: string[]
}

export interface GroupsResponse {
  campusUnits: CampusUnit[]
  roleGroups: RoleGroup[]
  userContext: {
    currentCoSo?: string
    currentRoles: string[]
    matchedUnit?: CampusUnit
    matchedRoles: RoleGroup[]
  }
}

export const ROLE_LABELS: Record<string, string> = {
  ROLE_STUDENT: 'Sinh viên',
  ROLE_TECHNICIAN: 'Kỹ thuật viên',
  ROLE_LAB_MANAGER: 'Trưởng phòng lab',
  ROLE_ADMIN: 'Quản trị hệ thống',
}

export const CAMPUS_LABELS: Record<string, string> = {
  CS1: 'Cơ sở 1 (Khu A & B – Bắc Từ Liêm)',
  CS2: 'Cơ sở 2 (Tây Tựu – Bắc Từ Liêm)',
  CS3: 'Cơ sở 3 (Phủ Lý – Hà Nam)',
}
