<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Kiến trúc DX-Lab

## Luồng gọi dịch vụ

```
Người dùng
   │ (1) đăng nhập SSO
   ▼
Keycloak ──(2) access token (JWT)──► Ứng dụng Nuxt (Tầng 2/3)
                                          │ (3) gọi API kèm token
                                          ▼
                                   Apache APISIX (gateway)
                                   kiểm tra token + vai trò
          ┌──────────────┬───────────────┼───────────────┐
          ▼              ▼               ▼               ▼
   /api/data       /api/workflow    /api/files       /api/ai
   Data API        Flowable REST    SeaweedFS        AI service
   (PostgreSQL)
```

Ứng dụng tầng trên **không** truy cập trực tiếp CSDL hay Flowable; mọi lời gọi
đi qua gateway. Đây là điểm chứng minh Open-Core đóng vai trò PaaS headless.

## Ánh xạ H-P-D-I

| Không gian | Chức năng | Dịch vụ lõi sử dụng |
|---|---|---|
| H | Đăng nhập, người dùng/nhóm/quyền, kho tài liệu | Keycloak, SeaweedFS |
| P | Quy trình yêu cầu hỗ trợ, hàng đợi xử lý, lịch sử | Flowable |
| D | Dữ liệu thống nhất, provenance, lọc/thống kê, dashboard | PostgreSQL, Data API |
| I | Phân loại/ưu tiên yêu cầu, hỏi–đáp tài liệu | AI service, pgvector |

## Quyết định kiến trúc

_(Ghi lại mỗi quyết định quan trọng: bối cảnh, lựa chọn, lý do.)_
