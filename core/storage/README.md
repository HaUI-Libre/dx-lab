<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# core/storage – SeaweedFS

Lưu tệp phi cấu trúc: ảnh đính kèm ticket, tài liệu. Service `seaweedfs` chạy
`weed server` (master, volume và filer trong một tiến trình), dữ liệu nằm trong
volume `seaweedfs-data`. Không mở cổng ra máy host và chưa bật S3; Tầng 2/3 chỉ
truy cập qua gateway.

Bucket `documents` là thư mục `/buckets/documents` của filer. Healthcheck tạo
thư mục này nếu chưa có, nên service chỉ healthy khi bucket đã sẵn sàng.

## Qua gateway

| Thao tác | Request |
|---|---|
| Tải lên | `PUT /api/files/<đường-dẫn>` với thân là nội dung tệp, hoặc `POST` dạng `multipart/form-data` |
| Tải về | `GET /api/files/<đường-dẫn>` |

- Cần Bearer token của một trong 4 vai trò.
- `<đường-dẫn>` gồm tối đa 5 đoạn, mỗi đoạn bắt đầu bằng chữ hoặc số và chỉ gồm
  chữ, số, `.`, `_`, `-`. Ví dụ: `ticket-12/loi-pc04.png`. Sai mẫu thì 400.
- Tệp tối đa 20 MB (413 nếu vượt).
- Không có liệt kê thư mục và xoá. Query string bị bỏ trước khi tới filer, để
  không dùng được các lệnh quản trị như `?mv.from=`.
- Tải lên cùng đường dẫn sẽ ghi đè. Data API nên tự sinh đường dẫn (ví dụ
  `ticket-<id>/<uuid>.<đuôi>`) thay vì dùng nguyên tên tệp người dùng.
- Khi tải về, gateway thêm `X-Content-Type-Options: nosniff` và
  `Content-Security-Policy: sandbox`, để tệp HTML/SVG do người dùng tải lên
  không chạy được script.

```bash
set -a; . ./.env; set +a
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
  -d grant_type=password -d client_id="$KEYCLOAK_CLIENT_ID" -d client_secret="$KEYCLOAK_CLIENT_SECRET" \
  -d username=sinhvien -d password="$DEMO_USER_PASSWORD" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
curl -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: image/png" \
  --data-binary @anh.png http://localhost:9080/api/files/ticket-12/anh.png   # 201
curl -H "Authorization: Bearer $TOKEN" -o anh-tai-ve.png \
  http://localhost:9080/api/files/ticket-12/anh.png                          # 200
```
