-- SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
-- SPDX-License-Identifier: Apache-2.0
--
-- Dữ liệu mẫu ticket, attachments và events nạp vào cơ sở dữ liệu dxdata
-- Phục vụ demo quy trình BPMN, định tuyến 3 cơ sở (CS1, CS2, CS3), dashboard và kiểm thử API.

BEGIN;

-- Dữ liệu mẫu dùng ID cố định và ON CONFLICT DO UPDATE để nạp lặp an toàn, đồng bộ UUID người dùng

-- ============================================================================
-- 1. TICKETS
-- ============================================================================

-- TICKET 1 (CS1): CLOSED - Hoàn thành sửa nguồn máy tính thực hành C401
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id, resolution_summary, satisfaction_rating,
    sla_due_at, submitted_at, resolved_at, closed_at, created_at, updated_at
) VALUES (
    'a1111111-1111-4111-8111-111111111101',
    'Máy PC-04 phòng C401 không lên nguồn',
    'Khi bật nút nguồn máy không có tín hiệu đèn, quạt nguồn không quay, có mùi khét nhẹ.',
    'HARDWARE', 'HIGH', 'CLOSED',
    'CS1-C-PM401', NULL, 'CS1', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk',
    NULL, 'Đã thay bộ nguồn ATX 500W mới và vệ sinh chân RAM. Máy khởi động bình thường.', 5,
    '2026-10-10 18:00:00+07', '2026-10-10 08:30:00+07', '2026-10-10 15:45:00+07', '2026-10-10 16:30:00+07',
    '2026-10-10 08:15:00+07', '2026-10-10 16:30:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 2 (CS1): IN_PROGRESS - Máy thực hành hỏng RAM và nguồn (khớp nhãn "Đang sửa chữa" HAUI-CS1-PC02)
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id, resolution_summary,
    sla_due_at, submitted_at, created_at, updated_at
) VALUES (
    'a1111111-1111-4111-8111-111111111102',
    'Máy PC-02 phòng C401 lỗi màn hình xanh dump liên tục',
    'Khởi động vào Windows được 2 phút thì bị màn hình xanh MEMORY_MANAGEMENT, máy tự khởi động lại.',
    'HARDWARE', 'HIGH', 'IN_PROGRESS',
    'CS1-C-PM401', NULL, 'CS1', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk',
    NULL, NULL,
    '2026-10-18 20:00:00+07', '2026-10-17 09:00:00+07',
    '2026-10-17 08:50:00+07', '2026-10-17 10:15:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 3 (CS1): RESOLVED - Cài đặt môi trường Docker và IDE phòng C302 chờ nghiệm thu
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id, resolution_summary,
    sla_due_at, submitted_at, resolved_at, created_at, updated_at
) VALUES (
    'a1111111-1111-4111-8111-111111111103',
    'Lỗi không khởi động được Docker Desktop trên máy trạm C302',
    'Docker Desktop báo lỗi WSL 2 kernel is missing, sinh viên không làm được bài thực hành Microservices.',
    'SOFTWARE_ENVIRONMENT', 'MEDIUM', 'RESOLVED',
    'CS1-C-LAB302', NULL, 'CS1', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk',
    NULL, 'Đã cập nhật gói wsl_update_x64 và kích hoạt Hyper-V trong BIOS, Docker chạy tốt.',
    '2026-10-19 12:00:00+07', '2026-10-17 14:00:00+07', '2026-10-18 07:30:00+07',
    '2026-10-17 13:45:00+07', '2026-10-18 07:30:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 4 (CS1): ASSIGNED - Đã phân công cho kỹ thuật viên xử lý switch mạng phòng A10-502
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id,
    sla_due_at, submitted_at, created_at, updated_at
) VALUES (
    'a1111111-1111-4111-8111-111111111104',
    'Mất kết nối mạng LAN dãy máy lẻ phòng A10-502',
    '10 máy tính dãy bàn số 1 và 3 không nhận địa chỉ IP từ DHCP, đèn cổng switch nháy cam.',
    'NETWORK_ACCOUNT', 'HIGH', 'ASSIGNED',
    'CS1-A10-MANG502', NULL, 'CS1', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk',
    NULL,
    '2026-10-18 17:00:00+07', '2026-10-18 08:00:00+07',
    '2026-10-18 07:50:00+07', '2026-10-18 08:10:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 5 (CS1): SUBMITTED - Đang chờ Trưởng phòng Lab CS1 tiếp nhận / phân công
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id,
    sla_due_at, submitted_at, created_at, updated_at
) VALUES (
    'a1111111-1111-4111-8111-111111111105',
    'Máy chiếu phòng C301 mờ bóng và chớp tắt',
    'Máy chiếu Panasonic sau khi bật khoảng 5 phút thì bóng đèn tự tắt, đèn cảnh báo Temp nhấp nháy đỏ.',
    'HARDWARE', 'MEDIUM', 'SUBMITTED',
    'CS1-C-LAB301', NULL, 'CS1', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', NULL, 'dx-helpdesk',
    NULL,
    '2026-10-19 17:00:00+07', '2026-10-18 08:15:00+07',
    '2026-10-18 08:10:00+07', '2026-10-18 08:15:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 6 (CS1): DRAFT - Bản nháp của sinh viên chưa gửi
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    created_at, updated_at
) VALUES (
    'a1111111-1111-4111-8111-111111111106',
    'Bàn phím máy C401-03 bị kẹt phím Enter',
    'Phím Enter của bàn phím cơ phòng máy bị kẹt cứng, không gõ được code.',
    'HARDWARE', 'LOW', 'DRAFT',
    'CS1-C-PM401', NULL, NULL, 'e90585fa-96ac-5f81-87a3-f817cc6d4323', NULL, 'dx-helpdesk',
    '2026-10-18 08:20:00+07', '2026-10-18 08:20:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 7 (CS2): IN_PROGRESS - Máy tính CS2 lỗi card mạng (khớp nhãn "Đang sửa chữa" HAUI-CS2-PC02)
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id,
    sla_due_at, submitted_at, created_at, updated_at
) VALUES (
    'b2222222-2222-4222-8222-222222222201',
    'Máy PC-02 phòng 201 Tòa B1 CS2 gãy chân cắm LAN RJ45',
    'Cổng mạng onboard trên mainboard bị thụt chốt tiếp xúc, không nhận dây mạng.',
    'HARDWARE', 'HIGH', 'IN_PROGRESS',
    'CS2-B1-PM201', NULL, 'CS2', '2324827d-3d37-5241-997f-25b64722818d', '18685db0-c1c9-5e08-97cd-fdd20f23f6ed', 'dx-helpdesk',
    NULL,
    '2026-10-19 10:00:00+07', '2026-10-17 11:00:00+07',
    '2026-10-17 10:45:00+07', '2026-10-17 11:30:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 8 (CS2): SUBMITTED - Chờ Trưởng phòng CS2 tiếp nhận
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id,
    sla_due_at, submitted_at, created_at, updated_at
) VALUES (
    'b2222222-2222-4222-8222-222222222202',
    'Yêu cầu cấp tài khoản phần mềm đồ họa phòng Lab B2-301',
    'Lớp Đồ họa truyền thông cần kích hoạt tài khoản bản quyền Blender và Photoshop phục vụ đồ án.',
    'SOFTWARE_ENVIRONMENT', 'MEDIUM', 'SUBMITTED',
    'CS2-B2-LAB301', NULL, 'CS2', '2324827d-3d37-5241-997f-25b64722818d', NULL, 'dx-helpdesk',
    NULL,
    '2026-10-20 17:00:00+07', '2026-10-18 07:45:00+07',
    '2026-10-18 07:30:00+07', '2026-10-18 07:45:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 9 (CS2): REJECTED - Từ chối ở bước tiếp nhận kèm lý do bắt buộc
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id, rejection_reason,
    sla_due_at, submitted_at, rejected_at, created_at, updated_at
) VALUES (
    'b2222222-2222-4222-8222-222222222203',
    'Mượn phòng máy 202 Tòa B1 tối chủ nhật tự học',
    'Nhóm sinh viên xin phép mở cửa phòng máy 202 tối chủ nhật để làm bài tập nhóm.',
    'LAB_ASSET', 'LOW', 'REJECTED',
    'CS2-B1-PM202', NULL, 'CS2', '2324827d-3d37-5241-997f-25b64722818d', NULL, 'dx-helpdesk',
    NULL, 'Yêu cầu mượn phòng ngoài giờ phải có giấy xác nhận của giảng viên hướng dẫn hoặc Khoa.',
    '2026-10-17 17:00:00+07', '2026-10-16 10:00:00+07', '2026-10-16 11:20:00+07',
    '2026-10-16 09:30:00+07', '2026-10-16 11:20:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 10 (CS3): CLOSED - Thay chuột quang và vệ sinh phòng 301 Tòa H1 CS3
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id, resolution_summary, satisfaction_rating,
    sla_due_at, submitted_at, resolved_at, closed_at, created_at, updated_at
) VALUES (
    'c3333333-3333-4333-8333-333333333301',
    'Liệt phím chuột trái máy tính H1-301-01',
    'Chuột không bấm đúp được, bi lăn bị kẹt bụi bẩn.',
    'HARDWARE', 'LOW', 'CLOSED',
    'CS3-H1-PM301', NULL, 'CS3', 'a7e3965a-b5b0-5a1f-b755-8f0f9130895b', 'b8074364-5be8-55e6-9106-a68702cbde00', 'dx-helpdesk',
    NULL, 'Đã thay mới chuột quang cổng USB thương hiệu Fuhlen.', 4,
    '2026-10-15 17:00:00+07', '2026-10-14 09:00:00+07', '2026-10-14 14:00:00+07', '2026-10-14 15:00:00+07',
    '2026-10-14 08:30:00+07', '2026-10-14 15:00:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 11 (CS3): SUBMITTED - Chờ Trưởng phòng CS3 tiếp nhận
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id,
    sla_due_at, submitted_at, created_at, updated_at
) VALUES (
    'c3333333-3333-4333-8333-333333333302',
    'Máy tính phòng H1-302 không kết nối được WiFi HaUI',
    'Card WiFi không dò thấy SSID HaUI_Student, các máy khác vẫn kết nối bình thường.',
    'NETWORK_ACCOUNT', 'MEDIUM', 'SUBMITTED',
    'CS3-H1-PM302', NULL, 'CS3', 'a7e3965a-b5b0-5a1f-b755-8f0f9130895b', NULL, 'dx-helpdesk',
    NULL,
    '2026-10-19 15:00:00+07', '2026-10-18 08:00:00+07',
    '2026-10-18 07:50:00+07', '2026-10-18 08:00:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- TICKET 12 (CS1): CLOSED kèm lịch sử MỞ LẠI (REOPEN) - Rất quan trọng cho kiểm thử BPMN và Audit
INSERT INTO tickets (
    id, title, description, category, priority, status,
    location, asset_id, co_so, created_by, assigned_to, source,
    workflow_instance_id, resolution_summary, satisfaction_rating,
    sla_due_at, submitted_at, resolved_at, closed_at, created_at, updated_at
) VALUES (
    'e1111111-1111-4111-8111-111111111112',
    'Cài đặt môi trường lập trình nhúng STM32 phòng C301',
    'Máy tính thiếu bộ công cụ STM32CubeIDE và trình dịch GNU Arm Toolchain.',
    'SOFTWARE_ENVIRONMENT', 'MEDIUM', 'CLOSED',
    'CS1-C-LAB301', NULL, 'CS1', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk',
    NULL, 'Đã bổ sung đầy đủ bản quyền Keil C và nạp firmware ST-Link v2 thành công.', 5,
    '2026-10-12 17:00:00+07', '2026-10-11 08:30:00+07', '2026-10-12 10:00:00+07', '2026-10-12 11:00:00+07',
    '2026-10-11 08:00:00+07', '2026-10-12 11:00:00+07'
) ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by,
    assigned_to = EXCLUDED.assigned_to,
    co_so = EXCLUDED.co_so;

-- ============================================================================
-- 2. TICKET ATTACHMENTS (Lưu trữ metadata SeaweedFS)
-- ============================================================================

INSERT INTO ticket_attachments (
    id, ticket_id, storage_key, file_name, content_type, size_bytes, source, created_by, created_at
) VALUES
(
    'f1111111-1111-4111-8111-111111111101',
    'a1111111-1111-4111-8111-111111111102',
    'tickets/2026/10/a1111111-02/bsod_screen.png',
    'bsod_screen.png',
    'image/png',
    184200,
    'dx-helpdesk',
    'e90585fa-96ac-5f81-87a3-f817cc6d4323',
    '2026-10-17 08:52:00+07'
),
(
    'f1111111-1111-4111-8111-111111111102',
    'a1111111-1111-4111-8111-111111111101',
    'tickets/2026/10/a1111111-01/bien_ban_thay_nguon.pdf',
    'bien_ban_thay_nguon.pdf',
    'application/pdf',
    425600,
    'dx-helpdesk',
    '9f19d880-973b-592b-bdb3-a354ac11cd6a',
    '2026-10-10 15:40:00+07'
),
(
    'f1111111-1111-4111-8111-111111111103',
    'b2222222-2222-4222-8222-222222222201',
    'tickets/2026/10/b2222222-01/cong_rj45_hong.jpg',
    'cong_rj45_hong.jpg',
    'image/jpeg',
    312450,
    'dx-helpdesk',
    '2324827d-3d37-5241-997f-25b64722818d',
    '2026-10-17 10:48:00+07'
)
ON CONFLICT (id) DO UPDATE SET
    created_by = EXCLUDED.created_by;

-- ============================================================================
-- 3. TICKET EVENTS (Lịch sử chuyển đổi trạng thái và provenance)
-- ============================================================================

INSERT INTO ticket_events (id, ticket_id, action, from_status, to_status, actor_sub, source, details, occurred_at)
OVERRIDING SYSTEM VALUE VALUES
-- Ticket 1 (CS1): CLOSED
(1, 'a1111111-1111-4111-8111-111111111101', 'CREATE_DRAFT', NULL, 'DRAFT', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{"ip": "10.1.40.15"}'::jsonb, '2026-10-10 08:15:00+07'),
(2, 'a1111111-1111-4111-8111-111111111101', 'SUBMIT', 'DRAFT', 'SUBMITTED', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{"routed_to": "CS1"}'::jsonb, '2026-10-10 08:30:00+07'),
(3, 'a1111111-1111-4111-8111-111111111101', 'ASSIGN', 'SUBMITTED', 'ASSIGNED', 'd8608553-a02a-50b8-b05f-6cfe42da7850', 'dx-helpdesk', '{"assigned_technician": "kythuatvien", "technician_sub": "9f19d880-973b-592b-bdb3-a354ac11cd6a"}'::jsonb, '2026-10-10 08:45:00+07'),
(4, 'a1111111-1111-4111-8111-111111111101', 'START_PROGRESS', 'ASSIGNED', 'IN_PROGRESS', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk', '{"snipeit_sync": "Đang sửa chữa"}'::jsonb, '2026-10-10 09:00:00+07'),
(5, 'a1111111-1111-4111-8111-111111111101', 'RESOLVE', 'IN_PROGRESS', 'RESOLVED', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk', '{"summary": "Đã thay nguồn ATX"}'::jsonb, '2026-10-10 15:45:00+07'),
(6, 'a1111111-1111-4111-8111-111111111101', 'CLOSE', 'RESOLVED', 'CLOSED', 'd8608553-a02a-50b8-b05f-6cfe42da7850', 'dx-helpdesk', '{"rating": 5, "snipeit_sync": "Sẵn sàng"}'::jsonb, '2026-10-10 16:30:00+07'),

-- Ticket 2 (CS1): IN_PROGRESS
(7, 'a1111111-1111-4111-8111-111111111102', 'CREATE_DRAFT', NULL, 'DRAFT', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{}'::jsonb, '2026-10-17 08:50:00+07'),
(8, 'a1111111-1111-4111-8111-111111111102', 'SUBMIT', 'DRAFT', 'SUBMITTED', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{"routed_to": "CS1"}'::jsonb, '2026-10-17 09:00:00+07'),
(9, 'a1111111-1111-4111-8111-111111111102', 'ASSIGN', 'SUBMITTED', 'ASSIGNED', 'd8608553-a02a-50b8-b05f-6cfe42da7850', 'dx-helpdesk', '{"assigned_technician": "kythuatvien", "technician_sub": "9f19d880-973b-592b-bdb3-a354ac11cd6a"}'::jsonb, '2026-10-17 09:15:00+07'),
(10, 'a1111111-1111-4111-8111-111111111102', 'START_PROGRESS', 'ASSIGNED', 'IN_PROGRESS', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk', '{"snipeit_sync": "Đang sửa chữa"}'::jsonb, '2026-10-17 10:15:00+07'),

-- Ticket 3 (CS1): RESOLVED
(11, 'a1111111-1111-4111-8111-111111111103', 'CREATE_DRAFT', NULL, 'DRAFT', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{}'::jsonb, '2026-10-17 13:45:00+07'),
(12, 'a1111111-1111-4111-8111-111111111103', 'SUBMIT', 'DRAFT', 'SUBMITTED', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{"routed_to": "CS1"}'::jsonb, '2026-10-17 14:00:00+07'),
(13, 'a1111111-1111-4111-8111-111111111103', 'ASSIGN', 'SUBMITTED', 'ASSIGNED', 'd8608553-a02a-50b8-b05f-6cfe42da7850', 'dx-helpdesk', '{"assigned_technician": "kythuatvien", "technician_sub": "9f19d880-973b-592b-bdb3-a354ac11cd6a"}'::jsonb, '2026-10-17 14:30:00+07'),
(14, 'a1111111-1111-4111-8111-111111111103', 'START_PROGRESS', 'ASSIGNED', 'IN_PROGRESS', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk', '{}'::jsonb, '2026-10-17 15:00:00+07'),
(15, 'a1111111-1111-4111-8111-111111111103', 'RESOLVE', 'IN_PROGRESS', 'RESOLVED', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk', '{"summary": "Đã cập nhật gói wsl_update_x64 và kích hoạt Hyper-V trong BIOS, Docker chạy tốt."}'::jsonb, '2026-10-18 07:30:00+07'),

-- Ticket 4 (CS1): ASSIGNED
(16, 'a1111111-1111-4111-8111-111111111104', 'CREATE_DRAFT', NULL, 'DRAFT', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{}'::jsonb, '2026-10-18 07:50:00+07'),
(17, 'a1111111-1111-4111-8111-111111111104', 'SUBMIT', 'DRAFT', 'SUBMITTED', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{"routed_to": "CS1"}'::jsonb, '2026-10-18 08:00:00+07'),
(18, 'a1111111-1111-4111-8111-111111111104', 'ASSIGN', 'SUBMITTED', 'ASSIGNED', 'd8608553-a02a-50b8-b05f-6cfe42da7850', 'dx-helpdesk', '{"assigned_technician": "kythuatvien", "technician_sub": "9f19d880-973b-592b-bdb3-a354ac11cd6a"}'::jsonb, '2026-10-18 08:10:00+07'),

-- Ticket 5 (CS1): SUBMITTED
(19, 'a1111111-1111-4111-8111-111111111105', 'CREATE_DRAFT', NULL, 'DRAFT', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{}'::jsonb, '2026-10-18 08:10:00+07'),
(20, 'a1111111-1111-4111-8111-111111111105', 'SUBMIT', 'DRAFT', 'SUBMITTED', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{"routed_to": "CS1"}'::jsonb, '2026-10-18 08:15:00+07'),

-- Ticket 6 (CS1): DRAFT
(21, 'a1111111-1111-4111-8111-111111111106', 'CREATE_DRAFT', NULL, 'DRAFT', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{}'::jsonb, '2026-10-18 08:20:00+07'),

-- Ticket 7 (CS2): IN_PROGRESS
(22, 'b2222222-2222-4222-8222-222222222201', 'CREATE_DRAFT', NULL, 'DRAFT', '2324827d-3d37-5241-997f-25b64722818d', 'dx-helpdesk', '{}'::jsonb, '2026-10-17 10:45:00+07'),
(23, 'b2222222-2222-4222-8222-222222222201', 'SUBMIT', 'DRAFT', 'SUBMITTED', '2324827d-3d37-5241-997f-25b64722818d', 'dx-helpdesk', '{"routed_to": "CS2"}'::jsonb, '2026-10-17 11:00:00+07'),
(24, 'b2222222-2222-4222-8222-222222222201', 'ASSIGN', 'SUBMITTED', 'ASSIGNED', '8fe64e2b-4772-5d63-ad4d-f48698f6b58e', 'dx-helpdesk', '{"assigned_technician": "kythuatvien_cs2", "technician_sub": "18685db0-c1c9-5e08-97cd-fdd20f23f6ed"}'::jsonb, '2026-10-17 11:15:00+07'),
(25, 'b2222222-2222-4222-8222-222222222201', 'START_PROGRESS', 'ASSIGNED', 'IN_PROGRESS', '18685db0-c1c9-5e08-97cd-fdd20f23f6ed', 'dx-helpdesk', '{"snipeit_sync": "Đang sửa chữa"}'::jsonb, '2026-10-17 11:30:00+07'),

-- Ticket 8 (CS2): SUBMITTED
(26, 'b2222222-2222-4222-8222-222222222202', 'CREATE_DRAFT', NULL, 'DRAFT', '2324827d-3d37-5241-997f-25b64722818d', 'dx-helpdesk', '{}'::jsonb, '2026-10-18 07:30:00+07'),
(27, 'b2222222-2222-4222-8222-222222222202', 'SUBMIT', 'DRAFT', 'SUBMITTED', '2324827d-3d37-5241-997f-25b64722818d', 'dx-helpdesk', '{"routed_to": "CS2"}'::jsonb, '2026-10-18 07:45:00+07'),

-- Ticket 9 (CS2): REJECTED
(28, 'b2222222-2222-4222-8222-222222222203', 'CREATE_DRAFT', NULL, 'DRAFT', '2324827d-3d37-5241-997f-25b64722818d', 'dx-helpdesk', '{}'::jsonb, '2026-10-16 09:30:00+07'),
(29, 'b2222222-2222-4222-8222-222222222203', 'SUBMIT', 'DRAFT', 'SUBMITTED', '2324827d-3d37-5241-997f-25b64722818d', 'dx-helpdesk', '{"routed_to": "CS2"}'::jsonb, '2026-10-16 10:00:00+07'),
(30, 'b2222222-2222-4222-8222-222222222203', 'REJECT', 'SUBMITTED', 'REJECTED', '8fe64e2b-4772-5d63-ad4d-f48698f6b58e', 'dx-helpdesk', '{"reason": "Yêu cầu mượn phòng ngoài giờ phải có giấy xác nhận của giảng viên hướng dẫn hoặc Khoa."}'::jsonb, '2026-10-16 11:20:00+07'),

-- Ticket 10 (CS3): CLOSED
(31, 'c3333333-3333-4333-8333-333333333301', 'CREATE_DRAFT', NULL, 'DRAFT', 'a7e3965a-b5b0-5a1f-b755-8f0f9130895b', 'dx-helpdesk', '{}'::jsonb, '2026-10-14 08:30:00+07'),
(32, 'c3333333-3333-4333-8333-333333333301', 'SUBMIT', 'DRAFT', 'SUBMITTED', 'a7e3965a-b5b0-5a1f-b755-8f0f9130895b', 'dx-helpdesk', '{"routed_to": "CS3"}'::jsonb, '2026-10-14 09:00:00+07'),
(33, 'c3333333-3333-4333-8333-333333333301', 'ASSIGN', 'SUBMITTED', 'ASSIGNED', '58ab5e48-abac-5e8e-8336-feb7e3e18a9e', 'dx-helpdesk', '{"assigned_technician": "kythuatvien_cs3", "technician_sub": "b8074364-5be8-55e6-9106-a68702cbde00"}'::jsonb, '2026-10-14 09:30:00+07'),
(34, 'c3333333-3333-4333-8333-333333333301', 'START_PROGRESS', 'ASSIGNED', 'IN_PROGRESS', 'b8074364-5be8-55e6-9106-a68702cbde00', 'dx-helpdesk', '{}'::jsonb, '2026-10-14 10:00:00+07'),
(35, 'c3333333-3333-4333-8333-333333333301', 'RESOLVE', 'IN_PROGRESS', 'RESOLVED', 'b8074364-5be8-55e6-9106-a68702cbde00', 'dx-helpdesk', '{"summary": "Đã thay mới chuột quang cổng USB thương hiệu Fuhlen."}'::jsonb, '2026-10-14 14:00:00+07'),
(36, 'c3333333-3333-4333-8333-333333333301', 'CLOSE', 'RESOLVED', 'CLOSED', '58ab5e48-abac-5e8e-8336-feb7e3e18a9e', 'dx-helpdesk', '{"rating": 4}'::jsonb, '2026-10-14 15:00:00+07'),

-- Ticket 11 (CS3): SUBMITTED
(37, 'c3333333-3333-4333-8333-333333333302', 'CREATE_DRAFT', NULL, 'DRAFT', 'a7e3965a-b5b0-5a1f-b755-8f0f9130895b', 'dx-helpdesk', '{}'::jsonb, '2026-10-18 07:50:00+07'),
(38, 'c3333333-3333-4333-8333-333333333302', 'SUBMIT', 'DRAFT', 'SUBMITTED', 'a7e3965a-b5b0-5a1f-b755-8f0f9130895b', 'dx-helpdesk', '{"routed_to": "CS3"}'::jsonb, '2026-10-18 08:00:00+07'),

-- Ticket 12 (CS1): CLOSED kèm lịch sử REOPEN
(39, 'e1111111-1111-4111-8111-111111111112', 'CREATE_DRAFT', NULL, 'DRAFT', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{}'::jsonb, '2026-10-11 08:00:00+07'),
(40, 'e1111111-1111-4111-8111-111111111112', 'SUBMIT', 'DRAFT', 'SUBMITTED', 'e90585fa-96ac-5f81-87a3-f817cc6d4323', 'dx-helpdesk', '{"routed_to": "CS1"}'::jsonb, '2026-10-11 08:30:00+07'),
(41, 'e1111111-1111-4111-8111-111111111112', 'ASSIGN', 'SUBMITTED', 'ASSIGNED', 'd8608553-a02a-50b8-b05f-6cfe42da7850', 'dx-helpdesk', '{"assigned_technician": "kythuatvien", "technician_sub": "9f19d880-973b-592b-bdb3-a354ac11cd6a"}'::jsonb, '2026-10-11 08:40:00+07'),
(42, 'e1111111-1111-4111-8111-111111111112', 'START_PROGRESS', 'ASSIGNED', 'IN_PROGRESS', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk', '{}'::jsonb, '2026-10-11 09:00:00+07'),
(43, 'e1111111-1111-4111-8111-111111111112', 'RESOLVE', 'IN_PROGRESS', 'RESOLVED', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk', '{"summary": "Đã cài IDE"}'::jsonb, '2026-10-11 16:00:00+07'),
(44, 'e1111111-1111-4111-8111-111111111112', 'REOPEN', 'RESOLVED', 'IN_PROGRESS', 'd8608553-a02a-50b8-b05f-6cfe42da7850', 'dx-helpdesk', '{"reason": "Sinh viên báo chưa cài đủ thư viện Arm Toolchain và driver ST-Link"}'::jsonb, '2026-10-11 17:00:00+07'),
(45, 'e1111111-1111-4111-8111-111111111112', 'RESOLVE', 'IN_PROGRESS', 'RESOLVED', '9f19d880-973b-592b-bdb3-a354ac11cd6a', 'dx-helpdesk', '{"summary": "Đã cài thêm Arm Toolchain và test nạp code thành công"}'::jsonb, '2026-10-12 10:00:00+07'),
(46, 'e1111111-1111-4111-8111-111111111112', 'CLOSE', 'RESOLVED', 'CLOSED', 'd8608553-a02a-50b8-b05f-6cfe42da7850', 'dx-helpdesk', '{"rating": 5}'::jsonb, '2026-10-12 11:00:00+07')
ON CONFLICT (id) DO NOTHING;

UPDATE tickets AS t SET location_id = l.location_id
FROM site_locations AS l WHERE t.location = l.code AND t.location_id IS NULL;

-- Asset tag mẫu cũ được giữ để đối soát với Snipe-IT sau khi seed.
INSERT INTO ticket_legacy_asset_refs (ticket_id, asset_ref) VALUES
    ('a1111111-1111-4111-8111-111111111101', 'HAUI-CS1-PC04'),
    ('a1111111-1111-4111-8111-111111111102', 'HAUI-CS1-PC02'),
    ('a1111111-1111-4111-8111-111111111103', 'HAUI-PC-0002'),
    ('a1111111-1111-4111-8111-111111111104', 'HAUI-CS1-SW01'),
    ('a1111111-1111-4111-8111-111111111105', 'HAUI-CS1-PRJ01'),
    ('a1111111-1111-4111-8111-111111111106', 'HAUI-CS1-PC03'),
    ('b2222222-2222-4222-8222-222222222201', 'HAUI-CS2-PC02'),
    ('c3333333-3333-4333-8333-333333333301', 'HAUI-CS3-PC01'),
    ('c3333333-3333-4333-8333-333333333302', 'HAUI-CS3-PC02'),
    ('e1111111-1111-4111-8111-111111111112', 'HAUI-LT-0001')
ON CONFLICT (ticket_id) DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('ticket_events', 'id'),
    COALESCE((SELECT MAX(id) FROM ticket_events), 1)
);

COMMIT;
