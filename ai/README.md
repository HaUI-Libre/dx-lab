<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# ai/

Dịch vụ Intelligence gợi ý loại sự cố và mức ưu tiên; người dùng xác nhận hoặc sửa
trước khi gửi ticket. `POST /classify` nhận `title`, `description`, trả `category`,
`priority`, `keywords` và `source` (`model` hoặc `rules`).

`rules.py` dùng từ khóa tiếng Việt để dự phòng khi mô hình chưa có, lỗi hoặc chạy quá
`AI_MODEL_TIMEOUT_SECONDS` (mặc định 1 giây). Từ khóa khớp được trả để giải thích.
Nếu không khớp loại nào, API trả 422 để người dùng chọn thủ công, không tự bịa loại.
Mức ưu tiên chỉ là gợi ý; luật không đổi trạng thái ticket hoặc quyền người dùng.

Chạy riêng trong môi trường phát triển: `uvicorn app:app --app-dir ai --port 8000`.
Dịch vụ đi qua APISIX và Docker Compose ở issue #31.
